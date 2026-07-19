from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QPlainTextEdit,
                               QCheckBox, QComboBox, QFileDialog, QMessageBox,
                               QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor, QIntValidator
from pathlib import Path
import gc

from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter
from coverage_tracker import CoverageTracker


class GenerationWorker(QThread):
    """Worker-поток для генерации датасета"""
    log_message = Signal(str)
    generation_complete = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, project_root: Path, profiles_directory: Path,
                 profile_name: str, num_scenes: int, output_dir: str,
                 balance_folder: str, balance_options: dict, force_closure: bool):
        super().__init__()
        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.profile_name = profile_name
        self.num_scenes = num_scenes
        self.output_dir = output_dir
        self.balance_folder = balance_folder
        self.balance_options = balance_options
        self.force_closure = force_closure

    def run(self):
        """Основная логика генерации"""
        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            self.log_message.emit(f"\n{'=' * 60}\n")
            self.log_message.emit(f"🚀 Starting generation: {self.num_scenes} scenes for '{self.profile_name}'\n")
            self.log_message.emit("📦 Initializing engine...\n")

            # Инициализация движка
            loader = ConfigLoader(project_root=str(self.project_root))
            library = PromptLibrary(library_path=str(self.project_root / "prompt-library"))
            rules = loader.load_scene_rules()
            loader.load_location_types()
            library.load_library()

            # Загрузка профиля
            profile_path = self.profiles_directory / f"{self.profile_name}.yaml"
            if not profile_path.exists():
                profile_path = self.project_root / "character-profile.yaml"
            if not profile_path.exists():
                raise FileNotFoundError(f"Profile not found: {self.profile_name}")

            import yaml
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = yaml.safe_load(f)

            builder = SceneBuilder(library=library, scene_rules=rules,
                                   character_profile=profile, location_types=loader.location_types)

            # Балансировка на основе папки
            if self.balance_folder:
                self.log_message.emit(f"⚖️ Analyzing balance folder: {self.balance_folder}\n")
                available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
                available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
                available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
                available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]

                tracker = CoverageTracker(
                    available_locations=available_locs, available_actions=available_acts,
                    available_weathers=available_weaths, available_cameras=available_cams
                )
                matrix = tracker.scan_folder(self.balance_folder)
                weights = tracker.calculate_generation_weights(matrix)
                filtered_weights = {}

                if self.balance_options.get('locations'): filtered_weights['location'] = weights.get('location')
                if self.balance_options.get('actions'): filtered_weights['action'] = weights.get('action')
                if self.balance_options.get('weather'): filtered_weights['weather'] = weights.get('weather')
                if self.balance_options.get('cameras'): filtered_weights['camera'] = weights.get('camera')

                builder.generation_weights = filtered_weights
                self.log_message.emit("✅ Weights calculated.\n")

            if not self.output_dir:
                raise ValueError("Output directory is not specified")

            self.log_message.emit(f"🎬 Generating {self.num_scenes} scenes...\n")
            if self.force_closure:
                self.log_message.emit("⚡ AGGRESSIVE Mode\n")
            else:
                self.log_message.emit("🌿 NATURAL Mode\n")

            exporter = Exporter(builder, self.profile_name,
                                generation_weights=builder.generation_weights,
                                log_callback=self.log_message.emit, verbose=False,
                                force_deficit_closure=self.force_closure)
            stats = exporter.export_dataset(num_scenes=self.num_scenes,
                                            output_dir=self.output_dir,
                                            create_placeholders=False)

            self.log_message.emit(f"\n✅ Generation complete! Total: {stats['total_scenes']}\n")
            self.log_message.emit(f"📂 Saved to: {self.output_dir}\n")
            self.generation_complete.emit(stats)

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.error_occurred.emit(str(e))
            self.log_message.emit(f"\n❌ ERROR: {e}\n")
            self.log_message.emit(error_msg)
        finally:
            if gc_was_enabled:
                gc.enable()
                gc.collect()


