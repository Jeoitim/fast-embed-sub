简体中文 | English README

# Fast Embed Sub

Fast Embed Sub is a lightweight, cross-platform video subtitle embedding and transcoding tool. Built on **PySide6** and **FFmpeg**, and styled with modern Fluent design themes, it provides a simple, fluid, and clutter-free transcoding experience. Drag-and-drop your media and subtitles to quickly encode them with professional settings.

---

## 📖 For Regular Users: Quick Start

If you just want to transcode videos and embed subtitles, Fast Embed Sub is designed for simplicity:

### Key Features
* 🎛️ **Drag-and-Drop**: Simply drag files or directories directly onto the UI inputs. No file-explorer navigation needed.
* 🔍 **Auto-Association**: When you load a video, the software automatically scans for subtitles (`.srt` / `.ass` / `.ssa`) with the same name in the same directory.
* ⚡ **Task Queue**: Add multiple transcoding tasks to the queue and let the background queue process them sequentially without freezing the UI.
* 📝 **Real-Time Log & Progress**: A visual progress bar along with raw stderr/stdout outputs from FFmpeg allows you to monitor encoding details.

### How to Use
1. **Run the App**: Launch Fast Embed Sub.
2. **Choose Source Files**: Drag your video into the input box. If matching subtitles exist, they will be loaded automatically.
3. **Select Preset**: Choose a preset from the dropdown (e.g., "Default", "Fast", or "Vpy Test Preset").
4. **Add to Queue**: Click "Add to Queue". Transcoding starts automatically in the background. You can check status and cancel tasks in the "Queue" tab.

---

## 💡 For Geeks and Encoders: Modular Preset Ecosystem

Fast Embed Sub's primary design goal is its **modular preset sharing model** coupled with a new **portable VapourSynth post-processing pipeline**.

### 1. Why Modular Preset Sharing?
Video encoding requires a deep understanding of FFmpeg parameters and endless test cycles to achieve the perfect size-to-quality balance.
With Fast Embed Sub, geeks can package optimized settings into simple `.txt` files. Users can download these files, place them in the `presets/` folder, and instantly access expert-tuned configurations after restarting the software, making **expert profiles reusable for everyone**.

### 2. Portable VapourSynth (VS) Environment Isolation
In this major upgrade, we introduced a portable VapourSynth post-processing pipeline.
VapourSynth is a Python-based video processing framework that excels in de-banding, de-noising, and super-resolution scaling. To avoid complex local Python setups and version conflicts ("DLL Hell"), we designed a **portable sandbox environment**:

## 🛠️ For Preset Authors: Preset Writing Guide

This software uses a data-driven preset system. Any `.txt` files placed in the `presets/` directory are automatically loaded as encoding preset templates.

For details on how to write custom **FFmpeg command line presets** or advanced **VapourSynth (Vpy) portable presets**, please refer to our comprehensive guide:

👉 **[预设文件编写指南 (简体中文)](presets/document.md)**
👉 **[Preset Writing Guide (English)](presets/document_en.md)**

---

## 💻 For Developers: Technical Stack & Architecture

Refer to these guidelines if you want to inspect, modify, or compile Fast Embed Sub.

### 1. Technology Stack & Dependencies
* **Language**: Python >= 3.12
* **GUI Framework**: PySide6 (Qt for Python)
* **UI Controls**: [PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PySide6-Fluent-Widgets) (Fluent design controls and dark theme framework)
* **YAML Parser**: PyYAML (to parse preset custom parameter metadata)
* **Compiler/Packager**: Nuitka 4.x (compiles Python code to optimized native executables)

### 2. File Architecture

The core functionality is split across five self-contained modules:

* **[main.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/main.py)**: Entry point. Displays the splash screen, asynchronously imports dependencies, applies dark themes, and shows the main window.
* **[preset_parser.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/preset_parser.py)**: Preset parsing engine. Splits YAML parameters, VvapourSynth templates, and command lines. Resolves type-safe parameter values and path slashes.
* **[vpy_param_widget.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/vpy_param_widget.py)**: Dynamic parameter widgets. Renders PySide6 controls dynamically from YAML configurations and handles form value extraction.
* **[gui.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/gui.py)**: Main UI window. Handles drag-and-drop (DragDropLineEdit), controls updates, layout margins, page switching, and preset parameters widget attachments.
* **[engine.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/engine.py)**: Scheduler and transcoding engine.
  * Dispatches `TranscodeTask` objects.
  * Writes compiled temporary `.vpy` scripts.
  * Checks for portable `vspipe.exe`. Sets environment variables (`PATH`, `PYTHONPATH`) on QProcess to run portable VapourSynth without installation dependencies.
  * Spawns `QProcess`. Wraps pipe commands inside `cmd.exe /c` on Windows.
  * Probes video duration to calibrate background task progress calculations, and deletes temporary `.vpy` files after execution.

### 3. Local Development
1. **Navigate to the Project**:
   ```bash
   cd fast-embed-sub
   ```
2. **Install Dependencies**:
   We recommend using `uv` to manage package installations:
   ```bash
   uv pip install -r requirements.txt
   ```
3. **Run App**:
   ```bash
   python main.py
   ```

### 4. Compilation & Packaging (`build.ps1`)
The repository includes a packaging script [build.ps1](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/build.ps1) that compiles the python files using Nuitka, syncs assets and presets to the output folder `dist/`, and runs post-build UPX compression on output executables and DLLs to minimize publication size.
