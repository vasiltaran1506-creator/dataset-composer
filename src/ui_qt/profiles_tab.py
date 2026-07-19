from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit,
                               QTabWidget, QTreeWidget, QTreeWidgetItem,
                               QScrollArea, QFrame, QGroupBox, QMessageBox,
                               QComboBox, QFileDialog, QInputDialog,
                               QSplitter, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import yaml
import shutil


class ProfilesTab(QWidget):
    """Вкладка редактирования профилей персонажей (Qt версия)"""

    def __init__(
        self,
        project_root: Path,
        profiles_directory: Path,
        settings_manager,
        log_callback,
        parent=None
    ):
        super().__init__(parent)
        
        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.settings_manager = settings_manager
        self._log = log_callback
        
        # Состояние
        self.current_profile_name: str | None = None
        self.profile_character_data: dict = {}
        
        # DNA
        self.selected_dna_tags: list[dict] = []
        self.dna_tag_ui_elements: dict[str, dict] = {}

        # Outfits
        self.selected_wardrobe_tags: list[dict] = []
        self.tag_ui_elements: dict[str, dict] = {}

        # Personality
        self.preferred_personality_tags: list[dict] = []
        self.avoided_personality_tags: list[dict] = []
        self.personality_tag_ui_elements: dict[str, dict] = {}

        # Signature
        self.signature_props: list[dict] = []
        self.hair_rules_data: dict = {'default': 'hair down', 'conditional': []}
        self._popup_selected_tags: set[str] = set()
        self._popup_selected_actions: set[str] = set()
        
        # Кэш
        self._tags_cache = {}
        
        self._setup_ui()
        self._refresh_profiles_list()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Profiles"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Используем QSplitter для левой и правой панелей
        splitter = QSplitter(Qt.Horizontal)
        
        # === ЛЕВАЯ ПАНЕЛЬ: Список профилей ===
        left_widget = QWidget()
        left_widget.setMaximumWidth(350)
        left_widget.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("📋 Characters"))
        
        # Список профилей
        self.profiles_list = QTreeWidget()
        self.profiles_list.setHeaderHidden(True)
        self.profiles_list.itemClicked.connect(self._on_profile_clicked)
        left_layout.addWidget(self.profiles_list)
        
        # Кнопки управления
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        new_btn = QPushButton("➕ New")
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        new_btn.clicked.connect(self._create_new_profile)
        buttons_layout.addWidget(new_btn)
        
        import_btn = QPushButton("📥 Import")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        import_btn.clicked.connect(self._import_profile)
        buttons_layout.addWidget(import_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #991b1b;
            }
        """)
        delete_btn.clicked.connect(self._delete_profile)
        buttons_layout.addWidget(delete_btn)
        
        left_layout.addWidget(buttons_frame)
        
        # === ПРАВАЯ ПАНЕЛЬ: Редактор ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.editor_title = QLabel("👤 Editing: (no selection)")
        self.editor_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(self.editor_title)
        
        self.edit_name_btn = QPushButton("✏️")
        self.edit_name_btn.setFixedSize(35, 30)
        self.edit_name_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: gray;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        self.edit_name_btn.clicked.connect(self._edit_profile_name)
        title_layout.addWidget(self.edit_name_btn)
        
        title_layout.addStretch()
        
        save_btn = QPushButton("💾 Save Profile")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        save_btn.clicked.connect(self._save_profile)
        title_layout.addWidget(save_btn)
        
        right_layout.addWidget(title_frame)
        
        # Субвкладки редактора
        self.editor_tabview = QTabWidget()
        self.editor_tabview.setDocumentMode(True)
        
        # Создаём субвкладки
        self.dna_widget = QWidget()
        self._setup_dna_tab(self.dna_widget)
        self.editor_tabview.addTab(self.dna_widget, "🧬 DNA")
        
        # Outfits
        outfits_widget = QWidget()
        self._setup_outfits_tab(outfits_widget)
        self.editor_tabview.addTab(outfits_widget, "👗 Outfits")
        
        # Personality
        personality_widget = QWidget()
        self._setup_personality_tab(personality_widget)
        self.editor_tabview.addTab(personality_widget, "🎭 Personality")
        
        # Signature
        signature_widget = QWidget()
        self._setup_signature_tab(signature_widget)
        self.editor_tabview.addTab(signature_widget, "✨ Signature")
        
        atmosphere_widget = QWidget()
        atmosphere_layout = QVBoxLayout(atmosphere_widget)
        atmosphere_layout.addWidget(QLabel("🌍 Atmosphere — coming soon..."))
        self.editor_tabview.addTab(atmosphere_widget, "🌍 Atmosphere")
        
        custom_widget = QWidget()
        custom_layout = QVBoxLayout(custom_widget)
        custom_layout.addWidget(QLabel("✍️ Custom — coming soon..."))
        self.editor_tabview.addTab(custom_widget, "✍️ Custom")
        
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.addWidget(QLabel("📄 Preview — coming soon..."))
        self.editor_tabview.addTab(preview_widget, "📄 Preview")
        
        right_layout.addWidget(self.editor_tabview)
        
        # Добавляем панели в splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)

    def _setup_dna_tab(self, widget: QWidget):
        """Настраивает субвкладку DNA"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        layout.addWidget(QLabel("🧬 Character DNA"))
        
        # Дерево DNA
        self.dna_tree_frame = QScrollArea()
        self.dna_tree_frame.setWidgetResizable(True)
        self.dna_tree_frame.setFrameShape(QFrame.NoFrame)
        
        dna_tree_widget = QWidget()
        self.dna_tree_layout = QVBoxLayout(dna_tree_widget)
        self.dna_tree_layout.setSpacing(2)
        
        self._build_dna_tree()
        
        self.dna_tree_frame.setWidget(dna_tree_widget)
        layout.addWidget(self.dna_tree_frame, 1)
        
        # Выбранные DNA теги
        selected_frame = QGroupBox("✅ Selected DNA Tags")
        selected_layout = QVBoxLayout(selected_frame)
        
        self.selected_dna_tags_container = QScrollArea()
        self.selected_dna_tags_container.setWidgetResizable(True)
        self.selected_dna_tags_container.setMaximumHeight(150)
        self.selected_dna_tags_container.setFrameShape(QFrame.NoFrame)
        
        selected_tags_widget = QWidget()
        self.selected_dna_tags_layout = QHBoxLayout(selected_tags_widget)
        self.selected_dna_tags_layout.setSpacing(5)
        self.selected_dna_tags_layout.addStretch()
        
        self.selected_dna_tags_container.setWidget(selected_tags_widget)
        selected_layout.addWidget(self.selected_dna_tags_container)
        
        layout.addWidget(selected_frame)
        
        self._refresh_selected_dna_tags_display()

    def _setup_outfits_tab(self, widget: QWidget):
        """Настраивает субвкладку Outfits"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        layout.addWidget(QLabel("👗 Wardrobe (Whitelist)"))
        
        # Дерево одежды
        self.wardrobe_tree_frame = QScrollArea()
        self.wardrobe_tree_frame.setWidgetResizable(True)
        self.wardrobe_tree_frame.setFrameShape(QFrame.NoFrame)
        
        wardrobe_tree_widget = QWidget()
        self.wardrobe_tree_layout = QVBoxLayout(wardrobe_tree_widget)
        self.wardrobe_tree_layout.setSpacing(2)
        
        self._build_wardrobe_tree()
        
        self.wardrobe_tree_frame.setWidget(wardrobe_tree_widget)
        layout.addWidget(self.wardrobe_tree_frame, 1)
        
        # Выбранные теги одежды
        selected_frame = QGroupBox("✅ Selected Wardrobe Tags")
        selected_layout = QVBoxLayout(selected_frame)
        
        self.selected_tags_container = QScrollArea()
        self.selected_tags_container.setWidgetResizable(True)
        self.selected_tags_container.setMaximumHeight(150)
        self.selected_tags_container.setFrameShape(QFrame.NoFrame)
        
        selected_tags_widget = QWidget()
        self.selected_tags_layout = QHBoxLayout(selected_tags_widget)
        self.selected_tags_layout.setSpacing(5)
        self.selected_tags_layout.addStretch()
        
        self.selected_tags_container.setWidget(selected_tags_widget)
        selected_layout.addWidget(self.selected_tags_container)
        
        layout.addWidget(selected_frame)
        
        self._refresh_selected_tags_display()

    def _build_dna_tree(self):
        """Строит дерево DNA"""
        # Очищаем
        while self.dna_tree_layout.count():
            item = self.dna_tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.dna_tag_ui_elements = {}
        
        # Категории DNA
        dna_categories = [
            ("🧬 Body Type", "01_character/body/type.txt"),
            ("🎭 Body Features", "01_character/body/features.txt"),
            ("👁️ Eye Color", "01_character/eyes/color.txt"),
            ("👁️ Eye Shape", "01_character/eyes/shape.txt"),
            ("🎭 Face Features", "01_character/face/features.txt"),
            ("💇 Hair Style", "01_character/hair/style.txt"),
            ("💇 Hair Color", "01_character/hair/color.txt"),
            ("💇 Hair Length", "01_character/hair/length.txt"),
            ("🧴 Skin Tone", "01_character/skin/tone.txt"),
        ]
        
        for cat_name, cat_file in dna_categories:
            self._create_dna_category(cat_name, cat_file)
        
        self.dna_tree_layout.addStretch()

    def _create_dna_category(self, cat_name: str, cat_file: str):
        """Создаёт раскрывающуюся категорию DNA"""
        cat_frame = QWidget()
        cat_frame.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(0, 2, 0, 2)
        cat_layout.setSpacing(0)
        
        # Кнопка-заголовок категории
        toggle_btn = QPushButton(f"➤ {cat_name}")
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-weight: bold;
                padding: 8px;
                text-align: left;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        cat_layout.addWidget(toggle_btn)
        
        # Контейнер для тегов (изначально скрыт)
        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)
        
        # Загружаем теги
        tags = self._load_tags_from_library(cat_file)
        for tag in tags:
            tag_key = f"dna::{cat_name}::{tag}"
            tag_row = QWidget()
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)
            
            tag_label = QLabel(f"  • {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)
            
            action_btn = QPushButton("+")
            action_btn.setFixedSize(30, 25)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
            action_btn.clicked.connect(
                lambda checked, t=tag, cn=cat_name, tk=tag_key: self._toggle_dna_tag(t, cn, tk)
            )
            tag_row_layout.addWidget(action_btn)
            
            tags_layout.addWidget(tag_row)
            
            self.dna_tag_ui_elements[tag_key] = {
                'label': tag_label, 'button': action_btn,
                'tag': tag, 'category': cat_name
            }
        
        tags_layout.addStretch()
        cat_layout.addWidget(tags_frame)
        
        # Обработчик сворачивания
        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            if is_visible:
                toggle_btn.setText(f"➤ {cat_name}")
            else:
                toggle_btn.setText(f"▼ {cat_name}")
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        self.dna_tree_layout.addWidget(cat_frame)

    def _toggle_dna_tag(self, tag: str, category: str, tag_key: str):
        """Добавляет/убирает DNA-тег из выбранных"""
        if tag_key not in self.dna_tag_ui_elements:
            return
        
        tag_entry = {'tag': tag, 'category': category}
        ui = self.dna_tag_ui_elements[tag_key]
        
        if tag_entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(tag_entry)
            ui['label'].setStyleSheet("color: #e0e0e0;")
            ui['button'].setText("+")
            ui['button'].setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
        else:
            self.selected_dna_tags.append(tag_entry)
            ui['label'].setStyleSheet("color: #22c55e;")
            ui['button'].setText("-")
            ui['button'].setStyleSheet("""
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
        
        self._refresh_selected_dna_tags_display()

    def _refresh_selected_dna_tags_display(self):
        """Отрисовывает chips с выбранными DNA-тегами"""
        # Очищаем
        while self.selected_dna_tags_layout.count() > 1:
            item = self.selected_dna_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.selected_dna_tags:
            label = QLabel("(No DNA tags selected — разверните категории и нажмите [+])")
            label.setStyleSheet("color: gray;")
            self.selected_dna_tags_layout.insertWidget(0, label)
            return
        
        for te in self.selected_dna_tags:
            chip = QWidget()
            chip.setStyleSheet("""
                QWidget {
                    background-color: #404040;
                    border-radius: 15px;
                }
            """)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 5, 4)
            chip_layout.setSpacing(5)
            
            chip_label = QLabel(f"  {te['tag'].replace('_', ' ')}  ")
            chip_label.setStyleSheet("font-size: 11px;")
            chip_layout.addWidget(chip_label)
            
            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(22, 22)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-weight: bold;
                    border-radius: 11px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
            remove_btn.clicked.connect(lambda checked, te=te: self._remove_dna_tag_from_chip(te))
            chip_layout.addWidget(remove_btn)
            
            self.selected_dna_tags_layout.insertWidget(
                self.selected_dna_tags_layout.count() - 1, chip
            )

    def _remove_dna_tag_from_chip(self, tag_entry: dict):
        """Удаляет DNA-тег через клик на крестик в chip"""
        if tag_entry not in self.selected_dna_tags:
            return
        
        self.selected_dna_tags.remove(tag_entry)
        tag_key = f"dna::{tag_entry['category']}::{tag_entry['tag']}"
        
        if tag_key in self.dna_tag_ui_elements:
            ui = self.dna_tag_ui_elements[tag_key]
            ui['label'].setStyleSheet("color: #e0e0e0;")
            ui['button'].setText("+")
            ui['button'].setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
        
        self._refresh_selected_dna_tags_display()

    def _build_wardrobe_tree(self):
        """Строит дерево одежды из prompt-library/02_clothing"""
        # Очищаем
        while self.wardrobe_tree_layout.count():
            item = self.wardrobe_tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.tag_ui_elements = {}
        
        clothing_dir = self.project_root / "prompt-library" / "02_clothing"
        if not clothing_dir.exists():
            return
        
        categories = {}
        for txt_file in sorted(clothing_dir.rglob("*.txt")):
            parts = txt_file.relative_to(clothing_dir).parts
            if len(parts) >= 2:
                main_cat = parts[0]
                sub_cat = parts[1].replace('.txt', '')
                if main_cat not in categories:
                    categories[main_cat] = {}
                categories[main_cat][sub_cat] = txt_file
        
        # Порядок категорий
        ORDER = ['full_body', 'topwear', 'bottomwear', 'legwear', 'footwear', 'underwear', 'accessories']
        
        def sort_key(cat):
            try:
                return ORDER.index(cat.lower())
            except ValueError:
                return 999
        
        for main_cat in sorted(categories.keys(), key=sort_key):
            self._create_wardrobe_category(main_cat, categories[main_cat])
        
        self.wardrobe_tree_layout.addStretch()

    def _create_wardrobe_category(self, main_cat: str, subcats: dict):
        """Создаёт главную категорию одежды"""
        cat_frame = QWidget()
        cat_frame.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(0, 2, 0, 2)
        cat_layout.setSpacing(0)
        
        # Кнопка-заголовок категории
        toggle_btn = QPushButton(f"➤ {main_cat.replace('_', ' ').title()}")
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-weight: bold;
                padding: 8px;
                text-align: left;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        cat_layout.addWidget(toggle_btn)
        
        # Контейнер для подкатегорий (изначально скрыт)
        subcats_frame = QWidget()
        subcats_frame.setVisible(False)
        subcats_layout = QVBoxLayout(subcats_frame)
        subcats_layout.setContentsMargins(20, 5, 0, 5)
        subcats_layout.setSpacing(1)
        
        for sub_cat, file_path in subcats.items():
            self._create_wardrobe_subcategory(subcats_layout, main_cat, sub_cat, file_path)
        
        subcats_layout.addStretch()
        cat_layout.addWidget(subcats_frame)
        
        # Обработчик сворачивания
        def toggle_visibility():
            is_visible = subcats_frame.isVisible()
            subcats_frame.setVisible(not is_visible)
            if is_visible:
                toggle_btn.setText(f"➤ {main_cat.replace('_', ' ').title()}")
            else:
                toggle_btn.setText(f"▼ {main_cat.replace('_', ' ').title()}")
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        self.wardrobe_tree_layout.addWidget(cat_frame)

    def _create_wardrobe_subcategory(self, parent_layout, main_cat: str, sub_cat: str, file_path: Path):
        """Создаёт подкатегорию одежды"""
        sub_frame = QWidget()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(0, 1, 0, 1)
        sub_layout.setSpacing(0)
        
        # Кнопка-заголовок подкатегории
        toggle_btn = QPushButton(f"  ➤ {sub_cat.replace('_', ' ').title()}")
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #353535;
                color: #cccccc;
                padding: 6px;
                text-align: left;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
        """)
        sub_layout.addWidget(toggle_btn)
        
        # Контейнер для тегов (изначально скрыт)
        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)
        
        # Загружаем теги
        tags = self._load_tags_from_file(file_path)
        for tag in tags:
            tag_key = f"{sub_cat}::{tag}"
            tag_row = QWidget()
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)
            
            tag_label = QLabel(f"    • {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)
            
            action_btn = QPushButton("+")
            action_btn.setFixedSize(30, 25)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
            action_btn.clicked.connect(
                lambda checked, t=tag, sc=sub_cat, tk=tag_key: self._toggle_wardrobe_tag(t, sc, tk)
            )
            tag_row_layout.addWidget(action_btn)
            
            tags_layout.addWidget(tag_row)
            
            self.tag_ui_elements[tag_key] = {
                'label': tag_label, 'button': action_btn,
                'tag': tag, 'subcategory': sub_cat
            }
        
        tags_layout.addStretch()
        sub_layout.addWidget(tags_frame)
        
        # Обработчик сворачивания
        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            if is_visible:
                toggle_btn.setText(f"  ➤ {sub_cat.replace('_', ' ').title()}")
            else:
                toggle_btn.setText(f"  ▼ {sub_cat.replace('_', ' ').title()}")
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        parent_layout.addWidget(sub_frame)

    def _toggle_wardrobe_tag(self, tag: str, subcategory: str, tag_key: str):
        """Добавляет/убирает тег одежды из whitelist"""
        if tag_key not in self.tag_ui_elements:
            return
        
        tag_entry = {'tag': tag, 'subcategory': subcategory}
        ui = self.tag_ui_elements[tag_key]
        
        if tag_entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(tag_entry)
            ui['label'].setStyleSheet("color: #e0e0e0;")
            ui['button'].setText("+")
            ui['button'].setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
        else:
            self.selected_wardrobe_tags.append(tag_entry)
            ui['label'].setStyleSheet("color: #22c55e;")
            ui['button'].setText("-")
            ui['button'].setStyleSheet("""
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
        
        self._refresh_selected_tags_display()

    def _refresh_selected_tags_display(self):
        """Отрисовывает chips с выбранными тегами одежды"""
        # Очищаем
        while self.selected_tags_layout.count() > 1:
            item = self.selected_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.selected_wardrobe_tags:
            label = QLabel("(No tags selected)")
            label.setStyleSheet("color: gray;")
            self.selected_tags_layout.insertWidget(0, label)
            return
        
        for te in self.selected_wardrobe_tags:
            chip = QWidget()
            chip.setStyleSheet("""
                QWidget {
                    background-color: #404040;
                    border-radius: 15px;
                }
            """)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 5, 4)
            chip_layout.setSpacing(5)
            
            chip_label = QLabel(f"  {te['tag'].replace('_', ' ')}  ")
            chip_label.setStyleSheet("font-size: 11px;")
            chip_layout.addWidget(chip_label)
            
            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(22, 22)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-weight: bold;
                    border-radius: 11px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
            remove_btn.clicked.connect(lambda checked, te=te: self._remove_tag_from_chip(te))
            chip_layout.addWidget(remove_btn)
            
            self.selected_tags_layout.insertWidget(
                self.selected_tags_layout.count() - 1, chip
            )

    def _remove_tag_from_chip(self, tag_entry: dict):
        """Удаляет тег одежды через крестик в chip"""
        if tag_entry not in self.selected_wardrobe_tags:
            return
        
        self.selected_wardrobe_tags.remove(tag_entry)
        tag_key = f"{tag_entry['subcategory']}::{tag_entry['tag']}"
        
        if tag_key in self.tag_ui_elements:
            ui = self.tag_ui_elements[tag_key]
            ui['label'].setStyleSheet("color: #e0e0e0;")
            ui['button'].setText("+")
            ui['button'].setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
        
        self._refresh_selected_tags_display()

    def _setup_personality_tab(self, widget: QWidget):
        """Настраивает субвкладку Personality"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        layout.addWidget(QLabel("🎭 Personality Filters (Prefer / Avoid)"))
        
        # Дерево Personality
        self.personality_tree_frame = QScrollArea()
        self.personality_tree_frame.setWidgetResizable(True)
        self.personality_tree_frame.setFrameShape(QFrame.NoFrame)
        
        personality_tree_widget = QWidget()
        self.personality_tree_layout = QVBoxLayout(personality_tree_widget)
        self.personality_tree_layout.setSpacing(2)
        
        self._build_personality_tree()
        
        self.personality_tree_frame.setWidget(personality_tree_widget)
        layout.addWidget(self.personality_tree_frame)
        
        # Контейнеры для Preferred и Avoided
        summary_frame = QWidget()
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preferred
        prefer_frame = QWidget()
        prefer_layout = QVBoxLayout(prefer_frame)
        prefer_layout.setContentsMargins(0, 0, 0, 0)
        prefer_layout.addWidget(QLabel("✅ Preferred:"))
        
        self.prefer_container = QScrollArea()
        self.prefer_container.setWidgetResizable(True)
        self.prefer_container.setMaximumHeight(150)
        self.prefer_container.setFrameShape(QFrame.NoFrame)
        
        prefer_tags_widget = QWidget()
        self.prefer_tags_layout = QHBoxLayout(prefer_tags_widget)
        self.prefer_tags_layout.setSpacing(5)
        self.prefer_tags_layout.addStretch()
        
        self.prefer_container.setWidget(prefer_tags_widget)
        prefer_layout.addWidget(self.prefer_container)
        summary_layout.addWidget(prefer_frame)
        
        # Avoided
        avoid_frame = QWidget()
        avoid_layout = QVBoxLayout(avoid_frame)
        avoid_layout.setContentsMargins(0, 0, 0, 0)
        avoid_layout.addWidget(QLabel("🚫 Avoided:"))
        
        self.avoid_container = QScrollArea()
        self.avoid_container.setWidgetResizable(True)
        self.avoid_container.setMaximumHeight(150)
        self.avoid_container.setFrameShape(QFrame.NoFrame)
        
        avoid_tags_widget = QWidget()
        self.avoid_tags_layout = QHBoxLayout(avoid_tags_widget)
        self.avoid_tags_layout.setSpacing(5)
        self.avoid_tags_layout.addStretch()
        
        self.avoid_container.setWidget(avoid_tags_widget)
        avoid_layout.addWidget(self.avoid_container)
        summary_layout.addWidget(avoid_frame)
        
        layout.addWidget(summary_frame)
        
        self._refresh_personality_tags_display()

    def _sync_tag_ui_states(self):
        """Синхронизирует UI одежды с текущими выбранными тегами"""
        if not self.tag_ui_elements:
            return
        
        for tag_key, ui in self.tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'subcategory': ui['subcategory']}
            if tag_entry in self.selected_wardrobe_tags:
                ui['label'].setStyleSheet("color: #22c55e;")
                ui['button'].setText("-")
                ui['button'].setStyleSheet("""
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
            else:
                ui['label'].setStyleSheet("color: #e0e0e0;")
                ui['button'].setText("+")
                ui['button'].setStyleSheet("""
                    QPushButton {
                        background-color: #22c55e;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #16a34a;
                    }
                """)

    def _build_personality_tree(self):
        """Строит дерево фильтров Personality (Prefer / Avoid)"""
        # Очищаем
        while self.personality_tree_layout.count():
            item = self.personality_tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.personality_tag_ui_elements = {}
        
        categories = [
            ("Expressions", "05_expression", ["mood", "eyes_expr", "mouth"]),
            ("Poses", "03_pose", ["base", "head", "arms", "legs"]),
        ]
        
        for cat_name, cat_dir, subcat_order in categories:
            self._create_personality_category(cat_name, cat_dir, subcat_order)
        
        self.personality_tree_layout.addStretch()

    def _create_personality_category(self, cat_name: str, cat_dir: str, subcat_order: list):
        """Создаёт категорию Personality (Expressions/Poses)"""
        cat_frame = QWidget()
        cat_frame.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(0, 2, 0, 2)
        cat_layout.setSpacing(0)
        
        # Кнопка-заголовок категории
        toggle_btn = QPushButton(f"➤ {cat_name}")
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-weight: bold;
                padding: 8px;
                text-align: left;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        cat_layout.addWidget(toggle_btn)
        
        # Контейнер для подкатегорий (изначально скрыт)
        subcats_frame = QWidget()
        subcats_frame.setVisible(False)
        subcats_layout = QVBoxLayout(subcats_frame)
        subcats_layout.setContentsMargins(20, 5, 0, 5)
        subcats_layout.setSpacing(1)
        
        dir_path = self.project_root / "prompt-library" / cat_dir
        if not dir_path.exists():
            cat_layout.addWidget(subcats_frame)
            self.personality_tree_layout.addWidget(cat_frame)
            
            def toggle_visibility():
                is_visible = subcats_frame.isVisible()
                subcats_frame.setVisible(not is_visible)
                if is_visible:
                    toggle_btn.setText(f"➤ {cat_name}")
                else:
                    toggle_btn.setText(f"▼ {cat_name}")
            
            toggle_btn.clicked.connect(toggle_visibility)
            return
        
        subcats = {}
        for txt_file in sorted(dir_path.rglob("*.txt")):
            parts = txt_file.relative_to(dir_path).parts
            if len(parts) == 1:
                sub_cat = parts[0].replace('.txt', '')
            elif len(parts) >= 2:
                sub_cat = parts[0]
            else:
                continue
            subcats[sub_cat] = txt_file
        
        def sort_key(sc):
            try:
                return subcat_order.index(sc.lower())
            except ValueError:
                return 999
        
        for sub_cat in sorted(subcats.keys(), key=sort_key):
            self._create_personality_subcategory(subcats_layout, cat_name, sub_cat, subcats[sub_cat])
        
        subcats_layout.addStretch()
        cat_layout.addWidget(subcats_frame)
        
        # Обработчик сворачивания
        def toggle_visibility():
            is_visible = subcats_frame.isVisible()
            subcats_frame.setVisible(not is_visible)
            if is_visible:
                toggle_btn.setText(f"➤ {cat_name}")
            else:
                toggle_btn.setText(f"▼ {cat_name}")
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        self.personality_tree_layout.addWidget(cat_frame)

    def _create_personality_subcategory(self, parent_layout, cat_name: str, sub_cat: str, file_path: Path):
        """Создаёт подкатегорию Personality с кнопками Prefer/Avoid"""
        sub_frame = QWidget()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(0, 1, 0, 1)
        sub_layout.setSpacing(0)
        
        # Кнопка-заголовок подкатегории
        toggle_btn = QPushButton(f"  ➤ {sub_cat.replace('_', ' ').title()}")
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #353535;
                color: #cccccc;
                padding: 6px;
                text-align: left;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
        """)
        sub_layout.addWidget(toggle_btn)
        
        # Контейнер для тегов (изначально скрыт)
        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)
        
        # Загружаем теги
        tags = self._load_tags_from_file(file_path)
        for tag in tags:
            tag_key = f"personality::{cat_name}::{sub_cat}::{tag}"
            tag_row = QWidget()
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)
            
            tag_label = QLabel(f"    • {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)
            
            # Кнопка Avoid (-)
            avoid_btn = QPushButton("-")
            avoid_btn.setFixedSize(25, 22)
            avoid_btn.setStyleSheet("""
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
            avoid_btn.clicked.connect(
                lambda checked, t=tag, cn=cat_name, sc=sub_cat, tk=tag_key:
                self._toggle_personality_tag(t, cn, sc, tk, 'avoid')
            )
            tag_row_layout.addWidget(avoid_btn)
            
            # Кнопка Prefer (+)
            prefer_btn = QPushButton("+")
            prefer_btn.setFixedSize(25, 22)
            prefer_btn.setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
            prefer_btn.clicked.connect(
                lambda checked, t=tag, cn=cat_name, sc=sub_cat, tk=tag_key:
                self._toggle_personality_tag(t, cn, sc, tk, 'prefer')
            )
            tag_row_layout.addWidget(prefer_btn)
            
            tags_layout.addWidget(tag_row)
            
            self.personality_tag_ui_elements[tag_key] = {
                'label': tag_label, 'prefer_btn': prefer_btn, 'avoid_btn': avoid_btn,
                'tag': tag, 'category': cat_name, 'subcategory': sub_cat
            }
        
        tags_layout.addStretch()
        sub_layout.addWidget(tags_frame)
        
        # Обработчик сворачивания
        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            if is_visible:
                toggle_btn.setText(f"  ➤ {sub_cat.replace('_', ' ').title()}")
            else:
                toggle_btn.setText(f"  ▼ {sub_cat.replace('_', ' ').title()}")
        
        toggle_btn.clicked.connect(toggle_visibility)
        
        parent_layout.addWidget(sub_frame)

    def _toggle_personality_tag(self, tag: str, category: str, subcategory: str, tag_key: str, action: str):
        """Добавляет/убирает тег в Prefer или Avoid"""
        tag_entry = {'tag': tag, 'category': category, 'subcategory': subcategory}
        
        # Проверяем, был ли тег уже в Prefer или Avoid
        was_in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
        was_in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
        
        # Удаляем из обоих списков
        self.preferred_personality_tags = [t for t in self.preferred_personality_tags if t['tag'] != tag]
        self.avoided_personality_tags = [t for t in self.avoided_personality_tags if t['tag'] != tag]
        
        # Добавляем в нужный список, если действие не отменяет предыдущее состояние
        if action == 'prefer' and not was_in_prefer:
            self.preferred_personality_tags.append(tag_entry)
        elif action == 'avoid' and not was_in_avoid:
            self.avoided_personality_tags.append(tag_entry)
        
        # Синхронизируем UI
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

    def _sync_personality_ui_states(self):
        """Синхронизирует цвета кнопок Prefer/Avoid с текущим состоянием"""
        if not self.personality_tag_ui_elements:
            return
        
        for tag_key, ui in self.personality_tag_ui_elements.items():
            tag = ui['tag']
            in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
            in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
            
            if in_prefer:
                ui['label'].setStyleSheet("color: #22c55e;")
                ui['prefer_btn'].setText("✓")
                ui['prefer_btn'].setStyleSheet("""
                    QPushButton {
                        background-color: darkgreen;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                """)
                ui['avoid_btn'].setText("-")
                ui['avoid_btn'].setStyleSheet("""
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
            elif in_avoid:
                ui['label'].setStyleSheet("color: #dc2626;")
                ui['prefer_btn'].setText("+")
                ui['prefer_btn'].setStyleSheet("""
                    QPushButton {
                        background-color: #22c55e;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #16a34a;
                    }
                """)
                ui['avoid_btn'].setText("✓")
                ui['avoid_btn'].setStyleSheet("""
                    QPushButton {
                        background-color: #991b1b;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                """)
            else:
                ui['label'].setStyleSheet("color: #e0e0e0;")
                ui['prefer_btn'].setText("+")
                ui['prefer_btn'].setStyleSheet("""
                    QPushButton {
                        background-color: #22c55e;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #16a34a;
                    }
                """)
                ui['avoid_btn'].setText("-")
                ui['avoid_btn'].setStyleSheet("""
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

    def _refresh_personality_tags_display(self):
        """Отрисовывает chips в секциях Preferred и Avoided"""
        # Очищаем Preferred
        while self.prefer_tags_layout.count() > 1:
            item = self.prefer_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Очищаем Avoided
        while self.avoid_tags_layout.count() > 1:
            item = self.avoid_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Отрисовываем Preferred
        if not self.preferred_personality_tags:
            label = QLabel("(empty)")
            label.setStyleSheet("color: gray;")
            self.prefer_tags_layout.insertWidget(0, label)
        else:
            for entry in self.preferred_personality_tags:
                chip = QWidget()
                chip.setStyleSheet("""
                    QWidget {
                        background-color: #404040;
                        border-radius: 15px;
                    }
                """)
                chip_layout = QHBoxLayout(chip)
                chip_layout.setContentsMargins(8, 4, 5, 4)
                chip_layout.setSpacing(5)
                
                chip_label = QLabel(f" {entry['tag'].replace('_', ' ')} ")
                chip_label.setStyleSheet("font-size: 13px; color: #22c55e;")
                chip_layout.addWidget(chip_label)
                
                remove_btn = QPushButton("×")
                remove_btn.setFixedSize(22, 22)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: white;
                        font-weight: bold;
                        border-radius: 11px;
                    }
                    QPushButton:hover {
                        background-color: #dc2626;
                    }
                """)
                remove_btn.clicked.connect(lambda checked, t=entry['tag']: self._remove_personality_tag(t))
                chip_layout.addWidget(remove_btn)
                
                self.prefer_tags_layout.insertWidget(
                    self.prefer_tags_layout.count() - 1, chip
                )
        
        # Отрисовываем Avoided
        if not self.avoided_personality_tags:
            label = QLabel("(empty)")
            label.setStyleSheet("color: gray;")
            self.avoid_tags_layout.insertWidget(0, label)
        else:
            for entry in self.avoided_personality_tags:
                chip = QWidget()
                chip.setStyleSheet("""
                    QWidget {
                        background-color: #404040;
                        border-radius: 15px;
                    }
                """)
                chip_layout = QHBoxLayout(chip)
                chip_layout.setContentsMargins(8, 4, 5, 4)
                chip_layout.setSpacing(5)
                
                chip_label = QLabel(f" {entry['tag'].replace('_', ' ')} ")
                chip_label.setStyleSheet(f"font-size: 13px; color: #dc2626;")
                chip_layout.addWidget(chip_label)
                
                remove_btn = QPushButton("×")
                remove_btn.setFixedSize(22, 22)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: white;
                        font-weight: bold;
                        border-radius: 11px;
                    }
                    QPushButton:hover {
                        background-color: #dc2626;
                    }
                """)
                remove_btn.clicked.connect(lambda checked, t=entry['tag']: self._remove_personality_tag(t))
                chip_layout.addWidget(remove_btn)
                
                self.avoid_tags_layout.insertWidget(
                    self.avoid_tags_layout.count() - 1, chip
                )

    def _remove_personality_tag(self, tag: str):
        """Удаляет тег из обоих списков Personality"""
        self.preferred_personality_tags = [x for x in self.preferred_personality_tags if x['tag'] != tag]
        self.avoided_personality_tags = [x for x in self.avoided_personality_tags if x['tag'] != tag]
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

    def _setup_signature_tab(self, widget: QWidget):
        """Настраивает субвкладку Signature"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        layout.addWidget(QLabel("✨ Signature Items & Hair Rules"))
        
        # === PROPS SECTION ===
        props_group = QGroupBox("🧸 Signature Props")
        props_layout = QVBoxLayout(props_group)
        
        # Кнопка добавления prop
        add_prop_btn = QPushButton("➕ Add Prop")
        add_prop_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        add_prop_btn.clicked.connect(self._add_signature_prop)
        props_layout.addWidget(add_prop_btn)
        
        # Контейнер для props
        self.props_container = QScrollArea()
        self.props_container.setWidgetResizable(True)
        self.props_container.setFrameShape(QFrame.NoFrame)
        
        props_widget = QWidget()
        self.props_layout = QVBoxLayout(props_widget)
        self.props_layout.setSpacing(5)
        self.props_layout.addStretch()
        
        self.props_container.setWidget(props_widget)
        props_layout.addWidget(self.props_container)
        
        layout.addWidget(props_group)
        
        # === HAIR RULES SECTION ===
        hair_group = QGroupBox("💇 Hair Rules")
        hair_layout = QVBoxLayout(hair_group)
        
        # Default style
        default_frame = QWidget()
        default_layout = QHBoxLayout(default_frame)
        default_layout.setContentsMargins(0, 0, 0, 0)
        
        default_label = QLabel("Default Style:")
        default_label.setFixedWidth(120)
        default_layout.addWidget(default_label)
        
        self.hair_default_btn = QPushButton("▼ hair down")
        self.hair_default_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                padding: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        self.hair_default_btn.clicked.connect(self._open_default_style_selector)
        default_layout.addWidget(self.hair_default_btn, 1)
        
        hair_layout.addWidget(default_frame)
        
        # Conditional rules
        cond_header = QWidget()
        cond_layout = QHBoxLayout(cond_header)
        cond_layout.setContentsMargins(0, 5, 0, 0)
        
        cond_label = QLabel("Conditional Rules:")
        cond_label.setStyleSheet("font-weight: bold;")
        cond_layout.addWidget(cond_label)
        cond_layout.addStretch()
        
        add_rule_btn = QPushButton("➕ Add Rule")
        add_rule_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        add_rule_btn.clicked.connect(self._add_hair_rule)
        cond_layout.addWidget(add_rule_btn)
        
        hair_layout.addWidget(cond_header)
        
        # Контейнер для conditional rules
        self.hair_rules_container = QScrollArea()
        self.hair_rules_container.setWidgetResizable(True)
        self.hair_rules_container.setFrameShape(QFrame.NoFrame)
        
        rules_widget = QWidget()
        self.hair_rules_layout = QVBoxLayout(rules_widget)
        self.hair_rules_layout.setSpacing(5)
        self.hair_rules_layout.addStretch()
        
        self.hair_rules_container.setWidget(rules_widget)
        hair_layout.addWidget(self.hair_rules_container)
        
        layout.addWidget(hair_group)
        
        self._refresh_signature_props_display()
        self._refresh_hair_rules_display()

    def _load_tags_from_file(self, file_path: Path) -> list:
        """Загружает теги из конкретного файла"""
        cache_key = str(file_path)
        if cache_key in self._tags_cache:
            return self._tags_cache[cache_key]
        
        tags = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        tags.append(line)
            self._tags_cache[cache_key] = tags
        except Exception as e:
            self._log(f"❌ Ошибка чтения {file_path}: {e}\n")
        
        return tags

    def _refresh_profiles_list(self):
        """Обновляет список профилей"""
        self.profiles_list.clear()
        
        profiles = self._get_available_profiles()
        for profile_name in profiles:
            item = QTreeWidgetItem([f"👤 {profile_name}"])
            item.setData(0, Qt.UserRole, profile_name)
            self.profiles_list.addTopLevelItem(item)

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

    def _on_profile_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработчик клика на профиль"""
        profile_name = item.data(0, Qt.UserRole)
        if profile_name:
            self._select_profile(profile_name)

    def _select_profile(self, profile_name: str):
        """Загружает профиль в редактор"""
        self.current_profile_name = profile_name
        self.editor_title.setText(f"👤 Editing: {profile_name}")
        self._load_profile_to_editor(profile_name)

    def _load_profile_to_editor(self, profile_name: str):
        """Загружает профиль из YAML в редактор"""
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            QMessageBox.critical(self, "Error", f"Profile not found: {profile_name}")
            return
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        
        # Загружаем DNA
        self.selected_dna_tags = []
        fixed_traits = profile.get('fixed_traits', [])
        all_dna_tags = {ui['tag']: ui['category'] for ui in self.dna_tag_ui_elements.values()}
        
        for trait in fixed_traits:
            if trait in all_dna_tags:
                self.selected_dna_tags.append({'tag': trait, 'category': all_dna_tags[trait]})
        
        self._sync_dna_tag_ui_states()
        self._refresh_selected_dna_tags_display()
        
        self._log(f"📥 Загружен профиль: {profile_name}\n")

        # Загружаем одежду
        self.selected_wardrobe_tags = []
        outfit_whitelist = profile.get('outfit_whitelist', {})
        for outfit_name, subcats in outfit_whitelist.items():
            if isinstance(subcats, dict):
                for subcategory, tags in subcats.items():
                    if isinstance(tags, list):
                        for tag in tags:
                            self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': subcategory})
        
        self._sync_tag_ui_states()
        self._refresh_selected_tags_display()

        # Загружаем Personality
        self.preferred_personality_tags = []
        self.avoided_personality_tags = []
        expr = profile.get('expression_filter', {})
        for t in expr.get('prefer', []):
            self.preferred_personality_tags.append({'tag': t, 'category': 'Expressions'})
        for t in expr.get('avoid', []):
            self.avoided_personality_tags.append({'tag': t, 'category': 'Expressions'})
        pose = profile.get('pose_filter', {})
        for t in pose.get('prefer', []):
            self.preferred_personality_tags.append({'tag': t, 'category': 'Poses'})
        for t in pose.get('avoid', []):
            self.avoided_personality_tags.append({'tag': t, 'category': 'Poses'})
        
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

        # === БЫСТРАЯ ЗАГРУЗКА: Signature ===
        self.signature_props = profile.get('signature_props', [])
        hair_rules = profile.get('hair_rules', {})
        self.hair_rules_data = {
            'default': hair_rules.get('default', 'hair down'),
            'conditional': hair_rules.get('conditional', [])
        }
        
        # ОБНОВЛЯЕМ UI после загрузки данных
        self._refresh_signature_props_display()
        self._refresh_hair_rules_display()

    def _sync_dna_tag_ui_states(self):
        """Синхронизирует UI DNA с текущими выбранными тегами"""
        if not self.dna_tag_ui_elements:
            return
        
        for tag_key, ui in self.dna_tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'category': ui['category']}
            if tag_entry in self.selected_dna_tags:
                ui['label'].setStyleSheet("color: #22c55e;")
                ui['button'].setText("-")
                ui['button'].setStyleSheet("""
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
            else:
                ui['label'].setStyleSheet("color: #e0e0e0;")
                ui['button'].setText("+")
                ui['button'].setStyleSheet("""
                    QPushButton {
                        background-color: #22c55e;
                        color: white;
                        font-weight: bold;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #16a34a;
                    }
                """)

    def _create_new_profile(self):
        """Создаёт новый профиль"""
        name, ok = QInputDialog.getText(self, "New Profile", "Enter character name:")
        if not ok or not name:
            return
        
        name = name.strip().replace(' ', '_')
        if not name or not all(c.isalnum() or c == '_' for c in name):
            QMessageBox.critical(self, "Error", "Name must contain only letters, numbers and underscores")
            return
        
        new_path = self.profiles_directory / f"{name}.yaml"
        if new_path.exists():
            QMessageBox.critical(self, "Error", f"Profile '{name}' already exists!")
            return
        
        profile = self._get_default_profile_structure(name)
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(f"# Character Profile: {name}\n")
            f.write("# Фильтр поверх scene-rules\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        self._log(f"➕ Создан новый профиль: {name}\n")
        self._refresh_profiles_list()
        self._select_profile(name)
        QMessageBox.information(self, "Success", f"Profile '{name}' created!")

    def _import_profile(self):
        """Импортирует профиль из внешнего YAML-файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Character Profile",
            "",
            "YAML files (*.yaml *.yml);;All files (*.*)"
        )
        if not file_path:
            return
        
        source = Path(file_path)
        name = source.stem
        dest = self.profiles_directory / f"{name}.yaml"
        counter = 1
        while dest.exists():
            dest = self.profiles_directory / f"{name}_{counter}.yaml"
            counter += 1
        
        try:
            shutil.copy2(source, dest)
            self._log(f"📥 Импортирован профиль: {source.name} → {dest.name}\n")
            self._refresh_profiles_list()
            self._select_profile(dest.stem)
            QMessageBox.information(self, "Success", f"Profile imported as '{dest.stem}'!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {e}")

    def _delete_profile(self):
        """Удаляет выбранный профиль"""
        if not self.current_profile_name:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        
        if self.settings_manager.get('behavior', 'confirm_delete'):
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete '{self.current_profile_name}'?\n\nThis cannot be undone!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        profile_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            QMessageBox.critical(self, "Error", "Profile file not found")
            return
        
        try:
            profile_path.unlink()
            self._log(f"🗑️ Удалён профиль: {self.current_profile_name}\n")
            
            self.current_profile_name = None
            self.profile_character_data = {}
            self.editor_title.setText("👤 Editing: (no selection)")
            
            # Очищаем DNA
            self.selected_dna_tags = []
            self._sync_dna_tag_ui_states()
            self._refresh_selected_dna_tags_display()
            
            # Очищаем Outfits
            self.selected_wardrobe_tags = []
            self._sync_tag_ui_states()
            self._refresh_selected_tags_display()
            
            # Очищаем Personality
            self.preferred_personality_tags = []
            self.avoided_personality_tags = []
            self._sync_personality_ui_states()
            self._refresh_personality_tags_display()
            
            # Очищаем Signature
            self.signature_props = []
            self.hair_rules_data = {'default': 'hair down', 'conditional': []}
            self._refresh_signature_props_display()
            self._refresh_hair_rules_display()
            
            self._refresh_profiles_list()
            QMessageBox.information(self, "Success", "Profile deleted!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")

    def _edit_profile_name(self):
        """Переименовывает профиль"""
        if not self.current_profile_name:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Profile",
            "Enter new name:",
            text=self.current_profile_name
        )
        if not ok or not new_name:
            return
        
        new_name = new_name.strip().replace(' ', '_')
        if not new_name or not all(c.isalnum() or c == '_' for c in new_name):
            QMessageBox.critical(self, "Error", "Name must contain only letters, numbers and underscores")
            return
        
        if new_name == self.current_profile_name:
            return
        
        old_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not old_path.exists():
            old_path = self.project_root / "character-profile.yaml"
        new_path = self.profiles_directory / f"{new_name}.yaml"
        
        if new_path.exists():
            QMessageBox.critical(self, "Error", f"Profile '{new_name}' already exists!")
            return
        
        try:
            if old_path.exists():
                shutil.move(str(old_path), str(new_path))
            
            old_name = self.current_profile_name
            self.current_profile_name = new_name
            self.editor_title.setText(f"👤 Editing: {new_name}")
            
            self._refresh_profiles_list()
            self._log(f"✏️ Профиль переименован: {old_name} → {new_name}\n")
            QMessageBox.information(self, "Success", f"Profile renamed to '{new_name}'!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def _save_profile(self):
        """Сохраняет текущее состояние редактора в YAML-файл"""
        if not self.current_profile_name:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        
        profile_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = yaml.safe_load(f) or self._get_default_profile_structure(self.current_profile_name)
        else:
            profile = self._get_default_profile_structure(self.current_profile_name)
        
        if not self.profile_character_data:
            self.profile_character_data = {
                'name': self.current_profile_name,
                'age': 18,
                'archetype': 'custom character'
            }
        
        profile['character'] = self.profile_character_data.copy()
        
        # DNA
        selected_traits = [entry['tag'] for entry in self.selected_dna_tags]
        profile['fixed_traits'] = selected_traits

        # Одежда
        wardrobe_by_subcat = {}
        for entry in self.selected_wardrobe_tags:
            wardrobe_by_subcat.setdefault(entry['subcategory'], []).append(entry['tag'])
        profile['outfit_whitelist'] = {'default': wardrobe_by_subcat}
        
        # Personality (Expressions + Poses)
        profile['expression_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t.get('category') == 'Expressions'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t.get('category') == 'Expressions']
        }
        profile['pose_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t.get('category') == 'Poses'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t.get('category') == 'Poses']
        }
        
        # Signature (Props + Hair Rules)
        profile['signature_props'] = self.signature_props
        profile['hair_rules'] = {
            'default': self.hair_rules_data.get('default', 'hair down'),
            'conditional': self.hair_rules_data.get('conditional', [])
        }
        
        # Atmosphere (пока пустые, добавим в следующем шаге)
        if 'atmosphere_preferences' not in profile:
            profile['atmosphere_preferences'] = {'lighting': [], 'weather': []}
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(f"# Character Profile: {self.current_profile_name}\n")
            f.write("# Фильтр поверх scene-rules\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        self._log(f"💾 Профиль '{self.current_profile_name}' сохранён\n")
        QMessageBox.information(self, "Success", f"Profile '{self.current_profile_name}' saved!")

    def _get_default_profile_structure(self, name: str = "New Character") -> dict:
        """Возвращает базовую структуру нового YAML-профиля"""
        return {
            'character': {'name': name, 'age': 18, 'archetype': 'custom character'},
            'fixed_traits': [],
            'outfit_whitelist': {},
            'underwear_whitelist': {},
            'signature_props': [],
            'hair_rules': {'default': 'hair down', 'conditional': []},
            'expression_filter': {'prefer': [], 'avoid': []},
            'pose_filter': {'prefer': [], 'avoid': []},
            'atmosphere_preferences': {'lighting': [], 'weather': []}
        }

    def _load_tags_from_library(self, relative_path: str) -> list:
        """Загружает список тегов из файла библиотеки тегов"""
        if relative_path in self._tags_cache:
            return self._tags_cache[relative_path]
        
        file_path = self.project_root / "prompt-library" / relative_path
        tags = []
        
        if not file_path.exists():
            self._log(f"⚠️ Файл не найден: {relative_path}\n")
            return tags
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        tags.append(line)
            self._tags_cache[relative_path] = tags
        except Exception as e:
            self._log(f"❌ Ошибка чтения {relative_path}: {e}\n")
        
        return tags
    # ═══════════════════════════════════════════════
    # SIGNATURE: Props + Hair Rules
    # ═══════════════════════════════════════════════
    def _add_signature_prop(self):
        """Добавляет новый signature prop"""
        self.signature_props.append({'name': 'new_item', 'tags': []})
        self._refresh_signature_props_display()

    def _remove_signature_prop(self, index: int):
        """Удаляет signature prop"""
        if 0 <= index < len(self.signature_props):
            self.signature_props.pop(index)
            self._refresh_signature_props_display()

    def _update_prop_name(self, index: int, new_name: str):
        """Обновляет имя prop"""
        if 0 <= index < len(self.signature_props):
            self.signature_props[index]['name'] = new_name.strip()

    def _add_tag_to_prop(self, index: int):
        """Добавляет тег к prop"""
        if 0 <= index < len(self.signature_props):
            self.signature_props[index]['tags'].append('new_tag')
            self._refresh_signature_props_display()

    def _remove_tag_from_prop(self, prop_index: int, tag_index: int):
        """Удаляет тег из prop"""
        if 0 <= prop_index < len(self.signature_props):
            tags = self.signature_props[prop_index]['tags']
            if 0 <= tag_index < len(tags):
                tags.pop(tag_index)
                self._refresh_signature_props_display()

    def _update_prop_tag(self, prop_index: int, tag_index: int, new_tag: str):
        """Обновляет тег prop"""
        if 0 <= prop_index < len(self.signature_props):
            tags = self.signature_props[prop_index]['tags']
            if 0 <= tag_index < len(tags):
                tags[tag_index] = new_tag.strip()

    def _refresh_signature_props_display(self):
        """Отрисовывает список Signature Props"""
        # Очищаем
        while self.props_layout.count() > 1:
            item = self.props_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.signature_props:
            label = QLabel("(No signature props — нажмите '➕ Add Prop')")
            label.setStyleSheet("color: gray;")
            self.props_layout.insertWidget(0, label)
            return

        for i, prop in enumerate(self.signature_props):
            prop_frame = QWidget()
            prop_frame.setStyleSheet("""
                QWidget {
                    background-color: #333333;
                    border-radius: 5px;
                }
            """)
            prop_layout = QVBoxLayout(prop_frame)
            prop_layout.setContentsMargins(10, 10, 10, 10)
            prop_layout.setSpacing(5)

            # Header с именем и кнопкой удаления
            header = QWidget()
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel("Prop name:")
            name_label.setStyleSheet("color: gray; font-size: 11px; font-style: italic;")
            header_layout.addWidget(name_label)

            name_entry = QLineEdit()
            name_entry.setPlaceholderText("Item name")
            name_entry.setText(prop['name'])
            name_entry.textChanged.connect(lambda text, idx=i: self._update_prop_name(idx, text))
            header_layout.addWidget(name_entry, 1)

            delete_btn = QPushButton("Delete Prop")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #991b1b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, idx=i: self._remove_signature_prop(idx))
            header_layout.addWidget(delete_btn)

            prop_layout.addWidget(header)

            # Tags
            tags_label = QLabel("Tags:")
            tags_label.setStyleSheet("font-weight: bold;")
            prop_layout.addWidget(tags_label)

            for j, tag in enumerate(prop['tags']):
                tag_row = QWidget()
                tag_layout = QHBoxLayout(tag_row)
                tag_layout.setContentsMargins(0, 0, 0, 0)
                tag_layout.setSpacing(5)

                tag_entry = QLineEdit()
                tag_entry.setText(tag)
                tag_entry.textChanged.connect(lambda text, pi=i, ti=j: self._update_prop_tag(pi, ti, text))
                tag_layout.addWidget(tag_entry, 1)

                browse_btn = QPushButton("Browse")
                browse_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        padding: 3px;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                """)
                browse_btn.clicked.connect(lambda checked, pi=i: self._open_tags_browser(pi))
                tag_layout.addWidget(browse_btn)

                remove_btn = QPushButton("×")
                remove_btn.setFixedSize(25, 25)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc2626;
                        color: white;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #991b1b;
                    }
                """)
                remove_btn.clicked.connect(lambda checked, pi=i, ti=j: self._remove_tag_from_prop(pi, ti))
                tag_layout.addWidget(remove_btn)

                prop_layout.addWidget(tag_row)

            # Кнопка добавления тега
            add_tag_btn = QPushButton("➕ Add Tag")
            add_tag_btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: white;
                    padding: 3px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
            add_tag_btn.clicked.connect(lambda checked, idx=i: self._add_tag_to_prop(idx))
            prop_layout.addWidget(add_tag_btn)

            self.props_layout.insertWidget(self.props_layout.count() - 1, prop_frame)

    def _open_tags_browser(self, prop_index: int):
        """Открывает popup для выбора тегов из prompt-library/09_props"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Browse Tags (Props)")
        dialog.resize(500, 600)

        layout = QVBoxLayout(dialog)

        label = QLabel("🧸 Select tags (multiple allowed):")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        props_dir = self.project_root / "prompt-library" / "09_props"
        if not props_dir.exists():
            error_label = QLabel(f"⚠️ Папка не найдена: {props_dir}")
            error_label.setStyleSheet("color: red;")
            scroll_layout.addWidget(error_label)
        else:
            current_tags = set(self.signature_props[prop_index]['tags'])
            self._popup_selected_tags = set(current_tags)

            for txt_file in sorted(props_dir.rglob("*.txt")):
                tags = self._load_tags_from_file(txt_file)
                if tags:
                    cat_label = QLabel(f"📁 {txt_file.stem.replace('_', ' ').title()}")
                    cat_label.setStyleSheet("font-weight: bold; padding: 5px 0;")
                    scroll_layout.addWidget(cat_label)

                    for tag in tags:
                        cb = QCheckBox(tag)
                        cb.setChecked(tag in current_tags)
                        cb.stateChanged.connect(
                            lambda state, t=tag, checkbox=cb: self._toggle_tag_selection(t, checkbox.isChecked())
                        )
                        scroll_layout.addWidget(cb)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(lambda: self._apply_tags_browser(prop_index, dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    def _toggle_tag_selection(self, tag: str, checked: bool):
        """Переключает выбор тега в popup"""
        if checked:
            self._popup_selected_tags.add(tag)
        else:
            self._popup_selected_tags.discard(tag)

    def _apply_tags_browser(self, prop_index: int, dialog):
        """Применяет выбранные теги к prop"""
        new_tags = sorted(list(self._popup_selected_tags))
        self.signature_props[prop_index]['tags'] = new_tags
        self._refresh_signature_props_display()
        dialog.accept()

    def _add_hair_rule(self):
        """Добавляет новое conditional hair rule"""
        hair_tags = self._load_tags_from_library("01_character/hair/style.txt")
        default_style = hair_tags[0] if hair_tags else "hair down"
        self.hair_rules_data['conditional'].append({
            'if_action': [], 'style': default_style, 'probability': 0.5
        })
        self._refresh_hair_rules_display()

    def _remove_hair_rule(self, index: int):
        """Удаляет conditional hair rule"""
        if 0 <= index < len(self.hair_rules_data['conditional']):
            self.hair_rules_data['conditional'].pop(index)
            self._refresh_hair_rules_display()

    def _update_hair_rule_style(self, index: int, style: str):
        """Обновляет стиль conditional rule"""
        if 0 <= index < len(self.hair_rules_data['conditional']):
            self.hair_rules_data['conditional'][index]['style'] = style

    def _update_hair_rule_probability(self, index: int, prob_str: str):
        """Обновляет вероятность conditional rule"""
        try:
            prob = float(prob_str)
            if 0 <= prob <= 1:
                self.hair_rules_data['conditional'][index]['probability'] = prob
        except ValueError:
            pass

    def _update_hair_rule_actions(self, index: int, actions_str: str):
        """Обновляет действия conditional rule"""
        if 0 <= index < len(self.hair_rules_data['conditional']):
            actions = [a.strip() for a in actions_str.split(',') if a.strip()]
            self.hair_rules_data['conditional'][index]['if_action'] = actions

    def _refresh_hair_rules_display(self):
        """Отрисовывает список conditional hair rules"""
        # Очищаем
        while self.hair_rules_layout.count() > 1:
            item = self.hair_rules_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Обновляем кнопку default style
        if hasattr(self, 'hair_default_btn') and self.hair_default_btn:
            current_default = self.hair_rules_data.get('default', 'hair down')
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == '💇 Hair Style']
            star = " ⭐" if current_default in dna_styles else ""
            self.hair_default_btn.setText(f"▼ {current_default}{star}")

        if not self.hair_rules_data['conditional']:
            label = QLabel("(No conditional rules — нажмите '➕ Add Rule')")
            label.setStyleSheet("color: gray;")
            self.hair_rules_layout.insertWidget(0, label)
            return

        from PySide6.QtWidgets import QSlider

        for i, rule in enumerate(self.hair_rules_data['conditional']):
            rule_frame = QWidget()
            rule_frame.setStyleSheet("""
                QWidget {
                    background-color: #333333;
                    border-radius: 5px;
                }
            """)
            rule_layout = QVBoxLayout(rule_frame)
            rule_layout.setContentsMargins(10, 10, 10, 10)
            rule_layout.setSpacing(5)

            # Header
            header = QWidget()
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 0)

            rule_label = QLabel(f"Rule #{i + 1}")
            rule_label.setStyleSheet("font-weight: bold;")
            header_layout.addWidget(rule_label)
            header_layout.addStretch()

            delete_btn = QPushButton("Delete Hair Rule")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #991b1b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, idx=i: self._remove_hair_rule(idx))
            header_layout.addWidget(delete_btn)

            rule_layout.addWidget(header)

            # If actions
            actions_frame = QWidget()
            actions_layout = QHBoxLayout(actions_frame)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            actions_label = QLabel("If actions:")
            actions_label.setFixedWidth(100)
            actions_layout.addWidget(actions_label)

            actions_entry = QLineEdit()
            actions_entry.setPlaceholderText("reading, studying, ...")
            actions_entry.setText(", ".join(rule['if_action']))
            actions_entry.textChanged.connect(lambda text, idx=i: self._update_hair_rule_actions(idx, text))
            actions_layout.addWidget(actions_entry, 1)

            browse_btn = QPushButton("Browse")
            browse_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    padding: 3px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            browse_btn.clicked.connect(lambda checked, idx=i, ae=actions_entry: self._open_actions_browser(idx, ae))
            actions_layout.addWidget(browse_btn)

            rule_layout.addWidget(actions_frame)

            # Style
            style_frame = QWidget()
            style_layout = QHBoxLayout(style_frame)
            style_layout.setContentsMargins(0, 0, 0, 0)

            style_label = QLabel("Style:")
            style_label.setFixedWidth(100)
            style_layout.addWidget(style_label)

            style_text = rule['style'] or "Select..."
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == '💇 Hair Style']
            star = " ⭐" if rule['style'] in dna_styles else ""

            style_btn = QPushButton(f"▼ {style_text}{star}")
            style_btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: white;
                    padding: 5px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
            style_btn.clicked.connect(lambda checked, idx=i, btn=style_btn: self._open_style_selector(idx, btn))
            style_layout.addWidget(style_btn, 1)

            rule_layout.addWidget(style_frame)

            # Probability
            prob_frame = QWidget()
            prob_layout = QHBoxLayout(prob_frame)
            prob_layout.setContentsMargins(0, 0, 0, 0)

            prob_label = QLabel("Prob:")
            prob_label.setFixedWidth(100)
            prob_layout.addWidget(prob_label)

            prob_slider = QSlider(Qt.Horizontal)
            prob_slider.setMinimum(0)
            prob_slider.setMaximum(100)
            prob_slider.setValue(int(rule['probability'] * 100))
            prob_slider.valueChanged.connect(lambda val, idx=i: self._update_prob_from_slider(idx, val / 100))
            prob_layout.addWidget(prob_slider, 1)

            prob_entry = QLineEdit()
            prob_entry.setFixedWidth(60)
            prob_entry.setText(str(rule['probability']))
            prob_entry.textChanged.connect(lambda text, idx=i, slider=prob_slider: self._update_prob_from_entry(idx, text, slider))
            prob_layout.addWidget(prob_entry)

            rule_layout.addWidget(prob_frame)

            self.hair_rules_layout.insertWidget(self.hair_rules_layout.count() - 1, rule_frame)

    def _open_style_selector(self, rule_index: int, button_widget):
        """Открывает popup выбора стиля прически"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Hair Style")
        dialog.resize(350, 500)

        layout = QVBoxLayout(dialog)

        label = QLabel("💇 Select hair style:")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == '💇 Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = " ⭐" if tag in dna_styles else ""
            btn = QPushButton(f"{tag}{star}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    text-align: left;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            btn.clicked.connect(lambda checked, t=tag: self._select_style(t, rule_index, button_widget, dialog))
            scroll_layout.addWidget(btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)

        dialog.exec()

    def _select_style(self, style: str, rule_index: int, button_widget, dialog):
        """Выбирает стиль для conditional rule"""
        self._update_hair_rule_style(rule_index, style)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == '💇 Hair Style']
        star = " ⭐" if style in dna_styles else ""
        button_widget.setText(f"▼ {style}{star}")
        dialog.accept()

    def _open_default_style_selector(self):
        """Открывает popup выбора default стиля прически"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Default Hair Style")
        dialog.resize(350, 500)

        layout = QVBoxLayout(dialog)

        label = QLabel("💇 Select default hair style:")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == '💇 Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = " ⭐" if tag in dna_styles else ""
            btn = QPushButton(f"{tag}{star}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    text-align: left;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            btn.clicked.connect(lambda checked, t=tag: self._select_default_style(t, dialog))
            scroll_layout.addWidget(btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)

        dialog.exec()

    def _select_default_style(self, style: str, dialog):
        """Выбирает default стиль прически"""
        self.hair_rules_data['default'] = style
        if hasattr(self, 'hair_default_btn') and self.hair_default_btn:
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == '💇 Hair Style']
            star = " ⭐" if style in dna_styles else ""
            self.hair_default_btn.setText(f"▼ {style}{star}")
        dialog.accept()

    def _open_actions_browser(self, rule_index: int, entry_widget):
        """Открывает popup выбора actions для conditional hair rule"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Actions")
        dialog.resize(500, 600)

        layout = QVBoxLayout(dialog)

        label = QLabel("🎬 Select actions:")
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        actions_dir = self.project_root / "prompt-library" / "04_action"
        if not actions_dir.exists():
            actions_dir = self.project_root / "prompt-library" / "03_pose"

        current_actions = set(self.hair_rules_data['conditional'][rule_index]['if_action'])
        self._popup_selected_actions = set(current_actions)

        if actions_dir.exists():
            for txt_file in sorted(actions_dir.rglob("*.txt")):
                tags = self._load_tags_from_file(txt_file)
                if tags:
                    cat_label = QLabel(f"📁 {txt_file.stem.replace('_', ' ').title()}")
                    cat_label.setStyleSheet("font-weight: bold; padding: 5px 0;")
                    scroll_layout.addWidget(cat_label)

                    for tag in tags:
                        cb = QCheckBox(tag)
                        cb.setChecked(tag in current_actions)
                        cb.stateChanged.connect(
                            lambda state, t=tag, checkbox=cb: self._toggle_action_selection(t, checkbox.isChecked())
                        )
                        scroll_layout.addWidget(cb)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(lambda: self._apply_actions_browser(rule_index, entry_widget, dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec()

    def _toggle_action_selection(self, tag: str, checked: bool):
        """Переключает выбор action в popup"""
        if checked:
            self._popup_selected_actions.add(tag)
        else:
            self._popup_selected_actions.discard(tag)

    def _apply_actions_browser(self, rule_index: int, entry_widget, dialog):
        """Применяет выбранные actions к conditional rule"""
        actions_list = sorted(list(self._popup_selected_actions))
        self.hair_rules_data['conditional'][rule_index]['if_action'] = actions_list
        entry_widget.setText(", ".join(actions_list))
        dialog.accept()

    def _update_prob_from_slider(self, rule_index: int, value: float):
        """Обновляет вероятность из слайдера"""
        rounded_value = round(value, 2)
        self._update_hair_rule_probability(rule_index, str(rounded_value))

        # Обновляем текстовое поле
        if hasattr(self, 'hair_rules_container') and self.hair_rules_container:
            rules_widget = self.hair_rules_container.widget()
            if rules_widget:
                rule_frames = [w for w in rules_widget.layout().children() if isinstance(w, QWidget)]
                if rule_index < len(rule_frames):
                    # Ищем QLineEdit с вероятностью
                    for child in rule_frames[rule_index].findChildren(QLineEdit):
                        if child.text().replace('.', '').isdigit():
                            child.setText(str(rounded_value))
                            break

    def _update_prob_from_entry(self, rule_index: int, value_str: str, slider_widget):
        """Обновляет вероятность из текстового поля"""
        try:
            value = float(value_str)
            if 0 <= value <= 1:
                self._update_hair_rule_probability(rule_index, value_str)
                slider_widget.setValue(int(value * 100))
        except ValueError:
            pass