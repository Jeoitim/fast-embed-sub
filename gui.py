# gui.py
# We avoid importing any QWidget-derived class at the module level so that
# the library can be safely imported before a QApplication exists.  When
# the fluent widgets package (`qfluentwidgets` from PyPI name
# `PySide6-Fluent-Widgets`) is available we lazily pull in its components
# inside MainUI.__init__ (after the application has been created).  This
# branch no longer supports falling back to native Qt widgets.

# 关于页信息变量
ABOUT_CONTENT = """
<h2>Fast Embed Sub v0.1.0 beta</h2>
<p><b>作者:</b> Jeoitim Yip</p>
<p><b>GitHub:</b> <a href="https://github.com/Jeoitim/fast-embed-sub">https://github.com/Jeoitim/fast-embed-sub</a></p>
<p><b>依赖库:</b></p>
<ul>
    <li>PySide6</li>
    <li>PySide6-Fluent-Widgets</li>
</ul>
<p><b>鸣谢:</b></p>
<ul>
    <li>FFmpeg项目</li>
    <li>所有开源贡献者</li>
</ul>
"""

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout,
                               QFileDialog, QSizePolicy, QToolBar, QMainWindow, QInputDialog)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction
from PySide6.QtCore import Qt, QTimer, QProcess, QMimeData
import os
import re
import sys

# 修改：从 qfluentwidgets 导入 NavigationInterface 和相关组件
from qfluentwidgets import LineEdit as FluentLineEdit, FluentIcon
from PySide6.QtGui import QIcon


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

