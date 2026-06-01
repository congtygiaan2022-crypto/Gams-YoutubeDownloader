import os
import logging
import threading

class YouTubeManager:
    def __init__(self, channels_file='danhsachkenh.txt', history_file='lichsutai.txt', queue_file='hangdoi.txt', stats_file='thongke_ngay.txt', loi_channels_file='kenh_loi.txt'):
        # Tự động xác định thư mục gốc của project
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Chuyển các file name thành path tuyệt đối nếu là relative
        self.channels_file = self._resolve_path(channels_file)
        self.history_file = self._resolve_path(history_file)
        self.queue_file = self._resolve_path(queue_file)
        self.stats_file = self._resolve_path(stats_file)
        self.loi_channels_file = self._resolve_path(loi_channels_file)
        self.channel_map_file = self._resolve_path('channel_map.txt')
        
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock() # Lock cho safe-thread

    def _resolve_path(self, path):
        if not os.path.isabs(path):
            return os.path.join(self.base_dir, path)
        return path

        # Đảm bảo các file tồn tại
        # (Dùng lock ở đây không quá cần thiết vì init chạy 1 lần, nhưng an toàn hơn)
        with self.lock:
            for f in [self.channels_file, self.history_file, self.queue_file, self.stats_file, self.channel_map_file]:
                if not os.path.exists(f):
                    with open(f, 'w', encoding='utf-8') as file:
                        pass

    def get_channels(self):
        """Đọc danh sách kênh từ file. Trả về list {'url': url, 'names': [name1, name2, ...]}."""
        channels_map = {} # url -> list of names
        with self.lock:
            if os.path.exists(self.channels_file):
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        parts = line.split('|')
                        url = parts[0].strip()
                        name = parts[1].strip() if len(parts) > 1 else None
                        
                        if url not in channels_map:
                            channels_map[url] = []
                        if name and name not in channels_map[url]:
                            channels_map[url].append(name)
                        elif not name and not channels_map[url]:
                            # Trường hợp link không có tên, để [] hoặc [None]
                            pass

        # Chuyển map thành list format cũ nhưng names là list
        result = []
        for url, names in channels_map.items():
            if not names:
                result.append({'url': url, 'names': [None]})
            else:
                result.append({'url': url, 'names': names})
        return result

    def update_channel_name(self, target_url, new_name):
        """Cập nhật tên cho kênh cụ thể trong file (Chỉ khi chưa có tên)."""
        with self.lock:
            # Đọc toàn bộ danh sách hiện tại
            channels = []
            if os.path.exists(self.channels_file):
                 with open(self.channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                         if not line.strip(): continue
                         parts = line.strip().split('|')
                         channels.append({'url': parts[0].strip(), 'name': parts[1].strip() if len(parts)>1 else None})
            
            updated = False
            for ch in channels:
                if ch['url'] == target_url:
                    # CHỈ cập nhật nếu hiện tại chưa có tên
                    if not ch['name'] or ch['name'].strip() == "":
                        ch['name'] = new_name
                        updated = True
                    break
            
            if updated:
                with open(self.channels_file, 'w', encoding='utf-8') as f:
                    for ch in channels:
                        if ch['name']:
                            f.write(f"{ch['url']}|{ch['name']}\n")
                        else:
                            f.write(f"{ch['url']}\n")
                self.logger.info(f"Đã cập nhật tên kênh tự động cho {target_url} thành {new_name}")
            else:
                self.logger.info(f"Giữ nguyên tên kênh thủ công cho {target_url}")

    def get_downloaded_history(self):
        """Đọc danh sách video đã tải. Trả về set các link video."""
        history = set()
        with self.lock:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split('|')
                        if len(parts) >= 2:
                            # Định dạng mới: channel|url hoặc channel|url|timestamp
                            url = parts[1].strip()
                            history.add(url)
                        else:
                            # Định dạng cũ: url
                            history.add(line)
        return history

    def update_history(self, channel_name, video_url):
        """Thêm video vào lịch sử tải kèm tên kênh và thời gian."""
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(f"{channel_name}|{video_url}|{now}\n")

    def add_to_queue(self, video_urls, channel_names):
        """Thêm video mới vào hàng đợi kèm danh sách thông tin kênh (phân tách bằng dấu phẩy)."""
        if isinstance(channel_names, list):
            names_str = ",".join(channel_names)
        else:
            names_str = str(channel_names)

        with self.lock:
            # Đọc history
            history = set()
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        parts = line.split('|')
                        if len(parts) >= 2:
                            history.add(parts[1].strip())
                        else:
                            history.add(line)
            
            # Đọc queue
            existing_queue = set()
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                     for line in f:
                        line = line.strip()
                        if not line: continue
                        if '|' in line:
                            _, url = line.split('|', 1)
                            existing_queue.add(url.strip())
                        else:
                            existing_queue.add(line)

            new_items = []
            for url in video_urls:
                if url not in history and url not in existing_queue:
                    new_items.append(f"{names_str}|{url}")
            
            if new_items:
                with open(self.queue_file, 'a', encoding='utf-8') as f:
                    for item in new_items:
                        f.write(item + '\n')
                self.logger.info(f"Đã thêm {len(new_items)} video mới vào hàng đợi cho {names_str}.")
            
            return len(new_items)

    def _get_queue_urls(self):
        """Helper nội bộ, không dùng lock vì được gọi bởi function đã có lock hoặc cẩn thận."""
        # Hàm này cũ, giờ logic đã gộp vào add_to_queue để an toàn.
        # Giữ lại nếu cần nhưng cẩn thận deadlock.
        urls = set()
        if os.path.exists(self.queue_file):
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '|' in line:
                         _, url = line.strip().split('|', 1)
                         urls.add(url)
        return urls

    def pop_from_queue(self):
        """Lấy và xóa item đầu tiên khỏi hàng đợi. Trả về (channel_names_list, url)."""
        with self.lock:
            if not os.path.exists(self.queue_file):
                return None, None
                
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            if not lines:
                return None, None
            
            item_line = lines[0]
            remaining = lines[1:]
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                for line in remaining:
                    f.write(line + '\n')
            
            if '|' in item_line:
                names_str, url = item_line.split('|', 1)
                names_list = [n.strip() for n in names_str.split(',')]
                return names_list, url
            return None, None

    def update_daily_stats(self, channel_name):
        """Cập nhật số lượng video tải được của kênh trong ngày."""
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        with self.lock:
            stats = {}
            # Đọc stats hiện tại
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        parts = line.split('|')
                        if len(parts) == 3:
                            date_str, ch_name, count_str = parts
                            if date_str not in stats:
                                stats[date_str] = {}
                            stats[date_str][ch_name] = int(count_str)
            
            # Cập nhật
            if today not in stats:
                stats[today] = {}
            stats[today][channel_name] = stats[today].get(channel_name, 0) + 1
            
            # Ghi lại toàn bộ
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                # Sắp xếp theo ngày giảm dần
                for date_str in sorted(stats.keys(), reverse=True):
                    for ch_name, data in stats[date_str].items():
                        if isinstance(data, int):
                            f.write(f"{date_str}|{ch_name}|{data}\n")
                        else:
                            # Nếu là dict (từ record_check_result), ghi đủ thông tin
                            count = data.get('count', 0)
                            msg = data.get('msg', '')
                            f.write(f"{date_str}|{ch_name}|{count}|{msg}\n")

    def record_check_result(self, channel_name, new_count):
        """Ghi nhận kết quả check kênh, đặc biệt xử lý trường hợp không có video mới."""
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        with self.lock:
            all_stats = []
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 2: # Ít nhất có date|name
                            all_stats.append(parts)
            
            # Tách record của hôm nay và lịch sử
            today_record = None
            history = []
            for r in all_stats:
                if r[0] == today and r[1] == channel_name:
                    today_record = r
                else:
                    history.append(r)
            
            if new_count > 0:
                # Nếu có video mới, cập nhật hoặc tạo mới
                if today_record:
                    try:
                        old_count = int(today_record[2])
                        today_record[2] = str(old_count + new_count)
                    except:
                        today_record[2] = str(new_count)
                    # Xóa message cảnh báo nếu có
                    if len(today_record) > 3:
                        today_record = today_record[:3]
                else:
                    today_record = [today, channel_name, str(new_count)]
            else:
                # Nếu không có video mới
                if today_record and len(today_record) >= 3 and int(today_record[2]) > 0:
                    # Nếu hôm nay ĐÃ có video rồi thì không ghi nhận "không có video" nữa
                    # Chỉ cập nhật lịch sử
                    pass
                else:
                    # Tính số ngày cộng dồn
                    consecutive_days = 1
                    last_success_date = ""
                    
                    # Tìm ngày gần nhất có video > 0 trong history
                    # History được duyệt theo thứ tự trong file (thường là mới đến cũ)
                    for r in history:
                        if r[1] == channel_name and len(r) >= 3:
                            try:
                                if int(r[2]) > 0:
                                    last_success_date = r[0]
                                    break
                            except: pass
                    
                    if last_success_date:
                        d1 = datetime.datetime.strptime(last_success_date, "%Y-%m-%d")
                        d2 = datetime.datetime.strptime(today, "%Y-%m-%d")
                        consecutive_days = (d2 - d1).days
                    else:
                        # Nếu không thấy ngày thành công, đếm các ngày đã check 0
                        zero_dates = set()
                        for r in history:
                            if r[1] == channel_name and len(r) >= 3:
                                try:
                                    if int(r[2]) == 0:
                                        zero_dates.add(r[0])
                                except: pass
                        consecutive_days = len(zero_dates) + 1

                    msg = f"Ngày {consecutive_days} không có video mới nào"
                    if consecutive_days >= 5:
                        msg += " . Cảnh báo: Đã lâu rồi chưa up video mới"
                    
                    today_record = [today, channel_name, "0", msg]
            
            # Hợp nhất và ghi lại (giữ thứ tự ban đầu nhưng đưa today_record lên đầu nếu mới)
            final_stats = history
            if today_record:
                # Tìm xem có record cũ của today/channel chưa để thay thế hoặc chèn mới
                found_old = False
                for i, r in enumerate(final_stats):
                    if r[0] == today and r[1] == channel_name:
                        final_stats[i] = today_record
                        found_old = True
                        break
                if not found_old:
                    final_stats.insert(0, today_record)
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                for record in final_stats:
                    f.write("|".join(record) + "\n")

    def get_all_stats(self):
        """Lấy toàn bộ dữ liệu thống kê để hiển thị UI."""
        data = []
        with self.lock:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 3:
                            # date, name, count, msg (optional)
                            data.append(parts)
        return data

    def log_failed_channel(self, url, reason):
        """Ghi nhận kênh bị lỗi hoặc đổi URL."""
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            # Kiểm tra xem URL đã có trong file chưa để tránh trùng lặp
            existing = []
            if os.path.exists(self.loi_channels_file):
                with open(self.loi_channels_file, 'r', encoding='utf-8') as f:
                    existing = [line.split('|')[0].strip() for line in f if line.strip()]
            
            if url not in existing:
                with open(self.loi_channels_file, 'a', encoding='utf-8') as f:
                    f.write(f"{url}|{reason}|{now}\n")
                self.logger.warning(f"Đã log kênh lỗi: {url} - Lý do: {reason}")

    def get_failed_channels(self):
        """Lấy danh sách kênh lỗi."""
        data = []
        with self.lock:
            if os.path.exists(self.loi_channels_file):
                with open(self.loi_channels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 2:
                            data.append(parts)
        return data

    def get_channel_id(self, url):
        """Lấy Channel ID đã lưu cho URL."""
        with self.lock:
            if os.path.exists(self.channel_map_file):
                with open(self.channel_map_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) == 2 and parts[0].strip() == url:
                            return parts[1].strip()
        return None

    def save_channel_id(self, url, channel_id):
        """Lưu mapping giữa URL và Channel ID."""
        with self.lock:
            # Kiểm tra xem đã có chưa
            existing = False
            if os.path.exists(self.channel_map_file):
                with open(self.channel_map_file, 'r', encoding='utf-8') as f:
                    if any(line.startswith(url + '|') for line in f):
                        existing = True
            
            if not existing:
                with open(self.channel_map_file, 'a', encoding='utf-8') as f:
                    f.write(f"{url}|{channel_id}\n")
