import os
import re

def clean_history():
    history_file = 'downloaded_history.txt'
    downloads_dir = 'downloads'
    
    if not os.path.exists(history_file):
        print("No history file found.")
        return

    # Read history
    with open(history_file, 'r', encoding='utf-8') as f:
        history_urls = [line.strip() for line in f if line.strip()]
    
    # Scan existing files
    existing_ids = set()
    for root, dirs, files in os.walk(downloads_dir):
        for file in files:
            # Extract ID from filename: "Title [ID].ext"
            match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', file)
            if match:
                existing_ids.add(match.group(1))
    
    print(f"Found {len(existing_ids)} existing videos on disk.")
    
    new_history = []
    removed_count = 0
    
    for url in history_urls:
        # Extract ID from URL
        # Format: https://www.youtube.com/shorts/ID
        # or https://youtu.be/ID
        # or simple ID
        vid_id = None
        if 'shorts/' in url:
            vid_id = url.split('shorts/')[-1]
        elif 'watch?v=' in url:
            vid_id = url.split('watch?v=')[-1].split('&')[0]
        else:
            vid_id = url # fallback
            
        if vid_id in existing_ids:
            new_history.append(url)
        else:
            removed_count += 1
            # print(f"Removing missing video from history: {url}")

    # Write back
    with open(history_file, 'w', encoding='utf-8') as f:
        for url in new_history:
            f.write(url + '\n')
            
    print(f"Cleaned history. Removed {removed_count} entries that are not on disk.")

if __name__ == "__main__":
    clean_history()
