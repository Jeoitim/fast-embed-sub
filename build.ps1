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

# 3. 执行 Nuitka 打包命令
# --standalone: 独立运行库
# --show-memory --show-progress: 显示过程
# --plugin-enable=pyside6: 自动处理 PySide6 依赖
# --include-data-dir: 包含你的资源文件夹
# --output-dir: 指定输出到 outputs
# --windows-icon-from-ico: 设置程序图标

nuitka "--standalone" `
       "--msvc=latest" `
       "--show-memory" `
       "--show-progress" `
       "--jobs=$env:NUMBER_OF_PROCESSORS" `
       "--plugin-enable=pyside6" `
       "--windows-disable-console" `
       "--include-data-dir=assets=assets" `
       "--include-data-dir=components=components" `
       "--output-dir=$OutputDir" `
       "--output-filename=FastEmbedSub" `
       "--windows-icon-from-ico=assets/icon.jpg" `
       "--nofollow-import-to=scipy" `
       "--nofollow-import-to=numpy" `
       "--nofollow-import-to=pyqt5" `
       "--follow-imports" `
       "main.py"

Write-Host "打包完成！生成的程序位于 $OutputDir/main.dist/" -ForegroundColor Cyan

# 4. 强制搬运资源文件夹 (保底方案)
$DistPath = "$OutputDir/main.dist"
# 如果你指定了 --output-filename=FastEmbedSub，路径可能是 "$OutputDir/FastEmbedSub.dist"
if (-not (Test-Path $DistPath)) {
    $DistPath = Get-ChildItem -Path "$OutputDir/*.dist" | Select-Object -ExpandProperty FullName -First 1
}

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

Write-Host "`n打包与资源同步完成！生成的程序位于: $DistPath" -ForegroundColor Cyan