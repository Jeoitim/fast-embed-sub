import sys
import os
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    
    # 1. 立即显示启动闪屏，提供即时视觉反馈
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.png")
    splash = None
    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        # 将图标缩放到适合闪屏的尺寸
        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        splash = QSplashScreen(scaled_pixmap)
        splash.show()
        splash.showMessage("正在启动 FastEmbedSub...", Qt.AlignBottom | Qt.AlignCenter, QColor("#FFFFFF"))
        app.processEvents()

    # 2. 延迟加载依赖库与重型 UI 模块
    if splash:
        splash.showMessage("正在加载核心组件...", Qt.AlignBottom | Qt.AlignCenter, QColor("#FFFFFF"))
        app.processEvents()

    try:
        from qfluentwidgets import setTheme, Theme
    except ImportError:
        if splash:
            splash.close()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "缺少依赖",
                             "未检测到 PySide6-Fluent-Widgets 库。请运行\n"
                             "`pip install PySide6-Fluent-Widgets` 后重试。")
        sys.exit(1)
        
    setTheme(Theme.DARK)
    
    if splash:
        splash.showMessage("正在初始化界面...", Qt.AlignBottom | Qt.AlignCenter, QColor("#FFFFFF"))
        app.processEvents()
        
    from gui import MainUI
    window = MainUI()
    window.show()
    
    if splash:
        splash.finish(window)
        
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

