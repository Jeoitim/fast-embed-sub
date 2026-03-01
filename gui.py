# gui.py
# We avoid importing any QWidget-derived class at the module level so that
# the library can be safely imported before a QApplication exists.

ABOUT_CONTENT = """
<h2>Fast Embed Sub v0.2.0 beta</h2>
<p><img src="{icon}" width="128" height="128"></p>
<p><b>作者:</b> Jeoitim Yip</p>
<p><b>GitHub:</b> <a href="https://github.com/Jeoitim/fast-embed-sub">https://github.com/Jeoitim/fast-embed-sub</a></p>
<p><b>依赖库:</b></p>
<ul>
    <li>PySide6</li> <a href="https://pypi.org/project/PySide6/">https://pypi.org/project/PySide6/</a></li>
    <li>PySide6-Fluent-Widgets</li> <a href="https://pypi.org/project/PySide6-Fluent-Widgets/">https://pypi.org/project/PySide6-Fluent-Widgets/</a></li>
</ul>
<p><b>鸣谢:</b></p>
<ul>
    <li>FFmpeg 项目</li> <a href="https://ffmpeg.org/">https://ffmpeg.org/</a></li>
    <li>所有开源贡献者</li>
</ul>
"""

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout,
                               QFileDialog, QSizePolicy, QMainWindow, QInputDialog,
                               QWidget, QFrame)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt
import os
import re
import ctypes

