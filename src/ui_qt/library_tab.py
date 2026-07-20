from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit,
                               QTabWidget, QTreeWidget, QTreeWidgetItem,
                               QScrollArea, QFrame, QGroupBox, QMessageBox,
                               QCheckBox, QApplication, QSplitter)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from pathlib import Path
import json


class LibraryTab(QWidget):
    """Вкладка редактирования библиотеки тегов и scene-rules (Qt версия)"""

    def __init__(
        self,
        project_root: Path,
        log_callback,
        parent=None
    ):
        super().__init__(parent)

        self.project_root = project_root
        self._log = log_callback

        # Состояние Tag Editor
        self.library_current_file: Path | None = None
        self.library_tags: list[str] = []
        self._tags_cache = {}

        # Состояние Scene Rules
        self.scene_rules_data = {}
        self.current_rule_file: str | None = None
        self._current_checkboxes = {}

        self._setup_ui()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Library"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Создаём QTabWidget для субвкладок
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Субвкладка 1: Tag Editor
        self.tag_editor_widget = QWidget()
        self._setup_tag_editor(self.tag_editor_widget)
        self.tab_widget.addTab(self.tag_editor_widget, "📚 Tag Editor")

        # Субвкладка 2: Scene Rules
        self.scene_rules_widget = QWidget()
        self._setup_scene_rules(self.scene_rules_widget)
        self.tab_widget.addTab(self.scene_rules_widget, "🎬 Scene Rules")

        main_layout.addWidget(self.tab_widget)

    # ═══════════════════════════════════════════════
    # TAG EDITOR
    # ═══════════════════════════════════════════════
    def _setup_tag_editor(self, widget: QWidget):
        """Настраивает субвкладку Tag Editor"""
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # === ЛЕВАЯ ПАНЕЛЬ: Дерево файлов ===
        left_widget = QWidget()
        left_widget.setMaximumWidth(400)
        left_widget.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("📚 Prompt Library"))

        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderHidden(True)
        self.library_tree.itemClicked.connect(self._on_library_item_clicked)
        left_layout.addWidget(self.library_tree)

        self._build_library_tree()

        # === ПРАВАЯ ПАНЕЛЬ: Редактор тегов ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.library_editor_title = QLabel("📝 Tag Editor (select a file)")
        self.library_editor_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self.library_editor_title)

        # Поиск
        search_layout = QHBoxLayout()
        self.library_search_entry = QLineEdit()
        self.library_search_entry.setPlaceholderText("🔍 Search tags...")
        self.library_search_entry.textChanged.connect(self._filter_library_tags)
        search_layout.addWidget(self.library_search_entry)

        clear_search_btn = QPushButton("Clear")
        clear_search_btn.clicked.connect(self._clear_library_search)
        search_layout.addWidget(clear_search_btn)
        right_layout.addLayout(search_layout)

        # Список тегов
        self.library_tags_container = QScrollArea()
        self.library_tags_container.setWidgetResizable(True)
        self.library_tags_container.setFrameShape(QFrame.NoFrame)

        tags_widget = QWidget()
        self.tags_layout = QVBoxLayout(tags_widget)
        self.tags_layout.setSpacing(2)
        self.tags_layout.addStretch()
        self.library_tags_container.setWidget(tags_widget)
        right_layout.addWidget(self.library_tags_container)

        # Добавление тега
        add_layout = QHBoxLayout()
        self.new_tag_entry = QLineEdit()
        self.new_tag_entry.setPlaceholderText("Enter new tag...")
        self.new_tag_entry.returnPressed.connect(self._add_library_tag)
        add_layout.addWidget(self.new_tag_entry)

        add_tag_btn = QPushButton("➕ Add Tag")
        add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        add_tag_btn.clicked.connect(self._add_library_tag)
        add_layout.addWidget(add_tag_btn)
        right_layout.addLayout(add_layout)

        # Добавляем панели
        layout.addWidget(left_widget)
        layout.addWidget(right_widget, 1)

    def _build_library_tree(self):
        """Строит дерево файлов из prompt-library"""
        self.library_tree.clear()

        library_dir = self.project_root / "prompt-library"
        if not library_dir.exists():
            item = QTreeWidgetItem(["⚠️ Папка не найдена"])
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

            if main_cat not in categories:
                categories[main_cat] = {}
            if sub_cat not in categories[main_cat]:
                categories[main_cat][sub_cat] = []
            categories[main_cat][sub_cat].append(txt_file)

        for main_cat, subcats in sorted(categories.items()):
            main_item = QTreeWidgetItem([f"{main_cat.replace('_', ' ').title()}"])
            main_item.setExpanded(False)

            for sub_cat, files in sorted(subcats.items()):
                sub_item = QTreeWidgetItem([f"{sub_cat.replace('_', ' ').title()}"])
                sub_item.setExpanded(False)

                for txt_file in files:
                    file_item = QTreeWidgetItem([f"📄 {txt_file.name}"])
                    file_item.setData(0, Qt.UserRole, str(txt_file))
                    sub_item.addChild(file_item)

                main_item.addChild(sub_item)

            self.library_tree.addTopLevelItem(main_item)

    def _on_library_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработчик клика на элемент дерева"""
        file_path_str = item.data(0, Qt.UserRole)
        if file_path_str:
            self._load_library_file(Path(file_path_str))

    def _load_library_file(self, file_path: Path):
        """Загружает теги из выбранного файла"""
        self.library_current_file = file_path
        self.library_tags = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.library_tags.append(line)
        except Exception as e:
            self._log(f"❌ Ошибка чтения {file_path}: {e}\n")
            return

        rel_path = file_path.relative_to(self.project_root / "prompt-library")
        self.library_editor_title.setText(f"📝 {rel_path} ({len(self.library_tags)} tags)")

        self._display_library_tags()
        self.library_search_entry.clear()

    def _display_library_tags(self, filter_text: str = ""):
        """Отображает теги в правой панели"""
        # Очищаем текущий список
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.library_tags:
            label = QLabel("(No tags in this file)")
            label.setStyleSheet("color: gray;")
            self.tags_layout.insertWidget(0, label)
            return

        filtered_tags = self.library_tags
        if filter_text:
            filter_lower = filter_text.lower()
            filtered_tags = [t for t in self.library_tags if filter_lower in t.lower()]

        if not filtered_tags:
            label = QLabel(f"(No tags match '{filter_text}')")
            label.setStyleSheet("color: gray;")
            self.tags_layout.insertWidget(0, label)
            return

        for tag in filtered_tags:
            tag_widget = QWidget()
            tag_layout = QHBoxLayout(tag_widget)
            tag_layout.setContentsMargins(5, 2, 5, 2)
            tag_layout.setSpacing(5)

            tag_label = QLabel(f"  • {tag}")
            tag_layout.addWidget(tag_label, 1)

            delete_btn = QPushButton("×")
            delete_btn.setFixedSize(25, 25)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #991b1b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, t=tag: self._delete_library_tag(t))
            tag_layout.addWidget(delete_btn)

            self.tags_layout.insertWidget(self.tags_layout.count() - 1, tag_widget)

    def _filter_library_tags(self, text: str):
        """Фильтрует теги по тексту поиска"""
        self._display_library_tags(text)

    def _clear_library_search(self):
        """Очищает поле поиска"""
        self.library_search_entry.clear()
        self._display_library_tags()

    def _add_library_tag(self):
        """Добавляет новый тег в файл"""
        if self.library_current_file is None:
            QMessageBox.warning(self, "Warning", "Сначала выберите файл")
            return

        new_tag = self.new_tag_entry.text().strip()
        if not new_tag:
            return

        if new_tag in self.library_tags:
            QMessageBox.warning(self, "Warning", f"Тег '{new_tag}' уже существует")
            return

        self.library_tags.append(new_tag)
        self.new_tag_entry.clear()
        self._save_library_file()
        self._display_library_tags()

        rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
        self.library_editor_title.setText(f"📝 {rel_path} ({len(self.library_tags)} tags)")
        self._log(f"➕ Добавлен тег: {new_tag}\n")

    def _delete_library_tag(self, tag: str):
        """Удаляет тег из файла"""
        if self.library_current_file is None:
            return

        if tag in self.library_tags:
            self.library_tags.remove(tag)
            self._save_library_file()

        filter_text = self.library_search_entry.text().strip()
        self._display_library_tags(filter_text)

        rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
        self.library_editor_title.setText(f"📝 {rel_path} ({len(self.library_tags)} tags)")
        self._log(f"🗑️ Удалён тег: {tag}\n")

    def _save_library_file(self):
        """Сохраняет теги обратно в файл"""
        if self.library_current_file is None:
            return

        try:
            with open(self.library_current_file, 'w', encoding='utf-8') as f:
                for tag in self.library_tags:
                    f.write(f"{tag}\n")

            cache_key = str(self.library_current_file)
            if cache_key in self._tags_cache:
                del self._tags_cache[cache_key]

            self._log(f"💾 Файл сохранён: {self.library_current_file.name}\n")
        except Exception as e:
            self._log(f"❌ Ошибка сохранения: {e}\n")
            QMessageBox.critical(self, "Error", f"Не удалось сохранить файл: {e}")

    # ═══════════════════════════════════════════════
    # SCENE RULES EDITOR (Полноценная версия)
    # ═══════════════════════════════════════════════

    def _setup_scene_rules(self, widget: QWidget):
        """Настраивает субвкладку Scene Rules с полноценным редактором"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # === ВЕРХНЯЯ ПАНЕЛЬ: Переключатели и кнопки ===
        top_layout = QHBoxLayout()

        self.auto_sync_check = QCheckBox("Auto-sync")
        self.auto_sync_check.setChecked(True)
        top_layout.addWidget(self.auto_sync_check)

        help_btn = QPushButton("?")
        help_btn.setFixedSize(25, 25)
        help_btn.clicked.connect(self._show_auto_sync_help)
        top_layout.addWidget(help_btn)

        top_layout.addStretch()

        reload_btn = QPushButton("🔄 Reload")
        reload_btn.clicked.connect(self._reload_scene_rules)
        top_layout.addWidget(reload_btn)

        validate_btn = QPushButton("✅ Validate")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        validate_btn.clicked.connect(self._validate_scene_rules_integrity)
        top_layout.addWidget(validate_btn)

        autofix_btn = QPushButton("🔧 Auto-fix")
        autofix_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        autofix_btn.clicked.connect(self._auto_fix_tag_format)
        top_layout.addWidget(autofix_btn)

        save_btn = QPushButton("💾 Save All")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        save_btn.clicked.connect(self._save_scene_rules)
        top_layout.addWidget(save_btn)

        layout.addLayout(top_layout)

        # === ОСНОВНОЙ КОНТЕНТ: Двухколоночный layout ===
        content_splitter = QSplitter(Qt.Horizontal)

        # Левая панель: список правил
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.scene_rules_tree = QTreeWidget()
        self.scene_rules_tree.setHeaderHidden(True)
        self.scene_rules_tree.itemClicked.connect(self._on_scene_rule_clicked)
        left_layout.addWidget(self.scene_rules_tree)

        # Правая панель: редактор
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.scene_rules_editor_scroll = QScrollArea()
        self.scene_rules_editor_scroll.setWidgetResizable(True)
        self.scene_rules_editor_scroll.setFrameShape(QFrame.NoFrame)

        self.scene_rules_editor_widget = QWidget()
        self.scene_rules_editor_layout = QVBoxLayout(self.scene_rules_editor_widget)
        self.scene_rules_editor_layout.setAlignment(Qt.AlignTop)

        # Заглушка
        placeholder = QLabel("👈 Выберите правило слева для редактирования")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        self.scene_rules_editor_layout.addWidget(placeholder)

        self.scene_rules_editor_scroll.setWidget(self.scene_rules_editor_widget)
        right_layout.addWidget(self.scene_rules_editor_scroll)

        # Добавляем в splitter
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)

        layout.addWidget(content_splitter, 1)

        # Загружаем данные
        self._load_scene_rules()
        self._build_scene_rules_tree()

    def _build_scene_rules_tree(self):
        """Строит дерево scene-rules с кнопками добавления для каждой категории"""
        self.scene_rules_tree.clear()

        if not self.scene_rules_data:
            item = QTreeWidgetItem(["(No rules loaded)"])
            self.scene_rules_tree.addTopLevelItem(item)
            return

        for category_name, rules in sorted(self.scene_rules_data.items()):
            cat_item = QTreeWidgetItem([f"{category_name.replace('_', ' ').title()} ({len(rules)})"])
            cat_item.setExpanded(True)

            # Кнопка добавления нового правила для этой категории
            add_item = QTreeWidgetItem(["➕ Add new rule..."])
            add_item.setData(0, Qt.UserRole, {'action': 'add', 'category': category_name})
            cat_item.addChild(add_item)

            for rule_name in sorted(rules.keys()):
                rule_item = QTreeWidgetItem([f"📄 {rule_name}"])
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
        """Обработчик клика на элемент дерева Scene Rules"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        action = data.get('action')

        if action == 'add':
            category = data.get('category')
            self._create_new_rule(category)
        elif action == 'select':
            category = data.get('category')
            rule_name = data.get('rule_name')
            self._select_scene_rule(category, rule_name)

    def _select_scene_rule(self, category: str, rule_name: str):
        """Загружает выбранное правило в редактор"""
        rule_data = self.scene_rules_data[category][rule_name]
        self.current_rule_file = rule_data['path']
        data = rule_data['data']
        meta = data.get('meta', {})

        self._log(f"📄 Редактирование: {category}/{rule_name}\n")

        # Очищаем редактор
        self._clear_scene_rules_editor()

        # Рендерим содержимое
        self._render_scene_rule_content(category, rule_name, data, meta)

    def _clear_scene_rules_editor(self):
        """Очищает правую панель редактора"""
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
        """Рендерит содержимое Scene Rule в правой панели"""
        # === Заголовок ===
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)

        title = QLabel(f"📝 {meta.get('display_name', rule_name)}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)

        subtitle = QLabel(f"({category}/{rule_name}.toml)")
        subtitle.setStyleSheet("color: gray60;")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        delete_btn = QPushButton("🗑️ Delete Rule")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #991b1b;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_scene_rule(category, rule_name))
        header_layout.addWidget(delete_btn)

        self.scene_rules_editor_layout.addWidget(header_frame)

        # === Секция Meta ===
        self._render_meta_section(meta, category)

        # === Секции в зависимости от категории ===
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
            placeholder = QLabel(f"📋 Редактор для категории '{category}' не реализован")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: gray; font-size: 12px; padding: 20px;")
            self.scene_rules_editor_layout.addWidget(placeholder)

    def _render_meta_section(self, meta: dict, category: str):
        """Рендерит секцию Meta Information (ID, Display Name, Type)"""
        meta_frame = QFrame()
        meta_frame.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        meta_layout = QVBoxLayout(meta_frame)
        meta_layout.setContentsMargins(15, 10, 15, 10)
        meta_layout.setSpacing(8)

        title = QLabel("🏷️ Meta Information")
        title.setStyleSheet("font-size: 13px; font-weight: bold;")
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

        # Type (только для locations)
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
        """Сохраняет изменения ID/Display Name/Type в TOML файл"""
        if not self.current_rule_file or not Path(self.current_rule_file).exists():
            return

        new_value = new_value.strip()
        if not new_value:
            return

        # Определяем текущую категорию и имя правила
        try:
            rel_path = Path(self.current_rule_file).relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) < 2:
                return
            category = parts[0]
            rule_name = parts[1].replace('.toml', '')
        except Exception:
            return

        # Загружаем текущие данные
        rule_data = self.scene_rules_data.get(category, {}).get(rule_name, {}).get('data', {})
        if not rule_data:
            return

        if 'meta' not in rule_data:
            rule_data['meta'] = {}

        old_value = rule_data['meta'].get(field, '')
        if old_value == new_value:
            return

        rule_data['meta'][field] = new_value

        # Сохраняем в файл
        try:
            import tomli_w
            with open(self.current_rule_file, 'wb') as f:
                tomli_w.dump(rule_data, f)
        except ImportError:
            self._write_toml_manually(Path(self.current_rule_file), rule_data)

        # Если изменился ID — переименовываем файл
        if field == 'id' and new_value != rule_name:
            safe_name = new_value.replace(' ', '_').lower()
            new_file_path = Path(self.current_rule_file).parent / f"{safe_name}.toml"
            if new_file_path.exists():
                self._log(f"⚠️ Файл с ID '{safe_name}' уже существует\n")
                QMessageBox.warning(self, "Warning", f"Rule with ID '{safe_name}' already exists!")
                return
            try:
                import shutil
                shutil.move(str(self.current_rule_file), str(new_file_path))
                self.current_rule_file = str(new_file_path)

                # Обновляем внутренние данные
                self.scene_rules_data[category][safe_name] = self.scene_rules_data[category].pop(rule_name)
                self.scene_rules_data[category][safe_name]['path'] = str(new_file_path)
                self.scene_rules_data[category][safe_name]['data']['meta']['id'] = safe_name

                # Перестраиваем список слева
                self._build_scene_rules_tree()
                self._log(f"✏️ ID изменён: {rule_name} → {safe_name}\n")
            except Exception as e:
                self._log(f"❌ Ошибка переименования: {e}\n")
                return
        else:
            self._log(f"💾 Meta сохранено: {field} = {new_value}\n")

    def _write_toml_manually(self, file_path: Path, data: dict):
        """Простая ручная запись TOML (fallback)"""
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
        """Создаёт новое правило"""
        new_name = f"new_{category.lower().replace(' ', '_')}_rule"

        # Проверяем уникальность имени
        if new_name in self.scene_rules_data.get(category, {}):
            counter = 1
            while f"{new_name}_{counter}" in self.scene_rules_data.get(category, {}):
                counter += 1
            new_name = f"{new_name}_{counter}"

        # Создаём файл
        rules_dir = self.project_root / "scene-rules" / category
        rules_dir.mkdir(parents=True, exist_ok=True)
        new_file_path = rules_dir / f"{new_name}.toml"

        # Базовая структура TOML
        new_data = {
            'meta': {
                'id': new_name,
                'display_name': new_name.replace('_', ' ').title(),
            },
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
            # Fallback: ручная запись
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(f'[meta]\nid = "{new_name}"\n')
                f.write(f'display_name = "{new_data["meta"]["display_name"]}"\n')
                if category == 'locations':
                    f.write('type = "indoor_private"\n')
                f.write("\n[soft_constraints]\n[hard_constraints]\n")
        except Exception as e:
            self._log(f"❌ Ошибка создания: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed: {e}")
            return

        # Добавляем в память
        if category not in self.scene_rules_data:
            self.scene_rules_data[category] = {}
        self.scene_rules_data[category][new_name] = {
            'path': str(new_file_path),
            'data': new_data
        }

        # Перестраиваем дерево
        self._build_scene_rules_tree()

        # Открываем новое правило
        self._select_scene_rule(category, new_name)
        self._log(f"➕ Создано новое правило: {category}/{new_name}\n")
        QMessageBox.information(self, "Success", f"New rule '{new_name}' created!")

    def _delete_scene_rule(self, category: str, rule_name: str):
        """Удаляет правило"""
        rule_path = self.project_root / "scene-rules" / category / f"{rule_name}.toml"
        if not rule_path.exists():
            self._log(f"⚠️ Файл не найден: {rule_path}\n")
            return

        reply = QMessageBox.question(
            self,
            "Delete Rule",
            f"Are you sure you want to delete rule '{rule_name}'?\n\n"
            f"📄 {category}/{rule_name}.toml\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            rule_path.unlink()

            # Удаляем из памяти
            if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                del self.scene_rules_data[category][rule_name]

            # Перестраиваем дерево
            self._build_scene_rules_tree()

            # Очищаем редактор
            self._clear_scene_rules_editor()
            placeholder = QLabel("👈 Выберите правило слева для редактирования")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: gray; font-size: 14px;")
            self.scene_rules_editor_layout.addWidget(placeholder)

            self.current_rule_file = None
            self._log(f"🗑️ Удалено правило: {category}/{rule_name}\n")
            QMessageBox.information(self, "Success", f"Rule '{rule_name}' deleted!")
        except Exception as e:
            self._log(f"❌ Ошибка удаления: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed: {e}")

    # ═══════════════════════════════════════════════
    # SCENE RULES: Вспомогательные методы
    # ═══════════════════════════════════════════════
    def _show_auto_sync_help(self):
        """Показывает справку о функции автосинхронизации"""
        help_text = (
            "🔄 Автосинхронизация связей\n\n"
            "Когда ВКЛЮЧЕНА:\n"
            "• Если вы добавляете действие 'reading' в список предпочтений локации 'library'\n"
            "• Программа автоматически добавит 'library' в список предпочтений действия 'reading'\n"
            "• Это обеспечивает консистентность данных\n\n"
            "Когда ВЫКЛЮЧЕНА:\n"
            "• Вы полностью контролируете все связи вручную\n"
            "• Изменения в одном файле не влияют на другие\n"
            "• Полезно для тонкой настройки или исправления ошибок\n\n"
            "Рекомендация:\n"
            "Оставьте включенной для большинства случаев."
        )
        QMessageBox.information(self, "Auto-sync Help", help_text)

    def _reload_scene_rules(self):
        """Перезагружает все TOML-файлы"""
        self._load_scene_rules()
        self._build_scene_rules_tree()
        self._log("🔄 Scene rules перезагружены\n")
        QMessageBox.information(self, "Success", "Scene rules reloaded!")

    def _save_scene_rules(self):
        """Сохраняет все изменения (заглушка для следующего шага)"""
        QMessageBox.information(self, "Info", "Save functionality coming in next step...")

    def _validate_scene_rules_integrity(self):
        """Проверяет целостность scene-rules (заглушка для следующего шага)"""
        QMessageBox.information(self, "Info", "Validate functionality coming in next step...")

    def _auto_fix_tag_format(self):
        """Автоматически исправляет формат тегов (заглушка для следующего шага)"""
        QMessageBox.information(self, "Info", "Auto-fix functionality coming in next step...")

    def _load_scene_rules(self):
        """Загружает все TOML-файлы из папки scene-rules"""
        self.scene_rules_data = {}
        rules_dir = self.project_root / "scene-rules"
        
        if not rules_dir.exists():
            self._log(f"⚠️ Папка scene-rules не найдена: {rules_dir}\n")
            return
        
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli
            except ImportError:
                self._log("❌ tomli/tomllib не установлен\n")
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
                        'path': str(toml_file),
                        'data': data
                    }
                except Exception as e:
                    self._log(f"❌ Ошибка чтения {toml_file.name}: {e}\n")
        
        total_files = sum(len(v) for v in self.scene_rules_data.values())
        self._log(f"✅ Загружено {total_files} scene-rules файлов\n")

    # ═══════════════════════════════════════════════
    # SCENE RULES: Рендеринг чекбоксов
    # ═══════════════════════════════════════════════
    def _render_section_header(self, parent_layout, title: str, emoji: str = "📋"):
        """Рендерит визуальный разделитель секции с заголовком"""
        separator_widget = QWidget()
        separator_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        separator_layout = QVBoxLayout(separator_widget)
        separator_layout.setContentsMargins(5, 20, 5, 5)
        separator_layout.setSpacing(5)
        
        # Верхняя линия
        top_line = QFrame()
        top_line.setFrameShape(QFrame.HLine)
        top_line.setStyleSheet("background-color: #555; max-height: 2px;")
        separator_layout.addWidget(top_line)
        
        # Заголовок
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 8, 15, 8)
        
        title_label = QLabel(f"{emoji} {title}")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        
        separator_layout.addWidget(header_frame)
        
        # Нижняя линия
        bottom_line = QFrame()
        bottom_line.setFrameShape(QFrame.HLine)
        bottom_line.setStyleSheet("background-color: #555; max-height: 2px;")
        separator_layout.addWidget(bottom_line)
        
        parent_layout.addWidget(separator_widget)

    def _load_all_tags_from_category(self, category: str) -> dict:
        """
        Загружает все теги из категории prompt-library с иерархической структурой.
        Использует кэш для предотвращения повторного сканирования.
        
        Returns:
            dict: {main_category: {sub_category: [list_of_tags]}}
        """
        # Инициализируем кэш при первом вызове
        if not hasattr(self, '_all_tags_category_cache'):
            self._all_tags_category_cache = {}
        
        # Возвращаем из кэша, если уже загружено
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
            
            # Загружаем теги из файла
            tags = []
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            tags.append(line)
            except Exception as e:
                self._log(f"❌ Ошибка чтения {txt_file}: {e}\n")
                continue
            
            if tags:
                if main_cat not in result:
                    result[main_cat] = {}
                result[main_cat][sub_cat] = tags
        
        self._all_tags_category_cache[category] = result
        return result

    def _render_checklist_section(self, parent_layout, title: str, all_items,
                                  selected_items: list, constraint_key: str,
                                  bg_color: str = "#333333"):
        """
        Рендерит сворачиваемую секцию с чекбоксами.
        
        Args:
            parent_layout: Layout, в который добавляем секцию
            title: Заголовок секции
            all_items: dict {main_cat: {sub_cat: [tags]}} или list [items]
            selected_items: list выбранных тегов
            constraint_key: ключ для сохранения (например, 'allowed_actions')
            bg_color: цвет фона секции
        """
        section_widget = QWidget()
        section_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 5px;
                margin: 5px;
            }}
        """)
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(5)
        
        # Инициализируем _current_checkboxes
        if not hasattr(self, '_current_checkboxes'):
            self._current_checkboxes = {}
        
        # Подсчёт выбранных / всего
        if isinstance(all_items, dict):
            total_count = 0
            selected_count = 0
            for main_cat, subcats in all_items.items():
                if isinstance(subcats, dict):
                    for subcat_name, tags in subcats.items():
                        total_count += len(tags)
                        selected_count += len([s for s in selected_items if s in tags])
                else:
                    total_count += len(subcats)
                    selected_count += len([s for s in selected_items if s in subcats])
        else:
            total_count = len(all_items) if all_items else 0
            selected_count = len([s for s in selected_items if s in (all_items or [])])
        
        # Заголовок с кнопкой сворачивания
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        toggle_btn = QPushButton(f"▶ {title} ({selected_count}/{total_count})")
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        header_layout.addWidget(toggle_btn)
        section_layout.addWidget(header_widget)
        
        # Контейнер для чекбоксов (изначально скрыт)
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
        
        # Создаём чекбоксы
        checkboxes = {}
        
        if isinstance(all_items, dict):
            for main_cat_name, subcats in sorted(all_items.items()):
                if not isinstance(subcats, dict):
                    continue
                for subcat_name, tags in sorted(subcats.items()):
                    subcat_label = QLabel(f"📁 {subcat_name.replace('_', ' ').title()}")
                    subcat_label.setStyleSheet("font-size: 11px; font-weight: bold; padding: 5px 0;")
                    checkbox_layout.addWidget(subcat_label)
                    
                    for tag in sorted(tags):
                        cb = QCheckBox(tag.replace('_', ' '))
                        cb.setChecked(tag in selected_items)
                        cb.setStyleSheet("padding: 2px 20px;")
                        cb.stateChanged.connect(
                            lambda state, t=tag, v=cb: self._on_checkbox_toggled(t, v, constraint_key, None, all_items)
                        )
                        checkbox_layout.addWidget(cb)
                        checkboxes[tag] = cb
        else:
            if all_items:
                for item in sorted(all_items):
                    cb = QCheckBox(item.replace('_', ' '))
                    cb.setChecked(item in selected_items)
                    cb.setStyleSheet("padding: 2px 10px;")
                    cb.stateChanged.connect(
                        lambda state, i=item, v=cb: self._on_checkbox_toggled(i, v, constraint_key, None, all_items)
                    )
                    checkbox_layout.addWidget(cb)
                    checkboxes[item] = cb
        
        checkbox_layout.addStretch()
        checkbox_scroll.setWidget(checkbox_widget)
        content_layout.addWidget(checkbox_scroll)
        
        section_layout.addWidget(content_widget)
        
        # Обработчик сворачивания
        def toggle_visibility():
            is_visible = content_widget.isVisible()
            content_widget.setVisible(not is_visible)
            if is_visible:
                toggle_btn.setText(f"▶ {title} ({selected_count}/{total_count})")
            else:
                toggle_btn.setText(f"▼ {title} ({selected_count}/{total_count})")
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        # Сохраняем чекбоксы
        self._current_checkboxes[constraint_key] = checkboxes
        
        parent_layout.addWidget(section_widget)

    def _on_checkbox_toggled(self, item: str, checkbox: QCheckBox, constraint_key: str, 
                             count_label, all_items):
        """Обработчик клика по чекбоксу с автосохранением"""
        is_checked = checkbox.isChecked()
        
        # Логируем действие
        self._log(f"{'☑' if is_checked else '☐'} {constraint_key}: {item}\n")
        
        # Автосохранение
        if self.current_rule_file:
            self._save_current_rule_silently()

    def _save_current_rule_silently(self):
        """Тихое сохранение текущего правила без всплывающих окон"""
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
            
            # Собираем изменения
            changes = self._collect_checkbox_changes()
            if not changes:
                return
            
            # Применяем изменения
            for category, rule_name, field, new_values in changes:
                target_section = 'hard_constraints' if 'excludes' in field or 'required' in field or 'allowed' in field else 'soft_constraints'
                if target_section not in data:
                    data[target_section] = {}
                data[target_section][field] = new_values
            
            # Сохраняем в файл
            with open(self.current_rule_file, 'wb') as f:
                tomli_w.dump(data, f)
            
            # Обновляем данные в памяти
            rel_path = Path(self.current_rule_file).relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) >= 2:
                category = parts[0]
                rule_name = parts[1].replace('.toml', '')
                if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                    self.scene_rules_data[category][rule_name]['data'] = data
        
        except Exception as e:
            self._log(f"⚠️ Автосохранение не удалось: {e}\n")

    def _collect_checkbox_changes(self) -> list:
        """Собирает все изменения из чекбоксов"""
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

    def _render_location_editor(self, parent_layout, data: dict):
        """Рендерит редактор для локации (locations/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # ═══════════════════════════════════════════════
        # СЕКЦИЯ: OUTFIT (Одежда)
        # ═══════════════════════════════════════════════
        self._render_section_header(parent_layout, "OUTFIT (Одежда)", "👗")
        all_outfit_styles = self._load_all_tags_from_category("02_clothing")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Outfit Styles (Hard Whitelist)",
            all_outfit_styles, hard.get('allowed_outfit_categories', []),
            'allowed_outfit_categories', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Outfit Styles (Hard Ban)",
            all_outfit_styles, hard.get('excludes_outfit_categories', []),
            'excludes_outfit_categories', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⭐ Preferred Outfit Styles (Soft Priority)",
            all_outfit_styles, soft.get('preferred_outfit_categories', []),
            'preferred_outfit_categories', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Outfit Styles (Soft Ban)",
            all_outfit_styles, soft.get('avoid_outfit_categories', []),
            'avoid_outfit_categories', bg_color="#2a2a2a"
        )
        
        # ═══════════════════════════════════════════════
        # СЕКЦИЯ: ACTIONS (Действия)
        # ═══════════════════════════════════════════════
        self._render_section_header(parent_layout, "ACTIONS (Действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Actions (Hard Whitelist)",
            all_actions, hard.get('allowed_actions', []),
            'allowed_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Actions (Hard Ban)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎬 Prefers Actions (Soft Priority)",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Actions (Soft Ban)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="#2a2a2a"
        )
        
        # ═══════════════════════════════════════════════
        # СЕКЦИЯ: PROPS (Реквизит)
        # ═══════════════════════════════════════════════
        self._render_section_header(parent_layout, "PROPS (Реквизит)", "📦")
        all_props = self._load_all_tags_from_category("09_props")
        
        self._render_checklist_section(
            parent_layout, "📦 Required Props (100% попадание)",
            all_props, hard.get('required_props', []),
            'required_props', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎲 Required Props Pool (случайный выбор)",
            all_props, hard.get('required_props_pool', []),
            'required_props_pool', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🧸 Prefers Props (высокий приоритет)",
            all_props, soft.get('prefers_props', []),
            'prefers_props', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Props (жёсткий бан)",
            all_props, hard.get('excludes_props', []),
            'excludes_props', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Props (мягкий бан - 30% шанс)",
            all_props, soft.get('avoid_props', []),
            'avoid_props', bg_color="#2a2a2a"
        )
        
        # ═══════════════════════════════════════════════
        # СЕКЦИЯ: LIGHTING & WEATHER (Освещение и Погода)
        # ═══════════════════════════════════════════════
        self._render_section_header(parent_layout, "LIGHTING & WEATHER (Освещение и Погода)", "🌤️")
        all_lighting = self._load_all_tags_from_category("07_lighting")
        
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Lighting Sources (жёсткий бан)",
            all_lighting, hard.get('excludes_lighting_sources', []),
            'excludes_lighting_sources', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "💡 Prefers Lighting (высокий приоритет)",
            all_lighting, soft.get('prefers_lighting_sources', []),
            'prefers_lighting_sources', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Lighting Sources (мягкий бан)",
            all_lighting, soft.get('avoid_lighting_sources', []),
            'avoid_lighting_sources', bg_color="#2a2a2a"
        )
        
        all_weather = self._load_all_tags_from_category("10_weather")
        
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Weather (жёсткий бан)",
            all_weather, hard.get('excludes_weather', []),
            'excludes_weather', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🌦️ Prefers Weather (высокий приоритет)",
            all_weather, soft.get('prefers_weather', []),
            'prefers_weather', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Weather (мягкий бан)",
            all_weather, soft.get('avoid_weather', []),
            'avoid_weather', bg_color="#2a2a2a"
        )

    def _render_action_editor(self, parent_layout, data: dict):
        """Рендерит редактор для действия (actions/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # СЕКЦИЯ: LOCATIONS (Локации)
        self._render_section_header(parent_layout, "LOCATIONS (Локации)", "📍")
        all_locations = self._load_all_tags_from_category("08_location")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Locations (Hard Whitelist)",
            all_locations, hard.get('allowed_locations', []),
            'allowed_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Locations (Hard Ban)",
            all_locations, hard.get('excluded_locations', []),
            'excluded_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "📍 Prefers Locations (Soft Priority)",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Locations (Soft Ban)",
            all_locations, soft.get('avoid_locations', []),
            'avoid_locations', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: POSES & EXPRESSIONS (Позы и Эмоции)
        self._render_section_header(parent_layout, "POSES & EXPRESSIONS (Позы и Эмоции)", "🎭")
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent_layout, "🎭 Prefers Poses",
            all_poses, soft.get('prefers_poses', []),
            'prefers_poses', bg_color="#2a2a2a"
        )
        
        all_expressions = self._load_all_tags_from_category("05_expression")
        self._render_checklist_section(
            parent_layout, "😊 Prefers Expressions",
            all_expressions, soft.get('prefers_expressions', []),
            'prefers_expressions', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: PROPS (Реквизит)
        self._render_section_header(parent_layout, "PROPS (Реквизит)", "📦")
        all_props = self._load_all_tags_from_category("09_props")
        
        self._render_checklist_section(
            parent_layout, "📦 Required Props (100% попадание)",
            all_props, hard.get('required_props', []),
            'required_props', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎲 Required Props Pool (случайный выбор)",
            all_props, hard.get('required_props_pool', []),
            'required_props_pool', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🧸 Prefers Props (высокий приоритет)",
            all_props, soft.get('prefers_props', []),
            'prefers_props', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Props (жёсткий бан)",
            all_props, hard.get('excludes_props', []),
            'excludes_props', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Props (мягкий бан - 30% шанс)",
            all_props, soft.get('avoid_props', []),
            'avoid_props', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: ACTIONS (Взаимоисключающие действия)
        self._render_section_header(parent_layout, "ACTIONS (Взаимоисключающие действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        
        self._render_checklist_section(
            parent_layout, "🚫 Excludes Actions (жёсткий бан)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Actions (мягкий бан)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="#2a2a2a"
        )

    def _render_weather_editor(self, parent_layout, data: dict):
        """Рендерит редактор для погоды (weather/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # СЕКЦИЯ: LOCATIONS (Локации)
        self._render_section_header(parent_layout, "LOCATIONS (Локации)", "📍")
        all_locations = self._load_all_tags_from_category("08_location")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Locations (Hard Whitelist)",
            all_locations, hard.get('allowed_locations', []),
            'allowed_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Locations (Hard Ban)",
            all_locations, hard.get('excluded_locations', []),
            'excluded_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "📍 Prefers Locations (Soft Priority)",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Locations (Soft Ban)",
            all_locations, soft.get('avoid_locations', []),
            'avoid_locations', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: ACTIONS (Действия)
        self._render_section_header(parent_layout, "ACTIONS (Действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Actions (Hard Whitelist)",
            all_actions, hard.get('allowed_actions', []),
            'allowed_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Actions (Hard Ban)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎬 Prefers Actions (Soft Priority)",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Actions (Soft Ban)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: LIGHTING (Освещение)
        self._render_section_header(parent_layout, "LIGHTING (Освещение)", "💡")
        all_lighting = self._load_all_tags_from_category("07_lighting")
        
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Lighting Sources (жёсткий бан)",
            all_lighting, hard.get('excludes_lighting_sources', []),
            'excludes_lighting_sources', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "💡 Prefers Lighting (высокий приоритет)",
            all_lighting, soft.get('prefers_lighting_sources', []),
            'prefers_lighting_sources', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Lighting Sources (мягкий бан)",
            all_lighting, soft.get('avoid_lighting_sources', []),
            'avoid_lighting_sources', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: WEATHER (Собственные ограничения)
        self._render_section_header(parent_layout, "WEATHER (Собственные ограничения)", "🌦️")
        all_weather = self._load_all_tags_from_category("10_weather")
        
        self._render_checklist_section(
            parent_layout, "🚫 Excludes Weather (жёсткий бан)",
            all_weather, hard.get('excludes_weather', []),
            'excludes_weather', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🌦️ Prefers Weather (высокий приоритет)",
            all_weather, soft.get('prefers_weather', []),
            'prefers_weather', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Weather (мягкий бан)",
            all_weather, soft.get('avoid_weather', []),
            'avoid_weather', bg_color="#2a2a2a"
        )

    def _render_camera_editor(self, parent_layout, data: dict):
        """Рендерит редактор для камеры (camera/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # СЕКЦИЯ: LOCATIONS (Локации)
        self._render_section_header(parent_layout, "LOCATIONS (Локации)", "📍")
        all_locations = self._load_all_tags_from_category("08_location")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Locations (Hard Whitelist)",
            all_locations, hard.get('allowed_locations', []),
            'allowed_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Locations (Hard Ban)",
            all_locations, hard.get('excluded_locations', []),
            'excluded_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "📍 Prefers Locations (Soft Priority)",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Locations (Soft Ban)",
            all_locations, soft.get('avoid_locations', []),
            'avoid_locations', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: ACTIONS (Действия)
        self._render_section_header(parent_layout, "ACTIONS (Действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Actions (Hard Whitelist)",
            all_actions, hard.get('allowed_actions', []),
            'allowed_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Actions (Hard Ban)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎬 Prefers Actions (Soft Priority)",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Actions (Soft Ban)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: POSES (Позы)
        self._render_section_header(parent_layout, "POSES (Позы)", "🎭")
        all_poses = self._load_all_tags_from_category("03_pose")
        
        self._render_checklist_section(
            parent_layout, "✅ Allowed Poses (Hard Whitelist)",
            all_poses, hard.get('allowed_poses', []),
            'allowed_poses', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🚫 Excluded Poses (Hard Ban)",
            all_poses, hard.get('excludes_poses', []),
            'excludes_poses', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎭 Prefers Poses (Soft Priority)",
            all_poses, soft.get('prefers_poses', []),
            'prefers_poses', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Poses (Soft Ban)",
            all_poses, soft.get('avoid_poses', []),
            'avoid_poses', bg_color="#2a2a2a"
        )
        
        # СЕКЦИЯ: CAMERA (Собственные ограничения)
        self._render_section_header(parent_layout, "CAMERA (Собственные ограничения)", "📸")
        all_camera = self._load_all_tags_from_category("06_camera")
        
        self._render_checklist_section(
            parent_layout, "🚫 Excludes Camera (жёсткий бан)",
            all_camera, hard.get('excludes_camera', []),
            'excludes_camera', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "📸 Prefers Camera (высокий приоритет)",
            all_camera, soft.get('prefers_camera', []),
            'prefers_camera', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "⚠️ Avoid Camera (мягкий бан)",
            all_camera, soft.get('avoid_camera', []),
            'avoid_camera', bg_color="#807171"
        )

    def _render_location_type_editor(self, parent_layout, data: dict):
        """Рендерит редактор для типа локации (location_types/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # Для location_types используем только имена правил из actions (не теги)
        all_actions = sorted(self.scene_rules_data.get('actions', {}).keys())
        
        self._render_checklist_section(
            parent_layout, "🚫 Excludes Actions",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="#2a2a2a"
        )
        self._render_checklist_section(
            parent_layout, "🎬 Prefers Actions",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="#2a2a2a"
        )