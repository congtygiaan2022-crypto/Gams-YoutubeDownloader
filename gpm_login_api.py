import requests
import config
import logging

class GPMLoginAPI:
    def __init__(self):
        self.base_url = config.GPM_LOGIN_API_URL
        self.logger = logging.getLogger(__name__)

    def get_profiles(self):
        """Lấy danh sách tất cả profile GPM Login."""
        # Docs giả định: GET /api/v3/profiles
        url = f"{self.base_url}/api/v3/profiles"
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            # GPM thường trả về list trực tiếp hoặc trong data
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get('data', [])
        except requests.RequestException as e:
            self.logger.error(f"Lỗi khi lấy danh sách profile GPM: {e}")
            return []

    def start_profile(self, profile_id):
        """Khởi động profile GPM và trả về thông tin kết nối."""
        # Docs giả định: GET /api/v3/profiles/start/{id}
        url = f"{self.base_url}/api/v3/profiles/start/{profile_id}"
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data.get('data', data) # Trả về data hoặc toàn bộ response nếu data không tồn tại
        except requests.RequestException as e:
            self.logger.error(f"Lỗi khi start profile GPM {profile_id}: {e}")
            raise

    def stop_profile(self, profile_id):
        """Dừng profile GPM."""
        # Docs giả định: GET /api/v3/profiles/close/{id}
        url = f"{self.base_url}/api/v3/profiles/close/{profile_id}"
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.info(f"Đã dừng profile GPM {profile_id}")
        except requests.RequestException as e:
            self.logger.error(f"Lỗi khi dừng profile GPM {profile_id}: {e}")
