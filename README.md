# Fast Embed Sub

一款轻量级、跨平台的字幕压制工具，基于FFmpeg和PySide6开发，支持自定义预设，操作简单直观。

## 功能特点

-   **拖拽支持**：视频、字幕、输出目录均支持拖拽操作

> ⚠️ 本分支依赖 **PySide6-Fluent-Widgets**（PyPI 名称），可通过
> ```bash
> pip install PySide6-Fluent-Widgets
> ```
> 安装。导入语句为 `import qfluentwidgets` 。
> 主窗口基类为 `FluentWindow`，程序启动时会自动应用暗色 Fluent
> 主题，整个界面将呈现原生 Fluent 设计风格。

-   **自动检测**：输入视频后自动检测同名字幕文件（.srt/.ass/.ssa）
-   **预设系统**：支持自定义预设模板，灵活配置压制参数
-   **实时进度**：显示压制进度条和详细日志
-   **格式灵活**：支持多种输出格式（mkv/mp4/mov等）
-   **错误处理**：完善的错误提示和文件覆盖确认


## 预设系统

本工具采用纯数据驱动的预设系统，任何放在 `presets/` 目录下的 [.txt](file://c:\Users\timrt\Documents\02MyDevelopment\fast-embed-sub\presets\收藏.txt) 文件都会被自动识别为压制选项。

### 预设文件格式

预设文件必须包含两部分：
1. **第一行（必须）**：以 `#` 开头的备注信息，显示在界面说明栏中
2. **第二行及以后**：实际执行的命令行模板

### 支持的变量占位符

- `{input_v}` : 视频源文件路径
- `{input_s}` : 字幕源文件路径（已自动处理Windows路径转义）
- `{output_dir}` : 输出目录路径
- `{filename}` : 输出文件名（不包含扩展名）
- `{format}` : 输出文件格式（扩展名）

### 强制格式语法

在预设中可以使用 `{format:xxx}` 来强制指定输出格式，例如：
```
{output_dir}/{filename}.{format:mkv}
```

### 核心路径规范

请始终使用 `components/ffmpeg.exe` 来调用压制核心，软件会自动转换为绝对路径。

### 输出路径规范

使用 `{output_dir}/{filename}.{format}` 组合指定输出路径。

## 预设示例

### 默认预设（适合上传视频网站）
```
# 适合上传视频网站：速度快，画质极高(CRF 18)，体积中等偏大，音频无损直通。
components/ffmpeg.exe -i "{input_v}" -vf "subtitles='{input_s}'" -c:v libx264 -preset fast -crf 18 -c:a copy -y "{output_dir}/{filename}.{format}"
```

### 收藏预设（适合本地收藏与BT分享）
```
# 适合本地收藏与BT分享：采用 H.265 10bit 编码，体积小画质极佳，但压制速度较慢，音频无损直通。
components/ffmpeg.exe -i "{input_v}" -vf "subtitles='{input_s}'" -c:v libx265 -preset slow -crf 20 -pix_fmt yuv420p10le -c:a copy -y "{output_dir}/{filename}.{format:mkv}"
```

## 自定义预设

1. 在 `presets/` 目录下创建新的 [.txt](file://c:\Users\timrt\Documents\02MyDevelopment\fast-embed-sub\presets\收藏.txt) 文件
2. 按照预设格式编写备注和命令模板
3. 重启程序即可在预设列表中看到新选项