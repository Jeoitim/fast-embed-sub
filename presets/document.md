[English Document](document_en.md) | 简体中文

# Fast Embed Sub - 预设文件编写指南

本工具采用纯数据驱动的预设系统。任何放置在 `presets/` 目录下的 `.txt` 文件都会被自动识别加载为压制选项。

预设编写者可以根据需求编写 **传统 FFmpeg 命令行预设** 或全新的 **VapourSynth (Vpy) 高级后处理预设**。

---

## 1. 传统 FFmpeg 预设格式

传统预设非常轻量，仅需包含两部分：
1. **第 1 行（必须）**：以 `#` 开头的说明文本，该文本会展示在软件界面的预设说明栏中。
2. **第 2 行及以后**：实际执行的 FFmpeg 命令行模板。

### 1.1 传统预设支持的占位符
在编写命令行模板时，使用以下大括号占位符，软件在运行时会自动将其替换为用户选择的绝对路径（已自动处理 Windows 下的反斜杠转义与路径转义，可安全用于 `subtitles` 滤镜）：
* `{input_v}`：视频源文件路径。
* `{input_s}`：字幕源文件路径（如果未选择字幕，该预设中的 `-vf "subtitles..."` 段会被引擎自动剔除，无需手动分流）。
* `{output_dir}`：输出目录路径。
* `{filename}`：输出视频文件名（不包含扩展名）。
* `{format}`：输出文件格式扩展名。

### 1.2 强制指定格式语法
在预设中可以使用 `{format:xxx}` 来强制指定特定的封装格式（例如强制为 `webm` 或 `mkv`），此时即使用户在 GUI 中选择了其他格式，也会强制使用指定的容器：
```bash
{output_dir}/{filename}.{format:mkv}
```

### 1.3 调用路径规范
- 请始终使用 `components/ffmpeg.exe` 来调用压制核心，软件在运行时会自动将其转换为正确的绝对路径。
- 始终使用 `{output_dir}/{filename}.{format}` 组合指定输出视频路径。

### 1.4 传统预设示例
```bash
# 默认压制 - H.264 + AAC 编码，音频直通，画质极高(CRF 18)
components/ffmpeg.exe -y -i "{input_v}" -vf "subtitles={input_s}" -c:v libx264 -preset fast -crf 18 -c:a copy "{output_dir}/{filename}.{format}"
```

---

## 2. 新型 VapourSynth (Vpy) 预设规范

为了支持高级视频修复、超分辨率缩放、去色带与复杂降噪，软件集成了 VapourSynth 便携式后处理管线。Vpy 预设文件支持在同一个文件中声明“动态参数配置卡片”、“Python/Vpy 脚本模板”和“联合编码命令行”。

### 2.1 Vpy 预设整体结构

```
# 第一行：预设说明显示文本

$custom-start
# 声明在 GUI 中动态生成的参数属性 (YAML 代码块)
$custom-end

$vpy-start
# VapourSynth 脚本模板 (Python 代码块)
$vpy-end

# 实际执行的 vspipe 联合 ffmpeg 管道压制命令模板
```

### 2.2 YAML 参数定义说明 (`$custom-start` 至 `$custom-end`)
支持在 YAML 中声明多个参数，软件会在主界面中动态渲染为对应的控件。参数属性如下：
* `id`：变量唯一标识符，对应 Vpy 脚本模板中的 `{id}`。
* `name`：在 GUI 界面显示的控件标签名称。
* `type`：控件类型。支持以下三种主要自定义 UI 模式及别名：
  * `slider`（别名 `slidebar`）：滑动条。在右侧配有实时数值/选项标签，极具现代感和高级质感。
    * **固定刻度模式**：若配置了 `options`（例如 `["low", "medium", "high"]` 或 `[0.25, 0.5, 0.75, 1.0]`），滑动条将在对应选项索引间滑动，标签实时显示该选项内容。
    * **数值范围模式**：若未配置 `options`，则根据 `range` 渲染。如果 `range` 边界值或 `step` 中有浮点数（或配置了 `decimals`），则自动作为浮点滑动条运行；否则作为整数滑动条。
  * `select`（别名 `selectbox`）：下拉选择框（渲染为 ComboBox，需配置 `options` 列表）。
  * `text`（别名 `input`、`inputbox`）：单行文本输入框（渲染为 LineEdit）。
  * 另兼容基础原子类型：`float`（DoubleSpinBox 微调框）、`integer`（SpinBox 微调框）、`bool`（CheckBox 开关）。
* `default`：默认值。
* `range`：取值范围（适用于 `slider`、`float` 和 `integer`），格式如 `[最小值, 最大值]`。
* `step`：步进/步长值（适用于 `slider`）。可以为浮点数（如 `0.1`、`0.05`）或整数（如 `8`）。设置后，拖动滑动条时数值会精确对齐并吸附到步长值的整数倍（例如，范围 `[16, 256]`，步进 `8`，拖动时会自动吸附在 `16, 24, 32...` 等刻度上，避免显示任意零散值）。
* `decimals`：小数点保留位数（适用于浮点数 `slider` 及 `float` 微调框）。
* `options`：下拉列表可选项（适用于 `select` 以及固定刻度模式下的 `slider`），格式如 `["Option1", "Option2"]`。
* `group`：界面分组卡片名称（同名分组会打包在一个带边框的 Fluent 卡片中）。
* `order`：在分组卡片中的显示顺序。
* `tooltip`：鼠标悬停在控件上时的气泡提示信息。

