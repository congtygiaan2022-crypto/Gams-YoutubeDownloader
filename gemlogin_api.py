import requests
import config
import logging

class GemLoginAPI:
    def __init__(self):
        self.base_url = config.GEMLOGIN_API_URL
        self.logger = logging.getLogger(__name__)

    def get_profiles(self):
        """Lấy danh sách tất cả profile."""
        # Docs: GET /api/profiles
        url = f"{self.base_url}/api/profiles"
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.RequestException as e:
            self.logger.error(f"Lỗi khi lấy danh sách profile: {e}")
            return []

    def start_profile(self, profile_id):
        """Khởi động profile và trả về cổng automation."""
        # Docs: GET /api/profiles/start/{id}
        url = f"{self.base_url}/api/profiles/start/{profile_id}"
        
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data.get('data', {})
        except requests.RequestException as e:
            self.logger.error(f"Lỗi khi start profile {profile_id}: {e}")
            raise

    def stop_profile(self, profile_id):
        """Dừng profile."""
        # Docs: GET /api/profiles/close/{id}
        url = f"{self.base_url}/api/profiles/close/{profile_id}"
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.info(f"Đã dừng profile {profile_id}")
        except requests.RequestException as e:
            self.logger.error(f"Lỗi khi dừng profile {profile_id}: {e}")
