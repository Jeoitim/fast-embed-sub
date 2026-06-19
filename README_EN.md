English | [简体中文 README](README.md)

# Fast Embed Sub

A lightweight, cross-platform subtitle embedding tool developed based on FFmpeg and PySide6. It supports custom presets and offers a simple, intuitive user interface.

## Features

- **Drag & Drop**: Videos, subtitles, and output directories all support drag-and-drop operations.
- **Auto-Detection**: Automatically detects same-named subtitle files (`.srt`/`.ass`/`.ssa`) when a video is loaded.
- **Preset System**: Supports custom preset templates for flexible configuration of encoding parameters.
- **Real-time Progress**: Displays encoding progress bar and detailed console logs.
- **Flexible Formats**: Supports multiple output formats (mkv, mp4, mov, etc.).

> ⚠️ This application depends on **PySide6-Fluent-Widgets** (PyPI package name), which can be installed via:
>
> ```bash
> pip install PySide6-Fluent-Widgets
> ```
>
> The import statement is `import qfluentwidgets`. The main window base class is `FluentWindow`. The app automatically applies a dark Fluent theme upon startup for a premium Windows 11 style design.

## 🖼️ Interface Preview

Main Interface - Clean and intuitive operation panel

![Main Interface](https://github.com/user-attachments/assets/0cafe3a2-0cc3-4f54-8b10-fe059b0c43e7)

Log Interface - Real-time encoding progress and detailed log console

![Log Interface](https://github.com/user-attachments/assets/1164bb04-d9b2-495c-9aa4-4d4289823ea7)

## 🌟 Modular Preset Configuration Sharing Philosophy

The core innovation of Fast Embed Sub is its **modular preset configuration sharing mechanism**, which changes how video encoding settings are configured and reused.

### 💡 Core Value

Traditional video embedding requires users to have deep knowledge of FFmpeg parameters and test repeatedly to achieve good results. Fast Embed Sub enables:

- **Zero-Barrier to Professional Parameters**: Directly download finely tuned preset files from others to get professional quality instantly.
- **One-Click to Ideal Quality**: No need to study complex parameters—just choose the appropriate preset.
- **Community Optimization Sharing**: Experienced users can package and share their best-practice presets.

### 🚀 Usage Workflow

1. **Get Preset**: Download a preset matching your needs (in `.txt` format) from the community.
2. **Place File**: Put the preset file into the `presets/` directory of the application.
3. **Select Preset**: Choose the preset from the dropdown in the UI.
4. **Start Embedding**: Choose your video and subtitle, then add to the queue.

### 📦 Preset Sharing Ecology

We encourage users to share their configurations:

- **Professional Tuning**: Share combinations of parameters validated by extensive testing.
- **Scenario Experts**: Configurations optimized for specific platforms (YouTube, Bilibili, local archiving, etc.).
- **Beginner-Friendly**: Simple, understandable setups to help newcomers get started quickly.

## About the Preset System

This tool uses a pure data-driven preset system. Any `.txt` file placed in the `presets/` directory will be parsed automatically.

### 1. Preset File Format

The preset file must contain two sections:
1. **First line (required)**: Description beginning with `#`, which is displayed in the UI's description card.
2. **Second line and onwards**: The actual command line template to execute.

### 2. Supported Placeholder Variables

- `{input_v}`: Source video file path.
- `{input_s}`: Source subtitle file path (Windows path separator and colon escapes are automatically handled).
- `{output_dir}`: Output directory path.
- `{filename}`: Output filename (without extension).
- `{format}`: Output format/container extension.

### 3. Forced Container Format Syntax

You can use `{format:xxx}` in the preset to force a specific output extension, e.g.:

```txt
{output_dir}/{filename}.{format:mkv}
```

### 4. Path Conventions

Always use `components/ffmpeg.exe` to call the FFmpeg encoder; the software will automatically resolve it to an absolute path. Always use the `{output_dir}/{filename}.{format}` combination to specify the output path.

### 5. Preset Examples

#### Default Preset (optimized for video upload sites)

```txt
# Suitable for video upload sites: Fast speed, extremely high quality (CRF 18), medium-large size, audio copy.
components/ffmpeg.exe -i "{input_v}" -vf "subtitles={input_s}" -c:v libx264 -preset fast -crf 18 -c:a copy -y "{output_dir}/{filename}.{format}"
```

#### Archive Preset (optimized for high-quality local collection)

```txt
# Suitable for local collection & torrent sharing: H.265 10bit encoding, small size, excellent quality, slower encoding speed, audio copy.
components/ffmpeg.exe -i "{input_v}" -vf "subtitles={input_s}" -c:v libx265 -preset slow -crf 20 -pix_fmt yuv420p10le -c:a copy -y "{output_dir}/{filename}.{format:mkv}"
```

#### Custom Presets

1. Create a new `.txt` file inside the `presets/` directory.
2. Write the description line (with `#`) and command template.
3. Restart or reload the app to see it in the list.
