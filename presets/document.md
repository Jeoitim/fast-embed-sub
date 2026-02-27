# 极简字幕压制工具 - 预设编写指南

本软件采用纯数据驱动的预设系统。任何放在 `presets/` 目录下的 `.txt` 文件都会被自动识别为压制选项。

## 预设文件格式

预设文件必须包含两部分： 1. **第一行（必须）**：以 `#` 开头的备注信息。这段文字会显示在软件界面的说明栏中。 2. **第二行及以后**：实际执行的命令行模板。

### 支持的变量占位符

在编写命令行时，请使用以下占位符，软件在运行时会自动替换为用户的实际路径：

* `{input_v}` : 视频源文件路径。

* `{input_s}` : 字幕源文件路径（软件已自动处理 Windows 盘符和斜杠转义，直接放入滤镜参数即可）。

* `{output_dir}` : 输出目录路径。

* `{filename}` : 输出文件名（不包含扩展名）。

* `{format}` : 输出文件格式（扩展名，不包含点号）。注意：在预设中可以使用 `{format:webm}` 来指定特定格式，这样即使用户选择了其他格式，也会强制使用 webm 格式。

### 核心路径规范

请始终使用 `components/ffmpeg.exe` 来调用压制核心，软件会自动将其转换为绝对路径。

### 输出路径规范

请使用 `{output_dir}/{filename}.{format}` 的组合来指定输出文件路径，不要使用单独的 `{output}` 占位符。

## 编写示例 & 常用参数参考

```         
#适合上传视频网站：速度快，画质极高(CRF 18)，体积中等偏大，音频无损直通。
components/ffmpeg.exe -i "{input_v}" -vf "subtitles='{input_s}'" -c:v libx264 -preset fast -crf 18 -c:a copy -y "{output}"
```

```         
#VP9 编码，高质量，体积较小
components/ffmpeg.exe -i "{input_v}" -vf "subtitles='{input_s}'" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -b:a 128k -y "{output}"
```

## **强制使用 WebM 格式的示例**

```         
#VP9 编码，强制使用webm容器格式
components/ffmpeg.exe -i "{input_v}" -vf "subtitles='{input_s}'" -c:v libvpx-vp9 -b:v 0 -crf 30 -c:a libopus -b:a 128k -y "{output_dir}/{filename}.{format:webm}"
```