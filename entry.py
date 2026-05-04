import sys
import os
import subprocess
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_local_identity():
    valid_choices = {'1': 'hung', '2': 'quang', '3': 'hoang'}
    while True:
        print("Vui lòng chọn danh tính local:")
        print("1. hung")
        print("2. quang")
        print("3. hoang")
        
        choice = input("Lựa chọn của bạn: ").strip()
        
        if choice in valid_choices:
            identity = valid_choices[choice]
            print(f"\n[*] Đã xác nhận danh tính: {identity}\n")
            return identity
        else:
            print("[-] Lựa chọn không hợp lệ. Vui lòng chỉ nhập 1, 2, hoặc 3.\n")

def main():
    # 1. Yêu cầu nhập danh tính trước tiên
    local_identity = get_local_identity()

    while True:
        url = input("\nEnter a VietNamToday URL (hoặc nhập 0 để thoát): ").strip()
        
        if url == '0':
            sys.exit(0)

        if not url:
            print("No URL provided. Hãy thử lại.")
            continue

        parsed_url = urlparse(url)
        if "vietnamtoday.vtv.vn" not in parsed_url.netloc:
            print("Invalid URL. Vui lòng nhập URL hợp lệ từ vietnamtoday.vtv.vn")
            continue

        print(f"URL received: {url}\nFetching data...")
        extracted_s_url = None
        
        extracted_video_id = None
        is_duplicate = False

        try:
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            })
            response.raise_for_status()
            html_content = response.text

            print("\n[*] Đang quét tìm đường dẫn stream gốc (master.m3u8) từ CDN...")
            
            # Regex chỉ lấy các URL bắt đầu bằng http(s)://cdn-videos.vtv.vn và kết thúc bằng /master.m3u8
            target_pattern = r'(https?://cdn-videos\.vtv\.vn/[^\s\"\']+/master\.m3u8)'
            stream_urls = set(re.findall(target_pattern, html_content))
            
            if len(stream_urls) == 1:
                s_url = list(stream_urls)[0]
                extracted_s_url = s_url
                # Trích xuất định danh (ID video)
                extracted_video_id = s_url.split('/')[-2].replace('.mp4', '')
                print(f"[+] Tìm thấy 1 luồng m3u8 mục tiêu:\n    => {s_url} (ID: {extracted_video_id})")
                
                # Kiểm tra tồn tại trong master (targets.txt)
                existing_targets = set()
                try:
                    with open("targets.txt", "r", encoding="utf-8") as f:
                        existing_targets = set(line.strip() for line in f if line.strip())
                except FileNotFoundError:
                    pass
                    
                if extracted_video_id in existing_targets:
                    print(f"[-] Mã định danh '{extracted_video_id}' đã tồn tại trong targets.txt. Bỏ qua lưu.")
                    is_duplicate = True
                else:
                    # Lưu toàn bộ URL CDN thay vì chỉ lưu mã ID để kịch bản xử lý sau có thể pull
                    with open(f"{local_identity}.txt", "a", encoding="utf-8") as f:
                        f.write(extracted_s_url + "\n")
                    with open("targets.txt", "a", encoding="utf-8") as f:
                        f.write(extracted_s_url + "\n")
                        
                    print(f"[*] Đã lưu URL CDN cho mã định danh '{extracted_video_id}' vào {local_identity}.txt và targets.txt")
            elif len(stream_urls) > 1:
                print(f"[-] Tìm thấy {len(stream_urls)} luồng m3u8 (yêu cầu duy nhất 1). Bỏ qua lưu.")
                for s_url in stream_urls:
                    v_id = s_url.split('/')[-2].replace('.mp4', '')
                    print(f"    => {s_url} (ID: {v_id})")
            else:
                print("[-] Không tìm thấy URL stream gốc dạng master.m3u8.")

        except requests.exceptions.RequestException as e:
            print(f"GET request failed: {e}")

        # Post-scan menu
        while True:
            print("\n--- Menu Tuỳ Chọn ---")
            print("1. Pull video đó (chưa có)")
            print("2. Quét URL mới")
            print("0. Thoát")
            
            choice = input("Lựa chọn của bạn: ").strip()
            if choice == '1':
                if extracted_video_id and not is_duplicate and extracted_s_url:
                    yt_dlp_path = os.path.join("bin", "yt-dlp.exe")
                    if not os.path.exists(yt_dlp_path):
                        print(f"[-] Cảnh báo: Không tìm thấy '{yt_dlp_path}'. Vui lòng kiểm tra lại thiết lập hoặc tải yt-dlp.")
                    else:
                        print(f"\n[*] Đang tiến hành pull video ID '{extracted_video_id}'...")
                        # Thư mục xuất dữ liệu
                        output_path = os.path.join("data", "raw", "video", f"{extracted_video_id}.mp4")
                        os.makedirs(os.path.join("data", "raw", "video"), exist_ok=True)
                        command = [
                            yt_dlp_path,
                            "--referer", "https://vietnamtoday.vtv.vn/",
                            extracted_s_url,
                            "-o", output_path
                        ]
                        try:
                            # Chạy tiến trình đồng bộ (in output ra màn hình)
                            subprocess.run(command)
                            print(f"\n[+] Đóng luồng pull.")
                        except Exception as e:
                            print(f"[-] Tiến trình pull gặp lỗi: {e}")
                elif is_duplicate:
                    print(f"\n[-] TỪ CHỐI PULL: Mã '{extracted_video_id}' đã tồn tại trong targets.txt. Không cho phép pull để tránh trùng lặp dữ liệu.")
                else:
                    print("\n[-] Chưa trích xuất được video hợp lệ nào trước đó.")
            elif choice == '2':
                break # Quay lại vòng lặp chính để quét URL mới
            elif choice == '0':
                print("Thoát chương trình.")
                sys.exit(0)
            else:
                print("[-] Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main()