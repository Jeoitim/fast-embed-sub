简体中文 | [English Document](document_en.md)

# Fast Embed Sub - Preset Writing Guide

This software uses a data-driven preset system. Any `.txt` files placed in the `presets/` directory are automatically loaded as encoding preset templates.

Preset authors can create **Classic FFmpeg command line presets** or advanced **VapourSynth (Vpy) post-processing presets**.

---

## 1. Classic FFmpeg Presets

Classic presets are extremely lightweight and contain only two sections:
1. **Line 1 (Required)**: Must start with `#` and serves as the description/tooltip displayed in the UI.
2. **Line 2 and onwards**: The FFmpeg command line template.

### 1.1 Supported Placeholders in Classic Presets
Use the following curly brace placeholders inside your command template. The engine automatically replaces them with absolute paths at runtime (Windows backslashes and path escaping are resolved automatically for use inside `-vf "subtitles..."`):
* `{input_v}`: Absolute path to the input video.
* `{input_s}`: Absolute path to the input subtitles (if no subtitle is selected, the `-vf "subtitles..."` segment is automatically removed by the engine).
* `{output_dir}`: Directory for the output file.
* `{filename}`: Output filename (without extension).
* `{format}`: Output container format extension.

### 1.2 Forced Format Syntax
Use `{format:xxx}` to enforce a specific container format (e.g. `mkv` or `webm`), overriding user format choices made in the GUI dropdown:
```bash
{output_dir}/{filename}.{format:mkv}
```

### 1.3 Path Conventions
- Always call the encoder via `components/ffmpeg.exe`. The software resolves this to the absolute executable path at runtime.
- Always use the `{output_dir}/{filename}.{format}` combination to target the output file.

### 1.4 Classic Preset Example
```bash
# Default Encoding - H.264 + AAC, Audio Direct Copy, High Quality (CRF 18)
components/ffmpeg.exe -y -i "{input_v}" -vf "subtitles={input_s}" -c:v libx264 -preset fast -crf 18 -c:a copy "{output_dir}/{filename}.{format}"
```

---

## 2. Advanced VapourSynth (Vpy) Presets

For advanced features like denoising, debanding, or AI super-resolution scaling, the software implements a portable VapourSynth post-processing pipeline. Vpy presets package parameter metadata, Vpy scripts, and FFmpeg commands together.

### 2.1 Vpy Preset File Structure

```
# Line 1: Preset description displayed in the UI

$custom-start
# YAML block declaring parameters for dynamic UI rendering
$custom-end

$vpy-start
# VapourSynth Python script template
$vpy-end

# Command template using vspipe and ffmpeg pipeline
```

### 2.2 YAML Parameter Configurations (`$custom-start` to `$custom-end`)
Parameters declared in this block are rendered dynamically in the UI. Supported fields:
* `id`: Unique identifier, matching `{id}` in the Vpy template.
* `name`: Label displayed in the GUI.
* `type`: Widget type. Supports three main custom UI modes and their aliases:
  * `slider` (alias `slidebar`): Slider. Renders a horizontal slider with a dynamic label showing the current value on the right, providing a premium and responsive feel.
    * **Fixed Ticks Mode**: If `options` is defined (e.g. `["low", "medium", "high"]` or `[0.25, 0.5, 0.75, 1.0]`), the slider snaps to those options and shows the corresponding option string in the label.
    * **Numeric Range Mode**: If no `options` list is provided, it slides within the defined `range`. If either range limit, step, or decimals is a float, it operates with floating-point math; otherwise, it handles integers.
  * `select` (alias `selectbox`): Dropdown menu (rendered as a Fluent ComboBox, requires `options` array).
  * `text` (alias `input`, `inputbox`): Single-line text input field (rendered as a LineEdit).
  * Also supports basic atom widgets: `float` (DoubleSpinBox), `integer` (SpinBox), and `bool` (CheckBox).
* `default`: Default value.
* `range`: Bounds array `[min, max]` (for `float` and `integer`).
* `decimals`: Decimal places (for `float`).
* `options`: List of select choices (for `select`), e.g., `["Option1", "Option2"]`.
* `group`: Category name. Widgets with the same group are grouped inside a bordered Fluent card.
* `order`: Placement ordering within the group.
* `tooltip`: Description displayed on mouse hover.

