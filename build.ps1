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