import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import os
import sys
import threading
import time
import config
import re
import json

# Fix DPI
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class GiaanTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Gams YouTube Download")
        self.root.geometry("1100x800") # Wider horizontal layout
        self.root.configure(bg="#1e1e1e")
        
        # --- Variables ---
        self.run_once = tk.BooleanVar(value=getattr(config, 'RUN_ONCE', True))
        self.loop_count = tk.IntVar(value=getattr(config, 'LOOP_COUNT', 5))
        self.loop_delay = tk.IntVar(value=getattr(config, 'LOOP_DELAY', 60)) # seconds
        self.download_threads = tk.IntVar(value=config.DOWNLOAD_THREADS)
        self.check_threads = tk.IntVar(value=config.CHECK_THREADS)
        self.download_path = tk.StringVar(value=getattr(config, 'DOWNLOAD_PATH', 'downloads'))
        self.use_api_scan = tk.BooleanVar(value=getattr(config, 'USE_API_SCAN', False))
        self.use_browser_scan = tk.BooleanVar(value=getattr(config, 'USE_BROWSER_SCAN', True))
        self.youtube_api_key = tk.StringVar(value=getattr(config, 'YOUTUBE_API_KEY', ''))
        self.cookies_from_browser = tk.StringVar(value=getattr(config, 'COOKIES_FROM_BROWSER', ''))
        self.cookies_file = tk.StringVar(value=getattr(config, 'COOKIES_FILE', 'cookies.txt'))
        self.selected_profile_id = tk.StringVar(value=getattr(config, 'SELECTED_PROFILE_ID', 'None'))
        self.selected_profile_name = tk.StringVar(value=getattr(config, 'SELECTED_PROFILE_NAME', 'None'))
        
        # --- Browser Settings ---
        self.browser_type = tk.StringVar(value=getattr(config, 'BROWSER_TYPE', 'gemlogin'))
        self.gemlogin_api_url = tk.StringVar(value=getattr(config, 'GEMLOGIN_API_URL', 'http://localhost:1010'))
        self.gpmlogin_api_url = tk.StringVar(value=getattr(config, 'GPM_LOGIN_API_URL', 'http://localhost:60064'))
        
        # --- Base Path ---
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.is_running = False
        self.stop_requested = False
        self.current_process = None # Track subprocess
        self.is_dark = True # Default Theme

        # --- Styles ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # --- GUI Layout ---
        self.create_header()
        
        # Create vertical PanedWindow for resizable layout (Drag up/down)
        self.paned_window = tk.PanedWindow(self.root, orient="vertical", bd=0, bg="#333333", sashwidth=7, sashrelief="flat")
        self.paned_window.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        # Upper pane: Configuration container
        self.main_container = ttk.Frame(self.paned_window)
        self.paned_window.add(self.main_container, minsize=450, height=450, stretch="always")
        
        # Left Column: Performance & General configurations
        self.left_col = ttk.Frame(self.main_container)
        self.left_col.pack(side="left", fill="both", expand=True, padx=5)
        
        # Middle Column: Browser connection & Run Mode
        self.mid_col = ttk.Frame(self.main_container)
        self.mid_col.pack(side="left", fill="both", expand=True, padx=5)
        
        # Right Column: Quick Actions & Controls
        self.right_col = ttk.Frame(self.main_container)
        self.right_col.pack(side="left", fill="both", expand=True, padx=5)
        
        # --- Populate Columns ---
        self.create_settings_frame(self.left_col)
        
        self.create_browser_settings_frame(self.mid_col)
        self.create_run_frame(self.mid_col)
        
        self.create_quick_actions_frame(self.right_col)
        self.create_control_frame(self.right_col)
        
        # Lower pane: Tabs/Log container
        self.tabs_container = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tabs_container, minsize=150, height=220, stretch="always")
        
        self.create_tabs_frame()
        
        # Apply initial theme
        self.apply_theme()

    def create_header(self):
        # Header Container
        h_frame = tk.Frame(self.root)
        h_frame.pack(fill="x", pady=(20, 10))
        
        # Title (Centered) - Using grid to center with a side button
        h_frame.grid_columnconfigure(0, weight=1)
        h_frame.grid_columnconfigure(1, weight=0)
        h_frame.grid_columnconfigure(2, weight=1)

        profile_name = getattr(config, 'PROFILE_NAME', 'Mặc định')
        self.header_label = tk.Label(h_frame, text=f"Antigravity Gams Download - Profile: {profile_name}", font=("Segoe UI", 16, "bold"), fg="#4CAF50")
        self.header_label.grid(row=0, column=1)
        
        # Theme Button (Right aligned)
        self.btn_theme = tk.Button(h_frame, text="☀/🌙", font=("Segoe UI", 10), command=self.toggle_theme, relief="flat", cursor="hand2")
        self.btn_theme.grid(row=0, column=2, sticky="e", padx=20)
        
        self.sub_label = tk.Label(self.root, text="YouTube Automation Control Panel", font=("Segoe UI", 10), fg="#888")
        self.sub_label.pack(pady=(0, 20))

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()

    def apply_theme(self):
        # Palettes
        if self.is_dark:
            bg_color = "#1e1e1e"
            fg_color = "#ffffff"
            input_bg = "#333333"
            btn_neutral_bg = "#555555"
        else:
            bg_color = "#f5f5f5"
            fg_color = "#222222"
            input_bg = "#ffffff"
            btn_neutral_bg = "#dddddd"

        # 1. Update Root & Frames
        self.root.configure(bg=bg_color)
        if hasattr(self, 'paned_window'):
            sash_color = "#333333" if self.is_dark else "#cccccc"
            self.paned_window.config(bg=sash_color)
        if hasattr(self, 'paned_window'):
            sash_color = "#333333" if self.is_dark else "#cccccc"
            self.paned_window.config(bg=sash_color)
        
        # Update TK widgets manually if needed (Labels that aren't TTK)
        # However, we used TTK for most structural things, but Header/Sub were TTK Label or TK Label?
        # In this updated code I used TK Label for Header so I can control it better or consistency.
        # Let's check: In create_header I used tk.Label for header_label.
        
        self.header_label.config(bg=bg_color)
        self.sub_label.config(bg=bg_color)
        self.btn_theme.config(bg=btn_neutral_bg, fg=fg_color)
        
        # 2. Update TTK Styles
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        self.style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)
        self.style.configure("Header.TLabel", background=bg_color, foreground="#4CAF50")
        
        # Update Radiobuttons
        # Radio buttons were Created as TK Radiobutton in create_run_frame
        # We need to access them. Best way is to rebuild or iterate.
        # Since I didn't store them in self list, I will iterate root children? No, too risky.
        # I will simpler: Re-configure Radiobuttons using a helper if possible, OR
        # Just update the specific style they use if they were TTK.
        # Actually, let's just make the background of Radiobuttons match.
        
        # Hacky fix for RadioButtons:
        for widget in self.root.winfo_children():
            self._recursive_theme_update(widget, bg_color, fg_color, input_bg, btn_neutral_bg)

    def _recursive_theme_update(self, widget, bg, fg, input_bg, btn_bg):
        try:
            wtype = widget.winfo_class()
            
            # Recursive
            for child in widget.winfo_children():
                self._recursive_theme_update(child, bg, fg, input_bg, btn_bg)
            
            # Apply Colors based on type
            if wtype in ('Frame', 'Labelframe', 'Canvas'):
                widget.config(bg=bg)
            elif wtype == 'Label':
                # Skip Header Label if handled manually, but safe to overwrite bg, keep fg if special?
                # Header Label FG is green, handled separately or we ignore if it has specific color?
                if widget == self.header_label:
                     pass
                elif widget == getattr(self, 'lbl_autosave', None):
                     widget.config(bg=bg)
                else:
                     # Check if it's one of the status labels in channel_rows
                     is_status_lbl = False
                     if hasattr(self, 'channel_rows'):
                         for row in self.channel_rows:
                             if row['status_label'] == widget:
                                 is_status_lbl = True
                                 break
                     if is_status_lbl:
                         widget.config(bg=bg) # Only update background, keep foreground red/green!
                     else:
                         widget.config(bg=bg, fg=fg)
            elif wtype in ('Radiobutton', 'Checkbutton'):
                widget.config(bg=bg, fg=fg, selectcolor=input_bg, activebackground=bg, activeforeground=fg)
            elif wtype == 'Button':
                # Only update "neutral" buttons like Browse or Theme. 
                # Start/Stop/Save/QuickActions have specific colors.
                # Heuristic: If current bg is white/black/grey?
                # Easier: Only update specific buttons we know.
                # But here we made a recursive loop.
                # Let's SKIP buttons in recursive loop to avoid breaking Red/Green/Blue buttons.
                # Only Update "Browse" button? 
                pass 
                
        except:
            pass
            
    def create_settings_frame(self, parent):
        frame = ttk.Labelframe(parent, text="Cấu Hình Hiệu Năng & Lưu Trữ", padding=15)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Threads
        f1 = ttk.Frame(frame)
        f1.pack(fill="x", pady=5)
        ttk.Label(f1, text="Số luồng Download:").pack(side="left")
        ttk.Entry(f1, textvariable=self.download_threads, width=5).pack(side="right")
        
        f2 = ttk.Frame(frame)
        f2.pack(fill="x", pady=5)
        ttk.Label(f2, text="Số luồng Check (Scrape):").pack(side="left")
        ttk.Entry(f2, textvariable=self.check_threads, width=5).pack(side="right")
        
        # Path
        f3 = ttk.Frame(frame)
        f3.pack(fill="x", pady=5)
        ttk.Label(f3, text="Thư mục lưu video:").pack(anchor="w")
        
        f3_inner = ttk.Frame(f3)
        f3_inner.pack(fill="x", pady=2)
        ttk.Entry(f3_inner, textvariable=self.download_path).pack(side="left", fill="x", expand=True)
        tk.Button(f3_inner, text="Chọn...", command=self.browse_folder, bg="#555", fg="white", relief="flat").pack(side="right", padx=(5, 0))

        # API & Browser Scan Options
        f4 = ttk.Frame(frame)
        f4.pack(fill="x", pady=5)
        self.cb_api = tk.Checkbutton(f4, text="Quét bằng API", variable=self.use_api_scan, bg="#1e1e1e", fg="white", selectcolor="#333", activebackground="#1e1e1e", activeforeground="white")
        self.cb_api.pack(side="left")
        self.cb_browser = tk.Checkbutton(f4, text="Quét bằng Browser", variable=self.use_browser_scan, bg="#1e1e1e", fg="white", selectcolor="#333", activebackground="#1e1e1e", activeforeground="white")
        self.cb_browser.pack(side="left", padx=10)

        # API Key
        f5 = ttk.Frame(frame)
        f5.pack(fill="x", pady=5)
        ttk.Label(f5, text="YouTube API Key:").pack(side="left")
        ttk.Entry(f5, textvariable=self.youtube_api_key).pack(side="left", fill="x", expand=True, padx=(5, 5))
        tk.Button(f5, text="Kiểm tra API", command=self.check_api_key, bg="#FF9800", fg="white", relief="flat", font=("Segoe UI", 9)).pack(side="right")

        # Cookies Settings
        f6 = ttk.Frame(frame)
        f6.pack(fill="x", pady=5)
        ttk.Label(f6, text="Cookies từ Browser (chrome/firefox/edge...):").pack(side="left")
        ttk.Entry(f6, textvariable=self.cookies_from_browser, width=15).pack(side="right")
        
        f7 = ttk.Frame(frame)
        f7.pack(fill="x", pady=5)
        ttk.Label(f7, text="File Cookies (tên file txt):").pack(side="left")
        ttk.Entry(f7, textvariable=self.cookies_file, width=15).pack(side="right")

        # Save Button
        btn_save = tk.Button(frame, text="Lưu Cấu Hình", bg="#2196F3", fg="white", relief="flat", command=self.save_config)
        btn_save.pack(fill="x", pady=(10, 0))

    def create_browser_settings_frame(self, parent):
        frame = ttk.Labelframe(parent, text="Cấu Hình Trình Duyệt (Anti-detect)", padding=15)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Selection
        f_type = ttk.Frame(frame)
        f_type.pack(fill="x", pady=5)
        ttk.Label(f_type, text="Loại Trình Duyệt:").pack(side="left")
        
        rb_gem = tk.Radiobutton(f_type, text="GemLogin", variable=self.browser_type, value="gemlogin", bg="#1e1e1e", fg="white", selectcolor="#333", activebackground="#1e1e1e", activeforeground="white", command=self.update_browser_ui)
        rb_gem.pack(side="left", padx=10)
        
        rb_gpm = tk.Radiobutton(f_type, text="GPM Login", variable=self.browser_type, value="gpmlogin", bg="#1e1e1e", fg="white", selectcolor="#333", activebackground="#1e1e1e", activeforeground="white", command=self.update_browser_ui)
        rb_gpm.pack(side="left")

        # API URL Container
        self.api_url_frame = ttk.Frame(frame)
        self.api_url_frame.pack(fill="x", pady=5)
        
        ttk.Label(self.api_url_frame, text="API URL:").pack(side="left")
        
        self.ent_api_url = ttk.Entry(self.api_url_frame)
        self.ent_api_url.pack(side="left", fill="x", expand=True, padx=5)
        
        btn_check = tk.Button(frame, text="Kiểm tra kết nối Browser API", command=self.check_browser_api, bg="#FF9800", fg="white", relief="flat", font=("Segoe UI", 9))
        btn_check.pack(fill="x", pady=(5, 5))

        # Khung chọn Profile
        f_profile = ttk.Frame(frame)
        f_profile.pack(fill="x", pady=5)
        
        ttk.Label(f_profile, text="Chọn Profile:").pack(side="left")
        
        self.cb_profile = ttk.Combobox(f_profile, state="readonly")
        self.cb_profile.pack(side="left", fill="x", expand=True, padx=5)
        self.cb_profile.bind("<<ComboboxSelected>>", self.on_profile_selected)
        
        self.btn_load_profiles = tk.Button(f_profile, text="Tải Profiles", command=self.load_profiles, bg="#9C27B0", fg="white", relief="flat", font=("Segoe UI", 9))
        self.btn_load_profiles.pack(side="right")
        
        # Thiết lập giá trị Combobox ban đầu
        saved_id = getattr(config, 'SELECTED_PROFILE_ID', 'None')
        saved_name = getattr(config, 'SELECTED_PROFILE_NAME', 'None')
        if saved_id != "None" and saved_name != "None":
            self.cb_profile['values'] = [f"{saved_name} ({saved_id})", "Mặc định (Dùng luồng)"]
            self.cb_profile.set(f"{saved_name} ({saved_id})")
        else:
            self.cb_profile['values'] = ["Mặc định (Dùng luồng)"]
            self.cb_profile.set("Mặc định (Dùng luồng)")
        
        self.update_browser_ui()

    def update_browser_ui(self):
        """Cập nhật Entry hiển thị đúng API URL dựa trên loại trình duyệt."""
        if self.browser_type.get() == "gemlogin":
            self.ent_api_url.config(textvariable=self.gemlogin_api_url)
        else:
            self.ent_api_url.config(textvariable=self.gpmlogin_api_url)
            
        # Reset lựa chọn profile khi đổi loại trình duyệt để tránh lỗi
        if hasattr(self, 'cb_profile'):
            self.cb_profile['values'] = ["Mặc định (Dùng luồng)"]
            self.cb_profile.set("Mặc định (Dùng luồng)")
            self.selected_profile_id.set("None")
            self.selected_profile_name.set("None")

    def check_browser_api(self):
        """Kiểm tra kết nối API của trình duyệt đã chọn."""
        b_type = self.browser_type.get()
        api_url = self.gemlogin_api_url.get() if b_type == "gemlogin" else self.gpmlogin_api_url.get()
        
        def run_check():
            try:
                import requests
                # Thử endpoint lấy profiles làm mẫu test connection
                endpoint = "/api/profiles" if b_type == "gemlogin" else "/api/v3/profiles"
                test_url = f"{api_url}{endpoint}"
                self.log(f"Đang kiểm tra kết nối {b_type} tại {test_url}...")
                
                response = requests.get(test_url, timeout=5)
                if response.status_code == 200:
                    self.root.after(0, lambda: messagebox.showinfo("Thành công", f"Kết nối tới {b_type} thành công!"))
                    self.log(f"Kết nối {b_type} OK.")
                else:
                    self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối thất bại. Status code: {response.status_code}"))
                    self.log(f"Kết nối {b_type} thất bại: HTTP {response.status_code}")
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể kết nối tới {b_type}: {e}"))
                self.log(f"Lỗi kết nối {b_type}: {e}")

        threading.Thread(target=run_check, daemon=True).start()

    def load_profiles(self):
        """Tải danh sách profiles từ browser API và cập nhật Combobox."""
        b_type = self.browser_type.get()
        api_url = self.gemlogin_api_url.get() if b_type == "gemlogin" else self.gpmlogin_api_url.get()
        
        def fetch():
            try:
                import requests
                endpoint = "/api/profiles" if b_type == "gemlogin" else "/api/v3/profiles"
                url = f"{api_url}{endpoint}"
                self.log(f"Đang tải danh sách profile từ {url}...")
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    profiles = []
                    if isinstance(data, list):
                        profiles = data
                    elif isinstance(data, dict):
                        profiles = data.get('data', [])
                    
                    self.root.after(0, lambda: self.update_profiles_list(profiles))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể lấy danh sách profile. HTTP {response.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Lỗi kết nối khi tải profile: {e}"))
                self.log(f"Lỗi tải profile: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    def update_profiles_list(self, profiles):
        options = ["Mặc định (Dùng luồng)"]
        for p in profiles:
            p_id = p.get('id') or p.get('uuid') or p.get('profile_id')
            p_name = p.get('name') or p.get('title') or p.get('profile_name') or p_id
            options.append(f"{p_name} ({p_id})")
        
        self.cb_profile['values'] = options
        
        saved_id = self.selected_profile_id.get()
        found = False
        if saved_id != "None":
            for opt in options:
                if f"({saved_id})" in opt:
                    self.cb_profile.set(opt)
                    found = True
                    break
        
        if not found:
            self.cb_profile.current(0)
            self.selected_profile_id.set("None")
            self.selected_profile_name.set("None")
            
        self.log(f"Đã tải {len(profiles)} profiles thành công.")

    def on_profile_selected(self, event=None):
        selected_val = self.cb_profile.get()
        if selected_val == "Mặc định (Dùng luồng)":
            self.selected_profile_id.set("None")
            self.selected_profile_name.set("None")
            self.log("Đã chọn: Mặc định (Tự động lấy theo số luồng)")
        else:
            match = re.search(r'^(.*)\s\(([^()]+)\)$', selected_val)
            if match:
                name = match.group(1).strip()
                p_id = match.group(2).strip()
                self.selected_profile_id.set(p_id)
                self.selected_profile_name.set(name)
                self.log(f"Đã chọn profile: {name} (ID: {p_id})")
            else:
                self.selected_profile_id.set("None")
                self.selected_profile_name.set("None")

    def create_quick_actions_frame(self, parent):
        frame = ttk.Labelframe(parent, text="Truy Cập Nhanh", padding=15)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_channels = tk.Button(frame, text="📁 Mở File Kênh", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("danhsachkenh.txt"), font=("Segoe UI", 9, "bold"))
        btn_channels.pack(fill="x", pady=4)
        
        btn_history = tk.Button(frame, text="📜 Mở Log Tải", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("lichsutai.txt"), font=("Segoe UI", 9, "bold"))
        btn_history.pack(fill="x", pady=4)
        
        btn_folder = tk.Button(frame, text="📂 Mở Thư Mục Video", bg="#607D8B", fg="white", relief="flat", command=self.open_download_folder, font=("Segoe UI", 9, "bold"))
        btn_folder.pack(fill="x", pady=4)

        btn_view_stats = tk.Button(frame, text="📊 Kiểm tra Video & Log", bg="#4CAF50", fg="white", relief="flat", command=self.show_stats_tab, font=("Segoe UI", 9, "bold"))
        btn_view_stats.pack(fill="x", pady=4)
        
        btn_backup = tk.Button(frame, text="💾 Sao Lưu Profile", bg="#2196F3", fg="white", relief="flat", command=self.backup_current_profile_ui, font=("Segoe UI", 9, "bold"))
        btn_backup.pack(fill="x", pady=4)
        
        btn_restore = tk.Button(frame, text="📥 Khôi Phục Profile", bg="#FF9800", fg="white", relief="flat", command=self.restore_current_profile_ui, font=("Segoe UI", 9, "bold"))
        btn_restore.pack(fill="x", pady=4)

    def show_stats_tab(self):
        """Chuyển sang tab Thống kê và làm mới dữ liệu."""
        self.notebook.select(1)
        self.refresh_stats()

    def open_file(self, filename):
        try:
            # Resolve relative path
            profile_dir = getattr(config, 'PROFILE_DIR', None)
            if profile_dir:
                full_path = os.path.join(self.base_dir, profile_dir, filename)
            else:
                full_path = os.path.join(self.base_dir, filename)
            
            # Ensure folder exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if not os.path.exists(full_path):
                 # Create if not exists so it opens blank
                 with open(full_path, 'w', encoding='utf-8') as f: pass
            os.startfile(full_path)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def backup_current_profile_ui(self):
        import zipfile
        import json
        from datetime import datetime
        
        profile_id = getattr(config, 'PROFILE_ID', None)
        profile_name = getattr(config, 'PROFILE_NAME', 'Mặc định')
        profile_dir = getattr(config, 'PROFILE_DIR', None)
        
        if not profile_id or not profile_dir:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy profile hoạt động để sao lưu.")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_profile_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        default_filename = f"backup_{safe_profile_name}_{timestamp}.zip"
        
        backup_dir = os.path.join(self.base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        file_path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu bản sao lưu",
            initialdir=backup_dir,
            initialfile=default_filename,
            filetypes=[("ZIP files", "*.zip")],
            defaultextension=".zip"
        )
        
        if not file_path:
            return
            
        try:
            full_profile_dir = os.path.join(self.base_dir, profile_dir)
            files_to_backup = [
                "config.json",
                "danhsachkenh.txt",
                "lichsutai.txt",
                "hangdoi.txt",
                "thongke_ngay.txt",
                "channel_map.txt",
                "cookies.txt",
                "kenh_loi.txt"
            ]
            
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                # Add files
                for fname in files_to_backup:
                    fpath = os.path.join(full_profile_dir, fname)
                    if os.path.exists(fpath):
                        zip_ref.write(fpath, fname)
                
                # Add metadata
                metadata = {
                    "profile_id": profile_id,
                    "profile_name": profile_name,
                    "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "tool": "Gams Youtube Downloader"
                }
                zip_ref.writestr("metadata.json", json.dumps(metadata, indent=4, ensure_ascii=False))
                
            self.log(f"Đã sao lưu Profile '{profile_name}' thành công vào: {file_path}")
            messagebox.showinfo("Thành công", f"Đã sao lưu dữ liệu Profile '{profile_name}' thành công!")
        except Exception as e:
            self.log(f"Lỗi sao lưu: {e}")
            messagebox.showerror("Lỗi", f"Không thể sao lưu dữ liệu: {e}")

    def restore_current_profile_ui(self):
        import zipfile
        import json
        
        profile_id = getattr(config, 'PROFILE_ID', None)
        profile_name = getattr(config, 'PROFILE_NAME', 'Mặc định')
        profile_dir = getattr(config, 'PROFILE_DIR', None)
        
        if not profile_id or not profile_dir:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy profile hoạt động để khôi phục.")
            return
            
        backup_dir = os.path.join(self.base_dir, "backups")
        file_path = filedialog.askopenfilename(
            title="Chọn tệp sao lưu để khôi phục (.zip)",
            initialdir=backup_dir,
            filetypes=[("ZIP files", "*.zip")]
        )
        
        if not file_path:
            return
            
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if "config.json" not in file_list:
                    messagebox.showerror("Lỗi", "Tệp sao lưu không hợp lệ (Không tìm thấy config.json).")
                    return
                    
                meta_info = ""
                if "metadata.json" in file_list:
                    try:
                        metadata = json.loads(zip_ref.read("metadata.json").decode('utf-8'))
                        meta_info = f"\n- Profile gốc: {metadata.get('profile_name')}\n- Thời gian sao lưu: {metadata.get('backup_time')}"
                    except:
                        pass
                
                confirm = messagebox.askyesno(
                    "Xác nhận khôi phục",
                    f"Bạn có chắc chắn muốn khôi phục dữ liệu từ tệp sao lưu này?{meta_info}\n\n⚠️ HÀNH ĐỘNG NÀY SẼ GHI ĐÈ TOÀN BỘ cấu hình và dữ liệu hiện tại của Profile '{profile_name}'!"
                )
                
                if not confirm:
                    return
                    
                full_profile_dir = os.path.join(self.base_dir, profile_dir)
                os.makedirs(full_profile_dir, exist_ok=True)
                
                # Extract and overwrite files
                for member in file_list:
                    if member == "metadata.json":
                        continue
                    # Read content and write to profile dir
                    target_path = os.path.join(full_profile_dir, member)
                    # Verify target_path is inside full_profile_dir (avoid directory traversal vulnerability)
                    real_target = os.path.abspath(target_path)
                    real_base = os.path.abspath(full_profile_dir)
                    if real_target.startswith(real_base):
                        with open(target_path, 'wb') as f:
                            f.write(zip_ref.read(member))
                            
            self.log(f"Đã khôi phục Profile '{profile_name}' thành công từ: {file_path}")
            
            # Reload configuration from the restored config.json
            profile_config_path = os.path.join(full_profile_dir, "config.json")
            if os.path.exists(profile_config_path):
                try:
                    with open(profile_config_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    for k, v in cfg_data.items():
                        setattr(config, k, v)
                except Exception as e:
                    self.log(f"Lỗi load lại config: {e}")
            
            # Resolve path cookies cho profile
            if config.COOKIES_FILE and not os.path.isabs(config.COOKIES_FILE):
                config.COOKIES_FILE = os.path.join(config.PROFILE_DIR, config.COOKIES_FILE)
            
            # Update GUI variables to match the restored config
            self.run_once.set(getattr(config, 'RUN_ONCE', True))
            self.loop_count.set(getattr(config, 'LOOP_COUNT', 5))
            self.loop_delay.set(getattr(config, 'LOOP_DELAY', 60))
            self.download_threads.set(getattr(config, 'DOWNLOAD_THREADS', 3))
            self.check_threads.set(getattr(config, 'CHECK_THREADS', 1))
            self.download_path.set(getattr(config, 'DOWNLOAD_PATH', 'downloads'))
            self.use_api_scan.set(getattr(config, 'USE_API_SCAN', False))
            self.use_browser_scan.set(getattr(config, 'USE_BROWSER_SCAN', True))
            self.youtube_api_key.set(getattr(config, 'YOUTUBE_API_KEY', ''))
            self.cookies_from_browser.set(getattr(config, 'COOKIES_FROM_BROWSER', ''))
            self.cookies_file.set(getattr(config, 'COOKIES_FILE', 'cookies.txt'))
            self.browser_type.set(getattr(config, 'BROWSER_TYPE', 'gemlogin'))
            self.gemlogin_api_url.set(getattr(config, 'GEMLOGIN_API_URL', 'http://localhost:1010'))
            self.gpmlogin_api_url.set(getattr(config, 'GPM_LOGIN_API_URL', 'http://localhost:60064'))
            self.selected_profile_id.set(getattr(config, 'SELECTED_PROFILE_ID', 'None'))
            self.selected_profile_name.set(getattr(config, 'SELECTED_PROFILE_NAME', 'None'))
            
            # Reload UI panels
            self.refresh_stats()
            self.refresh_error_channels()
            self.refresh_channels_tab()
            
            messagebox.showinfo("Thành công", f"Đã khôi phục dữ liệu Profile '{profile_name}' thành công!")
        except Exception as e:
            self.log(f"Lỗi khôi phục: {e}")
            messagebox.showerror("Lỗi", f"Không thể khôi phục dữ liệu: {e}")

    def open_download_folder(self):
        try:
            path = self.download_path.get()
            # If path is relative, make it absolute
            if not os.path.isabs(path):
                path = os.path.join(self.base_dir, path)

            if not os.path.exists(path):
                os.makedirs(path)
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_path.set(folder_selected)

    def create_run_frame(self, parent):
        frame = ttk.Labelframe(parent, text="Chế Độ Chạy", padding=15)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Radio
        rb1 = tk.Radiobutton(frame, text="Chạy 1 lần (Single Run)", variable=self.run_once, value=True, bg="#1e1e1e", fg="white", selectcolor="#2b2b2b", activebackground="#1e1e1e", activeforeground="white")
        rb1.pack(anchor="w")
        
        rb2 = tk.Radiobutton(frame, text="Chạy vòng lặp (Loop)", variable=self.run_once, value=False, bg="#1e1e1e", fg="white", selectcolor="#2b2b2b", activebackground="#1e1e1e", activeforeground="white")
        rb2.pack(anchor="w", pady=(5, 0))
        
        # Loop Options
        opts = ttk.Frame(frame)
        opts.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(opts, text="Số vòng lặp:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(opts, textvariable=self.loop_count, width=5).grid(row=0, column=1)
        
        ttk.Label(opts, text="Delay (giây):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(opts, textvariable=self.loop_delay, width=5).grid(row=1, column=1)

    def create_control_frame(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.btn_start = tk.Button(frame, text="▶ BẮT ĐẦU", bg="#4CAF50", fg="white", font=("Segoe UI", 12, "bold"), height=2, relief="flat", command=self.start_process)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_stop = tk.Button(frame, text="■ DỪNG", bg="#f44336", fg="white", font=("Segoe UI", 12, "bold"), height=2, relief="flat", command=self.stop_process, state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Reset small button
        btn_reset = tk.Button(frame, text="↻ Xóa Dữ Liệu (Reset)", bg="#FF9800", fg="white", relief="flat", command=self.run_reset)
        btn_reset.pack(fill="x", pady=(10, 0))

    def create_tabs_frame(self):
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.tabs_container)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Tab 0: Danh Sách Kênh
        self.channels_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.channels_tab, text=" 📋 Danh Sách Kênh ")
        self.create_channels_tab_ui()

        # Tab 1: Console Log
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text=" Log Hoạt Động ")
        
        self.console = tk.Text(self.log_tab, height=5, bg="#000", fg="#0f0", font=("Consolas", 9), state="disabled")
        self.console.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 2: Statistics
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text=" Thống kê & Lịch sử ")
        
        # Tab 3: Error Channels
        self.error_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.error_tab, text=" Danh Sách Kênh Lỗi ")
        
        # --- Tab 3: Error Channels setup ---
        err_f = ttk.Frame(self.error_tab)
        err_f.pack(fill="x", padx=5, pady=5)
        
        tk.Button(err_f, text="↻ Làm mới kênh lỗi", bg="#FF5722", fg="white", relief="flat", command=self.refresh_error_channels, font=("Segoe UI", 9)).pack(side="left")
        tk.Button(err_f, text="📁 Mở File Kênh Lỗi", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("kenh_loi.txt"), font=("Segoe UI", 9)).pack(side="right")

        main_err_f = ttk.Frame(self.error_tab)
        main_err_f.pack(fill="both", expand=True, padx=5, pady=5)

        err_scroll = ttk.Scrollbar(main_err_f)
        err_scroll.pack(side="right", fill="y")

        err_columns = ("stt", "url", "reason", "time")
        self.err_tree = ttk.Treeview(main_err_f, columns=err_columns, show="headings", yscrollcommand=err_scroll.set)
        
        self.err_tree.heading("stt", text="STT")
        self.err_tree.heading("url", text="URL Kênh")
        self.err_tree.heading("reason", text="Lý do lỗi / Trạng thái")
        self.err_tree.heading("time", text="Thời gian phát hiện")

        self.err_tree.column("stt", width=50, anchor="center")
        self.err_tree.column("url", width=450)
        self.err_tree.column("reason", width=250)
        self.err_tree.column("time", width=150, anchor="center")

        self.err_tree.pack(fill="both", expand=True)
        err_scroll.config(command=self.err_tree.yview)
        
        # Tools in Stats Tab
        tool_f = ttk.Frame(self.stats_tab)
        tool_f.pack(fill="x", padx=5, pady=5)
        
        tk.Button(tool_f, text="↻ Làm mới dữ liệu", bg="#FF5722", fg="white", relief="flat", command=self.refresh_stats, font=("Segoe UI", 9)).pack(side="left")
        tk.Button(tool_f, text="📁 Mở File Thống Kê", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("thongke_ngay.txt"), font=("Segoe UI", 9)).pack(side="right")

        # Table (The "Box")
        main_f = ttk.Frame(self.stats_tab)
        main_f.pack(fill="both", expand=True, padx=5, pady=5)

        tree_scroll = ttk.Scrollbar(main_f)
        tree_scroll.pack(side="right", fill="y")

        columns = ("stt", "date", "channel", "count", "warning")
        self.tree = ttk.Treeview(main_f, columns=columns, show="headings", yscrollcommand=tree_scroll.set)
        
        self.tree.heading("stt", text="STT")
        self.tree.heading("date", text="Ngày")
        self.tree.heading("channel", text="Tên Kênh")
        self.tree.heading("count", text="Số Video")
        self.tree.heading("warning", text="Cảnh báo / Trạng thái")

        self.tree.column("stt", width=50, anchor="center")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("channel", width=200)
        self.tree.column("count", width=100, anchor="center")
        self.tree.column("warning", width=450)

        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Tags for coloring
        self.tree.tag_configure("warning", foreground="red")
        self.tree.tag_configure("zero", foreground="#ff9800")
        
        self.refresh_stats()

    def on_tab_changed(self, event):
        """Tự động refresh khi người dùng click vào tab."""
        try:
            tab_id = self.notebook.select()
            tab_text = self.notebook.tab(tab_id, "text").strip()
            if "Thống kê" in tab_text:
                self.refresh_stats()
            elif "Kênh Lỗi" in tab_text:
                self.refresh_error_channels()
            elif "Danh Sách Kênh" in tab_text:
                self.refresh_channels_tab()
        except Exception as e:
            pass

    def refresh_stats(self):
        """Làm mới dữ liệu trong bảng thống kê."""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            from youtube_manager import YouTubeManager
            yt_manager = YouTubeManager()
            
            stats = yt_manager.get_all_stats()
            for i, row in enumerate(stats, 1):
                date = row[0]
                name = row[1]
                count = row[2]
                msg = row[3] if len(row) > 3 else ""
                
                tags = ()
                if "Cảnh báo" in msg:
                    tags = ("warning",)
                elif count == "0":
                    tags = ("zero",)
                
                self.tree.insert("", "end", values=(i, date, name, count, msg), tags=tags)
        except Exception as e:
            self.log(f"Lỗi refresh stats: {e}")

    def refresh_error_channels(self):
        """Làm mới dữ liệu trong bảng kênh lỗi."""
        try:
            for item in self.err_tree.get_children():
                self.err_tree.delete(item)
            
            from youtube_manager import YouTubeManager
            yt_manager = YouTubeManager()
            
            error_channels = yt_manager.get_failed_channels()
            for i, row in enumerate(error_channels, 1):
                url = row[0]
                reason = row[1]
                timestamp = row[2] if len(row) > 2 else ""
                
                self.err_tree.insert("", "end", values=(i, url, reason, timestamp))
        except Exception as e:
            self.log(f"Lỗi refresh kênh lỗi: {e}")

    def log(self, message):
        if hasattr(self, 'console'):
            self.console.config(state="normal")
            self.console.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.console.see("end")
            self.console.config(state="disabled")

    def save_config(self):
        try:
            profile_id = getattr(config, 'PROFILE_ID', None)
            if profile_id:
                # Save to JSON
                profile_dir = getattr(config, 'PROFILE_DIR', None)
                json_path = os.path.join(profile_dir, "config.json")
                
                # Build dict from variables
                cfg_data = {
                    "BROWSER_TYPE": self.browser_type.get(),
                    "GEMLOGIN_API_URL": self.gemlogin_api_url.get(),
                    "GPM_LOGIN_API_URL": self.gpmlogin_api_url.get(),
                    "DOWNLOAD_THREADS": self.download_threads.get(),
                    "CHECK_THREADS": self.check_threads.get(),
                    "RUN_ONCE": self.run_once.get(),
                    "LOOP_COUNT": self.loop_count.get(),
                    "LOOP_DELAY": self.loop_delay.get(),
                    "USE_API_SCAN": self.use_api_scan.get(),
                    "USE_BROWSER_SCAN": self.use_browser_scan.get(),
                    "YOUTUBE_API_KEY": self.youtube_api_key.get(),
                    "DOWNLOAD_PATH": self.download_path.get(),
                    "COOKIES_FROM_BROWSER": self.cookies_from_browser.get(),
                    "COOKIES_FILE": self.cookies_file.get(),
                    "SELECTED_PROFILE_ID": self.selected_profile_id.get(),
                    "SELECTED_PROFILE_NAME": self.selected_profile_name.get(),
                    "HEADLESS_LOCAL_CHROME": getattr(config, 'HEADLESS_LOCAL_CHROME', False)
                }
                
                # Overwrite config module properties dynamically in memory
                for k, v in cfg_data.items():
                    setattr(config, k, v)
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(cfg_data, f, indent=4, ensure_ascii=False)
                
                self.log("Đã lưu cấu hình profile thành công!")
                messagebox.showinfo("Thành công", "Đã lưu cấu hình profile mới!")
                return
            
            # Read config file
            config_path = os.path.join(self.base_dir, "config.py")
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace logic
            content = re.sub(r'DOWNLOAD_THREADS = \d+', f'DOWNLOAD_THREADS = {self.download_threads.get()}', content)
            content = re.sub(r'CHECK_THREADS = \d+', f'CHECK_THREADS = {self.check_threads.get()}', content)
            
            # Loop settings persistence
            if 'RUN_ONCE' in content:
                content = re.sub(r'RUN_ONCE = (True|False)', f'RUN_ONCE = {self.run_once.get()}', content)
            else:
                content += f'\nRUN_ONCE = {self.run_once.get()}'

            if 'LOOP_COUNT' in content:
                content = re.sub(r'LOOP_COUNT = \d+', f'LOOP_COUNT = {self.loop_count.get()}', content)
            else:
                content += f'\nLOOP_COUNT = {self.loop_count.get()}'
                
            if 'LOOP_DELAY' in content:
                content = re.sub(r'LOOP_DELAY = \d+', f'LOOP_DELAY = {self.loop_delay.get()}', content)
            else:
                content += f'\nLOOP_DELAY = {self.loop_delay.get()}'

            # Handle Path
            current_path = self.download_path.get().replace('\\', '\\\\') # Escape backslashes for python string
            if 'DOWNLOAD_PATH' in content:
                content = re.sub(r'DOWNLOAD_PATH = ".*?"', f'DOWNLOAD_PATH = "{current_path}"', content)
            else:
                content += f'\nDOWNLOAD_PATH = "{current_path}"'

            # --- New API Scanning Settings ---
            def update_or_add(key, value, is_str=False):
                nonlocal content
                pattern = f'{key} = .*'
                replacement = f'{key} = "{value}"' if is_str else f'{key} = {value}'
                if key in content:
                    content = re.sub(pattern, replacement, content)
                else:
                    content += f'\n{replacement}'

            update_or_add('USE_API_SCAN', self.use_api_scan.get())
            update_or_add('USE_BROWSER_SCAN', self.use_browser_scan.get())
            update_or_add('YOUTUBE_API_KEY', self.youtube_api_key.get(), is_str=True)
            
            val_browser = self.cookies_from_browser.get().strip()
            if not val_browser or val_browser.lower() == "none":
                update_or_add('COOKIES_FROM_BROWSER', 'None')
            else:
                update_or_add('COOKIES_FROM_BROWSER', val_browser, is_str=True)
                
            val_file = self.cookies_file.get().strip()
            if not val_file or val_file.lower() == "none":
                update_or_add('COOKIES_FILE', 'None')
            else:
                update_or_add('COOKIES_FILE', val_file, is_str=True)
            
            # Browser configuration
            update_or_add('BROWSER_TYPE', self.browser_type.get(), is_str=True)
            update_or_add('GEMLOGIN_API_URL', self.gemlogin_api_url.get(), is_str=True)
            update_or_add('GPM_LOGIN_API_URL', self.gpmlogin_api_url.get(), is_str=True)
            update_or_add('SELECTED_PROFILE_ID', self.selected_profile_id.get(), is_str=True)
            update_or_add('SELECTED_PROFILE_NAME', self.selected_profile_name.get().replace('"', '\\"'), is_str=True)
            
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + '\n')
                
            # Reload module logic not needed if we run subprocess
            self.log("Đã lưu cấu hình thành công!")
            messagebox.showinfo("Thành công", "Đã lưu cấu hình mới!")
        except Exception as e:
            self.log(f"Lỗi lưu cấu hình: {e}")

    def start_process(self):
        if self.is_running: return
        self.is_running = True
        self.stop_requested = False
        self.btn_start.config(state="disabled", bg="#666")
        self.btn_stop.config(state="normal", bg="#f44336")
        
        # Run in thread
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        # Dọn dẹp tiến trình main.py cũ trước khi chạy vòng lặp mới
        self.clean_orphaned_bot_processes()
        
        loops = 1 if self.run_once.get() else self.loop_count.get()
        delay = self.loop_delay.get()
        
        for i in range(loops):
            if self.stop_requested: break
            
            self.log(f"--- Bắt đầu vòng lặp {i+1}/{loops} ---")
            
            try:
                main_script = os.path.join(self.base_dir, "main.py")
                
                # Start process and track it
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                args = ["python", "-u", main_script]
                profile_id = getattr(config, 'PROFILE_ID', None)
                if profile_id:
                    args.extend(["--profile", str(profile_id)])
                    env["PROFILE_ID"] = str(profile_id)
                
                self.current_process = subprocess.Popen(
                    args,
                    cwd=self.base_dir, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, # Merge stderr into stdout to prevent deadlock
                    text=True, 
                    encoding='utf-8',
                    errors='replace', # Prevent crash on non-utf8 chars
                    env=env, # Force UTF8 encoding for the process
                    creationflags=subprocess.CREATE_NO_WINDOW # Optional: Hide console window
                )
                
                # Stream output
                while True:
                    if self.stop_requested: # Check flag to kill immediately
                        if self.current_process.poll() is None:
                            self.current_process.terminate()
                        break

                    # Read line-by-line unbuffered
                    line = self.current_process.stdout.readline()
                    status = self.current_process.poll()
                    
                    if not line and status is not None:
                        break
                    if line:
                        self.log(line.strip())
                
                self.current_process.wait()
                self.current_process = None # Clear after finish
                
            except Exception as e:
                self.log(f"Lỗi chạy script: {e}")

            # Cleanup
            self.log("Đang dọn dẹp (Cleanup)...")
            self.aggressive_cleanup()
            
            if i < loops - 1:
                if self.stop_requested: break
                self.log(f"Đang chờ {delay} giây trước vòng lặp mới...")
                # Sleep in chunks to allow interruption
                for s in range(delay):
                    if self.stop_requested: break
                    time.sleep(1)
            
        self.is_running = False
        self.log("--- Hoàn tất ---")
        self.root.after(0, self.reset_ui)

    def stop_process(self):
        self.stop_requested = True
        self.log("Đang yêu cầu dừng NGAY LẬP TỨC...")
        
        # Force kill if process is running
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate() # Or .kill() for stronger kill
                self.log("Đã ngắt tiến trình chạy.")
            except Exception as e:
                self.log(f"Lỗi ngắt tiến trình: {e}")
                
        self.aggressive_cleanup()
        self.clean_orphaned_bot_processes()
        # UI reset will happen in run_logic when loop breaks

    def reset_ui(self):
        self.btn_start.config(state="normal", bg="#4CAF50")
        self.btn_stop.config(state="disabled", bg="#666")
        self.refresh_stats()
        self.refresh_error_channels()
        if hasattr(self, 'refresh_channels_tab'):
            self.refresh_channels_tab()

    def clean_orphaned_bot_processes(self):
        """Tìm và diệt tất cả các tiến trình main.py chạy ngầm trong thư mục của dự án này để tránh xung đột lock."""
        # 1. Dừng PM2 nếu đang chạy để tránh PM2 tự khởi động lại tạo tiến trình mới tranh chấp lock
        try:
            import subprocess
            subprocess.run("pm2 stop \"Gams Youtube Downloader\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log("Đã dừng tiến trình chạy ngầm PM2 'Gams Youtube Downloader' (nếu có).")
        except Exception:
            pass

        # 2. Tìm và diệt các tiến trình Python chạy main.py cũ
        try:
            import psutil
            current_pid = os.getpid()
            killed_count = 0
            for p in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    if p.pid == current_pid:
                        continue
                    cmd = p.info.get('cmdline') or []
                    cwd = p.info.get('cwd') or ""
                    
                    is_python = 'python' in p.info.get('name', '').lower() or any('python' in arg.lower() for arg in cmd)
                    is_main_py = any('main.py' in arg for arg in cmd)
                    is_same_dir = False
                    if cwd:
                        is_same_dir = os.path.abspath(cwd) == os.path.abspath(self.base_dir)
                    else:
                        is_same_dir = any(self.base_dir in arg for arg in cmd)
                        
                    if is_python and is_main_py and is_same_dir:
                        if self.current_process and p.pid == self.current_process.pid:
                            continue
                            
                        self.log(f"Phát hiện tiến trình bot cũ đang chạy ngầm (PID {p.pid}). Đang dừng...")
                        p.kill()
                        killed_count += 1
                except:
                    pass
            if killed_count > 0:
                self.log(f"Đã dọn dẹp xong {killed_count} tiến trình bot cũ.")
        except Exception as e:
            self.log(f"Lỗi khi dọn dẹp tiến trình: {e}")

    def aggressive_cleanup(self):
        """Dừng chỉ các profile GemLogin đã được tool sử dụng."""
        try:
            from gemlogin_api import GemLoginAPI
            from gpm_login_api import GPMLoginAPI
            
            b_type = getattr(config, 'BROWSER_TYPE', 'gemlogin')
            if b_type == "gpmlogin":
                api = GPMLoginAPI()
            else:
                api = GemLoginAPI()
            
            profile_dir = getattr(config, 'PROFILE_DIR', None)
            if profile_dir:
                tmp_file = os.path.join(self.base_dir, profile_dir, "active_profiles.tmp")
            else:
                tmp_file = os.path.join(self.base_dir, "active_profiles.tmp")
            if os.path.exists(tmp_file):
                with open(tmp_file, "r") as f:
                    profile_ids = set(line.strip() for line in f if line.strip())
                
                if profile_ids:
                    self.log(f"Đang đóng {len(profile_ids)} trình duyệt của tool...")
                    for pid in profile_ids:
                        try:
                            api.stop_profile(pid)
                        except:
                            pass
                
                # Sau khi đóng xong thì xóa file tạm
                try:
                    os.remove(tmp_file)
                except:
                    pass
            
            # Chỉ kill driver liên quan để giải phóng tài nguyên, không kill chrome.exe global nữa
            drivers = ["chromedriver.exe", "gemdriver.exe"]
            for d in drivers:
                subprocess.run(f"taskkill /f /im {d}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
        except Exception as e:
            self.log(f"Lỗi dọn dẹp: {e}")

    def run_reset(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa hết Video và Lịch sử không?"):
            try:
                bat_file = os.path.join(self.base_dir, "xoa_du_lieu.bat")
                subprocess.run(bat_file, shell=True, cwd=self.base_dir)
                self.log("Đã Reset dữ liệu thành công.")
            except Exception as e:
                self.log(f"Lỗi reset: {e}")

    def check_api_key(self):
        """Kiểm tra xem API Key có hoạt động hay không."""
        api_key = self.youtube_api_key.get().strip()
        if not api_key:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập API Key trước khi kiểm tra.")
            return
            
        def run_check():
            try:
                from googleapiclient.discovery import build
                import logging
                logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
                youtube = build('youtube', 'v3', developerKey=api_key)
                # Thử một request đơn giản
                youtube.search().list(part="id", maxResults=1, q="test").execute()
                self.root.after(0, lambda: messagebox.showinfo("Thành công", "API Key hoạt động bình thường!"))
                self.log("API Key hợp lệ.")
            except Exception as e:
                error_msg = str(e)
                if "API key not valid" in error_msg or "keyInvalid" in error_msg:
                    msg = "API Key không hợp lệ!"
                elif "quotaExceeded" in error_msg:
                    msg = "API Key đã hết hạn mức (Quota Exceeded)!"
                else:
                    msg = f"Lỗi API: {error_msg}"
                self.root.after(0, lambda: messagebox.showerror("Lỗi API", msg))
                self.log(f"Kiểm tra API thất bại: {msg}")

        self.log("Đang kiểm tra API Key...")
        threading.Thread(target=run_check, daemon=True).start()

    def create_channels_tab_ui(self):
        self.channel_rows = []
        self._save_channels_timer = None
        
        # 1. Top bar: Title and Action Buttons
        top_f = ttk.Frame(self.channels_tab)
        top_f.pack(fill="x", padx=10, pady=5)
        
        lbl_title = ttk.Label(top_f, text="QUẢN LÝ DANH SÁCH KÊNH & FOLDER LƯU TRỮ", font=("Segoe UI", 10, "bold"))
        lbl_title.pack(side="left")
        
        lbl_autosave = tk.Label(top_f, text="● Tự động lưu: Đang bật", fg="#4CAF50", font=("Segoe UI", 9, "italic"))
        lbl_autosave.pack(side="left", padx=15)
        self.lbl_autosave = lbl_autosave
        
        # Refresh button
        btn_refresh = tk.Button(top_f, text="↻ Tải lại danh sách", bg="#ff9800", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), command=self.refresh_channels_tab)
        btn_refresh.pack(side="right", padx=5)
        
        # Open txt file button
        btn_open_txt = tk.Button(top_f, text="📁 Mở File TXT", bg="#607D8B", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), command=lambda: self.open_file("danhsachkenh.txt"))
        btn_open_txt.pack(side="right", padx=5)

        # Separator line
        sep = ttk.Separator(self.channels_tab, orient="horizontal")
        sep.pack(fill="x", padx=10, pady=5)

        # 3. Canvas & Scrollbar container
        list_container = ttk.Frame(self.channels_tab)
        list_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.channels_canvas = tk.Canvas(list_container, borderwidth=0, highlightthickness=0)
        self.channels_canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.channels_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.scrollable_frame = ttk.Frame(self.channels_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.channels_canvas.configure(
                scrollregion=self.channels_canvas.bbox("all")
            )
        )
        
        canvas_window = self.channels_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_canvas_width(event):
            self.channels_canvas.itemconfig(canvas_window, width=event.width)
            
        self.channels_canvas.bind("<Configure>", configure_canvas_width)
        self.channels_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel binding
        def _on_mousewheel(event):
            self.channels_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        def _bind_mw(event):
            self.channels_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_mw(event):
            self.channels_canvas.unbind_all("<MouseWheel>")
            
        self.channels_canvas.bind("<Enter>", _bind_mw)
        self.channels_canvas.bind("<Leave>", _unbind_mw)
        
        # Configure columns
        self.scrollable_frame.columnconfigure(0, weight=0) # STT
        self.scrollable_frame.columnconfigure(1, weight=3) # URL
        self.scrollable_frame.columnconfigure(2, weight=2) # Folder
        self.scrollable_frame.columnconfigure(3, weight=0) # Status
        self.scrollable_frame.columnconfigure(4, weight=0) # Delete
        
        # Add static headers
        headers = ["STT", "Link Kênh YouTube", "Thư mục lưu video (Folder)", "Trạng thái", "Hành động"]
        for col_idx, text in enumerate(headers):
            lbl = ttk.Label(self.scrollable_frame, text=text, font=("Segoe UI", 9, "bold"))
            lbl.grid(row=0, column=col_idx, padx=5, pady=5)
            
        # 4. Bottom frame
        bottom_f = ttk.Frame(self.channels_tab)
        bottom_f.pack(fill="x", padx=10, pady=5)
        
        btn_add = tk.Button(bottom_f, text="＋ Thêm Kênh Mới", bg="#4CAF50", fg="white", relief="flat", font=("Segoe UI", 9, "bold"), command=self.add_empty_channel_row)
        btn_add.pack(side="left", padx=5)
        
        self.refresh_channels_tab()

    def add_empty_channel_row(self):
        self.add_channel_row_ui(url="", folder="", statuses=None)
        self.channels_canvas.update_idletasks()
        self.channels_canvas.yview_moveto(1.0)

    def refresh_channels_tab(self):
        if hasattr(self, 'channel_rows') and self.channel_rows:
            for row in self.channel_rows:
                row['stt_label'].destroy()
                row['url_entry'].destroy()
                row['folder_entry'].destroy()
                row['status_label'].destroy()
                row['delete_btn'].destroy()
            self.channel_rows.clear()
            
        from youtube_manager import YouTubeManager
        yt_manager = YouTubeManager()
        channels = yt_manager.get_channels()
        statuses = self.get_channel_statuses()
        
        for i, ch in enumerate(channels):
            folder = ch['names'][0] if ch['names'] else ""
            if folder is None:
                folder = ""
            self.add_channel_row_ui(url=ch['url'], folder=folder, statuses=statuses, row_num=i+1)

    def normalize_url(self, url):
        if not url:
            return ""
        url = url.strip().lower()
        if url.endswith('/'):
            url = url[:-1]
        return url

    def get_channel_statuses(self):
        statuses = {}
        try:
            from youtube_manager import YouTubeManager
            yt_manager = YouTubeManager()
            failed = yt_manager.get_failed_channels()
            for row in failed:
                if not row or len(row) < 2:
                    continue
                url = row[0].strip()
                reason = row[1].strip()
                statuses[self.normalize_url(url)] = f"Die ({reason})"
        except Exception as e:
            self.log(f"Lỗi đọc trạng thái kênh lỗi: {e}")
        return statuses

    def add_channel_row_ui(self, url="", folder="", statuses=None, row_num=None):
        if statuses is None:
            statuses = self.get_channel_statuses()
        if row_num is None:
            row_num = len(self.channel_rows) + 1
            
        grid_row = row_num
        
        stt_lbl = ttk.Label(self.scrollable_frame, text=str(row_num), font=("Segoe UI", 9))
        stt_lbl.grid(row=grid_row, column=0, padx=5, pady=5)
        
        url_var = tk.StringVar(value=url)
        url_ent = ttk.Entry(self.scrollable_frame, textvariable=url_var)
        url_ent.grid(row=grid_row, column=1, padx=5, pady=5, sticky="ew")
        
        folder_var = tk.StringVar(value=folder if folder else "")
        folder_ent = ttk.Entry(self.scrollable_frame, textvariable=folder_var)
        folder_ent.grid(row=grid_row, column=2, padx=5, pady=5, sticky="ew")
        
        norm_url = self.normalize_url(url)
        status_text = statuses.get(norm_url, "Live")
        status_fg = "green"
        if "Die" in status_text:
            status_fg = "red"
            
        status_lbl = tk.Label(self.scrollable_frame, text=status_text, fg=status_fg, font=("Segoe UI", 9, "bold"))
        status_lbl.grid(row=grid_row, column=3, padx=5, pady=5)
        
        bg_color = "#1e1e1e" if self.is_dark else "#f5f5f5"
        status_lbl.config(bg=bg_color)
        
        def on_edit(*args):
            current_url = url_var.get()
            current_norm = self.normalize_url(current_url)
            current_statuses = self.get_channel_statuses()
            new_status = current_statuses.get(current_norm, "Live")
            
            if "Die" in new_status:
                status_lbl.config(text=new_status, fg="red")
            else:
                status_lbl.config(text="Live", fg="green")
                
            self.queue_save_channels()
            
        url_var.trace_add("write", on_edit)
        folder_var.trace_add("write", on_edit)
        
        delete_btn = tk.Button(
            self.scrollable_frame, 
            text="✕", 
            fg="white", 
            bg="#f44336", 
            relief="flat", 
            font=("Segoe UI", 8, "bold"),
            command=lambda: self.delete_channel_row(row_num)
        )
        delete_btn.grid(row=grid_row, column=4, padx=5, pady=5)
        
        row_dict = {
            'stt': row_num,
            'stt_label': stt_lbl,
            'url_var': url_var,
            'url_entry': url_ent,
            'folder_var': folder_var,
            'folder_entry': folder_ent,
            'status_label': status_lbl,
            'delete_btn': delete_btn
        }
        self.channel_rows.append(row_dict)

    def delete_channel_row(self, row_num):
        idx_to_remove = -1
        for idx, row in enumerate(self.channel_rows):
            if row['stt'] == row_num:
                idx_to_remove = idx
                break
        
        if idx_to_remove != -1:
            row = self.channel_rows[idx_to_remove]
            row['stt_label'].destroy()
            row['url_entry'].destroy()
            row['folder_entry'].destroy()
            row['status_label'].destroy()
            row['delete_btn'].destroy()
            
            self.channel_rows.pop(idx_to_remove)
            
            for new_idx, rem_row in enumerate(self.channel_rows):
                new_row_num = new_idx + 1
                rem_row['stt'] = new_row_num
                rem_row['stt_label'].config(text=str(new_row_num))
                
                grid_row = new_row_num
                rem_row['stt_label'].grid(row=grid_row, column=0)
                rem_row['url_entry'].grid(row=grid_row, column=1)
                rem_row['folder_entry'].grid(row=grid_row, column=2)
                rem_row['status_label'].grid(row=grid_row, column=3)
                rem_row['delete_btn'].grid(row=grid_row, column=4)
                
                rem_row['delete_btn'].config(command=lambda r=new_row_num: self.delete_channel_row(r))
            
            self.save_channels_to_file()

    def queue_save_channels(self):
        if hasattr(self, '_save_channels_timer') and self._save_channels_timer:
            self.root.after_cancel(self._save_channels_timer)
        self._save_channels_timer = self.root.after(500, self.save_channels_to_file)

    def save_channels_to_file(self):
        channels = []
        for row in self.channel_rows:
            url = row['url_entry'].get().strip()
            folder = row['folder_entry'].get().strip()
            if url:
                channels.append({'url': url, 'name': folder})
        
        from youtube_manager import YouTubeManager
        yt_manager = YouTubeManager()
        
        with yt_manager.lock:
            with open(yt_manager.channels_file, 'w', encoding='utf-8') as f:
                for ch in channels:
                    if ch['name']:
                        f.write(f"{ch['url']}|{ch['name']}\n")
                    else:
                        f.write(f"{ch['url']}\n")

class ProfileSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chọn Profile Hoạt Động")
        self.geometry("520x450")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        
        # Load or create config
        self.config_path = "profiles_config.json"
        self.load_config()
        
        # Design Title
        lbl_title = tk.Label(self, text="HỆ THỐNG QUẢN LÝ PROFILE", font=("Arial", 16, "bold"), bg="#1e1e2e", fg="#4CAF50")
        lbl_title.pack(pady=20)
        
        lbl_desc = tk.Label(self, text="Vui lòng chọn Profile để truy cập Dashboard riêng biệt:", font=("Arial", 10), bg="#1e1e2e", fg="#a6adc8")
        lbl_desc.pack(pady=(0, 20))
        
        # Grid frame
        grid_frame = tk.Frame(self, bg="#1e1e2e")
        grid_frame.pack(fill="both", expand=True, padx=40)
        
        self.buttons = []
        for i, prof in enumerate(self.profiles):
            row = i // 2
            col = i % 2
            
            # Subframe for button + edit button
            item_frame = tk.Frame(grid_frame, bg="#1e1e2e", pady=8, padx=8)
            item_frame.grid(row=row, column=col, sticky="nsew")
            
            # Select button
            btn_select = tk.Button(
                item_frame, text=prof['name'], font=("Arial", 11, "bold"),
                bg="#313244", fg="#cdd6f4", activebackground="#45475a", activeforeground="#4CAF50",
                bd=0, height=2, width=15, cursor="hand2",
                command=lambda p=prof: self.select_profile(p)
            )
            btn_select.pack(side="left", fill="x", expand=True)
            self.buttons.append((btn_select, prof))
            
            # Edit name button
            btn_edit = tk.Button(
                item_frame, text="✏️", font=("Arial", 10),
                bg="#1e1e2e", fg="#fab387", activebackground="#1e1e2e", activeforeground="#f38ba8",
                bd=0, cursor="hand2", padx=5,
                command=lambda idx=i: self.edit_profile_name(idx)
            )
            btn_edit.pack(side="right", padx=(5, 0))
            
        # Set grid weight
        for r in range(3):
            grid_frame.rowconfigure(r, weight=1)
        for c in range(2):
            grid_frame.columnconfigure(c, weight=1)
            
        self.selected_profile = None

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
            except:
                self.config_data = self.get_default_config()
        else:
            self.config_data = self.get_default_config()
            self.save_config()
            
        self.profiles = self.config_data.get("profiles", [])

    def get_default_config(self):
        return {
            "profiles": [
                {"id": 1, "name": "Profile 1"},
                {"id": 2, "name": "Profile 2"},
                {"id": 3, "name": "Profile 3"},
                {"id": 4, "name": "Profile 4"},
                {"id": 5, "name": "Profile 5"},
                {"id": 6, "name": "Profile 6"}
            ]
        }

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profiles config: {e}")

    def edit_profile_name(self, idx):
        current_name = self.profiles[idx]['name']
        new_name = simpledialog.askstring("Đổi tên Profile", f"Nhập tên mới cho {current_name}:", parent=self)
        if new_name and new_name.strip():
            self.profiles[idx]['name'] = new_name.strip()
            self.config_data['profiles'] = self.profiles
            self.save_config()
            self.buttons[idx][0].configure(text=new_name.strip())

    def select_profile(self, profile):
        self.selected_profile = profile
        self.destroy()

if __name__ == "__main__":
    from tkinter import simpledialog
    
    # 1. Khởi chạy ProfileSelector
    selector = ProfileSelector()
    selector.mainloop()
    
    if selector.selected_profile:
        prof = selector.selected_profile
        profile_id = prof['id']
        profile_name = prof['name']
        
        # Ghi nhận config cho GiaanTool
        import config
        config.PROFILE_ID = profile_id
        config.PROFILE_NAME = profile_name
        config.PROFILE_DIR = f"profiles/profile_{profile_id}"
        
        # Tạo thư mục lưu profile
        os.makedirs(config.PROFILE_DIR, exist_ok=True)
        
        # Di chuyển dữ liệu cũ từ root vào Profile 1 nếu là lần đầu tiên chạy Profile 1
        profile_config_path = os.path.join(config.PROFILE_DIR, "config.json")
        if (profile_id == 1 or profile_id == "1") and (not os.path.exists(profile_config_path) or os.path.getsize(profile_config_path) == 0):
            import shutil
            old_files = [
                "danhsachkenh.txt",
                "lichsutai.txt",
                "thongke_ngay.txt",
                "channel_map.txt",
                "cookies.txt",
                "kenh_loi.txt",
                "hangdoi.txt"
            ]
            for fname in old_files:
                src = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
                dst = os.path.join(config.PROFILE_DIR, fname)
                if os.path.exists(src) and os.path.isfile(src):
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Error migrating {fname}: {e}")
        
        # Load hoặc copy cấu hình mặc định vào profiles/profile_{id}/config.json
        cfg_loaded = False
        if os.path.exists(profile_config_path) and os.path.getsize(profile_config_path) > 0:
            try:
                with open(profile_config_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                for k, v in cfg_data.items():
                    setattr(config, k, v)
                cfg_loaded = True
            except Exception as e:
                print(f"Warning: Lỗi load profile config: {e}")
                
        if not cfg_loaded:
            default_cfg = {
                "BROWSER_TYPE": config.BROWSER_TYPE,
                "GEMLOGIN_API_URL": config.GEMLOGIN_API_URL,
                "GPM_LOGIN_API_URL": config.GPM_LOGIN_API_URL,
                "DOWNLOAD_THREADS": config.DOWNLOAD_THREADS,
                "CHECK_THREADS": config.CHECK_THREADS,
                "RUN_ONCE": config.RUN_ONCE,
                "LOOP_COUNT": config.LOOP_COUNT,
                "LOOP_DELAY": config.LOOP_DELAY,
                "USE_API_SCAN": config.USE_API_SCAN,
                "USE_BROWSER_SCAN": config.USE_BROWSER_SCAN,
                "YOUTUBE_API_KEY": config.YOUTUBE_API_KEY,
                "DOWNLOAD_PATH": config.DOWNLOAD_PATH,
                "COOKIES_FROM_BROWSER": config.COOKIES_FROM_BROWSER,
                "COOKIES_FILE": config.COOKIES_FILE,
                "SELECTED_PROFILE_ID": config.SELECTED_PROFILE_ID,
                "SELECTED_PROFILE_NAME": config.SELECTED_PROFILE_NAME,
                "HEADLESS_LOCAL_CHROME": getattr(config, 'HEADLESS_LOCAL_CHROME', False)
            }
            try:
                with open(profile_config_path, "w", encoding="utf-8") as f:
                    json.dump(default_cfg, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: Lỗi ghi profile config: {e}")
                
        # Resolve path cookies cho profile
        if config.COOKIES_FILE and not os.path.isabs(config.COOKIES_FILE):
            config.COOKIES_FILE = os.path.join(config.PROFILE_DIR, config.COOKIES_FILE)
            
        # Khởi chạy main app window
        root = tk.Tk()
        app = GiaanTool(root)
        root.mainloop()