from qfluentwidgets import LineEdit as FluentLineEdit, FluentIcon

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
            ComboBox, PushButton, TextEdit, ProgressBar,
            LineEdit, BodyLabel, MessageBox,
            setTheme, Theme, SimpleCardWidget, NavigationInterface,
            NavigationItemPosition, ScrollArea
        )
        setTheme(Theme.DARK)
        
        # 保存组件引用
        self._ComboBox = ComboBox
        self._PushButton = PushButton
        self._TextEdit = TextEdit
        self._ProgressBar = ProgressBar
        self._LineEdit = LineEdit
        self._Label = BodyLabel
        self._MessageBox = MessageBox
        self._SimpleCardWidget = SimpleCardWidget
        self._ScrollArea = ScrollArea

        self.setWindowTitle("Fast Embed Sub")
        self.resize(950, 650)
        
        icon_path = os.path.join("assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # ====== 核心初始化：引擎与信号 ======
        from main import TranscodeEngine
        self.engine = TranscodeEngine()
        self.engine.task_status_changed.connect(self.update_task_ui)
        self.task_widgets = {} # 存储队列UI卡片的字典

        # ====== 导航与页面架构 ======
        self.navigation_interface = NavigationInterface(self, showMenuButton=True)
        from PySide6.QtWidgets import QStackedWidget
        self.stacked_widget = QStackedWidget()
        
        self.create_home_page()
        self.create_log_page()
        self.create_queue_page()
        self.create_about_page()
        
        self.navigation_interface.addItem(
            routeKey='home', icon=FluentIcon.HOME, text='主页',
            onClick=lambda: self.switch_to_page(0), position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey='queue', icon=FluentIcon.HISTORY, text='任务队列',
            onClick=lambda: self.switch_to_page(2), position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey='log', icon=FluentIcon.DOCUMENT, text='日志',
            onClick=lambda: self.switch_to_page(1), position=NavigationItemPosition.TOP
        )
        self.navigation_interface.addItem(
            routeKey='theme', icon=FluentIcon.BRUSH, text='切换主题',
            onClick=self.toggle_theme, position=NavigationItemPosition.BOTTOM
        )
        self.navigation_interface.addItem(
            routeKey='about', icon=FluentIcon.INFO, text='关于',
            onClick=lambda: self.switch_to_page(3), position=NavigationItemPosition.BOTTOM
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
        self.switch_to_page(0)

    def showEvent(self, event):
        super().showEvent(event)
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

    def set_dark_mode_style(self):
        self.setStyleSheet('''
            QMainWindow { background-color: #272727; }
            BodyLabel#appTitle { color: #ffffff; font-size: 20px; font-weight: bold; }
            BodyLabel#sectionTitle { color: #ffffff; font-size: 16px; font-weight: bold; }
            SimpleCardWidget { margin-top: 8px; margin-bottom: 8px; }
            QFrame#taskCard { background-color: rgba(255,255,255,0.05); border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }
        ''')
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 20, ctypes.byref(ctypes.c_int(1)), 4)
        except: pass

    def set_light_mode_style(self):
        self.setStyleSheet('''
            QMainWindow { background-color: #f9f9f9; }
            BodyLabel#appTitle { color: #000000; font-size: 20px; font-weight: bold; }
            BodyLabel#sectionTitle { color: #000000; font-size: 16px; font-weight: bold; }
            SimpleCardWidget { margin-top: 8px; margin-bottom: 8px; }
            QFrame#taskCard { background-color: rgba(0,0,0,0.03); border-radius: 6px; border: 1px solid rgba(0,0,0,0.08); }
        ''')
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 20, ctypes.byref(ctypes.c_int(0)), 4)
        except: pass

    # ================= UI 页面创建 =================

    def create_home_page(self):
        self.home_widget = self._SimpleCardWidget()
        self.main_layout = QVBoxLayout(self.home_widget)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(20)

        header = QHBoxLayout()
        icon_path = os.path.join("assets", "icon.png")
        if os.path.exists(icon_path):
            logo = self._Label()
            logo.setPixmap(QIcon(icon_path).pixmap(32, 32))
            header.addWidget(logo)
        title_label = self._Label("Fast Embed Sub")
        title_label.setObjectName('appTitle')
        header.addWidget(title_label)
        header.addStretch()
        self.main_layout.addLayout(header)

        input_card = self._SimpleCardWidget()
        input_title = self._Label("输入文件")
        input_title.setObjectName("sectionTitle")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.addWidget(input_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.addWidget(self._Label("视频源:"), 0, 0)
        self.video_input = DragDropLineEdit()
        self.video_input.setPlaceholderText("请选择或拖入视频文件...")
        self.btn_browse_video = self._PushButton("浏览")
        self.btn_browse_video.setIcon(QIcon(FluentIcon.FOLDER.value))
        grid.addWidget(self.video_input, 0, 1)
        grid.addWidget(self.btn_browse_video, 0, 2)

        grid.addWidget(self._Label("字幕源:"), 1, 0)
        self.sub_input = DragDropLineEdit()
        self.sub_input.setPlaceholderText("自动检测同名文件，也可手动选择...")
        self.btn_browse_sub = self._PushButton("浏览")
        self.btn_browse_sub.setIcon(QIcon(FluentIcon.FOLDER.value))
        grid.addWidget(self.sub_input, 1, 1)
        grid.addWidget(self.btn_browse_sub, 1, 2)
        input_layout.addLayout(grid)
        self.main_layout.addWidget(input_card)

        output_group = self._SimpleCardWidget()
        output_title = self._Label("输出设置")
        output_title.setObjectName("sectionTitle")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(10, 10, 10, 10)
        output_layout.addWidget(output_title)

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self._Label("输出目录:"))
        self.output_input = DragDropLineEdit()
        self.output_input.setPlaceholderText("默认输出到视频同目录...")
        self.btn_browse_output = self._PushButton("浏览")
        self.btn_browse_output.setIcon(QIcon(FluentIcon.FOLDER.value))
        output_dir_layout.addWidget(self.output_input)
        output_dir_layout.addWidget(self.btn_browse_output)
        output_layout.addLayout(output_dir_layout)

        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self._Label("文件名:"))
        self.filename_input = self._LineEdit()
        self.filename_input.setPlaceholderText("自动使用输入文件名")
        filename_layout.addWidget(self.filename_input)
        filename_layout.addWidget(self._Label("格式:"))
        self.format_combo = self._ComboBox()
        self.format_combo.addItems(['mkv', 'mp4', 'mov'])
        filename_layout.addWidget(self.format_combo)
        output_layout.addLayout(filename_layout)
        self.main_layout.addWidget(output_group)

        preset_card = self._SimpleCardWidget()
        preset_title = self._Label("预设")
        preset_title.setObjectName("sectionTitle")
        preset_layout = QHBoxLayout(preset_card)
        preset_layout.setContentsMargins(10, 10, 10, 10)
        preset_layout.addWidget(preset_title)
        preset_layout.addWidget(self._Label("压制预设:"))
        self.preset_combo = self._ComboBox()
        self.preset_combo.setFixedWidth(150)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        self.main_layout.addWidget(preset_card)

        self.preset_desc = self._Label("预设说明：请选择预设")
        self.preset_desc.setStyleSheet("color: gray; font-style: italic;")
        self.main_layout.addWidget(self.preset_desc)

        self.btn_start = self._PushButton("加入队列")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_start.setIcon(QIcon(FluentIcon.ADD.value))
        self.btn_start.setProperty('type', 'primary')
        self.main_layout.addWidget(self.btn_start)

        self.btn_browse_video.clicked.connect(self.browse_video)
        self.btn_browse_sub.clicked.connect(self.browse_subtitle)
        self.btn_browse_output.clicked.connect(self.browse_output)
        self.btn_start.clicked.connect(self.add_to_queue_action)
        self.preset_combo.currentIndexChanged.connect(self.update_preset_desc)
        self.video_input.textChanged.connect(self.auto_detect_subtitle)

        self.load_presets()
        self.stacked_widget.addWidget(self.home_widget)

    def create_log_page(self):
        self.log_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.log_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        title = self._Label("日志输出")
        title.setObjectName('appTitle')
        layout.addWidget(title)
        
        self.log_output = self._TextEdit()
        self.log_output.setReadOnly(True)
        # 保持终端控制台风格
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        layout.addWidget(self.log_output)
        
        self.btn_export_log = self._PushButton("导出日志")
        self.btn_export_log.clicked.connect(self.export_log)
        layout.addWidget(self.btn_export_log, alignment=Qt.AlignLeft)
        
        self.stacked_widget.addWidget(self.log_widget)

    def create_queue_page(self):
        self.queue_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.queue_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        title = self._Label("任务队列")
        title.setObjectName('appTitle')
        layout.addWidget(title)

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

    def create_about_page(self):
        self.about_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.about_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        title = self._Label("关于")
        title.setObjectName('appTitle')
        layout.addWidget(title)
        
        about_content = self._TextEdit()
        about_content.setReadOnly(True)
        icon_abs_path = os.path.abspath(os.path.join("assets", "icon.png")).replace("\\", "/")
        about_content.setHtml(ABOUT_CONTENT.format(icon=icon_abs_path))
        layout.addWidget(about_content)
        
        self.stacked_widget.addWidget(self.about_widget)

    # ================= 辅助函数与事件 =================

    def switch_to_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def load_presets(self):
        presets = self.engine.get_presets()
        for name, (desc, _) in presets.items():
            self.preset_combo.addItem(name)
        
        index = self.preset_combo.findText("默认")
        if index != -1:
            self.preset_combo.setCurrentIndex(index)
        elif presets:
            self.preset_combo.setCurrentIndex(0)

    def update_preset_desc(self):
        presets = self.engine.get_presets()
        current_name = self.preset_combo.currentText()
        if current_name in presets:
            desc, template = presets[current_name]
            self.preset_desc.setText(f"预设说明：{desc}")
            if re.search(r'\{format:([^}]+)\}', template):
                self.format_combo.setEnabled(False)
            else:
                self.format_combo.setEnabled(True)

    def auto_detect_subtitle(self, video_path):
        if not video_path or not os.path.isfile(video_path): return
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        for ext in ['.srt', '.ass', '.ssa']:
            sub_path = os.path.join(video_dir, video_name + ext)
            if os.path.exists(sub_path):
                self.sub_input.setText(sub_path)
                break

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "视频 (*.mp4 *.mov *.mkv)")
        if file_path: self.video_input.setText(file_path)

    def browse_subtitle(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择字幕", "", "字幕 (*.srt *.ass *.ssa)")
        if file_path: self.sub_input.setText(file_path)

    def browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", "")
        if dir_path:
            self.output_input.setText(dir_path)
            if self.video_input.text():
                self.filename_input.setText(os.path.splitext(os.path.basename(self.video_input.text()))[0])

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出日志", "", "文本文件 (*.txt)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_output.toPlainText())

    def truncate_string(self, text, max_len=25):
        if len(text) <= max_len: return text
        half = (max_len - 3) // 2
        return f"{text[:half]}...{text[-half:]}"

    # ================= 核心业务：队列控制 =================

    def add_to_queue_action(self):
        video = self.video_input.text()
        sub = self.sub_input.text()
        output_dir = self.output_input.text()
        filename = self.filename_input.text() or None
        format_val = self.format_combo.currentText()

        if not video:
            self._MessageBox.warning(self, "警告", "请确保已选择视频文件")
            return

        if not output_dir:
            output_dir = os.path.dirname(video)
            self.output_input.setText(output_dir)

        if not filename:
            filename = os.path.splitext(os.path.basename(video))[0]
            self.filename_input.setText(filename)

        output_path = os.path.join(output_dir, f"{filename}.{format_val}")
        if os.path.exists(output_path):
            new_filename, ok = QInputDialog.getText(
                self, "文件已存在", f"输出文件已存在：\n{output_path}\n\n请输入新的文件名:", 
                self._LineEdit.Normal, filename
            )
            if not ok or not new_filename: return
            filename = new_filename

        current_preset = self.preset_combo.currentText()
        presets = self.engine.get_presets()
        if current_preset in presets:
            template = presets[current_preset][1]
            try:
                if not sub:
                    template = re.sub(r'-vf\s+"subtitles=\'\{input_s\}\'"', '', template)
                    template = re.sub(r'\s+', ' ', template).strip()
                
                task = self.engine.add_to_queue(template, video, sub, output_dir, filename, format_val, current_preset)
                self.create_task_widget(task)
                
                self.navigation_interface.setCurrentItem('queue')
                self.switch_to_page(2)

            except ValueError as e:
                self._MessageBox.critical(self, "错误", f"错误: {str(e)}")

    def create_task_widget(self, task):
        card = QFrame()
        card.setObjectName("taskCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        
        info_label = self._Label()
        info_label.setWordWrap(True)
        
        status_label = self._Label("等待中")
        status_label.setFixedWidth(65)
        status_label.setAlignment(Qt.AlignCenter)
        
        cancel_btn = self._PushButton("取消")
        cancel_btn.setProperty('type', 'danger')
        cancel_btn.setFixedWidth(60)
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
        
        info_text = f"<b>{v_name}</b> <span style='color:gray'>|</span> {task.preset_name} <span style='color:gray'>|</span> {o_name}"
        widgets["info"].setText(info_text)
        
        status_label = widgets["status"]
        cancel_btn = widgets["cancel_btn"]
        
        # 局部UI状态更新
        if task.status == "等待中":
            status_label.setText("等待中")
            status_label.setStyleSheet("color: #808080;")
            cancel_btn.setEnabled(True)
        elif task.status == "压制中":
            status_label.setText(f"{task.progress}%")
            status_label.setStyleSheet("color: #0078D4; font-weight: bold;")
            cancel_btn.setEnabled(True)
        elif task.status == "已完成":
            status_label.setText("已完成")
            status_label.setStyleSheet("color: #28a745; font-weight: bold;")
            cancel_btn.setEnabled(False)
        elif task.status == "已取消":
            status_label.setText("已取消")
            status_label.setStyleSheet("color: #6c757d;")
            cancel_btn.setEnabled(False)
        elif task.status == "失败":
            status_label.setText("失败")
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