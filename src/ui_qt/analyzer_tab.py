from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QPlainTextEdit,
                               QFileDialog, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from pathlib import Path
from coverage_tracker import CoverageTracker
from config_loader import ConfigLoader


class AnalysisWorker(QThread):
    """Worker-поток для анализа (предотвращает зависание UI)"""
    log_message = Signal(str)
    analysis_complete = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, folder: str, project_root: Path):
        super().__init__()
        self.folder = folder
        self.project_root = project_root

    def run(self):
        """Основная логика анализа (выполняется в фоне)"""
        try:
            self.log_message.emit(f"🔍 Сканирование: {self.folder}\n")
            self.log_message.emit("=" * 70 + "\n")

            loader = ConfigLoader(project_root=str(self.project_root))
            rules = loader.load_scene_rules()

            available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
            available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
            available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
            available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]

            # Собираем маппинг тегов одежды -> категории
            outfit_category_map = {}
            clothing_dir = self.project_root / "prompt-library" / "02_clothing"
            if clothing_dir.exists():
                for txt_file in clothing_dir.rglob("*.txt"):
                    category = txt_file.parent.name
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        tags = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    for tag in tags:
                        outfit_category_map[tag] = category

            tracker = CoverageTracker(
                available_locations=available_locs,
                available_actions=available_acts,
                available_weathers=available_weaths,
                available_cameras=available_cams,
                outfit_category_map=outfit_category_map
            )

            self.log_message.emit("📦 Запуск Coverage Tracker...\n")
            matrix = tracker.scan_folder(self.folder)

            if matrix["total_scenes"] == 0:
                self.log_message.emit("\n⚠️ Нет валидных промптов в папке.\n")
                return

            # Форматируем матрицу и отправляем в GUI
            self._format_matrix_for_gui(matrix)
            self.analysis_complete.emit(matrix)
            self.log_message.emit("\n✅ Анализ завершён!\n")

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.error_occurred.emit(str(e))
            self.log_message.emit(f"\n❌ Ошибка: {e}\n")
            self.log_message.emit(error_msg)

    def _format_matrix_for_gui(self, matrix: dict):
        """Форматирует матрицу покрытия для красивого вывода"""
        dimension_names = {
            "location": "📍 ЛОКАЦИИ",
            "action": "🎬 ДЕЙСТВИЯ",
            "weather": "🌦️ ПОГОДА",
            "camera": "📸 КАМЕРЫ",
            "outfit": "👗 ОДЕЖДА"
        }

        for dimension, display_name in dimension_names.items():
            counts = matrix["dimensions"].get(dimension, {})
            percentages = matrix["percentages"].get(dimension, {})

            if not counts:
                continue

            self.log_message.emit(f"\n{display_name}:\n" + "-" * 70 + "\n")

            for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                pct = percentages.get(category, 0)
                bar_length = int(pct / 2)
                bar = "█" * bar_length + "░" * (50 - bar_length)

                status = ""
                deficit_key = f"{dimension}.{category}"
                if deficit_key in matrix["status"].get("deficits", []):
                    status = " 🔻 ДЕФИЦИТ"
                elif deficit_key in matrix["status"].get("overflows", []):
                    status = " ⚠️ ПЕРЕИЗБЫТОК"

                self.log_message.emit(
                    f"   {category:25s}: {count:3d} ({pct:5.1f}%) [{bar}]{status}\n"
                )

        # Итоговая сводка
        self.log_message.emit("\n" + "=" * 70 + "\n📋 СВОДКА:\n")
        deficits = matrix["status"].get("deficits", [])
        overflows = matrix["status"].get("overflows", [])

        if deficits:
            self.log_message.emit(f"   🔻 Дефицит: {', '.join(deficits)}\n")
        if overflows:
            self.log_message.emit(f"   ⚠️ Переизбыток: {', '.join(overflows)}\n")
        if not deficits and not overflows:
            self.log_message.emit("   ✅ Баланс идеален!\n")

        self.log_message.emit("=" * 70 + "\n")


