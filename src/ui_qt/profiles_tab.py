from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit,
                               QPlainTextEdit, QTabWidget, QTreeWidget,
                               QTreeWidgetItem, QScrollArea, QFrame,
                               QGroupBox, QMessageBox, QComboBox,
                               QFileDialog, QInputDialog, QSplitter,
                               QApplication, QSlider, QDialog,
                               QDialogButtonBox, QCheckBox)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from pathlib import Path
import yaml
import shutil
from ui_qt.icon_manager import IconManager
from ui_qt.components.category_card import (
    CategoryCard, category_chip_variant, category_full
)
from ui_qt.components.compact_chip_row import CompactChipRow
from ui_qt.components.summary_panel import SummaryPanel


# ═══════════════════════════════════════════════
# КОНСТАНТЫ
# ═══════════════════════════════════════════════
DNA_CATEGORIES = [
    ("Body Type",     "01_character/body/type.txt",     "Build and proportions"),
    ("Body Features", "01_character/body/features.txt", "Body details"),
    ("Eye Color",     "01_character/eyes/color.txt",    "Iris color"),
    ("Eye Shape",     "01_character/eyes/shape.txt",    "Eye form"),
    ("Face Features", "01_character/face/features.txt", "Facial structure"),
    ("Hair Style",    "01_character/hair/style.txt",    "Cut and arrangement"),
    ("Hair Color",    "01_character/hair/color.txt",    "Hair hue"),
    ("Hair Length",   "01_character/hair/length.txt",   "Hair length"),
    ("Skin Tone",     "01_character/skin/tone.txt",     "Complexion"),
]

PERSONALITY_CATEGORIES = [
    ("Expressions", "05_expression", ["mood", "eyes_expr", "mouth"]),
    ("Poses", "03_pose", ["base", "head", "arms", "legs"]),
]

WARDROBE_ORDER = ['full_body', 'topwear', 'bottomwear', 'legwear',
                  'footwear', 'underwear', 'accessories']


