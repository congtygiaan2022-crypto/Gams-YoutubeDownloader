import logging
import socket
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class Browser:
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def _wait_for_port(self, address, timeout=10):
        """Chờ port mở trước khi kết nối."""
        host, port = address.split(':')
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, int(port)), timeout=1):
                    return True
            except:
                time.sleep(0.5)
        return False

    def attach(self, debugger_address, driver_path=None):
        """
        Kết nối với instance Chrome hiện có qua debuggerAddress.
        debugger_address: '127.0.0.1:xxxxx'
        """
        try:
            print(f"DEBUG: Connecting to {debugger_address}...", flush=True) # Direct stdout for GUI
            self.logger.info(f"Đang kiểm tra kết nối tới {debugger_address}...")
            if not self._wait_for_port(debugger_address):
                self.logger.error(f"Port {debugger_address} không phản hồi sau 10 giây.")
                return None

            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", debugger_address)
            
            # Nếu cần chromedriver cụ thể, có thể dùng Service.
            service = Service() if driver_path is None else Service(executable_path=driver_path)
            
            self.logger.info("Đang khởi tạo WebDriver...")
            # Thêm timeout cho việc khởi tạo
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Đặt limit load page để tránh treo nếu trang web hiện tại nặng
            self.driver.set_page_load_timeout(30)
            
            self.logger.info(f"Đã kết nối Chrome tại {debugger_address}")
            return self.driver
        except Exception as e:
            self.logger.error(f"Lỗi kết nối automation: {e}")
            # Không raise, trả về None để main xử lý retry
            return None

    def start_local_browser(self, headless=True):
        """Khởi động trình duyệt Chrome cục bộ (Dự phòng)."""
        try:
            self.logger.info("Đang khởi động trình duyệt Chrome cục bộ (Dự phòng)...")
            options = Options()
            if headless:
                options.add_argument("--headless=new")
                self.logger.info("Trình duyệt chạy ẩn danh (headless)")
            else:
                self.logger.info("Trình duyệt chạy hiển thị cửa sổ (headed)")
            
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1280,800")
            
            # Tránh phát hiện bot
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            self.logger.info("Đang khởi tạo Chrome WebDriver...")
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            self.logger.info("Khởi động Chrome cục bộ thành công.")
            return self.driver
        except Exception as e:
            self.logger.error(f"Lỗi khởi động Chrome cục bộ: {e}")
            return None

    def close(self):
        if self.driver:
            # Chúng ta giải phóng tài nguyên driver.
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