class AnalyzerTab(QWidget):
    """Вкладка анализа покрытия датасета (Qt версия)"""
    
    # Сигнал для MainWindow: передать папку в Generate
    auto_fix_deficit = Signal(str)

    def __init__(
        self,
        project_root: Path,
        output_directory: Path,
        log_callback,
        parent=None
    ):
        super().__init__(parent)

        self.project_root = project_root
        self.output_directory = output_directory
        self._log = log_callback
        self.analysis_worker = None
        self.last_matrix = None

        self._setup_ui()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Analyzer"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # === ВЕРХНЯЯ ПАНЕЛЬ: Выбор папки + кнопки ===
        top_group = QGroupBox("📂 Analysis Settings")
        top_layout = QGridLayout(top_group)
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("Analyze folder:"), 0, 0)
        self.analyze_path_entry = QLineEdit()
        self.analyze_path_entry.setPlaceholderText("Select folder with generated prompts...")
        top_layout.addWidget(self.analyze_path_entry, 0, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_analyze_folder)
        top_layout.addWidget(browse_btn, 0, 2)

        analyze_btn = QPushButton("🔍 Analyze")
        analyze_btn.clicked.connect(self._run_analysis)
        top_layout.addWidget(analyze_btn, 0, 3)

        auto_fix_btn = QPushButton("⚡ Auto-Fix")
        auto_fix_btn.clicked.connect(self._auto_fix_deficit)
        top_layout.addWidget(auto_fix_btn, 0, 4)

        main_layout.addWidget(top_group)

        # === НИЖНЯЯ ПАНЕЛЬ: Лог анализа ===
        log_group = QGroupBox("📊 Analysis Results")
        log_layout = QVBoxLayout(log_group)

        # Кнопки управления логом
        log_buttons = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self._copy_analyzer_to_clipboard)
        log_buttons.addWidget(copy_btn)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._clear_analyzer_log)
        log_buttons.addWidget(clear_btn)

        log_buttons.addStretch()
        log_layout.addLayout(log_buttons)

        # Текстовое поле для логов
        self.analyzer_textbox = QPlainTextEdit()
        self.analyzer_textbox.setReadOnly(True)
        self.analyzer_textbox.setFont(QFont("Consolas", 11))
        self.analyzer_textbox.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #444;
            }
        """)
        log_layout.addWidget(self.analyzer_textbox)

        main_layout.addWidget(log_group)

    # ═══════════════════════════════════════════════
    # ОБРАБОТЧИКИ UI
    # ═══════════════════════════════════════════════
    def _browse_analyze_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to analyze")
        if folder:
            self.analyze_path_entry.setText(folder)

    def _auto_fix_deficit(self):
        """Передаёт папку анализа во вкладку Generate через сигнал"""
        folder = self.analyze_path_entry.text().strip()
        if not folder:
            QMessageBox.warning(self, "Warning", "Сначала выберите папку для анализа")
            return

        # Отправляем сигнал в MainWindow
        self.auto_fix_deficit.emit(folder)

    def _clear_analyzer_log(self):
        self.analyzer_textbox.clear()

    def _copy_analyzer_to_clipboard(self):
        content = self.analyzer_textbox.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Info", "Лог пуст")
            return

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        QMessageBox.information(self, "Copied", "✅ Скопировано!")

    def _run_analysis(self):
        """Запускает анализ покрытия в отдельном потоке"""
        folder = self.analyze_path_entry.text().strip()
        if not folder:
            QMessageBox.warning(self, "Warning", "Выберите папку для анализа")
            return

        # Создаём worker-поток
        self.analysis_worker = AnalysisWorker(folder, self.project_root)
        self.analysis_worker.log_message.connect(self._append_log)
        self.analysis_worker.analysis_complete.connect(self._on_analysis_complete)
        self.analysis_worker.error_occurred.connect(self._on_analysis_error)
        self.analysis_worker.start()

    def _append_log(self, message: str):
        """Добавляет сообщение в лог (потокобезопасно через сигнал)"""
        self.analyzer_textbox.appendPlainText(message)
        # Автоскролл вниз
        cursor = self.analyzer_textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.analyzer_textbox.setTextCursor(cursor)

    def _on_analysis_complete(self, matrix: dict):
        """Обработчик завершения анализа"""
        self.last_matrix = matrix
        self._log(f"✅ Анализ завершён: {matrix['total_scenes']} сцен\n")

    def _on_analysis_error(self, error_msg: str):
        """Обработчик ошибки анализа"""
        QMessageBox.critical(self, "Analysis Error", error_msg)

    # ═══════════════════════════════════════════════
    # PUBLIC API (для синхронизации из MainWindow)
    # ═══════════════════════════════════════════════
    def set_output_directory(self, path):
        """Обновляет output_directory (вызывается из MainWindow)"""
        self.output_directory = path