import os

# Cấu hình Browser
BROWSER_TYPE = "gemlogin" # gemlogin hoặc gpmlogin
GEMLOGIN_API_URL = "http://localhost:1010"
GPM_LOGIN_API_URL = "http://localhost:60064"
API_VERSION = "v1"

# Đường dẫn
LOG_FILE = "automation.log"

# Thời gian chờ
REQUEST_TIMEOUT = 30  # giây

# Hiệu năng
DOWNLOAD_THREADS = 3 # Số luồng tải video
CHECK_THREADS = 1    # Số luồng check (Hiện tại chưa dùng hết nếu chỉ có 1 profile)

# Cấu hình vòng lặp
RUN_ONCE = False      # Chạy 1 lần hay vòng lặp
LOOP_COUNT = 10000       # Số vòng lặp mặc định
LOOP_DELAY = 60      # Giây chờ giữa các vòng lặp

# Cấu hình quét video
USE_API_SCAN = False
USE_BROWSER_SCAN = True
YOUTUBE_API_KEY = ""

# Đường dẫn lưu video
DOWNLOAD_PATH = "downloads"

# Cấu hình Cookies cho yt-dlp để tránh lỗi "Sign in to confirm you're not a bot"
COOKIES_FROM_BROWSER = None
COOKIES_FILE = "cookies.txt"

