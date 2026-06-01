import os
import logging
import yt_dlp
import config
import string
import random

def generate_random_hashtag(length=6):
    """Tạo chuỗi hashtag ngẫu nhiên."""
    chars = string.ascii_lowercase + string.digits
    return '#' + ''.join(random.choice(chars) for _ in range(length))

class Downloader:
    def __init__(self, download_dir=None):
        # Ưu tiên tham số truyền vào > config > mặc định 'downloads'
        if download_dir:
            self.download_dir = download_dir
        elif hasattr(config, 'DOWNLOAD_PATH') and config.DOWNLOAD_PATH:
            self.download_dir = config.DOWNLOAD_PATH
        else:
            self.download_dir = 'downloads'

        self.logger = logging.getLogger(__name__)
        self.last_error = None
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def clean_temp_files(self):
        """Quét và xóa các file tạm (.part, .ytdl) do lần tải trước bị lỗi để lại."""
        try:
            self.logger.info("Đang quét dọn file rác (.part, .ytdl)...")
            count = 0
            for root, dirs, files in os.walk(self.download_dir):
                for file in files:
                    if file.endswith('.part') or file.endswith('.ytdl') or '.f' in file and '.mp4' not in file: # .f137, .f251 etc
                        # Check kỹ hơn cho các file format ID (f137, f140...) thường không có ext rõ ràng hoặc nằm giữa
                        # Tuy nhiên yt-dlp thường để lại .part hoặc .ytdl là chính.
                        # Logic đơn giản nhất là xóa .part và .ytdl
                        pass

                    if file.endswith('.part') or file.endswith('.ytdl'):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            count += 1
                            self.logger.info(f"Đã xóa file rác: {file}")
                        except Exception as e:
                            self.logger.error(f"Không thể xóa {file}: {e}")
            
            if count > 0:
                self.logger.info(f"Đã dọn dẹp {count} file rác.")
            else:
                self.logger.info("Không tìm thấy file rác nào.")
                
        except Exception as e:
            self.logger.error(f"Lỗi khi dọn dẹp file tạm: {e}")

    def is_permanent_error(self, error_msg):
        """Kiểm tra xem lỗi tải có phải là lỗi vĩnh viễn (như members-only, private, deleted...) hay không."""
        if not error_msg:
            return False
        error_msg = error_msg.lower()
        permanent_keywords = [
            "members-only",
            "join this channel to get access to members-only content",
            "private video",
            "this video is private",
            "video unavailable",
            "this video is unavailable",
            "removed by the uploader",
            "sign in to confirm your age",
            "confirm your age",
            "age-restricted",
            "copyright claim",
            "country restriction",
            "not available in your country",
            "not made this video available",
            "is no longer available",
        ]
        return any(kw in error_msg for kw in permanent_keywords)

    def download_video(self, video_url, subfolder=None):
        """Tải video đơn lẻ sử dụng yt-dlp. Tùy chọn tải vào thư mục con."""
        self.last_error = None
        
        target_dir = self.download_dir
        if subfolder:
            target_dir = os.path.join(self.download_dir, subfolder)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

        # Tạo hashtag ngẫu nhiên thay cho ID
        random_tag = generate_random_hashtag()
        
        ydl_opts = {
            'outtmpl': os.path.join(target_dir, f'%(title)s {random_tag}.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        # Thiết lập Cookies để tránh lỗi "Sign in to confirm you're not a bot"
        cookie_file_configured = getattr(config, 'COOKIES_FILE', 'cookies.txt')
        # Tìm file cookies ở thư mục gốc của project
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_path = os.path.join(base_dir, cookie_file_configured) if not os.path.isabs(cookie_file_configured) else cookie_file_configured

        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
            self.logger.info(f"Đang sử dụng file cookies: {cookie_path}")
        elif getattr(config, 'COOKIES_FROM_BROWSER', None):
            ydl_opts['cookiesfrombrowser'] = config.COOKIES_FROM_BROWSER
            self.logger.info(f"Đang trích xuất cookies từ trình duyệt: {config.COOKIES_FROM_BROWSER}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"Đang tải: {video_url} vào {target_dir}")
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                # Chèn hashtag vào filename nếu cần (mặc định outtmpl đã có random_tag)
                # yt-dlp prepare_filename trả về path tuyệt đối hoặc tương đối tùy config
                return os.path.basename(filename)
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Lỗi khi tải {video_url}: {e}")
            return None

    def copy_video(self, filename, src_subfolder, dest_subfolder):
        """Copy video từ thư mục nguồn sang thư mục đích."""
        import shutil
        src_path = os.path.join(self.download_dir, src_subfolder, filename)
        dest_dir = os.path.join(self.download_dir, dest_subfolder)
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                self.logger.info(f"Đã copy {filename} từ {src_subfolder} sang {dest_subfolder}")
                return True
            else:
                self.logger.error(f"Không tìm thấy file nguồn để copy: {src_path}")
                return False
        except Exception as e:
            self.logger.error(f"Lỗi khi copy file {filename}: {e}")
            return False
