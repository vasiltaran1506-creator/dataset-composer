import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import yaml
import shutil
import os

# Палитра цветов (дублируем из MainWindow)
COLORS = {
    'primary_blue': '#3b82f6',
    'primary_blue_hover': '#2563eb',
    'success_green': 'green',
    'success_green_hover': 'darkgreen',
    'danger_red': '#dc2626',
    'danger_red_hover': '#991b1b',
    'border_color': 'gray50',
}


class ProfilesTab(ctk.CTkFrame):
    """Вкладка редактирования профилей персонажей"""

    def __init__(
        self,
        master,
        project_root: Path,
        profiles_directory: Path,
        settings_manager,
        log_callback,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        # Сохраняем ссылки
        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.settings_manager = settings_manager
        self._log = log_callback
        
        # Состояние редактора
        self.current_profile_name: str | None = None
        self.profile_character_data: dict = {}
        
        # === DNA ===
        self.selected_dna_tags: list[dict] = []
        self.dna_tag_ui_elements: dict[str, dict] = {}
        
        # === Outfits ===
        self.selected_wardrobe_tags: list[dict] = []
        self.tag_ui_elements: dict[str, dict] = {}
        self.wardrobe_sections_expanded: dict[str, dict] = {}
        
        # === Personality ===
        self.preferred_personality_tags: list[dict] = []
        self.avoided_personality_tags: list[dict] = []
        self.personality_tag_ui_elements: dict[str, dict] = {}
        self.personality_sections_expanded: dict[str, dict] = {}
        
        # === Signature ===
        self.signature_props: list[dict] = []
        self._popup_selected_tags: set[str] = set()
        self._popup_selected_actions: set[str] = set()
        self.hair_rules_data: dict = {'default': 'hair down', 'conditional': []}
        
        # === Atmosphere ===
        self.selected_lighting_tags: list[str] = []
        self.selected_weather_tags: list[str] = []
        self.lighting_tag_ui_elements: dict[str, dict] = {}
        self.weather_tag_ui_elements: dict[str, dict] = {}
        self.atmosphere_sections_expanded: dict[str, dict] = {}
        
        # === UI виджеты ===
        self.profiles_listbox: ctk.CTkScrollableFrame | None = None
        self.editor_title: ctk.CTkLabel | None = None
        self.edit_name_btn: ctk.CTkButton | None = None
        self.editor_tabview: ctk.CTkTabview | None = None
        
        # Scrollable frames
        self.dna_scroll: ctk.CTkScrollableFrame | None = None
        self.dna_tree_frame: ctk.CTkFrame | None = None
        self.selected_dna_tags_container: ctk.CTkScrollableFrame | None = None
        self.other_traits_text: ctk.CTkTextbox | None = None
        self.outfits_scroll: ctk.CTkScrollableFrame | None = None
        self.wardrobe_tree_frame: ctk.CTkFrame | None = None
        self.selected_tags_container: ctk.CTkScrollableFrame | None = None
        self.custom_scroll: ctk.CTkScrollableFrame | None = None
        self.personality_scroll: ctk.CTkScrollableFrame | None = None
        self.personality_tree_frame: ctk.CTkFrame | None = None
        self.prefer_container: ctk.CTkScrollableFrame | None = None
        self.avoid_container: ctk.CTkScrollableFrame | None = None
        self.signature_scroll: ctk.CTkScrollableFrame | None = None
        self.props_container: ctk.CTkFrame | None = None
        self.hair_default_btn: ctk.CTkButton | None = None
        self.hair_rules_container: ctk.CTkFrame | None = None
        self.atmosphere_scroll: ctk.CTkScrollableFrame | None = None
        self.lighting_tree_frame: ctk.CTkFrame | None = None
        self.weather_tree_frame: ctk.CTkFrame | None = None
        self.selected_lighting_container: ctk.CTkScrollableFrame | None = None
        self.selected_weather_container: ctk.CTkScrollableFrame | None = None
        self.preview_scroll: ctk.CTkScrollableFrame | None = None
        self.yaml_textbox: ctk.CTkTextbox | None = None
        
        # Кэш тегов
        self._tags_cache = {}
        
        # Debouncing
        self._update_timer = None
        self._ui_update_timer = None
        self._pending_ui_updates = set()
        
        # Строим UI
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Profiles"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # === ЛЕВАЯ ПАНЕЛЬ: Список профилей ===
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(left_frame, text="📋 Characters",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        self.profiles_listbox = ctk.CTkScrollableFrame(left_frame, width=200)
        self.profiles_listbox.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        buttons_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(buttons_frame, text="➕ New",
                      fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                      command=self._create_new_profile).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        
        ctk.CTkButton(buttons_frame, text="📥 Upload",
                      fg_color=COLORS['primary_blue'], hover_color=COLORS['primary_blue_hover'],
                      command=self._import_profile).grid(row=0, column=1, padx=3, sticky="ew")
        
        ctk.CTkButton(buttons_frame, text="🗑️ Delete",
                      fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                      command=self._delete_profile).grid(row=0, column=2, padx=(3, 0), sticky="ew")
        
        # === ПРАВАЯ ПАНЕЛЬ: Редактор ===
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        title_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        title_frame.grid_columnconfigure(1, weight=1)
        
        self.editor_title = ctk.CTkLabel(title_frame, text="👤 Editing: (no selection)",
                                         font=ctk.CTkFont(size=18, weight="bold"))
        self.editor_title.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.edit_name_btn = ctk.CTkButton(title_frame, text="✏️", width=35, height=30,
                                           fg_color="transparent", hover_color="gray40",
                                           text_color="gray70", font=ctk.CTkFont(size=16),
                                           command=self._edit_profile_name)
        self.edit_name_btn.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        ctk.CTkButton(title_frame, text="💾 Save Profile",
                      fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      width=130, height=35,
                      command=self._save_profile).grid(row=0, column=2)
        
        # Субвкладки редактора
        self.editor_tabview = ctk.CTkTabview(right_frame)
        self.editor_tabview.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        self.editor_tabview.add("🧬 DNA")
        self.editor_tabview.add("👗 Outfits")
        self.editor_tabview.add("🎭 Personality")
        self.editor_tabview.add("✨ Signature")
        self.editor_tabview.add("🌍 Atmosphere")
        self.editor_tabview.add("✍️ Custom")
        self.editor_tabview.add("📄 Preview")
        
        # Создаём scrollable frames для каждой субвкладки
        self.dna_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("🧬 DNA"))
        self.dna_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.outfits_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("👗 Outfits"))
        self.outfits_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.personality_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("🎭 Personality"))
        self.personality_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.signature_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("✨ Signature"))
        self.signature_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.atmosphere_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("🌍 Atmosphere"))
        self.atmosphere_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.custom_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("✍️ Custom"))
        self.custom_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.preview_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("📄 Preview"))
        self.preview_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Инициализируем содержимое субвкладок
        self._init_dna_tab()
        self._init_outfits_tab()
        self._init_personality_tab()
        self._init_signature_tab()
        self._init_atmosphere_tab()
        self._init_custom_tab()
        self._init_preview_tab()
        
        # Загружаем список профилей
        self._refresh_profiles_list()

    def _init_dna_tab(self):
        """Инициализирует содержимое вкладки DNA"""
        dna_frame = ctk.CTkFrame(self.dna_scroll)
        dna_frame.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(dna_frame, text="🧬 Character DNA",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.dna_tree_frame = ctk.CTkFrame(dna_frame, fg_color="transparent")
        self.dna_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._build_dna_tree()
        
        selected_dna_frame = ctk.CTkFrame(dna_frame)
        selected_dna_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        
        ctk.CTkLabel(selected_dna_frame, text="✅ Selected DNA Tags:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_dna_tags_container = ctk.CTkScrollableFrame(
            selected_dna_frame, fg_color="transparent"
        )
        self.selected_dna_tags_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._refresh_selected_dna_tags_display()

    def _init_outfits_tab(self):
        """Инициализирует содержимое вкладки Outfits"""
        wardrobe_frame = ctk.CTkFrame(self.outfits_scroll)
        wardrobe_frame.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(wardrobe_frame, text="👗 Wardrobe (Whitelist)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.wardrobe_tree_frame = ctk.CTkFrame(wardrobe_frame, fg_color="transparent")
        self.wardrobe_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._build_wardrobe_tree()
        
        selected_wardrobe_frame = ctk.CTkFrame(wardrobe_frame)
        selected_wardrobe_frame.pack(fill="x", padx=10, pady=(10, 10))
        
        ctk.CTkLabel(selected_wardrobe_frame, text="✅ Selected Wardrobe Tags:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_tags_container = ctk.CTkScrollableFrame(
            selected_wardrobe_frame, fg_color="transparent", height=120
        )
        self.selected_tags_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_selected_tags_display()

    def _init_personality_tab(self):
        """Инициализирует содержимое вкладки Personality"""
        personality_frame = ctk.CTkFrame(self.personality_scroll)
        personality_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(personality_frame, text="🎭 Personality Filters (Prefer / Avoid)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.personality_tree_frame = ctk.CTkFrame(personality_frame, fg_color="transparent")
        self.personality_tree_frame.pack(fill="x", padx=20, pady=5)
        
        self._build_personality_tree()
        
        summary_frame = ctk.CTkFrame(personality_frame, fg_color="transparent")
        summary_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=1)
        summary_frame.grid_rowconfigure(1, weight=1)
        
        prefer_frame = ctk.CTkFrame(summary_frame)
        prefer_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        
        ctk.CTkLabel(prefer_frame, text="✅ Preferred:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(8, 5))
        
        self.prefer_container = ctk.CTkScrollableFrame(prefer_frame, fg_color="transparent")
        self.prefer_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        avoid_frame = ctk.CTkFrame(summary_frame)
        avoid_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(avoid_frame, text="🚫 Avoided:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(8, 5))
        
        self.avoid_container = ctk.CTkScrollableFrame(avoid_frame, fg_color="transparent")
        self.avoid_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._refresh_personality_tags_display()

    def _init_signature_tab(self):
        """Инициализирует содержимое вкладки Signature"""
        signature_frame = ctk.CTkFrame(self.signature_scroll)
        signature_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(signature_frame, text="✨ Signature Items & Hair Rules",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Props section
        props_section = ctk.CTkFrame(signature_frame)
        props_section.pack(fill="x", padx=10, pady=10)
        
        props_header = ctk.CTkFrame(props_section, fg_color="transparent")
        props_header.pack(fill="x", padx=10, pady=(5, 5))
        props_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(props_header, text="🧸 Signature Props",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(props_header, text="➕ Add Prop", height=28,
                      fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                      command=self._add_signature_prop).grid(row=0, column=1, sticky="e")
        
        self.props_container = ctk.CTkFrame(props_section, fg_color="transparent")
        self.props_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # Hair section
        hair_section = ctk.CTkFrame(signature_frame)
        hair_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(hair_section, text="💇 Hair Rules",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        default_frame = ctk.CTkFrame(hair_section, fg_color="transparent")
        default_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(default_frame, text="Default Style:", width=120, anchor="w").pack(side="left")
        
        self.hair_default_btn = ctk.CTkButton(default_frame, text="▼ hair down", width=300, height=28,
                                              fg_color="gray40", hover_color="gray50",
                                              font=ctk.CTkFont(size=11),
                                              command=self._open_default_style_selector)
        self.hair_default_btn.pack(side="left", padx=(5, 0))
        
        cond_header = ctk.CTkFrame(hair_section, fg_color="transparent")
        cond_header.pack(fill="x", padx=10, pady=(10, 5))
        cond_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(cond_header, text="Conditional Rules:",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(cond_header, text="➕ Add Rule", height=28,
                      fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                      command=self._add_hair_rule).grid(row=0, column=1, sticky="e")
        
        self.hair_rules_container = ctk.CTkFrame(hair_section, fg_color="transparent")
        self.hair_rules_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_signature_props_display()
        self._refresh_hair_rules_display()

    def _init_atmosphere_tab(self):
        """Инициализирует содержимое вкладки Atmosphere"""
        atmosphere_frame = ctk.CTkFrame(self.atmosphere_scroll)
        atmosphere_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(atmosphere_frame, text="🌍 Atmosphere Preferences",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Lighting
        lighting_section = ctk.CTkFrame(atmosphere_frame)
        lighting_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(lighting_section, text="💡 Lighting Preferences",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.lighting_tree_frame = ctk.CTkFrame(lighting_section, fg_color="transparent")
        self.lighting_tree_frame.pack(fill="x", padx=10, pady=5)
        
        self._build_lighting_tree()
        
        selected_lighting_frame = ctk.CTkFrame(lighting_section)
        selected_lighting_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(selected_lighting_frame, text="✅ Selected Lighting:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_lighting_container = ctk.CTkScrollableFrame(
            selected_lighting_frame, fg_color="transparent", height=100
        )
        self.selected_lighting_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # Weather
        weather_section = ctk.CTkFrame(atmosphere_frame)
        weather_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(weather_section, text="🌦️ Weather Preferences",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.weather_tree_frame = ctk.CTkFrame(weather_section, fg_color="transparent")
        self.weather_tree_frame.pack(fill="x", padx=10, pady=5)
        
        self._build_weather_tree()
        
        selected_weather_frame = ctk.CTkFrame(weather_section)
        selected_weather_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(selected_weather_frame, text="✅ Selected Weather:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_weather_container = ctk.CTkScrollableFrame(
            selected_weather_frame, fg_color="transparent", height=100
        )
        self.selected_weather_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_selected_lighting_display()
        self._refresh_selected_weather_display()

    def _init_custom_tab(self):
        """Инициализирует содержимое вкладки Custom"""
        custom_frame = ctk.CTkFrame(self.custom_scroll)
        custom_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(custom_frame, text="✍️ Custom Traits (Advanced)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        description_frame = ctk.CTkFrame(custom_frame, fg_color="gray20", corner_radius=10)
        description_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(description_frame,
                     text="⚙️ Для продвинутых пользователей\n"
                          "Эта вкладка позволяет добавить произвольные теги.\n"
                          "💡 Примеры:\n"
                          "• Составные описания: 'long straight light blue hair'\n"
                          "• Редкие теги: 'freckles', 'beauty mark'\n"
                          "• Модификаторы: 'cinematic lighting'",
                     text_color="gray80", justify="left", wraplength=600).pack(anchor="w", padx=15, pady=15)
        
        ctk.CTkLabel(custom_frame, text="   Введите теги через запятую:",
                     text_color="gray").pack(anchor="w", padx=20, pady=(5, 5))
        
        self.other_traits_text = ctk.CTkTextbox(custom_frame, height=150)
        self.other_traits_text.pack(fill="x", padx=20, pady=(0, 10))

    def _init_preview_tab(self):
        """Инициализирует содержимое вкладки Preview"""
        preview_frame = ctk.CTkFrame(self.preview_scroll)
        preview_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(preview_frame, text="📄 YAML Preview (Live)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        buttons_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="🔄 Refresh from Editor", width=180,
                      fg_color=COLORS['primary_blue'], hover_color=COLORS['primary_blue_hover'],
                      command=self._refresh_yaml_preview).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(buttons_frame, text="✅ Apply Changes to Editor", width=200,
                      fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                      command=self._apply_yaml_to_editor).pack(side="left", padx=5)
        
        ctk.CTkButton(buttons_frame, text="📋 Copy YAML", width=120,
                      fg_color="gray40", hover_color="gray50",
                      command=self._copy_yaml_to_clipboard).pack(side="left", padx=5)
        
        self.yaml_textbox = ctk.CTkTextbox(preview_frame, font=ctk.CTkFont(family="Consolas", size=12), height=500)
        self.yaml_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._refresh_yaml_preview()

    # ═══════════════════════════════════════════════
    # PROFILES: Управление списком персонажей
    # ═══════════════════════════════════════════════
    def _get_available_profiles(self) -> list[str]:
        """Сканирует папку profiles и возвращает список доступных имён"""
        profiles = []
        if self.profiles_directory.exists():
            for file in self.profiles_directory.glob("*.yaml"):
                profiles.append(file.stem)
        if not profiles:
            root_yaml = self.project_root / "character-profile.yaml"
            if root_yaml.exists():
                profiles.append("luna")
        return profiles if profiles else ["No profiles found"]

    def _refresh_profiles_list(self):
        """Обновляет левый список персонажей во вкладке Profiles"""
        if self.profiles_listbox is None:
            return
        for widget in self.profiles_listbox.winfo_children():
            widget.destroy()
        for profile_name in self._get_available_profiles():
            if profile_name == "No profiles found":
                continue
            btn = ctk.CTkButton(
                self.profiles_listbox, text=f"👤 {profile_name}", anchor="w", height=35,
                fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray30"),
                border_width=1, border_color=COLORS['border_color'],
                command=lambda p=profile_name: self._select_profile(p)
            )
            btn.pack(fill="x", pady=2)

    def _select_profile(self, profile_name: str):
        """Обработчик клика на профиль в списке"""
        self.current_profile_name = profile_name
        if self.editor_title:
            self.editor_title.configure(text=f"👤 Editing: {profile_name}")
        self._load_profile_to_editor(profile_name)
        self._refresh_yaml_preview()

    def _edit_profile_name(self):
        """Открывает диалог для переименования профиля"""
        if not self.current_profile_name:
            messagebox.showwarning("Warning", "No profile selected")
            return
        new_name = simpledialog.askstring("Rename Profile", "Enter new name:",
                                          initialvalue=self.current_profile_name)
        if not new_name:
            return
        new_name = new_name.strip().replace(' ', '_')
        if not new_name or not all(c.isalnum() or c == '_' for c in new_name):
            messagebox.showerror("Error", "Name must contain only letters, numbers and underscores")
            return
        if new_name == self.current_profile_name:
            return
        old_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not old_path.exists():
            old_path = self.project_root / "character-profile.yaml"
        new_path = self.profiles_directory / f"{new_name}.yaml"
        if new_path.exists():
            messagebox.showerror("Error", f"Profile '{new_name}' already exists!")
            return
        try:
            if old_path.exists():
                shutil.move(str(old_path), str(new_path))
            old_name = self.current_profile_name
            self.current_profile_name = new_name
            if self.editor_title:
                self.editor_title.configure(text=f"👤 Editing: {new_name}")
            self._refresh_profiles_list()
            self._refresh_yaml_preview()
            self._log(f"✏️ Профиль переименован: {old_name} → {new_name}\n")
            messagebox.showinfo("Success", f"Profile renamed to '{new_name}'!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename: {e}")

    def _create_new_profile(self):
        """Создает новый YAML-файл профиля с дефолтной структурой"""
        name = simpledialog.askstring("New Profile", "Enter character name:")
        if not name:
            return
        name = name.strip().replace(' ', '_')
        if not name or not all(c.isalnum() or c == '_' for c in name):
            messagebox.showerror("Error", "Name must contain only letters, numbers and underscores")
            return
        new_path = self.profiles_directory / f"{name}.yaml"
        if new_path.exists():
            messagebox.showerror("Error", f"Profile '{name}' already exists!")
            return
        profile = self._get_default_profile_structure(name)
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(f"# Character Profile: {name}\n")
            f.write("# Фильтр поверх scene-rules\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._log(f"➕ Создан новый профиль: {name}\n")
        self._refresh_profiles_list()
        self._select_profile(name)
        messagebox.showinfo("Success", f"Profile '{name}' created!")

    def _import_profile(self):
        """Импортирует профиль из внешнего YAML-файла"""
        file_path = filedialog.askopenfilename(
            title="Import Character Profile",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
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
            messagebox.showinfo("Success", f"Profile imported as '{dest.stem}'!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")

    def _delete_profile(self):
        """Удаляет выбранный профиль (файл + очистка UI)"""
        if not self.current_profile_name:
            messagebox.showwarning("Warning", "No profile selected")
            return
        if self.settings_manager.get('behavior', 'confirm_delete'):
            if not messagebox.askyesno("Confirm Delete",
                                       f"Are you sure you want to delete '{self.current_profile_name}'?\n"
                                       "This cannot be undone!"):
                return
        profile_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            messagebox.showerror("Error", "Profile file not found")
            return
        try:
            profile_path.unlink()
            self._log(f"🗑️ Удалён профиль: {self.current_profile_name}\n")
            self.current_profile_name = None
            self.profile_character_data = {}
            if self.editor_title:
                self.editor_title.configure(text="👤 Editing: (no selection)")
            if self.other_traits_text:
                self.other_traits_text.delete("1.0", "end")
            self.selected_dna_tags = []
            self._sync_dna_tag_ui_states()
            self._refresh_selected_dna_tags_display()
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
            self._refresh_selected_lighting_display()
            self._refresh_selected_weather_display()
            self._refresh_profiles_list()
            messagebox.showinfo("Success", "Profile deleted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

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

    # ═══════════════════════════════════════════════
    # DNA
    # ═══════════════════════════════════════════════
    def _build_dna_tree(self):
        """Строит дерево DNA (Hair Style, Hair Color, Eye Color)"""
        if self.dna_tree_frame is None:
            return
        for w in self.dna_tree_frame.winfo_children():
            w.destroy()
        self.dna_tag_ui_elements = {}
        
        for cat_name, cat_file in [
            ("🧬 Body Type", "01_character/body/type.txt"),
            ("🎭 Body Features", "01_character/body/features.txt"),
            ("👁️ Eye Color", "01_character/eyes/color.txt"),
            ("👁️ Eye Shape", "01_character/eyes/shape.txt"),
            ("🎭 Face Features", "01_character/face/features.txt"),
            ("💇 Hair Style", "01_character/hair/style.txt"),
            ("💇 Hair Color", "01_character/hair/color.txt"),
            ("💇 Hair Length", "01_character/hair/length.txt"),
            ("🧴 Skin Tone", "01_character/skin/tone.txt"),
        ]:
            self._create_dna_category(cat_name, cat_file)

    def _create_dna_category(self, cat_name, cat_file):
        """Создает раскрывающуюся категорию DNA"""
        if self.dna_tree_frame is None:
            return
        cat_frame = ctk.CTkFrame(self.dna_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        ctk.CTkButton(cat_frame, text=f"➤ {cat_name}", anchor="w",
                      fg_color="gray30", hover_color="gray40", height=30,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: self._toggle_dna_category(cat_name)).pack(fill="x")
        
        tags_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        
        self._wardrobe_sections_expanded_local(f"dna.{cat_name}", tags_frame)
        
        for tag in self._load_tags_from_library(cat_file):
            tag_key = f"dna::{cat_name}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(tag_row, text=f"  • {tag.replace('_', ' ')}", anchor="w")
            tag_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            action_btn = ctk.CTkButton(tag_row, text="+", width=30, height=25,
                                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       command=lambda t=tag, cn=cat_name, tk=tag_key: self._toggle_dna_tag(t, cn, tk))
            action_btn.pack(side="right", padx=(0, 5))
            
            self.dna_tag_ui_elements[tag_key] = {
                'label': tag_label, 'button': action_btn, 'tag': tag, 'category': cat_name
            }

    def _wardrobe_sections_expanded_local(self, key, frame):
        """Локальный аналог wardrobe_sections_expanded для DNA"""
        if not hasattr(self, '_wardrobe_sections_state'):
            self._wardrobe_sections_state = {}
        self._wardrobe_sections_state[key] = {'frame': frame, 'expanded': False}

    def _get_section_state(self, key):
        if not hasattr(self, '_wardrobe_sections_state'):
            self._wardrobe_sections_state = {}
        return self._wardrobe_sections_state.get(key)

    def _set_section_state(self, key, expanded):
        if not hasattr(self, '_wardrobe_sections_state'):
            self._wardrobe_sections_state = {}
        if key in self._wardrobe_sections_state:
            self._wardrobe_sections_state[key]['expanded'] = expanded

    def _toggle_dna_category(self, cat_name):
        """Разворачивает/сворачивает категорию DNA"""
        key = f"dna.{cat_name}"
        section = self._get_section_state(key)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(key, not section['expanded'])

    def _toggle_dna_tag(self, tag, category, tag_key):
        """Добавляет/убирает DNA-тег из выбранных"""
        if tag_key not in self.dna_tag_ui_elements:
            return
        tag_entry = {'tag': tag, 'category': category}
        ui = self.dna_tag_ui_elements[tag_key]
        
        if tag_entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(tag_entry)
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        else:
            self.selected_dna_tags.append(tag_entry)
            ui['label'].configure(text_color="green")
            ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
        
        self._debounce_ui_update('dna_chips')
        self._debounce_ui_update('yaml_preview')
        self._debounce_ui_update('hair_rules')

    def _refresh_selected_dna_tags_display(self):
        """Отрисовывает chips с выбранными DNA-тегами"""
        if self.selected_dna_tags_container is None:
            return
        for w in self.selected_dna_tags_container.winfo_children():
            w.destroy()
        
        if not self.selected_dna_tags:
            ctk.CTkLabel(self.selected_dna_tags_container,
                         text="(No DNA tags selected — разверните категории и нажмите [+])",
                         text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        
        COLS = 4
        for i, te in enumerate(self.selected_dna_tags):
            chip = ctk.CTkFrame(self.selected_dna_tags_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i // COLS, column=i % COLS, padx=3, pady=3, sticky="ew")
            self.selected_dna_tags_container.grid_columnconfigure(i % COLS, weight=1)
            
            ctk.CTkLabel(chip, text=f"  {te['tag'].replace('_', ' ')}  ",
                         font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 5), pady=4)
            ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                          hover_color=COLORS['danger_red'], text_color="white",
                          font=ctk.CTkFont(size=14, weight="bold"),
                          command=lambda te=te: self._remove_dna_tag_from_chip(te)).pack(side="right", padx=(0, 5), pady=2)

    def _remove_dna_tag_from_chip(self, tag_entry):
        """Удаляет DNA-тег через клик на крестик в chip"""
        if tag_entry not in self.selected_dna_tags:
            return
        self.selected_dna_tags.remove(tag_entry)
        tag_key = f"dna::{tag_entry['category']}::{tag_entry['tag']}"
        if tag_key in self.dna_tag_ui_elements:
            ui = self.dna_tag_ui_elements[tag_key]
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        self._debounce_ui_update('dna_chips')
        self._debounce_ui_update('yaml_preview')
        self._debounce_ui_update('hair_rules')

    def _sync_dna_tag_ui_states(self):
        """Синхронизирует UI DNA с текущими выбранными тегами"""
        if not self.dna_tag_ui_elements:
            return
        for tag_key, ui in self.dna_tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'category': ui['category']}
            if tag_entry in self.selected_dna_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    def _sync_lighting_ui_states(self):
        """Синхронизирует UI Lighting с выбранными тегами"""
        if not self.lighting_tag_ui_elements:
            return
        for tag_key, ui in self.lighting_tag_ui_elements.items():
            tag = ui['tag']
            if tag in self.selected_lighting_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    def _sync_weather_ui_states(self):
        """Синхронизирует UI Weather с выбранными тегами"""
        if not self.weather_tag_ui_elements:
            return
        for tag_key, ui in self.weather_tag_ui_elements.items():
            tag = ui['tag']
            if tag in self.selected_weather_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    # ═══════════════════════════════════════════════
    # OUTFITS
    # ═══════════════════════════════════════════════
    def _build_wardrobe_tree(self):
        """Строит дерево одежды из prompt-library/02_clothing"""
        if self.wardrobe_tree_frame is None:
            return
        for w in self.wardrobe_tree_frame.winfo_children():
            w.destroy()
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
        
        ORDER = ['full_body', 'topwear', 'bottomwear', 'legwear', 'footwear', 'underwear', 'accessories']
        
        def sort_key(cat):
            try:
                return ORDER.index(cat.lower())
            except ValueError:
                return 999
        
        for main_cat in sorted(categories.keys(), key=sort_key):
            self._create_wardrobe_category(main_cat, categories[main_cat])

    def _create_wardrobe_category(self, main_cat, subcats):
        """Создает главную категорию одежды"""
        if self.wardrobe_tree_frame is None:
            return
        cat_frame = ctk.CTkFrame(self.wardrobe_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        ctk.CTkButton(cat_frame, text=f"➤ {main_cat.replace('_', ' ').title()}", anchor="w",
                      fg_color="gray30", hover_color="gray40", height=30,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: self._toggle_category(main_cat)).pack(fill="x")
        
        subcats_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        subcats_frame.pack(fill="x", padx=(20, 0))
        subcats_frame.pack_forget()
        
        self._wardrobe_sections_expanded_local(main_cat, subcats_frame)
        
        for sub_cat, file_path in subcats.items():
            self._create_wardrobe_subcategory(subcats_frame, main_cat, sub_cat, file_path)

    def _create_wardrobe_subcategory(self, parent_frame, main_cat, sub_cat, file_path):
        """Создает подкатегорию одежды"""
        sub_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        
        ctk.CTkButton(sub_frame, text=f"  ➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                      fg_color="gray25", hover_color="gray35", height=26,
                      font=ctk.CTkFont(size=12),
                      command=lambda: self._toggle_subcategory(main_cat, sub_cat)).pack(fill="x")
        
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        
        self._wardrobe_sections_expanded_local(f"{main_cat}.{sub_cat}", tags_frame)
        
        for tag in self._load_tags_from_file(file_path):
            tag_key = f"{sub_cat}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(tag_row, text=f"    • {tag.replace('_', ' ')}", anchor="w")
            tag_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            action_btn = ctk.CTkButton(tag_row, text="+", width=30, height=25,
                                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       command=lambda t=tag, sc=sub_cat, tk=tag_key: self._toggle_wardrobe_tag(t, sc, tk))
            action_btn.pack(side="right", padx=(0, 5))
            
            self.tag_ui_elements[tag_key] = {
                'label': tag_label, 'button': action_btn, 'tag': tag, 'subcategory': sub_cat
            }

    def _toggle_category(self, main_cat):
        """Разворачивает/сворачивает главную категорию одежды"""
        section = self._get_section_state(main_cat)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(main_cat, not section['expanded'])

    def _toggle_subcategory(self, main_cat, sub_cat):
        """Разворачивает/сворачивает подкатегорию одежды"""
        key = f"{main_cat}.{sub_cat}"
        section = self._get_section_state(key)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(key, not section['expanded'])

    def _toggle_wardrobe_tag(self, tag, subcategory, tag_key):
        """Добавляет/убирает тег одежды из whitelist"""
        if tag_key not in self.tag_ui_elements:
            return
        tag_entry = {'tag': tag, 'subcategory': subcategory}
        ui = self.tag_ui_elements[tag_key]
        
        if tag_entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(tag_entry)
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        else:
            self.selected_wardrobe_tags.append(tag_entry)
            ui['label'].configure(text_color="green")
            ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
        
        self._debounce_ui_update('wardrobe_chips')

    def _refresh_selected_tags_display(self):
        """Отрисовывает chips с выбранными тегами одежды"""
        if self.selected_tags_container is None:
            return
        for w in self.selected_tags_container.winfo_children():
            w.destroy()
        
        if not self.selected_wardrobe_tags:
            ctk.CTkLabel(self.selected_tags_container,
                         text="(No tags selected)", text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        
        COLS = 4
        for i, te in enumerate(self.selected_wardrobe_tags):
            chip = ctk.CTkFrame(self.selected_tags_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i // COLS, column=i % COLS, padx=3, pady=3, sticky="ew")
            self.selected_tags_container.grid_columnconfigure(i % COLS, weight=1)
            
            ctk.CTkLabel(chip, text=f"  {te['tag'].replace('_', ' ')}  ",
                         font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 5), pady=4)
            ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                          hover_color=COLORS['danger_red'], text_color="white",
                          font=ctk.CTkFont(size=14, weight="bold"),
                          command=lambda te=te: self._remove_tag_from_chip(te)).pack(side="right", padx=(0, 5), pady=2)

    def _remove_tag_from_chip(self, tag_entry):
        """Удаляет тег одежды через крестик в chip"""
        if tag_entry not in self.selected_wardrobe_tags:
            return
        self.selected_wardrobe_tags.remove(tag_entry)
        tag_key = f"{tag_entry['subcategory']}::{tag_entry['tag']}"
        if tag_key in self.tag_ui_elements:
            ui = self.tag_ui_elements[tag_key]
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        self._debounce_ui_update('wardrobe_chips')

    def _sync_tag_ui_states(self):
        """Синхронизирует UI одежды с текущими выбранными тегами"""
        if not self.tag_ui_elements:
            return
        for tag_key, ui in self.tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'subcategory': ui['subcategory']}
            if tag_entry in self.selected_wardrobe_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    # ═══════════════════════════════════════════════
    # PERSONALITY
    # ═══════════════════════════════════════════════
    def _build_personality_tree(self):
        """Строит дерево фильтров Personality (Prefer / Avoid)"""
        if self.personality_tree_frame is None:
            return
        for w in self.personality_tree_frame.winfo_children():
            w.destroy()
        self.personality_tag_ui_elements = {}
        
        categories = [
            ("Expressions", "05_expression", ["mood", "eyes_expr", "mouth"]),
            ("Poses", "03_pose", ["base", "head", "arms", "legs"]),
        ]
        
        for cat_name, cat_dir, subcat_order in categories:
            self._create_personality_category(cat_name, cat_dir, subcat_order)

    def _create_personality_category(self, cat_name, cat_dir, subcat_order):
        if self.personality_tree_frame is None:
            return
        cat_frame = ctk.CTkFrame(self.personality_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        ctk.CTkButton(cat_frame, text=f"➤ {cat_name}", anchor="w",
                      fg_color="gray30", hover_color="gray40", height=30,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: self._toggle_personality_category(cat_name)).pack(fill="x")
        
        subcats_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        subcats_frame.pack(fill="x", padx=(20, 0))
        subcats_frame.pack_forget()
        
        self._wardrobe_sections_expanded_local(f"personality.{cat_name}", subcats_frame)
        
        dir_path = self.project_root / "prompt-library" / cat_dir
        if not dir_path.exists():
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
            self._create_personality_subcategory(subcats_frame, cat_name, sub_cat, subcats[sub_cat])

    def _create_personality_subcategory(self, parent_frame, cat_name, sub_cat, file_path):
        sub_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        
        ctk.CTkButton(sub_frame, text=f"  ➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                      fg_color="gray25", hover_color="gray35", height=26,
                      font=ctk.CTkFont(size=12),
                      command=lambda: self._toggle_personality_subcategory(cat_name, sub_cat)).pack(fill="x")
        
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        
        self._wardrobe_sections_expanded_local(f"personality.{cat_name}.{sub_cat}", tags_frame)
        
        for tag in self._load_tags_from_file(file_path):
            tag_key = f"personality::{cat_name}::{sub_cat}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(tag_row, text=f"    • {tag.replace('_', ' ')}", anchor="w", width=220)
            tag_label.pack(side="left", padx=(5, 0))
            
            avoid_btn = ctk.CTkButton(tag_row, text="-", width=25, height=22,
                                      fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      command=lambda t=tag, cn=cat_name, sc=sub_cat, tk=tag_key:
                                      self._toggle_personality_tag(t, cn, sc, tk, 'avoid'))
            avoid_btn.pack(side="right", padx=(0, 2))
            
            prefer_btn = ctk.CTkButton(tag_row, text="+", width=25, height=22,
                                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       command=lambda t=tag, cn=cat_name, sc=sub_cat, tk=tag_key:
                                       self._toggle_personality_tag(t, cn, sc, tk, 'prefer'))
            prefer_btn.pack(side="right", padx=(0, 2))
            
            self.personality_tag_ui_elements[tag_key] = {
                'label': tag_label, 'prefer_btn': prefer_btn, 'avoid_btn': avoid_btn,
                'tag': tag, 'category': cat_name, 'subcategory': sub_cat
            }

    def _toggle_personality_category(self, cat_name):
        key = f"personality.{cat_name}"
        section = self._get_section_state(key)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(key, not section['expanded'])

    def _toggle_personality_subcategory(self, cat_name, sub_cat):
        key = f"personality.{cat_name}.{sub_cat}"
        section = self._get_section_state(key)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(key, not section['expanded'])

    def _toggle_personality_tag(self, tag, category, subcategory, tag_key, action):
        """Добавляет/убирает тег в Prefer или Avoid"""
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
        self._debounce_ui_update('personality_chips')

    def _sync_personality_ui_states(self):
        """Синхронизирует цвета кнопок Prefer/Avoid с текущим состоянием"""
        if not self.personality_tag_ui_elements:
            return
        for tag_key, ui in self.personality_tag_ui_elements.items():
            tag = ui['tag']
            in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
            in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
            
            if in_prefer:
                ui['label'].configure(text_color="green")
                ui['prefer_btn'].configure(text="✓", fg_color="darkgreen", hover_color="darkgreen")
                ui['avoid_btn'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            elif in_avoid:
                ui['label'].configure(text_color=COLORS['danger_red'])
                ui['prefer_btn'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
                ui['avoid_btn'].configure(text="✓", fg_color="#991b1b", hover_color="#991b1b")
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['prefer_btn'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
                ui['avoid_btn'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])

    def _refresh_personality_tags_display(self):
        """Отрисовывает chips в секциях Preferred и Avoided"""
        if self.prefer_container is None or self.avoid_container is None:
            return
        for w in self.prefer_container.winfo_children():
            w.destroy()
        for w in self.avoid_container.winfo_children():
            w.destroy()
        
        def build_chips(container, tags, color):
            if not tags:
                ctk.CTkLabel(container, text="(empty)", text_color="gray").pack(anchor="w", padx=10, pady=5)
                return
            COLS = 2
            for i, entry in enumerate(tags):
                chip = ctk.CTkFrame(container, fg_color="gray30", corner_radius=15)
                chip.grid(row=i // COLS, column=i % COLS, padx=3, pady=3, sticky="ew")
                container.grid_columnconfigure(i % COLS, weight=1)
                
                lbl = ctk.CTkLabel(chip, text=f" {entry['tag'].replace('_', ' ')} ",
                                   font=ctk.CTkFont(size=13), text_color=color)
                lbl.pack(side="left", padx=(8, 5), pady=5)
                
                def remove(t=entry['tag']):
                    self.preferred_personality_tags = [x for x in self.preferred_personality_tags if x['tag'] != t]
                    self.avoided_personality_tags = [x for x in self.avoided_personality_tags if x['tag'] != t]
                    self._sync_personality_ui_states()
                    self._refresh_personality_tags_display()
                
                ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                              hover_color=COLORS['danger_red'], text_color="white",
                              font=ctk.CTkFont(size=14, weight="bold"),
                              command=remove).pack(side="right", padx=(0, 5), pady=3)
        
        build_chips(self.prefer_container, self.preferred_personality_tags, "green")
        build_chips(self.avoid_container, self.avoided_personality_tags, COLORS['danger_red'])

            # ═══════════════════════════════════════════════
    # SIGNATURE (Props + Hair Rules)
    # ═══════════════════════════════════════════════
    def _add_signature_prop(self):
        self.signature_props.append({'name': 'new_item', 'tags': []})
        self._refresh_signature_props_display()

    def _remove_signature_prop(self, index):
        if 0 <= index < len(self.signature_props):
            self.signature_props.pop(index)
            self._refresh_signature_props_display()

    def _update_prop_name(self, index, new_name):
        if 0 <= index < len(self.signature_props):
            self.signature_props[index]['name'] = new_name.strip()

    def _add_tag_to_prop(self, index):
        if 0 <= index < len(self.signature_props):
            self.signature_props[index]['tags'].append('new_tag')
            self._refresh_signature_props_display()

    def _remove_tag_from_prop(self, prop_index, tag_index):
        if 0 <= prop_index < len(self.signature_props):
            tags = self.signature_props[prop_index]['tags']
            if 0 <= tag_index < len(tags):
                tags.pop(tag_index)
            self._refresh_signature_props_display()

    def _update_prop_tag(self, prop_index, tag_index, new_tag):
        if 0 <= prop_index < len(self.signature_props):
            tags = self.signature_props[prop_index]['tags']
            if 0 <= tag_index < len(tags):
                tags[tag_index] = new_tag.strip()

    def _refresh_signature_props_display(self):
        """Отрисовывает список Signature Props с полями ввода"""
        if self.props_container is None:
            return
        for w in self.props_container.winfo_children():
            w.destroy()
        
        if not self.signature_props:
            ctk.CTkLabel(self.props_container, text="(No signature props — нажмите '➕ Add Prop')",
                         text_color="gray").pack(anchor="w", padx=10, pady=5)
            return
        
        for i, prop in enumerate(self.signature_props):
            prop_frame = ctk.CTkFrame(self.props_container, fg_color="gray25", corner_radius=8)
            prop_frame.pack(fill="x", padx=5, pady=5)
            
            header = ctk.CTkFrame(prop_frame, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(5, 5))
            
            name_wrapper = ctk.CTkFrame(header, fg_color="transparent")
            name_wrapper.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(name_wrapper, text="Prop name",
                         font=ctk.CTkFont(size=11, slant="italic"), text_color="gray60").pack(anchor="w")
            name_entry = ctk.CTkEntry(name_wrapper, placeholder_text="Item name")
            name_entry.pack(fill="x", expand=True)
            name_entry.insert(0, prop['name'])
            name_entry.bind('<KeyRelease>', lambda e, idx=i: self._update_prop_name(idx, name_entry.get()))
            
            ctk.CTkButton(header, text="Delete Prop", width=100, height=28,
                          fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                          font=ctk.CTkFont(size=11),
                          command=lambda idx=i: self._remove_signature_prop(idx)).pack(side="right")
            
            tags_frame = ctk.CTkFrame(prop_frame, fg_color="transparent")
            tags_frame.pack(fill="x", padx=10, pady=(0, 10))
            ctk.CTkLabel(tags_frame, text="Tags:",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
            
            for j, tag in enumerate(prop['tags']):
                tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
                tag_row.pack(fill="x", pady=1)
                tag_entry = ctk.CTkEntry(tag_row, width=200)
                tag_entry.pack(side="left")
                tag_entry.insert(0, tag)
                tag_entry.bind('<KeyRelease>',
                               lambda e, pi=i, ti=j: self._update_prop_tag(pi, ti, tag_entry.get()))
                ctk.CTkButton(tag_row, text="Browse", width=70, height=25,
                              fg_color=COLORS['primary_blue'], hover_color=COLORS['primary_blue_hover'],
                              font=ctk.CTkFont(size=10),
                              command=lambda pi=i: self._open_tags_browser(pi)).pack(side="left", padx=(3, 0))
                ctk.CTkButton(tag_row, text="×", width=30, height=25,
                              fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                              command=lambda pi=i, ti=j: self._remove_tag_from_prop(pi, ti)).pack(side="right", padx=(5, 0))
            
            ctk.CTkButton(tags_frame, text="➕ Add Tag", width=100, height=25,
                          fg_color="gray40", hover_color="gray50",
                          command=lambda idx=i: self._add_tag_to_prop(idx)).pack(anchor="w", pady=(5, 0))

    def _add_hair_rule(self):
        """Добавляет новое условное правило для прически"""
        hair_tags = self._load_tags_from_library("01_character/hair/style.txt")
        default_style = hair_tags[0] if hair_tags else "hair down"
        self.hair_rules_data['conditional'].append({
            'if_action': [], 'style': default_style, 'probability': 0.5
        })
        self._refresh_hair_rules_display()

    def _remove_hair_rule(self, index):
        if 0 <= index < len(self.hair_rules_data['conditional']):
            self.hair_rules_data['conditional'].pop(index)
            self._refresh_hair_rules_display()

    def _update_hair_rule_style(self, index, style):
        if 0 <= index < len(self.hair_rules_data['conditional']):
            self.hair_rules_data['conditional'][index]['style'] = style

    def _update_hair_rule_probability(self, index, prob_str):
        try:
            prob = float(prob_str)
            if 0 <= prob <= 1:
                self.hair_rules_data['conditional'][index]['probability'] = prob
        except ValueError:
            pass

    def _update_hair_rule_actions(self, index, actions_str):
        if 0 <= index < len(self.hair_rules_data['conditional']):
            actions = [a.strip() for a in actions_str.split(',') if a.strip()]
            self.hair_rules_data['conditional'][index]['if_action'] = actions

    def _refresh_hair_rules_display(self):
        """Отрисовывает список условных правил прически"""
        if self.hair_rules_container is None:
            return
        
        if hasattr(self, 'hair_default_btn') and self.hair_default_btn:
            current_default = self.hair_rules_data.get('default', 'hair down')
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " ⭐" if current_default in dna_styles else ""
            self.hair_default_btn.configure(text=f"▼ {current_default}{star}")
        
        for w in self.hair_rules_container.winfo_children():
            w.destroy()
        
        if not self.hair_rules_data['conditional']:
            ctk.CTkLabel(self.hair_rules_container,
                         text="(No conditional rules — нажмите '➕ Add Rule')",
                         text_color="gray").pack(anchor="w", padx=10, pady=5)
            return
        
        for i, rule in enumerate(self.hair_rules_data['conditional']):
            rule_frame = ctk.CTkFrame(self.hair_rules_container, fg_color="gray25", corner_radius=8)
            rule_frame.pack(fill="x", padx=5, pady=5)
            
            header = ctk.CTkFrame(rule_frame, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(5, 5))
            ctk.CTkLabel(header, text=f"Rule #{i + 1}", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkButton(header, text="Delete Hair Rule", width=130, height=28,
                          fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                          font=ctk.CTkFont(size=11),
                          command=lambda idx=i: self._remove_hair_rule(idx)).pack(side="right")
            
            actions_frame = ctk.CTkFrame(rule_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(actions_frame, text="If actions:", width=100, anchor="w").pack(side="left")
            actions_entry = ctk.CTkEntry(actions_frame, placeholder_text="reading, studying, ...")
            actions_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))
            actions_entry.insert(0, ", ".join(rule['if_action']))
            actions_entry.bind('<KeyRelease>',
                               lambda e, idx=i: self._update_hair_rule_actions(idx, actions_entry.get()))
            ctk.CTkButton(actions_frame, text="Browse", width=70, height=25,
                          fg_color=COLORS['primary_blue'], hover_color=COLORS['primary_blue_hover'],
                          font=ctk.CTkFont(size=10),
                          command=lambda idx=i, ae=actions_entry: self._open_actions_browser(idx, ae)).pack(side="right")
            
            style_frame = ctk.CTkFrame(rule_frame, fg_color="transparent")
            style_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(style_frame, text="Style:", width=100, anchor="w").pack(side="left")
            style_text = rule['style'] or "Select..."
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " ⭐" if rule['style'] in dna_styles else ""
            style_btn = ctk.CTkButton(style_frame, text=f"▼ {style_text}{star}", width=200, height=28,
                                      fg_color="gray40", hover_color="gray50",
                                      font=ctk.CTkFont(size=11))
            style_btn.pack(side="left", padx=(5, 10))
            style_btn.configure(command=lambda idx=i, btn=style_btn: self._open_style_selector(idx, btn))
            
            ctk.CTkLabel(style_frame, text="Prob:", width=50, anchor="w").pack(side="left")
            prob_slider = ctk.CTkSlider(style_frame, from_=0, to=1, number_of_steps=20, width=120,
                                        command=lambda val, idx=i: self._update_prob_from_slider(idx, val))
            prob_slider.pack(side="left", padx=(5, 5))
            prob_slider.set(rule['probability'])
            prob_entry = ctk.CTkEntry(style_frame, width=60)
            prob_entry.pack(side="left")
            prob_entry.insert(0, str(rule['probability']))
            prob_entry.bind('<KeyRelease>',
                            lambda e, idx=i, slider=prob_slider: self._update_prob_from_entry(idx, prob_entry.get(), slider))

    def _open_tags_browser(self, prop_index):
        """Открывает popup для выбора тегов из prompt-library/09_props"""
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Browse Tags (Props)")
        popup.geometry("500x600")
        popup.transient(self.winfo_toplevel())
        popup.lift()
        
        if os.name == 'nt':
            try:
                import ctypes
                popup.update_idletasks()
                hwnd = ctypes.windll.user32.GetParent(popup.winfo_id())
                GWL_EXSTYLE = -20
                WS_EX_COMPOSITED = 0x02000000
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_COMPOSITED)
            except Exception:
                pass
        
        popup.update_idletasks()
        popup.update()
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="🧸 Select tags (multiple allowed):",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        props_dir = self.project_root / "prompt-library" / "09_props"
        if not props_dir.exists():
            ctk.CTkLabel(scroll_frame, text=f"⚠️ Папка не найдена: {props_dir}",
                         text_color="red").pack(pady=20)
            ctk.CTkButton(popup, text="Close", fg_color="gray",
                          command=popup.destroy).pack(pady=10)
            return
        
        current_tags = set(self.signature_props[prop_index]['tags'])
        self._popup_selected_tags = set(current_tags)
        
        categories = {}
        for txt_file in sorted(props_dir.rglob("*.txt")):
            parts = txt_file.relative_to(props_dir).parts
            if len(parts) >= 2:
                main_cat, sub_cat = parts[0], parts[1].replace('.txt', '')
            elif len(parts) == 1:
                main_cat, sub_cat = "general", parts[0].replace('.txt', '')
            else:
                continue
            if main_cat not in categories:
                categories[main_cat] = {}
            categories[main_cat][sub_cat] = txt_file
        
        subcat_data = {}
        for main_cat, subcats in sorted(categories.items()):
            cat_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=2)
            cat_container = ctk.CTkFrame(cat_frame, fg_color="transparent")
            cat_container.pack(fill="x")
            cat_container.pack_forget()
            
            ctk.CTkButton(cat_frame, text=f"➤ {main_cat.replace('_', ' ').title()}",
                          anchor="w", fg_color="gray30", hover_color="gray40", height=30,
                          font=ctk.CTkFont(size=13, weight="bold"),
                          command=lambda cc=cat_container: self._toggle_popup_section(cc)
                          ).pack(fill="x")
            
            for sub_cat, file_path in sorted(subcats.items()):
                sub_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
                sub_frame.pack(fill="x", padx=(20, 0), pady=1)
                sub_container = ctk.CTkFrame(sub_frame, fg_color="transparent")
                sub_container.pack(fill="x", padx=(20, 0))
                sub_container.pack_forget()
                
                tag_count = len(self._load_tags_from_file(file_path))
                sub_toggle_btn = ctk.CTkButton(sub_frame,
                                               text=f"▶ 📁 {sub_cat.replace('_', ' ').title()} ({tag_count})",
                                               anchor="w", fg_color="gray25", hover_color="gray35", height=26,
                                               font=ctk.CTkFont(size=12))
                sub_toggle_btn.pack(fill="x")
                
                subcat_key = f"{main_cat}::{sub_cat}"
                subcat_data[subcat_key] = {
                    'toggle_btn': sub_toggle_btn, 'container': sub_container,
                    'file_path': file_path, 'name': sub_cat,
                    'count': tag_count, 'loaded': False
                }
                
                def toggle_subcat(key=subcat_key, btn=sub_toggle_btn,
                                  cont=sub_container, fp=file_path,
                                  name=sub_cat, cnt=tag_count):
                    data = subcat_data[key]
                    if not data['loaded']:
                        for tag in self._load_tags_from_file(fp):
                            var = ctk.BooleanVar(value=(tag in current_tags))
                            ctk.CTkCheckBox(cont, text=tag, variable=var,
                                            command=lambda t=tag, v=var: self._toggle_tag_selection(t, v)
                                            ).pack(anchor="w", padx=10, pady=2)
                        data['loaded'] = True
                    
                    if cont.winfo_ismapped():
                        self._hide_container(cont)
                        btn.configure(text=f"▶ 📁 {name.replace('_', ' ').title()} ({cnt})")
                    else:
                        self._show_container(cont, padx=(20, 0))
                        btn.configure(text=f"▼ 📁 {name.replace('_', ' ').title()} ({cnt})")
                
                sub_toggle_btn.configure(command=toggle_subcat)
        
        def apply():
            new_tags = sorted(list(self._popup_selected_tags))
            self.signature_props[prop_index]['tags'] = new_tags
            self._refresh_signature_props_display()
            popup.destroy()
            self._log(f"✅ Теги обновлены ({len(new_tags)} total)\n")
        
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="✅ Confirm", fg_color=COLORS['success_green'],
                      hover_color=COLORS['success_green_hover'], width=120,
                      command=apply).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="❌ Cancel", fg_color=COLORS['danger_red'],
                      hover_color=COLORS['danger_red_hover'], width=120,
                      command=popup.destroy).pack(side="left", padx=5)
        
        popup.update_idletasks()
        popup.update()

    def _toggle_popup_section(self, container):
        """Разворачивает/сворачивает секцию в popup"""
        if container.winfo_ismapped():
            self._hide_container(container)
        else:
            self._show_container(container, padx=(20, 0))

    def _toggle_tag_selection(self, tag, var):
        if var.get():
            self._popup_selected_tags.add(tag)
        else:
            self._popup_selected_tags.discard(tag)

    def _open_style_selector(self, rule_index, button_widget):
        """Открывает popup выбора стиля прически для conditional rule"""
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Select Hair Style")
        popup.geometry("350x500")
        popup.transient(self.winfo_toplevel())
        popup.lift()
        
        if os.name == 'nt':
            try:
                import ctypes
                popup.update_idletasks()
                hwnd = ctypes.windll.user32.GetParent(popup.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x02000000)
            except Exception:
                pass
        
        popup.update_idletasks()
        popup.update()
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="💇 Select hair style:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = " ⭐" if tag in dna_styles else ""
            ctk.CTkButton(scroll_frame, text=f"{tag}{star}", anchor="w",
                          fg_color="transparent", text_color=("gray10", "gray90"),
                          hover_color=("gray85", "gray30"),
                          command=lambda t=tag: self._select_style(t, rule_index, button_widget, popup)
                          ).pack(fill="x", padx=5, pady=1)
        
        ctk.CTkButton(popup, text="Cancel", fg_color="gray", hover_color="darkgray",
                      command=popup.destroy).pack(pady=10)
        popup.update_idletasks()
        popup.update()

    def _select_style(self, style, rule_index, button_widget, popup):
        self._update_hair_rule_style(rule_index, style)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        star = " ⭐" if style in dna_styles else ""
        button_widget.configure(text=f"▼ {style}{star}")
        popup.destroy()

    def _open_default_style_selector(self):
        """Открывает popup выбора default стиля прически"""
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Select Default Hair Style")
        popup.geometry("350x500")
        popup.transient(self.winfo_toplevel())
        popup.lift()
        
        if os.name == 'nt':
            try:
                import ctypes
                popup.update_idletasks()
                hwnd = ctypes.windll.user32.GetParent(popup.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x02000000)
            except Exception:
                pass
        
        popup.update_idletasks()
        popup.update()
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="💇 Select default hair style:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        for tag in self._load_tags_from_library("01_character/hair/style.txt"):
            star = " ⭐" if tag in dna_styles else ""
            ctk.CTkButton(scroll_frame, text=f"{tag}{star}", anchor="w",
                          fg_color="transparent", text_color=("gray10", "gray90"),
                          hover_color=("gray85", "gray30"),
                          command=lambda t=tag: self._select_default_style(t, popup)
                          ).pack(fill="x", padx=5, pady=1)
        
        ctk.CTkButton(popup, text="Cancel", fg_color="gray", hover_color="darkgray",
                      command=popup.destroy).pack(pady=10)
        popup.update_idletasks()
        popup.update()

    def _select_default_style(self, style, popup):
        self.hair_rules_data['default'] = style
        if self.hair_default_btn:
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " ⭐" if style in dna_styles else ""
            self.hair_default_btn.configure(text=f"▼ {style}{star}")
        popup.destroy()

    def _open_actions_browser(self, rule_index, entry_widget):
        """Открывает popup выбора actions для conditional hair rule"""
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Select Actions")
        popup.geometry("500x600")
        popup.transient(self.winfo_toplevel())
        popup.lift()
        
        if os.name == 'nt':
            try:
                import ctypes
                popup.update_idletasks()
                hwnd = ctypes.windll.user32.GetParent(popup.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x02000000)
            except Exception:
                pass
        
        popup.update_idletasks()
        popup.update()
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="🎬 Select actions:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        actions_dir = self.project_root / "prompt-library" / "04_action"
        if not actions_dir.exists():
            actions_dir = self.project_root / "prompt-library" / "03_pose"
        
        current_actions = set(self.hair_rules_data['conditional'][rule_index]['if_action'])
        self._popup_selected_actions = set(current_actions)
        
        cat_data = {}
        if actions_dir.exists():
            for txt_file in sorted(actions_dir.rglob("*.txt")):
                tag_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                tag_frame.pack(fill="x", pady=2)
                tags_container = ctk.CTkFrame(tag_frame, fg_color="transparent")
                tags_container.pack(fill="x", padx=(20, 0))
                tags_container.pack_forget()
                
                tag_count = len(self._load_tags_from_file(txt_file))
                cat_name = txt_file.stem.replace('_', ' ').title()
                toggle_btn = ctk.CTkButton(tag_frame,
                                           text=f"▶ 📁 {cat_name} ({tag_count})",
                                           anchor="w", fg_color="gray30", hover_color="gray40", height=28,
                                           font=ctk.CTkFont(size=12, weight="bold"))
                toggle_btn.pack(fill="x")
                
                cat_data[txt_file.stem] = {
                    'toggle_btn': toggle_btn, 'container': tags_container,
                    'file_path': txt_file, 'name': cat_name,
                    'count': tag_count, 'loaded': False
                }
                
                def toggle_cat(key=txt_file.stem, btn=toggle_btn,
                               cont=tags_container, fp=txt_file,
                               name=cat_name, cnt=tag_count):
                    data = cat_data[key]
                    if not data['loaded']:
                        for tag in self._load_tags_from_file(fp):
                            var = ctk.BooleanVar(value=(tag in current_actions))
                            ctk.CTkCheckBox(cont, text=tag, variable=var,
                                            command=lambda t=tag, v=var: self._toggle_action_selection(t, v)
                                            ).pack(anchor="w", padx=15, pady=1)
                        data['loaded'] = True
                    
                    if cont.winfo_ismapped():
                        self._hide_container(cont)
                        btn.configure(text=f"▶ 📁 {name} ({cnt})")
                    else:
                        self._show_container(cont, padx=(20, 0))
                        btn.configure(text=f"▼ 📁 {name} ({cnt})")
                
                toggle_btn.configure(command=toggle_cat)
        
        def apply():
            actions_list = sorted(list(self._popup_selected_actions))
            self.hair_rules_data['conditional'][rule_index]['if_action'] = actions_list
            entry_widget.delete(0, "end")
            entry_widget.insert(0, ", ".join(actions_list))
            popup.destroy()
        
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="✅ Confirm", fg_color=COLORS['success_green'],
                      hover_color=COLORS['success_green_hover'],
                      command=apply).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="❌ Cancel", fg_color=COLORS['danger_red'],
                      hover_color=COLORS['danger_red_hover'],
                      command=popup.destroy).pack(side="left", padx=5)
        
        popup.update_idletasks()
        popup.update()

    def _toggle_action_selection(self, tag, var):
        if var.get():
            self._popup_selected_actions.add(tag)
        else:
            self._popup_selected_actions.discard(tag)

    def _update_prob_from_slider(self, rule_index, value):
        rounded_value = round(value, 2)
        self._update_hair_rule_probability(rule_index, str(rounded_value))
        if self.hair_rules_container and 0 <= rule_index < len(self.hair_rules_data['conditional']):
            rule_frames = [w for w in self.hair_rules_container.winfo_children() if isinstance(w, ctk.CTkFrame)]
            if rule_index < len(rule_frames):
                children = rule_frames[rule_index].winfo_children()
                if len(children) >= 3:
                    for w in children[2].winfo_children():
                        if isinstance(w, ctk.CTkEntry):
                            w.delete(0, "end")
                            w.insert(0, str(rounded_value))
                            break

    def _update_prob_from_entry(self, rule_index, value_str, slider_widget):
        try:
            value = float(value_str)
            if 0 <= value <= 1:
                self._update_hair_rule_probability(rule_index, value_str)
                slider_widget.set(value)
        except ValueError:
            pass

    # ═══════════════════════════════════════════════
    # ATMOSPHERE (Lighting + Weather)
    # ═══════════════════════════════════════════════
    def _build_lighting_tree(self):
        if self.lighting_tree_frame is None:
            return
        for w in self.lighting_tree_frame.winfo_children():
            w.destroy()
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

    def _create_lighting_subcategory(self, sub_cat, file_path):
        if self.lighting_tree_frame is None:
            return
        sub_frame = ctk.CTkFrame(self.lighting_tree_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        ctk.CTkButton(sub_frame, text=f"➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                      fg_color="gray30", hover_color="gray40", height=28,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self._toggle_lighting_subcategory(sub_cat)).pack(fill="x")
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        self._wardrobe_sections_expanded_local(f"lighting.{sub_cat}", tags_frame)
        for tag in self._load_tags_from_file(file_path):
            tag_key = f"lighting::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            ctk.CTkLabel(tag_row, text=f"  • {tag.replace('_', ' ')}", anchor="w", width=250).pack(side="left", padx=(5, 0))
            action_btn = ctk.CTkButton(tag_row, text="+", width=30, height=25,
                                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       command=lambda t=tag, tk=tag_key: self._toggle_lighting_tag(t, tk))
            action_btn.pack(side="right", padx=(0, 5))
            self.lighting_tag_ui_elements[tag_key] = {
                'label': tag_row.winfo_children()[0], 'button': action_btn, 'tag': tag
            }

    def _toggle_lighting_subcategory(self, sub_cat):
        key = f"lighting.{sub_cat}"
        section = self._get_section_state(key)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(key, not section['expanded'])

    def _toggle_lighting_tag(self, tag, tag_key):
        if tag_key not in self.lighting_tag_ui_elements:
            return
        ui = self.lighting_tag_ui_elements[tag_key]
        if tag in self.selected_lighting_tags:
            self.selected_lighting_tags.remove(tag)
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        else:
            self.selected_lighting_tags.append(tag)
            ui['label'].configure(text_color="green")
            ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
        self._debounce_ui_update('lighting_chips')

    def _refresh_selected_lighting_display(self):
        if self.selected_lighting_container is None:
            return
        for w in self.selected_lighting_container.winfo_children():
            w.destroy()
        if not self.selected_lighting_tags:
            ctk.CTkLabel(self.selected_lighting_container, text="(No lighting selected)",
                         text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        COLS = 4
        for i, tag in enumerate(self.selected_lighting_tags):
            chip = ctk.CTkFrame(self.selected_lighting_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i // COLS, column=i % COLS, padx=3, pady=3, sticky="ew")
            self.selected_lighting_container.grid_columnconfigure(i % COLS, weight=1)
            ctk.CTkLabel(chip, text=f"  {tag.replace('_', ' ')}  ", font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 5), pady=4)
            ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                          hover_color=COLORS['danger_red'], text_color="white",
                          font=ctk.CTkFont(size=14, weight="bold"),
                          command=lambda t=tag: self._remove_lighting_tag(t)).pack(side="right", padx=(0, 5), pady=2)

    def _remove_lighting_tag(self, tag):
        if tag in self.selected_lighting_tags:
            self.selected_lighting_tags.remove(tag)
        tag_key = f"lighting::{tag}"
        if tag_key in self.lighting_tag_ui_elements:
            ui = self.lighting_tag_ui_elements[tag_key]
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        self._refresh_selected_lighting_display()

    def _build_weather_tree(self):
        if self.weather_tree_frame is None:
            return
        for w in self.weather_tree_frame.winfo_children():
            w.destroy()
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

    def _create_weather_subcategory(self, sub_cat, file_path):
        if self.weather_tree_frame is None:
            return
        sub_frame = ctk.CTkFrame(self.weather_tree_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        ctk.CTkButton(sub_frame, text=f"➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                      fg_color="gray30", hover_color="gray40", height=28,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self._toggle_weather_subcategory(sub_cat)).pack(fill="x")
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        self._wardrobe_sections_expanded_local(f"weather.{sub_cat}", tags_frame)
        for tag in self._load_tags_from_file(file_path):
            tag_key = f"weather::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            ctk.CTkLabel(tag_row, text=f"  • {tag.replace('_', ' ')}", anchor="w", width=250).pack(side="left", padx=(5, 0))
            action_btn = ctk.CTkButton(tag_row, text="+", width=30, height=25,
                                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       command=lambda t=tag, tk=tag_key: self._toggle_weather_tag(t, tk))
            action_btn.pack(side="right", padx=(0, 5))
            self.weather_tag_ui_elements[tag_key] = {
                'label': tag_row.winfo_children()[0], 'button': action_btn, 'tag': tag
            }

    def _toggle_weather_subcategory(self, sub_cat):
        key = f"weather.{sub_cat}"
        section = self._get_section_state(key)
        if not section:
            return
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        self._set_section_state(key, not section['expanded'])

    def _toggle_weather_tag(self, tag, tag_key):
        if tag_key not in self.weather_tag_ui_elements:
            return
        ui = self.weather_tag_ui_elements[tag_key]
        if tag in self.selected_weather_tags:
            self.selected_weather_tags.remove(tag)
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        else:
            self.selected_weather_tags.append(tag)
            ui['label'].configure(text_color="green")
            ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
        self._debounce_ui_update('weather_chips')

    def _refresh_selected_weather_display(self):
        if self.selected_weather_container is None:
            return
        for w in self.selected_weather_container.winfo_children():
            w.destroy()
        if not self.selected_weather_tags:
            ctk.CTkLabel(self.selected_weather_container, text="(No weather selected)",
                         text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        COLS = 4
        for i, tag in enumerate(self.selected_weather_tags):
            chip = ctk.CTkFrame(self.selected_weather_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i // COLS, column=i % COLS, padx=3, pady=3, sticky="ew")
            self.selected_weather_container.grid_columnconfigure(i % COLS, weight=1)
            ctk.CTkLabel(chip, text=f"  {tag.replace('_', ' ')}  ", font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 5), pady=4)
            ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                          hover_color=COLORS['danger_red'], text_color="white",
                          font=ctk.CTkFont(size=14, weight="bold"),
                          command=lambda t=tag: self._remove_weather_tag(t)).pack(side="right", padx=(0, 5), pady=2)

    def _remove_weather_tag(self, tag):
        if tag in self.selected_weather_tags:
            self.selected_weather_tags.remove(tag)
        tag_key = f"weather::{tag}"
        if tag_key in self.weather_tag_ui_elements:
            ui = self.weather_tag_ui_elements[tag_key]
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        self._debounce_ui_update('weather_chips')

    # ═══════════════════════════════════════════════
    # PREVIEW
    # ═══════════════════════════════════════════════
    def _refresh_yaml_preview(self):
        """Обновляет текстовое превью YAML во вкладке Preview"""
        if self.yaml_textbox is None or not self.current_profile_name:
            return
        profile = self._get_default_profile_structure(self.current_profile_name)
        profile['character'] = self.profile_character_data.copy() if self.profile_character_data else {
            'name': self.current_profile_name, 'age': 18, 'archetype': 'custom character'
        }
        selected_traits = [entry['tag'] for entry in self.selected_dna_tags]
        other_text = self.other_traits_text.get("1.0", "end").strip() if self.other_traits_text else ""
        if other_text:
            selected_traits.extend([t.strip() for t in other_text.split(',') if t.strip()])
        profile['fixed_traits'] = selected_traits
        wardrobe_by_subcat = {}
        for entry in self.selected_wardrobe_tags:
            wardrobe_by_subcat.setdefault(entry['subcategory'], []).append(entry['tag'])
        profile['outfit_whitelist'] = {'default': wardrobe_by_subcat}
        profile['expression_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t['category'] == 'Expressions'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t['category'] == 'Expressions']
        }
        profile['pose_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t['category'] == 'Poses'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t['category'] == 'Poses']
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
        header = f"# Character Profile: {self.current_profile_name}\n# Фильтр поверх scene-rules\n"
        self.yaml_textbox.delete("1.0", "end")
        self.yaml_textbox.insert("1.0", header + yaml_str)

    def _apply_yaml_to_editor(self):
        """Применяет изменения из текстового YAML-превью обратно в UI"""
        if self.yaml_textbox is None:
            return
        try:
            profile = yaml.safe_load(self.yaml_textbox.get("1.0", "end").strip())
            if not profile:
                messagebox.showwarning("Warning", "YAML пустой")
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
                if self.editor_title:
                    self.editor_title.configure(text=f"👤 Editing: {new_name}")
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
                self.other_traits_text.delete("1.0", "end")
                if other_traits:
                    self.other_traits_text.insert("1.0", ", ".join(other_traits))
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
            messagebox.showinfo("Success", "YAML применён!")
        except yaml.YAMLError as e:
            messagebox.showerror("YAML Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _copy_yaml_to_clipboard(self):
        if self.yaml_textbox is None:
            return
        content = self.yaml_textbox.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Info", "YAML пуст")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ YAML скопирован!")

    # ═══════════════════════════════════════════════
    # LOAD / SAVE профиля
    # ═══════════════════════════════════════════════
    def _load_profile_to_editor(self, profile_name: str):
        """Загружает профиль в редактор с отложенной загрузкой для плавности UI"""
        if self.other_traits_text is None:
            return
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            messagebox.showerror("Error", f"Profile not found: {profile_name}")
            return
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        # === БЫСТРАЯ ЗАГРУЗКА: DNA ===
        self.selected_dna_tags = []
        fixed_traits = profile.get('fixed_traits', [])
        all_dna_tags = {ui['tag']: ui['category'] for ui in self.dna_tag_ui_elements.values()}
        other_traits = []
        for trait in fixed_traits:
            if trait in all_dna_tags:
                self.selected_dna_tags.append({'tag': trait, 'category': all_dna_tags[trait]})
            else:
                other_traits.append(trait)
        self.other_traits_text.delete("1.0", "end")
        if other_traits:
            self.other_traits_text.insert("1.0", ", ".join(other_traits))
        # === БЫСТРАЯ ЗАГРУЗКА: Wardrobe ===
        self.selected_wardrobe_tags = []
        outfit_whitelist = profile.get('outfit_whitelist', {})
        for outfit_name, subcats in outfit_whitelist.items():
            if isinstance(subcats, dict):
                for subcategory, tags in subcats.items():
                    if isinstance(tags, list):
                        for tag in tags:
                            self.selected_wardrobe_tags.append({'tag': tag, 'subcategory': subcategory})
        # === БЫСТРАЯ ЗАГРУЗКА: Personality ===
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
        # === БЫСТРАЯ ЗАГРУЗКА: Signature ===
        self.signature_props = profile.get('signature_props', [])
        hair_rules = profile.get('hair_rules', {})
        self.hair_rules_data = {
            'default': hair_rules.get('default', 'hair down'),
            'conditional': hair_rules.get('conditional', [])
        }
        # === БЫСТРАЯ ЗАГРУЗКА: Atmosphere ===
        atmosphere = profile.get('atmosphere_preferences', {})
        self.selected_lighting_tags = atmosphere.get('lighting', [])
        self.selected_weather_tags = atmosphere.get('weather', [])
        self.current_profile_name = profile_name
        # 👇 ОТЛОЖЕННАЯ ЗАГРУЗКА: Обновляем UI по частям (batch_load_ui)
        ui_update_tasks = [
            lambda: self._sync_dna_tag_ui_states(),
            lambda: self._refresh_selected_dna_tags_display(),
            lambda: self._sync_tag_ui_states(),
            lambda: self._refresh_selected_tags_display(),
            lambda: self._sync_personality_ui_states(),
            lambda: self._refresh_personality_tags_display(),
            lambda: self._refresh_signature_props_display(),
            lambda: self._refresh_hair_rules_display(),
            lambda: self._sync_lighting_ui_states(),
            lambda: self._refresh_selected_lighting_display(),
            lambda: self._sync_weather_ui_states(),
            lambda: self._refresh_selected_weather_display(),
            lambda: self._refresh_yaml_preview()
        ]
        self._batch_load_ui(ui_update_tasks, delay_ms=1)
        self._log(f"📥 Загружен профиль: {profile_name}\n")

    def _save_profile(self):
        """Сохраняет текущее состояние редактора в YAML-файл"""
        if not self.current_profile_name:
            messagebox.showwarning("Warning", "No profile selected")
            return
        if self.other_traits_text is None:
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
            self.profile_character_data = {'name': self.current_profile_name, 'age': 18, 'archetype': 'custom character'}
        profile['character'] = self.profile_character_data.copy()
        selected_traits = [entry['tag'] for entry in self.selected_dna_tags]
        other_text = self.other_traits_text.get("1.0", "end").strip()
        if other_text:
            selected_traits.extend([t.strip() for t in other_text.split(',') if t.strip()])
        profile['fixed_traits'] = selected_traits
        wardrobe_by_subcat = {}
        for entry in self.selected_wardrobe_tags:
            wardrobe_by_subcat.setdefault(entry['subcategory'], []).append(entry['tag'])
        profile['outfit_whitelist'] = {'default': wardrobe_by_subcat}
        profile['expression_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t['category'] == 'Expressions'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t['category'] == 'Expressions']
        }
        profile['pose_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t['category'] == 'Poses'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t['category'] == 'Poses']
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
            f.write("# Фильтр поверх scene-rules\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._log(f"💾 Профиль '{self.current_profile_name}' сохранён\n")
        messagebox.showinfo("Success", f"Profile '{self.current_profile_name}' saved!")

    # ═══════════════════════════════════════════════
    # UTILS: Утилиты библиотеки тегов и debouncing
    # ═══════════════════════════════════════════════
    def _load_tags_from_library(self, relative_path: str) -> list:
        """Загружает список тегов из файла библиотеки тегов (с кэшированием)"""
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

    def _load_tags_from_file(self, file_path) -> list:
        """Загружает теги из конкретного файла (с кэшированием)"""
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

    def _debounce_ui_update(self, update_type: str, delay_ms: int = 150):
        """Откладывает обновление UI на delay_ms миллисекунд (борьба с фризами)"""
        self._pending_ui_updates.add(update_type)
        if self._ui_update_timer:
            self.after_cancel(self._ui_update_timer)
        self._ui_update_timer = self.after(delay_ms, self._process_pending_ui_updates)

    def _process_pending_ui_updates(self):
        """Обрабатывает все отложенные обновления UI (chips)"""
        updates = self._pending_ui_updates.copy()
        self._pending_ui_updates.clear()
        self._ui_update_timer = None
        if 'dna_chips' in updates:
            self._refresh_selected_dna_tags_display()
        if 'wardrobe_chips' in updates:
            self._refresh_selected_tags_display()
        if 'personality_chips' in updates:
            self._refresh_personality_tags_display()
        if 'lighting_chips' in updates:
            self._refresh_selected_lighting_display()
        if 'weather_chips' in updates:
            self._refresh_selected_weather_display()
        if 'yaml_preview' in updates:
            self._refresh_yaml_preview()
        if 'hair_rules' in updates:
            self._refresh_hair_rules_display()

    def _hide_container(self, container):
        """Безопасно скрывает контейнер"""
        if container is None or not container.winfo_ismapped():
            return
        container.pack_forget()
        try:
            parent = container.master
            if parent and parent.winfo_exists():
                parent.update_idletasks()
        except Exception:
            pass

    def _show_container(self, container, padx=(30, 0)):
        """Показывает скрытый контейнер"""
        if container is None or container.winfo_ismapped():
            return
        container.pack(fill="x", padx=padx)
        try:
            container.update_idletasks()
            parent = container.master
            if parent and parent.winfo_exists():
                parent.update_idletasks()
        except Exception:
            pass

    def _batch_load_ui(self, tasks: list, delay_ms: int = 1):
        """
        Выполняет список задач с задержкой между ними для плавной загрузки UI.
        Предотвращает фризы при загрузке больших профилей.
        """
        if not tasks:
            return
        task = tasks[0]
        try:
            task()
        except Exception as e:
            self._log(f"❌ Ошибка при загрузке UI: {e}\n")
        if len(tasks) > 1:
            self.after(delay_ms, lambda: self._batch_load_ui(tasks[1:], delay_ms))