### 2.2.1 预设本地化配置 (可选)
如果需要预设在不同界面语言下显示对应的文本，可以在 YAML 中添加 `locales` 配置区块：
```yaml
locales:
  en:
    name: "WebM"
    desc: "Suitable for web embedding: VP9 encoding, outputs WebM format..."
    parameters:
      flip_horizontal:
        name: "Horizontal Flip (Flip H)"
        group: "Geometry"
        tooltip: "Whether to mirror the video horizontally"
```
当用户在 GUI 中将语言切换为对应语言（如 `en`）时，预设名称、描述以及各个自定义参数的 `name`、`group` 和 `tooltip` 都会自动应用此处定义的翻译，从而实现完全的语言解耦。

### 2.3 动态变量与路径占位符
所有的占位符均使用大括号 `{placeholder}` 语法。**在 VapourSynth 脚本被编译时，引擎会自动处理转义与格式转换：**

#### 系统内置路径占位符
* `{input_v}`：视频源绝对路径（已自动将反斜杠 `\` 转为正斜杠 `/`）。
* `{input_s}`：字幕源绝对路径（已自动将反斜杠 `\` 转为正斜杠 `/`）。
* `{preset_dir}`：指向本地的 `presets/` 目录。
* `{components_dir}`：指向全局的 `components/` 目录。
* `{preset_components_dir}`：指向当前预设专有的隔离文件夹 `presets/components/<预设文件名>/`。

#### 安全转义与替换规则
1. **路径类参数**：在 Vpy 模板中应使用双引号包裹，如 `source="{input_v}"`。注入时仅替换路径内容并自动将 Windows `\` 替换为 `/`，确保 Python 字符串解释安全。
2. **自定义字符串参数**：注入时自动对其内部的 `\` 替换为 `\\`、`"` 替换为 `\"` 进行转义，并**自动在两端包裹双引号**。因此，若你的模板中写有 `mode = {denoise_mode}`，被替换后将成为 `mode = "BM3D"`，安全防崩。
3. **布尔参数**：自动转换为 Python 的 `True` / `False` 关键字。
4. **数值参数**：转换为对应数字的字符串表示。
5. **Python 字典字面量保护**：系统只替换在变量字典中存在的占位符。如果你在 Vpy 模板中写了 `{ "a": 1 }` 这样的原生字典，解析器会识别到 `"a": 1` 不是合法变量而跳过替换，原样完整保留。

### 2.4 外部滤镜导入规范 (二进制 DLL 与 Python 脚本)
* **载入二进制插件（`.dll`）**：
  通过 `core.std.LoadPlugin(r"{preset_components_dir}/filename.dll")` 加载。建议利用 `r""` 原始字符串防止转义问题。
  *注意：存放在公共 `components/vapoursynth/plugins/` 目录下的 dll 在启动时会被 VS 自动加载，通常无需手动调用 `LoadPlugin`。*
* **载入 Python 滤镜脚本（`.py`）**：
  由于 `.py` 文件存放在便携/隔离目录，必须在 `import` 之前使用 `sys.path.append` 将目标路径加入 Python 搜索路径：
  ```python
  import sys
  # 将当前预设的隔离组件包目录和全局 plugins 目录加入搜索路径
  sys.path.append(r"{preset_components_dir}")
  sys.path.append(r"{components_dir}/vapoursynth/plugins")
  # 导入滤镜文件
  import vsutil
  import my_preset_filter
  ```

### 2.5 完整 Vpy 预设示例
```python
# 动漫高清缩放与去色带预设 - 使用隔离组件加载

$custom-start
parameters:
  - id: enable_deband
    name: 启用去色带
    type: bool
    default: true
    group: "画面修复"
    order: 1
    tooltip: "有效消除画面中的色彩断层"

  - id: resize_scale
    name: 画面缩放倍数
    type: select
    default: "0.5"
    options: ["1.0", "0.75", "0.5"]
    group: "画面尺寸"
    order: 2
$custom-end

$vpy-start
import sys
import vapoursynth as vs
core = vs.core

# 1. 注册隔离目录并引入公共/专属 Python 滤镜
sys.path.append(r"{preset_components_dir}")
sys.path.append(r"{components_dir}/vapoursynth/plugins")
import vsutil

# 2. 载入视频与同名外挂字幕 (VS 内部渲染)
clip = core.ffms2.Source(source="{input_v}")
sub_path = "{input_s}"
if sub_path and not sub_path.endswith("empty.srt"):
    # 动态载入隔离的专有字幕渲染插件
    core.std.LoadPlugin(path=r"{preset_components_dir}/subtext.dll")
    clip = core.sub.TextFile(clip, file=sub_path)

# 3. 去色带 (引用自定义 bool 变量)
if {enable_deband}:
    clip = core.f3kdb.Deband(clip, range=16, y=64, cb=64, cr=64, grainy=0, grainc=0)

# 4. 缩放 (引用自定义 select 变量，转换为 float)
scale = float({resize_scale})
if scale != 1.0:
    clip = core.resize.Bicubic(clip, width=int(clip.width*scale), height=int(clip.height*scale))

clip.set_output()
$vpy-end

# vspipe 解码为 y4m 流，并通过管道直接传输给 FFmpeg 压制，原视频音频无损直通
components/vspipe.exe --y4m "{vpy_path}" - | components/ffmpeg.exe -y -i - -i "{input_v}" -map 0:v -map 1:a? -c:v libx264 -preset fast -crf 20 -c:a copy "{output_dir}/{filename}.{format}"
```