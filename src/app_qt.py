import sys
from pathlib import Path

# Добавляем папку src в путь, чтобы импорты ядра работали
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui_qt.main_window import MainWindowQt

def main():
    # Включаем поддержку высоких DPI (чтобы интерфейс был чётким на 4K)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    # Применяем тёмную тему Fusion (базовая, но аккуратная)
    app.setStyle("Fusion")
    
    # Создаём и показываем главное окно
    window = MainWindowQt()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()