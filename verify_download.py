from youtube_manager import YouTubeManager
from downloader import Downloader
import logging
import sys
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    yt_manager = YouTubeManager()
    downloader = Downloader()

    print("Queue size before:", len(yt_manager._get_queue()))

    # Process just 2 videos for testing
    for _ in range(2):
        video_url = yt_manager.pop_from_queue()
        if not video_url:
            break
        
        # Skip invalid generic link if present
        if video_url == "https://www.youtube.com/shorts/":
            print("Skipping generic link")
            continue

        print(f"Downloading {video_url}...")
        success = downloader.download_video(video_url)
        if success:
            yt_manager.update_history(video_url)
            print("Download success")
        else:
            print("Download failed")

    print("Queue size after:", len(yt_manager._get_queue()))

if __name__ == "__main__":
    main()
