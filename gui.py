"""
知识星球内容爬取工具 - GUI 界面
使用 tkinter 实现可视化操作
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import sys
import json
from datetime import datetime

from scraper import ScraperConfig, Scraper, parse_time_arg

# ---- 配置持久化 ----
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.zsxq_config.json')


def load_saved_config():
    """从文件加载上次保存的配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config_to_file(config_dict):
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---- 主题色彩 ----
class Theme:
    # 浅色主题 - 高对比度，文字清晰
    BG = '#f0f2f5'
    BG_SECONDARY = '#dfe3ea'
    BG_CARD = '#ffffff'
    BG_INPUT = '#f8f9fb'
    BG_BUTTON = '#6c5ce7'
    BG_BUTTON_HOVER = '#5a4bd6'
    BG_BUTTON_DANGER = '#e74c3c'
    BG_BUTTON_DANGER_HOVER = '#d63c2c'
    BG_SUCCESS = '#27ae60'
    FG = '#2c3e50'
    FG_SECONDARY = '#7f8c9b'
    FG_ACCENT = '#6c5ce7'
    FG_TITLE = '#1a1a2e'
    BORDER = '#d1d5de'
    HIGHLIGHT = '#6c5ce7'
    LOG_BG = '#1e2030'
    LOG_FG = '#e0e0f0'
    PROGRESS_BG = '#dfe3ea'
    PROGRESS_FG = '#6c5ce7'