class ProfilesTab(QWidget):
    """Вкладка редактирования профилей персонажей (Qt версия, v2 — редизайн)"""

    def __init__(self, project_root: Path, profiles_directory: Path,
                 settings_manager, log_callback, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.settings_manager = settings_manager
        self._log = log_callback

        # ── Состояние ──
        self.current_profile_name: str | None = None
        self.profile_character_data: dict = {}

        # DNA
        self.selected_dna_tags: list[dict] = []
        self._dna_cards: list = []   # CategoryCard instances

        # Outfits
        self.selected_wardrobe_tags: list[dict] = []

        # Personality
        self.preferred_personality_tags: list[dict] = []
        self.avoided_personality_tags: list[dict] = []

        # Signature
        self.signature_props: list[dict] = []
        self.hair_rules_data: dict = {'default': 'hair down', 'conditional': []}
        self._popup_selected_tags: set[str] = set()
        self._popup_selected_actions: set[str] = set()

        # Atmosphere
        self.selected_lighting_tags: list[str] = []
        self.selected_weather_tags: list[str] = []

        # Custom
        self.other_traits_text = None

        # Кэш тегов
        self._tags_cache = {}

        self._setup_ui()
        self._refresh_profiles_list()

    # ═══════════════════════════════════════════════
    # MAIN LAYOUT
    # ═══════════════════════════════════════════════
    def _setup_ui(self):
        """Создаёт главный layout вкладки Profiles"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)

        # ═══ ЛЕВАЯ ПАНЕЛЬ: Список профилей ═══
        left_widget = QWidget()
        left_widget.setMaximumWidth(350)
        left_widget.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_title = QLabel(f"{IconManager.get('user')}  Characters")
        left_title.setObjectName("SectionTitle")
        left_layout.addWidget(left_title)

        self.profiles_list = QTreeWidget()
        self.profiles_list.setHeaderHidden(True)
        self.profiles_list.itemClicked.connect(self._on_profile_clicked)
        left_layout.addWidget(self.profiles_list)

        # Кнопки
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)

        new_btn = QPushButton(f"{IconManager.get('add')}  New")
        new_btn.setProperty("variant", "success")
        new_btn.clicked.connect(self._create_new_profile)
        buttons_layout.addWidget(new_btn)

        import_btn = QPushButton(f"{IconManager.get('import')}  Import")
        import_btn.setProperty("variant", "primary")
        import_btn.clicked.connect(self._import_profile)
        buttons_layout.addWidget(import_btn)

        delete_btn = QPushButton(f"{IconManager.get('delete')}  Delete")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self._delete_profile)
        buttons_layout.addWidget(delete_btn)

        left_layout.addWidget(buttons_frame)

        # ═══ ПРАВАЯ ПАНЕЛЬ: Редактор ═══
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Заголовок редактора
        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        self.editor_title = QLabel(f"Editing: (no selection)")
        self.editor_title.setObjectName("PageTitle")
        title_layout.addWidget(self.editor_title)

        self.edit_name_btn = QPushButton(f"{IconManager.get('pencil')}")
        self.edit_name_btn.setProperty("variant", "ghost")
        self.edit_name_btn.clicked.connect(self._edit_profile_name)
        self.edit_name_btn.setToolTip("Rename profile")
        title_layout.addWidget(self.edit_name_btn)
        title_layout.addStretch()

        save_btn = QPushButton(f"{IconManager.get('save')}  Save Profile")
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._save_profile)
        title_layout.addWidget(save_btn)

        right_layout.addWidget(title_frame)

        # Субвкладки
        self.editor_tabview = QTabWidget()
        self.editor_tabview.setDocumentMode(True)

        # DNA
        self.dna_widget = QWidget()
        self._setup_dna_tab(self.dna_widget)
        self.editor_tabview.addTab(self.dna_widget, f"{IconManager.get('dna')}  DNA")

        # Outfits
        self.outfits_widget = QWidget()
        self._setup_outfits_tab(self.outfits_widget)
        self.editor_tabview.addTab(self.outfits_widget, f"{IconManager.get('tshirt')}  Outfits")

        # Personality
        self.personality_widget = QWidget()
        self._setup_personality_tab(self.personality_widget)
        self.editor_tabview.addTab(self.personality_widget, f"{IconManager.get('mask')}  Personality")

        # Signature
        self.signature_widget = QWidget()
        self._setup_signature_tab(self.signature_widget)
        self.editor_tabview.addTab(self.signature_widget, f"{IconManager.get('star')}  Signature")

        # Atmosphere
        self.atmosphere_widget = QWidget()
        self._setup_atmosphere_tab(self.atmosphere_widget)
        self.editor_tabview.addTab(self.atmosphere_widget, f"{IconManager.get('cloud')}  Atmosphere")

        # Custom
        self.custom_widget = QWidget()
        self._setup_custom_tab(self.custom_widget)
        self.editor_tabview.addTab(self.custom_widget, f"{IconManager.get('code')}  Custom")

        # Preview
        self.preview_widget = QWidget()
        self._setup_preview_tab(self.preview_widget)
        self.editor_tabview.addTab(self.preview_widget, f"{IconManager.get('eye')}  Preview")

        self.editor_tabview.currentChanged.connect(self._on_editor_tab_changed)
        right_layout.addWidget(self.editor_tabview)

        # ═══ ПРАВАЯ ПАНЕЛЬ: Context Panel (Summary) ═══
        self.summary_panel = SummaryPanel()
        self.summary_panel.scroll_to_category.connect(self._scroll_to_dna_category)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.addWidget(self.summary_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        main_layout.addWidget(splitter)

    # ═══════════════════════════════════════════════
    # УНИВЕРСАЛЬНЫЕ ХЕЛПЕРЫ
    # ═══════════════════════════════════════════════
    def _create_chip(self, text: str, on_remove, variant: str = "chip") -> QWidget:
        """Создаёт chip-виджет (тег с крестиком)"""
        chip = QWidget()
        chip.setProperty("variant", variant)
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(10, 4, 4, 4)
        chip_layout.setSpacing(6)

        label = QLabel(text.replace('_', ' '))
        chip_layout.addWidget(label)

        remove_btn = QPushButton(f"{IconManager.get('close')}")
        remove_btn.setFixedSize(18, 18)
        remove_btn.setProperty("variant", "ghost")
        remove_btn.clicked.connect(on_remove)
        chip_layout.addWidget(remove_btn)
        return chip

    def _clear_layout(self, layout, keep_last=False):
        """Очищает layout, оставляя последний элемент (обычно stretch)"""
        end = 1 if keep_last else 0
        while layout.count() > end:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _load_tags_from_file(self, file_path: Path) -> list:
        """Загружает теги из файла с кэшированием"""
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
            self._log(f"[ERROR] Cannot read {file_path}: {e}\n")
        return tags

    def _load_tags_from_library(self, relative_path: str) -> list:
        """Загружает теги из библиотеки по относительному пути"""
        if relative_path in self._tags_cache:
            return self._tags_cache[relative_path]
        file_path = self.project_root / "prompt-library" / relative_path
        tags = []
        if not file_path.exists():
            self._log(f"[WARN] File not found: {relative_path}\n")
            return tags
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        tags.append(line)
            self._tags_cache[relative_path] = tags
        except Exception as e:
            self._log(f"[ERROR] Cannot read {relative_path}: {e}\n")
        return tags

    # ═══════════════════════════════════════════════
    # DNA TAB  (accordion-cards + check-cell grid)
    # ═══════════════════════════════════════════════
    
    def _setup_dna_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('dna')}  Character DNA")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        subtitle = QLabel("Core immutable traits. Selected tags are added to every generated prompt.")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(subtitle)

        # Chips container — Compact single-line row with overflow (§8.25)
        self.dna_chips_row = CompactChipRow()
        self.dna_chips_row.set_empty_text(
            "No DNA tags selected — expand categories and check tags"
        )
        self.dna_chips_row.remove_requested.connect(self._remove_dna_chip)
        layout.addWidget(self.dna_chips_row)

        # Поиск
        self.dna_search = QLineEdit()
        self.dna_search.setPlaceholderText(f"{IconManager.get('search')}  Search DNA tags...")
        self.dna_search.textChanged.connect(self._filter_tree)
        self.dna_search.setProperty("target_tree", "dna")
        layout.addWidget(self.dna_search)

        # Карточки категорий
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_widget = QWidget()
        self._dna_cards_layout = QVBoxLayout(cards_widget)
        self._dna_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._dna_cards_layout.setSpacing(10)
        self._dna_cards_layout.addStretch()
        cards_scroll.setWidget(cards_widget)
        layout.addWidget(cards_scroll, 1)

        self._build_dna_cards()
        self._refresh_dna_chips()

    def _build_dna_cards(self):
        # удаляем старые карточки
        for card in self._dna_cards:
            card.deleteLater()
        self._dna_cards.clear()
        self._clear_layout(self._dna_cards_layout, keep_last=True)

        selected_set = {e['tag'] for e in self.selected_dna_tags}
        for cat_name, cat_file, cat_desc in DNA_CATEGORIES:
            tags = self._load_tags_from_library(cat_file)
            card = CategoryCard(cat_name, cat_desc, tags, selected_set)
            card.toggled.connect(self._on_dna_toggled)
            self._dna_cards.append(card)
            self._dna_cards_layout.insertWidget(
                self._dna_cards_layout.count() - 1, card
            )

    def _on_dna_toggled(self, tag: str, selected: bool):
        """Колбэк от плитки: поддерживаем selected_dna_tags и chips."""
        # определяем категорию тега
        category = next(
            (c.category_name for c in self._dna_cards if tag in c.all_tags()),
            None
        )
        if category is None:
            return
        entry = {'tag': tag, 'category': category}
        if selected and entry not in self.selected_dna_tags:
            self.selected_dna_tags.append(entry)
        elif not selected and entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(entry)
        self._refresh_dna_chips()
        self._update_summary_panel()

    def _refresh_dna_chips(self):
        descriptors = [
            {
                'text': entry['tag'].replace('_', ' '),
                'variant': category_chip_variant(entry['category']),
                'color': category_full(entry['category']),
                'draw_bar': True,
                'payload': entry,
            }
            for entry in self.selected_dna_tags
        ]
        self.dna_chips_row.set_chips(descriptors)
        self._update_summary_panel()   # панель синхронизируется вместе с чипами

    def _update_summary_panel(self):
        """Обновляет правую context-панель с разбивкой по категориям."""
        if hasattr(self, 'summary_panel'):
            self.summary_panel.set_profile_name(self.current_profile_name or "")
            self.summary_panel.update_summary(self.selected_dna_tags)

    def _scroll_to_dna_category(self, category_name: str):
        """Скроллит DNA-вкладку к указанной категории."""
        if hasattr(self, '_dna_cards'):
            for card in self._dna_cards:
                if card.category_name == category_name:
                    # Раскрываем карточку, если она свёрнута
                    if not card._expanded:
                        card.set_expanded(True, animate=True)
                    # Скроллим к карточке
                    scroll_area = card.parent()
                    while scroll_area and not isinstance(scroll_area, QScrollArea):
                        scroll_area = scroll_area.parent()
                    if scroll_area:
                        scroll_area.ensureWidgetVisible(card, 0, 50)
                    break

    def _remove_dna_chip(self, entry: dict):
        if entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(entry)
        # синхронизируем плитку в нужной карточке (без сигнала)
        for card in self._dna_cards:
            if card.category_name == entry['category']:
                card.set_selected_set({e['tag'] for e in self.selected_dna_tags
                                       if e['category'] == card.category_name})
                break
        self._refresh_dna_chips()

    def _sync_dna_cards(self):
        """Синхронизация всех карточек с selected_dna_tags (load / apply / delete)."""
        for card in self._dna_cards:
            card.set_selected_set({e['tag'] for e in self.selected_dna_tags
                                   if e['category'] == card.category_name})

    def _get_all_dna_tags_map(self) -> dict:
        """{tag: category_name} по всем карточкам — замена обходу дерева."""
        m = {}
        for card in self._dna_cards:
            for t in card.all_tags():
                m[t] = card.category_name
        return m

    def _filter_dna_cards(self, text: str):
        for card in self._dna_cards:
            card.set_filter(text)

    def _update_category_counter(self, cat_item: QTreeWidgetItem):
        if not cat_item:
            return
        data = cat_item.data(0, Qt.UserRole) or {}
        cat_name = data.get('name', '')
        total = cat_item.childCount()
        selected = sum(
            1 for j in range(total)
            if cat_item.child(j).checkState(0) == Qt.Checked
        )
        cat_item.setText(0, f"{cat_name}  ({selected}/{total})")

    def _filter_tree(self, text: str):
        """Фильтрует дерево тегов по поиску. Определяет целевое дерево через property."""
        sender = self.sender()
        target = sender.property("target_tree") if sender else None
        if target == 'dna':
            self._filter_dna_cards(text)
            return
        tree_map = {
            'dna': self.dna_tree,
            'wardrobe': getattr(self, 'wardrobe_tree', None),
            'lighting': getattr(self, 'lighting_tree', None),
            'weather': getattr(self, 'weather_tree', None),
        }
        tree = tree_map.get(target)
        if not tree:
            return
        filter_lower = text.lower()
        for i in range(tree.topLevelItemCount()):
            cat_item = tree.topLevelItem(i)
            any_visible = False
            for j in range(cat_item.childCount()):
                tag_item = cat_item.child(j)
                tag_data = tag_item.data(0, Qt.UserRole) or {}
                tag_text = tag_data.get('tag', '').lower()
                is_match = filter_lower in tag_text if filter_lower else True
                tag_item.setHidden(not is_match)
                if is_match:
                    any_visible = True
            cat_item.setHidden(not any_visible)
            if any_visible and filter_lower:
                cat_item.setExpanded(True)

    # ═══════════════════════════════════════════════
    # OUTFITS TAB
    # ═══════════════════════════════════════════════
    def _setup_outfits_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('tshirt')}  Wardrobe (Whitelist)")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        subtitle = QLabel("Only these clothing tags will appear in generated prompts.")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(subtitle)

        # Chips
        chips_scroll = QScrollArea()
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setMaximumHeight(100)
        chips_scroll.setFrameShape(QFrame.NoFrame)
        chips_widget = QWidget()
        self.wardrobe_chips_layout = QHBoxLayout(chips_widget)
        self.wardrobe_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.wardrobe_chips_layout.setSpacing(6)
        self.wardrobe_chips_layout.addStretch()
        chips_scroll.setWidget(chips_widget)
        layout.addWidget(chips_scroll)

        # Поиск
        self.wardrobe_search = QLineEdit()
        self.wardrobe_search.setPlaceholderText(f"{IconManager.get('search')}  Search wardrobe...")
        self.wardrobe_search.textChanged.connect(self._filter_tree)
        self.wardrobe_search.setProperty("target_tree", "wardrobe")
        layout.addWidget(self.wardrobe_search)

        # Дерево
        self.wardrobe_tree = QTreeWidget()
        self.wardrobe_tree.setHeaderHidden(True)
        self.wardrobe_tree.setAnimated(True)
        self.wardrobe_tree.itemChanged.connect(self._on_wardrobe_item_changed)
        layout.addWidget(self.wardrobe_tree, 1)

        self._build_wardrobe_tree()
        self._refresh_wardrobe_chips()

    def _build_wardrobe_tree(self):
        self.wardrobe_tree.clear()
        clothing_dir = self.project_root / "prompt-library" / "02_clothing"
        if not clothing_dir.exists():
            return

        categories = {}
        for txt_file in sorted(clothing_dir.rglob("*.txt")):
            parts = txt_file.relative_to(clothing_dir).parts
            if len(parts) >= 2:
                main_cat = parts[0]
                sub_cat = parts[1].replace('.txt', '')
            else:
                continue
            categories.setdefault(main_cat, {})[sub_cat] = txt_file

        def sort_key(cat):
            try:
                return WARDROBE_ORDER.index(cat.lower())
            except ValueError:
                return 999

        for main_cat in sorted(categories.keys(), key=sort_key):
            cat_item = QTreeWidgetItem([main_cat.replace('_', ' ').title()])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setData(0, Qt.UserRole, {'type': 'category', 'name': main_cat})

            for sub_cat, file_path in sorted(categories[main_cat].items()):
                sub_item = QTreeWidgetItem([sub_cat.replace('_', ' ').title()])
                sub_item.setFlags(sub_item.flags() & ~Qt.ItemIsSelectable)
                sub_font = sub_item.font(0)
                sub_font.setItalic(True)
                sub_item.setFont(0, sub_font)
                sub_item.setData(0, Qt.UserRole, {'type': 'subcategory', 'name': sub_cat})

                tags = self._load_tags_from_file(file_path)
                for tag in tags:
                    tag_item = QTreeWidgetItem([tag.replace('_', ' ')])
                    tag_item.setFlags(tag_item.flags() | Qt.ItemIsUserCheckable)
                    tag_item.setCheckState(0, Qt.Unchecked)
                    tag_item.setData(0, Qt.UserRole, {
                        'type': 'tag', 'tag': tag, 'subcategory': sub_cat
                    })
                    sub_item.addChild(tag_item)
                cat_item.addChild(sub_item)
            self.wardrobe_tree.addTopLevelItem(cat_item)

    def _on_wardrobe_item_changed(self, item: QTreeWidgetItem, column: int):
        if column != 0:
            return
        data = item.data(0, Qt.UserRole) or {}
        if data.get('type') != 'tag':
            return
        tag = data['tag']
        subcategory = data['subcategory']
        tag_entry = {'tag': tag, 'subcategory': subcategory}
        if item.checkState(0) == Qt.Checked:
            if tag_entry not in self.selected_wardrobe_tags:
                self.selected_wardrobe_tags.append(tag_entry)
        else:
            if tag_entry in self.selected_wardrobe_tags:
                self.selected_wardrobe_tags.remove(tag_entry)
        # Обновляем счётчики для подкатегории и категории
        parent_subcat = item.parent()
        if parent_subcat:
            self._update_wardrobe_subcat_counter(parent_subcat)
            parent_cat = parent_subcat.parent()
            if parent_cat:
                self._update_wardrobe_cat_counter(parent_cat)
        self._refresh_wardrobe_chips()

    def _update_wardrobe_subcat_counter(self, subcat_item: QTreeWidgetItem):
        data = subcat_item.data(0, Qt.UserRole) or {}
        name = data.get('name', '').replace('_', ' ').title()
        total = subcat_item.childCount()
        selected = sum(1 for j in range(total) if subcat_item.child(j).checkState(0) == Qt.Checked)
        subcat_item.setText(0, f"{name}  ({selected}/{total})")

    def _update_wardrobe_cat_counter(self, cat_item: QTreeWidgetItem):
        data = cat_item.data(0, Qt.UserRole) or {}
        name = data.get('name', '').replace('_', ' ').title()
        total = 0
        selected = 0
        for j in range(cat_item.childCount()):
            sub = cat_item.child(j)
            total += sub.childCount()
            selected += sum(1 for k in range(sub.childCount()) if sub.child(k).checkState(0) == Qt.Checked)
        cat_item.setText(0, f"{name}  ({selected}/{total})")

    def _refresh_wardrobe_chips(self):
        self._clear_layout(self.wardrobe_chips_layout, keep_last=True)
        if not self.selected_wardrobe_tags:
            placeholder = QLabel("(No wardrobe tags selected)")
            placeholder.setObjectName("Subtitle")
            self.wardrobe_chips_layout.insertWidget(0, placeholder)
            return
        for entry in self.selected_wardrobe_tags:
            chip = self._create_chip(
                entry['tag'],
                lambda checked=False, e=entry: self._remove_wardrobe_chip(e)
            )
            self.wardrobe_chips_layout.insertWidget(
                self.wardrobe_chips_layout.count() - 1, chip
            )

    def _remove_wardrobe_chip(self, entry: dict):
        if entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(entry)
        # Найти и снять чекбокс
        for i in range(self.wardrobe_tree.topLevelItemCount()):
            cat_item = self.wardrobe_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                sub_item = cat_item.child(j)
                sub_data = sub_item.data(0, Qt.UserRole) or {}
                if sub_data.get('name') != entry['subcategory']:
                    continue
                for k in range(sub_item.childCount()):
                    tag_item = sub_item.child(k)
                    tag_data = tag_item.data(0, Qt.UserRole) or {}
                    if tag_data.get('tag') == entry['tag']:
                        tag_item.blockSignals(True)
                        tag_item.setCheckState(0, Qt.Unchecked)
                        tag_item.blockSignals(False)
                        break
                self._update_wardrobe_subcat_counter(sub_item)
                self._update_wardrobe_cat_counter(cat_item)
                break
        self._refresh_wardrobe_chips()

    # ═══════════════════════════════════════════════
    # PERSONALITY TAB (Tri-state: Unchecked / Prefer / Avoid)
    # ═══════════════════════════════════════════════
    def _setup_personality_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('mask')}  Personality Filters")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        # Легенда
        legend = QLabel(
            f"{IconManager.get('check')} Checked = Prefer    "
            f"{IconManager.get('minus')} Dashed = Avoid    "
            f"Unchecked = Neutral"
        )
        legend.setObjectName("Subtitle")
        layout.addWidget(legend)

        # Prefer chips
        prefer_frame = QWidget()
        prefer_layout = QVBoxLayout(prefer_frame)
        prefer_layout.setContentsMargins(0, 0, 0, 0)
        prefer_layout.setSpacing(4)
        prefer_label = QLabel(f"{IconManager.get('check')}  Preferred")
        prefer_label.setObjectName("Subtitle")
        prefer_layout.addWidget(prefer_label)
        prefer_scroll = QScrollArea()
        prefer_scroll.setWidgetResizable(True)
        prefer_scroll.setMaximumHeight(70)
        prefer_scroll.setFrameShape(QFrame.NoFrame)
        prefer_widget = QWidget()
        self.prefer_chips_layout = QHBoxLayout(prefer_widget)
        self.prefer_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.prefer_chips_layout.setSpacing(6)
        self.prefer_chips_layout.addStretch()
        prefer_scroll.setWidget(prefer_widget)
        prefer_layout.addWidget(prefer_scroll)
        layout.addWidget(prefer_frame)

        # Avoid chips
        avoid_frame = QWidget()
        avoid_layout = QVBoxLayout(avoid_frame)
        avoid_layout.setContentsMargins(0, 0, 0, 0)
        avoid_layout.setSpacing(4)
        avoid_label = QLabel(f"{IconManager.get('close')}  Avoided")
        avoid_label.setObjectName("Subtitle")
        avoid_layout.addWidget(avoid_label)
        avoid_scroll = QScrollArea()
        avoid_scroll.setWidgetResizable(True)
        avoid_scroll.setMaximumHeight(70)
        avoid_scroll.setFrameShape(QFrame.NoFrame)
        avoid_widget = QWidget()
        self.avoid_chips_layout = QHBoxLayout(avoid_widget)
        self.avoid_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.avoid_chips_layout.setSpacing(6)
        self.avoid_chips_layout.addStretch()
        avoid_scroll.setWidget(avoid_widget)
        avoid_layout.addWidget(avoid_scroll)
        layout.addWidget(avoid_frame)

        # Поиск
        self.personality_search = QLineEdit()
        self.personality_search.setPlaceholderText(f"{IconManager.get('search')}  Search expressions / poses...")
        self.personality_search.textChanged.connect(self._filter_tree)
        self.personality_search.setProperty("target_tree", "personality")
        layout.addWidget(self.personality_search)

        # Дерево с tri-state чекбоксами
        self.personality_tree = QTreeWidget()
        self.personality_tree.setHeaderHidden(True)
        self.personality_tree.setAnimated(True)
        self.personality_tree.itemChanged.connect(self._on_personality_item_changed)
        layout.addWidget(self.personality_tree, 1)

        self._build_personality_tree()
        self._refresh_personality_chips()

    def _build_personality_tree(self):
        self.personality_tree.clear()
        for cat_name, cat_dir, subcat_order in PERSONALITY_CATEGORIES:
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setData(0, Qt.UserRole, {'type': 'category', 'name': cat_name})

            dir_path = self.project_root / "prompt-library" / cat_dir
            if not dir_path.exists():
                self.personality_tree.addTopLevelItem(cat_item)
                continue

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
                sub_item = QTreeWidgetItem([sub_cat.replace('_', ' ').title()])
                sub_item.setFlags(sub_item.flags() & ~Qt.ItemIsSelectable)
                sub_font = sub_item.font(0)
                sub_font.setItalic(True)
                sub_item.setFont(0, sub_font)
                sub_item.setData(0, Qt.UserRole, {'type': 'subcategory', 'name': sub_cat, 'category': cat_name})

                tags = self._load_tags_from_file(subcats[sub_cat])
                for tag in tags:
                    tag_item = QTreeWidgetItem([tag.replace('_', ' ')])
                    tag_item.setFlags(tag_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsUserTristate)
                    tag_item.setCheckState(0, Qt.Unchecked)
                    tag_item.setData(0, Qt.UserRole, {
                        'type': 'tag', 'tag': tag,
                        'category': cat_name, 'subcategory': sub_cat
                    })
                    sub_item.addChild(tag_item)
                cat_item.addChild(sub_item)
            self.personality_tree.addTopLevelItem(cat_item)

    def _on_personality_item_changed(self, item: QTreeWidgetItem, column: int):
        if column != 0:
            return
        data = item.data(0, Qt.UserRole) or {}
        if data.get('type') != 'tag':
            return
        tag = data['tag']
        category = data['category']
        subcategory = data['subcategory']
        tag_entry = {'tag': tag, 'category': category, 'subcategory': subcategory}

        state = item.checkState(0)
        # Удаляем из обоих списков
        self.preferred_personality_tags = [t for t in self.preferred_personality_tags if t['tag'] != tag]
        self.avoided_personality_tags = [t for t in self.avoided_personality_tags if t['tag'] != tag]

        if state == Qt.Checked:
            self.preferred_personality_tags.append(tag_entry)
        elif state == Qt.PartiallyChecked:
            self.avoided_personality_tags.append(tag_entry)
        # Qt.Unchecked → ничего не добавляем

        self._refresh_personality_chips()

    def _refresh_personality_chips(self):
        self._clear_layout(self.prefer_chips_layout, keep_last=True)
        self._clear_layout(self.avoid_chips_layout, keep_last=True)

        if not self.preferred_personality_tags:
            ph = QLabel("(empty)")
            ph.setObjectName("Subtitle")
            self.prefer_chips_layout.insertWidget(0, ph)
        else:
            for entry in self.preferred_personality_tags:
                chip = self._create_chip(
                    entry['tag'],
                    lambda checked=False, t=entry['tag']: self._remove_personality_tag(t),
                    variant="chip-success"
                )
                self.prefer_chips_layout.insertWidget(
                    self.prefer_chips_layout.count() - 1, chip
                )

        if not self.avoided_personality_tags:
            ph = QLabel("(empty)")
            ph.setObjectName("Subtitle")
            self.avoid_chips_layout.insertWidget(0, ph)
        else:
            for entry in self.avoided_personality_tags:
                chip = self._create_chip(
                    entry['tag'],
                    lambda checked=False, t=entry['tag']: self._remove_personality_tag(t),
                    variant="chip-danger"
                )
                self.avoid_chips_layout.insertWidget(
                    self.avoid_chips_layout.count() - 1, chip
                )

    def _remove_personality_tag(self, tag: str):
        # Удаляем из списков
        self.preferred_personality_tags = [t for t in self.preferred_personality_tags if t['tag'] != tag]
        self.avoided_personality_tags = [t for t in self.avoided_personality_tags if t['tag'] != tag]
        # Сбрасываем чекбокс в дереве
        for i in range(self.personality_tree.topLevelItemCount()):
            cat_item = self.personality_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                sub_item = cat_item.child(j)
                for k in range(sub_item.childCount()):
                    tag_item = sub_item.child(k)
                    tag_data = tag_item.data(0, Qt.UserRole) or {}
                    if tag_data.get('tag') == tag:
                        tag_item.blockSignals(True)
                        tag_item.setCheckState(0, Qt.Unchecked)
                        tag_item.blockSignals(False)
                        break
        self._refresh_personality_chips()

    # ═══════════════════════════════════════════════
    # SIGNATURE TAB
    # ═══════════════════════════════════════════════
    def _setup_signature_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('star')}  Signature Items & Hair Rules")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(16)

        # ═══ PROPS SECTION ═══
        props_header = QWidget()
        props_header_layout = QHBoxLayout(props_header)
        props_header_layout.setContentsMargins(0, 0, 0, 0)
        props_label = QLabel(f"{IconManager.get('book')}  Signature Props")
        props_label.setObjectName("SectionTitle")
        props_header_layout.addWidget(props_label)
        props_header_layout.addStretch()
        add_prop_btn = QPushButton(f"{IconManager.get('add')}  Add Prop")
        add_prop_btn.setProperty("variant", "success")
        add_prop_btn.clicked.connect(self._add_signature_prop)
        props_header_layout.addWidget(add_prop_btn)
        scroll_layout.addWidget(props_header)

        self.props_container = QVBoxLayout()
        self.props_container.setSpacing(8)
        scroll_layout.addLayout(self.props_container)

        # ═══ HAIR RULES SECTION ═══
        hair_header = QWidget()
        hair_header_layout = QHBoxLayout(hair_header)
        hair_header_layout.setContentsMargins(0, 12, 0, 0)
        hair_label = QLabel(f"{IconManager.get('user')}  Hair Rules")
        hair_label.setObjectName("SectionTitle")
        hair_header_layout.addWidget(hair_label)
        hair_header_layout.addStretch()
        scroll_layout.addWidget(hair_header)

        # Default style
        default_card = QWidget()
        default_card.setProperty("variant", "card")
        default_card_layout = QVBoxLayout(default_card)
        default_card_layout.setContentsMargins(16, 12, 16, 12)
        default_card_layout.setSpacing(8)

        default_row = QHBoxLayout()
        default_row.setContentsMargins(0, 0, 0, 0)
        default_lbl = QLabel("Default Style:")
        default_lbl.setObjectName("Subtitle")
        default_lbl.setFixedWidth(120)
        default_row.addWidget(default_lbl)
        self.hair_default_btn = QPushButton(f"{IconManager.get('chevron-down')}  hair down")
        self.hair_default_btn.setProperty("variant", "section-toggle")
        self.hair_default_btn.clicked.connect(self._open_default_style_selector)
        default_row.addWidget(self.hair_default_btn, 1)
        default_card_layout.addLayout(default_row)
        scroll_layout.addWidget(default_card)

        # Conditional rules header
        cond_header = QWidget()
        cond_layout = QHBoxLayout(cond_header)
        cond_layout.setContentsMargins(0, 8, 0, 0)
        cond_lbl = QLabel("Conditional Rules:")
        cond_lbl.setObjectName("Subtitle")
        cond_layout.addWidget(cond_lbl)
        cond_layout.addStretch()
        add_rule_btn = QPushButton(f"{IconManager.get('add')}  Add Rule")
        add_rule_btn.setProperty("variant", "success")
        add_rule_btn.clicked.connect(self._add_hair_rule)
        cond_layout.addWidget(add_rule_btn)
        scroll_layout.addWidget(cond_header)

        self.hair_rules_container = QVBoxLayout()
        self.hair_rules_container.setSpacing(8)
        scroll_layout.addLayout(self.hair_rules_container)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self._refresh_signature_props_display()
        self._refresh_hair_rules_display()

    def _add_signature_prop(self):
        self.signature_props.append({'name': 'new_item', 'tags': []})
        self._refresh_signature_props_display()

    def _remove_signature_prop(self, index: int):
        if 0 <= index < len(self.signature_props):
            self.signature_props.pop(index)
            self._refresh_signature_props_display()

    def _update_prop_name(self, index: int, new_name: str):
        if 0 <= index < len(self.signature_props):
            self.signature_props[index]['name'] = new_name.strip()

    def _add_tag_to_prop(self, index: int):
        if 0 <= index < len(self.signature_props):
            self.signature_props[index]['tags'].append('new_tag')
            self._refresh_signature_props_display()

    def _remove_tag_from_prop(self, prop_index: int, tag_index: int):
        if 0 <= prop_index < len(self.signature_props):
            tags = self.signature_props[prop_index]['tags']
            if 0 <= tag_index < len(tags):
                tags.pop(tag_index)
                self._refresh_signature_props_display()

    def _update_prop_tag(self, prop_index: int, tag_index: int, new_tag: str):
        if 0 <= prop_index < len(self.signature_props):
            tags = self.signature_props[prop_index]['tags']
            if 0 <= tag_index < len(tags):
                tags[tag_index] = new_tag.strip()

    def _refresh_signature_props_display(self):
        self._clear_layout(self.props_container, keep_last=False)
        if not self.signature_props:
            label = QLabel("(No signature props — click 'Add Prop')")
            label.setObjectName("Subtitle")
            self.props_container.addWidget(label)
            return
        for i, prop in enumerate(self.signature_props):
            card = QWidget()
            card.setProperty("variant", "card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(8)

            # Header
            header_row = QHBoxLayout()
            header_row.setContentsMargins(0, 0, 0, 0)
            name_lbl = QLabel("Prop name:")
            name_lbl.setObjectName("Subtitle")
            header_row.addWidget(name_lbl)
            name_entry = QLineEdit()
            name_entry.setPlaceholderText("Item name")
            name_entry.setText(prop['name'])
            name_entry.textChanged.connect(lambda text, idx=i: self._update_prop_name(idx, text))
            header_row.addWidget(name_entry, 1)

            del_btn = QPushButton(f"{IconManager.get('delete')}  Delete")
            del_btn.setProperty("variant", "danger")
            del_btn.clicked.connect(lambda checked=False, idx=i: self._remove_signature_prop(idx))
            header_row.addWidget(del_btn)
            card_layout.addLayout(header_row)

            # Tags
            tags_lbl = QLabel(f"{IconManager.get('tag')}  Tags")
            tags_lbl.setObjectName("Subtitle")
            card_layout.addWidget(tags_lbl)

            for j, tag in enumerate(prop['tags']):
                tag_row = QHBoxLayout()
                tag_row.setContentsMargins(8, 0, 0, 0)
                tag_row.setSpacing(6)
                tag_entry = QLineEdit()
                tag_entry.setText(tag)
                tag_entry.textChanged.connect(lambda text, pi=i, ti=j: self._update_prop_tag(pi, ti, text))
                tag_row.addWidget(tag_entry, 1)

                browse_btn = QPushButton(f"{IconManager.get('folder')}")
                browse_btn.setProperty("variant", "ghost")
                browse_btn.setToolTip("Browse tags")
                browse_btn.clicked.connect(lambda checked=False, pi=i: self._open_tags_browser(pi))
                tag_row.addWidget(browse_btn)

                rm_btn = QPushButton(f"{IconManager.get('close')}")
                rm_btn.setFixedSize(25, 25)
                rm_btn.setProperty("variant", "danger")
                rm_btn.clicked.connect(lambda checked=False, pi=i, ti=j: self._remove_tag_from_prop(pi, ti))
                tag_row.addWidget(rm_btn)
                card_layout.addLayout(tag_row)

            add_tag_btn = QPushButton(f"{IconManager.get('add')}  Add Tag")
            add_tag_btn.setProperty("variant", "ghost")
            add_tag_btn.clicked.connect(lambda checked=False, idx=i: self._add_tag_to_prop(idx))
            card_layout.addWidget(add_tag_btn)

            self.props_container.addWidget(card)

    def _open_tags_browser(self, prop_index: int):
        dialog = QDialog(self)
        dialog.setWindowTitle("Browse Tags (Props)")
        dialog.resize(500, 600)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"{IconManager.get('book')}  Select tags (multiple allowed)")
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        props_dir = self.project_root / "prompt-library" / "09_props"
        if not props_dir.exists():
            err = QLabel(f"Folder not found: {props_dir}")
            err.setObjectName("SemanticError")
            scroll_layout.addWidget(err)
        else:
            current_tags = set(self.signature_props[prop_index]['tags'])
            self._popup_selected_tags = set(current_tags)
            for txt_file in sorted(props_dir.rglob("*.txt")):
                tags = self._load_tags_from_file(txt_file)
                if tags:
                    cat_lbl = QLabel(f"{IconManager.get('folder')}  {txt_file.stem.replace('_', ' ').title()}")
                    cat_lbl.setObjectName("Subtitle")
                    scroll_layout.addWidget(cat_lbl)
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._apply_tags_browser(prop_index, dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _toggle_tag_selection(self, tag: str, checked: bool):
        if checked:
            self._popup_selected_tags.add(tag)
        else:
            self._popup_selected_tags.discard(tag)

    def _apply_tags_browser(self, prop_index: int, dialog):
        self.signature_props[prop_index]['tags'] = sorted(list(self._popup_selected_tags))
        self._refresh_signature_props_display()
        dialog.accept()

    def _add_hair_rule(self):
        hair_tags = self._load_tags_from_library("01_character/hair/style.txt")
        default_style = hair_tags[0] if hair_tags else "hair down"
        self.hair_rules_data['conditional'].append({
            'if_action': [], 'style': default_style, 'probability': 0.5
        })
        self._refresh_hair_rules_display()

    def _remove_hair_rule(self, index: int):
        if 0 <= index < len(self.hair_rules_data['conditional']):
            self.hair_rules_data['conditional'].pop(index)
            self._refresh_hair_rules_display()

    def _update_hair_rule_style(self, index: int, style: str):
        if 0 <= index < len(self.hair_rules_data['conditional']):
            self.hair_rules_data['conditional'][index]['style'] = style

    def _update_hair_rule_probability(self, index: int, prob_str: str):
        try:
            prob = float(prob_str)
            if 0 <= prob <= 1:
                self.hair_rules_data['conditional'][index]['probability'] = prob
        except ValueError:
            pass

    def _update_hair_rule_actions(self, index: int, actions_str: str):
        if 0 <= index < len(self.hair_rules_data['conditional']):
            actions = [a.strip() for a in actions_str.split(',') if a.strip()]
            self.hair_rules_data['conditional'][index]['if_action'] = actions

    def _refresh_hair_rules_display(self):
        self._clear_layout(self.hair_rules_container, keep_last=False)

        # Обновляем кнопку default
        if hasattr(self, 'hair_default_btn'):
            current_default = self.hair_rules_data.get('default', 'hair down')
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = f"  {IconManager.get('star')}" if current_default in dna_styles else ""
            self.hair_default_btn.setText(f"{IconManager.get('chevron-down')}  {current_default}{star}")

        if not self.hair_rules_data['conditional']:
            label = QLabel("(No conditional rules — click 'Add Rule')")
            label.setObjectName("Subtitle")
            self.hair_rules_container.addWidget(label)
            return

        for i, rule in enumerate(self.hair_rules_data['conditional']):
            card = QWidget()
            card.setProperty("variant", "card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(8)

            # Header
            header_row = QHBoxLayout()
            header_row.setContentsMargins(0, 0, 0, 0)
            rule_lbl = QLabel(f"{IconManager.get('wand')}  Rule #{i + 1}")
            rule_lbl.setObjectName("Subtitle")
            header_row.addWidget(rule_lbl)
            header_row.addStretch()
            del_btn = QPushButton(f"{IconManager.get('delete')}  Delete")
            del_btn.setProperty("variant", "danger")
            del_btn.clicked.connect(lambda checked=False, idx=i: self._remove_hair_rule(idx))
            header_row.addWidget(del_btn)
            card_layout.addLayout(header_row)

            # If actions
            actions_row = QHBoxLayout()
            actions_row.setContentsMargins(0, 0, 0, 0)
            actions_lbl = QLabel("If actions:")
            actions_lbl.setFixedWidth(100)
            actions_lbl.setObjectName("Subtitle")
            actions_row.addWidget(actions_lbl)
            actions_entry = QLineEdit()
            actions_entry.setPlaceholderText("reading, studying, ...")
            actions_entry.setText(", ".join(rule['if_action']))
            actions_entry.textChanged.connect(lambda text, idx=i: self._update_hair_rule_actions(idx, text))
            actions_row.addWidget(actions_entry, 1)
            browse_btn = QPushButton(f"{IconManager.get('folder')}")
            browse_btn.setProperty("variant", "ghost")
            browse_btn.clicked.connect(lambda checked=False, idx=i, ae=actions_entry: self._open_actions_browser(idx, ae))
            actions_row.addWidget(browse_btn)
            card_layout.addLayout(actions_row)

            # Style
            style_row = QHBoxLayout()
            style_row.setContentsMargins(0, 0, 0, 0)
            style_lbl = QLabel("Style:")
            style_lbl.setFixedWidth(100)
            style_lbl.setObjectName("Subtitle")
            style_row.addWidget(style_lbl)
            style_text = rule['style'] or "Select..."
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = f"  {IconManager.get('star')}" if rule['style'] in dna_styles else ""
            style_btn = QPushButton(f"{IconManager.get('chevron-down')}  {style_text}{star}")
            style_btn.setProperty("variant", "section-toggle")
            style_btn.clicked.connect(lambda checked=False, idx=i, btn=style_btn: self._open_style_selector(idx, btn))
            style_row.addWidget(style_btn, 1)
            card_layout.addLayout(style_row)

            # Probability
            prob_row = QHBoxLayout()
            prob_row.setContentsMargins(0, 0, 0, 0)
            prob_lbl = QLabel("Probability:")
            prob_lbl.setFixedWidth(100)
            prob_lbl.setObjectName("Subtitle")
            prob_row.addWidget(prob_lbl)
            prob_slider = QSlider(Qt.Horizontal)
            prob_slider.setMinimum(0)
            prob_slider.setMaximum(100)
            prob_slider.setValue(int(rule['probability'] * 100))
            prob_slider.valueChanged.connect(lambda val, idx=i: self._update_prob_from_slider(idx, val / 100))
            prob_row.addWidget(prob_slider, 1)
            prob_entry = QLineEdit()
            prob_entry.setFixedWidth(60)
            prob_entry.setText(str(rule['probability']))
            prob_entry.textChanged.connect(lambda text, idx=i, slider=prob_slider: self._update_prob_from_entry(idx, text, slider))
            prob_row.addWidget(prob_entry)
            card_layout.addLayout(prob_row)

            self.hair_rules_container.addWidget(card)

    def _open_style_selector(self, rule_index: int, button_widget):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Hair Style")
        dialog.resize(350, 500)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"{IconManager.get('user')}  Select hair style")
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = f"  {IconManager.get('star')}" if tag in dna_styles else ""
            btn = QPushButton(f"{tag}{star}")
            btn.setProperty("variant", "ghost")
            btn.clicked.connect(lambda checked=False, t=tag: self._select_style(t, rule_index, button_widget, dialog))
            scroll_layout.addWidget(btn)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        dialog.exec()

    def _select_style(self, style: str, rule_index: int, button_widget, dialog):
        self._update_hair_rule_style(rule_index, style)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        star = f"  {IconManager.get('star')}" if style in dna_styles else ""
        button_widget.setText(f"{IconManager.get('chevron-down')}  {style}{star}")
        dialog.accept()

    def _open_default_style_selector(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Default Hair Style")
        dialog.resize(350, 500)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"{IconManager.get('user')}  Select default hair style")
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = f"  {IconManager.get('star')}" if tag in dna_styles else ""
            btn = QPushButton(f"{tag}{star}")
            btn.setProperty("variant", "ghost")
            btn.clicked.connect(lambda checked=False, t=tag: self._select_default_style(t, dialog))
            scroll_layout.addWidget(btn)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        dialog.exec()

    def _select_default_style(self, style: str, dialog):
        self.hair_rules_data['default'] = style
        if hasattr(self, 'hair_default_btn'):
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = f"  {IconManager.get('star')}" if style in dna_styles else ""
            self.hair_default_btn.setText(f"{IconManager.get('chevron-down')}  {style}{star}")
        dialog.accept()

    def _open_actions_browser(self, rule_index: int, entry_widget):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Actions")
        dialog.resize(500, 600)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"{IconManager.get('movie')}  Select actions")
        label.setObjectName("SectionTitle")
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
                    cat_lbl = QLabel(f"{IconManager.get('folder')}  {txt_file.stem.replace('_', ' ').title()}")
                    cat_lbl.setObjectName("Subtitle")
                    scroll_layout.addWidget(cat_lbl)
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
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._apply_actions_browser(rule_index, entry_widget, dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _toggle_action_selection(self, tag: str, checked: bool):
        if checked:
            self._popup_selected_actions.add(tag)
        else:
            self._popup_selected_actions.discard(tag)

    def _apply_actions_browser(self, rule_index: int, entry_widget, dialog):
        actions_list = sorted(list(self._popup_selected_actions))
        self.hair_rules_data['conditional'][rule_index]['if_action'] = actions_list
        entry_widget.setText(", ".join(actions_list))
        dialog.accept()

    def _update_prob_from_slider(self, rule_index: int, value: float):
        rounded_value = round(value, 2)
        self._update_hair_rule_probability(rule_index, str(rounded_value))

    def _update_prob_from_entry(self, rule_index: int, value_str: str, slider_widget):
        try:
            value = float(value_str)
            if 0 <= value <= 1:
                self._update_hair_rule_probability(rule_index, value_str)
                slider_widget.setValue(int(value * 100))
        except ValueError:
            pass

    # ═══════════════════════════════════════════════
    # ATMOSPHERE TAB (Lighting + Weather)
    # ═══════════════════════════════════════════════
    def _setup_atmosphere_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QLabel(f"{IconManager.get('cloud')}  Atmosphere Preferences")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # ═══ LIGHTING ═══
        lighting_group = QGroupBox(f"{IconManager.get('star')}  Lighting Preferences")
        lighting_layout = QVBoxLayout(lighting_group)
        lighting_layout.setSpacing(8)

        # Lighting chips
        lighting_chips_scroll = QScrollArea()
        lighting_chips_scroll.setWidgetResizable(True)
        lighting_chips_scroll.setMaximumHeight(70)
        lighting_chips_scroll.setFrameShape(QFrame.NoFrame)
        lighting_chips_widget = QWidget()
        self.lighting_chips_layout = QHBoxLayout(lighting_chips_widget)
        self.lighting_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.lighting_chips_layout.setSpacing(6)
        self.lighting_chips_layout.addStretch()
        lighting_chips_scroll.setWidget(lighting_chips_widget)
        lighting_layout.addWidget(lighting_chips_scroll)

        # Lighting search
        self.lighting_search = QLineEdit()
        self.lighting_search.setPlaceholderText(f"{IconManager.get('search')}  Search lighting...")
        self.lighting_search.textChanged.connect(self._filter_tree)
        self.lighting_search.setProperty("target_tree", "lighting")
        lighting_layout.addWidget(self.lighting_search)

        # Lighting tree
        self.lighting_tree = QTreeWidget()
        self.lighting_tree.setHeaderHidden(True)
        self.lighting_tree.setAnimated(True)
        self.lighting_tree.itemChanged.connect(self._on_lighting_item_changed)
        lighting_layout.addWidget(self.lighting_tree, 1)

        scroll_layout.addWidget(lighting_group)

        # ═══ WEATHER ═══
        weather_group = QGroupBox(f"{IconManager.get('cloud')}  Weather Preferences")
        weather_layout = QVBoxLayout(weather_group)
        weather_layout.setSpacing(8)

        # Weather chips
        weather_chips_scroll = QScrollArea()
        weather_chips_scroll.setWidgetResizable(True)
        weather_chips_scroll.setMaximumHeight(70)
        weather_chips_scroll.setFrameShape(QFrame.NoFrame)
        weather_chips_widget = QWidget()
        self.weather_chips_layout = QHBoxLayout(weather_chips_widget)
        self.weather_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.weather_chips_layout.setSpacing(6)
        self.weather_chips_layout.addStretch()
        weather_chips_scroll.setWidget(weather_chips_widget)
        weather_layout.addWidget(weather_chips_scroll)

        # Weather search
        self.weather_search = QLineEdit()
        self.weather_search.setPlaceholderText(f"{IconManager.get('search')}  Search weather...")
        self.weather_search.textChanged.connect(self._filter_tree)
        self.weather_search.setProperty("target_tree", "weather")
        weather_layout.addWidget(self.weather_search)

        # Weather tree
        self.weather_tree = QTreeWidget()
        self.weather_tree.setHeaderHidden(True)
        self.weather_tree.setAnimated(True)
        self.weather_tree.itemChanged.connect(self._on_weather_item_changed)
        weather_layout.addWidget(self.weather_tree, 1)

        scroll_layout.addWidget(weather_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        self._build_lighting_tree()
        self._build_weather_tree()
        self._refresh_lighting_chips()
        self._refresh_weather_chips()

    def _build_lighting_tree(self):
        self.lighting_tree.clear()
        lighting_dir = self.project_root / "prompt-library" / "07_lighting"
        if not lighting_dir.exists():
            return
        subcats = {}
        for txt_file in sorted(lighting_dir.rglob("*.txt")):
            parts = txt_file.relative_to(lighting_dir).parts
            if len(parts) == 1:
                sub_cat = parts[0].replace('.txt', '')
            elif len(parts) >= 2:
                sub_cat = parts[0]
            else:
                continue
            subcats[sub_cat] = txt_file

        for sub_cat, file_path in sorted(subcats.items()):
            cat_item = QTreeWidgetItem([sub_cat.replace('_', ' ').title()])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setData(0, Qt.UserRole, {'type': 'category', 'name': sub_cat})

            tags = self._load_tags_from_file(file_path)
            for tag in tags:
                tag_item = QTreeWidgetItem([tag.replace('_', ' ')])
                tag_item.setFlags(tag_item.flags() | Qt.ItemIsUserCheckable)
                tag_item.setCheckState(0, Qt.Unchecked)
                tag_item.setData(0, Qt.UserRole, {'type': 'tag', 'tag': tag})
                cat_item.addChild(tag_item)
            self.lighting_tree.addTopLevelItem(cat_item)

    def _build_weather_tree(self):
        self.weather_tree.clear()
        weather_dir = self.project_root / "prompt-library" / "10_weather"
        if not weather_dir.exists():
            return
        subcats = {}
        for txt_file in sorted(weather_dir.rglob("*.txt")):
            parts = txt_file.relative_to(weather_dir).parts
            if len(parts) == 1:
                sub_cat = parts[0].replace('.txt', '')
            elif len(parts) >= 2:
                sub_cat = parts[0]
            else:
                continue
            subcats[sub_cat] = txt_file

        for sub_cat, file_path in sorted(subcats.items()):
            cat_item = QTreeWidgetItem([sub_cat.replace('_', ' ').title()])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setData(0, Qt.UserRole, {'type': 'category', 'name': sub_cat})

            tags = self._load_tags_from_file(file_path)
            for tag in tags:
                tag_item = QTreeWidgetItem([tag.replace('_', ' ')])
                tag_item.setFlags(tag_item.flags() | Qt.ItemIsUserCheckable)
                tag_item.setCheckState(0, Qt.Unchecked)
                tag_item.setData(0, Qt.UserRole, {'type': 'tag', 'tag': tag})
                cat_item.addChild(tag_item)
            self.weather_tree.addTopLevelItem(cat_item)

    def _on_lighting_item_changed(self, item: QTreeWidgetItem, column: int):
        if column != 0:
            return
        data = item.data(0, Qt.UserRole) or {}
        if data.get('type') != 'tag':
            return
        tag = data['tag']
        if item.checkState(0) == Qt.Checked:
            if tag not in self.selected_lighting_tags:
                self.selected_lighting_tags.append(tag)
        else:
            if tag in self.selected_lighting_tags:
                self.selected_lighting_tags.remove(tag)
        self._update_category_counter(item.parent())
        self._refresh_lighting_chips()

    def _on_weather_item_changed(self, item: QTreeWidgetItem, column: int):
        if column != 0:
            return
        data = item.data(0, Qt.UserRole) or {}
        if data.get('type') != 'tag':
            return
        tag = data['tag']
        if item.checkState(0) == Qt.Checked:
            if tag not in self.selected_weather_tags:
                self.selected_weather_tags.append(tag)
        else:
            if tag in self.selected_weather_tags:
                self.selected_weather_tags.remove(tag)
        self._update_category_counter(item.parent())
        self._refresh_weather_chips()

    def _refresh_lighting_chips(self):
        self._clear_layout(self.lighting_chips_layout, keep_last=True)
        if not self.selected_lighting_tags:
            ph = QLabel("(No lighting selected)")
            ph.setObjectName("Subtitle")
            self.lighting_chips_layout.insertWidget(0, ph)
            return
        for tag in self.selected_lighting_tags:
            chip = self._create_chip(
                tag, lambda checked=False, t=tag: self._remove_lighting_chip(t)
            )
            self.lighting_chips_layout.insertWidget(
                self.lighting_chips_layout.count() - 1, chip
            )

    def _refresh_weather_chips(self):
        self._clear_layout(self.weather_chips_layout, keep_last=True)
        if not self.selected_weather_tags:
            ph = QLabel("(No weather selected)")
            ph.setObjectName("Subtitle")
            self.weather_chips_layout.insertWidget(0, ph)
            return
        for tag in self.selected_weather_tags:
            chip = self._create_chip(
                tag, lambda checked=False, t=tag: self._remove_weather_chip(t)
            )
            self.weather_chips_layout.insertWidget(
                self.weather_chips_layout.count() - 1, chip
            )

    def _remove_lighting_chip(self, tag: str):
        if tag in self.selected_lighting_tags:
            self.selected_lighting_tags.remove(tag)
        for i in range(self.lighting_tree.topLevelItemCount()):
            cat_item = self.lighting_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                tag_item = cat_item.child(j)
                tag_data = tag_item.data(0, Qt.UserRole) or {}
                if tag_data.get('tag') == tag:
                    tag_item.blockSignals(True)
                    tag_item.setCheckState(0, Qt.Unchecked)
                    tag_item.blockSignals(False)
                    self._update_category_counter(cat_item)
                    break
        self._refresh_lighting_chips()

    def _remove_weather_chip(self, tag: str):
        if tag in self.selected_weather_tags:
            self.selected_weather_tags.remove(tag)
        for i in range(self.weather_tree.topLevelItemCount()):
            cat_item = self.weather_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                tag_item = cat_item.child(j)
                tag_data = tag_item.data(0, Qt.UserRole) or {}
                if tag_data.get('tag') == tag:
                    tag_item.blockSignals(True)
                    tag_item.setCheckState(0, Qt.Unchecked)
                    tag_item.blockSignals(False)
                    self._update_category_counter(cat_item)
                    break
        self._refresh_weather_chips()

    # ═══════════════════════════════════════════════
    # CUSTOM TAB
    # ═══════════════════════════════════════════════
    def _setup_custom_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('code')}  Custom Traits (Advanced)")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        info_frame = QFrame()
        info_frame.setProperty("variant", "info-frame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)

        info_text = QLabel(
            "For advanced users.\n\n"
            "This tab allows adding arbitrary tags that don't fit into other categories.\n\n"
            "Examples:\n"
            "  • Compound descriptions: 'long straight light blue hair'\n"
            "  • Rare tags: 'freckles', 'beauty mark'\n"
            "  • Modifiers: 'cinematic lighting'"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        layout.addWidget(info_frame)

        hint_label = QLabel(f"{IconManager.get('edit')}  Enter tags separated by commas:")
        hint_label.setObjectName("Subtitle")
        layout.addWidget(hint_label)

        self.other_traits_text = QPlainTextEdit()
        self.other_traits_text.setMaximumHeight(180)
        self.other_traits_text.setPlaceholderText("freckles, beauty mark, cinematic lighting, ...")
        self.other_traits_text.setObjectName("LogBox")
        layout.addWidget(self.other_traits_text)
        layout.addStretch()

    # ═══════════════════════════════════════════════
    # PREVIEW TAB
    # ═══════════════════════════════════════════════
    def _setup_preview_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('eye')}  YAML Preview (Live)")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        # Buttons
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)

        refresh_btn = QPushButton(f"{IconManager.get('refresh')}  Refresh from Editor")
        refresh_btn.setProperty("variant", "primary")
        refresh_btn.clicked.connect(self._refresh_yaml_preview)
        buttons_layout.addWidget(refresh_btn)

        apply_btn = QPushButton(f"{IconManager.get('check')}  Apply YAML to Editor")
        apply_btn.setProperty("variant", "success")
        apply_btn.clicked.connect(self._apply_yaml_to_editor)
        buttons_layout.addWidget(apply_btn)

        copy_btn = QPushButton(f"{IconManager.get('copy')}  Copy YAML")
        copy_btn.setProperty("variant", "ghost")
        copy_btn.clicked.connect(self._copy_yaml_to_clipboard)
        buttons_layout.addWidget(copy_btn)
        buttons_layout.addStretch()
        layout.addWidget(buttons_frame)

        # YAML textbox
        self.yaml_textbox = QPlainTextEdit()
        self.yaml_textbox.setObjectName("AnalyzerLog")
        layout.addWidget(self.yaml_textbox, 1)
        self._refresh_yaml_preview()

    def _on_editor_tab_changed(self, index: int):
        if hasattr(self, 'preview_widget') and hasattr(self, 'yaml_textbox'):
            if self.editor_tabview.widget(index) is self.preview_widget:
                self._refresh_yaml_preview()

    def _refresh_yaml_preview(self):
        if not hasattr(self, 'yaml_textbox') or self.yaml_textbox is None:
            return
        if not self.current_profile_name:
            self.yaml_textbox.setPlainText("# No profile selected")
            return
        profile = self._get_default_profile_structure(self.current_profile_name)
        profile['character'] = self.profile_character_data.copy() if self.profile_character_data else {
            'name': self.current_profile_name, 'age': 18, 'archetype': 'custom character'
        }
        selected_traits = [e['tag'] for e in self.selected_dna_tags]
        other_text = self.other_traits_text.toPlainText().strip() if self.other_traits_text else ""
        if other_text:
            selected_traits.extend([t.strip() for t in other_text.split(',') if t.strip()])
        profile['fixed_traits'] = selected_traits
        wardrobe_by_subcat = {}
        for entry in self.selected_wardrobe_tags:
            wardrobe_by_subcat.setdefault(entry['subcategory'], []).append(entry['tag'])
        profile['outfit_whitelist'] = {'default': wardrobe_by_subcat}
        profile['expression_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t.get('category') == 'Expressions'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t.get('category') == 'Expressions']
        }
        profile['pose_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t.get('category') == 'Poses'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t.get('category') == 'Poses']
        }
        profile['signature_props'] = self.signature_props
        profile['hair_rules'] = {
            'default': self.hair_rules_data.get('default', 'hair down'),
            'conditional': self.hair_rules_data.get('conditional', [])
        }
        profile['atmosphere_preferences'] = {
            'lighting': self.selected_lighting_tags,
            'weather': self.selected_weather_tags
        }
        yaml_str = yaml.dump(profile, allow_unicode=True, default_flow_style=False, sort_keys=False)
        header = f"# Character Profile: {self.current_profile_name}\n# Filter over scene-rules\n"
        self.yaml_textbox.setPlainText(header + yaml_str)

    def _apply_yaml_to_editor(self):
        if not hasattr(self, 'yaml_textbox') or self.yaml_textbox is None:
            return
        try:
            profile = yaml.safe_load(self.yaml_textbox.toPlainText().strip())
            if not profile:
                QMessageBox.warning(self, "Warning", "YAML is empty.")
                return
            character = profile.get('character', {})
            if character:
                self.profile_character_data = character.copy()
            new_name = character.get('name', self.current_profile_name)
            if new_name != self.current_profile_name:
                old_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
                if not old_path.exists():
                    old_path = self.project_root / "character-profile.yaml"
                new_path = self.profiles_directory / f"{new_name}.yaml"
                if old_path.exists() and not new_path.exists():
                    shutil.move(str(old_path), str(new_path))
                self.current_profile_name = new_name
                self.editor_title.setText(f"Editing: {new_name}")
                self._refresh_profiles_list()

            # DNA
            self.selected_dna_tags = []
            fixed_traits = profile.get('fixed_traits', [])
            all_dna_tags = self._get_all_dna_tags_map()
            other_traits = []
            for trait in fixed_traits:
                if trait in all_dna_tags:
                    self.selected_dna_tags.append({'tag': trait, 'category': all_dna_tags[trait]})
                else:
                    other_traits.append(trait)
            self._sync_dna_cards()
            self._refresh_dna_chips()
            if self.other_traits_text:
                self.other_traits_text.clear()
                if other_traits:
                    self.other_traits_text.setPlainText(", ".join(other_traits))

            # Outfits
            self.selected_wardrobe_tags = []
            for outfit_name, subcats in profile.get('outfit_whitelist', {}).items():
                if isinstance(subcats, dict):
                    for subcategory, tags in subcats.items():
                        if isinstance(tags, list):
                            for tag in tags:
                                self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': subcategory})
            self._sync_wardrobe_tree_checkboxes()
            self._refresh_wardrobe_chips()

            # Personality
            self.preferred_personality_tags = []
            self.avoided_personality_tags = []
            for t in profile.get('expression_filter', {}).get('prefer', []):
                self.preferred_personality_tags.append({'tag': t, 'category': 'Expressions'})
            for t in profile.get('expression_filter', {}).get('avoid', []):
                self.avoided_personality_tags.append({'tag': t, 'category': 'Expressions'})
            for t in profile.get('pose_filter', {}).get('prefer', []):
                self.preferred_personality_tags.append({'tag': t, 'category': 'Poses'})
            for t in profile.get('pose_filter', {}).get('avoid', []):
                self.avoided_personality_tags.append({'tag': t, 'category': 'Poses'})
            self._sync_personality_tree_checkboxes()
            self._refresh_personality_chips()

            # Signature
            self.signature_props = profile.get('signature_props', [])
            hair_rules = profile.get('hair_rules', {})
            self.hair_rules_data = {
                'default': hair_rules.get('default', 'hair down'),
                'conditional': hair_rules.get('conditional', [])
            }
            self._refresh_signature_props_display()
            self._refresh_hair_rules_display()

            # Atmosphere
            atmosphere = profile.get('atmosphere_preferences', {})
            self.selected_lighting_tags = atmosphere.get('lighting', [])
            self.selected_weather_tags = atmosphere.get('weather', [])
            self._sync_lighting_tree_checkboxes()
            self._sync_weather_tree_checkboxes()
            self._refresh_lighting_chips()
            self._refresh_weather_chips()
            self._update_summary_panel()
            QMessageBox.information(self, "Success", "YAML applied.")
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "YAML Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _copy_yaml_to_clipboard(self):
        if not hasattr(self, 'yaml_textbox') or self.yaml_textbox is None:
            return
        content = self.yaml_textbox.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Info", "YAML is empty.")
            return
        QApplication.clipboard().setText(content)
        QMessageBox.information(self, "Copied", "YAML copied to clipboard.")

    # ═══════════════════════════════════════════════
    # PROFILE MANAGEMENT
    # ═══════════════════════════════════════════════
    def _refresh_profiles_list(self):
        self.profiles_list.clear()
        profiles = self._get_available_profiles()
        for profile_name in profiles:
            item = QTreeWidgetItem([profile_name])
            item.setData(0, Qt.UserRole, profile_name)
            self.profiles_list.addTopLevelItem(item)

    def _get_available_profiles(self) -> list[str]:
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
        profile_name = item.data(0, Qt.UserRole)
        if profile_name:
            self._select_profile(profile_name)

    def _select_profile(self, profile_name: str):
        self.current_profile_name = profile_name
        self.editor_title.setText(f"Editing: {profile_name}")
        self._load_profile_to_editor(profile_name)
        self._update_summary_panel()

    def _load_profile_to_editor(self, profile_name: str):
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            QMessageBox.critical(self, "Error", f"Profile not found: {profile_name}")
            return
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)

        # DNA + Custom
        self.selected_dna_tags = []
        fixed_traits = profile.get('fixed_traits', [])
        all_dna_tags = self._get_all_dna_tags_map()
        other_traits = []
        for trait in fixed_traits:
            if trait in all_dna_tags:
                self.selected_dna_tags.append({'tag': trait, 'category': all_dna_tags[trait]})
            else:
                other_traits.append(trait)
        self._sync_dna_cards()
        self._refresh_dna_chips()
        if hasattr(self, 'other_traits_text') and self.other_traits_text:
            self.other_traits_text.clear()
            if other_traits:
                self.other_traits_text.setPlainText(", ".join(other_traits))
        self._log(f"[LOAD] Profile loaded: {profile_name}\n")

        # Outfits
        self.selected_wardrobe_tags = []
        outfit_whitelist = profile.get('outfit_whitelist', {})
        for outfit_name, subcats in outfit_whitelist.items():
            if isinstance(subcats, dict):
                for subcategory, tags in subcats.items():
                    if isinstance(tags, list):
                        for tag in tags:
                            self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': subcategory})
        self._sync_wardrobe_tree_checkboxes()
        self._refresh_wardrobe_chips()

        # Personality
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
        self._sync_personality_tree_checkboxes()
        self._refresh_personality_chips()

        # Signature
        self.signature_props = profile.get('signature_props', [])
        hair_rules = profile.get('hair_rules', {})
        self.hair_rules_data = {
            'default': hair_rules.get('default', 'hair down'),
            'conditional': hair_rules.get('conditional', [])
        }
        self._refresh_signature_props_display()
        self._refresh_hair_rules_display()

        # Atmosphere
        atmosphere = profile.get('atmosphere_preferences', {})
        self.selected_lighting_tags = atmosphere.get('lighting', [])
        self.selected_weather_tags = atmosphere.get('weather', [])
        self._sync_lighting_tree_checkboxes()
        self._sync_weather_tree_checkboxes()
        self._refresh_lighting_chips()
        self._refresh_weather_chips()

        self._refresh_yaml_preview()
        self._update_summary_panel()

    def _sync_dna_tree_checkboxes(self):
        selected_set = {(e['tag'], e['category']) for e in self.selected_dna_tags}
        for i in range(self.dna_tree.topLevelItemCount()):
            cat_item = self.dna_tree.topLevelItem(i)
            cat_data = cat_item.data(0, Qt.UserRole) or {}
            cat_name = cat_data.get('name', '')
            for j in range(cat_item.childCount()):
                tag_item = cat_item.child(j)
                tag_data = tag_item.data(0, Qt.UserRole) or {}
                tag = tag_data.get('tag')
                checked = (tag, cat_name) in selected_set
                tag_item.blockSignals(True)
                tag_item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                tag_item.blockSignals(False)
            self._update_category_counter(cat_item)

    def _sync_wardrobe_tree_checkboxes(self):
        selected_set = {(e['tag'], e['subcategory']) for e in self.selected_wardrobe_tags}
        for i in range(self.wardrobe_tree.topLevelItemCount()):
            cat_item = self.wardrobe_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                sub_item = cat_item.child(j)
                sub_data = sub_item.data(0, Qt.UserRole) or {}
                sub_name = sub_data.get('name', '')
                for k in range(sub_item.childCount()):
                    tag_item = sub_item.child(k)
                    tag_data = tag_item.data(0, Qt.UserRole) or {}
                    tag = tag_data.get('tag')
                    checked = (tag, sub_name) in selected_set
                    tag_item.blockSignals(True)
                    tag_item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                    tag_item.blockSignals(False)
                self._update_wardrobe_subcat_counter(sub_item)
            self._update_wardrobe_cat_counter(cat_item)

    def _sync_personality_tree_checkboxes(self):
        prefer_set = {e['tag'] for e in self.preferred_personality_tags}
        avoid_set = {e['tag'] for e in self.avoided_personality_tags}
        for i in range(self.personality_tree.topLevelItemCount()):
            cat_item = self.personality_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                sub_item = cat_item.child(j)
                for k in range(sub_item.childCount()):
                    tag_item = sub_item.child(k)
                    tag_data = tag_item.data(0, Qt.UserRole) or {}
                    tag = tag_data.get('tag')
                    tag_item.blockSignals(True)
                    if tag in prefer_set:
                        tag_item.setCheckState(0, Qt.Checked)
                    elif tag in avoid_set:
                        tag_item.setCheckState(0, Qt.PartiallyChecked)
                    else:
                        tag_item.setCheckState(0, Qt.Unchecked)
                    tag_item.blockSignals(False)

    def _sync_lighting_tree_checkboxes(self):
        selected_set = set(self.selected_lighting_tags)
        for i in range(self.lighting_tree.topLevelItemCount()):
            cat_item = self.lighting_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                tag_item = cat_item.child(j)
                tag_data = tag_item.data(0, Qt.UserRole) or {}
                tag = tag_data.get('tag')
                tag_item.blockSignals(True)
                tag_item.setCheckState(0, Qt.Checked if tag in selected_set else Qt.Unchecked)
                tag_item.blockSignals(False)
            self._update_category_counter(cat_item)

    def _sync_weather_tree_checkboxes(self):
        selected_set = set(self.selected_weather_tags)
        for i in range(self.weather_tree.topLevelItemCount()):
            cat_item = self.weather_tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                tag_item = cat_item.child(j)
                tag_data = tag_item.data(0, Qt.UserRole) or {}
                tag = tag_data.get('tag')
                tag_item.blockSignals(True)
                tag_item.setCheckState(0, Qt.Checked if tag in selected_set else Qt.Unchecked)
                tag_item.blockSignals(False)
            self._update_category_counter(cat_item)

    def _create_new_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Enter character name:")
        if not ok or not name:
            return
        name = name.strip().replace(' ', '_')
        if not name or not all(c.isalnum() or c == '_' for c in name):
            QMessageBox.critical(self, "Error", "Name must contain only letters, numbers and underscores.")
            return
        new_path = self.profiles_directory / f"{name}.yaml"
        if new_path.exists():
            QMessageBox.critical(self, "Error", f"Profile '{name}' already exists!")
            return
        profile = self._get_default_profile_structure(name)
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(f"# Character Profile: {name}\n")
            f.write("# Filter over scene-rules\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._log(f"[ADD] New profile created: {name}\n")
        self._refresh_profiles_list()
        self._select_profile(name)
        QMessageBox.information(self, "Success", f"Profile '{name}' created!")

    def _import_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Character Profile", "",
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
            self._log(f"[IMPORT] Profile imported: {source.name} -> {dest.name}\n")
            self._refresh_profiles_list()
            self._select_profile(dest.stem)
            QMessageBox.information(self, "Success", f"Profile imported as '{dest.stem}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import: {e}")

    def _delete_profile(self):
        if not self.current_profile_name:
            QMessageBox.warning(self, "Warning", "No profile selected.")
            return
        if self.settings_manager.get('behavior', 'confirm_delete'):
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete '{self.current_profile_name}'?\n\nThis cannot be undone.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        profile_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            QMessageBox.critical(self, "Error", "Profile file not found.")
            return
        try:
            profile_path.unlink()
            self._log(f"[DEL] Profile deleted: {self.current_profile_name}\n")
            self.current_profile_name = None
            self.profile_character_data = {}
            self.editor_title.setText(f"Editing: (no selection)")
            # Reset all state
            self.selected_dna_tags = []
            self._sync_dna_cards()
            self._refresh_dna_chips()
            if self.other_traits_text:
                self.other_traits_text.clear()
            self.selected_wardrobe_tags = []
            self._sync_wardrobe_tree_checkboxes()
            self._refresh_wardrobe_chips()
            self.preferred_personality_tags = []
            self.avoided_personality_tags = []
            self._sync_personality_tree_checkboxes()
            self._refresh_personality_chips()
            self.signature_props = []
            self.hair_rules_data = {'default': 'hair down', 'conditional': []}
            self._refresh_signature_props_display()
            self._refresh_hair_rules_display()
            self.selected_lighting_tags = []
            self.selected_weather_tags = []
            self._sync_lighting_tree_checkboxes()
            self._sync_weather_tree_checkboxes()
            self._refresh_lighting_chips()
            self._refresh_weather_chips()
            self._refresh_profiles_list()
            self._update_summary_panel()
            QMessageBox.information(self, "Success", "Profile deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")

    def _edit_profile_name(self):
        if not self.current_profile_name:
            QMessageBox.warning(self, "Warning", "No profile selected.")
            return
        new_name, ok = QInputDialog.getText(
            self, "Rename Profile", "Enter new name:",
            text=self.current_profile_name
        )
        if not ok or not new_name:
            return
        new_name = new_name.strip().replace(' ', '_')
        if not new_name or not all(c.isalnum() or c == '_' for c in new_name):
            QMessageBox.critical(self, "Error", "Name must contain only letters, numbers and underscores.")
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
            self.editor_title.setText(f"Editing: {new_name}")
            self._refresh_profiles_list()
            self._log(f"[RENAME] Profile renamed: {old_name} -> {new_name}\n")
            QMessageBox.information(self, "Success", f"Profile renamed to '{new_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def _save_profile(self):
        if not self.current_profile_name:
            QMessageBox.warning(self, "Warning", "No profile selected.")
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
                'name': self.current_profile_name, 'age': 18, 'archetype': 'custom character'
            }
        profile['character'] = self.profile_character_data.copy()
        selected_traits = [e['tag'] for e in self.selected_dna_tags]
        other_text = self.other_traits_text.toPlainText().strip() if self.other_traits_text else ""
        if other_text:
            selected_traits.extend([t.strip() for t in other_text.split(',') if t.strip()])
        profile['fixed_traits'] = selected_traits
        wardrobe_by_subcat = {}
        for entry in self.selected_wardrobe_tags:
            wardrobe_by_subcat.setdefault(entry['subcategory'], []).append(entry['tag'])
        profile['outfit_whitelist'] = {'default': wardrobe_by_subcat}
        profile['expression_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t.get('category') == 'Expressions'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t.get('category') == 'Expressions']
        }
        profile['pose_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t.get('category') == 'Poses'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t.get('category') == 'Poses']
        }
        profile['signature_props'] = self.signature_props
        profile['hair_rules'] = {
            'default': self.hair_rules_data.get('default', 'hair down'),
            'conditional': self.hair_rules_data.get('conditional', [])
        }
        profile['atmosphere_preferences'] = {
            'lighting': self.selected_lighting_tags,
            'weather': self.selected_weather_tags
        }
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(f"# Character Profile: {self.current_profile_name}\n")
            f.write("# Filter over scene-rules\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._log(f"[SAVE] Profile '{self.current_profile_name}' saved.\n")
        QMessageBox.information(self, "Success", f"Profile '{self.current_profile_name}' saved.")

    def _get_default_profile_structure(self, name: str = "New Character") -> dict:
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