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
    New-Content $GitignoreFile -Value "$IgnoreEntry"
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
    "--include-data-dir=assets=assets",
    "--include-data-dir=components=components",
    "--output-dir=$OutputDir",
    "--output-filename=FastEmbedSub",
    "--windows-icon-from-ico=assets/icon.png",
    "--lto=yes"
)

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
nuitka @NuitkaArgs


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
        Copy-Item -Path $Folder -Destination $DistPath -Recurse -Force
        Write-Host " [OK] 已同步目录: $Folder -> $Dest" -ForegroundColor Green
    } else {
        Write-Host " [!] 警告: 未找到源目录 $Folder" -ForegroundColor Red
    }
}

# 6. UPX 后压缩（Nuitka 4.x 不再内置 UPX 支持，改为构建后手动压缩）
if ($UseUpx) {
    Write-Host "`n正在使用 UPX 压缩二进制文件..." -ForegroundColor Yellow
    $upxCount = 0
    Get-ChildItem -Path $DistPath -Recurse -Include "*.exe", "*.dll" | Where-Object {
        # 跳过 ffmpeg.exe（通常已优化且体积很大，压缩耗时长且收益低）
        $_.Name -ne "ffmpeg.exe"
    } | ForEach-Object {
        & upx --best "$($_.FullName)" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $upxCount++
        }
    }
    Write-Host " [OK] UPX 压缩完成，共处理 $upxCount 个文件" -ForegroundColor Green
}

Write-Host "`n打包与资源同步完成！生成的程序位于: $DistPath" -ForegroundColor Cyan