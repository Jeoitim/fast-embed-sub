import sys
import os
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import QCoreApplication, QSettings, Qt

from localization import TranslationManager

def main():
    app = QApplication(sys.argv)
    settings = QSettings("Jeoitim", "FastEmbedSub")
    translation_manager = TranslationManager(app, settings.value("language", "zh"))
    
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
        splash.showMessage(
            QCoreApplication.translate("Startup", "Starting Fast Embed Sub..."),
            Qt.AlignBottom | Qt.AlignCenter,
            QColor("#FFFFFF"),
        )
        app.processEvents()

    # 2. 延迟加载依赖库与重型 UI 模块
    if splash:
        splash.showMessage(
            QCoreApplication.translate("Startup", "Loading core components..."),
            Qt.AlignBottom | Qt.AlignCenter,
            QColor("#FFFFFF"),
        )
        app.processEvents()

    try:
        from qfluentwidgets import setTheme, Theme
    except ImportError:
        if splash:
            splash.close()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            QCoreApplication.translate("Startup", "Missing Dependency"),
            QCoreApplication.translate(
                "Startup",
                "PySide6-Fluent-Widgets was not found. Run\n"
                "`pip install PySide6-Fluent-Widgets` and try again.",
            ),
        )
        sys.exit(1)
        
    saved_theme = str(settings.value("theme", "dark")).lower()
    setTheme(Theme.LIGHT if saved_theme == "light" else Theme.DARK)
    
    if splash:
        splash.showMessage(
            QCoreApplication.translate("Startup", "Initializing interface..."),
            Qt.AlignBottom | Qt.AlignCenter,
            QColor("#FFFFFF"),
        )
        app.processEvents()
        
    from gui import MainUI
    window = MainUI(translation_manager)
    window.show()
    
    if splash:
        splash.finish(window)
        
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

