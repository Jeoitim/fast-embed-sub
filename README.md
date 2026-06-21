[English README](README_EN.md) | 简体中文

# Fast Embed Sub

Fast Embed Sub 是一款轻量级、跨平台的极简视频字幕压制工具。基于 **PySide6** 和 **FFmpeg** 构建，并融入了 Fluent 现代设计风格。它旨在提供一个极其简单、流畅的视频压制体验，用户只需简单的拖拽操作，即可快速完成专业级的硬字幕嵌入与视频转码。

---

## 📖 面向普通用户：快速开始

如果你只是想压制视频和嵌入字幕，Fast Embed Sub 提供了极其傻瓜式的操作：

### 核心功能
* 🎛️ **极简拖拽**：支持将视频、字幕文件或输出文件夹直接拖入软件界面，无需繁琐寻路。
* 🔍 **智能关联**：输入视频后，软件会自动扫描视频同目录下同名的 `.srt` / `.ass` / `.ssa` 字幕文件并自动填入。
* ⚡ **多任务队列**：支持将多个压制任务依次“加入任务队列”，后台依次自动压制，不占用前台操作。
* 📝 **实时进度与日志**：提供直观的进度条以及详细的底层 FFmpeg 命令行实时输出日志，压制细节一目了然。

### 快速使用步骤
1. **下载或运行软件**：启动 Fast Embed Sub。
2. **选择源文件**：将你的视频拖入软件，若有同名同目录字幕，软件会自动识别；亦可手动选择。
3. **选择压制预设**：在下拉列表中选择一个适合你的预设（如“默认”、“极速”或“Vpy测试预设”）。
4. **开始压制**：点击右下角“加入任务队列”按钮。压制会自动在后台队列中启动，你可以在“任务队列”选项卡中查看当前进度或取消任务。

---

## 💡 面向极客与调参师：模块化共享与隔离生态

Fast Embed Sub 的核心价值不仅在于“压制”，更在于其**模块化预设配置分享理念**与全新的 **VapourSynth 高级后处理运行环境**。

### 1. 为什么需要模块化预设共享？
视频调参是一门专业技术。为了画质与体积的平衡，需要反复调试 FFmpeg 参数，对普通用户门槛极高。
通过 Fast Embed Sub，极客与专业调参师可以将自己调试好的压制参数打包成一个 `.txt` 预设文件。普通用户只需将该文件放入 `presets/` 目录下，重启软件即可立即获得专业级压制效果，实现**零门槛的专业调参成果复用**。

### 2. 便携式 VapourSynth (VS) 环境隔离生态
在本次重大升级中，我们引入了 VapourSynth 便携版后处理系统。
VapourSynth 是基于 Python 的强大视频处理框架，在去色带、降噪、超分辨率缩放等方面远超 FFmpeg 内置滤镜。为了解决 VapourSynth 复杂的环境配置以及“滤镜 DLL 相互污染/版本冲突”的问题，我们设计了**便携隔离化生态**：
* **便携执行**：将 VapourSynth 便携版解压至 `components/vapoursynth/` 目录中。软件在运行压制时，会自动为子进程载入并激活便携版环境变量，免去系统安装 Python/VvapourSynth 注册表的烦恼。
* **隔离补充包**：
  * **全局滤镜**：放置在 `components/vapoursynth/plugins/` 目录中，供所有预设通用。
  * **预设专有滤镜（防污染）**：如果某个预设对插件版本有特殊要求或包含庞大的模型权重，可以直接将其放置在该预设专属的隔离目录：`presets/components/<预设名称>/` 中。

---

## 🛠️ 面向预设编写者：预设文件编写指南

本工具采用纯数据驱动的预设系统。任何放置在 `presets/` 目录下的 `.txt` 文件都会被自动识别加载为压制选项。

为了帮助您编写自定义的 **FFmpeg 命令行预设** 或高级的 **VapourSynth (Vpy) 便携化隔离预设**，我们准备了非常详尽的预设文件格式定义、YAML控件属性、路径变量及安全转义教程：

👉 **[预设文件编写指南 (简体中文)](presets/document.md)**
👉 **[Preset Writing Guide (English)](presets/document_en.md)**

---

## 💻 面向二次开发者：技术栈与架构设计

如果你想贡献代码或对 Fast Embed Sub 进行二次开发，请参考以下指南。

