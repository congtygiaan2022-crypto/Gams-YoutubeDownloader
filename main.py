import logging
import time
import sys
import os
import config
from gemlogin_api import GemLoginAPI
from gpm_login_api import GPMLoginAPI
from browser import Browser
from youtube_manager import YouTubeManager
from downloader import Downloader
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException

# Sửa lỗi hiển thị tiếng Việt trên console Windows
sys.stdout.reconfigure(encoding='utf-8')

import datetime

# Tạo thư mục logs nếu chưa có
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Tạo file log riêng cho mỗi phiên
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
session_log_file = os.path.join(log_dir, f"bot_session_{current_time}.log")

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(session_log_file, encoding='utf-8'),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'), # Giữ lại log tổng
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

import re

def sanitize_filename(name):
    """Loại bỏ ký tự không hợp lệ cho tên file Windows."""
    # Ký tự cấm: < > : " / \ | ? *
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def scrape_channel(driver, channel_url, max_videos=10):
    """Quét các video shorts mới nhất từ kênh. Trả về (video_links, channel_title)."""
    # ... (existing code omitted for brevity in replacement, but I will include it to match target)
    try:
        logger.info(f"Đang quét kênh (Browser): {channel_url}")
        driver.get(channel_url)
        time.sleep(5) # Chờ tải trang

        # Lấy tên kênh
        channel_title = ""
        try:
            # Chiến thuật 1: ytd-channel-name (chuẩn)
            title_el = driver.find_element(By.CSS_SELECTOR, "#channel-name #text")
            channel_title = title_el.text.strip()
        except:
            pass
        
        if not channel_title:
             try:
                 # Chiến thuật 1b: XPATH dự phòng
                 title_el = driver.find_element(By.XPATH, "//*[@id='channel-name']//yt-formatted-string")
                 channel_title = title_el.text.strip()
             except:
                 pass

        if not channel_title:
            try:
                # Chiến thuật 2: thẻ meta (og:title)
                meta = driver.find_element(By.XPATH, "//meta[@property='og:title']")
                channel_title = meta.get_attribute("content")
            except:
                pass

        if not channel_title:
             # Chiến thuật 3: Tiêu đề trang
             page_title = driver.title
             if page_title:
                 channel_title = page_title.replace(" - YouTube", "").strip()

        if not channel_title:
            channel_title = "unknown_channel"
        
        logger.info(f"Phát hiện tên kênh: {channel_title}")

        # Phát hiện 404 hoặc trang không tồn tại
        if "404 Not Found" in channel_title or "This page isn't available" in channel_title or "Trang này không khả dụng" in channel_title:
            return "404", channel_title

        # Logic cuộn trang để đảm bảo lấy đủ video
        video_links = []
        scroll_attempts = 0
        max_scrolls = 5
        
        while len(video_links) < max_videos and scroll_attempts < max_scrolls:
            # Cuộn xuống
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
            elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/shorts/')]")
            
            for el in elements:
                href = el.get_attribute('href')
                if href and '/shorts/' in href:
                    if href not in video_links and href != "https://www.youtube.com/shorts/" and href != "https://www.youtube.com/shorts":
                        video_links.append(href)
            
            # Nếu đã đủ thi dừng
            if len(video_links) >= max_videos:
                break
                
            scroll_attempts += 1
            
        if not video_links:
            logger.warning(f"Không tìm thấy video Short nào trên kênh {channel_url}. Có thể kênh không có Short hoặc giao diện thay đổi.")
            
        return video_links[:max_videos], channel_title

    except (WebDriverException, InvalidSessionIdException) as e:
        raise e
    except Exception as e:
        logger.error(f"Lỗi khi quét kênh {channel_url}: {e}", exc_info=True)
        return [], "unknown_channel"