class GenerateTab(QWidget):
    """Вкладка генерации датасета (Qt версия)"""
    
    # Сигнал для MainWindow: настройки изменились
    settings_changed = Signal(str, str, object)  # section, key, value

    def __init__(
        self,
        project_root: Path,
        profiles_directory: Path,
        output_directory: Path,
        settings_manager,
        log_callback,
        parent=None
    ):
        super().__init__(parent)

        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.output_directory = output_directory
        self.settings_manager = settings_manager
        self._log = log_callback
        self.generation_worker = None

        self._setup_ui()
        self._load_settings_to_ui()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Generate"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === ЛЕВАЯ ПАНЕЛЬ: Настройки генерации ===
        left_widget = QWidget()
        left_widget.setMaximumWidth(450)
        left_widget.setMinimumWidth(380)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # --- Generation Settings ---
        gen_group = QGroupBox("⚙️ Generation Settings")
        gen_layout = QGridLayout(gen_group)
        gen_layout.setSpacing(8)

        gen_layout.addWidget(QLabel("👤 Character Profile:"), 0, 0)
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self._get_available_profiles())
        gen_layout.addWidget(self.profile_combo, 0, 1)

        gen_layout.addWidget(QLabel("🎬 Number of Scenes:"), 1, 0)
        self.scenes_entry = QLineEdit()
        self.scenes_entry.setPlaceholderText("100")
        self.scenes_entry.setValidator(QIntValidator(1, 100000))
        self.scenes_entry.editingFinished.connect(self._save_num_scenes)
        gen_layout.addWidget(self.scenes_entry, 1, 1)

        gen_layout.addWidget(QLabel("📂 Save to folder:"), 2, 0, 1, 2)
        output_frame = QWidget()
        output_layout = QHBoxLayout(output_frame)
        output_layout.setContentsMargins(0, 0, 0, 0)
        self.output_path_entry = QLineEdit()
        self.output_path_entry.setPlaceholderText("Select output folder...")
        output_layout.addWidget(self.output_path_entry)
        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self._browse_output_folder)
        output_layout.addWidget(browse_output_btn)
        gen_layout.addWidget(output_frame, 3, 0, 1, 2)

        left_layout.addWidget(gen_group)

        # --- Coverage Engine ---
        cov_group = QGroupBox("⚖️ Coverage Engine")
        cov_layout = QVBoxLayout(cov_group)
        cov_layout.setSpacing(5)

        cov_layout.addWidget(QLabel("Balance from folder:"))
        balance_frame = QWidget()
        balance_layout = QHBoxLayout(balance_frame)
        balance_layout.setContentsMargins(0, 0, 0, 0)
        self.balance_path_entry = QLineEdit()
        self.balance_path_entry.setPlaceholderText("Optional...")
        balance_layout.addWidget(self.balance_path_entry)
        browse_balance_btn = QPushButton("Browse")
        browse_balance_btn.clicked.connect(self._browse_balance_folder)
        balance_layout.addWidget(browse_balance_btn)
        cov_layout.addWidget(balance_frame)

        # Чекбоксы
        self.balance_locs_check = QCheckBox("Balance Locations")
        self.balance_locs_check.stateChanged.connect(
            lambda: self._save_balance_var('balance_locations', self.balance_locs_check))
        cov_layout.addWidget(self.balance_locs_check)

        self.balance_acts_check = QCheckBox("Balance Actions")
        self.balance_acts_check.stateChanged.connect(
            lambda: self._save_balance_var('balance_actions', self.balance_acts_check))
        cov_layout.addWidget(self.balance_acts_check)

        self.balance_weath_check = QCheckBox("Balance Weather")
        self.balance_weath_check.stateChanged.connect(
            lambda: self._save_balance_var('balance_weather', self.balance_weath_check))
        cov_layout.addWidget(self.balance_weath_check)

        self.balance_cams_check = QCheckBox("Balance Cameras")
        self.balance_cams_check.stateChanged.connect(
            lambda: self._save_balance_var('balance_cameras', self.balance_cams_check))
        cov_layout.addWidget(self.balance_cams_check)

        # Force Deficit Closure
        closure_frame = QWidget()
        closure_layout = QHBoxLayout(closure_frame)
        closure_layout.setContentsMargins(0, 5, 0, 0)
        self.force_closure_check = QCheckBox("⚡ Force Deficit Closure")
        self.force_closure_check.stateChanged.connect(self._save_force_closure)
        closure_layout.addWidget(self.force_closure_check)
        help_btn = QPushButton("?")
        help_btn.setFixedSize(25, 25)
        help_btn.clicked.connect(self._show_force_closure_help)
        closure_layout.addWidget(help_btn)
        closure_layout.addStretch()
        cov_layout.addWidget(closure_frame)

        left_layout.addWidget(cov_group)

        # --- Кнопки запуска ---
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        roll_dice_btn = QPushButton("🎲 Roll Dice")
        roll_dice_btn.clicked.connect(self._roll_dice)
        buttons_layout.addWidget(roll_dice_btn)
        
        generate_btn = QPushButton("🚀 Generate Batch")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        generate_btn.clicked.connect(self._start_generation)
        buttons_layout.addWidget(generate_btn)
        
        left_layout.addWidget(buttons_frame)
        left_layout.addStretch()

        # === ПРАВАЯ ПАНЕЛЬ: Лог генерации ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        log_header = QWidget()
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(0, 0, 0, 0)
        log_header_layout.addWidget(QLabel("📝 Generation Log"))
        log_header_layout.addStretch()
        copy_log_btn = QPushButton("📋 Copy All")
        copy_log_btn.clicked.connect(self._copy_log_to_clipboard)
        log_header_layout.addWidget(copy_log_btn)
        right_layout.addWidget(log_header)

        self.log_textbox = QPlainTextEdit()
        self.log_textbox.setReadOnly(True)
        self.log_textbox.setFont(QFont("Consolas", 10))
        self.log_textbox.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #444;
            }
        """)
        right_layout.addWidget(self.log_textbox)

        # Добавляем панели в главный layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)  # stretch=1 - правая панель растягивается

        # Начальный лог
        self._append_log("✅ Dataset Composer готов к работе.\n")
        self._append_log(f"📂 Output directory: {self.output_directory}\n")

    def _load_settings_to_ui(self):
        """Загружает текущие настройки из SettingsManager в UI"""
        num_scenes = self.settings_manager.get('generation_defaults', 'num_scenes')
        self.scenes_entry.setText(str(num_scenes))

        saved_output = self.settings_manager.get('directories', 'output_directory')
        self.output_path_entry.setText(saved_output if saved_output else str(self.output_directory))

        self.force_closure_check.setChecked(
            self.settings_manager.get('generation_defaults', 'force_deficit_closure')
        )
        self.balance_locs_check.setChecked(
            self.settings_manager.get('generation_defaults', 'balance_locations')
        )
        self.balance_acts_check.setChecked(
            self.settings_manager.get('generation_defaults', 'balance_actions')
        )
        self.balance_weath_check.setChecked(
            self.settings_manager.get('generation_defaults', 'balance_weather')
        )
        self.balance_cams_check.setChecked(
            self.settings_manager.get('generation_defaults', 'balance_cameras')
        )

    def _get_available_profiles(self) -> list[str]:
        """Сканирует папку profiles"""
        profiles = []
        if self.profiles_directory.exists():
            for file in self.profiles_directory.glob("*.yaml"):
                profiles.append(file.stem)
        if not profiles:
            root_yaml = self.project_root / "character-profile.yaml"
            if root_yaml.exists():
                profiles.append("luna")
        return profiles if profiles else ["No profiles found"]

    # ═══════════════════════════════════════════════
    # ОБРАБОТЧИКИ UI
    # ═══════════════════════════════════════════════
    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_path_entry.setText(folder)
            self.settings_manager.set('directories', 'output_directory', folder)
            self.settings_changed.emit('directories', 'output_directory', folder)
            self._append_log(f"📂 Output directory set to: {folder}\n")

    def _browse_balance_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select balance folder")
        if folder:
            self.balance_path_entry.setText(folder)

    def _save_num_scenes(self):
        try:
            value = int(self.scenes_entry.text())
            if value > 0:
                self.settings_manager.set('generation_defaults', 'num_scenes', value)
                self.settings_changed.emit('generation_defaults', 'num_scenes', value)
            else:
                raise ValueError
        except ValueError:
            valid_value = self.settings_manager.get('generation_defaults', 'num_scenes')
            self.scenes_entry.setText(str(valid_value))
            QMessageBox.warning(self, "Warning", "Please enter a valid positive number")

    def _save_force_closure(self):
        value = self.force_closure_check.isChecked()
        self.settings_manager.set('generation_defaults', 'force_deficit_closure', value)
        self.settings_changed.emit('generation_defaults', 'force_deficit_closure', value)

    def _save_balance_var(self, key: str, checkbox: QCheckBox):
        value = checkbox.isChecked()
        self.settings_manager.set('generation_defaults', key, value)
        self.settings_changed.emit('generation_defaults', key, value)

    def _show_force_closure_help(self):
        QMessageBox.information(
            self,
            "⚡ Force Deficit Closure",
            "Этот режим меняет порядок генерации:\n\n"
            "🌿 Natural Mode: сначала локация, потом действие.\n\n"
            "⚡ Aggressive Mode: сначала дефицитное действие, потом локация."
        )

    def _roll_dice(self):
        """Генерирует один случайный промпт для отладки"""
        self._append_log("\n🎲 Rolling dice...\n")
        try:
            import random
            profile_name = self.profile_combo.currentText()
            
            loader = ConfigLoader(project_root=str(self.project_root))
            library = PromptLibrary(library_path=str(self.project_root / "prompt-library"))
            rules = loader.load_scene_rules()
            loader.load_location_types()
            library.load_library()

            profile_path = self.profiles_directory / f"{profile_name}.yaml"
            if not profile_path.exists():
                profile_path = self.project_root / "character-profile.yaml"
            if not profile_path.exists():
                raise FileNotFoundError(f"Profile not found: {profile_name}")

            import yaml
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = yaml.safe_load(f)

            builder = SceneBuilder(library=library, scene_rules=rules,
                                   character_profile=profile, location_types=loader.location_types)
            available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
            loc = random.choice(available_locs)
            scene = builder.build_scene(loc)
            fixed_traits = profile.get('fixed_traits', [])
            prompt = scene.to_prompt(fixed_traits)
            self._append_log(f"📍 Location: {loc}\n")
            self._append_log(f"📝 Prompt: {prompt}\n")
        except Exception as e:
            self._append_log(f"❌ Error: {e}\n")
            QMessageBox.critical(self, "Error", str(e))

    def _start_generation(self):
        """Запускает батчевую генерацию в отдельном потоке"""
        try:
            num_scenes = int(self.scenes_entry.text())
            if num_scenes <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "Error", "Please enter a valid number of scenes")
            return

        balance_options = {
            'locations': self.balance_locs_check.isChecked(),
            'actions': self.balance_acts_check.isChecked(),
            'weather': self.balance_weath_check.isChecked(),
            'cameras': self.balance_cams_check.isChecked(),
        }

        self.generation_worker = GenerationWorker(
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            profile_name=self.profile_combo.currentText(),
            num_scenes=num_scenes,
            output_dir=self.output_path_entry.text().strip(),
            balance_folder=self.balance_path_entry.text().strip(),
            balance_options=balance_options,
            force_closure=self.force_closure_check.isChecked()
        )
        self.generation_worker.log_message.connect(self._append_log)
        self.generation_worker.generation_complete.connect(self._on_generation_complete)
        self.generation_worker.error_occurred.connect(self._on_generation_error)
        self.generation_worker.start()

    def _append_log(self, message: str):
        """Добавляет сообщение в лог (потокобезопасно)"""
        self.log_textbox.appendPlainText(message)
        cursor = self.log_textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_textbox.setTextCursor(cursor)

    def _on_generation_complete(self, stats: dict):
        QMessageBox.information(
            self, "Success",
            f"Generated {stats['total_scenes']} scenes!\nSaved to:\n{self.output_path_entry.text()}"
        )

    def _on_generation_error(self, error_msg: str):
        QMessageBox.critical(self, "Generation Error", error_msg)

    def _copy_log_to_clipboard(self):
        content = self.log_textbox.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Info", "Log is empty")
            return
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(content)
        QMessageBox.information(self, "Copied", "✅ Log copied to clipboard!")

    # ═══════════════════════════════════════════════
    # PUBLIC API (для синхронизации из MainWindow)
    # ═══════════════════════════════════════════════
    def set_output_directory(self, path):
        """Обновляет поле Output Directory"""
        self.output_path_entry.setText(str(path))

    def set_num_scenes(self, value):
        """Обновляет поле Number of Scenes"""
        self.scenes_entry.setText(str(value))

    def set_balance_var(self, key: str, value):
        """Обновляет состояние чекбокса балансировки"""
        var_map = {
            'balance_locations': self.balance_locs_check,
            'balance_actions': self.balance_acts_check,
            'balance_weather': self.balance_weath_check,
            'balance_cameras': self.balance_cams_check,
            'force_deficit_closure': self.force_closure_check,
        }
        checkbox = var_map.get(key)
        if checkbox:
            checkbox.setChecked(value)

    def set_balance_folder(self, path):
        """Устанавливает путь к папке балансировки (используется Auto-Fix из Analyzer)"""
        self.balance_path_entry.setText(str(path))
        # Включаем все чекбоксы балансировки
        self.balance_locs_check.setChecked(True)
        self.balance_acts_check.setChecked(True)
        self.balance_weath_check.setChecked(True)
        self.balance_cams_check.setChecked(True)