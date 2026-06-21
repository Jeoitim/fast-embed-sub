# 0. 自动生成 icon.ico 文件 (用于 Nuitka 和 NSIS 图标)
$IcoFile = "assets/icon.ico"
$PngFile = "assets/icon.png"
if (Test-Path $PngFile) {
    Write-Host "正在生成 Windows 多尺寸图标 (assets/icon.ico)..." -ForegroundColor Yellow
    $PythonExe = "python"
    if (Test-Path ".venv\Scripts\python.exe") {
        $PythonExe = ".venv\Scripts\python.exe"
    }
    & $PythonExe -c "from PIL import Image; img = Image.open('$PngFile'); img.save('$IcoFile', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])" 2>&1 | Out-Null
    if (Test-Path $IcoFile) {
        Write-Host " [OK] 图标生成成功" -ForegroundColor Green
    } else {
        Write-Host " [!] 警告: 图标生成失败，将使用 Nuitka 默认转换" -ForegroundColor Red
    }
}

# 1. 定义输出目录
$OutputDir = "outputs"

# 2. 自动管理 .gitignore
$GitignoreFile = ".gitignore"
$IgnoreEntry = "$OutputDir/"

if (Test-Path $GitignoreFile) {
    $Content = Get-Content $GitignoreFile
    if ($Content -notcontains $IgnoreEntry) {
        Add-Content $GitignoreFile "`n$IgnoreEntry"
        Write-Host "已将 $IgnoreEntry 添加到 .gitignore" -ForegroundColor Green
    }
} else {
    Set-Content $GitignoreFile -Value "$IgnoreEntry"
    Write-Host "已创建 .gitignore 并添加 $IgnoreEntry" -ForegroundColor Green
}

# 3. 检测 UPX 并组装 Nuitka 打包参数
$NuitkaArgs = @(
    "--standalone",
    "--msvc=latest",
    "--show-memory",
    "--show-progress",
    "--jobs=$env:NUMBER_OF_PROCESSORS",
    "--plugin-enable=pyside6",
    "--windows-disable-console",
    "--output-dir=$OutputDir",
    "--output-filename=FastEmbedSub",
    "--lto=yes"
)

if (Test-Path $IcoFile) {
    $NuitkaArgs += "--windows-icon-from-ico=$IcoFile"
} elseif (Test-Path $PngFile) {
    $NuitkaArgs += "--windows-icon-from-ico=$PngFile"
}

$UseUpx = $false
if (Get-Command "upx" -ErrorAction SilentlyContinue) {
    $UseUpx = $true
    Write-Host '检测到 UPX，将在打包完成后自动压缩 exe 和 dll 文件以缩减体积。' -ForegroundColor Green
} else {
    Write-Host '未检测到 UPX。提示：如果想要将软件体积进一步缩减 ~50%，请前往 https://upx.github.io 下载 UPX 并将其所在目录加入到系统环境变量 PATH 中。' -ForegroundColor Yellow
}

# 排除不需要的第三方库和 Qt 子模块，减少打包体积
$Excludes = @(
    "scipy", "numpy", "pyqt5", "matplotlib", "pandas",
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras", "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic", "PySide6.Qt3DRender", "PySide6.QtBluetooth", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtDesigner", "PySide6.QtLocation", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtNfc", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2", "PySide6.QtRemoteObjects", "PySide6.QtSensors", "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtUiTools",
    "PySide6.QtWebChannel", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebSockets", "PySide6.QtNetwork", "PySide6.QtOpenGL",
    "PySide6.QtDBus", "PySide6.QtPrintSupport"
)

foreach ($Exc in $Excludes) {
    $NuitkaArgs += "--nofollow-import-to=$Exc"
}

$NuitkaArgs += "--follow-imports"
$NuitkaArgs += "main.py"

Write-Host "开始运行 Nuitka 进行 Standalone 编译..." -ForegroundColor Cyan
$NuitkaExe = "nuitka"
if (Test-Path ".venv\Scripts\nuitka.exe") {
    $NuitkaExe = ".venv\Scripts\nuitka.exe"
}
& $NuitkaExe @NuitkaArgs


# 4. 强制搬运资源文件夹 (保底方案)
$DistPath = "$OutputDir/FastEmbedSub.dist"
if (-not (Test-Path $DistPath)) {
    $DistPath = Get-ChildItem -Path "$OutputDir/*.dist" | Select-Object -ExpandProperty FullName -First 1
}

Write-Host "打包完成！生成的程序位于: $DistPath" -ForegroundColor Cyan

Write-Host "`n正在执行资源物理搬运..." -ForegroundColor Yellow

$FoldersToCopy = @("components", "presets", "assets")

