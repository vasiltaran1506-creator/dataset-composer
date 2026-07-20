import sys
from pathlib import Path

# Добавляем папку src в системный путь, чтобы импорты работали корректно
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui_qt.main_window import MainWindowQt


def main():
    # Включаем поддержку высоких DPI (чёткость на 4K-мониторах)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Базовая тема (тёмная палитра применяется в MainWindowQt)

    window = MainWindowQt()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()