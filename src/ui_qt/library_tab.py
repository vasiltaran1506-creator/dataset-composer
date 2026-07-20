from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit,
                               QTabWidget, QTreeWidget, QTreeWidgetItem,
                               QScrollArea, QFrame, QGroupBox, QMessageBox,
                               QCheckBox, QApplication, QSplitter)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from pathlib import Path
from ui_qt.icon_manager import IconManager
import json
from ui_qt.icon_manager import IconManager


class LibraryTab(QWidget):
    """Вкладка редактирования библиотеки тегов и scene-rules"""

    def __init__(self, project_root: Path, log_callback, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self._log = log_callback

        # Tag Editor state
        self.library_current_file: Path | None = None
        self.library_tags: list[str] = []
        self._tags_cache = {}

        # Scene Rules state
        self.scene_rules_data = {}
        self.current_rule_file: str | None = None
        self._current_checkboxes = {}
        self._loading_checkboxes = False

        self._setup_ui()

    # ═══════════════════════════════════════════════
    # MAIN LAYOUT
    # ═══════════════════════════════════════════════
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Tag Editor
        self.tag_editor_widget = QWidget()
        self._setup_tag_editor(self.tag_editor_widget)
        self.tab_widget.addTab(self.tag_editor_widget, f"{IconManager.get('tag')} Tag Editor")

        # Scene Rules
        self.scene_rules_widget = QWidget()
        self._setup_scene_rules(self.scene_rules_widget)
        self.tab_widget.addTab(self.scene_rules_widget, f"{IconManager.get('movie')} Scene Rules")

        main_layout.addWidget(self.tab_widget)

    # ═══════════════════════════════════════════════
    # TAG EDITOR
    # ═══════════════════════════════════════════════
    def _setup_tag_editor(self, widget: QWidget):
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Left panel: file tree
        left_widget = QWidget()
        left_widget.setMaximumWidth(400)
        left_widget.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        tree_title = QLabel("Prompt Library")
        tree_title.setObjectName("SectionTitle")
        left_layout.addWidget(tree_title)

        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderHidden(True)
        self.library_tree.itemClicked.connect(self._on_library_item_clicked)
        left_layout.addWidget(self.library_tree)
        self._build_library_tree()

        # Right panel: tag editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.library_editor_title = QLabel("Tag Editor (select a file)")
        self.library_editor_title.setObjectName("PageTitle")
        right_layout.addWidget(self.library_editor_title)

        # Search bar
        search_layout = QHBoxLayout()
        self.library_search_entry = QLineEdit()
        self.library_search_entry.setPlaceholderText("Search tags...")
        self.library_search_entry.textChanged.connect(self._filter_library_tags)
        search_layout.addWidget(self.library_search_entry)

        clear_search_btn = QPushButton(f"{IconManager.get('close')} Clear")
        clear_search_btn.setProperty("variant", "ghost")
        clear_search_btn.clicked.connect(self._clear_library_search)
        search_layout.addWidget(clear_search_btn)
        right_layout.addLayout(search_layout)

        # Tags container
        self.library_tags_container = QScrollArea()
        self.library_tags_container.setWidgetResizable(True)
        self.library_tags_container.setFrameShape(QFrame.NoFrame)
        tags_widget = QWidget()
        self.tags_layout = QVBoxLayout(tags_widget)
        self.tags_layout.setSpacing(2)
        self.tags_layout.addStretch()
        self.library_tags_container.setWidget(tags_widget)
        right_layout.addWidget(self.library_tags_container)

        # Add tag
        add_layout = QHBoxLayout()
        self.new_tag_entry = QLineEdit()
        self.new_tag_entry.setPlaceholderText("Enter new tag...")
        self.new_tag_entry.returnPressed.connect(self._add_library_tag)
        add_layout.addWidget(self.new_tag_entry)

        add_tag_btn = QPushButton(f"{IconManager.get('plus')} Add Tag")
        add_tag_btn.setProperty("variant", "success")
        add_tag_btn.clicked.connect(self._add_library_tag)
        add_layout.addWidget(add_tag_btn)
        right_layout.addLayout(add_layout)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget, 1)

    def _build_library_tree(self):
        self.library_tree.clear()
        library_dir = self.project_root / "prompt-library"
        if not library_dir.exists():
            item = QTreeWidgetItem(["Folder not found"])
            self.library_tree.addTopLevelItem(item)
            return

        categories = {}
        for txt_file in sorted(library_dir.rglob("*.txt")):
            parts = txt_file.relative_to(library_dir).parts
            if len(parts) >= 2:
                main_cat = parts[0]
                sub_cat = parts[1].replace('.txt', '')
            elif len(parts) == 1:
                main_cat = "general"
                sub_cat = parts[0].replace('.txt', '')
            else:
                continue
            categories.setdefault(main_cat, {}).setdefault(sub_cat, []).append(txt_file)

        for main_cat, subcats in sorted(categories.items()):
            main_item = QTreeWidgetItem([main_cat.replace('_', ' ').title()])
            main_item.setExpanded(False)
            for sub_cat, files in sorted(subcats.items()):
                sub_item = QTreeWidgetItem([sub_cat.replace('_', ' ').title()])
                sub_item.setExpanded(False)
                for txt_file in files:
                    file_item = QTreeWidgetItem([txt_file.name])
                    file_item.setData(0, Qt.UserRole, str(txt_file))
                    sub_item.addChild(file_item)
                main_item.addChild(sub_item)
            self.library_tree.addTopLevelItem(main_item)

    def _on_library_item_clicked(self, item: QTreeWidgetItem, column: int):
        file_path_str = item.data(0, Qt.UserRole)
        if file_path_str:
            self._load_library_file(Path(file_path_str))

    def _load_library_file(self, file_path: Path):
        self.library_current_file = file_path
        self.library_tags = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.library_tags.append(line)
        except Exception as e:
            self._log(f"[ERROR] Cannot read {file_path}: {e}\n")
            return
        rel_path = file_path.relative_to(self.project_root / "prompt-library")
        self.library_editor_title.setText(f"{rel_path} ({len(self.library_tags)} tags)")
        self._display_library_tags()
        self.library_search_entry.clear()

    def _display_library_tags(self, filter_text: str = ""):
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered_tags = self.library_tags
        if filter_text:
            filter_lower = filter_text.lower()
            filtered_tags = [t for t in self.library_tags if filter_lower in t.lower()]

        if not self.library_tags:
            label = QLabel("(No tags in this file)")
            label.setObjectName("Subtitle")
            self.tags_layout.insertWidget(0, label)
            return

        if not filtered_tags:
            label = QLabel(f"(No tags match '{filter_text}')")
            label.setObjectName("Subtitle")
            self.tags_layout.insertWidget(0, label)
            return

        for tag in filtered_tags:
            tag_widget = QWidget()
            tag_widget.setObjectName("TagRow")
            tag_layout = QHBoxLayout(tag_widget)
            tag_layout.setContentsMargins(8, 2, 8, 2)
            tag_layout.setSpacing(5)

            tag_label = QLabel(f"  {tag}")
            tag_layout.addWidget(tag_label, 1)

            delete_btn = QPushButton(f"{IconManager.get('close')}")
            delete_btn.setFixedSize(25, 25)
            delete_btn.setProperty("variant", "icon-only")
            delete_btn.clicked.connect(lambda checked, t=tag: self._delete_library_tag(t))
            tag_layout.addWidget(delete_btn)

            self.tags_layout.insertWidget(self.tags_layout.count() - 1, tag_widget)

    def _filter_library_tags(self, text: str):
        self._display_library_tags(text)

    def _clear_library_search(self):
        self.library_search_entry.clear()
        self._display_library_tags()

    def _add_library_tag(self):
        if self.library_current_file is None:
            QMessageBox.warning(self, "Warning", "Select a file first.")
            return
        new_tag = self.new_tag_entry.text().strip()
        if not new_tag:
            return
        if new_tag in self.library_tags:
            QMessageBox.warning(self, "Warning", f"Tag '{new_tag}' already exists.")
            return
        self.library_tags.append(new_tag)
        self.new_tag_entry.clear()
        self._save_library_file()
        self._display_library_tags()
        rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
        self.library_editor_title.setText(f"{rel_path} ({len(self.library_tags)} tags)")
        self._log(f"[ADD] Tag added: {new_tag}\n")

    def _delete_library_tag(self, tag: str):
        if self.library_current_file is None:
            return
        if tag in self.library_tags:
            self.library_tags.remove(tag)
            self._save_library_file()
        filter_text = self.library_search_entry.text().strip()
        self._display_library_tags(filter_text)
        rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
        self.library_editor_title.setText(f"{rel_path} ({len(self.library_tags)} tags)")
        self._log(f"[DEL] Tag removed: {tag}\n")

    def _save_library_file(self):
        if self.library_current_file is None:
            return
        try:
            with open(self.library_current_file, 'w', encoding='utf-8') as f:
                for tag in self.library_tags:
                    f.write(f"{tag}\n")
            cache_key = str(self.library_current_file)
            if cache_key in self._tags_cache:
                del self._tags_cache[cache_key]
            self._log(f"[SAVE] File saved: {self.library_current_file.name}\n")
        except Exception as e:
            self._log(f"[ERROR] Save failed: {e}\n")
            QMessageBox.critical(self, "Error", f"Cannot save file: {e}")

    # ═══════════════════════════════════════════════
    # SCENE RULES EDITOR
    # ══════════════════════════════════════════════
    def _setup_scene_rules(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Top bar
        top_layout = QHBoxLayout()
        self.auto_sync_check = QCheckBox("Auto-sync")
        self.auto_sync_check.setChecked(True)
        top_layout.addWidget(self.auto_sync_check)

        help_btn = QPushButton(f"{IconManager.get('help')}")
        help_btn.setFixedSize(25, 25)
        help_btn.setProperty("variant", "ghost")
        help_btn.clicked.connect(self._show_auto_sync_help)
        top_layout.addWidget(help_btn)
        top_layout.addStretch()

        reload_btn = QPushButton(f"{IconManager.get('refresh')} Reload")
        reload_btn.clicked.connect(self._reload_scene_rules)
        top_layout.addWidget(reload_btn)

        validate_btn = QPushButton(f"{IconManager.get('check')} Validate")
        validate_btn.setProperty("variant", "primary")
        validate_btn.clicked.connect(self._validate_scene_rules_integrity)
        top_layout.addWidget(validate_btn)

        autofix_btn = QPushButton(f"{IconManager.get('wand')} Auto-fix")
        autofix_btn.setProperty("variant", "primary")
        autofix_btn.clicked.connect(self._auto_fix_tag_format)
        top_layout.addWidget(autofix_btn)

        save_btn = QPushButton(f"{IconManager.get('save')} Save All")
        save_btn.setProperty("variant", "success")
        save_btn.clicked.connect(self._save_scene_rules)
        top_layout.addWidget(save_btn)

        layout.addLayout(top_layout)

        # Splitter
        content_splitter = QSplitter(Qt.Horizontal)

        # Left: rules tree
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.scene_rules_tree = QTreeWidget()
        self.scene_rules_tree.setHeaderHidden(True)
        self.scene_rules_tree.itemClicked.connect(self._on_scene_rule_clicked)
        left_layout.addWidget(self.scene_rules_tree)

        # Right: editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.scene_rules_editor_scroll = QScrollArea()
        self.scene_rules_editor_scroll.setWidgetResizable(True)
        self.scene_rules_editor_scroll.setFrameShape(QFrame.NoFrame)
        self.scene_rules_editor_widget = QWidget()
        self.scene_rules_editor_layout = QVBoxLayout(self.scene_rules_editor_widget)
        self.scene_rules_editor_layout.setAlignment(Qt.AlignTop)

        placeholder = QLabel("Select a rule on the left to edit")
        placeholder.setObjectName("Subtitle")
        placeholder.setAlignment(Qt.AlignCenter)
        self.scene_rules_editor_layout.addWidget(placeholder)

        self.scene_rules_editor_scroll.setWidget(self.scene_rules_editor_widget)
        right_layout.addWidget(self.scene_rules_editor_scroll)

        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        layout.addWidget(content_splitter, 1)

        self._load_scene_rules()
        self._build_scene_rules_tree()

    def _build_scene_rules_tree(self):
        self.scene_rules_tree.clear()
        if not self.scene_rules_data:
            item = QTreeWidgetItem(["(No rules loaded)"])
            self.scene_rules_tree.addTopLevelItem(item)
            return

        for category_name, rules in sorted(self.scene_rules_data.items()):
            cat_item = QTreeWidgetItem([f"{category_name.replace('_', ' ').title()} ({len(rules)})"])
            cat_item.setExpanded(True)

            add_item = QTreeWidgetItem([f"{IconManager.get('plus')} Add new rule..."])
            add_item.setData(0, Qt.UserRole, {'action': 'add', 'category': category_name})
            cat_item.addChild(add_item)

            for rule_name in sorted(rules.keys()):
                rule_item = QTreeWidgetItem([f"{IconManager.get('book')} {rule_name}"])
                rule_data = rules[rule_name]
                rule_item.setData(0, Qt.UserRole, {
                    'action': 'select',
                    'category': category_name,
                    'rule_name': rule_name,
                    'path': str(rule_data['path'])
                })
                cat_item.addChild(rule_item)
            self.scene_rules_tree.addTopLevelItem(cat_item)

    def _on_scene_rule_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        action = data.get('action')
        if action == 'add':
            self._create_new_rule(data.get('category'))
        elif action == 'select':
            self._select_scene_rule(data.get('category'), data.get('rule_name'))

    def _select_scene_rule(self, category: str, rule_name: str):
        rule_data = self.scene_rules_data[category][rule_name]
        self.current_rule_file = rule_data['path']
        data = rule_data['data']
        meta = data.get('meta', {})
        self._log(f"[EDIT] {category}/{rule_name}\n")
        self._clear_scene_rules_editor()
        self._render_scene_rule_content(category, rule_name, data, meta)

    def _clear_scene_rules_editor(self):
        while self.scene_rules_editor_layout.count():
            item = self.scene_rules_editor_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

    def _render_scene_rule_content(self, category: str, rule_name: str, data: dict, meta: dict):
        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)

        title = QLabel(meta.get('display_name', rule_name))
        title.setObjectName("PageTitle")
        header_layout.addWidget(title)

        subtitle = QLabel(f"({category}/{rule_name}.toml)")
        subtitle.setObjectName("Subtitle")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        delete_btn = QPushButton("Delete Rule")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(lambda: self._delete_scene_rule(category, rule_name))
        header_layout.addWidget(delete_btn)

        self.scene_rules_editor_layout.addWidget(header_frame)

        # Meta
        self._render_meta_section(meta, category)

        # Category-specific editors
        if category == 'locations':
            self._render_location_editor(self.scene_rules_editor_layout, data)
        elif category == 'actions':
            self._render_action_editor(self.scene_rules_editor_layout, data)
        elif category == 'weather':
            self._render_weather_editor(self.scene_rules_editor_layout, data)
        elif category == 'camera':
            self._render_camera_editor(self.scene_rules_editor_layout, data)
        elif category == 'location_types':
            self._render_location_type_editor(self.scene_rules_editor_layout, data)
        else:
            placeholder = QLabel(f"Editor for category '{category}' not implemented.")
            placeholder.setObjectName("Subtitle")
            placeholder.setAlignment(Qt.AlignCenter)
            self.scene_rules_editor_layout.addWidget(placeholder)

    def _render_meta_section(self, meta: dict, category: str):
        meta_frame = QFrame()
        meta_frame.setObjectName("MetaPanel")
        meta_layout = QVBoxLayout(meta_frame)
        meta_layout.setContentsMargins(15, 10, 15, 10)
        meta_layout.setSpacing(8)

        title = QLabel("Meta Information")
        title.setObjectName("SectionTitle")
        meta_layout.addWidget(title)

        # ID
        id_row = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setFixedWidth(120)
        id_row.addWidget(id_label)
        self.meta_id_entry = QLineEdit()
        self.meta_id_entry.setText(meta.get('id', ''))
        self.meta_id_entry.editingFinished.connect(lambda: self._save_meta_changes('id', self.meta_id_entry.text()))
        id_row.addWidget(self.meta_id_entry)
        meta_layout.addLayout(id_row)

        # Display Name
        name_row = QHBoxLayout()
        name_label = QLabel("Display Name:")
        name_label.setFixedWidth(120)
        name_row.addWidget(name_label)
        self.meta_name_entry = QLineEdit()
        self.meta_name_entry.setText(meta.get('display_name', ''))
        self.meta_name_entry.editingFinished.connect(lambda: self._save_meta_changes('display_name', self.meta_name_entry.text()))
        name_row.addWidget(self.meta_name_entry)
        meta_layout.addLayout(name_row)

        # Type (locations only)
        if category == 'locations':
            type_row = QHBoxLayout()
            type_label = QLabel("Location Type:")
            type_label.setFixedWidth(120)
            type_row.addWidget(type_label)
            from PySide6.QtWidgets import QComboBox
            self.meta_type_combo = QComboBox()
            types = sorted(self.scene_rules_data.get('location_types', {}).keys())
            self.meta_type_combo.addItems(types)
            current_type = meta.get('type', '')
            if current_type in types:
                self.meta_type_combo.setCurrentText(current_type)
            self.meta_type_combo.currentTextChanged.connect(lambda val: self._save_meta_changes('type', val))
            type_row.addWidget(self.meta_type_combo)
            meta_layout.addLayout(type_row)

        self.scene_rules_editor_layout.addWidget(meta_frame)

    def _save_meta_changes(self, field: str, new_value: str):
        if not self.current_rule_file or not Path(self.current_rule_file).exists():
            return
        new_value = new_value.strip()
        if not new_value:
            return
        try:
            rel_path = Path(self.current_rule_file).relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) < 2:
                return
            category = parts[0]
            rule_name = parts[1].replace('.toml', '')
        except Exception:
            return

        rule_data = self.scene_rules_data.get(category, {}).get(rule_name, {}).get('data', {})
        if not rule_data:
            return
        if 'meta' not in rule_data:
            rule_data['meta'] = {}

        old_value = rule_data['meta'].get(field, '')
        if old_value == new_value:
            return
        rule_data['meta'][field] = new_value

        try:
            import tomli_w
            with open(self.current_rule_file, 'wb') as f:
                tomli_w.dump(rule_data, f)
        except ImportError:
            self._write_toml_manually(Path(self.current_rule_file), rule_data)

        if field == 'id' and new_value != rule_name:
            safe_name = new_value.replace(' ', '_').lower()
            new_file_path = Path(self.current_rule_file).parent / f"{safe_name}.toml"
            if new_file_path.exists():
                self._log(f"[WARNING] File with ID '{safe_name}' already exists.\n")
                QMessageBox.warning(self, "Warning", f"Rule with ID '{safe_name}' already exists!")
                return
            try:
                import shutil
                shutil.move(str(self.current_rule_file), str(new_file_path))
                self.current_rule_file = str(new_file_path)
                self.scene_rules_data[category][safe_name] = self.scene_rules_data[category].pop(rule_name)
                self.scene_rules_data[category][safe_name]['path'] = str(new_file_path)
                self.scene_rules_data[category][safe_name]['data']['meta']['id'] = safe_name
                self._build_scene_rules_tree()
                self._log(f"[RENAME] ID changed: {rule_name} -> {safe_name}\n")
            except Exception as e:
                self._log(f"[ERROR] Rename failed: {e}\n")
                return
        else:
            self._log(f"[SAVE] Meta saved: {field} = {new_value}\n")

    def _write_toml_manually(self, file_path: Path, data: dict):
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            for section, content in data.items():
                f.write(f"[{section}]\n")
                if isinstance(content, dict):
                    for key, value in content.items():
                        if isinstance(value, list):
                            f.write(f'{key} = {json.dumps(value)}\n')
                        elif isinstance(value, str):
                            f.write(f'{key} = "{value}"\n')
                        elif isinstance(value, (int, float, bool)):
                            f.write(f'{key} = {json.dumps(value)}\n')
                f.write("\n")

    def _create_new_rule(self, category: str):
        new_name = f"new_{category.lower().replace(' ', '_')}_rule"
        if new_name in self.scene_rules_data.get(category, {}):
            counter = 1
            while f"{new_name}_{counter}" in self.scene_rules_data.get(category, {}):
                counter += 1
            new_name = f"{new_name}_{counter}"

        rules_dir = self.project_root / "scene-rules" / category
        rules_dir.mkdir(parents=True, exist_ok=True)
        new_file_path = rules_dir / f"{new_name}.toml"

        new_data = {
            'meta': {'id': new_name, 'display_name': new_name.replace('_', ' ').title()},
            'soft_constraints': {},
            'hard_constraints': {}
        }
        if category == 'locations':
            new_data['meta']['type'] = 'indoor_private'

        try:
            import tomli_w
            with open(new_file_path, 'wb') as f:
                tomli_w.dump(new_data, f)
        except ImportError:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(f'[meta]\nid = "{new_name}"\n')
                f.write(f'display_name = "{new_data["meta"]["display_name"]}"\n')
                if category == 'locations':
                    f.write('type = "indoor_private"\n')
                f.write("\n[soft_constraints]\n[hard_constraints]\n")
        except Exception as e:
            self._log(f"[ERROR] Create failed: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed: {e}")
            return

        if category not in self.scene_rules_data:
            self.scene_rules_data[category] = {}
        self.scene_rules_data[category][new_name] = {'path': str(new_file_path), 'data': new_data}
        self._build_scene_rules_tree()
        self._select_scene_rule(category, new_name)
        self._log(f"[ADD] New rule created: {category}/{new_name}\n")
        QMessageBox.information(self, "Success", f"New rule '{new_name}' created!")

    def _delete_scene_rule(self, category: str, rule_name: str):
        rule_path = self.project_root / "scene-rules" / category / f"{rule_name}.toml"
        if not rule_path.exists():
            self._log(f"[WARNING] File not found: {rule_path}\n")
            return
        reply = QMessageBox.question(
            self, "Delete Rule",
            f"Are you sure you want to delete rule '{rule_name}'?\n\n"
            f"{category}/{rule_name}.toml\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            rule_path.unlink()
            if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                del self.scene_rules_data[category][rule_name]
            self._build_scene_rules_tree()
            self._clear_scene_rules_editor()
            placeholder = QLabel("Select a rule on the left to edit")
            placeholder.setObjectName("Subtitle")
            placeholder.setAlignment(Qt.AlignCenter)
            self.scene_rules_editor_layout.addWidget(placeholder)
            self.current_rule_file = None
            self._log(f"[DEL] Rule deleted: {category}/{rule_name}\n")
            QMessageBox.information(self, "Success", f"Rule '{rule_name}' deleted.")
        except Exception as e:
            self._log(f"[ERROR] Delete failed: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed: {e}")

    # ═══════════════════════════════════════════════
    # SCENE RULES HELPERS
    # ═══════════════════════════════════════════════
    def _show_auto_sync_help(self):
        help_text = (
            "Auto-sync relationships\n\n"
            "When ENABLED:\n"
            "  - Adding action 'reading' to location 'library' preferences\n"
            "  - Automatically adds 'library' to action 'reading' preferences\n"
            "  - Ensures data consistency\n\n"
            "When DISABLED:\n"
            "  - Full manual control over all relationships\n"
            "  - Changes in one file do not affect others\n"
            "  - Useful for fine-tuning or fixing errors\n\n"
            "Recommendation: keep enabled for most cases."
        )
        QMessageBox.information(self, "Auto-sync Help", help_text)

    def _reload_scene_rules(self):
        self._load_scene_rules()
        self._build_scene_rules_tree()
        self._log("[RELOAD] Scene rules reloaded.\n")
        QMessageBox.information(self, "Success", "Scene rules reloaded.")

    def _save_scene_rules(self):
        QMessageBox.information(self, "Info", "Save functionality coming in next step...")

    def _validate_scene_rules_integrity(self):
        QMessageBox.information(self, "Info", "Validate functionality coming in next step...")

    def _auto_fix_tag_format(self):
        QMessageBox.information(self, "Info", "Auto-fix functionality coming in next step...")

    def _load_scene_rules(self):
        self.scene_rules_data = {}
        rules_dir = self.project_root / "scene-rules"
        if not rules_dir.exists():
            self._log(f"[WARNING] Scene rules folder not found: {rules_dir}\n")
            return
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli
            except ImportError:
                self._log("[ERROR] tomli/tomllib not installed.\n")
                return

        for category_dir in sorted(rules_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category_name = category_dir.name
            self.scene_rules_data[category_name] = {}
            for toml_file in sorted(category_dir.glob("*.toml")):
                try:
                    with open(toml_file, 'rb') as f:
                        data = tomli.load(f)
                    self.scene_rules_data[category_name][toml_file.stem] = {
                        'path': str(toml_file), 'data': data
                    }
                except Exception as e:
                    self._log(f"[ERROR] Cannot read {toml_file.name}: {e}\n")
        total_files = sum(len(v) for v in self.scene_rules_data.values())
        self._log(f"[OK] Loaded {total_files} scene-rule files.\n")

    # ═══════════════════════════════════════════════
    # SECTION RENDERING (with LAZY LOADING)
    # ═══════════════════════════════════════════════
    def _render_section_header(self, parent_layout, title: str):
        separator_widget = QWidget()
        separator_widget.setObjectName("SectionDivider")
        separator_layout = QVBoxLayout(separator_widget)
        separator_layout.setContentsMargins(5, 16, 5, 5)
        separator_layout.setSpacing(5)

        top_line = QFrame()
        top_line.setFrameShape(QFrame.HLine)
        separator_layout.addWidget(top_line)

        header_frame = QFrame()
        header_frame.setObjectName("SectionDividerTitle")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 8, 15, 8)
        title_label = QLabel(title)
        title_label.setObjectName("SectionDividerLabel")
        header_layout.addWidget(title_label)
        separator_layout.addWidget(header_frame)

        bottom_line = QFrame()
        bottom_line.setFrameShape(QFrame.HLine)
        separator_layout.addWidget(bottom_line)

        parent_layout.addWidget(separator_widget)

    def _load_all_tags_from_category(self, category: str) -> dict:
        if not hasattr(self, '_all_tags_category_cache'):
            self._all_tags_category_cache = {}
        if category in self._all_tags_category_cache:
            return self._all_tags_category_cache[category]

        result = {}
        cat_dir = self.project_root / "prompt-library" / category
        if not cat_dir.exists():
            self._all_tags_category_cache[category] = result
            return result

        for txt_file in sorted(cat_dir.rglob("*.txt")):
            rel_path = txt_file.relative_to(cat_dir)
            if len(rel_path.parts) >= 2:
                main_cat = rel_path.parts[0]
                sub_cat = txt_file.stem
            else:
                main_cat = "general"
                sub_cat = txt_file.stem

            tags = []
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            tags.append(line)
            except Exception as e:
                self._log(f"[ERROR] Cannot read {txt_file}: {e}\n")
                continue
            if tags:
                result.setdefault(main_cat, {})[sub_cat] = tags
        self._all_tags_category_cache[category] = result
        return result

    def _count_items(self, all_items, selected_items):
        """Подсчитывает общее количество и количество выбранных."""
        total = 0
        selected = 0
        if isinstance(all_items, dict):
            for main_cat, subcats in all_items.items():
                if isinstance(subcats, dict):
                    for subcat_name, tags in subcats.items():
                        total += len(tags)
                        selected += sum(1 for s in selected_items if s in tags)
                else:
                    total += len(subcats)
                    selected += sum(1 for s in selected_items if s in subcats)
        else:
            total = len(all_items) if all_items else 0
            selected = sum(1 for s in selected_items if s in (all_items or []))
        return total, selected

    def _render_checklist_section(self, parent_layout, title: str, all_items,
                                  selected_items: list, constraint_key: str):
        """Рендерит сворачиваемую секцию с ЛЕНИВОЙ загрузкой чекбоксов."""
        section_widget = QWidget()
        section_widget.setObjectName("ChecklistSection")
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(8, 8, 8, 8)
        section_layout.setSpacing(5)

        if not hasattr(self, '_current_checkboxes'):
            self._current_checkboxes = {}

        total_count, selected_count = self._count_items(all_items, selected_items)

        # Toggle button
        toggle_btn = QPushButton(f"{IconManager.get('chevron-right')}  {title} ({selected_count}/{total_count})")
        section_layout.addWidget(toggle_btn)

        # Content container (hidden by default)
        content_widget = QWidget()
        content_widget.setVisible(False)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 5, 10, 10)

        checkbox_scroll = QScrollArea()
        checkbox_scroll.setWidgetResizable(True)
        checkbox_scroll.setMaximumHeight(300)
        checkbox_scroll.setFrameShape(QFrame.NoFrame)
        checkbox_widget = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_widget)
        checkbox_layout.setSpacing(2)
        checkbox_layout.addStretch()

        checkbox_scroll.setWidget(checkbox_widget)
        content_layout.addWidget(checkbox_scroll)
        section_layout.addWidget(content_widget)

        # Lazy loading state
        content_widget._is_loaded = False
        content_widget._all_items = all_items
        content_widget._selected_items = selected_items
        content_widget._constraint_key = constraint_key
        content_widget._checkbox_layout = checkbox_layout
        content_widget._checkboxes = {}
        content_widget._toggle_btn = toggle_btn
        content_widget._title = title
        content_widget._total_count = total_count
        content_widget._selected_count = selected_count

        def toggle_visibility():
            is_visible = content_widget.isVisible()
            content_widget.setVisible(not is_visible)
            if not is_visible:
                toggle_btn.setText(f"{IconManager.get('chevron-right')}  {title} ({selected_count}/{total_count})")
                if not content_widget._is_loaded:
                    self._lazy_load_checkboxes(content_widget)
            else:
                toggle_btn.setText(f"{IconManager.get('chevron-down')}  {title} ({selected_count}/{total_count})")

        toggle_btn.clicked.connect(toggle_visibility)
        self._current_checkboxes[constraint_key] = content_widget._checkboxes
        parent_layout.addWidget(section_widget)

    def _lazy_load_checkboxes(self, content_widget):
        """Создаёт чекбоксы батчами, не блокируя UI. Решает проблему подвисания."""
        self._loading_checkboxes = True

        layout = content_widget._checkbox_layout
        all_items = content_widget._all_items
        selected_items = content_widget._selected_items
        constraint_key = content_widget._constraint_key
        checkboxes = content_widget._checkboxes

        # Show loading indicator
        loading_label = QLabel("Loading tags...")
        loading_label.setObjectName("Subtitle")
        layout.insertWidget(0, loading_label)
        QApplication.processEvents()

        # Build flat list of items to render
        flat_items = []
        if isinstance(all_items, dict):
            for main_cat_name, subcats in sorted(all_items.items()):
                if not isinstance(subcats, dict):
                    continue
                for subcat_name, tags in sorted(subcats.items()):
                    flat_items.append(('header', subcat_name))
                    for tag in sorted(tags):
                        flat_items.append(('tag', tag))
        else:
            if all_items:
                for item in sorted(all_items):
                    flat_items.append(('tag', item))

        iterator = iter(flat_items)
        BATCH_SIZE = 80

        def process_batch():
            count = 0
            while count < BATCH_SIZE:
                try:
                    item_type, item_value = next(iterator)
                except StopIteration:
                    # Remove loading indicator
                    if loading_label.parent() is not None:
                        loading_label.deleteLater()
                    content_widget._is_loaded = True
                    self._loading_checkboxes = False
                    return

                if item_type == 'header':
                    header_label = QLabel(item_value.replace('_', ' ').title())
                    header_label.setObjectName("Subtitle")
                    layout.insertWidget(layout.count() - 1, header_label)
                else:
                    tag = item_value
                    cb = QCheckBox(tag.replace('_', ' '))
                    cb.setChecked(tag in selected_items)
                    cb.stateChanged.connect(
                        lambda state, t=tag, v=cb: self._on_checkbox_toggled(t, v, constraint_key, None, all_items)
                    )
                    layout.insertWidget(layout.count() - 1, cb)
                    checkboxes[tag] = cb
                count += 1

            # Schedule next batch
            QTimer.singleShot(0, process_batch)

        process_batch()

    def _on_checkbox_toggled(self, item: str, checkbox: QCheckBox, constraint_key: str,
                             count_label, all_items):
        is_checked = checkbox.isChecked()
        self._log(f"[{'ON' if is_checked else 'OFF'}] {constraint_key}: {item}\n")
        # Не сохранять во время массовой загрузки — избегаем сотен записей TOML
        if not self._loading_checkboxes and self.current_rule_file:
            self._save_current_rule_silently()

    def _save_current_rule_silently(self):
        if not self.current_rule_file or not Path(self.current_rule_file).exists():
            return
        if not hasattr(self, '_current_checkboxes') or not self._current_checkboxes:
            return
        try:
            import tomli
            import tomli_w
        except ImportError:
            return
        try:
            with open(self.current_rule_file, 'rb') as f:
                data = tomli.load(f)
            changes = self._collect_checkbox_changes()
            if not changes:
                return
            for category, rule_name, field, new_values in changes:
                target_section = 'hard_constraints' if 'excludes' in field or 'required' in field or 'allowed' in field else 'soft_constraints'
                if target_section not in data:
                    data[target_section] = {}
                data[target_section][field] = new_values
            with open(self.current_rule_file, 'wb') as f:
                tomli_w.dump(data, f)
            rel_path = Path(self.current_rule_file).relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) >= 2:
                category = parts[0]
                rule_name = parts[1].replace('.toml', '')
                if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                    self.scene_rules_data[category][rule_name]['data'] = data
        except Exception as e:
            self._log(f"[WARNING] Autosave failed: {e}\n")

    def _collect_checkbox_changes(self) -> list:
        changes = []
        if not self.current_rule_file:
            return changes
        try:
            rel_path = Path(self.current_rule_file).relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) < 2:
                return changes
            current_category = parts[0]
            current_rule_name = parts[1].replace('.toml', '')
        except Exception:
            return changes
        for constraint_key, checkboxes in self._current_checkboxes.items():
            selected_values = [tag for tag, cb in checkboxes.items() if cb.isChecked()]
            changes.append((current_category, current_rule_name, constraint_key, sorted(selected_values)))
        return changes

    # ═══════════════════════════════════════════════
    # CATEGORY-SPECIFIC EDITORS
    # ═══════════════════════════════════════════════
    def _render_location_editor(self, parent_layout, data: dict):
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})

        self._render_section_header(parent_layout, "OUTFIT")
        all_outfit_styles = self._load_all_tags_from_category("02_clothing")
        self._render_checklist_section(parent_layout, "Allowed Outfit Styles (Hard Whitelist)",
                                       all_outfit_styles, hard.get('allowed_outfit_categories', []), 'allowed_outfit_categories')
        self._render_checklist_section(parent_layout, "Excluded Outfit Styles (Hard Ban)",
                                       all_outfit_styles, hard.get('excludes_outfit_categories', []), 'excludes_outfit_categories')
        self._render_checklist_section(parent_layout, "Preferred Outfit Styles (Soft Priority)",
                                       all_outfit_styles, soft.get('preferred_outfit_categories', []), 'preferred_outfit_categories')
        self._render_checklist_section(parent_layout, "Avoid Outfit Styles (Soft Ban)",
                                       all_outfit_styles, soft.get('avoid_outfit_categories', []), 'avoid_outfit_categories')

        self._render_section_header(parent_layout, "ACTIONS")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent_layout, "Allowed Actions (Hard Whitelist)",
                                       all_actions, hard.get('allowed_actions', []), 'allowed_actions')
        self._render_checklist_section(parent_layout, "Excluded Actions (Hard Ban)",
                                       all_actions, hard.get('excludes_actions', []), 'excludes_actions')
        self._render_checklist_section(parent_layout, "Prefers Actions (Soft Priority)",
                                       all_actions, soft.get('prefers_actions', []), 'prefers_actions')
        self._render_checklist_section(parent_layout, "Avoid Actions (Soft Ban)",
                                       all_actions, soft.get('avoid_actions', []), 'avoid_actions')

        self._render_section_header(parent_layout, "PROPS")
        all_props = self._load_all_tags_from_category("09_props")
        self._render_checklist_section(parent_layout, "Required Props (100% match)",
                                       all_props, hard.get('required_props', []), 'required_props')
        self._render_checklist_section(parent_layout, "Required Props Pool (random selection)",
                                       all_props, hard.get('required_props_pool', []), 'required_props_pool')
        self._render_checklist_section(parent_layout, "Prefers Props (high priority)",
                                       all_props, soft.get('prefers_props', []), 'prefers_props')
        self._render_checklist_section(parent_layout, "Excluded Props (hard ban)",
                                       all_props, hard.get('excludes_props', []), 'excludes_props')
        self._render_checklist_section(parent_layout, "Avoid Props (soft ban — 30% chance)",
                                       all_props, soft.get('avoid_props', []), 'avoid_props')

        self._render_section_header(parent_layout, "LIGHTING & WEATHER")
        all_lighting = self._load_all_tags_from_category("07_lighting")
        self._render_checklist_section(parent_layout, "Excluded Lighting Sources (hard ban)",
                                       all_lighting, hard.get('excludes_lighting_sources', []), 'excludes_lighting_sources')
        self._render_checklist_section(parent_layout, "Prefers Lighting (high priority)",
                                       all_lighting, soft.get('prefers_lighting_sources', []), 'prefers_lighting_sources')
        self._render_checklist_section(parent_layout, "Avoid Lighting Sources (soft ban)",
                                       all_lighting, soft.get('avoid_lighting_sources', []), 'avoid_lighting_sources')
        all_weather = self._load_all_tags_from_category("10_weather")
        self._render_checklist_section(parent_layout, "Excluded Weather (hard ban)",
                                       all_weather, hard.get('excludes_weather', []), 'excludes_weather')
        self._render_checklist_section(parent_layout, "Prefers Weather (high priority)",
                                       all_weather, soft.get('prefers_weather', []), 'prefers_weather')
        self._render_checklist_section(parent_layout, "Avoid Weather (soft ban)",
                                       all_weather, soft.get('avoid_weather', []), 'avoid_weather')

    def _render_action_editor(self, parent_layout, data: dict):
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})

        self._render_section_header(parent_layout, "LOCATIONS")
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(parent_layout, "Allowed Locations (Hard Whitelist)",
                                       all_locations, hard.get('allowed_locations', []), 'allowed_locations')
        self._render_checklist_section(parent_layout, "Excluded Locations (Hard Ban)",
                                       all_locations, hard.get('excluded_locations', []), 'excluded_locations')
        self._render_checklist_section(parent_layout, "Prefers Locations (Soft Priority)",
                                       all_locations, soft.get('prefers_locations', []), 'prefers_locations')
        self._render_checklist_section(parent_layout, "Avoid Locations (Soft Ban)",
                                       all_locations, soft.get('avoid_locations', []), 'avoid_locations')

        self._render_section_header(parent_layout, "POSES & EXPRESSIONS")
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent_layout, "Prefers Poses",
                                       all_poses, soft.get('prefers_poses', []), 'prefers_poses')
        all_expressions = self._load_all_tags_from_category("05_expression")
        self._render_checklist_section(parent_layout, "Prefers Expressions",
                                       all_expressions, soft.get('prefers_expressions', []), 'prefers_expressions')

        self._render_section_header(parent_layout, "PROPS")
        all_props = self._load_all_tags_from_category("09_props")
        self._render_checklist_section(parent_layout, "Required Props (100% match)",
                                       all_props, hard.get('required_props', []), 'required_props')
        self._render_checklist_section(parent_layout, "Required Props Pool (random selection)",
                                       all_props, hard.get('required_props_pool', []), 'required_props_pool')
        self._render_checklist_section(parent_layout, "Prefers Props (high priority)",
                                       all_props, soft.get('prefers_props', []), 'prefers_props')
        self._render_checklist_section(parent_layout, "Excluded Props (hard ban)",
                                       all_props, hard.get('excludes_props', []), 'excludes_props')
        self._render_checklist_section(parent_layout, "Avoid Props (soft ban)",
                                       all_props, soft.get('avoid_props', []), 'avoid_props')

        self._render_section_header(parent_layout, "ACTIONS (Mutually exclusive)")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent_layout, "Excludes Actions (hard ban)",
                                       all_actions, hard.get('excludes_actions', []), 'excludes_actions')
        self._render_checklist_section(parent_layout, "Avoid Actions (soft ban)",
                                       all_actions, soft.get('avoid_actions', []), 'avoid_actions')

    def _render_weather_editor(self, parent_layout, data: dict):
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})

        self._render_section_header(parent_layout, "LOCATIONS")
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(parent_layout, "Allowed Locations (Hard Whitelist)",
                                       all_locations, hard.get('allowed_locations', []), 'allowed_locations')
        self._render_checklist_section(parent_layout, "Excluded Locations (Hard Ban)",
                                       all_locations, hard.get('excluded_locations', []), 'excluded_locations')
        self._render_checklist_section(parent_layout, "Prefers Locations (Soft Priority)",
                                       all_locations, soft.get('prefers_locations', []), 'prefers_locations')
        self._render_checklist_section(parent_layout, "Avoid Locations (Soft Ban)",
                                       all_locations, soft.get('avoid_locations', []), 'avoid_locations')

        self._render_section_header(parent_layout, "ACTIONS")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent_layout, "Allowed Actions (Hard Whitelist)",
                                       all_actions, hard.get('allowed_actions', []), 'allowed_actions')
        self._render_checklist_section(parent_layout, "Excluded Actions (Hard Ban)",
                                       all_actions, hard.get('excludes_actions', []), 'excludes_actions')
        self._render_checklist_section(parent_layout, "Prefers Actions (Soft Priority)",
                                       all_actions, soft.get('prefers_actions', []), 'prefers_actions')
        self._render_checklist_section(parent_layout, "Avoid Actions (Soft Ban)",
                                       all_actions, soft.get('avoid_actions', []), 'avoid_actions')

        self._render_section_header(parent_layout, "LIGHTING")
        all_lighting = self._load_all_tags_from_category("07_lighting")
        self._render_checklist_section(parent_layout, "Excluded Lighting Sources (hard ban)",
                                       all_lighting, hard.get('excludes_lighting_sources', []), 'excludes_lighting_sources')
        self._render_checklist_section(parent_layout, "Prefers Lighting (high priority)",
                                       all_lighting, soft.get('prefers_lighting_sources', []), 'prefers_lighting_sources')
        self._render_checklist_section(parent_layout, "Avoid Lighting Sources (soft ban)",
                                       all_lighting, soft.get('avoid_lighting_sources', []), 'avoid_lighting_sources')

        self._render_section_header(parent_layout, "WEATHER (Self constraints)")
        all_weather = self._load_all_tags_from_category("10_weather")
        self._render_checklist_section(parent_layout, "Excludes Weather (hard ban)",
                                       all_weather, hard.get('excludes_weather', []), 'excludes_weather')
        self._render_checklist_section(parent_layout, "Prefers Weather (high priority)",
                                       all_weather, soft.get('prefers_weather', []), 'prefers_weather')
        self._render_checklist_section(parent_layout, "Avoid Weather (soft ban)",
                                       all_weather, soft.get('avoid_weather', []), 'avoid_weather')

    def _render_camera_editor(self, parent_layout, data: dict):
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})

        self._render_section_header(parent_layout, "LOCATIONS")
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(parent_layout, "Allowed Locations (Hard Whitelist)",
                                       all_locations, hard.get('allowed_locations', []), 'allowed_locations')
        self._render_checklist_section(parent_layout, "Excluded Locations (Hard Ban)",
                                       all_locations, hard.get('excluded_locations', []), 'excluded_locations')
        self._render_checklist_section(parent_layout, "Prefers Locations (Soft Priority)",
                                       all_locations, soft.get('prefers_locations', []), 'prefers_locations')
        self._render_checklist_section(parent_layout, "Avoid Locations (Soft Ban)",
                                       all_locations, soft.get('avoid_locations', []), 'avoid_locations')

        self._render_section_header(parent_layout, "ACTIONS")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent_layout, "Allowed Actions (Hard Whitelist)",
                                       all_actions, hard.get('allowed_actions', []), 'allowed_actions')
        self._render_checklist_section(parent_layout, "Excluded Actions (Hard Ban)",
                                       all_actions, hard.get('excludes_actions', []), 'excludes_actions')
        self._render_checklist_section(parent_layout, "Prefers Actions (Soft Priority)",
                                       all_actions, soft.get('prefers_actions', []), 'prefers_actions')
        self._render_checklist_section(parent_layout, "Avoid Actions (Soft Ban)",
                                       all_actions, soft.get('avoid_actions', []), 'avoid_actions')

        self._render_section_header(parent_layout, "POSES")
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent_layout, "Allowed Poses (Hard Whitelist)",
                                       all_poses, hard.get('allowed_poses', []), 'allowed_poses')
        self._render_checklist_section(parent_layout, "Excluded Poses (Hard Ban)",
                                       all_poses, hard.get('excludes_poses', []), 'excludes_poses')
        self._render_checklist_section(parent_layout, "Prefers Poses (Soft Priority)",
                                       all_poses, soft.get('prefers_poses', []), 'prefers_poses')
        self._render_checklist_section(parent_layout, "Avoid Poses (Soft Ban)",
                                       all_poses, soft.get('avoid_poses', []), 'avoid_poses')

        self._render_section_header(parent_layout, "CAMERA (Self constraints)")
        all_camera = self._load_all_tags_from_category("06_camera")
        self._render_checklist_section(parent_layout, "Excludes Camera (hard ban)",
                                       all_camera, hard.get('excludes_camera', []), 'excludes_camera')
        self._render_checklist_section(parent_layout, "Prefers Camera (high priority)",
                                       all_camera, soft.get('prefers_camera', []), 'prefers_camera')
        self._render_checklist_section(parent_layout, "Avoid Camera (soft ban)",
                                       all_camera, soft.get('avoid_camera', []), 'avoid_camera')

    def _render_location_type_editor(self, parent_layout, data: dict):
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})

        all_actions = sorted(self.scene_rules_data.get('actions', {}).keys())
        self._render_checklist_section(parent_layout, "Excludes Actions",
                                       all_actions, hard.get('excludes_actions', []), 'excludes_actions')
        self._render_checklist_section(parent_layout, "Prefers Actions",
                                       all_actions, soft.get('prefers_actions', []), 'prefers_actions')