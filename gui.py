# gui.py
# We avoid importing any QWidget-derived class at the module level so that
# the library can be safely imported before a QApplication exists.



from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout,
                               QFileDialog, QSizePolicy, QMainWindow,
                               QWidget, QFrame)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt, QTimer, QSettings
import os
import re
import ctypes

from qfluentwidgets import LineEdit as FluentLineEdit, FluentIcon

TRANSLATIONS = {
    'zh': {
        'home': '主页',
        'queue': '任务队列',
        'log': '日志',
        'theme': '切换主题',
        'language': 'English',
        'about': '关于',
        'app_subtitle': '轻量级、极速的字幕视频压制工具',
        'media_sub_sources': '媒体与字幕源',
        'video_source': '视频源文件',
        'video_placeholder': '选择或直接拖入视频文件...',
        'sub_source': '字幕源文件',
        'sub_placeholder': '选择字幕文件 (支持自动检测同名 SRT / ASS / SSA)...',
        'output_settings': '输出与编码设置',
        'output_dir': '输出保存目录',
        'output_dir_placeholder': '默认保存到视频文件同目录...',
        'output_filename': '输出文件名',
        'filename_placeholder': '默认使用输入文件名...',
        'format': '封装格式',
        'preset': '压制预设',
        'preset_desc_default': '预设说明：请选择预设',
        'preset_desc_prefix': '预设说明：',
        'add_to_queue': '加入任务队列',
        'log_output': '日志输出',
        'export_log': '导出日志',
        'clear_queue': '清空队列',
        'empty_queue_confirm_running': '当前有正在处理的任务，清空队列将取消当前正在压制的任务，确定继续吗？',
        'empty_queue_confirm_all': '确定要清空队列中的所有任务吗？',
        'warning': '警告',
        'info': '提示',
        'error': '错误',
        'select_video_warning': '请确保已选择视频文件',
        'output_exists_warning': '输出文件已存在：\n{path}\n\n请更改文件名或输出目录后再试。',
        'about_software': '关于软件',
        'author': '作者:',
        'github': 'GitHub:',
        'license': '许可证:',
        'deps_thanks': '技术依赖与致谢',
        'pyside_desc': '• <b>PySide6</b>: Qt 6 官方 Python 绑定',
        'pysf_desc': '• <b>PySide6-Fluent-Widgets</b>: 微软 Fluent 设计风格组件库',
        'ffmpeg_desc': '• <b>FFmpeg 项目</b>: 极速且强大的音视频核心编解码库',
        'official_link': '官方链接',
        'special_thanks': '特别鸣谢：感谢所有开源社区贡献者对本项目及依赖库的支持。',
        'exit_confirm': '当前有任务正在压制，确定要退出并取消任务吗？',
        'Waiting': '等待中',
        'Encoding': '压制中',
        'Completed': '已完成',
        'Cancelled': '已取消',
        'Failed': '失败',
        
        # Dialogs
        'select_video_dialog_title': '选择视频',
        'video_file_filter': '视频 (*.mp4 *.mov *.mkv)',
        'select_sub_dialog_title': '选择字幕',
        'sub_file_filter': '字幕 (*.srt *.ass *.ssa)',
        'select_output_dir_dialog_title': '选择输出目录',
        'export_log_dialog_title': '导出日志',
        'text_file_filter': '文本文件 (*.txt)',
        
        # Presets
        '默认': '默认',
        '收藏': '收藏',
        '默认_desc': '适合上传视频网站：速度快，画质极高(CRF 18)，体积中等偏大，音频无损直通。',
        '收藏_desc': '适合本地收藏与BT分享：采用 H.265 10bit 编码，体积小画质极佳，但压制速度较慢，音频无损直通。',
    },
    'en': {
        'home': 'Home',
        'queue': 'Task Queue',
        'log': 'Log',
        'theme': 'Toggle Theme',
        'language': '简体中文',
        'about': 'About',
        'app_subtitle': 'Lightweight & high-speed subtitle embed tool',
        'media_sub_sources': 'Media & Subtitle Sources',
        'video_source': 'Source Video File',
        'video_placeholder': 'Select or drag & drop video file here...',
        'sub_source': 'Source Subtitle File',
        'sub_placeholder': 'Select subtitle file (auto-detect same-named SRT/ASS/SSA supported)...',
        'output_settings': 'Output & Encoding Settings',
        'output_dir': 'Output Saving Directory',
        'output_dir_placeholder': 'Default to the same directory as the source video...',
        'output_filename': 'Output Filename',
        'filename_placeholder': 'Default to input filename...',
        'format': 'Container Format',
        'preset': 'Encoding Preset',
        'preset_desc_default': 'Preset description: Please select a preset',
        'preset_desc_prefix': 'Preset description: ',
        'add_to_queue': 'Add to Task Queue',
        'log_output': 'Log Output',
        'export_log': 'Export Log',
        'clear_queue': 'Clear Queue',
        'empty_queue_confirm_running': 'Active tasks are in progress. Clearing the queue will cancel them. Do you want to continue?',
        'empty_queue_confirm_all': 'Are you sure you want to clear all tasks from the queue?',
        'warning': 'Warning',
        'info': 'Info',
        'error': 'Error',
        'select_video_warning': 'Please make sure a video file is selected.',
        'output_exists_warning': 'Output file already exists:\n{path}\n\nPlease change the filename or output directory and try again.',
        'about_software': 'About Software',
        'author': 'Author:',
        'github': 'GitHub:',
        'license': 'License:',
        'deps_thanks': 'Dependencies & Acknowledgements',
        'pyside_desc': '• <b>PySide6</b>: Official Python bindings for Qt 6',
        'pysf_desc': '• <b>PySide6-Fluent-Widgets</b>: Fluent design widgets library for PySide6',
        'ffmpeg_desc': '• <b>FFmpeg Project</b>: Fast and powerful audio/video codec library',
        'official_link': 'Official Link',
        'special_thanks': 'Special thanks to all open-source community contributors for supporting this project and its dependencies.',
        'exit_confirm': 'A task is currently encoding. Are you sure you want to exit and cancel it?',
        'Waiting': 'Waiting',
        'Encoding': 'Encoding',
        'Completed': 'Completed',
        'Cancelled': 'Cancelled',
        'Failed': 'Failed',
        
        # Dialogs
        'select_video_dialog_title': 'Select Video',
        'video_file_filter': 'Video Files (*.mp4 *.mov *.mkv)',
        'select_sub_dialog_title': 'Select Subtitles',
        'sub_file_filter': 'Subtitle Files (*.srt *.ass *.ssa)',
        'select_output_dir_dialog_title': 'Select Output Directory',
        'export_log_dialog_title': 'Export Log',
        'text_file_filter': 'Text Files (*.txt)',
        
        # Presets
        '默认': 'Default',
        '收藏': 'Favorites',
        '默认_desc': 'Suitable for video upload sites: Fast speed, extremely high quality (CRF 18), medium-large size, audio copy.',
        '收藏_desc': 'Suitable for local collection & torrent sharing: H.265 10bit encoding, small size, excellent quality, slower encoding speed, audio copy.',
    }
}

