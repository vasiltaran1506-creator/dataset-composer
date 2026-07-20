from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QPlainTextEdit,
                               QFileDialog, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from pathlib import Path
from ui_qt.icon_manager import IconManager
from coverage_tracker import CoverageTracker
from config_loader import ConfigLoader


class AnalysisWorker(QThread):
    log_message = Signal(str)
    analysis_complete = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, folder: str, project_root: Path):
        super().__init__()
        self.folder = folder
        self.project_root = project_root

    def run(self):
        try:
            self.log_message.emit(f"Scanning: {self.folder}\n")
            self.log_message.emit("=" * 70 + "\n")
            loader = ConfigLoader(project_root=str(self.project_root))
            rules = loader.load_scene_rules()
            available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
            available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
            available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
            available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]

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
            self.log_message.emit("Running Coverage Tracker...\n")
            matrix = tracker.scan_folder(self.folder)
            if matrix["total_scenes"] == 0:
                self.log_message.emit("\nNo valid prompts in folder.\n")
                return
            self._format_matrix_for_gui(matrix)
            self.analysis_complete.emit(matrix)
            self.log_message.emit("\nAnalysis complete.\n")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.error_occurred.emit(str(e))
            self.log_message.emit(f"\nError: {e}\n")
            self.log_message.emit(error_msg)

    def _format_matrix_for_gui(self, matrix: dict):
        dimension_names = {
            "location": "LOCATIONS",
            "action": "ACTIONS",
            "weather": "WEATHER",
            "camera": "CAMERAS",
            "outfit": "OUTFIT"
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
                    status = " [DEFICIT]"
                elif deficit_key in matrix["status"].get("overflows", []):
                    status = " [OVERFLOW]"
                self.log_message.emit(
                    f"   {category:25s}: {count:3d} ({pct:5.1f}%) [{bar}]{status}\n"
                )

        self.log_message.emit("\n" + "=" * 70 + "\nSUMMARY:\n")
        deficits = matrix["status"].get("deficits", [])
        overflows = matrix["status"].get("overflows", [])
        if deficits:
            self.log_message.emit(f"   Deficit: {', '.join(deficits)}\n")
        if overflows:
            self.log_message.emit(f"   Overflow: {', '.join(overflows)}\n")
        if not deficits and not overflows:
            self.log_message.emit("   Perfect balance.\n")
        self.log_message.emit("=" * 70 + "\n")


class AnalyzerTab(QWidget):
    auto_fix_deficit = Signal(str)

    def __init__(self, project_root: Path, output_directory: Path, log_callback, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self.output_directory = output_directory
        self._log = log_callback
        self.analysis_worker = None
        self.last_matrix = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- Верхняя панель ---
        top_group = QGroupBox("Analysis Settings")
        top_layout = QGridLayout(top_group)
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("Analyze folder:"), 0, 0)
        self.analyze_path_entry = QLineEdit()
        self.analyze_path_entry.setPlaceholderText("Select folder with generated prompts...")
        top_layout.addWidget(self.analyze_path_entry, 0, 1)

        browse_btn = QPushButton(f"{IconManager.get('folder')} Browse")
        browse_btn.clicked.connect(self._browse_analyze_folder)
        top_layout.addWidget(browse_btn, 0, 2)

        analyze_btn = QPushButton(f"{IconManager.get('search')} Analyze")
        analyze_btn.setProperty("variant", "primary")
        analyze_btn.clicked.connect(self._run_analysis)
        top_layout.addWidget(analyze_btn, 0, 3)

        auto_fix_btn = QPushButton(f"{IconManager.get('wand')} Auto-Fix")
        auto_fix_btn.clicked.connect(self._auto_fix_deficit)
        top_layout.addWidget(auto_fix_btn, 0, 4)

        main_layout.addWidget(top_group)

        # --- Нижняя панель: лог ---
        log_group = QGroupBox("Analysis Results")
        log_layout = QVBoxLayout(log_group)

        log_buttons = QHBoxLayout()
        copy_btn = QPushButton(f"{IconManager.get('copy')} Copy")
        copy_btn.clicked.connect(self._copy_analyzer_to_clipboard)
        log_buttons.addWidget(copy_btn)

        clear_btn = QPushButton(f"{IconManager.get('close')} Clear")
        clear_btn.clicked.connect(self._clear_analyzer_log)
        log_buttons.addWidget(clear_btn)
        log_buttons.addStretch()
        log_layout.addLayout(log_buttons)

        self.analyzer_textbox = QPlainTextEdit()
        self.analyzer_textbox.setReadOnly(True)
        self.analyzer_textbox.setObjectName("AnalyzerLog")
        log_layout.addWidget(self.analyzer_textbox)

        main_layout.addWidget(log_group)

    def _browse_analyze_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to analyze")
        if folder:
            self.analyze_path_entry.setText(folder)

    def _auto_fix_deficit(self):
        folder = self.analyze_path_entry.text().strip()
        if not folder:
            QMessageBox.warning(self, "Warning", "Select a folder to analyze first.")
            return
        self.auto_fix_deficit.emit(folder)

    def _clear_analyzer_log(self):
        self.analyzer_textbox.clear()

    def _copy_analyzer_to_clipboard(self):
        content = self.analyzer_textbox.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Info", "Log is empty.")
            return
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(content)
        QMessageBox.information(self, "Copied", "Log copied to clipboard.")

    def _run_analysis(self):
        folder = self.analyze_path_entry.text().strip()
        if not folder:
            QMessageBox.warning(self, "Warning", "Select a folder to analyze.")
            return
        self.analysis_worker = AnalysisWorker(folder, self.project_root)
        self.analysis_worker.log_message.connect(self._append_log)
        self.analysis_worker.analysis_complete.connect(self._on_analysis_complete)
        self.analysis_worker.error_occurred.connect(self._on_analysis_error)
        self.analysis_worker.start()

    def _append_log(self, message: str):
        self.analyzer_textbox.appendPlainText(message)
        cursor = self.analyzer_textbox.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.analyzer_textbox.setTextCursor(cursor)

    def _on_analysis_complete(self, matrix: dict):
        self.last_matrix = matrix
        self._log(f"Analysis complete: {matrix['total_scenes']} scenes.\n")

    def _on_analysis_error(self, error_msg: str):
        QMessageBox.critical(self, "Analysis Error", error_msg)

    def set_output_directory(self, path):
        self.output_directory = path