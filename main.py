import os
import re
import sys
import uuid # 用于生成乱码后缀防止冲突
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QProcess

class TranscodeEngine:
    def __init__(self, ffmpeg_path="components/ffmpeg.exe"):
        # 修改：添加兼容性逻辑处理打包后的路径问题
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件路径
            self.bundle_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境下的路径
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 构建ffmpeg的完整路径
        self.ffmpeg_path = os.path.join(self.bundle_dir, ffmpeg_path)
        self.ffmpeg_path = os.path.abspath(self.ffmpeg_path)
        
        self.process = QProcess()
        # 连接信号
        self.process.started.connect(self.on_process_started)
        self.process.finished.connect(self.on_process_finished)
        self.process.readyReadStandardOutput.connect(self.on_ready_read_stdout)
        self.process.readyReadStandardError.connect(self.on_ready_read_stderr)
        
        # 用于存储视频总时长（秒）
        self.total_duration = None
        # 用于避免重复解析总时长
        self.duration_parsed = False
        
    def get_presets(self):
        """扫描 preset 文件夹，返回 {文件名: (备注, 命令模板)}"""
        presets = {}
        preset_dir = "presets"
        if not os.path.exists(preset_dir):
            return presets
            
        for f in os.listdir(preset_dir):
            if f.endswith(".txt"):
                with open(os.path.join(preset_dir, f), 'r', encoding='utf-8') as tf:
                    content = tf.read().strip()
                    # 修改正则表达式以支持无空格的备注行
                    comment = re.search(r'^#\s*(.*)', content)
                    comment_text = comment.group(1) if comment else "无备注"
                    # 提取命令（去除备注行）
                    cmd_template = re.sub(r'^#.*$', '', content, flags=re.MULTILINE).strip()
                    presets[f.replace(".txt", "")] = (comment_text, cmd_template)
        return presets

    def run_task(self, template, video, sub, output_dir, filename=None, format=None):
        """将路径填入模板并执行"""
        # 1. 如果用户没填字幕，使用 assets 里的空字幕
        if not sub:
            # 使用 self.bundle_dir 兼容打包环境
            sub = os.path.join(self.bundle_dir, "assets", "empty.srt")
    
        # 2. 统一处理路径（包括用户填的或我们的 empty.srt）
        abs_sub_path = os.path.abspath(sub)
        drive, rest = os.path.splitdrive(abs_sub_path)
    
        if drive:
            # 结果类似于 C\:/Users/.../assets/empty.srt
            path_fixed = f"{drive[0].upper()}\\:{rest.replace('\\', '/')}"
        else:
            path_fixed = abs_sub_path.replace("\\", "/")
    
        # 3. 始终生成带有 filename 的字符串
        escaped_sub = f"filename='{path_fixed}'"
        

        # 获取输入文件的文件名和扩展名
        input_filename = os.path.splitext(os.path.basename(video))[0]
        input_format = os.path.splitext(video)[1][1:]  # 移除点号
        
        # 如果未指定文件名和格式，使用输入文件的信息
        if filename is None:
            filename = input_filename
        if format is None:
            format = input_format if input_format in ['mp4', 'mov'] else 'mkv'
        
        # 检查模板中是否包含 {format:xxx} 语法
        format_match = re.search(r'\{format:([^}]+)\}', template)
        if format_match:
            # 如果模板中指定了格式，则覆盖用户选择
            forced_format = format_match.group(1)
            format = forced_format
        
        # 处理 {format:xxx} 语法
        def replace_format_placeholder(match):
            specified_format = match.group(1)
            return specified_format
        
        template = re.sub(r'\{format:([^}]+)\}', replace_format_placeholder, template)
        
        # 确保所有必需的占位符都被替换（输出路径通过 output_dir/filename/format 三个变量拼接）
        try:
            final_cmd = template.format(
                input_v=video,
                input_s=escaped_sub,
                output_dir=output_dir,
                filename=filename,
                format=format
            )
        except KeyError as e:
            raise ValueError(f"预设模板中包含未支持的占位符: {e}. 支持的占位符包括: input_v, input_s, output_dir, filename, format")
        
        # 修复路径问题：正确替换 components/ffmpeg.exe 为绝对路径
        final_cmd = final_cmd.replace('components/ffmpeg.exe', f'"{self.ffmpeg_path}"')
            
        print(f"执行命令: {final_cmd}")
        self.process.startCommand(final_cmd)

    def on_process_started(self):
        """进程开始时的回调"""
        print("FFmpeg 进程已启动")
        
    def on_process_finished(self, exit_code, exit_status):
        """进程结束时的回调"""
        # 隐藏进度条
        if hasattr(QApplication.instance().activeWindow(), 'progress_bar'):
            window = QApplication.instance().activeWindow()
            window.progress_bar.setVisible(False)
            
        if exit_status == QProcess.NormalExit:
            if exit_code == 0:
                print("压制完成！")
                # 直接向日志区域添加绿色成功消息
                if hasattr(QApplication.instance().activeWindow(), 'log_output'):
                    window = QApplication.instance().activeWindow()
                    window.log_output.append('<span style="color: green;">压制完成！</span>')
            else:
                print(f"压制失败，退出码: {exit_code}")
                # 直接向日志区域添加红色错误消息
                if hasattr(QApplication.instance().activeWindow(), 'log_output'):
                    window = QApplication.instance().activeWindow()
                    window.log_output.append(f'<span style="color: red;">压制失败，退出码: {exit_code}</span>')
        else:
            print("进程异常终止")
            # 直接向日志区域添加红色错误消息
            if hasattr(QApplication.instance().activeWindow(), 'log_output'):
                window = QApplication.instance().activeWindow()
                window.log_output.append('<span style="color: red;">压制进程异常终止</span>')

    def on_ready_read_stdout(self):
        """读取标准输出"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        print(f"STDOUT: {data.strip()}")
        # 将标准输出添加到日志区域
        if hasattr(QApplication.instance().activeWindow(), 'log_output'):
            window = QApplication.instance().activeWindow()
            window.log_output.append(data.strip())
        
    def on_ready_read_stderr(self):
        """读取标准错误"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        lines = data.split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            # 检查是否包含Duration信息（只解析一次）
            if not self.duration_parsed and 'Duration:' in line:
                self._parse_duration(line)
                self.duration_parsed = True
                
            # 检查是否是进度行（包含time=）
            if 'time=' in line and 'bitrate=' in line:
                self._parse_progress(line)
                # 不将进度行添加到日志（避免刷屏），但可以添加其他信息
                continue
                
            # 检查是否是真正的错误（通常包含"Error"或"error"，但FFmpeg错误通常以大写开头）
            is_error = any(keyword in line for keyword in ['Error', 'error', 'Invalid', 'invalid', 'Failed', 'failed'])
            
            # 将其他信息添加到日志区域
            if hasattr(QApplication.instance().activeWindow(), 'log_output'):
                window = QApplication.instance().activeWindow()
                if is_error:
                    window.log_output.append(f'<span style="color: red;">{line.strip()}</span>')
                else:
                    # 普通信息（如配置信息、流信息等）用默认颜色
                    window.log_output.append(line.strip())
                    
            print(f"STDERR: {line.strip()}")

    def _parse_duration(self, line):
        """解析视频总时长"""
        # 示例: Duration: 00:01:25.77, start: 0.000000, bitrate: 8002 kb/s
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', line)
        if match:
            hours, minutes, seconds = match.groups()
            self.total_duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            print(f"Total duration: {self.total_duration} seconds")

    def _parse_progress(self, line):
        """解析进度信息并更新进度条"""
        # 示例: frame= 121 fps=0.0 q=24.0 size= 1KiB time=00:00:03.96 bitrate= 2.1kbits/s speed=7.61x
        match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
        if match and self.total_duration:
            hours, minutes, seconds = match.groups()
            current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            progress = min(100, int((current_time / self.total_duration) * 100))
            
            # 更新进度条
            if hasattr(QApplication.instance().activeWindow(), 'progress_bar'):
                window = QApplication.instance().activeWindow()
                window.progress_bar.setValue(progress)

# 添加主程序入口点
def main():
    # create the application first – this must occur before any QWidget is
    # instantiated.  doing the fluent widgets import (`qfluentwidgets`) afterwards
    # avoids the frequent error about "Must construct a QApplication before a QWidget".
    app = QApplication(sys.argv)

    # apply fluent theme (PySide6‑Fluent‑Widgets) now that QApplication exists
    # the package imports as `qfluentwidgets`.  If it's not installed we
    # show an error dialog and exit rather than falling back to native Qt.
    try:
        from qfluentwidgets import setTheme, Theme, MessageBox
    except ImportError:
        # if import fails we can't proceed
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "缺少依赖",
                             "未检测到 PySide6-Fluent-Widgets 库。请运行\n"
                             "`pip install PySide6-Fluent-Widgets` 后重试。")
        sys.exit(1)
    setTheme(Theme.DARK)

    # import MainUI now that QApplication exists (the class itself won't
    # create a widget until we instantiate it, but some fluent helpers may
    # create proxies during import so we delay for safety)
    from gui import MainUI

    window = MainUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()