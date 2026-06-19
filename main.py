import sys
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    try:
        from qfluentwidgets import setTheme, Theme
    except ImportError:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "缺少依赖",
                             "未检测到 PySide6-Fluent-Widgets 库。请运行\n"
                             "`pip install PySide6-Fluent-Widgets` 后重试。")
        sys.exit(1)
    setTheme(Theme.DARK)
    from gui import MainUI
    window = MainUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
