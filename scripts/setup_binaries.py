import os
import urllib.request
import zipfile
import shutil
import time

BIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'bin')
os.makedirs(BIN_DIR, exist_ok=True)


def download_with_progress(url, dest, description="file"):
    start_time = None
    last_time = None
    last_bytes = 0

    def sizeof(num, with_unit=True):
        for unit in ['B','KB','MB','GB','TB']:
            if num < 1024.0:
                return f"{num:3.1f}{unit}" if with_unit else f"{num:3.1f}"
            num /= 1024.0
        return f"{num:.1f}PB" if with_unit else f"{num:.1f}"

    def reporthook(block_num, block_size, total_size):
        nonlocal start_time
        if start_time is None:
            start_time = time.time()
            
        downloaded = block_num * block_size
        now = time.time()
        elapsed = now - start_time
        
        if elapsed <= 0:
            elapsed = 1e-6
            
        speed = downloaded / elapsed

        if total_size > 0:
            percent = min((downloaded / total_size) * 100, 100.0)
            total_s = sizeof(total_size)
        else:
            percent = 0
            total_s = "?"

        msg = f"{description}: {percent:5.1f}% ({sizeof(downloaded)}/{total_s}) - {sizeof(speed)}/s"
        print(msg.ljust(80), end='\r')
        if total_size > 0 and downloaded >= total_size:
            print()

    try:
        urllib.request.urlretrieve(url, dest, reporthook)
    except Exception:
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except Exception:
                pass
        raise

def binaries_exist():
    ytdlp_path = os.path.join(BIN_DIR, "yt-dlp.exe")
    ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg.exe")
    return os.path.exists(ytdlp_path) and os.path.exists(ffmpeg_path)

def ask_redownload():
    while True:
        response = input("Binaries đã tồn tại. Bạn có muốn tải lại không? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Vui lòng nhập 'y' hoặc 'n'")

def download_ytdlp():
    print("Pulling yt-dlp...")
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    dest = os.path.join(BIN_DIR, "yt-dlp.exe")
    download_with_progress(url, dest, "yt-dlp")
    print("Done!")

def download_ffmpeg():
    print("Pulling ffmpeg...")
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    zip_path = os.path.join(BIN_DIR, "ffmpeg_temp.zip")
    
    download_with_progress(url, zip_path, "ffmpeg zip")
    
    print("Unzipping ffmpeg...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(BIN_DIR)
    
    for item in os.listdir(BIN_DIR):
        if item.startswith("ffmpeg-master-latest"):
            target_exe = os.path.join(BIN_DIR, item, "bin", "ffmpeg.exe")
            if os.path.exists(target_exe):
                shutil.move(target_exe, os.path.join(BIN_DIR, "ffmpeg.exe"))
            shutil.rmtree(os.path.join(BIN_DIR, item))
            break
            
    os.remove(zip_path)
    print("Done! ffmpeg.exe")

if __name__ == "__main__":
    download_ytdlp()
    download_ffmpeg()
    print(f"Setup xong, binaries nằm tại thư mục: {os.path.abspath(BIN_DIR)}")
