import sys
from pathlib import Path

# Добавляем папку src в системный путь, чтобы импорты работали корректно
sys.path.append(str(Path(__file__).parent))

from ui.main_window import MainWindow

def main():
    # Создаем экземпляр главного окна и запускаем цикл обработки событий
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()