def scrape_channel_api(yt_manager, channel_url, api_key, max_videos=10):
    """Quét video từ kênh bằng YouTube Data API v3."""
    try:
        from googleapiclient.discovery import build
        import logging
        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        logger.info(f"Đang quét kênh (API): {channel_url}")
        
        # 1. Xác định Channel ID từ URL (Thử lấy từ cache trước)
        channel_id = yt_manager.get_channel_id(channel_url)
        
        if not channel_id:
            if '/channel/' in channel_url:
                channel_id = channel_url.split('/channel/')[1].split('/')[0].split('?')[0]
            elif '/@' in channel_url:
                handle = channel_url.split('/@')[1].split('/')[0].split('?')[0]
                # Dùng search để tìm channel ID từ handle (Tốn 100 quota)
                search_response = youtube.search().list(
                    q=f"@{handle}",
                    type='channel',
                    part='id,snippet',
                    maxResults=1
                ).execute()
                if search_response.get('items'):
                    channel_id = search_response['items'][0]['id']['channelId']
            else:
                # Thử tìm kiếm chung qua URL (Tốn 100 quota)
                search_response = youtube.search().list(
                    q=channel_url,
                    type='channel',
                    part='id,snippet',
                    maxResults=1
                ).execute()
                if search_response.get('items'):
                    channel_id = search_response['items'][0]['id']['channelId']
            
            # Lưu vào cache nếu tìm thấy
            if channel_id:
                yt_manager.save_channel_id(channel_url, channel_id)

        if not channel_id:
            logger.error(f"Không thể xác định Channel ID từ URL: {channel_url}")
            return [], "unknown_channel"

        # 2. Lấy thông tin kênh (Title)
        channel_response = youtube.channels().list(
            part='snippet,contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response.get('items'):
            return "404", "unknown_channel"
            
        channel_info = channel_response['items'][0]
        channel_title = channel_info['snippet']['title']
        uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
        
        # 3. Lấy video mới nhất từ playlist uploads
        # Lưu ý: API search list có thể lọc shorts tốt hơn nếu dùng type=video và q=shorts
        # Nhưng uploads playlist là chính xác nhất cho video mới.
        # Ta sẽ lấy 50 video mới nhất và lọc lấy shorts (giả định shorts có từ khóa shorts hoặc độ dài ngắn)
        # Tuy nhiên, YouTube Shorts link chuẩn nhất là https://www.youtube.com/shorts/VIDEO_ID
        
        playlist_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='snippet,contentDetails',
            maxResults=50
        ).execute()
        
        video_links = []
        for item in playlist_response.get('items', []):
            video_id = item['contentDetails']['videoId']
            # Kiểm tra xem có phải shorts không. 
            # API không có flag 'is_shorts', nhưng ta có thể check video categories hoặc duration.
            # Đơn giản nhất là trả về dạng shorts link.
            video_url = f"https://www.youtube.com/shorts/{video_id}"
            video_links.append(video_url)
            if len(video_links) >= max_videos:
                break
                
        return video_links, channel_title

    except Exception as e:
        if "quotaExceeded" in str(e):
            return "QUOTA_EXCEEDED", "quota_error"
        logger.error(f"Lỗi khi quét API cho {channel_url}: {e}")
        return [], "unknown_channel"

def start_browser_session(api, browser_handler, profile_id):
    """Khởi động profile và kết nối selenium, trả về driver."""
    logger.info(f"Đang khởi động profile {profile_id}...")
    try:
        result = api.start_profile(profile_id)
        
        debugger_address = result.get('http') or result.get('selenium_remote_debug_address') or result.get('remote_debugging_address')
        driver_path = result.get('driver_path')
        
        if not debugger_address:
            # Dự phòng dùng port
            port = result.get('port')
            if port:
                debugger_address = f"127.0.0.1:{port}"
        
        if not debugger_address:
            logger.error(f"Không lấy được địa chỉ debugger từ kết quả khởi động: {result}")
            return None

        logger.info(f"Địa chỉ debugger: {debugger_address}")
        # time.sleep(5) # Removed: Browser class now handles smart waiting
        
        return browser_handler.attach(debugger_address, driver_path=driver_path)
    except Exception as e:
        logger.error(f"Lỗi khởi động/kết nối session: {e}")
        return None

