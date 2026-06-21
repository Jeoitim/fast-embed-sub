import os
import re
import sys
import shutil
import uuid
import tempfile
from PySide6.QtCore import QTimer, QProcess, QObject, Signal

from preset_parser import PresetParser

# 预编译正则表达式以提高解析性能
DURATION_REGEX = re.compile(r'Duration: (\d+):(\d+):(\d+\.\d+)')
TIME_REGEX = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')


class TranscodeTask:
    """定义单个压制任务的状态模型"""
    def __init__(self, task_id, video, sub, output_path, preset_name, final_cmd, temp_vpy_path=None):
        self.task_id = task_id
        self.video = video
        self.sub = sub
        self.output_path = output_path
        self.preset_name = preset_name
        self.final_cmd = final_cmd
        self.temp_vpy_path = temp_vpy_path
        
        self.status = "等待中"  # 状态：等待中, 压制中, 已完成, 已取消, 失败
        self.progress = 0
        self.total_duration = None
        self.duration_parsed = False

class TranscodeEngine(QObject):
    # 定义信号，用于通知 GUI
    task_status_changed = Signal(str)  # 任务状态或进度变化时触发
    log_message = Signal(str, str)     # 新增信号：通知 GUI 打印日志 (message, color)
    
    def __init__(self, ffmpeg_path="components/ffmpeg.exe"):
        super().__init__()
        if getattr(sys, 'frozen', False):
            self.bundle_dir = os.path.dirname(sys.executable)
        else:
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.ffmpeg_path = os.path.abspath(os.path.join(self.bundle_dir, ffmpeg_path))
        if not os.path.exists(self.ffmpeg_path):
            # 自动寻路环境变量中的 ffmpeg
            sys_ffmpeg = shutil.which("ffmpeg")
            if sys_ffmpeg:
                self.ffmpeg_path = sys_ffmpeg
            else:
                # 延迟发出通知，等待界面连接好 log_message 信号
                QTimer.singleShot(500, lambda: self._log_to_window(
                    "<b>[警告]</b> 未在 components/ 目录下检测到 ffmpeg.exe，且环境变量中没有找到 ffmpeg。压制任务将无法正常运行！", "red"
                ))
        
        # 任务队列管理
        self.queue = []  # 存储 TranscodeTask 对象
        self.current_task = None
        
        self.process = QProcess()
        self.process.started.connect(self.on_process_started)
        self.process.finished.connect(self.on_process_finished)
        self.process.readyReadStandardOutput.connect(self.on_ready_read_stdout)
        self.process.readyReadStandardError.connect(self.on_ready_read_stderr)
        
        # 自动配置便携式 VapourSynth 运行环境的 TOML 映射
        self.configure_vapoursynth_toml()
        
        # 预先生成基础 Vpy 模板到 assets/base.vpy
        self.get_base_vpy_template()
        
    def configure_vapoursynth_toml(self):
        """自动为便携版 VapourSynth 注册 Python 运行库路径到系统的 vapoursynth.toml"""
        try:
            appdata = os.environ.get("APPDATA")
            if not appdata:
                return
            
            toml_dir = os.path.join(appdata, "vapoursynth")
            toml_path = os.path.join(toml_dir, "vapoursynth.toml")
            
            os.makedirs(toml_dir, exist_ok=True)
            
            # 1. 如果 toml 文件不存在，运行一次 vapoursynth config 以生成默认配置
            if not os.path.exists(toml_path):
                probe_process = QProcess()
                venv_python = sys.executable
                probe_process.start(venv_python, ["-m", "vapoursynth", "config"])
                probe_process.waitForFinished(3000)
                
            if not os.path.exists(toml_path):
                return
                
            # 2. 读取 toml 并解析/写入映射
            with open(toml_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            portable_vsscript = os.path.abspath(os.path.join(self.bundle_dir, "components", "vapoursynth", "vsscript.dll"))
            portable_key = portable_vsscript.lower().replace("\\", "\\\\")
            
            # 如果已经有了这个 key，就不重复写入了
            if f'"{portable_key}"' in content or f"'{portable_key}'" in content:
                return
                
            # 查找已有的 Python 路径数组定义 (比如 site-packages 中的)
            match = re.search(r'=\s*(\[.*?\])', content)
            if match:
                python_paths_array = match.group(1)
                # 添加便携版映射
                with open(toml_path, 'a', encoding='utf-8') as f:
                    f.write(f'\n"{portable_key}" = {python_paths_array}\n')
                self._log_to_window(f"[系统] 已自动为便携版 VapourSynth 注册 Python 运行库映射。")
        except Exception as e:
            print(f"自动配置 VapourSynth toml 失败: {e}")

    def get_presets(self):
        """获取预设列表"""
        presets = {}
        presets_dir = os.path.join(self.bundle_dir, "presets")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir, exist_ok=True)
            
        # 若预设文件夹为空，自动创建一个可用的默认预设文件
        if not os.listdir(presets_dir) or len([f for f in os.listdir(presets_dir) if f.endswith('.txt')]) == 0:
            default_preset_path = os.path.join(presets_dir, "默认.txt")
            default_content = (
                "# 默认压制 - H.264 + AAC\n"
                "components/ffmpeg.exe -y -i \"{input_v}\" -vf \"subtitles='{input_s}'\" "
                "-c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k \"{output_dir}/{filename}.{format}\"\n"
            )
            try:
                with open(default_preset_path, 'w', encoding='utf-8') as f:
                    f.write(default_content)
            except Exception as e:
                print(f"写入默认预设文件失败: {e}")
        
        for filename in os.listdir(presets_dir):
            if filename.endswith('.txt'):
                preset_path = os.path.join(presets_dir, filename)
                try:
                    preset_data = PresetParser.parse_preset(preset_path)
                    presets[os.path.splitext(filename)[0]] = preset_data
                except Exception as e:
                    print(f"读取预设错误: {e}")
        return presets

    def get_video_duration(self, video_path):
        """使用 ffmpeg 探测视频时长"""
        try:
            probe_process = QProcess()
            probe_process.start(self.ffmpeg_path, ["-i", video_path])
            probe_process.waitForFinished(3000)
            output = probe_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            match = DURATION_REGEX.search(output)
            if match:
                h, m, s = match.groups()
                return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception as e:
            print(f"获取视频时长失败: {e}")
        return None

    def compile_and_register_vpy(self, vpy_template, param_values, video_path, subtitle_path, preset_name):
        """编译并生成临时的 .vpy 文件，返回其绝对路径"""
        abs_sub_path = os.path.abspath(subtitle_path)
        drive, rest = os.path.splitdrive(abs_sub_path)
        path_fixed = f"{drive[0].upper()}\\:{rest.replace('\\', '/')}" if drive else abs_sub_path.replace("\\", "/")
        escaped_sub = path_fixed
        
        # 准备目录占位符的真实路径
        preset_dir = os.path.abspath(os.path.join(self.bundle_dir, "presets"))
        components_dir = os.path.abspath(os.path.join(self.bundle_dir, "components"))
        preset_components_dir = os.path.abspath(os.path.join(preset_dir, "components", preset_name))
        
        # 将系统内置路径与自定义参数一同交给 compile_vpy_script 统一替换和转义
        all_values = {
            "input_v": video_path,
            "input_s": escaped_sub,
            "preset_dir": preset_dir,
            "components_dir": components_dir,
            "preset_components_dir": preset_components_dir
        }
        all_values.update(param_values)
        
        vpy_compiled = PresetParser.compile_vpy_script(vpy_template, all_values)
        
        # 写入系统临时文件夹
        temp_dir = tempfile.gettempdir()
        vpy_filename = f"vs_temp_{uuid.uuid4().hex[:8]}.vpy"
        vpy_path = os.path.join(temp_dir, vpy_filename)
        
        with open(vpy_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(vpy_compiled)
            
        return os.path.abspath(vpy_path)

    def get_base_vpy_template(self):
        """获取或创建 assets/base.vpy 中的基础 Vpy 模板"""
        assets_dir = os.path.join(self.bundle_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir, exist_ok=True)
            
        base_vpy_path = os.path.join(assets_dir, "base.vpy")
        
        default_template = (
            "# 基础 VapourSynth 脚本模板 - 用于传统 FFmpeg 预设支持 VS 几何与尺寸变换\n"
            "import sys\n"
            "import vapoursynth as vs\n"
            "core = vs.core\n\n"
            "# 1. 载入视频 (优先尝试 ffms2 或 lsmash)\n"
            "try:\n"
            "    clip = core.ffms2.Source(source=\"{input_v}\")\n"
            "except AttributeError:\n"
            "    try:\n"
            "        clip = core.lsmas.LWLibavSource(source=\"{input_v}\")\n"
            "    except AttributeError:\n"
            "        # 万能回退\n"
            "        clip = core.ffms2.Source(source=\"{input_v}\")\n\n"
            "# 2. 水平翻转\n"
            "if {flip_horizontal}:\n"
            "    clip = core.std.FlipHorizontal(clip)\n\n"
            "# 3. 垂直翻转\n"
            "if {flip_vertical}:\n"
            "    clip = core.std.FlipVertical(clip)\n\n"
            "# 4. 尺寸缩放\n"
            "scale = float({resize_scale})\n"
            "if scale != 1.0:\n"
            "    new_w = int(clip.width * scale)\n"
            "    new_h = int(clip.height * scale)\n"
            "    # 确保是偶数\n"
            "    new_w = (new_w // 2) * 2\n"
            "    new_h = (new_h // 2) * 2\n"
            "    clip = core.resize.Bicubic(clip, width=new_w, height=new_h)\n\n"
            "# 5. 字幕渲染 (如果选择了字幕)\n"
            "sub_path = \"{input_s}\"\n"
            "if sub_path and not sub_path.endswith(\"empty.srt\"):\n"
            "    try:\n"
            "        clip = core.sub.TextFile(clip, file=sub_path)\n"
            "    except AttributeError:\n"
            "        try:\n"
            "            core.std.LoadPlugin(path=r\"{components_dir}/vapoursynth/plugins/subtext.dll\")\n"
            "            clip = core.sub.TextFile(clip, file=sub_path)\n"
            "        except Exception:\n"
            "            pass\n\n"
            "# 6. 输出\n"
            "clip.set_output()\n"
        )
        
        if not os.path.exists(base_vpy_path):
            try:
                with open(base_vpy_path, 'w', encoding='utf-8') as f:
                    f.write(default_template)
            except Exception as e:
                print(f"创建 assets/base.vpy 失败: {e}")
                return default_template
                
        try:
            with open(base_vpy_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取 assets/base.vpy 失败: {e}")
            return default_template

    def convert_to_vpy_cmd(self, ffmpeg_cmd):
        """将传统 FFmpeg 压制命令行模板转换为基于 vspipe 的管道格式"""
        cmd = ffmpeg_cmd
        # 1. 替换或插入 vspipe 管道前缀
        if "components/ffmpeg.exe" in cmd:
            cmd = cmd.replace("components/ffmpeg.exe", 'components/vspipe.exe -c y4m "{vpy_path}" - | components/ffmpeg.exe')
        elif "ffmpeg.exe" in cmd:
            cmd = cmd.replace("ffmpeg.exe", 'components/vspipe.exe -c y4m "{vpy_path}" - | ffmpeg.exe')
        elif "ffmpeg" in cmd:
            cmd = cmd.replace("ffmpeg", 'components/vspipe.exe -c y4m "{vpy_path}" - | ffmpeg', 1)
        else:
            cmd = 'components/vspipe.exe -c y4m "{vpy_path}" - | ' + cmd
            
        # 2. 替换 -i "{input_v}" 为管道输入 -i - 并映射多声道与视频流
        # 注意需要保留对原始视频 {input_v} 的映射以提取音轨 (比如 -i - -i "{input_v}" -map 0:v -map 1:a?)
        for pat in ['-i "{input_v}"', "-i '{input_v}'", "-i {input_v}"]:
            if pat in cmd:
                cmd = cmd.replace(pat, '-i - -i "{input_v}" -map 0:v -map 1:a?')
                break
                
        # 3. 移除命令行中的字幕渲染滤镜，防止二次烧录
        cmd = re.sub(r'-vf\s+"subtitles=\'\{input_s\}\'"', '', cmd)
        cmd = re.sub(r'-vf\s+subtitles=\'\{input_s\}\'', '', cmd)
        cmd = re.sub(r'-vf\s+"subtitles=\{input_s\}"', '', cmd)
        cmd = re.sub(r'-vf\s+subtitles=\{input_s\}', '', cmd)
        
        # 清理残留的空 -vf 标志或连续空格
        cmd = re.sub(r'-vf\s+""', '', cmd)
        cmd = re.sub(r'-vf\s+\'\'', '', cmd)
        cmd = re.sub(r'\s+', ' ', cmd).strip()
        return cmd

    def add_to_queue(self, video, sub, output_dir, filename, format_val, preset_name, param_values=None):
        """构造任务并加入队列"""
        if not sub:
            sub = os.path.join(self.bundle_dir, "assets", "empty.srt")
            
        presets = self.get_presets()
        preset_data = presets.get(preset_name)
        if not preset_data:
            raise ValueError(f"未找到预设: {preset_name}")
            
        # 准备目录占位符的真实路径
        preset_dir = os.path.abspath(os.path.join(self.bundle_dir, "presets"))
        components_dir = os.path.abspath(os.path.join(self.bundle_dir, "components"))
        preset_components_dir = os.path.abspath(os.path.join(preset_dir, "components", preset_name))
            
        temp_vpy_path = None
        
        # 检测是否开启了 VScript 相关几何变换/缩放参数
        has_vpy_adjustments = False
        if param_values:
            flip_h = param_values.get("flip_horizontal", False)
            flip_v = param_values.get("flip_vertical", False)
            try:
                scale = float(param_values.get("resize_scale", 1.0))
            except (ValueError, TypeError):
                scale = 1.0
            if flip_h or flip_v or scale != 1.0:
                has_vpy_adjustments = True

        is_actually_vpy = preset_data["is_vpy"] or has_vpy_adjustments
        
        if is_actually_vpy:
            if preset_data["is_vpy"]:
                vpy_template = preset_data["vpy_template"]
                cmd_template = preset_data["cmd_template"]
            else:
                vpy_template = self.get_base_vpy_template()
                cmd_template = self.convert_to_vpy_cmd(preset_data["cmd_template"])
                
            compiled_params = param_values if param_values else {}
            # 确保补齐基础参数的默认值
            if "flip_horizontal" not in compiled_params:
                compiled_params["flip_horizontal"] = False
            if "flip_vertical" not in compiled_params:
                compiled_params["flip_vertical"] = False
            if "resize_scale" not in compiled_params:
                compiled_params["resize_scale"] = "1.0"
                
            temp_vpy_path = self.compile_and_register_vpy(vpy_template, compiled_params, video, sub, preset_name)
            
            if not cmd_template:
                cmd_template = 'components/vspipe.exe --y4m "{vpy_path}" - | components/ffmpeg.exe -y -i - -i "{input_v}" -map 0:v -map 1:a? -c:v libx264 -preset medium -crf 23 "{output_dir}/{filename}.{format}"'
                
            final_cmd = cmd_template.replace("{vpy_path}", temp_vpy_path.replace("\\", "/"))
        else:
            final_cmd = preset_data["cmd_template"]
            
        format_match = re.search(r'\{format:([^}]+)\}', final_cmd)
        if format_match:
            format_val = format_match.group(1)
            
        output_path = os.path.join(output_dir, f"{filename}.{format_val}")
        
        final_cmd = re.sub(r'\{format:([^}]+)\}', r'\1', final_cmd)
        
        if not is_actually_vpy and not sub:
            final_cmd = re.sub(r'-vf\s+"subtitles=\'\{input_s\}\'"', '', final_cmd)
            final_cmd = re.sub(r'-vf\s+subtitles=\'\{input_s\}\'', '', final_cmd)
            final_cmd = re.sub(r'-vf\s+"subtitles=\{input_s\}"', '', final_cmd)
            final_cmd = re.sub(r'-vf\s+subtitles=\{input_s\}', '', final_cmd)
            final_cmd = re.sub(r'-vf\s+""', '', final_cmd)
            final_cmd = re.sub(r'-vf\s+\'\'', '', final_cmd)
            final_cmd = re.sub(r'\s+', ' ', final_cmd).strip()
            
        abs_sub_path = os.path.abspath(sub)
        drive, rest = os.path.splitdrive(abs_sub_path)
        path_fixed = f"{drive[0].upper()}\\:{rest.replace('\\', '/')}" if drive else abs_sub_path.replace("\\", "/")
        escaped_sub_legacy = f"filename='{path_fixed}'"
        
        try:
            final_cmd = final_cmd.format(
                input_v=video,
                input_s=escaped_sub_legacy,
                output_dir=output_dir,
                filename=filename,
                format=format_val,
                preset_dir=preset_dir.replace("\\", "/"),
                components_dir=components_dir.replace("\\", "/"),
                preset_components_dir=preset_components_dir.replace("\\", "/")
            )
        except KeyError as e:
            raise ValueError(f"不支持的占位符: {e}")
            
        final_cmd = final_cmd.replace('components/ffmpeg.exe', f'"{self.ffmpeg_path}"')
        
        vspipe_path = None
        vspipe_checks = [
            os.path.join(self.bundle_dir, "components", "vapoursynth", "vspipe.exe"),
            os.path.join(self.bundle_dir, "components", "vspipe.exe")
        ]
        for p in vspipe_checks:
            if os.path.exists(p):
                vspipe_path = os.path.abspath(p)
                break
                
        if not vspipe_path:
            vspipe_sys = shutil.which("vspipe")
            if vspipe_sys:
                vspipe_path = vspipe_sys
            else:
                vspipe_path = "vspipe"
                
        final_cmd = final_cmd.replace('components/vspipe.exe', f'"{vspipe_path}"')
        # VapourSynth R77 移除了 --y4m 参数，统一使用 -c y4m 替代以确保向后兼容性
        final_cmd = final_cmd.replace('--y4m', '-c y4m')
        
        task_id = f"task_{uuid.uuid4().hex[:8]}_{os.path.basename(video)}"
        new_task = TranscodeTask(task_id, video, sub, output_path, preset_name, final_cmd, temp_vpy_path)
        
        total_dur = self.get_video_duration(video)
        if total_dur:
            new_task.total_duration = total_dur
            new_task.duration_parsed = True
            
        self.queue.append(new_task)
        
        self._log_to_window(f"<b>[队列]</b> 任务已添加: {os.path.basename(video)} ({preset_name})", "blue")
        
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
                self._log_to_window(f"<b>[{os.path.basename(task.video)}]</b> 执行命令: {task.final_cmd}", "blue")
                
                # 为子进程加载便携式 VapourSynth 运行环境
                from PySide6.QtCore import QProcessEnvironment
                env = QProcessEnvironment.systemEnvironment()
                vs_portable_dir = os.path.abspath(os.path.join(self.bundle_dir, "components", "vapoursynth"))
                if os.path.exists(vs_portable_dir):
                    path_val = env.value("PATH")
                    env.insert("PATH", vs_portable_dir + os.pathsep + path_val)
                    
                    pythonpath_val = env.value("PYTHONPATH")
                    if pythonpath_val:
                        env.insert("PYTHONPATH", vs_portable_dir + os.pathsep + pythonpath_val)
                    else:
                        env.insert("PYTHONPATH", vs_portable_dir)
                    
                    self.process.setProcessEnvironment(env)
                    self._log_to_window(f"[系统] 已载入便携版 VapourSynth 运行环境: {vs_portable_dir}")
                
                # Windows 平台下如果包含管道符，需要通过 cmd.exe /c 运行
                # 使用 setNativeArguments 绕过 Qt 默认参数转义，防止引号被转义导致找不到可执行文件
                if "|" in task.final_cmd:
                    if sys.platform == "win32":
                        self.process.setProgram("cmd.exe")
                        self.process.setNativeArguments(f'/c "{task.final_cmd}"')
                        self.process.start()
                    else:
                        self.process.start("/bin/sh", ["-c", task.final_cmd])
                else:
                    self.process.startCommand(task.final_cmd)
                return
        
        self.current_task = None
        self._log_to_window("<b>[队列]</b> 所有任务处理完毕", "cyan")

    def _cleanup_temp_vpy(self, task):
        """清理临时生成的 Vpy 文件"""
        if task and hasattr(task, 'temp_vpy_path') and task.temp_vpy_path:
            if os.path.exists(task.temp_vpy_path):
                try:
                    os.remove(task.temp_vpy_path)
                    self._log_to_window(f"[系统] 已清理临时 Vpy 文件: {os.path.basename(task.temp_vpy_path)}")
                except Exception as e:
                    print(f"清理临时文件失败: {e}")

    def cancel_task(self, task_id):
        """取消指定任务"""
        for task in self.queue:
            if task.task_id == task_id:
                if task.status == "压制中":
                    self.process.kill()  # 触发 on_process_finished
                    task.status = "已取消"
                    self._cleanup_temp_vpy(task)
                    QTimer.singleShot(100, lambda: self._delete_unfinished_file(task))
                elif task.status == "等待中":
                    task.status = "已取消"
                    self._cleanup_temp_vpy(task)
                self.task_status_changed.emit(task_id)
                break

    def clear_queue(self):
        """清空所有任务。如果有正在运行的任务，取消并终止进程。"""
        if self.current_task and self.current_task.status == "压制中":
            self.process.kill()
            self.current_task.status = "已取消"
            self._cleanup_temp_vpy(self.current_task)
            self._delete_unfinished_file(self.current_task)
        self.queue.clear()
        self.current_task = None
        self._log_to_window("<b>[队列]</b> 任务队列已清空", "orange")

    def _delete_unfinished_file(self, task):
        """删除未完成的文件"""
        if os.path.exists(task.output_path):
            try:
                os.remove(task.output_path)
                self._log_to_window(f"<b>[{os.path.basename(task.video)}]</b> 已删除未完成文件: {os.path.basename(task.output_path)}", "orange")
            except Exception as e:
                self._log_to_window(f"<b>[{os.path.basename(task.video)}]</b> 删除文件失败: {e}", "red")

    def _log_to_window(self, message, color=None):
        """发送日志信号，解耦 GUI"""
        self.log_message.emit(message, color or "")

    def on_process_started(self):
        self.task_status_changed.emit(self.current_task.task_id)

    def on_process_finished(self, exit_code, exit_status):
        if self.current_task:
            self._cleanup_temp_vpy(self.current_task)
            if self.current_task.status == "已取消":
                self._log_to_window(f"<b>[{os.path.basename(self.current_task.video)}]</b> 任务已手动取消", "gray")
                self._delete_unfinished_file(self.current_task)
            elif exit_code == 0:
                self.current_task.status = "已完成"
                self.current_task.progress = 100
                self._log_to_window(f"<b>[{os.path.basename(self.current_task.video)}]</b> 压制成功", "green")
            else:
                self.current_task.status = "失败"
                self._log_to_window(f"<b>[{os.path.basename(self.current_task.video)}]</b> 压制失败 (退出码: {exit_code})", "red")
            
            self.task_status_changed.emit(self.current_task.task_id)
        
        self._start_next_task()

    def on_ready_read_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if self.current_task:
            prefix = f"[{os.path.basename(self.current_task.video)}]"
            for line in data.splitlines():
                line = line.strip()
                if line:
                    self._log_to_window(f"{prefix} {line}")

    def on_ready_read_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if not self.current_task: return
        
        prefix = f"[{os.path.basename(self.current_task.video)}]"
        for line in data.splitlines():
            line = line.strip()
            if not line: continue
            
            if not self.current_task.duration_parsed and 'Duration:' in line:
                match = DURATION_REGEX.search(line)
                if match:
                    h, m, s = match.groups()
                    self.current_task.total_duration = int(h) * 3600 + int(m) * 60 + float(s)
                    self.current_task.duration_parsed = True

            if 'time=' in line and self.current_task.total_duration:
                match = TIME_REGEX.search(line)
                if match:
                    h, m, s = match.groups()
                    curr = int(h) * 3600 + int(m) * 60 + float(s)
                    prog = min(100, int((curr / self.current_task.total_duration) * 100))
                    if prog != self.current_task.progress:
                        self.current_task.progress = prog
                        self.task_status_changed.emit(self.current_task.task_id)
            
            self._log_to_window(f"{prefix} {line}")