foreach ($Folder in $FoldersToCopy) {
    if (Test-Path $Folder) {
        $Dest = Join-Path $DistPath $Folder
        # 先清理已存在的旧目录，防止 Copy-Item 嵌套复制
        if (Test-Path $Dest) {
            Remove-Item -Path $Dest -Recurse -Force
        }
        Copy-Item -Path $Folder -Destination $DistPath -Recurse -Force
        Write-Host " [OK] 已同步目录: $Folder -> $Dest" -ForegroundColor Green
    } else {
        Write-Host " [!] 警告: 未找到源目录 $Folder" -ForegroundColor Red
    }
}

# 5. 优化打包运行库 (删除冗余开发文件，缩减安装包体积)
Write-Host "`n正在优化打包运行库 (删除冗余开发文件)..." -ForegroundColor Yellow
$ComponentsDist = Join-Path $DistPath "components"
if (Test-Path $ComponentsDist) {
    # 删除所有 .pdb 调试符号文件
    Get-ChildItem -Path $ComponentsDist -Recurse -Filter "*.pdb" | Remove-Item -Force
    Write-Host " [OK] 已清理所有 .pdb 调试符号文件" -ForegroundColor Green

    # 删除 VapourSynth 中的 C/C++ 开发头文件 include 目录和 pkgconfig 编译配置目录
    $VSInclude = Join-Path $ComponentsDist "vapoursynth/include"
    if (Test-Path $VSInclude) {
        Remove-Item -Path $VSInclude -Recurse -Force
        Write-Host " [OK] 已清理开发头文件 (include)" -ForegroundColor Green
    }
    $VSPkgConfig = Join-Path $ComponentsDist "vapoursynth/pkgconfig"
    if (Test-Path $VSPkgConfig) {
        Remove-Item -Path $VSPkgConfig -Recurse -Force
        Write-Host " [OK] 已清理编译配置 (pkgconfig)" -ForegroundColor Green
    }

    # 删除 get-pip.py 脚本 (只在搭建环境时需要)
    $VSGetPip = Join-Path $ComponentsDist "vapoursynth/get-pip.py"
    if (Test-Path $VSGetPip) {
        Remove-Item -Path $VSGetPip -Force
        Write-Host " [OK] 已清理 get-pip.py 脚本" -ForegroundColor Green
    }

    # 删除所有的 *.dist-info 和 *.egg-info 文件夹 (运行时不需要的 pip 元数据)
    Get-ChildItem -Path $ComponentsDist -Recurse -Directory -Filter "*.dist-info" | Remove-Item -Recurse -Force
    Get-ChildItem -Path $ComponentsDist -Recurse -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force
    Write-Host " [OK] 已清理所有冗余的 .dist-info 和 .egg-info 元数据目录" -ForegroundColor Green

    # 清理所有的 __pycache__ 缓存目录，进一步压缩包体积
    Get-ChildItem -Path $ComponentsDist -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Write-Host " [OK] 已清理所有的 __pycache__ 缓存目录" -ForegroundColor Green
}

# 6. UPX 后压缩（Nuitka 4.x 不再内置 UPX 支持，改为构建后手动压缩）
if ($UseUpx) {
    Write-Host "`n正在使用 UPX 压缩二进制文件..." -ForegroundColor Yellow
    $upxCount = 0
    Get-ChildItem -Path $DistPath -Recurse -Include "*.exe", "*.dll" | Where-Object {
        # 跳过 components 目录下的所有二进制文件，防止损坏 VapourSynth 插件与 ffmpeg
        $_.FullName -notlike "*\components\*" -and $_.Name -ne "ffmpeg.exe"
    } | ForEach-Object {
        & upx --best "$($_.FullName)" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $upxCount++
        }
    }
    Write-Host " [OK] UPX 压缩完成，共处理 $upxCount 个文件" -ForegroundColor Green
}

# 7. 检测并执行 NSIS 安装包制作
$MakeNsisPath = ""
if (Get-Command "makensis" -ErrorAction SilentlyContinue) {
    $MakeNsisPath = "makensis"
} elseif (Test-Path "C:\Program Files (x86)\NSIS\makensis.exe") {
    $MakeNsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
} elseif (Test-Path "C:\Program Files\NSIS\makensis.exe") {
    $MakeNsisPath = "C:\Program Files\NSIS\makensis.exe"
}

if ($MakeNsisPath -ne "") {
    Write-Host "`n检测到 NSIS，正在制作安装包..." -ForegroundColor Yellow
    & $MakeNsisPath /DAPP_DIST_DIR="$DistPath" installer.nsi
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK] 安装包已成功制作并保存至 outputs 目录！" -ForegroundColor Green
    } else {
        Write-Host " [!] 制作安装包时出错！" -ForegroundColor Red
    }
} else {
    Write-Host "`n提示：未检测到 NSIS (makensis.exe)。" -ForegroundColor Yellow
    Write-Host "如果你想自动制作 exe 安装包，请前往 https://nsis.sourceforge.io 下载并安装 NSIS，然后将其所在目录加入到系统环境变量 PATH 中。" -ForegroundColor Yellow
}

Write-Host "`n打包与资源同步完成！生成的程序位于: $DistPath" -ForegroundColor Cyan