# 基础 VapourSynth 脚本模板 - 用于传统 FFmpeg 预设支持 VS 几何与尺寸变换
import sys
import vapoursynth as vs
core = vs.core

# 1. 载入视频 (优先尝试 ffms2 或 lsmash)
try:
    clip = core.ffms2.Source(source="{input_v}")
except AttributeError:
    try:
        clip = core.lsmas.LWLibavSource(source="{input_v}")
    except AttributeError:
        # 万能回退
        clip = core.ffms2.Source(source="{input_v}")

# 2. 水平翻转
if {flip_horizontal}:
    clip = core.std.FlipHorizontal(clip)

# 3. 垂直翻转
if {flip_vertical}:
    clip = core.std.FlipVertical(clip)

# 4. 尺寸缩放
scale = float({resize_scale})
if scale != 1.0:
    new_w = int(clip.width * scale)
    new_h = int(clip.height * scale)
    # 确保是偶数
    new_w = (new_w // 2) * 2
    new_h = (new_h // 2) * 2
    clip = core.resize.Bicubic(clip, width=new_w, height=new_h)

# 5. 字幕渲染 (如果选择了字幕)
sub_path = "{input_s}"
if sub_path and not sub_path.endswith("empty.srt"):
    try:
        clip = core.sub.TextFile(clip, file=sub_path)
    except AttributeError:
        try:
            core.std.LoadPlugin(path=r"{components_dir}/vapoursynth/plugins/subtext.dll")
            clip = core.sub.TextFile(clip, file=sub_path)
        except Exception:
            pass

# 6. 输出
clip.set_output()
