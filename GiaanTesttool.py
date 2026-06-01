import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import os
import sys
import threading
import time
import config
import re

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
        self.root.geometry("1100x750") # Wider horizontal layout
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
        
        # Main Layout Container (Horizontal split)
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="x", expand=False, padx=10, pady=5)
        
        # Left Column: Configuration & Mode
        self.left_col = ttk.Frame(self.main_container)
        self.left_col.pack(side="left", fill="both", expand=True, padx=5)
        
        # Right Column: Quick Actions & Controls
        self.right_col = ttk.Frame(self.main_container)
        self.right_col.pack(side="left", fill="both", expand=True, padx=5)
        
        # --- Populate Columns ---
        self.create_settings_frame(self.left_col)
        self.create_browser_settings_frame(self.left_col)
        self.create_run_frame(self.left_col)
        
        self.create_quick_actions_frame(self.right_col)
        self.create_control_frame(self.right_col)
        
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

        self.header_label = tk.Label(h_frame, text="Antigravity Gams Download", font=("Segoe UI", 16, "bold"), fg="#4CAF50")
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
            if wtype in ('Frame', 'Labelframe'):
                widget.config(bg=bg)
            elif wtype == 'Label':
                # Skip Header Label if handled manually, but safe to overwrite bg, keep fg if special?
                # Header Label FG is green, handled separately or we ignore if it has specific color?
                if widget != self.header_label:
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
        btn_check.pack(fill="x", pady=(5, 0))
        
        self.update_browser_ui()

    def update_browser_ui(self):
        """Cập nhật Entry hiển thị đúng API URL dựa trên loại trình duyệt."""
        if self.browser_type.get() == "gemlogin":
            self.ent_api_url.config(textvariable=self.gemlogin_api_url)
        else:
            self.ent_api_url.config(textvariable=self.gpmlogin_api_url)

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

    def create_quick_actions_frame(self, parent):
        frame = ttk.Labelframe(parent, text="Truy Cập Nhanh", padding=15)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_channels = tk.Button(frame, text="Mở File Kênh", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("danhsachkenh.txt"))
        btn_channels.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        btn_history = tk.Button(frame, text="Mở Log Tải", bg="#607D8B", fg="white", relief="flat", command=lambda: self.open_file("lichsutai.txt"))
        btn_history.pack(side="left", fill="x", expand=True, padx=2)
        
        btn_folder = tk.Button(frame, text="Mở Thư Mục Video", bg="#607D8B", fg="white", relief="flat", command=self.open_download_folder)
        btn_folder.pack(side="left", fill="x", expand=True, padx=2)

        btn_view_stats = tk.Button(frame, text="Kiểm tra Video & Log", bg="#4CAF50", fg="white", relief="flat", command=self.show_stats_tab, font=("Segoe UI", 9, "bold"))
        btn_view_stats.pack(side="left", fill="x", expand=True, padx=(2, 0))

    def show_stats_tab(self):
        """Chuyển sang tab Thống kê và làm mới dữ liệu."""
        self.notebook.select(1)
        self.refresh_stats()

    def open_file(self, filename):
        try:
            # Resolve relative path
            full_path = os.path.join(self.base_dir, filename)
            
            if not os.path.exists(full_path):
                 # Create if not exists so it opens blank
                 with open(full_path, 'w', encoding='utf-8') as f: pass
            os.startfile(full_path)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

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
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

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
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 1:
            self.refresh_stats()
        elif selected_tab == 2:
            self.refresh_error_channels()

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
                
                self.current_process = subprocess.Popen(
                    ["python", "-u", main_script], # -u for unbuffered output
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
        # UI reset will happen in run_logic when loop breaks

    def reset_ui(self):
        self.btn_start.config(state="normal", bg="#4CAF50")
        self.btn_stop.config(state="disabled", bg="#666")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = GiaanTool(root)
    root.mainloop()
