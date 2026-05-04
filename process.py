import sys
import os
import subprocess

def get_local_identity():
    valid_choices = {'1': 'hung', '2': 'quang', '3': 'hoang'}
    while True:
        print("Vui lòng chọn danh tính local để xử lý:")
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
    identity = get_local_identity()
    file_path = f"{identity}.txt"
    
    if not os.path.exists(file_path):
        print(f"[-] File {file_path} không tồn tại. Không có dữ liệu để xử lý.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print(f"[-] File {file_path} trống.")
        return

    print(f"[*] Tìm thấy {len(lines)} mục trong {file_path}.")

    # Đảm bảo các thư mục đích tồn tại
    video_dir = os.path.join("data", "raw", "video")
    audio_dir = os.path.join("data", "raw", "audio")
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    yt_dlp_path = os.path.join("bin", "yt-dlp.exe")
    ffmpeg_path = os.path.join("bin", "ffmpeg.exe")

    valid_identities = ['hung', 'quang', 'hoang']

    for line in lines:
        # Hỗ trợ cả trường hợp lưu URL đầy đủ và ID sơ cấp
        if line.startswith("http://") or line.startswith("https://"):
            full_url = line
            # Trích xuất định danh sơ cấp từ url CDN (ví dụ: yt-jica-...)
            primary_id = full_url.split('/')[-2].replace('.mp4', '')
        else:
            full_url = None
            primary_id = line

        print(f"\n--- Đang xử lý: {primary_id} ---")

        # KIỂM TRA TRÙNG LẶP GIỮA CÁC WORKSPACE (Danh tính)
        found_in_workspaces = []
        for ident in valid_identities:
            ident_file = f"{ident}.txt"
            if os.path.exists(ident_file):
                with open(ident_file, "r", encoding="utf-8") as id_f:
                    # Kiểm tra xem primary_id có nằm trong nội dung file của danh tính khác không
                    if primary_id in id_f.read():
                        found_in_workspaces.append(ident)

        if len(found_in_workspaces) > 1:
            print(f"[-] CẢNH BÁO: ID '{primary_id}' bị trùng lặp giữa các workspace (danh tính): {', '.join(found_in_workspaces)}")
            print(f"[-] YÊU CẦU RESOLVE THỦ CÔNG. Bỏ qua tiến trình pull/convert.")
            continue

        video_path = os.path.join(video_dir, f"{primary_id}.mp4")
        audio_path = os.path.join(audio_dir, f"{primary_id}.wav")

        has_video = os.path.exists(video_path)
        has_audio = os.path.exists(audio_path)

        # 2.3: Nếu id đã có audio, hay video lẫn audio, báo SKIPPING ID
        if has_audio:
            print(f"[+] Audio đã tồn tại tại {audio_path}.")
            print("[-] SKIPPING ID")
            continue

        # 2.1: Nếu id chưa có trong data raw (video lẫn audio), tiến hành pull
        if not has_video and not has_audio:
            if not full_url:
                print(f"[-] LỖI: Dòng log '{line}' chỉ chứa định danh sơ cấp, không có URL đầy đủ để pull. Bỏ qua.")
                continue

            if not os.path.exists(yt_dlp_path):
                print(f"[-] CẢNH BÁO: Không tìm thấy '{yt_dlp_path}'. Bỏ qua tiến trình pull cho '{primary_id}'.")
                # Không thoát script, tiếp tục các mục khác
                continue
            
            print(f"[*] Tiến hành pull video cho ID '{primary_id}'...")
            command = [
                yt_dlp_path,
                "--referer", "https://vietnamtoday.vtv.vn/",
                full_url,
                "-o", video_path
            ]
            try:
                subprocess.run(command)
                if os.path.exists(video_path):
                    has_video = True
                    print(f"[+] Pull video thành công.")
                else:
                    print(f"[-] Pull video thất bại (không tìm thấy file output).")
            except Exception as e:
                print(f"[-] Lỗi trong quá trình pull video: {e}")

        # 2.2: Nếu id đã có video (từ trước, hoặc vừa pull xong), thực hiện convert to audio
        if has_video and not has_audio:
            if not os.path.exists(ffmpeg_path):
                print(f"[-] CẢNH BÁO: Không tìm thấy '{ffmpeg_path}'. Bỏ qua tiến trình convert audio cho '{primary_id}'.")
                continue

            print(f"[*] Tiến hành convert video sang audio cho ID '{primary_id}'...")
            command = [
                ffmpeg_path,
                "-i", video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                audio_path
            ]
            try:
                subprocess.run(command)
                if os.path.exists(audio_path):
                    print(f"[+] Convert audio thành công: {audio_path}")
                else:
                    print(f"[-] Convert audio thất bại (không tìm thấy file output).")
            except Exception as e:
                print(f"[-] Lỗi trong quá trình convert audio: {e}")

if __name__ == "__main__":
    main()