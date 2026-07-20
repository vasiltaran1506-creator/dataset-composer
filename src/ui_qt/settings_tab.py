from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QCheckBox,
                               QComboBox, QFileDialog, QMessageBox, QGroupBox,
                               QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path
from ui_qt.icon_manager import IconManager


class SettingsTab(QWidget):
    def __init__(self, settings_manager, project_root: Path,
                 output_directory: Path, profiles_directory: Path,
                 log_callback, on_settings_change=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.project_root = project_root
        self.output_directory = output_directory
        self.profiles_directory = profiles_directory
        self._log = log_callback
        self._on_settings_changed = on_settings_change
        self._setup_ui()
        self._load_settings_to_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # --- Directories ---
        dirs_group = QGroupBox("Directories")
        dirs_layout = QGridLayout(dirs_group)
        dirs_layout.setSpacing(10)
        dirs_layout.addWidget(QLabel("Output Directory:"), 0, 0)
        self.output_dir_entry = QLineEdit()
        self.output_dir_entry.setPlaceholderText("Select folder for generated prompts...")
        dirs_layout.addWidget(self.output_dir_entry, 0, 1)
        browse_output_btn = QPushButton(f"{IconManager.get('folder')} Browse")
        browse_output_btn.clicked.connect(self._browse_output_folder)
        dirs_layout.addWidget(browse_output_btn, 0, 2)
        dirs_layout.addWidget(QLabel("Profiles Directory:"), 1, 0)
        self.profiles_dir_entry = QLineEdit()
        self.profiles_dir_entry.setPlaceholderText("Select folder for character profiles...")
        dirs_layout.addWidget(self.profiles_dir_entry, 1, 1)
        browse_profiles_btn = QPushButton(f"{IconManager.get('folder')} Browse")
        browse_profiles_btn.clicked.connect(self._browse_profiles_folder)
        dirs_layout.addWidget(browse_profiles_btn, 1, 2)
        scroll_layout.addWidget(dirs_group)

        # --- Generation Defaults ---
        gen_group = QGroupBox("Generation Defaults")
        gen_layout = QGridLayout(gen_group)
        gen_layout.setSpacing(10)
        gen_layout.addWidget(QLabel("Number of Scenes:"), 0, 0)
        self.num_scenes_entry = QLineEdit()
        self.num_scenes_entry.setPlaceholderText("30")
        self.num_scenes_entry.editingFinished.connect(self._save_num_scenes)
        gen_layout.addWidget(self.num_scenes_entry, 0, 1, 1, 2)
        self.force_closure_check = QCheckBox("Force Deficit Closure (Aggressive Mode)")
        self.force_closure_check.stateChanged.connect(self._save_force_closure)
        gen_layout.addWidget(self.force_closure_check, 1, 0, 1, 3)
        self.balance_locs_check = QCheckBox("Balance Locations")
        self.balance_locs_check.stateChanged.connect(lambda: self._save_balance_var('balance_locations', self.balance_locs_check))
        gen_layout.addWidget(self.balance_locs_check, 2, 0)
        self.balance_acts_check = QCheckBox("Balance Actions")
        self.balance_acts_check.stateChanged.connect(lambda: self._save_balance_var('balance_actions', self.balance_acts_check))
        gen_layout.addWidget(self.balance_acts_check, 2, 1)
        self.balance_weath_check = QCheckBox("Balance Weather")
        self.balance_weath_check.stateChanged.connect(lambda: self._save_balance_var('balance_weather', self.balance_weath_check))
        gen_layout.addWidget(self.balance_weath_check, 3, 0)
        self.balance_cams_check = QCheckBox("Balance Cameras")
        self.balance_cams_check.stateChanged.connect(lambda: self._save_balance_var('balance_cameras', self.balance_cams_check))
        gen_layout.addWidget(self.balance_cams_check, 3, 1)
        scroll_layout.addWidget(gen_group)

        # --- Behavior ---
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        self.confirm_delete_check = QCheckBox("Ask for confirmation before deleting profiles/tags")
        self.confirm_delete_check.stateChanged.connect(self._save_confirm_delete)
        behavior_layout.addWidget(self.confirm_delete_check)
        scroll_layout.addWidget(behavior_group)

        # --- About ---
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout(about_group)
        about_text = QLabel(
            "Dataset Composer v1.1\n"
            "Author: Vasily Taran\n"
            "GitHub: <a href='https://github.com/vasiltaran1506-creator/dataset-composer'>repository</a>"
        )
        about_text.setOpenExternalLinks(True)
        about_layout.addWidget(about_text)
        scroll_layout.addWidget(about_group)

        # --- Кнопки внизу ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        reset_btn = QPushButton(f"{IconManager.get('refresh')} Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(reset_btn)
        scroll_layout.addLayout(buttons_layout)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _load_settings_to_ui(self):
        output_dir = self.settings_manager.get('directories', 'output_directory')
        self.output_dir_entry.setText(str(output_dir) if output_dir else str(self.output_directory))
        profiles_dir = self.settings_manager.get('directories', 'profiles_path')
        self.profiles_dir_entry.setText(str(profiles_dir) if profiles_dir else str(self.profiles_directory))
        num_scenes = self.settings_manager.get('generation_defaults', 'num_scenes')
        self.num_scenes_entry.setText(str(num_scenes))
        self.force_closure_check.setChecked(self.settings_manager.get('generation_defaults', 'force_deficit_closure'))
        self.balance_locs_check.setChecked(self.settings_manager.get('generation_defaults', 'balance_locations'))
        self.balance_acts_check.setChecked(self.settings_manager.get('generation_defaults', 'balance_actions'))
        self.balance_weath_check.setChecked(self.settings_manager.get('generation_defaults', 'balance_weather'))
        self.balance_cams_check.setChecked(self.settings_manager.get('generation_defaults', 'balance_cameras'))
        self.confirm_delete_check.setChecked(self.settings_manager.get('behavior', 'confirm_delete'))

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir_entry.setText(folder)
            self.settings_manager.set('directories', 'output_directory', folder)
            if self._on_settings_changed:
                self._on_settings_changed('directories', 'output_directory', folder)
            self._log(f"Output directory set to: {folder}\n")

    def _browse_profiles_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select profiles folder")
        if folder:
            self.profiles_dir_entry.setText(folder)
            self.settings_manager.set('directories', 'profiles_path', folder)
            if self._on_settings_changed:
                self._on_settings_changed('directories', 'profiles_path', folder)
            self._log(f"Profiles directory set to: {folder}\n")

    def _save_num_scenes(self):
        try:
            value = int(self.num_scenes_entry.text())
            if value > 0:
                self.settings_manager.set('generation_defaults', 'num_scenes', value)
                if self._on_settings_changed:
                    self._on_settings_changed('generation_defaults', 'num_scenes', value)
                self._log(f"Number of scenes set to: {value}\n")
            else:
                raise ValueError
        except ValueError:
            valid_value = self.settings_manager.get('generation_defaults', 'num_scenes')
            self.num_scenes_entry.setText(str(valid_value))
            QMessageBox.warning(self, "Warning", "Please enter a valid positive number.")

    def _save_force_closure(self):
        value = self.force_closure_check.isChecked()
        self.settings_manager.set('generation_defaults', 'force_deficit_closure', value)
        if self._on_settings_changed:
            self._on_settings_changed('generation_defaults', 'force_deficit_closure', value)
        self._log(f"Force Deficit Closure: {'ON' if value else 'OFF'}\n")

    def _save_balance_var(self, key: str, checkbox: QCheckBox):
        value = checkbox.isChecked()
        self.settings_manager.set('generation_defaults', key, value)
        if self._on_settings_changed:
            self._on_settings_changed('generation_defaults', key, value)
        self._log(f"{key}: {'ON' if value else 'OFF'}\n")

    def _save_confirm_delete(self):
        value = self.confirm_delete_check.isChecked()
        self.settings_manager.set('behavior', 'confirm_delete', value)
        self._log(f"Confirm delete: {'ON' if value else 'OFF'}\n")

    def _reset_to_defaults(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings_manager.reset_to_defaults()
            self._load_settings_to_ui()
            self._log("Settings reset to defaults.\n")
            QMessageBox.information(self, "Success", "Settings have been reset.")

    def set_output_directory(self, path):
        self.output_dir_entry.setText(str(path))

    def set_num_scenes(self, value):
        self.num_scenes_entry.setText(str(value))

    def set_balance_var(self, key: str, value):
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