### 1. 核心技术栈与依赖
* **开发语言**：Python >= 3.12
* **GUI 框架**：PySide6 (Qt for Python)
* **UI 组件库**：[PySide6-Fluent-Widgets](https://github.com/zhiyiYo/PySide6-Fluent-Widgets)（提供美观的 Fluent 现代设计控件及暗色主题支持）
* **解析器**：PyYAML (用于解析预设文件中的 YAML 参数声明)
* **打包工具**：Nuitka 4.x (用于将 Python 脚本编译为独立无损的高性能可执行程序)

### 2. 核心模块与架构关系

整个应用程序由以下五个核心源文件构成，逻辑清晰解耦：

* **[main.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/main.py)**：入口程序。负责应用启动闪屏渲染（SplashScreen）、异步加载重型组件、应用 Fluent 风格全局暗色主题、以及窗口初始化展示。
* **[preset_parser.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/preset_parser.py)**：预设解析核心。通过正则与切片技术分离 YAML 声明、Vpy 模板和命令行模板。包含统一替换路径和转义字符串的 `compile_vpy_script` 静态方法。
* **[vpy_param_widget.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/vpy_param_widget.py)**：动态 UI 面板。根据 `PresetParser` 读取的 YAML 参数配置，动态在界面上实例化控件，对参数输入范围及精度进行 Qt 约束校验，并向上提供当前参数值的字典。
* **[gui.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/gui.py)**：主窗口与交互界面。基于 `FluentWindow` 构建，处理拖拽事件（DragDropLineEdit）、更新源文件信息、管理界面卡片联动、并在预设下拉列表变更时动态挂载或隐藏 `vpy_param_widget`。
* **[engine.py](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/engine.py)**：转码与队列调度引擎。
  * 将任务放入 `TranscodeTask` 状态模型并调度。
  * 针对 Vpy 预设，在系统 Temp 目录下写入经过安全转义编译的临时 `.vpy` 文件。
  * 搜索并定位便携版 `vspipe.exe`。若检测到 `components/vapoursynth`，在 `QProcessEnvironment` 中注入便携版 `PATH` 与 `PYTHONPATH` 路径。
  * 调度 `QProcess`。如果命令行含有管道符 `|`，则使用 `cmd.exe /c` 执行流式任务；否则直接调用可执行命令。
  * 探测视频时长以校准管道压制时的进度刷新，并在压制完成/手动取消任务后负责清理临时生成的 `.vpy` 文件。

### 3. 本地开发与运行
1. **克隆或进入工作区**：
   ```bash
   cd fast-embed-sub
   ```
2. **安装依赖**：
   我们使用 `uv` 提高依赖解析与安装速度。你可以使用以下命令：
   ```bash
   uv pip install -r requirements.txt
   ```
   *（或者直接使用传统的 `pip install -r requirements.txt`）*
3. **运行程序**：
   ```bash
   python main.py
   ```

### 4. 编译打包与安装包制作说明 (`build.ps1`)
项目根目录下提供了用于编译打包和安装包制作的 PowerShell 脚本 [build.ps1](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/build.ps1)。
运行该脚本会全自动执行以下流程：
1. **自动生成图标**：读取 `assets/icon.png` 自动转换为支持 Windows 的多尺寸 `assets/icon.ico` 图标。
2. **Nuitka STANDALONE 编译**：自动调用 `.venv` 环境，将 Python 代码编译为高性能的 Windows 独立绿色包，生成在 `outputs/main.dist/` 中。
3. **资源及依赖同步**：物理复制 `components/`、`presets/` 和 `assets/` 文件夹至打包目录。
4. **运行库优化 (体积瘦身)**：自动分析打包后的 `components` 运行库目录，删除不必要的 C/C++ 头文件 (`include/`)、`.pdb` 调试文件、`get-pip.py` 脚本以及所有的 `*.dist-info`/`*.egg-info` 元数据与 `__pycache__` 缓存，大幅减少文件个数并节省 ~25MB 体积。
5. **安全 UPX 压缩**：调用系统的 UPX 压缩打包目录下的二进制文件。**脚本自动跳过了 `components/` 目录**（包含 FFmpeg 和 VapourSynth 的 DLL/EXE 插件），防止对外部运行库造成损坏，仅压缩主程序本身。
6. **NSIS 安装包制作**：自动检测系统中的 `makensis` 编译器，读取 [installer.nsi](file:///C:/Users/timrt/Documents/02MyDevelopment/fast-embed-sub/installer.nsi) 配置文件，自动将精简优化后的绿色包编译为一键安装包：`outputs/FastEmbedSub_v1.0.0_Setup.exe` (约 206MB)。
   * 安装包自带桌面与开始菜单快捷方式、卸载项注册，并具备安装路径注册表匹配与主程序验证的多重安全检查，防止卸载时误删用户其他文件。
