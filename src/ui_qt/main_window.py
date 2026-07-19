import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, 
                               QVBoxLayout, QLabel, QStatusBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor


class MainWindowQt(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- Настройки окна ---
        self.setWindowTitle("Dataset Composer v1.1 - Qt Edition")
        self.resize(1300, 800)
        self.setMinimumSize(1000, 600)
        
        # Шрифт
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        # --- Пути к директориям проекта ---
        if hasattr(sys, '_MEIPASS'):
            self.project_root = Path(sys.executable).parent
        else:
            self.project_root = Path(__file__).parent.parent.parent
        
        # --- Менеджер настроек ---
        from settings_manager import SettingsManager
        self.settings_manager = SettingsManager(self.project_root / "settings.json")
        
        # --- Пути к папкам ---
        saved_output = self.settings_manager.get('directories', 'output_directory')
        self.output_directory = Path(saved_output) if saved_output else self.project_root / "output"
        
        saved_profiles = self.settings_manager.get('directories', 'profiles_path')
        self.profiles_directory = Path(saved_profiles) if saved_profiles else self.project_root / "character-profiles"
        self.profiles_directory.mkdir(exist_ok=True)
        
        # --- Центральный виджет и Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- QTabWidget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Добавляем вкладки

        # ProfilesTab — реальная вкладка
        from ui_qt.profiles_tab import ProfilesTab
        self.profiles_tab_widget = ProfilesTab(
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            settings_manager=self.settings_manager,
            log_callback=self._log
        )
        self.tab_widget.addTab(self.profiles_tab_widget, "Profiles")

        # LibraryTab — реальная вкладка
        from ui_qt.library_tab import LibraryTab
        self.library_tab_widget = LibraryTab(
            project_root=self.project_root,
            log_callback=self._log
        )
        self.tab_widget.addTab(self.library_tab_widget, "Library")

        # GenerateTab — реальная вкладка
        from ui_qt.generate_tab import GenerateTab
        self.generate_tab_widget = GenerateTab(
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            output_directory=self.output_directory,
            settings_manager=self.settings_manager,
            log_callback=self._log
        )
        # Подключаем сигнал settings_changed к обработчику
        self.generate_tab_widget.settings_changed.connect(self._on_generate_settings_changed)
        self.tab_widget.addTab(self.generate_tab_widget, "Generate")

        # AnalyzerTab — реальная вкладка (вместо заглушки)
        from ui_qt.analyzer_tab import AnalyzerTab
        self.analyzer_tab_widget = AnalyzerTab(
            project_root=self.project_root,
            output_directory=self.output_directory,
            log_callback=self._log
        )
        # Подключаем сигнал Auto-Fix к обработчику
        self.analyzer_tab_widget.auto_fix_deficit.connect(self._on_auto_fix_deficit)
        self.tab_widget.addTab(self.analyzer_tab_widget, "Analyzer")
        
        # SettingsTab — реальная вкладка
        from ui_qt.settings_tab import SettingsTab
        self.settings_tab_widget = SettingsTab(
            settings_manager=self.settings_manager,
            project_root=self.project_root,
            output_directory=self.output_directory,
            profiles_directory=self.profiles_directory,
            log_callback=self._log,
            on_settings_changed=self._on_settings_changed
        )
        self.tab_widget.addTab(self.settings_tab_widget, "Settings")
        
        layout.addWidget(self.tab_widget)
        
        # --- Статус-бар ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✅ Core Engine initialized. UI is migrating to Qt...")
        
        # --- Центрирование окна ---
        self.center_on_screen()
        
        # --- Применяем кастомную тёмную палитру ---
        self.apply_dark_theme()

    def center_on_screen(self):
        """Центрирует окно на экране монитора"""
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def apply_dark_theme(self):
        """Применяет тёмную тему"""
        palette = QPalette()
        
        dark_bg = QColor("#2b2b2b")
        widget_bg = QColor("#333333")
        text_color = QColor("#e0e0e0")
        accent_color = QColor("#3b82f6")
        
        palette.setColor(QPalette.Window, dark_bg)
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, widget_bg)
        palette.setColor(QPalette.AlternateBase, dark_bg)
        palette.setColor(QPalette.ToolTipBase, text_color)
        palette.setColor(QPalette.ToolTipText, text_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.Button, widget_bg)
        palette.setColor(QPalette.ButtonText, text_color)
        palette.setColor(QPalette.BrightText, QColor("#ff0000"))
        palette.setColor(QPalette.Link, accent_color)
        palette.setColor(QPalette.Highlight, accent_color)
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; background: #2b2b2b; }
            QTabBar::tab { background: #333; color: #ccc; padding: 8px 20px; border: 1px solid #444; }
            QTabBar::tab:selected { background: #3b82f6; color: white; }
            QTabBar::tab:hover { background: #444; }
            QScrollBar:vertical { background: #2b2b2b; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: #555; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

    def _log(self, message):
        """Глобальный лог"""
        print(message, end='')

    def _on_settings_changed(self, section: str, key: str, value):
        """Callback от SettingsTab"""
        if section == 'directories' and key == 'output_directory':
            self.output_directory = Path(value) if not isinstance(value, Path) else value
        elif section == 'generation_defaults':
            pass

    def _on_generate_settings_changed(self, section: str, key: str, value):
        """Обработчик сигнала settings_changed от GenerateTab"""
        if section == 'directories' and key == 'output_directory':
            self.output_directory = Path(value) if not isinstance(value, Path) else value
            # Синхронизируем с Settings и Analyzer
            if hasattr(self, 'settings_tab_widget'):
                self.settings_tab_widget.set_output_directory(value)
            if hasattr(self, 'analyzer_tab_widget'):
                self.analyzer_tab_widget.set_output_directory(value)
        elif section == 'generation_defaults':
            # Синхронизируем с Settings
            if hasattr(self, 'settings_tab_widget'):
                if key == 'num_scenes':
                    self.settings_tab_widget.set_num_scenes(value)
                else:
                    self.settings_tab_widget.set_balance_var(key, value)

    def _on_auto_fix_deficit(self, folder: str):
        """Обработчик сигнала Auto-Fix от Analyzer"""
        # Переключаемся на вкладку Generate (индекс 2)
        self.tab_widget.setCurrentIndex(2)

        # Передаём папку в Generate и включаем все чекбоксы балансировки
        if hasattr(self, 'generate_tab_widget'):
            self.generate_tab_widget.set_balance_folder(folder)
            QMessageBox.information(
                self, "Auto-Fix Ready",
                f"✅ Balance from: {folder}\nНажмите '🚀 Generate Batch'!"
            )

        self._log(f"⚡ Auto-Fix: папка {folder} передана в Generate\n")