from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QTextEdit,
                               QPlainTextEdit, QTabWidget, QTreeWidget,
                               QTreeWidgetItem, QScrollArea, QFrame,
                               QGroupBox, QMessageBox, QComboBox,
                               QFileDialog, QInputDialog, QSplitter,
                               QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from pathlib import Path
from ui_qt.icon_manager import IconManager
import yaml
import shutil
from ui_qt.icon_manager import IconManager


class ProfilesTab(QWidget):
    """Вкладка редактирования профилей персонажей"""

    def __init__(self, project_root: Path, profiles_directory: Path,
                 settings_manager, log_callback, parent=None):
        super().__init__(parent)
        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.settings_manager = settings_manager
        self._log = log_callback

        # State
        self.current_profile_name: str | None = None
        self.profile_character_data: dict = {}
        self.selected_dna_tags: list[dict] = []
        self.dna_tag_ui_elements: dict[str, dict] = {}
        self.selected_wardrobe_tags: list[dict] = []
        self.tag_ui_elements: dict[str, dict] = {}
        self.preferred_personality_tags: list[dict] = []
        self.avoided_personality_tags: list[dict] = []
        self.personality_tag_ui_elements: dict[str, dict] = {}
        self.signature_props: list[dict] = []
        self.hair_rules_data: dict = {'default': 'hair down', 'conditional': []}
        self._popup_selected_tags: set[str] = set()
        self._popup_selected_actions: set[str] = set()
        self.selected_lighting_tags: list[str] = []
        self.selected_weather_tags: list[str] = []
        self.lighting_tag_ui_elements: dict[str, dict] = {}
        self.weather_tag_ui_elements: dict[str, dict] = {}
        self.other_traits_text = None
        self._tags_cache = {}

        self._setup_ui()
        self._refresh_profiles_list()

    # ═══════════════════════════════════════════════
    # MAIN LAYOUT
    # ═══════════════════════════════════════════════
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)

        # ─── LEFT: profiles list ───
        left_widget = QWidget()
        left_widget.setMaximumWidth(350)
        left_widget.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_title = QLabel("Characters")
        list_title.setObjectName("SectionTitle")
        left_layout.addWidget(list_title)

        self.profiles_list = QTreeWidget()
        self.profiles_list.setHeaderHidden(True)
        self.profiles_list.itemClicked.connect(self._on_profile_clicked)
        left_layout.addWidget(self.profiles_list)

        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        new_btn = QPushButton(f"{IconManager.get('add')} New")
        new_btn.setProperty("variant", "success")
        new_btn.clicked.connect(self._create_new_profile)
        buttons_layout.addWidget(new_btn)

        import_btn = QPushButton(f"{IconManager.get('import')} Import")
        import_btn.setProperty("variant", "primary")
        import_btn.clicked.connect(self._import_profile)
        buttons_layout.addWidget(import_btn)

        delete_btn = QPushButton(f"{IconManager.get('delete')} Delete")
        delete_btn.setProperty("variant", "danger")
        delete_btn.clicked.connect(self._delete_profile)
        buttons_layout.addWidget(delete_btn)

        left_layout.addWidget(buttons_frame)

        # ─── RIGHT: editor ───
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        title_frame = QWidget()
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.editor_title = QLabel("Editing: (no selection)")
        self.editor_title.setObjectName("PageTitle")
        title_layout.addWidget(self.editor_title)

        self.edit_name_btn = QPushButton(f"{IconManager.get('pencil')}")
        self.edit_name_btn.setProperty("variant", "icon-only")
        self.edit_name_btn.clicked.connect(self._edit_profile_name)
        title_layout.addWidget(self.edit_name_btn)
        title_layout.addStretch()

        save_btn = QPushButton(f"{IconManager.get('save')} Save Profile")
        save_btn.setProperty("variant", "success")
        save_btn.clicked.connect(self._save_profile)
        title_layout.addWidget(save_btn)

        right_layout.addWidget(title_frame)

        self.editor_tabview = QTabWidget()
        self.editor_tabview.setDocumentMode(True)

        self.dna_widget = QWidget()
        self._setup_dna_tab(self.dna_widget)
        self.editor_tabview.addTab(self.dna_widget, f"{IconManager.get('dna')} DNA")

        outfits_widget = QWidget()
        self._setup_outfits_tab(outfits_widget)
        self.editor_tabview.addTab(outfits_widget, f"{IconManager.get('tshirt')} Outfits")

        personality_widget = QWidget()
        self._setup_personality_tab(personality_widget)
        self.editor_tabview.addTab(personality_widget, f"{IconManager.get('mask')} Personality")

        signature_widget = QWidget()
        self._setup_signature_tab(signature_widget)
        self.editor_tabview.addTab(signature_widget, f"{IconManager.get('star')} Signature")

        atmosphere_widget = QWidget()
        self._setup_atmosphere_tab(atmosphere_widget)
        self.editor_tabview.addTab(atmosphere_widget, f"{IconManager.get('cloud')} Atmosphere")

        custom_widget = QWidget()
        self._setup_custom_tab(custom_widget)
        self.editor_tabview.addTab(custom_widget, f"{IconManager.get('code')} Custom")

        self.preview_widget = QWidget()
        self._setup_preview_tab(self.preview_widget)
        self.editor_tabview.addTab(self.preview_widget, f"{IconManager.get('eye')} Preview")

        self.editor_tabview.currentChanged.connect(self._on_editor_tab_changed)
        right_layout.addWidget(self.editor_tabview)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

    # ═══════════════════════════════════════════════
    # DNA TAB
    # ═══════════════════════════════════════════════
    def _setup_dna_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Character DNA")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.dna_tree_frame = QScrollArea()
        self.dna_tree_frame.setWidgetResizable(True)
        self.dna_tree_frame.setFrameShape(QFrame.NoFrame)
        dna_tree_widget = QWidget()
        self.dna_tree_layout = QVBoxLayout(dna_tree_widget)
        self.dna_tree_layout.setSpacing(2)
        self._build_dna_tree()
        self.dna_tree_frame.setWidget(dna_tree_widget)
        layout.addWidget(self.dna_tree_frame, 1)

        selected_frame = QGroupBox("Selected DNA Tags")
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
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Wardrobe (Whitelist)")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.wardrobe_tree_frame = QScrollArea()
        self.wardrobe_tree_frame.setWidgetResizable(True)
        self.wardrobe_tree_frame.setFrameShape(QFrame.NoFrame)
        wardrobe_tree_widget = QWidget()
        self.wardrobe_tree_layout = QVBoxLayout(wardrobe_tree_widget)
        self.wardrobe_tree_layout.setSpacing(2)
        self._build_wardrobe_tree()
        self.wardrobe_tree_frame.setWidget(wardrobe_tree_widget)
        layout.addWidget(self.wardrobe_tree_frame, 1)

        selected_frame = QGroupBox("Selected Wardrobe Tags")
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
        while self.dna_tree_layout.count():
            item = self.dna_tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.dna_tag_ui_elements = {}

        dna_categories = [
            ("Body Type", "01_character/body/type.txt"),
            ("Body Features", "01_character/body/features.txt"),
            ("Eye Color", "01_character/eyes/color.txt"),
            ("Eye Shape", "01_character/eyes/shape.txt"),
            ("Face Features", "01_character/face/features.txt"),
            ("Hair Style", "01_character/hair/style.txt"),
            ("Hair Color", "01_character/hair/color.txt"),
            ("Hair Length", "01_character/hair/length.txt"),
            ("Skin Tone", "01_character/skin/tone.txt"),
        ]
        for cat_name, cat_file in dna_categories:
            self._create_dna_category(cat_name, cat_file)
        self.dna_tree_layout.addStretch()

    def _create_dna_category(self, cat_name: str, cat_file: str):
        cat_frame = QWidget()
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(0, 2, 0, 2)
        cat_layout.setSpacing(0)

        toggle_btn = QPushButton(f"{IconManager.get('chevron-right')}  {cat_name}")
        toggle_btn.setProperty("variant", "section-toggle")
        cat_layout.addWidget(toggle_btn)

        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)

        tags = self._load_tags_from_library(cat_file)
        for tag in tags:
            tag_key = f"dna::{cat_name}::{tag}"
            tag_row = QWidget()
            tag_row.setObjectName("TagRow")
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)

            tag_label = QLabel(f"  {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)

            action_btn = QPushButton(f"{IconManager.get('plus')}")
            action_btn.setProperty("variant", "success")
            action_btn.setProperty("variant2", "icon-only")
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

        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            toggle_btn.setText(f"{'▼' if is_visible else '▶'} {cat_name}")

        toggle_btn.clicked.connect(toggle_visibility)
        self.dna_tree_layout.addWidget(cat_frame)

    def _toggle_dna_tag(self, tag: str, category: str, tag_key: str):
        if tag_key not in self.dna_tag_ui_elements:
            return
        tag_entry = {'tag': tag, 'category': category}
        ui = self.dna_tag_ui_elements[tag_key]
        if tag_entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(tag_entry)
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
        else:
            self.selected_dna_tags.append(tag_entry)
            ui['button'].setText(f"{IconManager.get('minus')}")
            ui['button'].setProperty("variant", "danger")
        ui['button'].style().unpolish(ui['button'])
        ui['button'].style().polish(ui['button'])
        self._refresh_selected_dna_tags_display()

    def _refresh_selected_dna_tags_display(self):
        while self.selected_dna_tags_layout.count() > 1:
            item = self.selected_dna_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.selected_dna_tags:
            label = QLabel("(No DNA tags selected — expand categories and click [+])")
            label.setObjectName("Subtitle")
            self.selected_dna_tags_layout.insertWidget(0, label)
            return
        for te in self.selected_dna_tags:
            chip = QWidget()
            chip.setProperty("variant", "chip")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 5, 4)
            chip_layout.setSpacing(5)
            chip_label = QLabel(te['tag'].replace('_', ' '))
            chip_layout.addWidget(chip_label)
            remove_btn = QPushButton(f"{IconManager.get('close')}")
            remove_btn.setProperty("variant", "icon-only")
            remove_btn.setProperty("variant2", "ghost")
            remove_btn.setProperty("variant", "ghost")
            remove_btn.clicked.connect(lambda checked, te=te: self._remove_dna_tag_from_chip(te))
            chip_layout.addWidget(remove_btn)
            self.selected_dna_tags_layout.insertWidget(
                self.selected_dna_tags_layout.count() - 1, chip
            )

    def _remove_dna_tag_from_chip(self, tag_entry: dict):
        if tag_entry not in self.selected_dna_tags:
            return
        self.selected_dna_tags.remove(tag_entry)
        tag_key = f"dna::{tag_entry['category']}::{tag_entry['tag']}"
        if tag_key in self.dna_tag_ui_elements:
            ui = self.dna_tag_ui_elements[tag_key]
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])
        self._refresh_selected_dna_tags_display()

    def _build_wardrobe_tree(self):
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
                categories.setdefault(main_cat, {})[sub_cat] = txt_file

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
        cat_frame = QWidget()
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(0, 2, 0, 2)
        cat_layout.setSpacing(0)

        toggle_btn = QPushButton(f"▶ {main_cat.replace('_', ' ').title()}")
        toggle_btn.setProperty("variant", "section-toggle")
        cat_layout.addWidget(toggle_btn)

        subcats_frame = QWidget()
        subcats_frame.setVisible(False)
        subcats_layout = QVBoxLayout(subcats_frame)
        subcats_layout.setContentsMargins(20, 5, 0, 5)
        subcats_layout.setSpacing(1)
        for sub_cat, file_path in subcats.items():
            self._create_wardrobe_subcategory(subcats_layout, main_cat, sub_cat, file_path)
        subcats_layout.addStretch()
        cat_layout.addWidget(subcats_frame)

        def toggle_visibility():
            is_visible = subcats_frame.isVisible()
            subcats_frame.setVisible(not is_visible)
            toggle_btn.setText(f"{'▼' if is_visible else '▶'} {main_cat.replace('_', ' ').title()}")

        toggle_btn.clicked.connect(toggle_visibility)
        self.wardrobe_tree_layout.addWidget(cat_frame)

    def _create_wardrobe_subcategory(self, parent_layout, main_cat: str, sub_cat: str, file_path: Path):
        sub_frame = QWidget()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(0, 1, 0, 1)
        sub_layout.setSpacing(0)

        toggle_btn = QPushButton(f"  ▶ {sub_cat.replace('_', ' ').title()}")
        toggle_btn.setProperty("variant", "ghost")
        sub_layout.addWidget(toggle_btn)

        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)

        tags = self._load_tags_from_file(file_path)
        for tag in tags:
            tag_key = f"{sub_cat}::{tag}"
            tag_row = QWidget()
            tag_row.setObjectName("TagRow")
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)

            tag_label = QLabel(f"    {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)

            action_btn = QPushButton(f"{IconManager.get('plus')}")
            action_btn.setProperty("variant", "success")
            action_btn.setProperty("variant2", "icon-only")
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

        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            toggle_btn.setText(f"  {'▼' if is_visible else '▶'} {sub_cat.replace('_', ' ').title()}")

        toggle_btn.clicked.connect(toggle_visibility)
        parent_layout.addWidget(sub_frame)

    def _toggle_wardrobe_tag(self, tag: str, subcategory: str, tag_key: str):
        if tag_key not in self.tag_ui_elements:
            return
        tag_entry = {'tag': tag, 'subcategory': subcategory}
        ui = self.tag_ui_elements[tag_key]
        if tag_entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(tag_entry)
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
        else:
            self.selected_wardrobe_tags.append(tag_entry)
            ui['button'].setText(f"{IconManager.get('minus')}")
            ui['button'].setProperty("variant", "danger")
        ui['button'].style().unpolish(ui['button'])
        ui['button'].style().polish(ui['button'])
        self._refresh_selected_tags_display()

    def _refresh_selected_tags_display(self):
        while self.selected_tags_layout.count() > 1:
            item = self.selected_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.selected_wardrobe_tags:
            label = QLabel("(No tags selected)")
            label.setObjectName("Subtitle")
            self.selected_tags_layout.insertWidget(0, label)
            return
        for te in self.selected_wardrobe_tags:
            chip = QWidget()
            chip.setProperty("variant", "chip")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 5, 4)
            chip_layout.setSpacing(5)
            chip_label = QLabel(te['tag'].replace('_', ' '))
            chip_layout.addWidget(chip_label)
            remove_btn = QPushButton(f"{IconManager.get('close')}")
            remove_btn.setProperty("variant", "icon-only")
            remove_btn.setProperty("variant2", "ghost")
            remove_btn.setProperty("variant", "ghost")
            remove_btn.clicked.connect(lambda checked, te=te: self._remove_tag_from_chip(te))
            chip_layout.addWidget(remove_btn)
            self.selected_tags_layout.insertWidget(
                self.selected_tags_layout.count() - 1, chip
            )

    def _remove_tag_from_chip(self, tag_entry: dict):
        if tag_entry not in self.selected_wardrobe_tags:
            return
        self.selected_wardrobe_tags.remove(tag_entry)
        tag_key = f"{tag_entry['subcategory']}::{tag_entry['tag']}"
        if tag_key in self.tag_ui_elements:
            ui = self.tag_ui_elements[tag_key]
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])
        self._refresh_selected_tags_display()

    # ═══════════════════════════════════════════════
    # PERSONALITY TAB
    # ═══════════════════════════════════════════════
    def _setup_personality_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Personality Filters (Prefer / Avoid)")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.personality_tree_frame = QScrollArea()
        self.personality_tree_frame.setWidgetResizable(True)
        self.personality_tree_frame.setFrameShape(QFrame.NoFrame)
        personality_tree_widget = QWidget()
        self.personality_tree_layout = QVBoxLayout(personality_tree_widget)
        self.personality_tree_layout.setSpacing(2)
        self._build_personality_tree()
        self.personality_tree_frame.setWidget(personality_tree_widget)
        layout.addWidget(self.personality_tree_frame)

        summary_frame = QWidget()
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)

        prefer_frame = QWidget()
        prefer_layout = QVBoxLayout(prefer_frame)
        prefer_layout.setContentsMargins(0, 0, 0, 0)
        prefer_label = QLabel("Preferred:")
        prefer_label.setObjectName("Subtitle")
        prefer_layout.addWidget(prefer_label)
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

        avoid_frame = QWidget()
        avoid_layout = QVBoxLayout(avoid_frame)
        avoid_layout.setContentsMargins(0, 0, 0, 0)
        avoid_label = QLabel("Avoided:")
        avoid_label.setObjectName("Subtitle")
        avoid_layout.addWidget(avoid_label)
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
        if not self.tag_ui_elements:
            return
        for tag_key, ui in self.tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'subcategory': ui['subcategory']}
            if tag_entry in self.selected_wardrobe_tags:
                ui['button'].setText("-")
                ui['button'].setProperty("variant", "danger")
            else:
                ui['button'].setText("+")
                ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])

    def _build_personality_tree(self):
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
        cat_frame = QWidget()
        cat_layout = QVBoxLayout(cat_frame)
        cat_layout.setContentsMargins(0, 2, 0, 2)
        cat_layout.setSpacing(0)

        toggle_btn = QPushButton(f"{IconManager.get('chevron-right')}  {cat_name}")
        toggle_btn.setProperty("variant", "section-toggle")
        cat_layout.addWidget(toggle_btn)

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
                toggle_btn.setText(f"{'▼' if is_visible else '▶'} {cat_name}")
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

        def toggle_visibility():
            is_visible = subcats_frame.isVisible()
            subcats_frame.setVisible(not is_visible)
            toggle_btn.setText(f"{'▼' if is_visible else '▶'} {cat_name}")

        toggle_btn.clicked.connect(toggle_visibility)
        self.personality_tree_layout.addWidget(cat_frame)

    def _create_personality_subcategory(self, parent_layout, cat_name: str, sub_cat: str, file_path: Path):
        sub_frame = QWidget()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(0, 1, 0, 1)
        sub_layout.setSpacing(0)

        toggle_btn = QPushButton(f"  ▶ {sub_cat.replace('_', ' ').title()}")
        toggle_btn.setProperty("variant", "ghost")
        sub_layout.addWidget(toggle_btn)

        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)

        tags = self._load_tags_from_file(file_path)
        for tag in tags:
            tag_key = f"personality::{cat_name}::{sub_cat}::{tag}"
            tag_row = QWidget()
            tag_row.setObjectName("TagRow")
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)

            tag_label = QLabel(f"    {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)

            avoid_btn = QPushButton("-")
            avoid_btn.setFixedSize(25, 22)
            avoid_btn.setProperty("variant", "danger")
            avoid_btn.clicked.connect(
                lambda checked, t=tag, cn=cat_name, sc=sub_cat, tk=tag_key:
                self._toggle_personality_tag(t, cn, sc, tk, 'avoid')
            )
            tag_row_layout.addWidget(avoid_btn)

            prefer_btn = QPushButton("+")
            prefer_btn.setFixedSize(25, 22)
            prefer_btn.setProperty("variant", "success")
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

        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            toggle_btn.setText(f"  {'▼' if is_visible else '▶'} {sub_cat.replace('_', ' ').title()}")

        toggle_btn.clicked.connect(toggle_visibility)
        parent_layout.addWidget(sub_frame)

    def _toggle_personality_tag(self, tag: str, category: str, subcategory: str, tag_key: str, action: str):
        tag_entry = {'tag': tag, 'category': category, 'subcategory': subcategory}
        was_in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
        was_in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
        self.preferred_personality_tags = [t for t in self.preferred_personality_tags if t['tag'] != tag]
        self.avoided_personality_tags = [t for t in self.avoided_personality_tags if t['tag'] != tag]
        if action == 'prefer' and not was_in_prefer:
            self.preferred_personality_tags.append(tag_entry)
        elif action == 'avoid' and not was_in_avoid:
            self.avoided_personality_tags.append(tag_entry)
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

    def _sync_personality_ui_states(self):
        if not self.personality_tag_ui_elements:
            return
        for tag_key, ui in self.personality_tag_ui_elements.items():
            tag = ui['tag']
            in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
            in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
            if in_prefer:
                ui['prefer_btn'].setText("v")
                ui['prefer_btn'].setProperty("variant", "success")
                ui['avoid_btn'].setText("-")
                ui['avoid_btn'].setProperty("variant", "danger")
            elif in_avoid:
                ui['prefer_btn'].setText("+")
                ui['prefer_btn'].setProperty("variant", "success")
                ui['avoid_btn'].setText("v")
                ui['avoid_btn'].setProperty("variant", "danger")
            else:
                ui['prefer_btn'].setText("+")
                ui['prefer_btn'].setProperty("variant", "success")
                ui['avoid_btn'].setText("-")
                ui['avoid_btn'].setProperty("variant", "danger")
            ui['prefer_btn'].style().unpolish(ui['prefer_btn'])
            ui['prefer_btn'].style().polish(ui['prefer_btn'])
            ui['avoid_btn'].style().unpolish(ui['avoid_btn'])
            ui['avoid_btn'].style().polish(ui['avoid_btn'])

    def _refresh_personality_tags_display(self):
        while self.prefer_tags_layout.count() > 1:
            item = self.prefer_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while self.avoid_tags_layout.count() > 1:
            item = self.avoid_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.preferred_personality_tags:
            label = QLabel("(empty)")
            label.setObjectName("Subtitle")
            self.prefer_tags_layout.insertWidget(0, label)
        else:
            for entry in self.preferred_personality_tags:
                chip = QWidget()
                chip.setProperty("variant", "chip-success")
                chip_layout = QHBoxLayout(chip)
                chip_layout.setContentsMargins(8, 4, 5, 4)
                chip_layout.setSpacing(5)
                chip_label = QLabel(entry['tag'].replace('_', ' '))
                chip_layout.addWidget(chip_label)
                remove_btn = QPushButton("x")
                remove_btn.setFixedSize(22, 22)
                remove_btn.setProperty("variant", "ghost")
                remove_btn.clicked.connect(lambda checked, t=entry['tag']: self._remove_personality_tag(t))
                chip_layout.addWidget(remove_btn)
                self.prefer_tags_layout.insertWidget(
                    self.prefer_tags_layout.count() - 1, chip
                )

        if not self.avoided_personality_tags:
            label = QLabel("(empty)")
            label.setObjectName("Subtitle")
            self.avoid_tags_layout.insertWidget(0, label)
        else:
            for entry in self.avoided_personality_tags:
                chip = QWidget()
                chip.setProperty("variant", "chip-danger")
                chip_layout = QHBoxLayout(chip)
                chip_layout.setContentsMargins(8, 4, 5, 4)
                chip_layout.setSpacing(5)
                chip_label = QLabel(entry['tag'].replace('_', ' '))
                chip_layout.addWidget(chip_label)
                remove_btn = QPushButton("x")
                remove_btn.setFixedSize(22, 22)
                remove_btn.setProperty("variant", "ghost")
                remove_btn.clicked.connect(lambda checked, t=entry['tag']: self._remove_personality_tag(t))
                chip_layout.addWidget(remove_btn)
                self.avoid_tags_layout.insertWidget(
                    self.avoid_tags_layout.count() - 1, chip
                )

    def _remove_personality_tag(self, tag: str):
        self.preferred_personality_tags = [x for x in self.preferred_personality_tags if x['tag'] != tag]
        self.avoided_personality_tags = [x for x in self.avoided_personality_tags if x['tag'] != tag]
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

    # ═══════════════════════════════════════════════
    # SIGNATURE TAB
    # ═══════════════════════════════════════════════
    def _setup_signature_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Signature Items & Hair Rules")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # PROPS
        props_group = QGroupBox("Signature Props")
        props_layout = QVBoxLayout(props_group)

        add_prop_btn = QPushButton("Add Prop")
        add_prop_btn.setProperty("variant", "success")
        add_prop_btn.clicked.connect(self._add_signature_prop)
        props_layout.addWidget(add_prop_btn)

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

        # HAIR RULES
        hair_group = QGroupBox("Hair Rules")
        hair_layout = QVBoxLayout(hair_group)

        default_frame = QWidget()
        default_layout = QHBoxLayout(default_frame)
        default_layout.setContentsMargins(0, 0, 0, 0)
        default_label = QLabel("Default Style:")
        default_label.setFixedWidth(120)
        default_layout.addWidget(default_label)
        self.hair_default_btn = QPushButton("▼ hair down")
        self.hair_default_btn.setProperty("variant", "section-toggle")
        self.hair_default_btn.clicked.connect(self._open_default_style_selector)
        default_layout.addWidget(self.hair_default_btn, 1)
        hair_layout.addWidget(default_frame)

        cond_header = QWidget()
        cond_layout = QHBoxLayout(cond_header)
        cond_layout.setContentsMargins(0, 5, 0, 0)
        cond_label = QLabel("Conditional Rules:")
        cond_label.setObjectName("Subtitle")
        cond_layout.addWidget(cond_label)
        cond_layout.addStretch()
        add_rule_btn = QPushButton("Add Rule")
        add_rule_btn.setProperty("variant", "success")
        add_rule_btn.clicked.connect(self._add_hair_rule)
        cond_layout.addWidget(add_rule_btn)
        hair_layout.addWidget(cond_header)

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
        all_dna_tags = {ui['tag']: ui['category'] for ui in self.dna_tag_ui_elements.values()}
        other_traits = []
        for trait in fixed_traits:
            if trait in all_dna_tags:
                self.selected_dna_tags.append({'tag': trait, 'category': all_dna_tags[trait]})
            else:
                other_traits.append(trait)
        if hasattr(self, 'other_traits_text') and self.other_traits_text:
            self.other_traits_text.clear()
            if other_traits:
                self.other_traits_text.setPlainText(", ".join(other_traits))
        self._sync_dna_tag_ui_states()
        self._refresh_selected_dna_tags_display()
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
        self._sync_tag_ui_states()
        self._refresh_selected_tags_display()

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
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

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
        self._sync_lighting_ui_states()
        self._sync_weather_ui_states()
        self._refresh_selected_lighting_display()
        self._refresh_selected_weather_display()

        self._refresh_yaml_preview()

    def _sync_dna_tag_ui_states(self):
        if not self.dna_tag_ui_elements:
            return
        for tag_key, ui in self.dna_tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'category': ui['category']}
            if tag_entry in self.selected_dna_tags:
                ui['button'].setText("-")
                ui['button'].setProperty("variant", "danger")
            else:
                ui['button'].setText("+")
                ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])

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
            self.editor_title.setText("Editing: (no selection)")
            self.selected_dna_tags = []
            self._sync_dna_tag_ui_states()
            self._refresh_selected_dna_tags_display()
            if hasattr(self, 'other_traits_text') and self.other_traits_text:
                self.other_traits_text.clear()
            self.selected_wardrobe_tags = []
            self._sync_tag_ui_states()
            self._refresh_selected_tags_display()
            self.preferred_personality_tags = []
            self.avoided_personality_tags = []
            self._sync_personality_ui_states()
            self._refresh_personality_tags_display()
            self.signature_props = []
            self.hair_rules_data = {'default': 'hair down', 'conditional': []}
            self._refresh_signature_props_display()
            self._refresh_hair_rules_display()
            self.selected_lighting_tags = []
            self.selected_weather_tags = []
            self._sync_lighting_ui_states()
            self._sync_weather_ui_states()
            self._refresh_selected_lighting_display()
            self._refresh_selected_weather_display()
            self._refresh_profiles_list()
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

        selected_traits = [entry['tag'] for entry in self.selected_dna_tags]
        other_text = self.other_traits_text.toPlainText().strip() if hasattr(self, 'other_traits_text') and self.other_traits_text else ""
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

    def _load_tags_from_library(self, relative_path: str) -> list:
        if relative_path in self._tags_cache:
            return self._tags_cache[relative_path]
        file_path = self.project_root / "prompt-library" / relative_path
        tags = []
        if not file_path.exists():
            self._log(f"[WARNING] File not found: {relative_path}\n")
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
    # SIGNATURE PROPS METHODS
    # ═══════════════════════════════════════════════
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
        while self.props_layout.count() > 1:
            item = self.props_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.signature_props:
            label = QLabel("(No signature props — click 'Add Prop')")
            label.setObjectName("Subtitle")
            self.props_layout.insertWidget(0, label)
            return
        for i, prop in enumerate(self.signature_props):
            prop_frame = QWidget()
            prop_frame.setProperty("variant", "card")
            prop_layout = QVBoxLayout(prop_frame)
            prop_layout.setContentsMargins(10, 10, 10, 10)
            prop_layout.setSpacing(5)

            header = QWidget()
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 0)
            name_label = QLabel("Prop name:")
            name_label.setObjectName("Subtitle")
            header_layout.addWidget(name_label)

            name_entry = QLineEdit()
            name_entry.setPlaceholderText("Item name")
            name_entry.setText(prop['name'])
            name_entry.textChanged.connect(lambda text, idx=i: self._update_prop_name(idx, text))
            header_layout.addWidget(name_entry, 1)

            delete_btn = QPushButton("Delete Prop")
            delete_btn.setProperty("variant", "danger")
            delete_btn.clicked.connect(lambda checked, idx=i: self._remove_signature_prop(idx))
            header_layout.addWidget(delete_btn)
            prop_layout.addWidget(header)

            tags_label = QLabel("Tags:")
            tags_label.setObjectName("Subtitle")
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
                browse_btn.setProperty("variant", "primary")
                browse_btn.clicked.connect(lambda checked, pi=i: self._open_tags_browser(pi))
                tag_layout.addWidget(browse_btn)

                remove_btn = QPushButton("x")
                remove_btn.setFixedSize(25, 25)
                remove_btn.setProperty("variant", "danger")
                remove_btn.clicked.connect(lambda checked, pi=i, ti=j: self._remove_tag_from_prop(pi, ti))
                tag_layout.addWidget(remove_btn)
                prop_layout.addWidget(tag_row)

            add_tag_btn = QPushButton("Add Tag")
            add_tag_btn.setProperty("variant", "ghost")
            add_tag_btn.clicked.connect(lambda checked, idx=i: self._add_tag_to_prop(idx))
            prop_layout.addWidget(add_tag_btn)
            self.props_layout.insertWidget(self.props_layout.count() - 1, prop_frame)

    def _open_tags_browser(self, prop_index: int):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Browse Tags (Props)")
        dialog.resize(500, 600)
        layout = QVBoxLayout(dialog)
        label = QLabel("Select tags (multiple allowed):")
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        props_dir = self.project_root / "prompt-library" / "09_props"
        if not props_dir.exists():
            error_label = QLabel(f"Folder not found: {props_dir}")
            error_label.setObjectName("SemanticError")
            scroll_layout.addWidget(error_label)
        else:
            current_tags = set(self.signature_props[prop_index]['tags'])
            self._popup_selected_tags = set(current_tags)
            for txt_file in sorted(props_dir.rglob("*.txt")):
                tags = self._load_tags_from_file(txt_file)
                if tags:
                    cat_label = QLabel(txt_file.stem.replace('_', ' ').title())
                    cat_label.setObjectName("Subtitle")
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
        new_tags = sorted(list(self._popup_selected_tags))
        self.signature_props[prop_index]['tags'] = new_tags
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
        while self.hair_rules_layout.count() > 1:
            item = self.hair_rules_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if hasattr(self, 'hair_default_btn') and self.hair_default_btn:
            current_default = self.hair_rules_data.get('default', 'hair down')
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = f"  {IconManager.get('star')}" if current_default in dna_styles else ""
            self.hair_default_btn.setText(f"▼ {current_default}{star}")
        if not self.hair_rules_data['conditional']:
            label = QLabel("(No conditional rules — click 'Add Rule')")
            label.setObjectName("Subtitle")
            self.hair_rules_layout.insertWidget(0, label)
            return
        from PySide6.QtWidgets import QSlider
        for i, rule in enumerate(self.hair_rules_data['conditional']):
            rule_frame = QWidget()
            rule_frame.setProperty("variant", "card")
            rule_layout = QVBoxLayout(rule_frame)
            rule_layout.setContentsMargins(10, 10, 10, 10)
            rule_layout.setSpacing(5)

            header = QWidget()
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 0)
            rule_label = QLabel(f"Rule #{i + 1}")
            rule_label.setObjectName("Subtitle")
            header_layout.addWidget(rule_label)
            header_layout.addStretch()

            delete_btn = QPushButton("Delete Hair Rule")
            delete_btn.setProperty("variant", "danger")
            delete_btn.clicked.connect(lambda checked, idx=i: self._remove_hair_rule(idx))
            header_layout.addWidget(delete_btn)
            rule_layout.addWidget(header)

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
            browse_btn.setProperty("variant", "primary")
            browse_btn.clicked.connect(lambda checked, idx=i, ae=actions_entry: self._open_actions_browser(idx, ae))
            actions_layout.addWidget(browse_btn)
            rule_layout.addWidget(actions_frame)

            style_frame = QWidget()
            style_layout = QHBoxLayout(style_frame)
            style_layout.setContentsMargins(0, 0, 0, 0)
            style_label = QLabel("Style:")
            style_label.setFixedWidth(100)
            style_layout.addWidget(style_label)
            style_text = rule['style'] or "Select..."
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " *" if rule['style'] in dna_styles else ""
            style_btn = QPushButton(f"▼ {style_text}{star}")
            style_btn.setProperty("variant", "section-toggle")
            style_btn.clicked.connect(lambda checked, idx=i, btn=style_btn: self._open_style_selector(idx, btn))
            style_layout.addWidget(style_btn, 1)
            rule_layout.addWidget(style_frame)

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
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Hair Style")
        dialog.resize(350, 500)
        layout = QVBoxLayout(dialog)
        label = QLabel("Select hair style:")
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = " *" if tag in dna_styles else ""
            btn = QPushButton(f"{tag}{star}")
            btn.setProperty("variant", "ghost")
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
        self._update_hair_rule_style(rule_index, style)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        star = " *" if style in dna_styles else ""
        button_widget.setText(f"▼ {style}{star}")
        dialog.accept()

    def _open_default_style_selector(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Default Hair Style")
        dialog.resize(350, 500)
        layout = QVBoxLayout(dialog)
        label = QLabel("Select default hair style:")
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = " *" if tag in dna_styles else ""
            btn = QPushButton(f"{tag}{star}")
            btn.setProperty("variant", "ghost")
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
        self.hair_rules_data['default'] = style
        if hasattr(self, 'hair_default_btn') and self.hair_default_btn:
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " *" if style in dna_styles else ""
            self.hair_default_btn.setText(f"▼ {style}{star}")
        dialog.accept()

    def _open_actions_browser(self, rule_index: int, entry_widget):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Actions")
        dialog.resize(500, 600)
        layout = QVBoxLayout(dialog)
        label = QLabel("Select actions:")
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
                    cat_label = QLabel(txt_file.stem.replace('_', ' ').title())
                    cat_label.setObjectName("Subtitle")
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
        if hasattr(self, 'hair_rules_container') and self.hair_rules_container:
            rules_widget = self.hair_rules_container.widget()
            if rules_widget:
                rule_frames = [w for w in rules_widget.layout().children() if isinstance(w, QWidget)]
                if rule_index < len(rule_frames):
                    for child in rule_frames[rule_index].findChildren(QLineEdit):
                        if child.text().replace('.', '').isdigit():
                            child.setText(str(rounded_value))
                            break

    def _update_prob_from_entry(self, rule_index: int, value_str: str, slider_widget):
        try:
            value = float(value_str)
            if 0 <= value <= 1:
                self._update_hair_rule_probability(rule_index, value_str)
                slider_widget.setValue(int(value * 100))
        except ValueError:
            pass

    # ═══════════════════════════════════════════════
    # ATMOSPHERE TAB
    # ═══════════════════════════════════════════════
    def _setup_atmosphere_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Atmosphere Preferences")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        # LIGHTING
        lighting_group = QGroupBox("Lighting Preferences")
        lighting_layout = QVBoxLayout(lighting_group)
        self.lighting_tree_frame = QWidget()
        self.lighting_tree_layout = QVBoxLayout(self.lighting_tree_frame)
        self.lighting_tree_layout.setContentsMargins(0, 0, 0, 0)
        self.lighting_tree_layout.setSpacing(2)
        self._build_lighting_tree()
        lighting_layout.addWidget(self.lighting_tree_frame)

        selected_lighting_frame = QGroupBox("Selected Lighting")
        selected_lighting_layout = QVBoxLayout(selected_lighting_frame)
        self.selected_lighting_container = QScrollArea()
        self.selected_lighting_container.setWidgetResizable(True)
        self.selected_lighting_container.setMaximumHeight(120)
        self.selected_lighting_container.setFrameShape(QFrame.NoFrame)
        selected_lighting_widget = QWidget()
        self.selected_lighting_layout = QHBoxLayout(selected_lighting_widget)
        self.selected_lighting_layout.setSpacing(5)
        self.selected_lighting_layout.addStretch()
        self.selected_lighting_container.setWidget(selected_lighting_widget)
        selected_lighting_layout.addWidget(self.selected_lighting_container)
        lighting_layout.addWidget(selected_lighting_frame)
        scroll_layout.addWidget(lighting_group)

        # WEATHER
        weather_group = QGroupBox("Weather Preferences")
        weather_layout = QVBoxLayout(weather_group)
        self.weather_tree_frame = QWidget()
        self.weather_tree_layout = QVBoxLayout(self.weather_tree_frame)
        self.weather_tree_layout.setContentsMargins(0, 0, 0, 0)
        self.weather_tree_layout.setSpacing(2)
        self._build_weather_tree()
        weather_layout.addWidget(self.weather_tree_frame)

        selected_weather_frame = QGroupBox("Selected Weather")
        selected_weather_layout = QVBoxLayout(selected_weather_frame)
        self.selected_weather_container = QScrollArea()
        self.selected_weather_container.setWidgetResizable(True)
        self.selected_weather_container.setMaximumHeight(120)
        self.selected_weather_container.setFrameShape(QFrame.NoFrame)
        selected_weather_widget = QWidget()
        self.selected_weather_layout = QHBoxLayout(selected_weather_widget)
        self.selected_weather_layout.setSpacing(5)
        self.selected_weather_layout.addStretch()
        self.selected_weather_container.setWidget(selected_weather_widget)
        selected_weather_layout.addWidget(self.selected_weather_container)
        weather_layout.addWidget(selected_weather_frame)

        scroll_layout.addWidget(weather_group)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        self._refresh_selected_lighting_display()
        self._refresh_selected_weather_display()

    def _build_lighting_tree(self):
        while self.lighting_tree_layout.count():
            item = self.lighting_tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.lighting_tag_ui_elements = {}
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
            self._create_lighting_subcategory(sub_cat, file_path)
        self.lighting_tree_layout.addStretch()

    def _create_lighting_subcategory(self, sub_cat: str, file_path: Path):
        sub_frame = QWidget()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(0, 1, 0, 1)
        sub_layout.setSpacing(0)

        toggle_btn = QPushButton(f"▶ {sub_cat.replace('_', ' ').title()}")
        toggle_btn.setProperty("variant", "section-toggle")
        sub_layout.addWidget(toggle_btn)

        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)

        tags = self._load_tags_from_file(file_path)
        for tag in tags:
            tag_key = f"lighting::{tag}"
            tag_row = QWidget()
            tag_row.setObjectName("TagRow")
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)
            tag_label = QLabel(f"  {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)
            action_btn = QPushButton(f"{IconManager.get('plus')}")
            action_btn.setProperty("variant", "success")
            action_btn.setProperty("variant2", "icon-only")
            action_btn.clicked.connect(
                lambda checked, t=tag, tk=tag_key: self._toggle_lighting_tag(t, tk)
            )
            tag_row_layout.addWidget(action_btn)
            tags_layout.addWidget(tag_row)
            self.lighting_tag_ui_elements[tag_key] = {
                'label': tag_label, 'button': action_btn, 'tag': tag
            }
        tags_layout.addStretch()
        sub_layout.addWidget(tags_frame)

        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            toggle_btn.setText(f"{'▼' if is_visible else '▶'} {sub_cat.replace('_', ' ').title()}")

        toggle_btn.clicked.connect(toggle_visibility)
        self.lighting_tree_layout.addWidget(sub_frame)

    def _toggle_lighting_tag(self, tag: str, tag_key: str):
        if tag_key not in self.lighting_tag_ui_elements:
            return
        ui = self.lighting_tag_ui_elements[tag_key]
        if tag in self.selected_lighting_tags:
            self.selected_lighting_tags.remove(tag)
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
        else:
            self.selected_lighting_tags.append(tag)
            ui['button'].setText(f"{IconManager.get('minus')}")
            ui['button'].setProperty("variant", "danger")
        ui['button'].style().unpolish(ui['button'])
        ui['button'].style().polish(ui['button'])
        self._refresh_selected_lighting_display()

    def _refresh_selected_lighting_display(self):
        if not hasattr(self, 'selected_lighting_layout'):
            return
        while self.selected_lighting_layout.count() > 1:
            item = self.selected_lighting_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.selected_lighting_tags:
            label = QLabel("(No lighting selected)")
            label.setObjectName("Subtitle")
            self.selected_lighting_layout.insertWidget(0, label)
            return
        for tag in self.selected_lighting_tags:
            chip = QWidget()
            chip.setProperty("variant", "chip")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 5, 4)
            chip_layout.setSpacing(5)
            chip_label = QLabel(tag.replace('_', ' '))
            chip_layout.addWidget(chip_label)
            remove_btn = QPushButton(f"{IconManager.get('close')}")
            remove_btn.setProperty("variant", "icon-only")
            remove_btn.setProperty("variant2", "ghost")
            remove_btn.setProperty("variant", "ghost")
            remove_btn.clicked.connect(lambda checked, t=tag: self._remove_lighting_tag(t))
            chip_layout.addWidget(remove_btn)
            self.selected_lighting_layout.insertWidget(
                self.selected_lighting_layout.count() - 1, chip
            )

    def _remove_lighting_tag(self, tag: str):
        if tag in self.selected_lighting_tags:
            self.selected_lighting_tags.remove(tag)
        tag_key = f"lighting::{tag}"
        if tag_key in self.lighting_tag_ui_elements:
            ui = self.lighting_tag_ui_elements[tag_key]
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])
        self._refresh_selected_lighting_display()

    def _sync_lighting_ui_states(self):
        if not self.lighting_tag_ui_elements:
            return
        for tag_key, ui in self.lighting_tag_ui_elements.items():
            tag = ui['tag']
            if tag in self.selected_lighting_tags:
                ui['button'].setText("-")
                ui['button'].setProperty("variant", "danger")
            else:
                ui['button'].setText("+")
                ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])

    def _build_weather_tree(self):
        while self.weather_tree_layout.count():
            item = self.weather_tree_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.weather_tag_ui_elements = {}
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
            self._create_weather_subcategory(sub_cat, file_path)
        self.weather_tree_layout.addStretch()

    def _create_weather_subcategory(self, sub_cat: str, file_path: Path):
        sub_frame = QWidget()
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(0, 1, 0, 1)
        sub_layout.setSpacing(0)

        toggle_btn = QPushButton(f"▶ {sub_cat.replace('_', ' ').title()}")
        toggle_btn.setProperty("variant", "section-toggle")
        sub_layout.addWidget(toggle_btn)

        tags_frame = QWidget()
        tags_frame.setVisible(False)
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(20, 5, 0, 5)
        tags_layout.setSpacing(1)

        tags = self._load_tags_from_file(file_path)
        for tag in tags:
            tag_key = f"weather::{tag}"
            tag_row = QWidget()
            tag_row.setObjectName("TagRow")
            tag_row_layout = QHBoxLayout(tag_row)
            tag_row_layout.setContentsMargins(0, 1, 0, 1)
            tag_row_layout.setSpacing(5)
            tag_label = QLabel(f"  {tag.replace('_', ' ')}")
            tag_row_layout.addWidget(tag_label, 1)
            action_btn = QPushButton(f"{IconManager.get('plus')}")
            action_btn.setProperty("variant", "success")
            action_btn.setProperty("variant2", "icon-only")
            action_btn.clicked.connect(
                lambda checked, t=tag, tk=tag_key: self._toggle_weather_tag(t, tk)
            )
            tag_row_layout.addWidget(action_btn)
            tags_layout.addWidget(tag_row)
            self.weather_tag_ui_elements[tag_key] = {
                'label': tag_label, 'button': action_btn, 'tag': tag
            }
        tags_layout.addStretch()
        sub_layout.addWidget(tags_frame)

        def toggle_visibility():
            is_visible = tags_frame.isVisible()
            tags_frame.setVisible(not is_visible)
            toggle_btn.setText(f"{'▼' if is_visible else '▶'} {sub_cat.replace('_', ' ').title()}")

        toggle_btn.clicked.connect(toggle_visibility)
        self.weather_tree_layout.addWidget(sub_frame)

    def _toggle_weather_tag(self, tag: str, tag_key: str):
        if tag_key not in self.weather_tag_ui_elements:
            return
        ui = self.weather_tag_ui_elements[tag_key]
        if tag in self.selected_weather_tags:
            self.selected_weather_tags.remove(tag)
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
        else:
            self.selected_weather_tags.append(tag)
            ui['button'].setText(f"{IconManager.get('minus')}")
            ui['button'].setProperty("variant", "danger")
        ui['button'].style().unpolish(ui['button'])
        ui['button'].style().polish(ui['button'])
        self._refresh_selected_weather_display()

    def _refresh_selected_weather_display(self):
        if not hasattr(self, 'selected_weather_layout'):
            return
        while self.selected_weather_layout.count() > 1:
            item = self.selected_weather_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.selected_weather_tags:
            label = QLabel("(No weather selected)")
            label.setObjectName("Subtitle")
            self.selected_weather_layout.insertWidget(0, label)
            return
        for tag in self.selected_weather_tags:
            chip = QWidget()
            chip.setProperty("variant", "chip")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 5, 4)
            chip_layout.setSpacing(5)
            chip_label = QLabel(tag.replace('_', ' '))
            chip_layout.addWidget(chip_label)
            remove_btn = QPushButton(f"{IconManager.get('close')}")
            remove_btn.setProperty("variant", "icon-only")
            remove_btn.setProperty("variant2", "ghost")
            remove_btn.setProperty("variant", "ghost")
            remove_btn.clicked.connect(lambda checked, t=tag: self._remove_weather_tag(t))
            chip_layout.addWidget(remove_btn)
            self.selected_weather_layout.insertWidget(
                self.selected_weather_layout.count() - 1, chip
            )

    def _remove_weather_tag(self, tag: str):
        if tag in self.selected_weather_tags:
            self.selected_weather_tags.remove(tag)
        tag_key = f"weather::{tag}"
        if tag_key in self.weather_tag_ui_elements:
            ui = self.weather_tag_ui_elements[tag_key]
            ui['button'].setText("+")
            ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])
        self._refresh_selected_weather_display()

    def _sync_weather_ui_states(self):
        if not self.weather_tag_ui_elements:
            return
        for tag_key, ui in self.weather_tag_ui_elements.items():
            tag = ui['tag']
            if tag in self.selected_weather_tags:
                ui['button'].setText("-")
                ui['button'].setProperty("variant", "danger")
            else:
                ui['button'].setText("+")
                ui['button'].setProperty("variant", "success")
            ui['button'].style().unpolish(ui['button'])
            ui['button'].style().polish(ui['button'])

    # ═══════════════════════════════════════════════
    # CUSTOM TAB
    # ═══════════════════════════════════════════════
    def _setup_custom_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("Custom Traits (Advanced)")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        description_frame = QFrame()
        description_frame.setProperty("variant", "info-frame")
        description_layout = QVBoxLayout(description_frame)
        description_layout.setContentsMargins(15, 15, 15, 15)
        description_label = QLabel(
            "For advanced users.\n\n"
            "This tab allows adding arbitrary tags.\n\n"
            "Examples:\n"
            "  - Compound descriptions: 'long straight light blue hair'\n"
            "  - Rare tags: 'freckles', 'beauty mark'\n"
            "  - Modifiers: 'cinematic lighting'"
        )
        description_label.setWordWrap(True)
        description_layout.addWidget(description_label)
        layout.addWidget(description_frame)

        hint_label = QLabel("Enter tags separated by commas:")
        hint_label.setObjectName("Subtitle")
        layout.addWidget(hint_label)

        self.other_traits_text = QPlainTextEdit()
        self.other_traits_text.setMaximumHeight(150)
        self.other_traits_text.setPlaceholderText("freckles, beauty mark, cinematic lighting, ...")
        self.other_traits_text.setObjectName("LogBox")
        layout.addWidget(self.other_traits_text)
        layout.addStretch()

    # ═══════════════════════════════════════════════
    # PREVIEW TAB
    # ═══════════════════════════════════════════════
    def _setup_preview_tab(self, widget: QWidget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("YAML Preview (Live)")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        refresh_btn = QPushButton("Refresh from Editor")
        refresh_btn.setProperty("variant", "primary")
        refresh_btn.clicked.connect(self._refresh_yaml_preview)
        buttons_layout.addWidget(refresh_btn)

        apply_btn = QPushButton("Apply Changes to Editor")
        apply_btn.setProperty("variant", "success")
        apply_btn.clicked.connect(self._apply_yaml_to_editor)
        buttons_layout.addWidget(apply_btn)

        copy_btn = QPushButton("Copy YAML")
        copy_btn.setProperty("variant", "ghost")
        copy_btn.clicked.connect(self._copy_yaml_to_clipboard)
        buttons_layout.addWidget(copy_btn)
        buttons_layout.addStretch()
        layout.addWidget(buttons_frame)

        self.yaml_textbox = QPlainTextEdit()
        self.yaml_textbox.setObjectName("AnalyzerLog")
        layout.addWidget(self.yaml_textbox, 1)
        self._refresh_yaml_preview()

    def _on_editor_tab_changed(self, index: int):
        if not hasattr(self, 'preview_widget') or not hasattr(self, 'yaml_textbox'):
            return
        if self.yaml_textbox is None:
            return
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
        selected_traits = [entry['tag'] for entry in self.selected_dna_tags]
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

            self.selected_dna_tags = []
            fixed_traits = profile.get('fixed_traits', [])
            all_dna_tags = {ui['tag']: ui['category'] for ui in self.dna_tag_ui_elements.values()}
            other_traits = []
            for trait in fixed_traits:
                if trait in all_dna_tags:
                    self.selected_dna_tags.append({'tag': trait, 'category': all_dna_tags[trait]})
                else:
                    other_traits.append(trait)
            self._sync_dna_tag_ui_states()
            self._refresh_selected_dna_tags_display()
            if self.other_traits_text:
                self.other_traits_text.clear()
                if other_traits:
                    self.other_traits_text.setPlainText(", ".join(other_traits))

            self.selected_wardrobe_tags = []
            for outfit_name, subcats in profile.get('outfit_whitelist', {}).items():
                if isinstance(subcats, dict):
                    for subcategory, tags in subcats.items():
                        if isinstance(tags, list):
                            for tag in tags:
                                self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': subcategory})
            self._sync_tag_ui_states()
            self._refresh_selected_tags_display()

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
            self._sync_personality_ui_states()
            self._refresh_personality_tags_display()

            self.signature_props = profile.get('signature_props', [])
            hair_rules = profile.get('hair_rules', {})
            self.hair_rules_data = {
                'default': hair_rules.get('default', 'hair down'),
                'conditional': hair_rules.get('conditional', [])
            }
            self._refresh_signature_props_display()
            self._refresh_hair_rules_display()

            atmosphere = profile.get('atmosphere_preferences', {})
            self.selected_lighting_tags = atmosphere.get('lighting', [])
            self.selected_weather_tags = atmosphere.get('weather', [])
            self._sync_lighting_ui_states()
            self._sync_weather_ui_states()
            self._refresh_selected_lighting_display()
            self._refresh_selected_weather_display()
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