### 2.2.1 Preset Localization (Optional)
If a preset needs to display localized text for different GUI languages, you can define a `locales` block in the YAML metadata:
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
When the user switches the GUI language, the preset's name, description, and parameter fields (`name`, `group`, `tooltip`) will automatically adapt to the corresponding translation.

### 2.3 Dynamic Placeholders & Path Safety
All placeholders use curly braces `{placeholder}`. **During compilation, the engine handles path formats and escaping safety rules automatically:**

#### System Path Placeholders
* `{input_v}`: Absolute path to the input video (slashes are converted to `/`).
* `{input_s}`: Absolute path to the input subtitles (slashes are converted to `/`).
* `{preset_dir}`: Path to the `presets/` folder.
* `{components_dir}`: Path to the `components/` folder.
* `{preset_components_dir}`: Path to the current preset's isolated component directory (`presets/components/<PresetName>/`).

#### Escaping & Formatting Rules
1. **Path Parameters**: Path variables should be double-quoted in Vpy templates, e.g. `source="{input_v}"`. The compiler injects the raw path and replaces Windows `\` with `/` to avoid string escape issues.
2. **Custom String Parameters**: Replaces `\` with `\\` and `"` with `\"`, and **automatically wraps the value in double quotes**. If you write `mode = {denoise_mode}`, it compiles to `mode = "BM3D"`, preventing script syntax crashes.
3. **Boolean Parameters**: Converted to Python `True` / `False` keywords.
4. **Numeric Parameters**: Written as raw numbers.
5. **Python Dict Literal Safeguard**: The compiler only replaces placeholders matching known parameters. Standard Python dictionary syntax like `{ "a": 1 }` is ignored and kept intact.

### 2.4 Importing External DLLs and Python Modules
* **DLL Plugins**:
  Loaded using `core.std.LoadPlugin(r"{preset_components_dir}/myplugin.dll")`.
  *Note: DLL files inside `components/vapoursynth/plugins/` are auto-loaded by VapourSynth at startup and do not require manual `LoadPlugin` calls.*
* **Python Scripts (`.py`)**:
  Add search folders to `sys.path` before importing:
  ```python
  import sys
  sys.path.append(r"{preset_components_dir}")
  sys.path.append(r"{components_dir}/vapoursynth/plugins")
  import vsutil
  import my_filter
  ```

### 2.5 Complete Vpy Preset Example
```python
# Anime Deband and Scaling - Portable Example

$custom-start
parameters:
  - id: enable_deband
    name: Enable Deband
    type: bool
    default: true
    group: "Processing"
    order: 1
    tooltip: "Smooths color gradients and reduces banding"

  - id: resize_scale
    name: Resolution Scale
    type: select
    default: "0.5"
    options: ["1.0", "0.75", "0.5"]
    group: "Resolution"
    order: 2
$custom-end

$vpy-start
import sys
import vapoursynth as vs
core = vs.core

# 1. Register paths and import libraries
sys.path.append(r"{preset_components_dir}")
sys.path.append(r"{components_dir}/vapoursynth/plugins")
import vsutil

# 2. Load video and subtitles (inside VvapourSynth)
clip = core.ffms2.Source(source="{input_v}")
sub_path = "{input_s}"
if sub_path and not sub_path.endswith("empty.srt"):
    core.std.LoadPlugin(path=r"{preset_components_dir}/subtext.dll")
    clip = core.sub.TextFile(clip, file=sub_path)

# 3. Deband processing
if {enable_deband}:
    clip = core.f3kdb.Deband(clip, range=16, y=64, cb=64, cr=64, grainy=0, grainc=0)

# 4. Resize
scale = float({resize_scale})
if scale != 1.0:
    clip = core.resize.Bicubic(clip, width=int(clip.width*scale), height=int(clip.height*scale))

clip.set_output()
$vpy-end

# Stream decoded frames from vspipe to FFmpeg over pipe, coping audio stream
components/vspipe.exe --y4m "{vpy_path}" - | components/ffmpeg.exe -y -i - -i "{input_v}" -map 0:v -map 1:a? -c:v libx264 -preset fast -crf 20 -c:a copy "{output_dir}/{filename}.{format}"
```
