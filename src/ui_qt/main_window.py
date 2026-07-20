import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget,
                               QVBoxLayout, QLabel, QStatusBar, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui_qt.icon_manager import IconManager


class MainWindowQt(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Настройки окна ---
        self.setWindowTitle("Dataset Composer v1.1")
        self.resize(1300, 800)
        self.setMinimumSize(1000, 600)

        # Шрифт (QSS переопределит для большинства виджетов)
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
        layout.setContentsMargins(0, 0, 0, 0)

        # --- QTabWidget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # --- Profiles ---
        from ui_qt.profiles_tab import ProfilesTab
        self.profiles_tab_widget = ProfilesTab(
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            settings_manager=self.settings_manager,
            log_callback=self._log
        )
        self.tab_widget.addTab(self.profiles_tab_widget, f"{IconManager.get('user')} Profiles")

        # --- Library ---
        from ui_qt.library_tab import LibraryTab
        self.library_tab_widget = LibraryTab(
            project_root=self.project_root,
            log_callback=self._log
        )
        self.tab_widget.addTab(self.library_tab_widget, f"{IconManager.get('database')} Library")

        # --- Generate ---
        from ui_qt.generate_tab import GenerateTab
        self.generate_tab_widget = GenerateTab(
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            output_directory=self.output_directory,
            settings_manager=self.settings_manager,
            log_callback=self._log
        )
        self.generate_tab_widget.settings_changed.connect(self._on_generate_settings_changed)
        self.tab_widget.addTab(self.generate_tab_widget, f"{IconManager.get('rocket')} Generate")

        # --- Analyzer ---
        from ui_qt.analyzer_tab import AnalyzerTab
        self.analyzer_tab_widget = AnalyzerTab(
            project_root=self.project_root,
            output_directory=self.output_directory,
            log_callback=self._log
        )
        self.analyzer_tab_widget.auto_fix_deficit.connect(self._on_auto_fix_deficit)
        self.tab_widget.addTab(self.analyzer_tab_widget, f"{IconManager.get('chart')} Analyzer")

        # --- Settings ---
        from ui_qt.settings_tab import SettingsTab
        self.settings_tab_widget = SettingsTab(
            settings_manager=self.settings_manager,
            project_root=self.project_root,
            output_directory=self.output_directory,
            profiles_directory=self.profiles_directory,
            log_callback=self._log,
            on_settings_change=self._on_settings_changed
        )
        self.tab_widget.addTab(self.settings_tab_widget, f"{IconManager.get('cog')} Settings")

        layout.addWidget(self.tab_widget)

        # --- Статус-бар ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Core Engine initialized. Ready.")

        # --- Центрирование + тема ---
        self.center_on_screen()
        self.apply_theme()

    def center_on_screen(self):
        """Центрирует окно на экране"""
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def apply_theme(self):
        """Загружает глобальный QSS из файла theme.qss (VS Code Dark)."""
        qss_path = Path(__file__).parent / "theme.qss"
        if qss_path.exists():
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print(f"Theme load error: {e}")
        else:
            print(f"Theme file not found: {qss_path}")

    def _log(self, message):
        """Глобальный лог (в консоль)."""
        print(message, end='')

    def _on_settings_changed(self, section: str, key: str, value):
        if section == 'directories' and key == 'output_directory':
            self.output_directory = Path(value) if not isinstance(value, Path) else value
        elif section == 'generation_defaults':
            pass

    def _on_generate_settings_changed(self, section: str, key: str, value):
        if section == 'directories' and key == 'output_directory':
            self.output_directory = Path(value) if not isinstance(value, Path) else value
            if hasattr(self, 'settings_tab_widget'):
                self.settings_tab_widget.set_output_directory(value)
            if hasattr(self, 'analyzer_tab_widget'):
                self.analyzer_tab_widget.set_output_directory(value)
        elif section == 'generation_defaults':
            if hasattr(self, 'settings_tab_widget'):
                if key == 'num_scenes':
                    self.settings_tab_widget.set_num_scenes(value)
                else:
                    self.settings_tab_widget.set_balance_var(key, value)

    def _on_auto_fix_deficit(self, folder: str):
        """Обработчик сигнала Auto-Fix от Analyzer."""
        self.tab_widget.setCurrentIndex(2)  # Generate
        if hasattr(self, 'generate_tab_widget'):
            self.generate_tab_widget.set_balance_folder(folder)
            QMessageBox.information(
                self, "Auto-Fix Ready",
                f"Balance from:\n{folder}\n\nPress 'Generate Batch' to continue."
            )
        self._log(f"Auto-Fix: folder {folder} passed to Generate\n")