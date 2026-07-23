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
from ui_qt.components.department_tabs import DepartmentTabs
from ui_qt.theme import WardrobeColors


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

# ── Personality → блок 'personality' (Character Behavior Model, путь А) ──
# tri-state UI = частный случай весов: prefer=PREFER_WEIGHT, avoid=0.0,
# neutral = не пишем (в движке отсутствующий тег = 1.0).
PREFER_WEIGHT = 5.0
AVOID_WEIGHT = 0.0
_UI_SUBCAT_TO_SLOT = {'eyes_expr': 'eyes'}      # UI subcat -> слот модели/движка
_SLOT_TO_UI_SUBCAT = {'eyes': 'eyes_expr'}      # слот -> UI subcat
_SLOT_TO_UI_CATEGORY = {                         # слот -> UI category
    'mood': 'Expressions', 'eyes': 'Expressions', 'mouth': 'Expressions',
    'base': 'Poses', 'head': 'Poses', 'arms': 'Poses', 'legs': 'Poses',
}

# Цвета групп Atmosphere (§11.6 расшир.): освещение / погода
ATMOSPHERE_COLORS = {
    'lighting': '#f59e0b',   # amber
    'weather':  '#60a5fa',   # sky blue
}

# Personality: цвета отношений + нейтральный акцент секций/карточек
PREFER_COLOR = "#3dd68c"
AVOID_COLOR = "#f5475b"
PERSONALITY_ACCENT = "#4f6df5"


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
            card.expand_toggled.connect(self._single_open_dna)
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

    # ── Одиночная полка-аккордеон (single-open) ───────────────────
    def _apply_single_open(self, source, cards):
        """Свернуть все полки кроме source. Уважает настройку single_open_shelves."""
        enabled = self.settings_manager.get('behavior', 'single_open_shelves')
        if enabled is None:        # ключа ещё нет в settings.json
            enabled = True
        if not enabled:
            return
        for card in cards:
            if card is not source:
                card.set_expanded(False, animate=True)   # by_user=False => без сигнала

    def _single_open_dna(self, source):
        self._apply_single_open(source, self._dna_cards)

    def _single_open_outfits(self, source):
        self._apply_single_open(source, self._outfit_cards)

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
        """Правая панель: DNA-сводка или Wardrobe-сводка по активной подвкладке."""
        if not hasattr(self, 'summary_panel'):
            return
        self.summary_panel.set_profile_name(self.current_profile_name or "")
        active = None
        if hasattr(self, 'editor_tabview'):
            idx = self.editor_tabview.currentIndex()
            if idx >= 0:
                active = self.editor_tabview.widget(idx)
        if active is getattr(self, 'outfits_widget', None):
            self.summary_panel.update_wardrobe_summary(
                self.selected_wardrobe_tags, self._wardrobe_summary_spec()
            )
        elif active is getattr(self, 'atmosphere_widget', None):
            self.summary_panel.update_atmosphere_summary(
                self.selected_lighting_tags, self.selected_weather_tags
            )
        elif active is getattr(self, 'personality_widget', None):
            self.summary_panel.update_personality_summary(
                self.preferred_personality_tags, self.avoided_personality_tags
            )
        else:
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
    # OUTFITS TAB  (department tabs + accordion shelves + grid)
    # ═══════════════════════════════════════════════
    def _build_wardrobe_index(self):
        """Строит индексы из prompt-library/02_clothing один раз."""
        self._wardrobe_structure = {}   # dept -> [(subcat, [tags]), ...]
        self._subcat_to_dept = {}       # subcat -> dept
        self._tag_to_dept = {}          # tag -> dept
        clothing_dir = self.project_root / "prompt-library" / "02_clothing"
        if not clothing_dir.exists():
            return
        for dept_dir in sorted(clothing_dir.iterdir()):
            if not dept_dir.is_dir():
                continue
            dept = dept_dir.name
            subcats = []
            for txt in sorted(dept_dir.glob("*.txt")):
                subcat = txt.stem
                tags = self._load_tags_from_file(txt)
                subcats.append((subcat, tags))
                self._subcat_to_dept[subcat] = dept
                for t in tags:
                    self._tag_to_dept[t] = dept
            self._wardrobe_structure[dept] = subcats

    def _wardrobe_summary_spec(self) -> dict:
        return {
            'order': WARDROBE_ORDER,
            'labels': {d: WardrobeColors.LABELS.get(d, d) for d in WARDROBE_ORDER},
            'colors': {d: WardrobeColors.get(d) for d in WARDROBE_ORDER},
            'subcat_to_dept': getattr(self, '_subcat_to_dept', {}),
            'tag_to_dept': getattr(self, '_tag_to_dept', {}),
        }

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

        # Круглые цветные чипы одежды
        self._outfit_chips_row = CompactChipRow()
        self._outfit_chips_row.set_empty_text("No wardrobe tags selected")
        self._outfit_chips_row.remove_requested.connect(self._remove_wardrobe_chip)
        layout.addWidget(self._outfit_chips_row)

        # Ряд отделов-пилюль
        self._outfit_dept_tabs = DepartmentTabs()
        self._outfit_dept_tabs.set_departments(WARDROBE_ORDER)
        self._outfit_dept_tabs.department_changed.connect(self._on_outfit_dept_changed)
        layout.addWidget(self._outfit_dept_tabs)

        # Поиск по активному отделу
        first_dept = WARDROBE_ORDER[0]
        self._outfit_search = QLineEdit()
        self._outfit_search.setPlaceholderText(
            f"{IconManager.get('search')}  Search in {WardrobeColors.LABELS.get(first_dept, first_dept)}..."
        )
        self._outfit_search.textChanged.connect(self._filter_outfit_cards)
        layout.addWidget(self._outfit_search)

        # Полки (аккордеон-карточки) активного отдела
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_widget = QWidget()
        self._outfit_cards_layout = QVBoxLayout(cards_widget)
        self._outfit_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._outfit_cards_layout.setSpacing(10)
        self._outfit_cards_layout.addStretch()
        cards_scroll.setWidget(cards_widget)
        layout.addWidget(cards_scroll, 1)

        self._outfit_cards: list = []
        self._build_wardrobe_index()
        self._build_outfit_cards(first_dept)
        self._refresh_wardrobe_chips()

    def _on_outfit_dept_changed(self, dept: str):
        self._outfit_search.blockSignals(True)
        self._outfit_search.setText("")
        self._outfit_search.blockSignals(False)
        self._outfit_search.setPlaceholderText(
            f"{IconManager.get('search')}  Search in {WardrobeColors.LABELS.get(dept, dept)}..."
        )
        self._build_outfit_cards(dept)

    def _build_outfit_cards(self, dept: str):
        for card in self._outfit_cards:
            card.deleteLater()
        self._outfit_cards.clear()
        self._clear_layout(self._outfit_cards_layout, keep_last=True)

        color = WardrobeColors.get(dept)
        selected_set = {e['tag'] for e in self.selected_wardrobe_tags
                        if (e.get('subcategory') == dept)}
        for subcat, tags in self._wardrobe_structure.get(dept, []):
            card = CategoryCard(
                subcat.replace('_', ' ').title(), "", tags, selected_set, color=color
            )
            card.toggled.connect(self._on_outfit_toggled)
            card.expand_toggled.connect(self._single_open_outfits)
            self._outfit_cards.append(card)
            self._outfit_cards_layout.insertWidget(
                self._outfit_cards_layout.count() - 1, card
            )
        fl = self._outfit_search.text()
        if fl:
            self._filter_outfit_cards(fl)

    def _on_outfit_toggled(self, tag: str, selected: bool):
        dept = self._tag_to_dept.get(tag)
        if dept is None:
            return
        entry = {'tag': tag, 'subcategory': dept}
        if selected and entry not in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.append(entry)
        elif not selected and entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(entry)
        self._refresh_wardrobe_chips()

    def _filter_outfit_cards(self, text: str):
        for card in self._outfit_cards:
            card.set_filter(text)

    def _refresh_wardrobe_chips(self):
        descriptors = [
            {
                'text': e['tag'].replace('_', ' '),
                'color': WardrobeColors.get(e.get('subcategory', '')),
                'payload': e,
            }
            for e in self.selected_wardrobe_tags
        ]
        self._outfit_chips_row.set_chips(descriptors)
        self._update_summary_panel()

    def _remove_wardrobe_chip(self, entry: dict):
        if entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(entry)
        for card in self._outfit_cards:
            card_tags = set(card.all_tags())
            card.set_selected_set(
                {e['tag'] for e in self.selected_wardrobe_tags if e['tag'] in card_tags}
            )
        self._refresh_wardrobe_chips()

    def _sync_wardrobe_cards(self):
        for card in self._outfit_cards:
            card_tags = set(card.all_tags())
            card.set_selected_set(
                {e['tag'] for e in self.selected_wardrobe_tags if e['tag'] in card_tags}
            )

    # ═══════════════════════════════════════════════
    # PERSONALITY TAB  (tri-state плитки: prefer / avoid / neutral)
    # ═══════════════════════════════════════════════
    def _setup_personality_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('mask')}  Personality Filters")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        subtitle = QLabel(
            "Mark expressions and poses to prefer or avoid. "
            "Hover a tag to reveal  +  (prefer) and  −  (avoid)."
        )
        subtitle.setObjectName("Subtitle")
        layout.addWidget(subtitle)

        # Один общий ряд круглых чипов (prefer зелёные + avoid красные)
        self._personality_chips_row = CompactChipRow()
        self._personality_chips_row.set_empty_text("No personality filters set")
        self._personality_chips_row.remove_requested.connect(self._remove_personality_chip)
        layout.addWidget(self._personality_chips_row)

        # Общий поиск по всем подкатегориям
        self._personality_search = QLineEdit()
        self._personality_search.setPlaceholderText(
            f"{IconManager.get('search')}  Search expressions / poses..."
        )
        self._personality_search.textChanged.connect(self._filter_personality_cards)
        layout.addWidget(self._personality_search)

        # Скролл с секциями Expressions / Poses
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_widget = QWidget()
        self._personality_cards_layout = QVBoxLayout(cards_widget)
        self._personality_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._personality_cards_layout.setSpacing(10)
        self._personality_cards_layout.addStretch()
        cards_scroll.setWidget(cards_widget)
        layout.addWidget(cards_scroll, 1)

        self._personality_cards: list = []   # list of (CategoryCard, raw_subcat)
        self._build_personality_sections()
        self._refresh_personality_chips()

    def _build_personality_sections(self):
        for card, _s in self._personality_cards:
            card.deleteLater()
        self._personality_cards.clear()
        self._clear_layout(self._personality_cards_layout, keep_last=True)

        for cat_name, cat_dir, subcat_order in PERSONALITY_CATEGORIES:
            # Заголовок секции (нейтральный акцент — цвет занят под prefer/avoid)
            self._personality_cards_layout.insertWidget(
                self._personality_cards_layout.count() - 1,
                self._make_section_header(PERSONALITY_ACCENT, cat_name))

            dir_path = self.project_root / "prompt-library" / cat_dir
            subcats = {}
            if dir_path.exists():
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
                tags = self._load_tags_from_file(subcats[sub_cat])
                card = CategoryCard(
                    sub_cat.replace('_', ' ').title(), "", tags, set(),
                    color=PERSONALITY_ACCENT, tristate=True, counter_word="marked"
                )
                card.state_changed.connect(
                    lambda t, st, c=cat_name, s=sub_cat:
                        self._on_personality_state(t, st, c, s))
                card.expand_toggled.connect(self._single_open_personality)
                self._personality_cards.append((card, sub_cat))
                self._personality_cards_layout.insertWidget(
                    self._personality_cards_layout.count() - 1, card)

        fl = self._personality_search.text()
        if fl:
            self._filter_personality_cards(fl)
        self._sync_personality_cards()

    def _on_personality_state(self, tag: str, state: str,
                              category: str, subcategory: str):
        # убираем тег из обоих списков, затем кладём в нужный по состоянию
        self.preferred_personality_tags = [
            t for t in self.preferred_personality_tags if t['tag'] != tag]
        self.avoided_personality_tags = [
            t for t in self.avoided_personality_tags if t['tag'] != tag]
        if state != "neutral":
            entry = {'tag': tag, 'category': category, 'subcategory': subcategory}
            if state == "prefer":
                self.preferred_personality_tags.append(entry)
            else:
                self.avoided_personality_tags.append(entry)
        self._refresh_personality_chips()

    def _filter_personality_cards(self, text: str):
        for card, _s in self._personality_cards:
            card.set_filter(text)

    def _refresh_personality_chips(self):
        descriptors = []
        for e in self.preferred_personality_tags:
            descriptors.append({
                'text': e['tag'].replace('_', ' '),
                'color': PREFER_COLOR,
                'payload': ('prefer', e),
            })
        for e in self.avoided_personality_tags:
            descriptors.append({
                'text': e['tag'].replace('_', ' '),
                'color': AVOID_COLOR,
                'payload': ('avoid', e),
            })
        self._personality_chips_row.set_chips(descriptors)
        self._update_summary_panel()

    def _remove_personality_chip(self, payload):
        group, entry = payload
        lst = (self.preferred_personality_tags if group == 'prefer'
               else self.avoided_personality_tags)
        if entry in lst:
            lst.remove(entry)
        self._sync_personality_cards()
        self._refresh_personality_chips()

    def _sync_personality_cards(self):
        # Матчим тег к карточке по принадлежности к её тегам — без опоры на
        # subcategory (его нет у тегов, загруженных из yaml), поэтому не падает
        # и корректно проставляет состояния плиток при выборе профиля.
        prefer_tags = {e['tag'] for e in self.preferred_personality_tags}
        avoid_tags = {e['tag'] for e in self.avoided_personality_tags}
        for card, _subcat in self._personality_cards:
            card_tags = set(card.all_tags())
            card.set_tristate_sets(prefer_tags & card_tags, avoid_tags & card_tags)

    def _single_open_personality(self, source):
        enabled = self.settings_manager.get('behavior', 'single_open_shelves')
        if enabled is None:
            enabled = True
        if not enabled:
            return
        for card, _s in self._personality_cards:
            if card is not source:
                card.set_expanded(False, animate=True)

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
    # ATMOSPHERE TAB  (две секции Lighting/Weather, accordion-полки, single-open)
    # ═══════════════════════════════════════════════
    def _build_atmosphere_index(self):
        """Строит индекс полок из prompt-library/07_lighting и 10_weather."""
        self._atmosphere_structure = {'lighting': [], 'weather': []}
        for group, folder in (('lighting', '07_lighting'), ('weather', '10_weather')):
            folder_path = self.project_root / "prompt-library" / folder
            if not folder_path.exists():
                continue
            for txt in sorted(folder_path.glob("*.txt")):
                tags = self._load_tags_from_file(txt)
                self._atmosphere_structure[group].append((txt.stem, tags))

    def _make_section_header(self, color: str, title: str) -> QWidget:
        """Заголовок секции: цветной маркер группы + название."""
        head = QWidget()
        hl = QHBoxLayout(head)
        hl.setContentsMargins(0, 8, 0, 2)
        hl.setSpacing(8)
        swatch = QFrame()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
        hl.addWidget(swatch)
        lab = QLabel(title)
        lab.setObjectName("CategoryTitle")
        hl.addWidget(lab)
        hl.addStretch(1)
        return head

    def _setup_atmosphere_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"{IconManager.get('cloud')}  Atmosphere Preferences")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        subtitle = QLabel("Lighting and weather preferences that bias generated scenes.")
        subtitle.setObjectName("Subtitle")
        layout.addWidget(subtitle)

        # Общий ряд круглых цветных чипов (lighting + weather)
        self._atmosphere_chips_row = CompactChipRow()
        self._atmosphere_chips_row.set_empty_text("No atmosphere tags selected")
        self._atmosphere_chips_row.remove_requested.connect(self._remove_atmosphere_chip)
        layout.addWidget(self._atmosphere_chips_row)

        # Общий поиск по обеим секциям
        self._atmosphere_search = QLineEdit()
        self._atmosphere_search.setPlaceholderText(
            f"{IconManager.get('search')}  Search atmosphere..."
        )
        self._atmosphere_search.textChanged.connect(self._filter_atmosphere_cards)
        layout.addWidget(self._atmosphere_search)

        # Скролл с двумя секциями полок
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setFrameShape(QFrame.NoFrame)
        cards_widget = QWidget()
        self._atmosphere_cards_layout = QVBoxLayout(cards_widget)
        self._atmosphere_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._atmosphere_cards_layout.setSpacing(10)
        self._atmosphere_cards_layout.addStretch()
        cards_scroll.setWidget(cards_widget)
        layout.addWidget(cards_scroll, 1)

        self._atmosphere_cards: list = []   # list of (CategoryCard, group)
        self._build_atmosphere_index()
        self._build_atmosphere_sections()
        self._refresh_atmosphere_chips()

    def _build_atmosphere_sections(self):
        for card, _g in self._atmosphere_cards:
            card.deleteLater()
        self._atmosphere_cards.clear()
        self._clear_layout(self._atmosphere_cards_layout, keep_last=True)

        lighting_set = set(self.selected_lighting_tags)
        weather_set = set(self.selected_weather_tags)

        # --- Lighting ---
        self._atmosphere_cards_layout.insertWidget(
            self._atmosphere_cards_layout.count() - 1,
            self._make_section_header(ATMOSPHERE_COLORS['lighting'], 'Lighting'))
        for subcat, tags in self._atmosphere_structure.get('lighting', []):
            card = CategoryCard(
                subcat.replace('_', ' ').title(), "", tags, lighting_set,
                color=ATMOSPHERE_COLORS['lighting'])
            card.toggled.connect(
                lambda t, s, g='lighting': self._on_atmosphere_toggled(t, s, g))
            card.expand_toggled.connect(self._single_open_atmosphere)
            self._atmosphere_cards.append((card, 'lighting'))
            self._atmosphere_cards_layout.insertWidget(
                self._atmosphere_cards_layout.count() - 1, card)

        # --- Weather ---
        self._atmosphere_cards_layout.insertWidget(
            self._atmosphere_cards_layout.count() - 1,
            self._make_section_header(ATMOSPHERE_COLORS['weather'], 'Weather'))
        for subcat, tags in self._atmosphere_structure.get('weather', []):
            card = CategoryCard(
                subcat.replace('_', ' ').title(), "", tags, weather_set,
                color=ATMOSPHERE_COLORS['weather'])
            card.toggled.connect(
                lambda t, s, g='weather': self._on_atmosphere_toggled(t, s, g))
            card.expand_toggled.connect(self._single_open_atmosphere)
            self._atmosphere_cards.append((card, 'weather'))
            self._atmosphere_cards_layout.insertWidget(
                self._atmosphere_cards_layout.count() - 1, card)

        fl = self._atmosphere_search.text()
        if fl:
            self._filter_atmosphere_cards(fl)

    def _on_atmosphere_toggled(self, tag: str, selected: bool, group: str):
        lst = self.selected_lighting_tags if group == 'lighting' else self.selected_weather_tags
        if selected and tag not in lst:
            lst.append(tag)
        elif not selected and tag in lst:
            lst.remove(tag)
        self._refresh_atmosphere_chips()

    def _filter_atmosphere_cards(self, text: str):
        for card, _g in self._atmosphere_cards:
            card.set_filter(text)

    def _refresh_atmosphere_chips(self):
        descriptors = []
        for tag in self.selected_lighting_tags:
            descriptors.append({
                'text': tag.replace('_', ' '),
                'color': ATMOSPHERE_COLORS['lighting'],
                'payload': ('lighting', tag),
            })
        for tag in self.selected_weather_tags:
            descriptors.append({
                'text': tag.replace('_', ' '),
                'color': ATMOSPHERE_COLORS['weather'],
                'payload': ('weather', tag),
            })
        self._atmosphere_chips_row.set_chips(descriptors)
        self._update_summary_panel()

    def _remove_atmosphere_chip(self, payload):
        group, tag = payload
        lst = self.selected_lighting_tags if group == 'lighting' else self.selected_weather_tags
        if tag in lst:
            lst.remove(tag)
        self._sync_atmosphere_cards()
        self._refresh_atmosphere_chips()

    def _sync_atmosphere_cards(self):
        lighting_set = set(self.selected_lighting_tags)
        weather_set = set(self.selected_weather_tags)
        for card, group in self._atmosphere_cards:
            s = lighting_set if group == 'lighting' else weather_set
            card.set_selected_set(set(card.all_tags()) & s)

    def _single_open_atmosphere(self, source):
        enabled = self.settings_manager.get('behavior', 'single_open_shelves')
        if enabled is None:
            enabled = True
        if not enabled:
            return
        for card, _g in self._atmosphere_cards:
            if card is not source:
                card.set_expanded(False, animate=True)

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
        self._update_summary_panel()

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
        # Новый блок характера (Character Behavior Model). Устаревшие ключи
        # expression_filter / pose_filter больше не пишутся.
        _pblock = self._personality_to_yaml_block()
        if _pblock is not None:
            profile['personality'] = _pblock
        else:
            profile.pop('personality', None)
        profile.pop('expression_filter', None)
        profile.pop('pose_filter', None)
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

            # Outfits (нормализуем второй уровень yaml в отдел)
            self.selected_wardrobe_tags = []
            for outfit_name, subcats in profile.get('outfit_whitelist', {}).items():
                if isinstance(subcats, dict):
                    for subcategory, tags in subcats.items():
                        if isinstance(tags, list):
                            dept = self._subcat_to_dept.get(subcategory, subcategory)
                            for tag in tags:
                                self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': dept})
            self._sync_wardrobe_cards()
            self._refresh_wardrobe_chips()

            # Personality (новый блок 'personality'; fallback на устаревший формат)
            if profile.get('personality'):
                self.preferred_personality_tags, self.avoided_personality_tags = \
                    self._personality_from_yaml_block(profile.get('personality'))
            else:
                self.preferred_personality_tags, self.avoided_personality_tags = \
                    self._load_personality_legacy(profile)
            self._sync_personality_cards()
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
            self._sync_atmosphere_cards()
            self._refresh_atmosphere_chips()
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

        # Outfits (нормализуем второй уровень yaml в отдел)
        self.selected_wardrobe_tags = []
        outfit_whitelist = profile.get('outfit_whitelist', {})
        for outfit_name, subcats in outfit_whitelist.items():
            if isinstance(subcats, dict):
                for subcategory, tags in subcats.items():
                    if isinstance(tags, list):
                        dept = self._subcat_to_dept.get(subcategory, subcategory)
                        for tag in tags:
                            self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': dept})
        self._sync_wardrobe_cards()
        self._refresh_wardrobe_chips()

        # Personality (новый блок 'personality'; fallback на устаревший формат)
        if profile.get('personality'):
            self.preferred_personality_tags, self.avoided_personality_tags = \
                self._personality_from_yaml_block(profile.get('personality'))
        else:
            self.preferred_personality_tags, self.avoided_personality_tags = \
                self._load_personality_legacy(profile)
        self._sync_personality_cards()
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
        self._sync_atmosphere_cards()
        self._refresh_atmosphere_chips()

        self._refresh_yaml_preview()
        self._update_summary_panel()

    def _sync_personality_tree_checkboxes(self):
        prefer_set = {e['tag'] for e in self.preferred_personality_tags}
        avoid_set = {e['tag'] for e in self.avoided_personality_tags}
        # Блокируем сигнал на ДЕРЕВЕ (не на элементе!) на всё время синхронизации,
        # чтобы setCheckState не дёргал _on_personality_item_changed.
        self.personality_tree.blockSignals(True)
        try:
            for i in range(self.personality_tree.topLevelItemCount()):
                cat_item = self.personality_tree.topLevelItem(i)
                for j in range(cat_item.childCount()):
                    sub_item = cat_item.child(j)
                    for k in range(sub_item.childCount()):
                        tag_item = sub_item.child(k)
                        tag_data = tag_item.data(0, Qt.UserRole) or {}
                        tag = tag_data.get('tag')
                        if tag in prefer_set:
                            tag_item.setCheckState(0, Qt.Checked)
                        elif tag in avoid_set:
                            tag_item.setCheckState(0, Qt.PartiallyChecked)
                        else:
                            tag_item.setCheckState(0, Qt.Unchecked)
        finally:
            self.personality_tree.blockSignals(False)

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
            self._sync_wardrobe_cards()
            self._refresh_wardrobe_chips()
            self.preferred_personality_tags = []
            self.avoided_personality_tags = []
            self._sync_personality_cards()
            self._refresh_personality_chips()
            self.signature_props = []
            self.hair_rules_data = {'default': 'hair down', 'conditional': []}
            self._refresh_signature_props_display()
            self._refresh_hair_rules_display()
            self.selected_lighting_tags = []
            self.selected_weather_tags = []
            self._sync_atmosphere_cards()
            self._refresh_atmosphere_chips()
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

    # ═══════════════════════════════════════════════
    # PERSONALITY ↔ YAML 'personality' (Character Behavior Model, путь А)
    # ═══════════════════════════════════════════════
    def _build_personality_tag_index(self):
        """Ленивый индекс {tag: (ui_category, ui_subcategory)} из библиотеки.
        Нужен, чтобы для тегов без subcategory (старый формат) знать слот."""
        if getattr(self, '_personality_tag_index', None) is not None:
            return self._personality_tag_index
        idx = {}
        for cat_name, cat_dir, _order in PERSONALITY_CATEGORIES:
            dir_path = self.project_root / "prompt-library" / cat_dir
            if not dir_path.exists():
                continue
            for txt_file in sorted(dir_path.rglob("*.txt")):
                parts = txt_file.relative_to(dir_path).parts
                sub_cat = parts[0] if len(parts) >= 2 else txt_file.stem
                for tag in self._load_tags_from_file(txt_file):
                    idx.setdefault(tag, (cat_name, sub_cat))
        self._personality_tag_index = idx
        return idx

    def _personality_to_yaml_block(self):
        """Собирает блок 'personality' (один режим) из preferred/avoided.
        None, если ничего не отмечено (нейтральный характер)."""
        idx = self._build_personality_tag_index()
        axes = {}

        def place(entry, weight):
            tag = entry.get('tag', '')
            sub = entry.get('subcategory', '')
            cat = entry.get('category', '')
            if sub:
                slot = _UI_SUBCAT_TO_SLOT.get(sub, sub)
            else:
                info = idx.get(tag)
                if not info:
                    self._log(f"[WARN] personality tag not in library, skipped: {tag}\n")
                    return
                slot = _UI_SUBCAT_TO_SLOT.get(info[1], info[1])
            axis = 'expression' if cat == 'Expressions' else 'pose'
            axes.setdefault(axis, {}).setdefault(slot, {})[tag] = weight

        for e in self.preferred_personality_tags:
            place(e, PREFER_WEIGHT)
        for e in self.avoided_personality_tags:
            place(e, AVOID_WEIGHT)   # avoid перекрывает prefer при конфликте
        if not axes:
            return None
        return {'modes': [{'id': 'default', 'weight': 1.0, 'axes': axes}]}

    def _personality_from_yaml_block(self, block):
        """Блок 'personality' -> (prefer_list, avoid_list) UI-формата.
        Базовый UI не знает режимов => объединяет все режимы: тег = avoid,
        если вес 0.0 хоть в одном режиме (бан сильнее); иначе prefer, если
        вес > 1.0 хоть в одном; иначе neutral. Ось atmosphere игнорируется."""
        prefer, avoid = [], []
        if not block or not isinstance(block, dict):
            return prefer, avoid
        eff = {}  # (axis, slot, tag) -> {'min':..,'max':..}
        for md in (block.get('modes') or []):
            if not isinstance(md, dict):
                continue
            axes = md.get('axes') or {}
            if not isinstance(axes, dict):
                continue
            for axis, slots in axes.items():
                if not isinstance(slots, dict):
                    continue
                for slot, tags in slots.items():
                    if not isinstance(tags, dict):
                        continue
                    for tag, w in tags.items():
                        try:
                            w = float(w)
                        except (TypeError, ValueError):
                            continue
                        d = eff.setdefault((axis, slot, tag), {'min': w, 'max': w})
                        d['min'] = min(d['min'], w)
                        d['max'] = max(d['max'], w)
        for (axis, slot, tag), d in eff.items():
            cat = _SLOT_TO_UI_CATEGORY.get(slot)
            if cat is None:
                continue  # atmosphere и неизвестные оси — мимо базового UI
            entry = {'tag': tag, 'category': cat,
                     'subcategory': _SLOT_TO_UI_SUBCAT.get(slot, slot)}
            if d['min'] <= 0.0:
                avoid.append(entry)
            elif d['max'] > 1.0:
                prefer.append(entry)
        return prefer, avoid

    def _load_personality_legacy(self, profile):
        """Read-only fallback: устаревший expression_filter/pose_filter
        (теги без subcategory) + обогащение subcategory через индекс."""
        idx = self._build_personality_tag_index()
        prefer, avoid = [], []
        expr = profile.get('expression_filter', {}) or {}
        pose = profile.get('pose_filter', {}) or {}
        for t in expr.get('prefer', []):
            prefer.append({'tag': t, 'category': 'Expressions',
                           'subcategory': idx.get(t, ('Expressions', ''))[1]})
        for t in expr.get('avoid', []):
            avoid.append({'tag': t, 'category': 'Expressions',
                          'subcategory': idx.get(t, ('Expressions', ''))[1]})
        for t in pose.get('prefer', []):
            prefer.append({'tag': t, 'category': 'Poses',
                           'subcategory': idx.get(t, ('Poses', ''))[1]})
        for t in pose.get('avoid', []):
            avoid.append({'tag': t, 'category': 'Poses',
                          'subcategory': idx.get(t, ('Poses', ''))[1]})
        return prefer, avoid

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
        # Новый блок характера (Character Behavior Model). Устаревшие ключи
        # expression_filter / pose_filter больше не пишутся.
        _pblock = self._personality_to_yaml_block()
        if _pblock is not None:
            profile['personality'] = _pblock
        else:
            profile.pop('personality', None)
        profile.pop('expression_filter', None)
        profile.pop('pose_filter', None)
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
        # expression_filter / pose_filter устарели; характер живёт в блоке
        # 'personality', который _save_profile добавляет сам при наличии отметок.
            'atmosphere_preferences': {'lighting': [], 'weather': []}
        }