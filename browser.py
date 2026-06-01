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

    def close(self):
        if self.driver:
            # Chúng ta giải phóng tài nguyên driver.
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
