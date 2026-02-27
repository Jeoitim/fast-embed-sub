# gui.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
                               QFileDialog, QGroupBox, QRadioButton, QButtonGroup,
                               QMessageBox, QProgressDialog, QApplication, QProgressBar)
from PySide6.QtCore import Qt, QTimer, QProcess, QMimeData
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent  # 添加这行导入
import os
import re
import sys

class DragDropLineEdit(QLineEdit):
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

class MainUI(QWidget):
    def __init__(self):
        super().__init__()  # 添加这行来正确调用父类构造函数
        self.setWindowTitle("极简字幕压制工具")
        self.resize(600, 500)
        # 设置应用图标
        icon_path = os.path.join("assets", "icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 图标文件 {icon_path} 不存在")

        # 主布局
        main_layout = QVBoxLayout(self)

        # 网格布局：用于文件选择
        grid = QGridLayout()
        
        # 1. 视频源
        grid.addWidget(QLabel("视频源:"), 0, 0)
        self.video_input = DragDropLineEdit()  # 修改为自定义类
        self.video_input.setPlaceholderText("请选择或拖入视频文件...")
        self.btn_browse_video = QPushButton("浏览")
        grid.addWidget(self.video_input, 0, 1)
        grid.addWidget(self.btn_browse_video, 0, 2)

        # 2. 字幕源
        grid.addWidget(QLabel("字幕源:"), 1, 0)
        self.sub_input = DragDropLineEdit()  # 修改为自定义类
        self.sub_input.setPlaceholderText("自动检测同名文件，也可手动选择...")
        self.btn_browse_sub = QPushButton("浏览")
        grid.addWidget(self.sub_input, 1, 1)
        grid.addWidget(self.btn_browse_sub, 1, 2)

        main_layout.addLayout(grid)

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("输出目录:"))
        self.output_input = DragDropLineEdit()  # 修改为自定义类（可选，但通常目录也可以拖入）
        self.output_input.setPlaceholderText("默认输出到视频同目录...")
        self.btn_browse_output = QPushButton("浏览")
        output_dir_layout.addWidget(self.output_input)
        output_dir_layout.addWidget(self.btn_browse_output)
        output_layout.addLayout(output_dir_layout)

        # 文件名和格式设置
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("文件名:"))
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("自动使用输入文件名")
        filename_layout.addWidget(self.filename_input)
        
        filename_layout.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['mkv', 'mp4', 'mov'])
        filename_layout.addWidget(self.format_combo)
        output_layout.addLayout(filename_layout)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # 预设选择区
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("压制预设:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        main_layout.addLayout(preset_layout)

        # 预设备注显示
        self.preset_desc = QLabel("预设说明：请选择预设")
        self.preset_desc.setStyleSheet("color: gray;")
        main_layout.addWidget(self.preset_desc)

        # 压制日志 / 命令行输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        self.log_output.setHtml("")  # 初始化为空HTML
        main_layout.addWidget(self.log_output)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)  # 初始隐藏
        main_layout.addWidget(self.progress_bar)

        # 开始按钮
        self.btn_start = QPushButton("开始压制")
        self.btn_start.setMinimumHeight(40)
        main_layout.addWidget(self.btn_start)

        # 绑定按钮点击事件
        self.btn_browse_video.clicked.connect(self.browse_video)
        self.btn_browse_sub.clicked.connect(self.browse_subtitle)
        self.btn_browse_output.clicked.connect(self.browse_output)
        self.btn_start.clicked.connect(self.start_transcoding)

        # 绑定预设选择变化事件
        self.preset_combo.currentIndexChanged.connect(self.update_preset_desc)

        # 加载预设并设置默认选项
        self.load_presets()

        # 绑定视频输入框文本变化事件，用于自动检测字幕
        self.video_input.textChanged.connect(self.auto_detect_subtitle)

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

    def start_transcoding(self):
        # 实现压制任务启动逻辑
        from main import TranscodeEngine
        engine = TranscodeEngine()
        
        video = self.video_input.text()
        sub = self.sub_input.text()
        output_dir = self.output_input.text()
        filename = self.filename_input.text() or None
        format = self.format_combo.currentText()
        
        if not video or not sub:
            QMessageBox.warning(self, "警告", "请确保已选择视频和字幕")
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
        
        # 检查输出文件是否已存在
        output_path = os.path.join(output_dir, f"{filename}.{format}")
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self, 
                "文件已存在", 
                f"输出文件已存在：\n{output_path}\n\n是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 获取当前选中的预设
        current_preset = self.preset_combo.currentText()
        presets = engine.get_presets()
        if current_preset in presets:
            template = presets[current_preset][1]
            try:
                # 重置进度条
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(True)
                
                engine.run_task(template, video, sub, output_dir, filename, format)
                
                # 启动定时器监控进程状态
                self.monitor_timer = QTimer()
                self.monitor_timer.timeout.connect(lambda: self.check_process_status(engine))
                self.monitor_timer.start(1000)  # 每秒检查一次
                
            except ValueError as e:
                QMessageBox.critical(self, "错误", f"错误: {str(e)}")
                self.progress_bar.setVisible(False)
        else:
            QMessageBox.critical(self, "错误", "无效的预设")
            self.progress_bar.setVisible(False)

    def check_process_status(self, engine):
        """检查进程状态"""
        if hasattr(engine, 'process') and engine.process.state() == QProcess.NotRunning:
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()
            # 重新启用开始按钮
            self.btn_start.setEnabled(True)
        else:
            # 更新日志输出已在TranscodeEngine的回调中处理，这里不需要重复处理
            pass

# 添加主程序入口点
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec())