class App:
    """主应用窗口"""

    def __init__(self, root):
        self.root = root
        self.scraper = None
        self.is_running = False

        self._setup_window()
        self._setup_styles()
        self._build_ui()
        self._load_config()

    def _setup_window(self):
        self.root.title('知识星球爬取工具')
        self.root.geometry('780x720')
        self.root.minsize(680, 600)
        self.root.configure(bg=Theme.BG)

        # 让窗口居中
        self.root.update_idletasks()
        w = 780
        h = 720
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry('{}x{}+{}+{}'.format(w, h, x, y))

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Frame
        style.configure('Card.TFrame', background=Theme.BG_CARD)
        style.configure('Main.TFrame', background=Theme.BG)

        # Label
        style.configure('Title.TLabel',
                        background=Theme.BG,
                        foreground=Theme.FG_TITLE,
                        font=('SF Pro Display', 20, 'bold'))
        style.configure('Subtitle.TLabel',
                        background=Theme.BG,
                        foreground=Theme.FG_SECONDARY,
                        font=('SF Pro Text', 11))
        style.configure('Section.TLabel',
                        background=Theme.BG_CARD,
                        foreground=Theme.FG_ACCENT,
                        font=('SF Pro Text', 12, 'bold'))
        style.configure('Field.TLabel',
                        background=Theme.BG_CARD,
                        foreground=Theme.FG,
                        font=('SF Pro Text', 11))
        style.configure('Status.TLabel',
                        background=Theme.BG,
                        foreground=Theme.FG_SECONDARY,
                        font=('SF Pro Text', 10))

        # Entry
        style.configure('Custom.TEntry',
                        fieldbackground=Theme.BG_INPUT,
                        foreground=Theme.FG,
                        bordercolor=Theme.BORDER,
                        insertcolor=Theme.FG,
                        font=('SF Mono', 11))
        style.map('Custom.TEntry',
                  bordercolor=[('focus', Theme.HIGHLIGHT)])

        # Checkbutton
        style.configure('Custom.TCheckbutton',
                        background=Theme.BG_CARD,
                        foreground=Theme.FG,
                        font=('SF Pro Text', 11))
        style.map('Custom.TCheckbutton',
                  background=[('active', Theme.BG_CARD)])

        # Progressbar
        style.configure('Custom.Horizontal.TProgressbar',
                        background=Theme.PROGRESS_FG,
                        troughcolor=Theme.PROGRESS_BG,
                        bordercolor=Theme.BG_CARD,
                        lightcolor=Theme.PROGRESS_FG,
                        darkcolor=Theme.PROGRESS_FG)

    def _build_ui(self):
        # 主容器
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # ---- 标题区域 ----
        header = ttk.Frame(main_frame, style='Main.TFrame')
        header.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(header, text='🌟 知识星球爬取工具', style='Title.TLabel').pack(anchor='w')
        ttk.Label(header, text='配置参数后点击开始爬取，数据将保存为 Markdown 文件', style='Subtitle.TLabel').pack(anchor='w', pady=(4, 0))

        # ---- 可滚动内容区域 ----
        # 使用 Canvas + Frame 实现可滚动
        content_canvas = tk.Canvas(main_frame, bg=Theme.BG, highlightthickness=0)
        content_canvas.pack(fill=tk.BOTH, expand=True)

        # 内部 Frame
        inner_frame = ttk.Frame(content_canvas, style='Main.TFrame')
        content_canvas.create_window((0, 0), window=inner_frame, anchor='nw', tags='inner')

        def on_configure(e):
            content_canvas.configure(scrollregion=content_canvas.bbox('all'))
            # 让内部Frame宽度跟随Canvas
            content_canvas.itemconfig('inner', width=content_canvas.winfo_width())

        inner_frame.bind('<Configure>', on_configure)
        content_canvas.bind('<Configure>', on_configure)

        # ---- 连接设置卡片 ----
        self._build_connection_card(inner_frame)

        # ---- 时间范围卡片 ----
        self._build_time_card(inner_frame)

        # ---- 选项卡片 ----
        self._build_options_card(inner_frame)

        # ---- 操作按钮 ----
        self._build_buttons(inner_frame)

        # ---- 进度信息 ----
        self._build_progress(inner_frame)

        # ---- 日志窗口 ----
        self._build_log(inner_frame)

    def _make_card(self, parent, title, pad_y=(0, 10)):
        """创建一个带标题的卡片容器"""
        card = tk.Frame(parent, bg=Theme.BG_CARD,
                        highlightbackground=Theme.BORDER,
                        highlightthickness=1,
                        bd=0)
        card.pack(fill=tk.X, pady=pad_y)

        # 内部 padding
        inner = tk.Frame(card, bg=Theme.BG_CARD)
        inner.pack(fill=tk.X, padx=16, pady=12)

        # 标题
        tk.Label(inner, text=title,
                 bg=Theme.BG_CARD, fg=Theme.FG_ACCENT,
                 font=('SF Pro Text', 12, 'bold')).pack(anchor='w', pady=(0, 8))

        return inner

    def _make_field(self, parent, label, default='', show=None):
        """创建一个输入字段"""
        row = tk.Frame(parent, bg=Theme.BG_CARD)
        row.pack(fill=tk.X, pady=3)

        tk.Label(row, text=label, width=12, anchor='w',
                 bg=Theme.BG_CARD, fg=Theme.FG,
                 font=('SF Pro Text', 11)).pack(side=tk.LEFT)

        entry = tk.Entry(row,
                         bg=Theme.BG_INPUT, fg=Theme.FG,
                         insertbackground=Theme.FG,
                         font=('SF Mono', 11),
                         relief='flat',
                         highlightbackground=Theme.BORDER,
                         highlightcolor=Theme.HIGHLIGHT,
                         highlightthickness=1,
                         bd=4)
        if show:
            entry.configure(show=show)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if default:
            entry.insert(0, default)

        return entry

    def _build_connection_card(self, parent):
        card = self._make_card(parent, '🔗 连接设置')

        self.entry_group = self._make_field(card, '星球 ID', '88882252841552')

        # Cookie 区域 - 使用 Text 多行显示
        row = tk.Frame(card, bg=Theme.BG_CARD)
        row.pack(fill=tk.X, pady=3)

        tk.Label(row, text='Cookie', width=12, anchor='w',
                 bg=Theme.BG_CARD, fg=Theme.FG,
                 font=('SF Pro Text', 11)).pack(side=tk.LEFT, anchor='n', pady=4)

        self.text_cookie = tk.Text(row,
                                   height=3,
                                   bg=Theme.BG_INPUT, fg=Theme.FG,
                                   insertbackground=Theme.FG,
                                   font=('SF Mono', 10),
                                   relief='flat',
                                   highlightbackground=Theme.BORDER,
                                   highlightcolor=Theme.HIGHLIGHT,
                                   highlightthickness=1,
                                   bd=4,
                                   wrap=tk.WORD)
        self.text_cookie.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_time_card(self, parent):
        card = self._make_card(parent, '⏱ 时间范围')

        today = datetime.now().strftime('%Y-%m-%d')

        self.entry_start = self._make_field(card, '开始时间', '2026-01-01')
        self.entry_end = self._make_field(card, '结束时间', today)

        hint = tk.Label(card, text='格式: YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS',
                        bg=Theme.BG_CARD, fg=Theme.FG_SECONDARY,
                        font=('SF Pro Text', 9))
        hint.pack(anchor='w', pady=(4, 0))

    def _build_options_card(self, parent):
        card = self._make_card(parent, '⚙ 爬取选项')

        opts_row = tk.Frame(card, bg=Theme.BG_CARD)
        opts_row.pack(fill=tk.X, pady=2)

        self.var_images = tk.BooleanVar(value=False)
        self.var_files = tk.BooleanVar(value=False)

        cb_images = tk.Checkbutton(opts_row, text='  爬取图片',
                                   variable=self.var_images,
                                   bg=Theme.BG_CARD, fg=Theme.FG,
                                   selectcolor=Theme.BG_INPUT,
                                   activebackground=Theme.BG_CARD,
                                   activeforeground=Theme.FG,
                                   font=('SF Pro Text', 11))
        cb_images.pack(side=tk.LEFT, padx=(0, 20))

        cb_files = tk.Checkbutton(opts_row, text='  爬取文件',
                                  variable=self.var_files,
                                  bg=Theme.BG_CARD, fg=Theme.FG,
                                  selectcolor=Theme.BG_INPUT,
                                  activebackground=Theme.BG_CARD,
                                  activeforeground=Theme.FG,
                                  font=('SF Pro Text', 11))
        cb_files.pack(side=tk.LEFT)

        # 输出目录
        dir_row = tk.Frame(card, bg=Theme.BG_CARD)
        dir_row.pack(fill=tk.X, pady=(8, 0))

        tk.Label(dir_row, text='输出目录', width=12, anchor='w',
                 bg=Theme.BG_CARD, fg=Theme.FG,
                 font=('SF Pro Text', 11)).pack(side=tk.LEFT)

        self.entry_output = tk.Entry(dir_row,
                                     bg=Theme.BG_INPUT, fg=Theme.FG,
                                     insertbackground=Theme.FG,
                                     font=('SF Mono', 11),
                                     relief='flat',
                                     highlightbackground=Theme.BORDER,
                                     highlightcolor=Theme.HIGHLIGHT,
                                     highlightthickness=1,
                                     bd=4)
        self.entry_output.insert(0, './output')
        self.entry_output.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_browse = tk.Button(dir_row, text='📁 浏览',
                               command=self._browse_output,
                               bg=Theme.BG_SECONDARY, fg=Theme.FG,
                               activebackground=Theme.BG_CARD,
                               activeforeground=Theme.FG,
                               font=('SF Pro Text', 10),
                               relief='flat', bd=0,
                               cursor='hand2',
                               padx=10, pady=2)
        btn_browse.pack(side=tk.LEFT, padx=(8, 0))

    def _build_buttons(self, parent):
        btn_frame = tk.Frame(parent, bg=Theme.BG)
        btn_frame.pack(fill=tk.X, pady=(12, 8))

        # 保存配置按钮
        self.btn_save = tk.Button(btn_frame, text='💾 保存配置',
                                  command=self._save_config,
                                  bg=Theme.BG_SECONDARY, fg=Theme.FG,
                                  activebackground=Theme.BG_CARD,
                                  activeforeground=Theme.FG,
                                  font=('SF Pro Text', 12),
                                  relief='flat', bd=0,
                                  cursor='hand2',
                                  padx=18, pady=8)
        self.btn_save.pack(side=tk.LEFT)

        # 停止按钮
        self.btn_stop = tk.Button(btn_frame, text='⏹ 停止',
                                  command=self._stop_scraper,
                                  bg=Theme.BG_BUTTON_DANGER, fg='#ffffff',
                                  activebackground=Theme.BG_BUTTON_DANGER_HOVER,
                                  activeforeground='#ffffff',
                                  font=('SF Pro Text', 12, 'bold'),
                                  relief='flat', bd=0,
                                  cursor='hand2',
                                  padx=24, pady=8,
                                  state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, padx=(8, 0))

        # 开始按钮
        self.btn_start = tk.Button(btn_frame, text='🚀 开始爬取',
                                   command=self._start_scraper,
                                   bg=Theme.BG_BUTTON, fg='#ffffff',
                                   activebackground=Theme.BG_BUTTON_HOVER,
                                   activeforeground='#ffffff',
                                   font=('SF Pro Text', 12, 'bold'),
                                   relief='flat', bd=0,
                                   cursor='hand2',
                                   padx=24, pady=8)
        self.btn_start.pack(side=tk.RIGHT)

    def _build_progress(self, parent):
        progress_frame = tk.Frame(parent, bg=Theme.BG)
        progress_frame.pack(fill=tk.X, pady=(0, 6))

        self.label_status = tk.Label(progress_frame,
                                     text='就绪',
                                     bg=Theme.BG, fg=Theme.FG_SECONDARY,
                                     font=('SF Pro Text', 10))
        self.label_status.pack(anchor='w')

        self.progress = ttk.Progressbar(progress_frame,
                                        style='Custom.Horizontal.TProgressbar',
                                        mode='indeterminate',
                                        length=300)
        self.progress.pack(fill=tk.X, pady=(4, 0))

        # 统计信息
        stats_frame = tk.Frame(progress_frame, bg=Theme.BG)
        stats_frame.pack(fill=tk.X, pady=(6, 0))

        self.label_topics = tk.Label(stats_frame, text='Topics: 0',
                                     bg=Theme.BG, fg=Theme.FG_ACCENT,
                                     font=('SF Mono', 10))
        self.label_topics.pack(side=tk.LEFT, padx=(0, 16))

        self.label_images = tk.Label(stats_frame, text='Images: 0',
                                     bg=Theme.BG, fg=Theme.FG_ACCENT,
                                     font=('SF Mono', 10))
        self.label_images.pack(side=tk.LEFT, padx=(0, 16))

        self.label_files = tk.Label(stats_frame, text='Files: 0',
                                    bg=Theme.BG, fg=Theme.FG_ACCENT,
                                    font=('SF Mono', 10))
        self.label_files.pack(side=tk.LEFT)

    def _build_log(self, parent):
        log_frame = tk.Frame(parent, bg=Theme.BG)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        tk.Label(log_frame, text='📋 运行日志',
                 bg=Theme.BG, fg=Theme.FG_ACCENT,
                 font=('SF Pro Text', 11, 'bold')).pack(anchor='w', pady=(0, 4))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            bg=Theme.LOG_BG, fg=Theme.LOG_FG,
            insertbackground=Theme.FG,
            font=('SF Mono', 10),
            relief='flat',
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.HIGHLIGHT,
            highlightthickness=1,
            bd=6,
            wrap=tk.WORD,
            state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志标签颜色
        self.log_text.tag_configure('info', foreground='#a8e6cf')
        self.log_text.tag_configure('error', foreground='#ff8b94')
        self.log_text.tag_configure('warn', foreground='#ffd93d')
        self.log_text.tag_configure('timestamp', foreground='#6a6a8a')

        # 清空日志按钮
        btn_clear = tk.Button(log_frame, text='🗑 清空日志',
                              command=self._clear_log,
                              bg=Theme.BG_SECONDARY, fg=Theme.FG,
                              activebackground=Theme.BG_CARD,
                              activeforeground=Theme.FG,
                              font=('SF Pro Text', 9),
                              relief='flat', bd=0,
                              cursor='hand2',
                              padx=8, pady=2)
        btn_clear.pack(anchor='e', pady=(4, 0))

    # ---- 工具方法 ----

    def _append_log(self, msg, tag='info'):
        """线程安全地追加日志"""
        def _do():
            self.log_text.configure(state=tk.NORMAL)
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_text.insert(tk.END, '[{}] '.format(timestamp), 'timestamp')
            self.log_text.insert(tk.END, msg + '\n', tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(0, _do)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _browse_output(self):
        directory = filedialog.askdirectory(title='选择输出目录')
        if directory:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, directory)

    def _update_progress(self, category, count):
        """线程安全地更新进度统计"""
        def _do():
            if category == 'topics':
                self.label_topics.configure(text='Topics: {}'.format(count))
            elif category == 'images':
                self.label_images.configure(text='Images: {}'.format(count))
            elif category == 'files':
                self.label_files.configure(text='Files: {}'.format(count))
        self.root.after(0, _do)

    def _set_running(self, running):
        """切换运行状态 UI"""
        def _do():
            self.is_running = running
            if running:
                self.btn_start.configure(state=tk.DISABLED, bg='#b8b5d4')
                self.btn_stop.configure(state=tk.NORMAL)
                self.progress.start(15)
                self.label_status.configure(text='⏳ 正在爬取...', fg='#e67e22')
            else:
                self.btn_start.configure(state=tk.NORMAL, bg=Theme.BG_BUTTON)
                self.btn_stop.configure(state=tk.DISABLED)
                self.progress.stop()
        self.root.after(0, _do)

    # ---- 配置管理 ----

    def _get_current_config(self):
        """获取当前界面上的配置"""
        return {
            'group': self.entry_group.get().strip(),
            'cookies': self.text_cookie.get('1.0', tk.END).strip(),
            'start_time': self.entry_start.get().strip(),
            'end_time': self.entry_end.get().strip(),
            'enable_images': self.var_images.get(),
            'enable_files': self.var_files.get(),
            'output_dir': self.entry_output.get().strip(),
        }

    def _save_config(self):
        config = self._get_current_config()
        save_config_to_file(config)
        self._append_log('配置已保存', 'info')

    def _load_config(self):
        saved = load_saved_config()
        if not saved:
            # 如果没有保存的配置，使用默认 cookies
            default_cookies = 'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2228282542855111%22%2C%22first_id%22%3A%221956c28a227557-0d59562d16f75c8-7e433c49-1296000-1956c28a228c2c%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk1NmMyOGEyMjc1NTctMGQ1OTU2MmQxNmY3NWM4LTdlNDMzYzQ5LTEyOTYwMDAtMTk1NmMyOGEyMjhjMmMiLCIkaWRlbnRpdHlfbG9naW5faWQiOiIyODI4MjU0Mjg1NTExMSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%2228282542855111%22%7D%7D; abtest_env=product; _c_WBKFRo=RUnziX2Q55t7ToRSewaVanjGdIXCMy3ZQodI2AuL; _nb_ioWEgULi=; zsxq_access_token=80200F68-58F0-4D2D-8248-17FEFE86999F_EF970781A970961C'
            self.text_cookie.insert('1.0', default_cookies)
            return

        if 'group' in saved:
            self.entry_group.delete(0, tk.END)
            self.entry_group.insert(0, saved['group'])
        if 'cookies' in saved:
            self.text_cookie.delete('1.0', tk.END)
            self.text_cookie.insert('1.0', saved['cookies'])
        if 'start_time' in saved:
            self.entry_start.delete(0, tk.END)
            self.entry_start.insert(0, saved['start_time'])
        if 'end_time' in saved:
            self.entry_end.delete(0, tk.END)
            self.entry_end.insert(0, saved['end_time'])
        if 'enable_images' in saved:
            self.var_images.set(saved['enable_images'])
        if 'enable_files' in saved:
            self.var_files.set(saved['enable_files'])
        if 'output_dir' in saved:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, saved['output_dir'])

        self._append_log('已加载上次保存的配置', 'info')

    # ---- 爬取控制 ----

    def _validate_config(self):
        """验证配置是否合法"""
        config = self._get_current_config()

        if not config['group']:
            messagebox.showerror('配置错误', '请输入星球 ID')
            return None
        if not config['cookies']:
            messagebox.showerror('配置错误', '请输入 Cookie')
            return None
        if not config['start_time'] and not config['end_time']:
            messagebox.showwarning('提示', '未设置时间范围，将爬取所有内容')

        # 验证时间格式
        try:
            start = parse_time_arg(config['start_time'])
            end = parse_time_arg(config['end_time'])
        except ValueError as e:
            messagebox.showerror('时间格式错误', str(e))
            return None

        if start and end and start > end:
            messagebox.showerror('时间范围错误', '开始时间不能晚于结束时间')
            return None

        return ScraperConfig(
            group=config['group'],
            cookies=config['cookies'],
            start_time=start,
            end_time=end,
            enable_images=config['enable_images'],
            enable_files=config['enable_files'],
            output_dir=config['output_dir'],
        )

    def _start_scraper(self):
        if self.is_running:
            return

        config = self._validate_config()
        if not config:
            return

        # 重置计数器
        self.label_topics.configure(text='Topics: 0')
        self.label_images.configure(text='Images: 0')
        self.label_files.configure(text='Files: 0')

        self._set_running(True)
        self._append_log('开始爬取...', 'info')

        def on_finished(success, msg):
            def _do():
                self._set_running(False)
                if success:
                    self.label_status.configure(text='✅ {}'.format(msg), fg=Theme.BG_SUCCESS)
                    self._append_log('🎉 {}'.format(msg), 'info')
                else:
                    self.label_status.configure(text='❌ {}'.format(msg), fg=Theme.BG_BUTTON_DANGER)
                    self._append_log('❌ {}'.format(msg), 'error')
            self.root.after(0, _do)

        self.scraper = Scraper(
            config,
            on_log=lambda msg: self._append_log(msg),
            on_progress=lambda cat, cnt: self._update_progress(cat, cnt),
            on_finished=on_finished,
            on_duplicate=self._on_duplicate,
            on_file_exists=self._on_file_exists,
        )

        thread = threading.Thread(target=self.scraper.run, daemon=True)
        thread.start()

    def _on_duplicate(self, create_time):
        """从工作线程调用，弹窗询问用户是否退出（线程安全）"""
        result = [False]  # False=继续, True=退出
        event = threading.Event()

        def _ask():
            answer = messagebox.askyesno(
                '发现重复内容',
                '检测到重复的 create_time:\n{}\n\n是否停止爬取？\n\n点击「是」停止，点击「否」跳过继续'.format(create_time))
            result[0] = answer
            event.set()

        self.root.after(0, _ask)
        event.wait()  # 阻塞工作线程直到用户做出选择
        return result[0]

    def _on_file_exists(self, filepath):
        """从工作线程调用，弹窗询问用户是否覆盖文件（线程安全）"""
        result = [False]  # False=追加, True=覆盖
        event = threading.Event()

        def _ask():
            answer = messagebox.askyesno(
                '文件已存在',
                '输出文件已存在：\n{}\n\n是否覆盖文件内容？\n\n点击「是」覆盖，点击「否」追加'.format(
                    os.path.basename(filepath)))
            result[0] = answer
            event.set()

        self.root.after(0, _ask)
        event.wait()
        return result[0]

    def _stop_scraper(self):
        if self.scraper:
            self.scraper.stop()
            self._append_log('已发送停止信号...', 'warn')


def main():
    root = tk.Tk()

    # macOS 特殊处理
    if sys.platform == 'darwin':
        try:
            root.tk.call('tk', 'scaling', 2.0)
        except Exception:
            pass

    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
