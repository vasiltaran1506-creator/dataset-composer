import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui_qt.main_window import MainWindowQt
from ui_qt.icon_manager import IconManager

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 1. Инициализация иконок
    IconManager.initialize()
    
    # 2. Глобальный шрифт с fallback на иконки
    if IconManager._font_family:
        global_font = QFont(f"Segoe UI, {IconManager._font_family}")
        global_font.setPointSize(10)
        app.setFont(global_font)
        
    window = MainWindowQt()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()