def main():
    # Initialize appropriate Browser API based on config
    browser_type = getattr(config, 'BROWSER_TYPE', 'gemlogin')
    if browser_type == "gpmlogin":
        api = GPMLoginAPI()
        logger.info("Sử dụng trình duyệt: GPM Login")
    else:
        api = GemLoginAPI()
        logger.info("Sử dụng trình duyệt: GemLogin")

    yt_manager = YouTubeManager()
    downloader = Downloader()
    
    # Dọn dẹp file rác từ phiên trước
    downloader.clean_temp_files()

    try:
        # 1. Lấy danh sách Profiles
        logger.info("Đang lấy danh sách profiles GemLogin...")
        profiles = api.get_profiles()
        
        if not profiles:
            logger.error("Không tìm thấy profile nào. Vui lòng tạo profile trong GemLogin trước.")
            return

        # Lấy tối đa số luồng check từ config
        max_check_threads = getattr(config, 'CHECK_THREADS', 1)
        available_profiles = profiles[:max_check_threads]
        
        logger.info(f"Cấu hình: {max_check_threads} luồng Scrape, {config.DOWNLOAD_THREADS} luồng Download.")
        logger.info(f"Sử dụng {len(available_profiles)} profile để quét kênh.")

        # 4. Xử lý danh sách kênh (Chia việc quét theo luồng profile)
        channels_data = yt_manager.get_channels()
        if not channels_data:
            logger.warning("Danh sách kênh trống (danhsachkenh.txt).")
            return

        import concurrent.futures

        def scrape_worker(profile_info, list_of_channels):
            browser_handler = Browser()
            p_id = profile_info.get('id') or profile_info.get('uuid') or profile_info.get('profile_id')
            
            # Ghi nhận profile đang chạy để GiaanTesttool có thể dọn dẹp an toàn
            try:
                with open("active_profiles.tmp", "a") as tmp:
                    tmp.write(f"{p_id}\n")
            except:
                pass

            # Khởi động browser (Chỉ khi cần)
            driver = None
            if getattr(config, 'USE_BROWSER_SCAN', True):
                driver = start_browser_session(api, browser_handler, p_id)
                if not driver:
                    logger.error(f"Không thể khởi động profile {p_id}")
                    return
            else:
                logger.info(f"Đang chạy chế độ API Only. Không khởi động trình duyệt.")

            api_quota_exceeded = False
            try:
                for ch_data in list_of_channels:
                    channel_url = ch_data['url']
                    existing_names = ch_data['names']
                    
                    max_retries = 2
                    for attempt in range(max_retries):
                        try:
                            videos = []
                            scraped_titles = []
                            
                            # 1. API Scan
                            if not api_quota_exceeded and getattr(config, 'USE_API_SCAN', False) and getattr(config, 'YOUTUBE_API_KEY', ''):
                                try:
                                    v_api, t_api = scrape_channel_api(yt_manager, channel_url, config.YOUTUBE_API_KEY)
                                    if v_api == "QUOTA_EXCEEDED":
                                        api_quota_exceeded = True
                                        logger.warning(f"Phát hiện hết Quota API. Tạm dừng quét API cho luồng này.")
                                    elif v_api == "404":
                                        logger.error(f"[Lỗi 404 API] Kênh {channel_url} không tồn tại.")
                                    elif v_api:
                                        videos.extend(v_api)
                                        scraped_titles.append(t_api)
                                except Exception as e:
                                    logger.error(f"Lỗi quét API cho {channel_url}: {e}")

                            # 2. Browser Scan
                            if getattr(config, 'USE_BROWSER_SCAN', True):
                                try:
                                    v_browser, t_browser = scrape_channel(driver, channel_url)
                                    if v_browser == "404":
                                        logger.error(f"[Lỗi 404 Browser] Kênh {channel_url} không tồn tại.")
                                    elif v_browser:
                                        videos.extend(v_browser)
                                        scraped_titles.append(t_browser)
                                except Exception as e:
                                    logger.error(f"Lỗi quét Browser cho {channel_url}: {e}")
                                    if isinstance(e, (WebDriverException, InvalidSessionIdException)):
                                        raise e
                            
                            # Loại bỏ trùng lặp video và lấy tiêu đề đầu tiên hợp lệ
                            videos = list(dict.fromkeys(videos))
                            scraped_title = scraped_titles[0] if scraped_titles else "unknown_channel"

                            # Xác định danh sách tên thư mục
                            final_names = []
                            for existing_name in existing_names:
                                if existing_name:
                                     final_name = existing_name
                                else:
                                     safe_title = sanitize_filename(scraped_title)
                                     if safe_title and safe_title != "unknown_channel":
                                         final_name = f"{safe_title} short"
                                         # Lưu lại tên (Chỉ khi chưa có)
                                         yt_manager.update_channel_name(channel_url, final_name)
                                     else:
                                         final_name = "unknown_channel_short"
                                if final_name not in final_names:
                                    final_names.append(final_name)

                            if videos:
                                logger.info(f"[{','.join(final_names)}] Tổng cộng tìm thấy {len(videos)} video")
                                new_count = yt_manager.add_to_queue(videos, final_names)
                                if new_count > 0:
                                    logger.info(f"[{','.join(final_names)}] Đã thêm {new_count} video mới!")
                                else:
                                    logger.info(f"[{','.join(final_names)}] Kênh không có video nào mới.")
                                for fn in final_names:
                                    yt_manager.record_check_result(fn, new_count)
                            else:
                                logger.warning(f"[{','.join(final_names)}] Không lấy được link video nào.")
                                for fn in final_names:
                                    yt_manager.record_check_result(fn, 0)
                            
                            # Đảm bảo thư mục luôn được tạo để người dùng thấy đủ số lượng folder
                            for fn in final_names:
                                try:
                                    target_path = os.path.join(getattr(config, 'DOWNLOAD_PATH', 'downloads'), fn)
                                    if not os.path.exists(target_path):
                                        os.makedirs(target_path, exist_ok=True)
                                        logger.info(f"Đã tạo thư mục trống cho kênh: {fn}")
                                except Exception as e:
                                    logger.error(f"Lỗi tạo thư mục cho {fn}: {e}")

                            break 
                        except (WebDriverException, InvalidSessionIdException) as e:
                            logger.error(f"Lỗi kết nối trình duyệt (mất session): {e}")
                            # Dừng worker này vì trình duyệt đã chết
                            return
                        except Exception as e:
                            logger.warning(f"Lỗi quét {channel_url} (retry {attempt+1}): {e}")
                            if attempt == max_retries - 1:
                                logger.error(f"Thất bại hoàn toàn khi quét kênh: {channel_url}")
                            time.sleep(2)
            finally:
                browser_handler.close()
                api.stop_profile(p_id)

        # Chia danh sách kênh cho các profile
        def chunkify(lst, n):
            return [lst[i::n] for i in range(n)]
        
        num_workers = min(len(available_profiles), len(channels_data))
        channel_chunks = chunkify(channels_data, num_workers)
        
        logger.info(f"Bắt đầu quét kênh với {num_workers} luồng Scrape...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as scraper_executor:
            scrape_futures = []
            for i in range(num_workers):
                scrape_futures.append(scraper_executor.submit(scrape_worker, available_profiles[i], channel_chunks[i]))
            concurrent.futures.wait(scrape_futures)

        # 6. Tải video từ hàng đợi đa luồng
        logger.info(f"Bắt đầu tải xuống với {config.DOWNLOAD_THREADS} luồng...")
        
        def download_worker():
            while True:
                channel_names, video_url = yt_manager.pop_from_queue()
                if not video_url:
                    if channel_names is None: break
                    else: continue
                
                # Tải vào folder đầu tiên
                main_folder = channel_names[0]
                filename = downloader.download_video(video_url, subfolder=main_folder)
                
                if filename:
                    # Update history/stats cho folder chính
                    yt_manager.update_history(main_folder, video_url)
                    yt_manager.update_daily_stats(main_folder)
                    logger.info(f"[Xong] {video_url} -> {main_folder}")
                    
                    # Copy sang các folder còn lại
                    for other_folder in channel_names[1:]:
                        success_copy = downloader.copy_video(filename, main_folder, other_folder)
                        if success_copy:
                            yt_manager.update_history(other_folder, video_url)
                            yt_manager.update_daily_stats(other_folder)
                            logger.info(f"[Copy] {video_url} -> {other_folder}")
                        else:
                            logger.error(f"[Lỗi Copy] {filename} -> {other_folder}")
                else:
                    logger.error(f"[Lỗi Tải] {video_url} -> {main_folder}")
                    if downloader.last_error and downloader.is_permanent_error(downloader.last_error):
                        logger.warning(f"[Bỏ qua vĩnh viễn] Phát hiện lỗi vĩnh viễn cho {video_url}: {downloader.last_error.strip()}. Đang thêm vào lịch sử để không tải lại.")
                        yt_manager.update_history(main_folder, video_url)
                        for other_folder in channel_names[1:]:
                            yt_manager.update_history(other_folder, video_url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.DOWNLOAD_THREADS) as downloader_executor:
            download_futures = [downloader_executor.submit(download_worker) for _ in range(config.DOWNLOAD_THREADS)]
            concurrent.futures.wait(download_futures)
                
    except Exception as e:
        logger.exception(f"Lỗi nghiêm trọng: {e}")
    finally:
        logger.info("Chương trình kết thúc.")

if __name__ == "__main__":
    main()