class DragDropLineEdit(FluentLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                self.setText(url.toLocalFile())
                event.acceptProposedAction()
            else:
                super().dropEvent(event)
        else:
            super().dropEvent(event)


class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()

        from qfluentwidgets import (
            ComboBox, PushButton, PrimaryPushButton, ToolButton, HyperlinkButton, TextEdit, ProgressBar,
            LineEdit, BodyLabel, StrongBodyLabel, CaptionLabel, TitleLabel, SubtitleLabel,
            MessageBox, setTheme, Theme, SimpleCardWidget, CardWidget, NavigationInterface,
            NavigationItemPosition, ScrollArea
        )
        setTheme(Theme.DARK)
        
        # 保存组件引用
        self._ComboBox = ComboBox
        self._PushButton = PushButton
        self._PrimaryPushButton = PrimaryPushButton
        self._ToolButton = ToolButton
        self._HyperlinkButton = HyperlinkButton
        self._TextEdit = TextEdit
        self._ProgressBar = ProgressBar
        self._LineEdit = LineEdit
        self._Label = BodyLabel
        self._StrongBodyLabel = StrongBodyLabel
        self._CaptionLabel = CaptionLabel
        self._TitleLabel = TitleLabel
        self._SubtitleLabel = SubtitleLabel
        self._MessageBox = MessageBox
        self._SimpleCardWidget = SimpleCardWidget
        self._CardWidget = CardWidget
        self._ScrollArea = ScrollArea

        # Initialize translation settings
        self.settings = QSettings("Jeoitim", "FastEmbedSub")
        self.lang = self.settings.value("language", "zh")

        self.setWindowTitle("Fast Embed Sub")
        self.resize(950, 650)
        
        icon_path = os.path.join("assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # ====== 核心初始化：引擎与信号 ======
        from engine import TranscodeEngine
        self.engine = TranscodeEngine()
        self.engine.task_status_changed.connect(self.update_task_ui)
        self.engine.log_message.connect(self._on_log_message)
        self.task_widgets = {} # 存储队列UI卡片的字典
        self.log_history = [] # 缓存历史日志

        # ====== 导航与页面架构 ======
        self.navigation_interface = NavigationInterface(self, showMenuButton=True)
        from PySide6.QtWidgets import QStackedWidget
        self.stacked_widget = QStackedWidget()
        
        self.pages = {
            'home': None,
            'log': None,
            'queue': None,
            'about': None
        }
        
        self.navigation_interface.addItem(
            routeKey='home', icon=FluentIcon.HOME, text=self.t('home'),
            onClick=lambda: self.switch_to_page('home'), position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey='queue', icon=FluentIcon.HISTORY, text=self.t('queue'),
            onClick=lambda: self.switch_to_page('queue'), position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey='log', icon=FluentIcon.PRINT, text=self.t('log'),
            onClick=lambda: self.switch_to_page('log'), position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey='theme', icon=FluentIcon.BRIGHTNESS, text=self.t('theme'),
            onClick=self.toggle_theme, position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey='language', icon=FluentIcon.GLOBE, text=self.t('language'),
            onClick=self.toggle_language, position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey='about', icon=FluentIcon.INFO, text=self.t('about'),
            onClick=lambda: self.switch_to_page('about'), position=NavigationItemPosition.BOTTOM
        )
        
        # 构建右侧内容区（StackedWidget + 全局进度条）
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        self.right_layout.addWidget(self.stacked_widget)
        
        # ===== 全局共享进度条 =====
        self.global_progress = self._ProgressBar()
        self.global_progress.setRange(0, 100)
        self.global_progress.setValue(0)
        self.global_progress.setVisible(False)
        self.global_progress.setFixedHeight(4) # 设为细长条更美观
        self.right_layout.addWidget(self.global_progress)

        # 整体布局
        central_widget = self._SimpleCardWidget()
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.navigation_interface)
        layout.addWidget(self.right_widget)
        self.setCentralWidget(central_widget)
        
        self.set_dark_mode_style()
        self.switch_to_page('home')
        
        # 延迟 100ms 加载预设，提高首屏渲染响应度
        QTimer.singleShot(100, self.load_presets)

    def showEvent(self, event):
        super().showEvent(event)

    def closeEvent(self, event):
        # 退出前确保杀死所有正在运行的转码进程，防止 ffmpeg 变成后台僵尸进程
        if self.engine and self.engine.current_task:
            reply = self._MessageBox(self.t("info"), self.t("exit_confirm"), self)
            if reply.exec():
                self.engine.cancel_task(self.engine.current_task.task_id)
                # 等待一会儿让进程完全退出 and 删除未完成文件
                self.engine.process.waitForFinished(1000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        from qfluentwidgets import isDarkTheme
        if isDarkTheme():
            self.set_dark_mode_style()
        else:
            self.set_light_mode_style()

    def toggle_theme(self):
        from qfluentwidgets import toggleTheme, isDarkTheme
        toggleTheme()
        if isDarkTheme():
            self.set_dark_mode_style()
        else:
            self.set_light_mode_style()

    def t(self, key):
        return TRANSLATIONS[self.lang].get(key, key)

    def toggle_language(self):
        self.lang = 'en' if self.lang == 'zh' else 'zh'
        self.settings.setValue("language", self.lang)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle("Fast Embed Sub")
        self.navigation_interface.widget('home').setText(self.t('home'))
        self.navigation_interface.widget('queue').setText(self.t('queue'))
        self.navigation_interface.widget('log').setText(self.t('log'))
        self.navigation_interface.widget('theme').setText(self.t('theme'))
        self.navigation_interface.widget('language').setText(self.t('language'))
        self.navigation_interface.widget('about').setText(self.t('about'))
        
        if self.pages.get('home') is not None:
            self.lbl_subtitle.setText(self.t('app_subtitle'))
            self.lbl_input_title.setText(self.t('media_sub_sources'))
            self.lbl_video_label.setText(self.t('video_source'))
            self.video_input.setPlaceholderText(self.t('video_placeholder'))
            self.lbl_sub_label.setText(self.t('sub_source'))
            self.sub_input.setPlaceholderText(self.t('sub_placeholder'))
            self.lbl_output_title.setText(self.t('output_settings'))
            self.lbl_output_dir_label.setText(self.t('output_dir'))
            self.output_input.setPlaceholderText(self.t('output_dir_placeholder'))
            self.lbl_filename_label.setText(self.t('output_filename'))
            self.filename_input.setPlaceholderText(self.t('filename_placeholder'))
            self.lbl_format_label.setText(self.t('format'))
            self.lbl_preset_label.setText(self.t('preset'))
            self.btn_start.setText(self.t('add_to_queue'))
            self.load_presets()
            
        if self.pages.get('log') is not None:
            self.lbl_log_title.setText(self.t('log_output'))
            self.btn_export_log.setText(self.t('export_log'))
            
        if self.pages.get('queue') is not None:
            self.lbl_queue_title.setText(self.t('queue'))
            self.btn_clear_queue.setText(self.t('clear_queue'))
            for task_id in list(self.task_widgets.keys()):
                self.update_task_ui(task_id)
                
        if self.pages.get('about') is not None:
            self.lbl_info_title.setText(self.t('about_software'))
            self.lbl_author_label.setText(self.t('author'))
            self.lbl_github_label.setText(self.t('github'))
            self.lbl_license_label.setText(self.t('license'))
            self.lbl_deps_title.setText(self.t('deps_thanks'))
            self.lbl_pyside_desc.setText(self.t('pyside_desc'))
            self.lbl_pysf_desc.setText(self.t('pysf_desc'))
            self.lbl_ffmpeg_desc.setText(self.t('ffmpeg_desc'))
            self.btn_pyside_link.setText(self.t('official_link'))
            self.btn_pysf_link.setText(self.t('official_link'))
            self.btn_ffmpeg_link.setText(self.t('official_link'))
            self.lbl_special_thanks.setText(self.t('special_thanks'))

    def set_dark_mode_style(self):
        self.setStyleSheet('''
            QMainWindow { background-color: #202020; }
            QScrollArea { background: transparent; border: none; }
            QWidget#homeWidget { background: transparent; }
            
            /* CardWidget Style */
            CardWidget {
                background-color: rgba(30, 30, 30, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
            
            /* Title Labels */
            TitleLabel#appTitle {
                color: #ffffff;
                font-weight: 600;
            }
            
            /* Preset Desc Card */
            QFrame#presetDescCard {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
            }
            
            /* Task Card Styling */
            QFrame#taskCard {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QFrame#taskCard:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
        ''')
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 20, ctypes.byref(ctypes.c_int(1)), 4)
        except: pass

    def set_light_mode_style(self):
        self.setStyleSheet('''
            QMainWindow { background-color: #f3f3f3; }
            QScrollArea { background: transparent; border: none; }
            QWidget#homeWidget { background: transparent; }
            
            /* CardWidget Style */
            CardWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 8px;
            }
            
            /* Title Labels */
            TitleLabel#appTitle {
                color: #000000;
                font-weight: 600;
            }
            
            /* Preset Desc Card */
            QFrame#presetDescCard {
                background-color: rgba(0, 0, 0, 0.02);
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 6px;
            }
            
            /* Task Card Styling */
            QFrame#taskCard {
                background-color: rgba(0, 0, 0, 0.02);
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
            QFrame#taskCard:hover {
                background-color: rgba(0, 0, 0, 0.04);
                border: 1px solid rgba(0, 0, 0, 0.08);
            }
        ''')
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 20, ctypes.byref(ctypes.c_int(0)), 4)
        except: pass

    # ================= UI 页面创建 =================

    def create_home_page(self):
        # Create ScrollArea to contain the home interface, ensuring no overflow on smaller windows
        self.home_scroll = self._ScrollArea()
        self.home_scroll.setObjectName("homeScroll")
        self.home_scroll.setWidgetResizable(True)
        self.home_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.home_scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        self.home_widget = QWidget()
        self.home_widget.setObjectName("homeWidget")
        self.home_widget.setStyleSheet("QWidget#homeWidget { background: transparent; }")
        self.home_scroll.setWidget(self.home_widget)

        self.main_layout = QVBoxLayout(self.home_widget)
        self.main_layout.setContentsMargins(32, 24, 32, 24)
        self.main_layout.setSpacing(24)

        # Title section
        header = QHBoxLayout()
        header.setSpacing(12)
        
        icon_path = os.path.join("assets", "icon.png")
        if os.path.exists(icon_path):
            logo = self._Label()
            logo.setPixmap(QIcon(icon_path).pixmap(36, 36))
            header.addWidget(logo)
            
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title_label = self._TitleLabel("Fast Embed Sub")
        title_label.setObjectName('appTitle')
        self.lbl_subtitle = self._CaptionLabel(self.t("app_subtitle"))
        self.lbl_subtitle.setStyleSheet("color: #a0a0a0;")
        
        title_container.addWidget(title_label)
        title_container.addWidget(self.lbl_subtitle)
        
        header.addLayout(title_container)
        header.addStretch()
        self.main_layout.addLayout(header)

        # Media sources Card
        input_card = self._CardWidget()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(16)
        
        self.lbl_input_title = self._SubtitleLabel(self.t("media_sub_sources"))
        input_layout.addWidget(self.lbl_input_title)
        
        # Video Input Row
        video_block = QVBoxLayout()
        video_block.setSpacing(6)
        self.lbl_video_label = self._StrongBodyLabel(self.t("video_source"))
        video_sub = QHBoxLayout()
        self.video_input = DragDropLineEdit()
        self.video_input.setPlaceholderText(self.t("video_placeholder"))
        self.btn_browse_video = self._ToolButton(self)
        self.btn_browse_video.setIcon(FluentIcon.VIDEO)
        video_sub.addWidget(self.video_input)
        video_sub.addWidget(self.btn_browse_video)
        video_block.addWidget(self.lbl_video_label)
        video_block.addLayout(video_sub)
        input_layout.addLayout(video_block)
        
        # Subtitle Input Row
        sub_block = QVBoxLayout()
        sub_block.setSpacing(6)
        self.lbl_sub_label = self._StrongBodyLabel(self.t("sub_source"))
        sub_sub = QHBoxLayout()
        self.sub_input = DragDropLineEdit()
        self.sub_input.setPlaceholderText(self.t("sub_placeholder"))
        self.btn_browse_sub = self._ToolButton(self)
        self.btn_browse_sub.setIcon(FluentIcon.DOCUMENT)
        sub_sub.addWidget(self.sub_input)
        sub_sub.addWidget(self.btn_browse_sub)
        sub_block.addWidget(self.lbl_sub_label)
        sub_block.addLayout(sub_sub)
        input_layout.addLayout(sub_block)
        
        self.main_layout.addWidget(input_card)

        # Output and Encoding Settings Card
        output_card = self._CardWidget()
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(16)
        
        self.lbl_output_title = self._SubtitleLabel(self.t("output_settings"))
        output_layout.addWidget(self.lbl_output_title)
        
        # Output Directory Row
        output_dir_block = QVBoxLayout()
        output_dir_block.setSpacing(6)
        self.lbl_output_dir_label = self._StrongBodyLabel(self.t("output_dir"))
        output_dir_sub = QHBoxLayout()
        self.output_input = DragDropLineEdit()
        self.output_input.setPlaceholderText(self.t("output_dir_placeholder"))
        self.btn_browse_output = self._ToolButton(self)
        self.btn_browse_output.setIcon(FluentIcon.FOLDER)
        output_dir_sub.addWidget(self.output_input)
        output_dir_sub.addWidget(self.btn_browse_output)
        output_dir_block.addWidget(self.lbl_output_dir_label)
        output_dir_block.addLayout(output_dir_sub)
        output_layout.addLayout(output_dir_block)
        
        # Filename & Format Row
        name_format_row = QHBoxLayout()
        name_format_row.setSpacing(16)
        
        filename_block = QVBoxLayout()
        filename_block.setSpacing(6)
        self.lbl_filename_label = self._StrongBodyLabel(self.t("output_filename"))
        self.filename_input = self._LineEdit()
        self.filename_input.setPlaceholderText(self.t("filename_placeholder"))
        filename_block.addWidget(self.lbl_filename_label)
        filename_block.addWidget(self.filename_input)
        name_format_row.addLayout(filename_block, 3)
        
        format_block = QVBoxLayout()
        format_block.setSpacing(6)
        self.lbl_format_label = self._StrongBodyLabel(self.t("format"))
        self.format_combo = self._ComboBox()
        self.format_combo.addItems(['mp4', 'mkv', 'mov'])
        self.format_combo.setMinimumWidth(120)
        format_block.addWidget(self.lbl_format_label)
        format_block.addWidget(self.format_combo)
        name_format_row.addLayout(format_block, 1)
        
        output_layout.addLayout(name_format_row)
        
        # Preset Row
        preset_block = QVBoxLayout()
        preset_block.setSpacing(6)
        self.lbl_preset_label = self._StrongBodyLabel(self.t("preset"))
        
        preset_combo_layout = QHBoxLayout()
        self.preset_combo = self._ComboBox()
        self.preset_combo.setFixedWidth(200)
        preset_combo_layout.addWidget(self.preset_combo)
        preset_combo_layout.addStretch()
        preset_block.addWidget(self.lbl_preset_label)
        preset_block.addLayout(preset_combo_layout)
        
        # Preset description card
        self.preset_desc_card = QFrame()
        self.preset_desc_card.setObjectName("presetDescCard")
        desc_card_layout = QHBoxLayout(self.preset_desc_card)
        desc_card_layout.setContentsMargins(12, 10, 12, 10)
        desc_card_layout.setSpacing(8)
        
        info_icon = self._Label()
        info_icon.setPixmap(FluentIcon.INFO.icon().pixmap(16, 16))
        
        self.preset_desc = self._CaptionLabel(self.t("preset_desc_default"))
        self.preset_desc.setWordWrap(True)
        
        desc_card_layout.addWidget(info_icon)
        desc_card_layout.addWidget(self.preset_desc, 1)
        preset_block.addWidget(self.preset_desc_card)
        
        output_layout.addLayout(preset_block)
        
        self.main_layout.addWidget(output_card)
 
        # Add to Queue Button
        self.btn_start = self._PrimaryPushButton(self.t("add_to_queue"), self)
        self.btn_start.setMinimumHeight(44)
        self.btn_start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_start.setIcon(FluentIcon.ADD)
        self.main_layout.addWidget(self.btn_start)
 
        self.btn_browse_video.clicked.connect(self.browse_video)
        self.btn_browse_sub.clicked.connect(self.browse_subtitle)
        self.btn_browse_output.clicked.connect(self.browse_output)
        self.btn_start.clicked.connect(self.add_to_queue_action)
        self.preset_combo.currentIndexChanged.connect(self.update_preset_desc)
        self.video_input.textChanged.connect(self.on_video_changed)
 
        self.stacked_widget.addWidget(self.home_scroll)
        self.pages['home'] = self.home_scroll
 
    def create_log_page(self):
        self.log_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.log_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.lbl_log_title = self._Label(self.t("log_output"))
        self.lbl_log_title.setObjectName('appTitle')
        layout.addWidget(self.lbl_log_title)
        
        self.log_output = self._TextEdit()
        self.log_output.setReadOnly(True)
        # 保持终端控制台风格
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        layout.addWidget(self.log_output)
        
        # 填充历史日志
        for log in self.log_history:
            self.log_output.append(log)
        
        self.btn_export_log = self._PushButton(self.t("export_log"))
        self.btn_export_log.clicked.connect(self.export_log)
        layout.addWidget(self.btn_export_log, alignment=Qt.AlignLeft)
        
        self.stacked_widget.addWidget(self.log_widget)
        self.pages['log'] = self.log_widget
 
    def create_queue_page(self):
        self.queue_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.queue_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title bar with Clear Button
        title_layout = QHBoxLayout()
        self.lbl_queue_title = self._TitleLabel(self.t("queue"))
        self.lbl_queue_title.setObjectName('appTitle')
        title_layout.addWidget(self.lbl_queue_title)
        
        title_layout.addStretch()
        
        self.btn_clear_queue = self._PushButton(self.t("clear_queue"), self)
        self.btn_clear_queue.setIcon(FluentIcon.DELETE)
        self.btn_clear_queue.clicked.connect(self.clear_queue_action)
        title_layout.addWidget(self.btn_clear_queue)
        
        layout.addLayout(title_layout)
 
        self.queue_scroll = self._ScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        
        self.queue_scroll_content = QWidget()
        self.queue_scroll_content.setStyleSheet("background: transparent;")
        self.queue_layout = QVBoxLayout(self.queue_scroll_content)
        self.queue_layout.setAlignment(Qt.AlignTop)
        self.queue_layout.setSpacing(8)
        
        self.queue_scroll.setWidget(self.queue_scroll_content)
        layout.addWidget(self.queue_scroll)
        
        self.stacked_widget.addWidget(self.queue_widget)
        self.pages['queue'] = self.queue_widget
 
    def create_about_page(self):
        self.about_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.about_widget)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # 1. Header with App Title & Subtitle & Logo
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        logo = self._Label()
        icon_path = os.path.abspath(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            logo.setPixmap(QIcon(icon_path).pixmap(64, 64))
        header_layout.addWidget(logo)
        
        title_v_layout = QVBoxLayout()
        title_v_layout.setSpacing(4)
        
        app_name = self._TitleLabel("Fast Embed Sub")
        version_label = self._SubtitleLabel("v0.3.0 beta")
        version_label.setStyleSheet("color: #0078D4; font-weight: bold;")
        
        title_v_layout.addWidget(app_name)
        title_v_layout.addWidget(version_label)
        header_layout.addLayout(title_v_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 2. Software details Card
        info_card = self._CardWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)
        
        self.lbl_info_title = self._StrongBodyLabel(self.t("about_software"))
        self.lbl_info_title.setStyleSheet("font-size: 16px;")
        info_layout.addWidget(self.lbl_info_title)
        
        # Grid of key-values
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.lbl_author_label = self._Label(self.t("author"))
        grid.addWidget(self.lbl_author_label, 0, 0)
        grid.addWidget(self._Label("Jeoitim Yip"), 0, 1)
        
        self.lbl_github_label = self._Label(self.t("github"))
        grid.addWidget(self.lbl_github_label, 1, 0)
        github_link = self._HyperlinkButton("https://github.com/Jeoitim/fast-embed-sub", "https://github.com/Jeoitim/fast-embed-sub", self)
        grid.addWidget(github_link, 1, 1)
        
        self.lbl_license_label = self._Label(self.t("license"))
        grid.addWidget(self.lbl_license_label, 2, 0)
        grid.addWidget(self._Label("MIT License"), 2, 1)
        
        info_layout.addLayout(grid)
        layout.addWidget(info_card)
        
        # 3. Credits & Dependencies Card
        deps_card = self._CardWidget()
        deps_layout = QVBoxLayout(deps_card)
        deps_layout.setContentsMargins(20, 20, 20, 20)
        deps_layout.setSpacing(12)
        
        self.lbl_deps_title = self._StrongBodyLabel(self.t("deps_thanks"))
        self.lbl_deps_title.setStyleSheet("font-size: 16px;")
        deps_layout.addWidget(self.lbl_deps_title)
        
        pyside_layout = QHBoxLayout()
        self.lbl_pyside_desc = self._Label(self.t("pyside_desc"))
        pyside_layout.addWidget(self.lbl_pyside_desc)
        pyside_layout.addStretch()
        self.btn_pyside_link = self._HyperlinkButton("https://pypi.org/project/PySide6/", self.t("official_link"), self)
        pyside_layout.addWidget(self.btn_pyside_link)
        deps_layout.addLayout(pyside_layout)
        
        pysf_layout = QHBoxLayout()
        self.lbl_pysf_desc = self._Label(self.t("pysf_desc"))
        pysf_layout.addWidget(self.lbl_pysf_desc)
        pysf_layout.addStretch()
        self.btn_pysf_link = self._HyperlinkButton("https://pypi.org/project/PySide6-Fluent-Widgets/", self.t("official_link"), self)
        pysf_layout.addWidget(self.btn_pysf_link)
        deps_layout.addLayout(pysf_layout)
        
        ffmpeg_layout = QHBoxLayout()
        self.lbl_ffmpeg_desc = self._Label(self.t("ffmpeg_desc"))
        ffmpeg_layout.addWidget(self.lbl_ffmpeg_desc)
        ffmpeg_layout.addStretch()
        self.btn_ffmpeg_link = self._HyperlinkButton("https://ffmpeg.org/", self.t("official_link"), self)
        ffmpeg_layout.addWidget(self.btn_ffmpeg_link)
        deps_layout.addLayout(ffmpeg_layout)
        
        self.lbl_special_thanks = self._Label(self.t("special_thanks"))
        deps_layout.addWidget(self.lbl_special_thanks)
        
        layout.addWidget(deps_card)
        layout.addStretch()
        
        self.stacked_widget.addWidget(self.about_widget)
        self.pages['about'] = self.about_widget

    # ================= 辅助函数与事件 =================

    def switch_to_page(self, name):
        if self.pages.get(name) is None:
            if name == 'home':
                self.create_home_page()
            elif name == 'log':
                self.create_log_page()
            elif name == 'queue':
                self.create_queue_page()
            elif name == 'about':
                self.create_about_page()
        widget = self.pages.get(name)
        if widget:
            self.stacked_widget.setCurrentWidget(widget)

    def load_presets(self):
        current_sel = self.preset_combo.currentData()
        
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        
        presets = self.engine.get_presets()
        for name, (desc, _) in presets.items():
            translated_name = self.t(name)
            self.preset_combo.addItem(translated_name, userData=name)
            
        self.preset_combo.blockSignals(False)
        
        if current_sel:
            index = self.preset_combo.findData(current_sel)
            if index != -1:
                self.preset_combo.setCurrentIndex(index)
            else:
                self.preset_combo.setCurrentIndex(0)
        else:
            index = self.preset_combo.findData("默认")
            if index != -1:
                self.preset_combo.setCurrentIndex(index)
            elif presets:
                self.preset_combo.setCurrentIndex(0)

    def update_preset_desc(self):
        presets = self.engine.get_presets()
        current_name = self.preset_combo.currentData()
        if current_name in presets:
            desc, template = presets[current_name]
            desc_key = f"{current_name}_desc"
            translated_desc = self.t(desc_key)
            if translated_desc == desc_key:
                translated_desc = desc
            self.preset_desc.setText(f"{self.t('preset_desc_prefix')}{translated_desc}")
            if re.search(r'\{format:([^}]+)\}', template):
                self.format_combo.setEnabled(False)
            else:
                self.format_combo.setEnabled(True)

    def on_video_changed(self, video_path):
        if not video_path or not os.path.isfile(video_path): return
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 自动更新文件名与输出目录
        self.filename_input.setText(video_name)
        self.output_input.setText(video_dir)
        
        # 自动检测同名外部字幕（先清空，防止旧字幕残留）
        self.sub_input.clear()
        for ext in ['.srt', '.ass', '.ssa']:
            sub_path = os.path.join(video_dir, video_name + ext)
            if os.path.exists(sub_path):
                self.sub_input.setText(sub_path)
                break

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.t("select_video_dialog_title"), "", self.t("video_file_filter"))
        if file_path: self.video_input.setText(file_path)

    def browse_subtitle(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.t("select_sub_dialog_title"), "", self.t("sub_file_filter"))
        if file_path: self.sub_input.setText(file_path)

    def browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, self.t("select_output_dir_dialog_title"), "")
        if dir_path:
            self.output_input.setText(dir_path)
            if self.video_input.text():
                self.filename_input.setText(os.path.splitext(os.path.basename(self.video_input.text()))[0])

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, self.t("export_log_dialog_title"), "", self.t("text_file_filter"))
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_output.toPlainText())

    def truncate_string(self, text, max_len=25):
        if len(text) <= max_len: return text
        half = (max_len - 3) // 2
        return f"{text[:half]}...{text[-half:]}"

    def show_warning(self, title, content):
        w = self._MessageBox(title, content, self)
        w.hideCancelButton()
        w.exec()

    def show_critical(self, title, content):
        w = self._MessageBox(title, content, self)
        w.hideCancelButton()
        w.exec()

    def clear_queue_action(self):
        is_running = any(t.status == "压制中" for t in self.engine.queue)
        if is_running:
            confirm = self._MessageBox(self.t("warning"), self.t("empty_queue_confirm_running"), self)
            if not confirm.exec():
                return
        else:
            confirm = self._MessageBox(self.t("info"), self.t("empty_queue_confirm_all"), self)
            if not confirm.exec():
                return

        # 调用引擎清空任务
        self.engine.clear_queue()

        # 从 UI 布局中删除所有任务卡片
        while self.queue_layout.count() > 0:
            item = self.queue_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        self.task_widgets.clear()
        
        # 隐藏全局进度条
        self.global_progress.setVisible(False)
        self.global_progress.setValue(0)

    # ================= 核心业务：队列控制 =================

    def add_to_queue_action(self):
        video = self.video_input.text()
        sub = self.sub_input.text()
        output_dir = self.output_input.text()
        filename = self.filename_input.text() or None
        format_val = self.format_combo.currentText()

        if not video:
            self.show_warning(self.t("warning"), self.t("select_video_warning"))
            return

        if not output_dir:
            output_dir = os.path.dirname(video)
            self.output_input.setText(output_dir)

        if not filename:
            filename = os.path.splitext(os.path.basename(video))[0]
            self.filename_input.setText(filename)

        output_path = os.path.join(output_dir, f"{filename}.{format_val}")
        if os.path.exists(output_path):
            self.show_warning(self.t("warning"), self.t("output_exists_warning").format(path=output_path))
            return

        current_preset = self.preset_combo.currentData()
        presets = self.engine.get_presets()
        if current_preset in presets:
            template = presets[current_preset][1]
            try:
                if not sub:
                    template = re.sub(r'-vf\s+"subtitles=\'\{input_s\}\'"', '', template)
                    template = re.sub(r'\s+', ' ', template).strip()
                
                task = self.engine.add_to_queue(template, video, sub, output_dir, filename, format_val, current_preset)
                self.switch_to_page('queue')
                self.navigation_interface.setCurrentItem('queue')
                self.create_task_widget(task)

            except ValueError as e:
                self.show_critical(self.t("error"), f"{self.t('error')}: {str(e)}")

    def create_task_widget(self, task):
        card = QFrame()
        card.setObjectName("taskCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        info_label = self._Label()
        info_label.setWordWrap(True)
        
        status_label = self._Label(self.t("Waiting"))
        status_label.setFixedWidth(80)
        status_label.setAlignment(Qt.AlignCenter)
        
        cancel_btn = self._ToolButton(self)
        cancel_btn.setIcon(FluentIcon.CLOSE)
        cancel_btn.setFixedWidth(36)
        cancel_btn.clicked.connect(lambda: self.engine.cancel_task(task.task_id))
        
        layout.addWidget(info_label, 1)
        layout.addWidget(status_label)
        layout.addWidget(cancel_btn)
        
        self.queue_layout.addWidget(card)
        
        self.task_widgets[task.task_id] = {
            "card": card,
            "info": info_label,
            "status": status_label,
            "cancel_btn": cancel_btn
        }
        self.update_task_ui(task.task_id)

    def update_task_ui(self, task_id):
        task = next((t for t in self.engine.queue if t.task_id == task_id), None)
        if not task or task_id not in self.task_widgets: return
            
        widgets = self.task_widgets[task_id]
        
        v_name = self.truncate_string(os.path.basename(task.video), 25)
        o_name = self.truncate_string(os.path.basename(task.output_path), 25)
        
        translated_preset = self.t(task.preset_name)
        info_text = f"<b>{v_name}</b> <span style='color:gray'>|</span> {translated_preset} <span style='color:gray'>|</span> {o_name}"
        widgets["info"].setText(info_text)
        
        status_label = widgets["status"]
        cancel_btn = widgets["cancel_btn"]
        
        # 局部UI状态更新
        if task.status == "等待中":
            status_label.setText(self.t("Waiting"))
            status_label.setStyleSheet("color: #808080;")
            cancel_btn.setEnabled(True)
        elif task.status == "压制中":
            status_label.setText(f"{task.progress}%")
            status_label.setStyleSheet("color: #0078D4; font-weight: bold;")
            cancel_btn.setEnabled(True)
        elif task.status == "已完成":
            status_label.setText(self.t("Completed"))
            status_label.setStyleSheet("color: #28a745; font-weight: bold;")
            cancel_btn.setEnabled(False)
        elif task.status == "已取消":
            status_label.setText(self.t("Cancelled"))
            status_label.setStyleSheet("color: #6c757d;")
            cancel_btn.setEnabled(False)
        elif task.status == "失败":
            status_label.setText(self.t("Failed"))
            status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            cancel_btn.setEnabled(False)

        # ====== 全局共享进度条逻辑 ======
        if task.status == "压制中":
            self.global_progress.setVisible(True)
            self.global_progress.setValue(task.progress)
        elif task.status in ["已完成", "已取消", "失败"]:
            # 如果当前没有任何任务在“压制中”，则隐藏进度条并归零
            is_running = any(t.status == "压制中" for t in self.engine.queue)
            if not is_running:
                self.global_progress.setVisible(False)
                self.global_progress.setValue(0)

    def _on_log_message(self, message, color):
        if self.lang == 'en':
            message = message.replace("<b>[警告]</b>", "<b>[WARNING]</b>")
            message = message.replace("未在 components/ 目录下检测到 ffmpeg.exe，且环境变量中没有找到 ffmpeg。压制任务将无法正常运行！", 
                                      "ffmpeg.exe was not detected in the components/ directory, and ffmpeg was not found in environment variables. Encoding tasks will not work properly!")
            message = message.replace("<b>[队列]</b> 任务已添加:", "<b>[Queue]</b> Task added:")
            message = message.replace("开始压制...", "Started encoding...")
            message = message.replace("执行命令:", "Executing command:")
            message = message.replace("<b>[队列]</b> 所有任务处理完毕", "<b>[Queue]</b> All tasks completed")
            message = message.replace("<b>[队列]</b> 任务队列已清空", "<b>[Queue]</b> Task queue cleared")
            message = message.replace("已删除未完成文件:", "Deleted incomplete file:")
            message = message.replace("删除文件失败:", "Failed to delete file:")
            message = message.replace("任务已手动取消", "Task manually cancelled")
            message = message.replace("压制成功", "Successfully encoded")
            message = message.replace("压制失败", "Encoding failed")
            message = message.replace("退出码:", "Exit code:")
            
        styled = f'<span style="color: {color};">{message}</span>' if color else message
        self.log_history.append(styled)
        if self.pages.get('log') is not None:
            self.log_output.append(styled)