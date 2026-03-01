import os
import re
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QProcess, QObject, Signal

class TranscodeTask:
    """定义单个压制任务的状态模型"""
    def __init__(self, task_id, video, sub, output_path, preset_name, final_cmd):
        self.task_id = task_id
        self.video = video
        self.sub = sub
        self.output_path = output_path
        self.preset_name = preset_name
        self.final_cmd = final_cmd
        
        self.status = "等待中"  # 状态：等待中, 压制中, 已完成, 已取消, 失败
        self.progress = 0
        self.total_duration = None
        self.duration_parsed = False

class TranscodeEngine(QObject):
    # 定义信号，用于通知 GUI 更新队列 UI
    task_status_changed = Signal(str)  # 任务状态或进度变化时触发
    
    def __init__(self, ffmpeg_path="components/ffmpeg.exe"):
        super().__init__()
        if getattr(sys, 'frozen', False):
            self.bundle_dir = os.path.dirname(sys.executable)
        else:
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.ffmpeg_path = os.path.abspath(os.path.join(self.bundle_dir, ffmpeg_path))
        
        # 任务队列管理
        self.queue = []  # 存储 TranscodeTask 对象
        self.current_task = None
        
        self.process = QProcess()
        self.process.started.connect(self.on_process_started)
        self.process.finished.connect(self.on_process_finished)
        self.process.readyReadStandardOutput.connect(self.on_ready_read_stdout)
        self.process.readyReadStandardError.connect(self.on_ready_read_stderr)
        
    def get_presets(self):
        """获取预设列表逻辑保持不变"""
        presets = {}
        presets_dir = os.path.join(self.bundle_dir, "presets")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir, exist_ok=True)
            # ... 创建默认预设逻辑 ...
        
        for filename in os.listdir(presets_dir):
            if filename.endswith('.txt'):
                preset_path = os.path.join(presets_dir, filename)
                try:
                    with open(preset_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) >= 2:
                            desc = lines[0].strip().lstrip('#').strip()
                            template = ''.join(lines[1:]).strip()
                            presets[os.path.splitext(filename)[0]] = (desc, template)
                except Exception as e:
                    print(f"读取预设错误: {e}")
        return presets

    def add_to_queue(self, template, video, sub, output_dir, filename, format, preset_name):
        """构造任务并加入队列"""
        # 1. 处理字幕路径转义
        if not sub:
            sub = os.path.join(self.bundle_dir, "assets", "empty.srt")
        
        abs_sub_path = os.path.abspath(sub)
        drive, rest = os.path.splitdrive(abs_sub_path)
        path_fixed = f"{drive[0].upper()}\\:{rest.replace('\\', '/')}" if drive else abs_sub_path.replace("\\", "/")
        escaped_sub = f"filename='{path_fixed}'"

        # 2. 确定输出路径
        output_path = os.path.join(output_dir, f"{filename}.{format}")
        
        # 3. 模板格式化
        format_match = re.search(r'\{format:([^}]+)\}', template)
        if format_match:
            format = format_match.group(1)
        
        template_cleaned = re.sub(r'\{format:([^}]+)\}', r'\1', template)
        
        try:
            final_cmd = template_cleaned.format(
                input_v=video,
                input_s=escaped_sub,
                output_dir=output_dir,
                filename=filename,
                format=format
            )
        except KeyError as e:
            raise ValueError(f"不支持的占位符: {e}")
            
        final_cmd = final_cmd.replace('components/ffmpeg.exe', f'"{self.ffmpeg_path}"')

        # 4. 创建任务对象并入队
        task_id = f"task_{len(self.queue)}_{os.path.basename(video)}"
        new_task = TranscodeTask(task_id, video, sub, output_path, preset_name, final_cmd)
        self.queue.append(new_task)
        
        # 向日志发送“已入队”消息
        self._log_to_window(f"<b>[队列]</b> 任务已添加: {os.path.basename(video)} ({preset_name})", "blue")
        
        # 如果当前没有正在运行的任务，启动它
        if self.current_task is None:
            self._start_next_task()
            
        return new_task

    def _start_next_task(self):
        """寻找下一个等待中的任务并启动"""
        for task in self.queue:
            if task.status == "等待中":
                self.current_task = task
                self.current_task.status = "压制中"
                self.task_status_changed.emit(task.task_id)
                
                self._log_to_window(f"<b>[{os.path.basename(task.video)}]</b> 开始压制...", "green")
                
                # ---> 新增这一行：用蓝色输出即将执行的完整 FFmpeg 命令 <---
                self._log_to_window(f"<b>[{os.path.basename(task.video)}]</b> 执行命令: {task.final_cmd}", "blue")
                
                self.process.startCommand(task.final_cmd)
                return
        
        self.current_task = None
        self._log_to_window("<b>[队列]</b> 所有任务处理完毕", "cyan")

    def cancel_task(self, task_id):
        """取消指定任务"""
        for task in self.queue:
            if task.task_id == task_id:
                if task.status == "压制中":
                    self.process.kill() # 触发 on_process_finished
                    task.status = "已取消"
                elif task.status == "等待中":
                    task.status = "已取消"
                self.task_status_changed.emit(task_id)
                break

    def _log_to_window(self, message, color=None):
        """统一辅助函数：发送日志到 GUI 窗口"""
        window = QApplication.instance().activeWindow()
        if window and hasattr(window, 'log_output'):
            styled_msg = f'<span style="color: {color};">{message}</span>' if color else message
            window.log_output.append(styled_msg)

    def on_process_started(self):
        self.task_status_changed.emit(self.current_task.task_id)

    def on_process_finished(self, exit_code, exit_status):
        if self.current_task:
            if self.current_task.status == "已取消":
                self._log_to_window(f"<b>[{os.path.basename(self.current_task.video)}]</b> 任务已手动取消", "gray")
            elif exit_code == 0:
                self.current_task.status = "已完成"
                self.current_task.progress = 100
                self._log_to_window(f"<b>[{os.path.basename(self.current_task.video)}]</b> 压制成功", "green")
            else:
                self.current_task.status = "失败"
                self._log_to_window(f"<b>[{os.path.basename(self.current_task.video)}]</b> 压制失败 (退出码: {exit_code})", "red")
            
            self.task_status_changed.emit(self.current_task.task_id)
        
        # 无论成功失败，尝试执行下一个
        self._start_next_task()

    def on_ready_read_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if self.current_task:
            prefix = f"[{os.path.basename(self.current_task.video)}]"
            self._log_to_window(f"{prefix} {data.strip()}")

    def on_ready_read_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if not self.current_task: return
        
        line = data.strip()
        # 解析时长
        if not self.current_task.duration_parsed and 'Duration:' in line:
            match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', line)
            if match:
                h, m, s = match.groups()
                self.current_task.total_duration = int(h) * 3600 + int(m) * 60 + float(s)
                self.current_task.duration_parsed = True

        # 解析进度
        if 'time=' in line and self.current_task.total_duration:
            match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
            if match:
                h, m, s = match.groups()
                curr = int(h) * 3600 + int(m) * 60 + float(s)
                prog = min(100, int((curr / self.current_task.total_duration) * 100))
                if prog != self.current_task.progress:
                    self.current_task.progress = prog
                    self.task_status_changed.emit(self.current_task.task_id)
        
        self._log_to_window(f"[{os.path.basename(self.current_task.video)}] {line}")

def main():
    app = QApplication(sys.argv)
    try:
        from qfluentwidgets import setTheme, Theme, MessageBox
    except ImportError:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "缺少依赖",
                             "未检测到 PySide6-Fluent-Widgets 库。请运行\n"
                             "`pip install PySide6-Fluent-Widgets` 后重试。")
        sys.exit(1)
    setTheme(Theme.DARK)
    from gui import MainUI
    window = MainUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