# 修改：将 FluentWindow 替换为 QMainWindow 并添加导航功能
class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # import fluent widgets from the PySide6‑Fluent‑Widgets package.
        # actual import name is `qfluentwidgets`.  class names are plain
        # (ComboBox, PushButton, etc.) rather than prefixed with "Fluent".
        from qfluentwidgets import (
            ComboBox, PushButton, TextEdit,
            ProgressBar, LineEdit, BodyLabel, MessageBox,
            setTheme, Theme, SimpleCardWidget, NavigationInterface,
            NavigationItemPosition
        )
        setTheme(Theme.DARK)
        # additional stylesheet tweaks
        self.setStyleSheet('''
            BodyLabel#appTitle { color: #0078D4; font-size: 20px; }
            SimpleCardWidget { margin-top: 8px; margin-bottom: 8px; }
        ''')

        # keep references to the classes so they can be used below
        self._ComboBox = ComboBox
        self._PushButton = PushButton
        self._TextEdit = TextEdit
        self._ProgressBar = ProgressBar
        self._LineEdit = LineEdit
        self._Label = BodyLabel  # 修改为 BodyLabel
        self._MessageBox = MessageBox
        self._SimpleCardWidget = SimpleCardWidget

        self.setWindowTitle("Fast Embed Sub")
        self.resize(900, 600)  # 增加窗口宽度以容纳侧边栏
        # 设置应用图标（同时在标题栏显示）
        icon_path = os.path.join("assets", "icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 图标文件 {icon_path} 不存在")

        # 创建导航界面
        self.navigation_interface = NavigationInterface(self, showMenuButton=True)
        
        # 创建堆叠窗口用于页面切换
        from PySide6.QtWidgets import QStackedWidget
        self.stacked_widget = QStackedWidget()
        
        # 创建各个页面
        self.create_home_page()
        self.create_log_page()
        self.create_about_page()
        
        # 添加导航项
        self.navigation_interface.addItem(
            routeKey='home',
            icon=FluentIcon.HOME,
            text='主页',
            onClick=lambda: self.switch_to_page(0),
            position=NavigationItemPosition.TOP
        )
        
        self.navigation_interface.addItem(
            routeKey='log',
            icon=FluentIcon.FONT,
            text='日志',
            onClick=lambda: self.switch_to_page(1),
            position=NavigationItemPosition.TOP
        )
        
        self.navigation_interface.addItem(
            routeKey='about',
            icon=FluentIcon.INFO,
            text='关于',
            onClick=lambda: self.switch_to_page(2),
            position=NavigationItemPosition.BOTTOM
        )
        
        # 设置中心部件
        central_widget = self._SimpleCardWidget()
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.navigation_interface)
        layout.addWidget(self.stacked_widget)
        self.setCentralWidget(central_widget)
        
        # 默认显示主页
        self.switch_to_page(0)

    def create_home_page(self):
        """创建主页"""
        self.home_widget = self._SimpleCardWidget()
        self.main_layout = QVBoxLayout(self.home_widget)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(20)

        # 页眉：logo + 应用标题
        header = QHBoxLayout()
        icon_path = os.path.join("assets", "icon.jpg")
        if os.path.exists(icon_path):
            logo = self._Label()
            logo.setPixmap(QIcon(icon_path).pixmap(32, 32))
            header.addWidget(logo)
        title_label = self._Label("Fast Embed Sub")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title_label)
        header.addStretch()
        self.main_layout.addLayout(header)

        # 输入文件卡片
        input_card = self._SimpleCardWidget()

        # 手动添加标题标签
        input_title = self._Label("输入文件")
        input_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)
        input_layout.addWidget(input_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        # 1. 视频源
        grid.addWidget(self._Label("视频源:"), 0, 0)
        self.video_input = DragDropLineEdit()
        self.video_input.setPlaceholderText("请选择或拖入视频文件...")
        self.btn_browse_video = self._PushButton("浏览")
        # 修改：使用 FluentIcon.FOLDER.value 获取图标
        self.btn_browse_video.setIcon(QIcon(FluentIcon.FOLDER.value))
        self.btn_browse_video.setProperty('type', 'secondary')
        grid.addWidget(self.video_input, 0, 1)
        grid.addWidget(self.btn_browse_video, 0, 2)

        # 2. 字幕源
        grid.addWidget(self._Label("字幕源:"), 1, 0)
        self.sub_input = DragDropLineEdit()
        self.sub_input.setPlaceholderText("自动检测同名文件，也可手动选择...")
        self.btn_browse_sub = self._PushButton("浏览")
        # 修改：使用 FluentIcon.FOLDER.value 获取图标
        self.btn_browse_sub.setIcon(QIcon(FluentIcon.FOLDER.value))
        self.btn_browse_sub.setProperty('type', 'secondary')
        grid.addWidget(self.sub_input, 1, 1)
        grid.addWidget(self.btn_browse_sub, 1, 2)

        input_layout.addLayout(grid)
        self.main_layout.addWidget(input_card)

        # 输出设置卡片
        output_group = self._SimpleCardWidget()

        # 手动添加标题标签
        output_title = self._Label("输出设置")
        output_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(10, 10, 10, 10)
        output_layout.setSpacing(10)
        output_layout.addWidget(output_title)

        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self._Label("输出目录:"))
        self.output_input = DragDropLineEdit()
        self.output_input.setPlaceholderText("默认输出到视频同目录...")
        self.btn_browse_output = self._PushButton("浏览")
        # 修改：使用 FluentIcon.FOLDER.value 获取图标
        self.btn_browse_output.setIcon(QIcon(FluentIcon.FOLDER.value))
        self.btn_browse_output.setProperty('type', 'secondary')
        output_dir_layout.addWidget(self.output_input)
        output_dir_layout.addWidget(self.btn_browse_output)
        output_layout.addLayout(output_dir_layout)

        # 文件名和格式设置
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

        # 预设选择区
        preset_card = self._SimpleCardWidget()

        # 手动添加标题标签
        preset_title = self._Label("预设")
        preset_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        preset_layout = QHBoxLayout(preset_card)
        preset_layout.setContentsMargins(10, 10, 10, 10)
        preset_layout.addWidget(preset_title)
        preset_layout.addWidget(self._Label("压制预设:"))
        self.preset_combo = self._ComboBox()
        # 替代方案：设置固定宽度
        self.preset_combo.setFixedWidth(150)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        self.main_layout.addWidget(preset_card)

        # 预设备注显示
        self.preset_desc = self._Label("预设说明：请选择预设")
        self.preset_desc.setStyleSheet("color: gray; font-style: italic;")
        self.main_layout.addWidget(self.preset_desc)

        # 开始和取消按钮
        button_layout = QHBoxLayout()
        self.btn_start = self._PushButton("开始压制")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 修改：使用 FluentIcon.PLAY.value 获取图标
        self.btn_start.setIcon(QIcon(FluentIcon.PLAY.value))
        self.btn_start.setProperty('type', 'primary')
        
        self.btn_cancel = self._PushButton("取消")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 修改：使用 FluentIcon.CANCEL.value 获取图标
        self.btn_cancel.setIcon(QIcon(FluentIcon.CANCEL.value))
        self.btn_cancel.setProperty('type', 'danger')
        self.btn_cancel.setVisible(False)

        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_cancel)
        self.main_layout.addLayout(button_layout)

        # 绑定按钮点击事件
        self.btn_browse_video.clicked.connect(self.browse_video)
        self.btn_browse_sub.clicked.connect(self.browse_subtitle)
        self.btn_browse_output.clicked.connect(self.browse_output)
        self.btn_start.clicked.connect(self.start_transcoding)
        self.btn_cancel.clicked.connect(self.cancel_transcoding)

        # 绑定预设选择变化事件
        self.preset_combo.currentIndexChanged.connect(self.update_preset_desc)

        # 加载预设并设置默认选项
        self.load_presets()

        # 绑定视频输入框文本变化事件，用于自动检测字幕
        self.video_input.textChanged.connect(self.auto_detect_subtitle)
        
        # 添加到堆叠窗口
        self.stacked_widget.addWidget(self.home_widget)

    def create_log_page(self):
        """创建日志页面"""
        self.log_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.log_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # 页面标题
        title = self._Label("日志")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # 日志显示区域
        self.log_output = self._TextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        self.log_output.setHtml("")
        layout.addWidget(self.log_output)
        
        # 进度条
        self.progress_bar = self._ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.btn_export_log = self._PushButton("导出日志")
        self.btn_export_log.clicked.connect(self.export_log)
        button_layout.addWidget(self.btn_export_log)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 添加到堆叠窗口
        self.stacked_widget.addWidget(self.log_widget)

    def create_about_page(self):
        """创建关于页面"""
        self.about_widget = self._SimpleCardWidget()
        layout = QVBoxLayout(self.about_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # 页面标题
        title = self._Label("关于")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # 关于内容
        about_content = self._TextEdit()
        about_content.setReadOnly(True)
        about_content.setHtml(ABOUT_CONTENT)
        layout.addWidget(about_content)
        
        # 添加到堆叠窗口
        self.stacked_widget.addWidget(self.about_widget)

    def switch_to_page(self, index):
        """切换到指定页面"""
        self.stacked_widget.setCurrentIndex(index)

    def load_presets(self):
        from main import TranscodeEngine
        engine = TranscodeEngine()
        presets = engine.get_presets()
        for name, (desc, _) in presets.items():
            self.preset_combo.addItem(name)
        if presets:
            self.preset_combo.setCurrentIndex(0)

    def update_preset_desc(self):
        from main import TranscodeEngine
        engine = TranscodeEngine()
        presets = engine.get_presets()
        current_name = self.preset_combo.currentText()
        if current_name in presets:
            desc, template = presets[current_name]
            self.preset_desc.setText(f"预设说明：{desc}")

            # 检查是否包含 {format:xxx} 语法
            if re.search(r'\{format:([^}]+)\}', template):
                # 如果包含，则禁用格式选择框
                self.format_combo.setEnabled(False)
                self.format_combo.setStyleSheet("QComboBox { background-color: #f0f0f0; }")
            else:
                # 否则启用格式选择框
                self.format_combo.setEnabled(True)
                self.format_combo.setStyleSheet("")

    def auto_detect_subtitle(self, video_path):
        """自动检测同名字幕文件"""
        if not video_path or not os.path.isfile(video_path):
            return

        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        # 检查常见字幕格式
        for ext in ['.srt', '.ass', '.ssa']:
            sub_path = os.path.join(video_dir, video_name + ext)
            if os.path.exists(sub_path):
                self.sub_input.setText(sub_path)
                break

    def browse_video(self):
        # 实现视频文件选择逻辑
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.mov *.mkv)"
        )
        if file_path:
            self.video_input.setText(file_path)
            # 注意：现在不需要在这里调用auto_detect_subtitle，因为textChanged会自动触发

    def browse_subtitle(self):
        # 实现字幕文件选择逻辑
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "字幕文件 (*.srt *.ass *.ssa)"
        )
        if file_path:
            self.sub_input.setText(file_path)

    def browse_output(self):
        # 实现输出目录选择逻辑
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", ""
        )
        if dir_path:
            self.output_input.setText(dir_path)
            # 自动填充文件名
            if self.video_input.text():
                input_filename = os.path.splitext(os.path.basename(self.video_input.text()))[0]
                self.filename_input.setText(input_filename)

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "文本文件 (*.txt)"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_output.toPlainText())

    def start_transcoding(self):
        # 实现压制任务启动逻辑
        from main import TranscodeEngine
        engine = TranscodeEngine()

        video = self.video_input.text()
        sub = self.sub_input.text()
        output_dir = self.output_input.text()
        filename = self.filename_input.text() or None
        format = self.format_combo.currentText()

        # 修改：只检查视频路径，不再强制要求字幕路径
        if not video:
            self._MessageBox.warning(self, "警告", "请确保已选择视频文件")
            return

        # 如果输出目录为空，则使用视频所在目录
        if not output_dir:
            output_dir = os.path.dirname(video)
            self.output_input.setText(output_dir)

        # 自动填充文件名（如果未指定）
        if not filename:
            input_filename = os.path.splitext(os.path.basename(video))[0]
            filename = input_filename
            self.filename_input.setText(filename)

        # 构造完整的输出路径
        output_path = os.path.join(output_dir, f"{filename}.{format}")
        
        # 调试日志：打印输出路径
        print(f"输出路径: {output_path}")

        # 检查输出文件是否已存在
        if os.path.exists(output_path):
            from PySide6.QtWidgets import QMessageBox, QLineEdit
            # 强制用户更改文件名
            new_filename, ok = QInputDialog.getText(
                self,
                "文件已存在",
                f"输出文件已存在：\n{output_path}\n\n请输入新的文件名（不含扩展名）:",
                QLineEdit.Normal,
                filename
            )
            if not ok or not new_filename:
                return
            # 更新文件名并重新构造输出路径
            filename = new_filename
            output_path = os.path.join(output_dir, f"{filename}.{format}")
            self.filename_input.setText(filename)

        # 获取当前选中的预设
        current_preset = self.preset_combo.currentText()
        presets = engine.get_presets()
        if current_preset in presets:
            template = presets[current_preset][1]
            try:
                # 重置进度条
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(True)
                
                # 显示取消按钮，隐藏开始按钮
                self.btn_start.setVisible(False)
                self.btn_cancel.setVisible(True)

                # 修改：根据是否有字幕选择不同的处理方式
                if sub:
                    # 有字幕的情况，使用原有的处理逻辑
                    engine.run_task(template, video, sub, output_dir, filename, format)
                else:
                    # 没有字幕的情况，从命令模板中移除字幕相关的参数
                    # 删除 -vf "subtitles='{input_s}'" 这一部分
                    modified_template = re.sub(r'-vf\s+"subtitles=\'\{input_s\}\'"', '', template)
                    # 清理多余的空格
                    modified_template = re.sub(r'\s+', ' ', modified_template).strip()
                    engine.run_task(modified_template, video, "", output_dir, filename, format)

                # 启动定时器监控进程状态
                self.monitor_timer = QTimer()
                self.monitor_timer.timeout.connect(lambda: self.check_process_status(engine))
                self.monitor_timer.start(1000)  # 每秒检查一次

            except ValueError as e:
                self._MessageBox.critical(self, "错误", f"错误: {str(e)}")
                self.progress_bar.setVisible(False)
                # 隐藏取消按钮，显示开始按钮
                self.btn_cancel.setVisible(False)
                self.btn_start.setVisible(True)

    def cancel_transcoding(self):
        if hasattr(self, 'engine') and hasattr(self.engine, 'process'):
            self.engine.process.kill()
        self.progress_bar.setVisible(False)
        # 隐藏取消按钮，显示开始按钮
        self.btn_cancel.setVisible(False)
        self.btn_start.setVisible(True)

    def check_process_status(self, engine):
        """检查进程状态"""
        if hasattr(engine, 'process') and engine.process.state() == QProcess.NotRunning:
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()
            # 重新启用开始按钮
            self.btn_start.setEnabled(True)
            # 隐藏取消按钮，显示开始按钮
            self.btn_cancel.setVisible(False)
            self.btn_start.setVisible(True)
        else:
            # 更新日志输出已在TranscodeEngine的回调中处理，这里不需要重复处理
            pass