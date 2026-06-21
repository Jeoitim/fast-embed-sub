# 基础 VapourSynth 脚本模板 - 支持去色带、锐化、降噪与升采样
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

# 4. 降噪 (Denoise)
denoise_opt = {denoise}
denoise_str = float({denoise_strength})
if "mvtools" in str(denoise_opt).lower():
    thsad_val = int(denoise_str * 200)
    sup = core.mv.Super(clip, pel=2, sharp=2)
    mv_b1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=4)
    mv_f1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=4)
    mv_b2 = core.mv.Analyse(sup, isb=True, delta=2, overlap=4)
    mv_f2 = core.mv.Analyse(sup, isb=False, delta=2, overlap=4)
    clip = core.mv.Degrain2(clip, super=sup, mvbw=mv_b1, mvfw=mv_f1, mvbw2=mv_b2, mvfw2=mv_f2, thsad=thsad_val)
elif "bm3d" in str(denoise_opt).lower():
    try:
        import mvsfunc
        clip = mvsfunc.BM3D(clip, sigma=denoise_str)
    except Exception:
        pass

# 5. 尺寸缩放与升采样 (Resize & Upsampling)
scale = float({resize_scale})
super_res = {super_res}
if scale != 1.0:
    new_w = int(clip.width * scale)
    new_h = int(clip.height * scale)
    new_w = (new_w // 2) * 2
    new_h = (new_h // 2) * 2
    
    if scale > 1.0 and "znedi3" in str(super_res).lower():
        try:
            # 2倍神经网络放大
            clip = core.znedi3.nnedi3(clip, field=0, dh=True)
            clip = core.std.Transpose(clip)
            clip = core.znedi3.nnedi3(clip, field=0, dh=True)
            clip = core.std.Transpose(clip)
            
            # 如果缩放比例不刚好是 2.0，再微调缩放到目标尺寸
            if scale != 2.0:
                clip = core.resize.Bicubic(clip, width=new_w, height=new_h)
        except Exception:
            clip = core.resize.Bicubic(clip, width=new_w, height=new_h)
    else:
        clip = core.resize.Bicubic(clip, width=new_w, height=new_h)

# 6. 锐化 (Sharpen)
if {sharpen}:
    sharpen_str = float({sharpen_strength})
    clip = core.cas.CAS(clip, sharpness=sharpen_str)

# 7. 去色带 (Deband)
if {deband}:
    deband_thr = int({deband_threshold})
    clip = core.neo_f3kdb.Deband(clip, range=16, y=deband_thr, cb=deband_thr, cr=deband_thr, grainy=0, grainc=0)

# 8. 字幕渲染 (如果选择了字幕)
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

# 9. 输出
clip.set_output()
