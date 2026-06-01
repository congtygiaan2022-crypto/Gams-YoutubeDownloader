# -*- coding: utf-8 -*-
"""
git_dev_push.py - Công cụ đóng gói và đẩy code sạch lên GitHub cho Dev
====================================================================
Chạy script này để đẩy mã nguồn quan trọng của phần mềm lên Git,
loại bỏ toàn bộ dữ liệu cấu hình cá nhân, API keys, database, và logs.
"""

import sys
import os
import subprocess
import datetime
import re

# Sửa lỗi hiển thị ký tự đặc biệt trên console Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# DANH SÁCH CÁC FILE VÀ THƯ MỤC QUAN TRỌNG ĐƯỢC PHÉP ĐẨY LÊN GIT
ALLOWED_FILES = [
    # Core source files
    "main.py",
    "downloader.py",
    "config.py",
    "browser.py",
    "gemlogin_api.py",
    "gpm_login_api.py",
    "youtube_manager.py",
    "clean_history.py",
    "verify_download.py",
    "requirements.txt",
    "icon.ico",
    "HUONG_DAN_CAI_DAT.txt",
    "GiaanTesttool.py",
    ".gitignore",
    "Day_Cap_Nhat_Git.bat",
    "git_dev_push.py",
    
    # Client-side setup files inside AutoUpdate folder
    "AutoUpdate - Antigravity_Gams_Youtubedownload/Cai_Dat_Thu_Vien.bat",
    "AutoUpdate - Antigravity_Gams_Youtubedownload/Chay_Tool.bat",
    "AutoUpdate - Antigravity_Gams_Youtubedownload/HUONG_DAN_CAI_DAT.txt",
    "AutoUpdate - Antigravity_Gams_Youtubedownload/launcher_git.py",
    "AutoUpdate - Antigravity_Gams_Youtubedownload/requirements.txt"
]

def get_git_remote_url():
    try:
        res = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except:
        pass
    return None

def run_clean_push():
    print("====================================================")
    print("  BAT DAU DONG GOI & DAY PHAN MEM MOI TINH LEN GIT")
    print("====================================================")
    
    # 1. Khởi tạo Git nếu chưa có
    if not os.path.exists(".git"):
        print("[+] Khoi tao local Git Repository...")
        subprocess.run(["git", "init"], check=True)
        
    # 2. Kiểm tra Remote URL
    remote_url = get_git_remote_url()
    if not remote_url:
        print("[!] Chua tim thay Git Remote Origin URL.")
        remote_url = input("-> Nhap URL Repository Git (vi du: https://github.com/user/repo.git): ").strip()
        if not remote_url:
            print("[-] Loi: Can co URL Git Repository de day cap nhat.")
            return
        
        # Liên kết với remote origin
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        print(f"[OK] Da lien ket remote origin: {remote_url}")
    else:
        print(f"[OK] Da tim thay remote origin: {remote_url}")
        change = input("-> Ban co muon thay doi URL repository nay khong? (y/N): ").strip().lower()
        if change == 'y':
            new_url = input("-> Nhap URL Repository Git moi: ").strip()
            if new_url:
                subprocess.run(["git", "remote", "set-url", "origin", new_url], check=True)
                remote_url = new_url
                print(f"[OK] Da cap nhat remote origin sang: {remote_url}")


    # 3. Cấu hình branch mặc định là main
    subprocess.run(["git", "branch", "-M", "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Tự động cập nhật repo URL vào launcher của User
    launcher_path = "AutoUpdate - Antigravity_Gams_Youtubedownload/launcher_git.py"
    if os.path.exists(launcher_path):
        try:
            with open(launcher_path, "r", encoding="utf-8") as f:
                launcher_content = f.read()
            
            updated_content = re.sub(
                r'GIT_REPO_URL = ".*?"',
                f'GIT_REPO_URL = "{remote_url}"',
                launcher_content
            )
            
            with open(launcher_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print(f"[OK] Da tu dong cap nhat URL Git vao client launcher: {launcher_path}")
        except Exception as e:
            print(f"[!] Canh bao: Khong the cap nhat URL Git vao client launcher: {e}")

    try:
        # 5. Huỷ theo dõi toàn bộ file trong Git index để reset sạch sẽ
        print("[+] Buoc 1: Reset Git Index (Khong xoa file cuc bo)...")
        subprocess.run(["git", "rm", "-r", "--cached", "."], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 6. Xử lý config.py để giấu API Key trước khi stage
        config_path = "config.py"
        has_config = os.path.exists(config_path)
        original_config = None
        
        if has_config:
            print("[+] Buoc 2: Dang lam sach config.py (Giang mat YouTube API Key)...")
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    original_config = f.read()
                
                # Làm sạch API key
                sanitized_config = re.sub(
                    r'YOUTUBE_API_KEY = ".*?"',
                    'YOUTUBE_API_KEY = ""',
                    original_config
                )
                
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(sanitized_config)
            except Exception as e:
                print(f"[!] Canh bao: Khong the lam sach config.py: {e}")

        # 7. Add các file được phép vào git index
        print("[+] Buoc 3: Them cac file quan trong vao danh sach phat hanh...")
        added_count = 0
        for file_path in ALLOWED_FILES:
            if os.path.exists(file_path):
                # Thay thế dấu gạch chéo ngược để tương thích Git
                normalized_path = file_path.replace("\\", "/")
                subprocess.run(["git", "add", normalized_path], check=True)
                print(f"  [OK] Da them: {file_path}")
                added_count += 1
            else:
                print(f"  [!] Khong tim thay: {file_path}")

        # Khôi phục lại file config.py gốc cho nhà phát triển ngay lập tức
        if has_config and original_config is not None:
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(original_config)
                print("[OK] Da khoi phuc lai config.py voi API Key cuc bo cho nha phat trien.")
            except Exception as e:
                print(f"[!] Canh bao: Khong the khoi phuc lai config.py cho nha phat trien: {e}")

        if added_count == 0:
            print("[-] Loi: Khong co file nao de day len Git.")
            return

        # 8. Tạo commit message với thời gian hiện tại
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Release-Clean-{now_str}"
        print(f"\n[+] Buoc 4: Tao ban ghi commit: '{commit_msg}'...")
        
        # Kiểm tra xem có gì thay đổi để commit không
        status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status_res.stdout.strip():
            print("[OK] Khong co thay doi nao so voi phien ban truoc tren Git.")
        else:
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            print("[OK] Tao ban ghi commit thanh cong.")
            
        # 9. Đẩy code lên GitHub
        print("\n[+] Buoc 5: Dang day phien ban sach len Github (branch main)...")
        # Đảm bảo push trỏ đúng origin main
        result = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n====================================================")
            print("  DA UP CODES & PHAT HANH PHIEN BAN MOI LEN GIT!")
            print("  Nguoi dung chi can chay Chay_Tool.bat de nhan cap nhat.")
            print("====================================================")
        else:
            print("\n[-] LOI KHI DAY LEN GITHUB:")
            print(result.stderr)
            print("\n-> Vui long kiem tra: 1. Ket noi internet. 2. Quyen truy cap repo.")
            
    except Exception as e:
        print(f"\n[-] Da xay ra loi trong qua trinh day code: {e}")

if __name__ == "__main__":
    run_clean_push()
    print("\nNhan Enter de thoat.")
    input()
