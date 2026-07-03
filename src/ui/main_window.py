import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
from pathlib import Path
import threading

sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter
from coverage_tracker import CoverageTracker

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLORS = {
    'primary_blue': '#3b82f6',
    'primary_blue_hover': '#2563eb',
    'success_green': 'green',
    'success_green_hover': 'darkgreen',
    'danger_red': '#dc2626',
    'danger_red_hover': '#991b1b',
    'border_color': 'gray50',
}


class MainWindow(ctk.CTk):

    # ════════════════════════════════════════════════════════════════════════════
    # 1. ИНИЦИАЛИЗАЦИЯ
    # ════════════════════════════════════════════════════════════════════════════
    
    def __init__(self):
        super().__init__()

        # 👇 ФИКС "ЖЕЛЕ": Включаем двойную буферизацию для всего окна (Windows)
        if os.name == 'nt':
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                GWL_EXSTYLE = -20
                WS_EX_COMPOSITED = 0x02000000
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_COMPOSITED)
            except Exception:
                pass  # Тихо пропускаем, если не сработало

        self.title("Dataset Composer v1.1 - Character LoRA Pipeline")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.project_root = Path(__file__).parent.parent.parent
        self.output_directory = r"D:\VASILY\MY GENERATION\Test Generations"
        self.profiles_directory = self.project_root / "character-profiles"
        self.profiles_directory.mkdir(exist_ok=True)

        self.current_profile_name: str | None = None
        self.profile_character_data: dict = {}
        
        self.selected_dna_tags: list[dict] = []
        self.dna_tag_ui_elements: dict[str, dict] = {}
        
        self.selected_wardrobe_tags: list[dict] = []
        self.tag_ui_elements: dict[str, dict] = {}
        self.wardrobe_sections_expanded: dict[str, dict] = {}
        
        self.preferred_personality_tags: list[dict] = []
        self.avoided_personality_tags: list[dict] = []
        self.personality_tag_ui_elements: dict[str, dict] = {}
        self.personality_sections_expanded: dict[str, dict] = {}
        
        self.signature_props: list[dict] = []
        self.hair_rules_data: dict = {'default': '', 'conditional': []}
        
        self.selected_lighting_tags: list[str] = []
        self.selected_weather_tags: list[str] = []
        self.lighting_tag_ui_elements: dict[str, dict] = {}
        self.weather_tag_ui_elements: dict[str, dict] = {}
        self.atmosphere_sections_expanded: dict[str, dict] = {}
        
        # UI
        self.profiles_listbox: ctk.CTkScrollableFrame | None = None
        self.editor_title: ctk.CTkLabel | None = None
        self.edit_name_btn: ctk.CTkButton | None = None
        self.editor_tabview: ctk.CTkTabview | None = None
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

        # Scene Rules UI
        self.scene_rules_scroll: ctk.CTkScrollableFrame | None = None
        self.scene_rules_list_frame: ctk.CTkScrollableFrame | None = None
        self.scene_rules_editor_frame: ctk.CTkFrame | None = None
        self.auto_sync_var: ctk.BooleanVar | None = None
        
        # Scene Rules данные
        self.scene_rules_data: dict = {}  # Загруженные данные из TOML
        self.current_rule_file: Path | None = None  # Текущий редактируемый файл

        # Library UI
        self.library_tree: ctk.CTkScrollableFrame | None = None
        self.library_editor_frame: ctk.CTkFrame | None = None
        self.library_tags_container: ctk.CTkScrollableFrame | None = None
        self.library_search_entry: ctk.CTkEntry | None = None
        self.library_current_file: Path | None = None
        self.library_tags: list[str] = []

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Profiles")
        self.tabview.add("Library")
        self.tabview.add("Generate")
        self.tabview.add("Analyzer")
        self.tabview.add("Settings")       

        self._tags_cache = {}

        # Debouncing для update_idletasks (борьба с "плаванием" окна)
        self._update_timer = None
        
        # Debouncing для поиска в Scene Rules
        self._search_timer = None

        # Debouncing для UI обновлений
        self._ui_update_timer = None
        self._pending_ui_updates = set()

        # Создаём только Profiles и Generate сразу (они нужны чаще всего)
        self._create_profiles_tab()
        self._create_generate_tab()
        self._create_library_tab()
        self._create_analyzer_tab()
        self._create_settings_tab()
        
        # Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_placeholder(self, tab, text):
        label = ctk.CTkLabel(tab, text=text, font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(expand=True)

    # ════════════════════════════════════════════════════════════════════════════
    # 2. СОЗДАНИЕ ВКЛАДОК (UI)
    # ════════════════════════════════════════════════════════════════════════════
    
    def _create_profiles_tab(self):
        tab = self.tabview.tab("Profiles")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=3)
        tab.grid_rowconfigure(0, weight=1)
        
        # === ЛЕВАЯ ПАНЕЛЬ ===
        left_frame = ctk.CTkFrame(tab)
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
        
        # === ПРАВАЯ ПАНЕЛЬ ===
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        title_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        title_frame.grid_columnconfigure(1, weight=1)
        
        self.editor_title = ctk.CTkLabel(title_frame, text="👤 Editing: (no selection)",
                                          font=ctk.CTkFont(size=18, weight="bold"))
        self.editor_title.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # 👇 ПОЛИРОВКА: Карандаш для переименования
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
        
        self.editor_tabview = ctk.CTkTabview(right_frame)
        self.editor_tabview.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        self.editor_tabview.add("🧬 DNA")
        self.editor_tabview.add("👗 Outfits")
        self.editor_tabview.add("🎭 Personality")
        self.editor_tabview.add("✨ Signature")
        self.editor_tabview.add("🌍 Atmosphere")
        self.editor_tabview.add("✍️ Custom")
        self.editor_tabview.add("📄 Preview")
        
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
        
        # === DNA ===
        dna_frame = ctk.CTkFrame(self.dna_scroll)
        dna_frame.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(dna_frame, text="🧬 Character DNA",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.dna_tree_frame = ctk.CTkFrame(dna_frame, fg_color="transparent")
        # 👇 ПОЛИРОВКА: Растянуть до границ
        self.dna_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self._build_dna_tree()
        
        selected_dna_frame = ctk.CTkFrame(dna_frame)
        # 👇 ПОЛИРОВКА: Растянуть вниз (expand=True + pady как в Outfits)
        selected_dna_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        
        ctk.CTkLabel(selected_dna_frame, text="✅ Selected DNA Tags:",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_dna_tags_container = ctk.CTkScrollableFrame(
            selected_dna_frame, fg_color="transparent"
        )
        self.selected_dna_tags_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._refresh_selected_dna_tags_display()
        
        # === Custom ===
        custom_frame = ctk.CTkFrame(self.custom_scroll)
        custom_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(custom_frame, text="✍️ Custom Traits (Advanced)",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        description_frame = ctk.CTkFrame(custom_frame, fg_color="gray20", corner_radius=10)
        description_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(description_frame, 
                      text="⚙️ Для продвинутых пользователей\n\n"
                           "Эта вкладка позволяет добавить произвольные теги.\n\n"
                           "💡 Примеры:\n"
                           "• Составные описания: 'long straight light blue hair'\n"
                           "• Редкие теги: 'freckles', 'beauty mark'\n"
                           "• Модификаторы: 'cinematic lighting'",
                      text_color="gray80", justify="left", wraplength=600).pack(anchor="w", padx=15, pady=15)
        
        ctk.CTkLabel(custom_frame, text="   Введите теги через запятую:",
                      text_color="gray").pack(anchor="w", padx=20, pady=(5, 5))
        
        self.other_traits_text = ctk.CTkTextbox(custom_frame, height=150)
        self.other_traits_text.pack(fill="x", padx=20, pady=(0, 10))
        
        # === Outfits ===
        wardrobe_frame = ctk.CTkFrame(self.outfits_scroll)
        wardrobe_frame.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(wardrobe_frame, text="👗 Wardrobe (Whitelist)",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.wardrobe_tree_frame = ctk.CTkFrame(wardrobe_frame, fg_color="transparent")
        # 👇 ПОЛИРОВКА: Растянуть до границ
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
        
        # === Personality ===
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
        
        # === Signature ===
        signature_frame = ctk.CTkFrame(self.signature_scroll)
        signature_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(signature_frame, text="✨ Signature Items & Hair Rules",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        props_section = ctk.CTkFrame(signature_frame)
        props_section.pack(fill="x", padx=10, pady=10)
        
        props_header = ctk.CTkFrame(props_section, fg_color="transparent")
        props_header.pack(fill="x", padx=10, pady=(5, 5))
        props_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(props_header, text="🧸 Signature Props",
                      font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="w")
        
        # 👇 ПОЛИРОВКА: Add Prop справа, но растянутый
        ctk.CTkButton(props_header, text="➕ Add Prop", height=28,
                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                       command=self._add_signature_prop).grid(row=0, column=1, sticky="e")
        
        self.props_container = ctk.CTkFrame(props_section, fg_color="transparent")
        self.props_container.pack(fill="x", padx=10, pady=(0, 10))
        
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
        
        # 👇 ПОЛИРОВКА: Add Rule справа, растянутый
        ctk.CTkButton(cond_header, text="➕ Add Rule", height=28,
                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                       command=self._add_hair_rule).grid(row=0, column=1, sticky="e")
        
        self.hair_rules_container = ctk.CTkFrame(hair_section, fg_color="transparent")
        self.hair_rules_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_signature_props_display()
        self._refresh_hair_rules_display()
        
        # === Atmosphere ===
        atmosphere_frame = ctk.CTkFrame(self.atmosphere_scroll)
        atmosphere_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(atmosphere_frame, text="🌍 Atmosphere Preferences",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
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
        
        # === Preview ===
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
        
        self._refresh_profiles_list()

    def _create_library_tab(self):
        """Создает вкладку редактирования библиотеки тегов и scene-rules"""
        tab = self.tabview.tab("Library")
        
        # Создаём субвкладки
        library_tabview = ctk.CTkTabview(tab)
        library_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        library_tabview.add("📚 Tag Editor")
        library_tabview.add("🎬 Scene Rules")
        
        # === СУБВКЛАДКА 1: Tag Editor ===
        tag_editor_tab = library_tabview.tab("📚 Tag Editor")
        self._create_tag_editor_content(tag_editor_tab)
        
        # === СУБВКЛАДКА 2: Scene Rules ===
        scene_rules_tab = library_tabview.tab("🎬 Scene Rules")
        self._create_scene_rules_content(scene_rules_tab)
    
    def _create_tag_editor_content(self, tab):
        """Создает содержимое вкладки Tag Editor (переносим старый код сюда)"""
        # Двухколоночный layout
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)
        
        # === ЛЕВАЯ ПАНЕЛЬ: Дерево файлов ===
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(left_frame, text="📚 Prompt Library",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        self.library_tree = ctk.CTkScrollableFrame(left_frame)
        self.library_tree.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        self._build_library_tree()
        
        # === ПРАВАЯ ПАНЕЛЬ: Редактор тегов ===
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(2, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self.library_editor_title = ctk.CTkLabel(right_frame, text="📝 Tag Editor (select a file)",
                                                   font=ctk.CTkFont(size=18, weight="bold"))
        self.library_editor_title.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        # Поиск
        search_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.library_search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search tags...")
        self.library_search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.library_search_entry.bind('<KeyRelease>', lambda e: self._filter_library_tags())
        
        clear_search_btn = ctk.CTkButton(search_frame, text="Clear", width=60,
                                          command=self._clear_library_search)
        clear_search_btn.grid(row=0, column=1)
        
        # Контейнер для тегов
        self.library_tags_container = ctk.CTkScrollableFrame(right_frame)
        self.library_tags_container.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        # Панель добавления тега
        add_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        add_frame.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        add_frame.grid_columnconfigure(0, weight=1)
        
        self.new_tag_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter new tag...")
        self.new_tag_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.new_tag_entry.bind('<Return>', lambda e: self._add_library_tag())
        
        add_tag_btn = ctk.CTkButton(add_frame, text="➕ Add Tag", width=100,
                                     fg_color="green", hover_color="darkgreen",
                                     command=self._add_library_tag)
        add_tag_btn.grid(row=0, column=1)
        
        self.library_editor_frame = right_frame
    
    def _create_scene_rules_content(self, tab):
        """Создает содержимое вкладки Scene Rules"""
        # === ВЕРХНЯЯ ПАНЕЛЬ: Переключатель автосинхронизации + кнопки ===
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Переключатель автосинхронизации
        sync_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        sync_frame.pack(side="left", padx=(10, 5))
        
        self.auto_sync_var = ctk.BooleanVar(value=True)
        sync_switch = ctk.CTkSwitch(sync_frame, text="Auto-sync", variable=self.auto_sync_var,
                                     command=self._on_auto_sync_toggled)
        sync_switch.pack(side="left", padx=(0, 5))
        
        # Кнопка с вопросом (тултип)
        help_btn = ctk.CTkButton(sync_frame, text="?", width=25, height=25,
                                  fg_color="gray40", hover_color="gray50",
                                  font=ctk.CTkFont(size=12, weight="bold"),
                                  corner_radius=12,
                                  command=self._show_auto_sync_help)
        help_btn.pack(side="left")
        
        # Кнопки справа
        reload_btn = ctk.CTkButton(top_frame, text="🔄 Reload", width=100,
                                    fg_color="gray40", hover_color="gray50",
                                    command=self._reload_scene_rules)
        reload_btn.pack(side="right", padx=(5, 10))
        
        save_btn = ctk.CTkButton(top_frame, text="💾 Save All", width=100,
                                  fg_color="green", hover_color="darkgreen",
                                  command=self._save_scene_rules)
        save_btn.pack(side="right", padx=(5, 0))
        
        # === ОСНОВНОЙ КОНТЕНТ: Двухколоночный layout ===
        content_frame = ctk.CTkFrame(tab)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Левая панель: список правил (обёртка с фиксированной шириной)
        left_wrapper = ctk.CTkFrame(content_frame, width=280)
        left_wrapper.grid(row=0, column=0, padx=(5, 2), pady=5, sticky="nsew")
        left_wrapper.grid_propagate(False)
        left_wrapper.grid_rowconfigure(0, weight=1)
        left_wrapper.grid_columnconfigure(0, weight=1)
        
        self.scene_rules_list_frame = ctk.CTkScrollableFrame(left_wrapper)
        self.scene_rules_list_frame.grid(row=0, column=0, sticky="nsew")
        
        # Правая панель: редактор
        self.scene_rules_editor_frame = ctk.CTkFrame(content_frame)
        self.scene_rules_editor_frame.grid(row=0, column=1, padx=(2, 5), pady=5, sticky="nsew")
        
        # Заглушка редактора
        placeholder = ctk.CTkLabel(self.scene_rules_editor_frame,
                                    text="👈 Выберите правило слева для редактирования",
                                    font=ctk.CTkFont(size=14),
                                    text_color="gray")
        placeholder.pack(expand=True)
        
        # Загружаем данные
        self._load_scene_rules()
        self._build_scene_rules_list()

    def _show_auto_sync_help(self):
        """Показывает справку о функции автосинхронизации"""
        help_text = """🔄 Автосинхронизация связей

Когда ВКЛЮЧЕНА:
• Если вы добавляете действие 'reading' в список предпочтений локации 'library'
• Программа автоматически добавит 'library' в список предпочтений действия 'reading'
• Это обеспечивает консистентность данных

Когда ВЫКЛЮЧЕНА:
• Вы полностью контролируете все связи вручную
• Изменения в одном файле не влияют на другие
• Полезно для тонкой настройки или исправления ошибок

Рекомендация:
Оставьте включенной для большинства случаев. Отключайте только если нужно создать асимметричные связи."""
        
        messagebox.showinfo("Auto-sync Help", help_text)
    
    def _on_auto_sync_toggled(self):
        """Обработчик переключения автосинхронизации"""
        if self.auto_sync_var is None:
            return
        if self.auto_sync_var.get():
            self._log("🔄 Автосинхронизация ВКЛЮЧЕНА\n")
        else:
            self._log("🔒 Автосинхронизация ВЫКЛЮЧЕНА (ручной режим)\n")

    # ════════════════════════════════════════════════════════════════════════════
    # LIBRARY: Scene Rules Editor
    # ════════════════════════════════════════════════════════════════════════════
    
    def _load_scene_rules(self):
        """Загружает все TOML-файлы из папки scene-rules"""
        self.scene_rules_data = {}
        
        rules_dir = self.project_root / "scene-rules"
        if not rules_dir.exists():
            self._log(f"⚠️ Папка scene-rules не найдена: {rules_dir}\n")
            return
        
        # Сканируем все подпапки: locations, actions, location_types, weather, camera
        for category_dir in sorted(rules_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            
            category_name = category_dir.name
            self.scene_rules_data[category_name] = {}
            
            for toml_file in sorted(category_dir.glob("*.toml")):
                try:
                    import tomli
                    with open(toml_file, 'rb') as f:
                        data = tomli.load(f)
                    self.scene_rules_data[category_name][toml_file.stem] = {
                        'path': toml_file,
                        'data': data
                    }
                except ImportError:
                    # tomli не установлен, пробуем tomllib (Python 3.11+)
                    try:
                        import tomllib
                        with open(toml_file, 'rb') as f:
                            data = tomllib.load(f)
                        self.scene_rules_data[category_name][toml_file.stem] = {
                            'path': toml_file,
                            'data': data
                        }
                    except Exception as e:
                        self._log(f"❌ Ошибка чтения {toml_file.name}: {e}\n")
                except Exception as e:
                    self._log(f"❌ Ошибка чтения {toml_file.name}: {e}\n")
        
        # Подсчёт
        total_files = sum(len(v) for v in self.scene_rules_data.values())
        self._log(f"✅ Загружено {total_files} scene-rules файлов\n")
    
    def _build_scene_rules_list(self):
        """Строит список правил в левой панели с кнопками добавления"""
        if self.scene_rules_list_frame is None:
            return
        
        # Очищаем список
        for w in self.scene_rules_list_frame.winfo_children():
            w.destroy()
        
        if not self.scene_rules_data:
            ctk.CTkLabel(self.scene_rules_list_frame,
                         text="(No rules loaded)",
                         text_color="gray").pack(pady=10)
            return
        
        # Создаём категории
        for category_name, rules in sorted(self.scene_rules_data.items()):
            cat_frame = ctk.CTkFrame(self.scene_rules_list_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=2)
            
            # Заголовок категории с кнопкой добавления
            header_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
            header_frame.pack(fill="x")
            
            cat_container = ctk.CTkFrame(cat_frame, fg_color="transparent")
            cat_container.pack(fill="x")
            cat_container.pack_forget()
            
            ctk.CTkButton(
                header_frame,
                text=f"➤ {category_name.replace('_', ' ').title()} ({len(rules)})",
                anchor="w", fg_color="gray30", hover_color="gray40", height=30,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda cc=cat_container: self._toggle_scene_rules_section(cc)
            ).pack(side="left", fill="x", expand=True)
            
            # Кнопка добавления нового правила
            add_btn = ctk.CTkButton(
                header_frame,
                text="+",
                width=30, height=30,
                fg_color=COLORS['success_green'],
                hover_color=COLORS['success_green_hover'],
                font=ctk.CTkFont(size=16, weight="bold"),
                command=lambda cat=category_name: self._create_new_rule(cat)
            )
            add_btn.pack(side="right", padx=(5, 0))
            
            for rule_name in sorted(rules.keys()):
                rule_btn = ctk.CTkButton(
                    cat_container,
                    text=f"📄 {rule_name}",
                    anchor="w", fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray85", "gray30"),
                    command=lambda c=category_name, r=rule_name: self._select_scene_rule(c, r)
                )
                rule_btn.pack(fill="x", padx=(20, 0), pady=1)
    
    def _create_new_rule(self, category: str):
        """Создает новое правило в указанной категории"""
        # Генерируем имя для нового правила
        new_name = f"new_{category.lower().replace(' ', '_')}_rule"
        
        # Проверяем, что такого правила ещё нет
        if new_name in self.scene_rules_data.get(category, {}):
            # Если есть, добавляем номер
            counter = 1
            while f"{new_name}_{counter}" in self.scene_rules_data.get(category, {}):
                counter += 1
            new_name = f"{new_name}_{counter}"
        
        # Создаём путь к новому файлу
        rules_dir = self.project_root / "scene-rules" / category
        rules_dir.mkdir(parents=True, exist_ok=True)
        new_file_path = rules_dir / f"{new_name}.toml"
        
        # Создаём базовую структуру TOML
        new_data = {
            'meta': {
                'id': new_name,
                'display_name': new_name.replace('_', ' ').title(),
            },
            'soft_constraints': {},
            'hard_constraints': {}
        }
        
        # Для locations добавляем type
        if category == 'locations':
            new_data['meta']['type'] = 'indoor_private'
        
        # Записываем в файл
        try:
            import tomli_w
            with open(new_file_path, 'wb') as f:
                tomli_w.dump(new_data, f)
            
            # Перезагружаем данные
            self._load_scene_rules()
            self._build_scene_rules_list()
            
            # Автоматически открываем новое правило
            self._select_scene_rule(category, new_name)
            
            self._log(f"➕ Создано новое правило: {category}/{new_name}\n")
            messagebox.showinfo("Success", f"New rule '{new_name}' created!")
            
        except ImportError:
            # Если tomli_w не установлен, пишем вручную
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write("[meta]\n")
                f.write(f'id = "{new_name}"\n')
                f.write(f'display_name = "{new_name.replace("_", " ").title()}"\n')
                if category == 'locations':
                    f.write('type = "indoor_private"\n')
                f.write("\n[soft_constraints]\n\n[hard_constraints]\n")
            
            self._load_scene_rules()
            self._build_scene_rules_list()
            self._select_scene_rule(category, new_name)
            
            self._log(f"➕ Создано новое правило: {category}/{new_name}\n")
            messagebox.showinfo("Success", f"New rule '{new_name}' created!")
            
        except Exception as e:
            self._log(f"❌ Ошибка создания правила: {e}\n")
            messagebox.showerror("Error", f"Failed to create rule: {e}")
    
    def _toggle_scene_rules_section(self, container):
        """Разворачивает/сворачивает категорию в списке"""
        if container.winfo_ismapped():
            self._hide_container(container)
        else:
            container.pack(fill="x", padx=(20, 0))
    
    def _select_scene_rule(self, category: str, rule_name: str):
        """Обработчик выбора правила из списка — отображает редактор справа с индикатором загрузки"""
        if self.scene_rules_editor_frame is None:
            return
        
        # Очищаем правую панель
        for w in self.scene_rules_editor_frame.winfo_children():
            w.destroy()
        
        # Получаем данные правила
        rule_data = self.scene_rules_data[category][rule_name]
        self.current_rule_file = rule_data['path']
        data = rule_data['data']
        meta = data.get('meta', {})
        
        self._log(f"📄 Редактирование: {category}/{rule_name}\n")
        
        # === Заголовок (отображаем сразу — это быстро) ===
        header_frame = ctk.CTkFrame(self.scene_rules_editor_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(header_frame, 
                      text=f"📝 {meta.get('display_name', rule_name)}",
                      font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        ctk.CTkLabel(header_frame,
                      text=f"({category}/{rule_name}.toml)",
                      text_color="gray60").pack(side="left", padx=(10, 0))
        
        # 👇 ИНДИКАТОР ЗАГРУЗКИ (показываем сразу)
        loading_frame = ctk.CTkFrame(self.scene_rules_editor_frame, fg_color="transparent")
        loading_frame.pack(fill="both", expand=True, padx=10, pady=50)
        
        ctk.CTkLabel(loading_frame, 
                      text="⏳ Загрузка...",
                      font=ctk.CTkFont(size=16),
                      text_color="gray60").pack(expand=True)
        
        # Принудительная перерисовка, чтобы индикатор отобразился ДО рендеринга
        self.scene_rules_editor_frame.update_idletasks()
        
        # 👇 ОТЛОЖЕННЫЙ РЕНДЕРИНГ: даём UI шанс отрисовать индикатор
        self.after(10, lambda: self._render_scene_rule_content(category, rule_name, rule_data, data, meta, loading_frame))
    
    def _render_scene_rule_content(self, category, rule_name, rule_data, data, meta, loading_frame):
        """Отложенный рендеринг содержимого Scene Rule"""
        # Убираем индикатор загрузки
        if loading_frame and loading_frame.winfo_exists():
            loading_frame.destroy()
        
        # === Скроллируемая область для секций ===
        scroll_frame = ctk.CTkScrollableFrame(self.scene_rules_editor_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # === Секция Meta ===
        self._render_meta_section(scroll_frame, meta, category)
        
        # === Секции в зависимости от категории ===
        if category == 'locations':
            self._render_location_editor(scroll_frame, data)
        elif category == 'actions':
            self._render_action_editor(scroll_frame, data)
        elif category == 'location_types':
            self._render_location_type_editor(scroll_frame, data)
        elif category == 'weather':
            self._render_weather_editor(scroll_frame, data)
        elif category == 'camera':
            self._render_camera_editor(scroll_frame, data)
        
        # Финальная перерисовка
        if self.scene_rules_editor_frame is not None:
            self.scene_rules_editor_frame.update_idletasks()

    def _render_meta_section(self, parent, meta: dict, category: str):
        """Рендерит секцию meta-информации (редактируемую)"""
        meta_frame = ctk.CTkFrame(parent)
        meta_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(meta_frame, text="🏷️ Meta Information",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 5))
        
        # ID (редактируемый)
        id_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
        id_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(id_row, text="ID:", width=120, anchor="w").pack(side="left")
        id_entry = ctk.CTkEntry(id_row, width=300)
        id_entry.pack(side="left")
        id_entry.insert(0, meta.get('id', ''))
        id_entry.bind('<FocusOut>', lambda e: self._save_meta_changes('id', id_entry.get()))
        
        # Display Name (редактируемый)
        name_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(name_row, text="Display Name:", width=120, anchor="w").pack(side="left")
        name_entry = ctk.CTkEntry(name_row, width=300)
        name_entry.pack(side="left")
        name_entry.insert(0, meta.get('display_name', ''))
        name_entry.bind('<FocusOut>', lambda e: self._save_meta_changes('display_name', name_entry.get()))
        
        # Type (только для locations)
        if category == 'locations':
            type_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
            type_row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(type_row, text="Location Type:", width=120, anchor="w").pack(side="left")
            types = sorted(self.scene_rules_data.get('location_types', {}).keys())
            type_combo = ctk.CTkComboBox(type_row, values=types, width=300)
            type_combo.pack(side="left")
            current_type = meta.get('type', '')
            if current_type in types:
                type_combo.set(current_type)
            type_combo.configure(command=lambda val: self._save_meta_changes('type', val))

    def _save_meta_changes(self, field: str, new_value: str):
        """Сохраняет изменения ID/Display Name/Type в TOML файл"""
        if self.current_rule_file is None or not self.current_rule_file.exists():
            return
        
        new_value = new_value.strip()
        if not new_value:
            return
        
        # Определяем текущую категорию и имя правила
        try:
            rel_path = self.current_rule_file.relative_to(self.project_root / "scene-rules")
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
            # Fallback: ручная запись (упрощенная)
            self._write_toml_manually(self.current_rule_file, rule_data)
        
        # Если изменился ID — переименовываем файл
        if field == 'id' and new_value != rule_name:
            # Проверяем, что новое имя валидно
            safe_name = new_value.replace(' ', '_').lower()
            new_file_path = self.current_rule_file.parent / f"{safe_name}.toml"
            
            if new_file_path.exists():
                self._log(f"⚠️ Файл с ID '{safe_name}' уже существует\n")
                messagebox.showwarning("Warning", f"Rule with ID '{safe_name}' already exists!")
                return
            
            try:
                import shutil
                shutil.move(str(self.current_rule_file), str(new_file_path))
                self.current_rule_file = new_file_path
                
                # Обновляем внутренние данные
                self.scene_rules_data[category][safe_name] = self.scene_rules_data[category].pop(rule_name)
                
                # Обновляем meta внутри
                self.scene_rules_data[category][safe_name]['path'] = new_file_path
                self.scene_rules_data[category][safe_name]['data']['meta']['id'] = safe_name
                
                # Перестраиваем список слева
                self._build_scene_rules_list()
                
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
            # Упрощённая запись — для совместимости
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
    
    def _render_location_editor(self, parent, data: dict):
        """Рендерит редактор для локации (locations/*.toml)"""
        soft = data.get('soft_constraints', {})
        
        # 1. Prefers Actions (из prompt-library/04_action или 03_pose)
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent, "🎬 Prefers Actions", 
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="gray25"
        )
        
        # 2. Prefers Locations (для reference, если нужно)
        # Пропускаем, так как это сама локация
        
        # 3. Prefers Props
        all_props = self._load_all_tags_from_category("09_props")
        self._render_checklist_section(
            parent, "🧸 Prefers Props",
            all_props, soft.get('prefers_props', []),
            'prefers_props', bg_color="gray25"
        )
        
        # 4. Prefers Lighting
        all_lighting = self._load_all_tags_from_category("07_lighting")
        self._render_checklist_section(
            parent, "💡 Prefers Lighting",
            all_lighting, soft.get('prefers_lighting_sources', []),
            'prefers_lighting', bg_color="gray25"
        )
        
        # 5. Prefers Weather (ДОБАВЛЕНО!)
        all_weather = self._load_all_tags_from_category("10_weather")
        self._render_checklist_section(
            parent, "🌦️ Prefers Weather",
            all_weather, soft.get('prefers_weather', []),
            'prefers_weather', bg_color="gray25"
        )
    
    def _render_action_editor(self, parent, data: dict):
        """Рендерит редактор для действия (actions/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # 1. Prefers Locations
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(
            parent, "📍 Prefers Locations",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="gray25"
        )
        
        # 2. Prefers Poses (с подкатегориями)
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent, "🎭 Prefers Poses",
            all_poses, soft.get('prefers_poses', []),
            'prefers_poses', bg_color="gray25"
        )
        
        # 3. Prefers Expressions (с подкатегориями)
        all_expressions = self._load_all_tags_from_category("05_expression")
        self._render_checklist_section(
            parent, "😊 Prefers Expressions",
            all_expressions, soft.get('prefers_expressions', []),
            'prefers_expressions', bg_color="gray25"
        )
        
        # 4. Excludes Actions
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent, "🚫 Excludes Actions",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="gray25"
        )
        
        # 5. Requires Props
        all_props = self._load_all_tags_from_category("09_props")
        self._render_checklist_section(
            parent, "📦 Requires Props",
            all_props, hard.get('requires_props', []),
            'requires_props', bg_color="gray25"
        )

    def _render_weather_editor(self, parent, data: dict):
        """Рендерит редактор для погоды (weather/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # 1. Prefers Locations
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(
            parent, "📍 Prefers Locations",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="gray25"
        )
        
        # 2. Prefers Actions
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent, "🎬 Prefers Actions",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="gray25"
        )
        
        # 3. Prefers Lighting
        all_lighting = self._load_all_tags_from_category("07_lighting")
        self._render_checklist_section(
            parent, "💡 Prefers Lighting",
            all_lighting, soft.get('prefers_lighting_sources', []),
            'prefers_lighting', bg_color="gray25"
        )
        
        # 4. Excludes Weather (другие типы погоды)
        all_weather = self._load_all_tags_from_category("10_weather")
        self._render_checklist_section(
            parent, "🚫 Excludes Weather",
            all_weather, hard.get('excludes_weather', []),
            'excludes_weather', bg_color="gray25"
        )
    
    def _render_camera_editor(self, parent, data: dict):
        """Рендерит редактор для камеры (camera/*.toml)"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        # 1. Prefers Locations
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(
            parent, "📍 Prefers Locations",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="gray25"
        )
        
        # 2. Prefers Actions
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent, "🎬 Prefers Actions",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="gray25"
        )
        
        # 3. Prefers Poses
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(
            parent, "🎭 Prefers Poses",
            all_poses, soft.get('prefers_poses', []),
            'prefers_poses', bg_color="gray25"
        )
        
        # 4. Excludes Camera (другие ракурсы)
        all_camera = self._load_all_tags_from_category("06_camera")
        self._render_checklist_section(
            parent, "🚫 Excludes Camera",
            all_camera, hard.get('excludes_camera', []),
            'excludes_camera', bg_color="gray25"
        )
    
    def _render_location_type_editor(self, parent, data: dict):
        """Рендерит редактор для типа локации"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        all_actions = sorted(self.scene_rules_data.get('actions', {}).keys())
        
        # Excludes Actions
        self._render_checklist_section(
            parent, "🚫 Excludes Actions",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions'
        )
        
        # Prefers Actions
        self._render_checklist_section(
            parent, "🎬 Prefers Actions",
            all_actions, soft.get('prefers_actions', []),
            'actions'
        )
    
    def _render_checklist_section(self, parent, title: str, all_items,
                                   selected_items: list, constraint_key: str,
                                   bg_color="gray20"):
        """Рендерит сворачиваемую секцию с ленивой загрузкой и правильным поиском"""
        section = ctk.CTkFrame(parent, fg_color=bg_color)
        section.pack(fill="x", padx=5, pady=8)
        
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        toggle_btn = ctk.CTkButton(header, text=f"▶ {title}", width=400, height=28,
                                    fg_color="gray30", hover_color="gray40",
                                    font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        toggle_btn.pack(side="left")
        
        if isinstance(all_items, dict):
            total_count = sum(len(tags) for tags in all_items.values())
            selected_count = len([s for s in selected_items if any(s in tags for tags in all_items.values())])
        else:
            total_count = len(all_items) if all_items else 0
            selected_count = len([s for s in selected_items if s in (all_items or [])])
        
        count_label = ctk.CTkLabel(header, text=f"({selected_count}/{total_count})", text_color="gray60")
        count_label.pack(side="left", padx=(10, 0))
        
        content_frame = ctk.CTkFrame(section, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=(0, 10))
        content_frame.pack_forget()
        
        search_entry = ctk.CTkEntry(content_frame, placeholder_text="🔍 Filter tags...", height=30)
        search_entry.pack(fill="x", pady=(5, 10))
        
        checkbox_scroll = ctk.CTkScrollableFrame(content_frame, height=300)
        checkbox_scroll.pack(fill="both", expand=True)
        
        # Явная типизация для Pylance
        checkboxes: dict[str, ctk.BooleanVar] = {}
        has_subcategories = isinstance(all_items, dict)
        
        # Словарь для хранения состояний подкатегорий (ленивая загрузка)
        subcat_data: dict[str, dict] = {}
        
        def render_subcat_tags(subcat_name: str, tags: list, container: ctk.CTkFrame):
            """Рендерит теги внутри подкатегории (вызывается при первом разворачивании)"""
            for tag in sorted(tags):
                var = checkboxes.get(tag, ctk.BooleanVar(value=(tag in selected_items)))
                cb = ctk.CTkCheckBox(container, text=tag.replace('_', ' '), 
                                      variable=var,
                                      command=lambda i=tag, v=var, cl=count_label: 
                                        self._on_checkbox_toggled(i, v, constraint_key, cl, all_items))
                cb.pack(anchor="w", padx=5, pady=1)
                checkboxes[tag] = var
                subcat_data[subcat_name]['widgets'][tag] = cb

        if has_subcategories:
            for subcat_name, tags in sorted(all_items.items()):
                subcat_frame = ctk.CTkFrame(checkbox_scroll, fg_color="transparent")
                subcat_frame.pack(fill="x", pady=2)
                
                subcat_header = ctk.CTkFrame(subcat_frame, fg_color="transparent")
                subcat_header.pack(fill="x")
                
                subcat_toggle_btn = ctk.CTkButton(
                    subcat_header, 
                    text=f"▶ 📁 {subcat_name.replace('_', ' ').title()} ({len(tags)})",
                    anchor="w", fg_color="gray35", hover_color="gray45", 
                    height=26, font=ctk.CTkFont(size=12, weight="bold")
                )
                subcat_toggle_btn.pack(side="left", fill="x", expand=True)
                
                # Кнопка Select All / Clear (с правильной передачей button)
                select_all_btn = ctk.CTkButton(
                    subcat_header, text="Select All", width=80, height=24,
                    fg_color="gray40", hover_color="gray50", font=ctk.CTkFont(size=10)
                )
                select_all_btn.pack(side="right", padx=(5, 0))
                
                tags_container = ctk.CTkFrame(subcat_frame, fg_color="transparent")
                tags_container.pack(fill="x", padx=(30, 0))
                tags_container.pack_forget()
                
                subcat_data[subcat_name] = {
                    'toggle_btn': subcat_toggle_btn,
                    'select_all_btn': select_all_btn,
                    'container': tags_container,
                    'tags': tags,
                    'widgets': {},
                    'loaded': False
                }
                
                def toggle_subcat(btn=subcat_toggle_btn, cont=tags_container, name=subcat_name, tag_count=len(tags)):
                    if cont.winfo_ismapped():
                        self._hide_container(cont)
                        btn.configure(text=f"▶ 📁 {name.replace('_', ' ').title()} ({tag_count})")
                    else:
                        self._show_container(cont, padx=(30, 0))
                        btn.configure(text=f"▼ 📁 {name.replace('_', ' ').title()} ({tag_count})")
                
                subcat_toggle_btn.configure(command=toggle_subcat)
                
                def select_all_handler(sn=subcat_name):
                    data = subcat_data[sn]
                    # Передаем кнопку, чтобы текст менялся на Clear All
                    self._toggle_select_all_subcategory(sn, data['tags'], count_label, constraint_key, all_items, data['select_all_btn'])
                
                select_all_btn.configure(command=select_all_handler)
        else:
            if all_items:
                for item in sorted(all_items):
                    var = ctk.BooleanVar(value=(item in selected_items))
                    cb = ctk.CTkCheckBox(checkbox_scroll, text=item.replace('_', ' '), 
                                          variable=var,
                                          command=lambda i=item, v=var, cl=count_label: 
                                            self._on_checkbox_toggled(i, v, constraint_key, cl, all_items))
                    cb.pack(anchor="w", padx=10, pady=1)
                    checkboxes[item] = var
        
        # Логика поиска с debouncing (задержка 250мс для устранения тормозов)
        # Логика поиска с debouncing (задержка 250мс для устранения тормозов)
        def _do_search():
            """Выполняет поиск после задержки"""
            filter_text = search_entry.get().strip().lower()
            # 👇 Сюда вставить ВЕСЬ код поиска, который был внутри _do_search
            for w in checkbox_scroll.winfo_children():
                w.destroy()
            
            if has_subcategories:
                for subcat_name, data in subcat_data.items():
                    matching_tags = [t for t in data['tags'] if filter_text in t.lower()]
                    if not filter_text or matching_tags:
                        subcat_frame = ctk.CTkFrame(checkbox_scroll, fg_color="transparent")
                        subcat_frame.pack(fill="x", pady=2)
                        
                        subcat_header = ctk.CTkFrame(subcat_frame, fg_color="transparent")
                        subcat_header.pack(fill="x")
                        
                        display_count = len(matching_tags) if filter_text else len(data['tags'])
                        btn_text = f"▼ 📁 {subcat_name.replace('_', ' ').title()} ({display_count})" if filter_text else f"▶ 📁 {subcat_name.replace('_', ' ').title()} ({display_count})"
                        
                        subcat_toggle_btn = ctk.CTkButton(subcat_header, text=btn_text, anchor="w", fg_color="gray35", hover_color="gray45", height=26, font=ctk.CTkFont(size=12, weight="bold"))
                        subcat_toggle_btn.pack(side="left", fill="x", expand=True)
                        
                        select_all_btn = ctk.CTkButton(subcat_header, text="Select All", width=80, height=24, fg_color="gray40", hover_color="gray50", font=ctk.CTkFont(size=10))
                        select_all_btn.pack(side="right", padx=(5, 0))
                        
                        tags_container = ctk.CTkFrame(subcat_frame, fg_color="transparent")
                        if filter_text:
                            tags_container.pack(fill="x", padx=(30, 0))
                        else:
                            tags_container.pack(fill="x", padx=(30, 0))
                            tags_container.pack_forget()
                        
                        tags_to_show = matching_tags if filter_text else data['tags']
                        for tag in sorted(tags_to_show):
                            var = checkboxes.get(tag, ctk.BooleanVar(value=(tag in selected_items)))
                            cb = ctk.CTkCheckBox(tags_container, text=tag.replace('_', ' '), variable=var,
                                                  command=lambda i=tag, v=var, cl=count_label: self._on_checkbox_toggled(i, v, constraint_key, cl, all_items))
                            cb.pack(anchor="w", padx=5, pady=1)
                            checkboxes[tag] = var
                        
                        def toggle_search_subcat(cont=tags_container, btn=subcat_toggle_btn, name=subcat_name, cnt=display_count):
                            if cont.winfo_ismapped():
                                cont.pack_forget()
                                btn.configure(text=f"▶ 📁 {name.replace('_', ' ').title()} ({cnt})")
                            else:
                                cont.pack(fill="x", padx=(30, 0))
                                btn.configure(text=f"▼ 📁 {name.replace('_', ' ').title()} ({cnt})")
                        subcat_toggle_btn.configure(command=toggle_search_subcat)
                        
                        def search_select_all(sn=subcat_name):
                            self._toggle_select_all_subcategory(sn, data['tags'], count_label, constraint_key, all_items, select_all_btn)
                        select_all_btn.configure(command=search_select_all)
            else:
                for item in sorted(all_items):
                    if not filter_text or filter_text in item.lower():
                        var = checkboxes.get(item, ctk.BooleanVar(value=(item in selected_items)))
                        cb = ctk.CTkCheckBox(checkbox_scroll, text=item.replace('_', ' '), variable=var,
                                              command=lambda i=item, v=var, cl=count_label: self._on_checkbox_toggled(i, v, constraint_key, cl, all_items))
                        cb.pack(anchor="w", padx=10, pady=1)
                        checkboxes[item] = var
        
        def on_search(event):
            """Обработчик ввода в поле поиска с debouncing"""
            if self._search_timer is not None:
                self.after_cancel(self._search_timer)
            self._search_timer = self.after(250, _do_search)
        
        search_entry.bind('<KeyRelease>', on_search)
        
        def toggle_visibility():
            if content_frame.winfo_ismapped():
                self._hide_container(content_frame)
                toggle_btn.configure(text=f"▶ {title}")
            else:
                content_frame.pack(fill="x", padx=10, pady=(0, 10))
                toggle_btn.configure(text=f"▼ {title}")
        
        toggle_btn.configure(command=toggle_visibility)
        
        if not hasattr(self, '_current_checkboxes'):
            self._current_checkboxes = {}
        self._current_checkboxes[constraint_key] = checkboxes

    def _toggle_select_all_subcategory(self, subcat_name: str, tags: list,
                                        count_label, constraint_key: str, all_items, button):
        """Переключает выбор всех тегов в подкатегории"""
        if constraint_key not in self._current_checkboxes:
            return
        
        # Проверяем, сколько тегов из этой подкатегории уже выбрано
        selected_in_subcat = sum(1 for tag in tags
                                 if tag in self._current_checkboxes[constraint_key]
                                 and self._current_checkboxes[constraint_key][tag].get())
        
        # Если выбраны все или почти все — снимаем выбор, иначе — выбираем все
        should_select = selected_in_subcat < len(tags) / 2
        
        for tag in tags:
            if tag in self._current_checkboxes[constraint_key]:
                var = self._current_checkboxes[constraint_key][tag]
                var.set(should_select)
        
        # 👇 ОБНОВЛЯЕМ ТЕКСТ КНОПКИ
        if should_select:
            button.configure(text="Clear All")
        else:
            button.configure(text="Select All")
        
        # Обновляем счётчик
        if isinstance(all_items, dict):
            all_tags = []
            for subcat_tags in all_items.values():
                all_tags.extend(subcat_tags)
            selected_count = sum(1 for tag in all_tags
                                 if tag in self._current_checkboxes[constraint_key]
                                 and self._current_checkboxes[constraint_key][tag].get())
            total_count = len(all_tags)
        else:
            selected_count = sum(1 for v in self._current_checkboxes[constraint_key].values() if v.get())
            total_count = len(all_items) if all_items else 0
        
        count_label.configure(text=f"({selected_count}/{total_count})")
        
        action = "выбраны" if should_select else "сняты"
        self._log(f"{'☑' if should_select else '☐'} {subcat_name}: все теги {action}\n")
    
    def _on_props_checkbox_toggled(self, tag: str, var, count_label):
        """Обработчик чекбокса для props"""
        selected_count = sum(1 for v in self._current_checkboxes['props'].values() if v.get())
        count_label.configure(text=f"({selected_count} selected)")
        self._log(f"{'☑' if var.get() else '☐'} props: {tag}\n")
    
    def _on_checkbox_toggled(self, item: str, var, constraint_key: str, count_label, all_items):
        """Обработчик обычного чекбокса с Auto-sync"""
        # Подсчет выбранных элементов
        if isinstance(all_items, dict):
            all_tags = []
            for tags in all_items.values():
                all_tags.extend(tags)
            selected_count = sum(1 for tag in all_tags
                                 if self._current_checkboxes[constraint_key].get(tag, ctk.BooleanVar(value=False)).get())
            total_count = len(all_tags)
        else:
            selected_count = sum(1 for v in self._current_checkboxes[constraint_key].values() if v.get())
            total_count = len(all_items) if all_items else 0
        
        count_label.configure(text=f"({selected_count}/{total_count})")
        
        # 👇 AUTO-SYNC: синхронизация связей при включенном переключателе
        if self.auto_sync_var is not None and self.auto_sync_var.get() and self.current_rule_file:
            current_category = None
            current_rule_name = None
            try:
                rel_path = self.current_rule_file.relative_to(self.project_root / "scene-rules")
                parts = rel_path.parts
                if len(parts) >= 2:
                    current_category = parts[0]
                    current_rule_name = parts[1].replace('.toml', '')
            except Exception:
                pass
            
            if current_category and current_rule_name:
                sync_rules = {
                    ('locations', 'prefers_actions'): ('actions', 'prefers_locations'),
                    ('actions', 'prefers_locations'): ('locations', 'prefers_actions'),
                    ('actions', 'excludes_actions'): ('actions', 'excludes_actions'),
                }
                
                if (current_category, constraint_key) in sync_rules:
                    target_cat, target_field = sync_rules[(current_category, constraint_key)]
                    
                    if var.get():
                        self._add_bidirectional_link(target_cat, item, target_field, current_rule_name)
                    else:
                        self._remove_bidirectional_link(target_cat, item, target_field, current_rule_name)
        
        self._log(f"{'☑' if var.get() else '☐'} {constraint_key}: {item}\n")
        
        # 👇 AUTO-SYNC: синхронизация связей при включенном переключателе
        if self.auto_sync_var and self.auto_sync_var.get() and self.current_rule_file:
            current_category = None
            current_rule_name = None
            try:
                rel_path = self.current_rule_file.relative_to(self.project_root / "scene-rules")
                parts = rel_path.parts
                if len(parts) >= 2:
                    current_category = parts[0]
                    current_rule_name = parts[1].replace('.toml', '')
            except Exception:
                pass
            
            if current_category and current_rule_name:
                # Карта соответствий: что синхронизировать с чем
                sync_rules = {
                    # Редактируем location → синхронизируем action
                    ('locations', 'prefers_actions'): ('actions', 'prefers_locations'),
                    # Редактируем action → синхронизируем location
                    ('actions', 'prefers_locations'): ('locations', 'prefers_actions'),
                    # Редактируем action → синхронизируем другое action (для excludes)
                    ('actions', 'excludes_actions'): ('actions', 'excludes_actions'),
                }
                
                if (current_category, constraint_key) in sync_rules:
                    target_cat, target_field = sync_rules[(current_category, constraint_key)]
                    
                    if var.get():
                        self._add_bidirectional_link(target_cat, item, target_field, current_rule_name)
                    else:
                        self._remove_bidirectional_link(target_cat, item, target_field, current_rule_name)
        
        self._log(f"{'☑' if var.get() else '☐'} {constraint_key}: {item}\n")

    def _add_bidirectional_link(self, target_category: str, target_name: str,
                                 field: str, value_to_add: str):
        """Автоматически добавляет связь в связанный TOML файл (Auto-sync)"""
        target_path = self.project_root / "scene-rules" / target_category / f"{target_name}.toml"
        if not target_path.exists():
            self._log(f"⚠️ Auto-sync: файл {target_name}.toml не найден в {target_category}\n")
            return
        
        try:
            import tomli
            import tomli_w
            
            with open(target_path, 'rb') as f:
                data = tomli.load(f)
            
            changed = False
            for section in ['soft_constraints', 'hard_constraints']:
                if section in data and field in data[section]:
                    current_list = data[section][field]
                    if value_to_add not in current_list:
                        current_list.append(value_to_add)
                        data[section][field] = sorted(current_list)
                        changed = True
                    break
            
            if not changed:
                if 'soft_constraints' not in data:
                    data['soft_constraints'] = {}
                data['soft_constraints'][field] = [value_to_add]
            
            with open(target_path, 'wb') as f:
                tomli_w.dump(data, f)
            
            self._log(f"🔗 Auto-sync: {value_to_add} → {target_category}/{target_name}.{field}\n")
            
            if target_category in self.scene_rules_data and target_name in self.scene_rules_data[target_category]:
                self.scene_rules_data[target_category][target_name]['data'] = data
        
        except ImportError:
            self._log("⚠️ Auto-sync: установите tomli и tomli_w (pip install tomli tomli-w)\n")
        except Exception as e:
            self._log(f"❌ Auto-sync error: {e}\n")
    
    def _remove_bidirectional_link(self, target_category: str, target_name: str,
                                    field: str, value_to_remove: str):
        """Автоматически удаляет связь из связанного TOML файла (Auto-sync)"""
        target_path = self.project_root / "scene-rules" / target_category / f"{target_name}.toml"
        if not target_path.exists():
            return
        
        try:
            import tomli
            import tomli_w
            
            with open(target_path, 'rb') as f:
                data = tomli.load(f)
            
            changed = False
            for section in ['soft_constraints', 'hard_constraints']:
                if section in data and field in data[section]:
                    current_list = data[section][field]
                    if value_to_remove in current_list:
                        current_list.remove(value_to_remove)
                        data[section][field] = current_list
                        changed = True
                    break
            
            if changed:
                with open(target_path, 'wb') as f:
                    tomli_w.dump(data, f)
                self._log(f"🔗 Auto-sync: удалено {value_to_remove} из {target_category}/{target_name}.{field}\n")
                
                if target_category in self.scene_rules_data and target_name in self.scene_rules_data[target_category]:
                    self.scene_rules_data[target_category][target_name]['data'] = data
        
        except ImportError:
            pass
        except Exception as e:
            self._log(f"❌ Auto-sync error: {e}\n")
    
    def _on_category_toggled(self, cat_name: str, cat_var):
        """Обработчик клика на категорию props"""
        self._log(f"{'☑' if cat_var.get() else '☐'} Категория props: {cat_name}\n")
        # TODO: Обновить все дочерние теги
    
    def _on_tag_toggled(self, cat_name: str, cat_var, tag_var, all_tags_in_cat):
        """Обработчик клика на отдельный тег props"""
        self._log(f"{'☑' if tag_var.get() else '☐'} Тег в {cat_name}\n")
        # TODO: Обновить состояние родительской категории
    
    def _load_all_tags_from_category(self, category: str) -> dict:
        """Загружает все теги из категории prompt-library с сохранением структуры подкатегорий
        
        Returns:
            dict: {subcategory_name: [list_of_tags]}
        """
        result = {}
        cat_dir = self.project_root / "prompt-library" / category
        
        if not cat_dir.exists():
            return result
        
        for txt_file in sorted(cat_dir.rglob("*.txt")):
            # Извлекаем имя подкатегории из имени файла
            subcat_name = txt_file.stem  # arms.txt -> arms
            tags = self._load_tags_from_file(txt_file)
            if tags:
                result[subcat_name] = tags
        
        return result
    
    def _reload_scene_rules(self):
        """Перезагружает все TOML-файлы"""
        self._load_scene_rules()
        self._build_scene_rules_list()
        self._log("🔄 Scene rules перезагружены\n")
    
    def _save_scene_rules(self):
        """Сохраняет все изменения чекбоксов в TOML-файлы"""
        if not hasattr(self, '_current_checkboxes') or not self._current_checkboxes:
            messagebox.showinfo("Info", "Нет изменений для сохранения")
            return
        
        try:
            import tomli
            import tomli_w
        except ImportError:
            messagebox.showerror("Error", "Установите tomli и tomli-w:\npip install tomli tomli-w")
            return
        
        # Собираем все изменения
        changes = self._collect_checkbox_changes()
        
        if not changes:
            messagebox.showinfo("Info", "Нет изменений для сохранения")
            return
        
        # Применяем изменения к файлам
        saved_count = 0
        errors = []
        
        for category, rule_name, field, new_values in changes:
            file_path = self.project_root / "scene-rules" / category / f"{rule_name}.toml"
            if not file_path.exists():
                errors.append(f"Файл не найден: {file_path.name}")
                continue
            
            try:
                with open(file_path, 'rb') as f:
                    data = tomli.load(f)
                
                # Определяем, в какую секцию сохранять
                if 'soft_constraints' not in data:
                    data['soft_constraints'] = {}
                
                data['soft_constraints'][field] = new_values
                
                with open(file_path, 'wb') as f:
                    tomli_w.dump(data, f)
                
                # Обновляем внутренние данные
                if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                    self.scene_rules_data[category][rule_name]['data'] = data
                
                saved_count += 1
                
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
        
        # Показываем результат
        if errors:
            error_msg = "\n".join(errors[:5])  # Показываем только первые 5 ошибок
            if len(errors) > 5:
                error_msg += f"\n... и ещё {len(errors) - 5} ошибок"
            messagebox.showerror("Ошибки сохранения", error_msg)
            self._log(f"⚠️ Сохранено {saved_count} файлов, {len(errors)} ошибок\n")
        else:
            messagebox.showinfo("Success", f"✅ Сохранено {saved_count} файлов!")
            self._log(f"💾 Успешно сохранено {saved_count} TOML-файлов\n")
    
    def _collect_checkbox_changes(self) -> list:
        """Собирает все изменения из чекбоксов
        
        Returns:
            list: [(category, rule_name, field, [selected_values])]
        """
        changes = []
        
        if not self.current_rule_file:
            return changes
        
        try:
            rel_path = self.current_rule_file.relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) < 2:
                return changes
            current_category = parts[0]
            current_rule_name = parts[1].replace('.toml', '')
        except Exception:
            return changes
        
        # Собираем значения из каждого constraint_key
        for constraint_key, checkboxes in self._current_checkboxes.items():
            selected_values = [tag for tag, var in checkboxes.items() if var.get()]
            
            if selected_values:  # Сохраняем только если есть выбранные значения
                changes.append((current_category, current_rule_name, constraint_key, sorted(selected_values)))
        
        return changes

    def _create_generate_tab(self):
        tab = self.tabview.tab("Generate")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        # 👇 ПОЛИРОВКА: row 2 растягивается (где лог и кнопки)
        tab.grid_rowconfigure(2, weight=1)
        
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(left_frame, text="⚙️ Generation Settings",
                      font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 10), padx=15, anchor="w")
        
        ctk.CTkLabel(left_frame, text="👤 Character Profile:", anchor="w").pack(pady=(10, 0), padx=15, fill="x")
        self.character_combobox = ctk.CTkComboBox(left_frame, values=self._get_available_profiles())
        self.character_combobox.pack(pady=(0, 15), padx=15, fill="x")
        profiles = self._get_available_profiles()
        if profiles:
            self.character_combobox.set(profiles[0])
        
        ctk.CTkLabel(left_frame, text="🎬 Number of Scenes:", anchor="w").pack(pady=(10, 0), padx=15, fill="x")
        self.scenes_entry = ctk.CTkEntry(left_frame, placeholder_text="100")
        self.scenes_entry.insert(0, "30")
        self.scenes_entry.pack(pady=(0, 15), padx=15, fill="x")
        
        ctk.CTkLabel(left_frame, text="📂 Save to folder:", anchor="w").pack(pady=(10, 0), padx=15, fill="x")
        output_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        output_frame.pack(pady=(0, 15), padx=15, fill="x")
        output_frame.grid_columnconfigure(0, weight=1)
        self.output_path_entry = ctk.CTkEntry(output_frame)
        self.output_path_entry.insert(0, self.output_directory)
        self.output_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(output_frame, text="Browse", width=80, command=self._browse_output_folder).grid(row=0, column=1)
        
        ctk.CTkFrame(left_frame, height=2).pack(pady=15, padx=15, fill="x")
        
        ctk.CTkLabel(left_frame, text="⚖️ Coverage Engine:",
                      font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(pady=(0, 10), padx=15, fill="x")
        ctk.CTkLabel(left_frame, text="Balance from folder:", anchor="w").pack(pady=(0, 5), padx=15, fill="x")
        balance_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        balance_frame.pack(pady=(0, 10), padx=15, fill="x")
        balance_frame.grid_columnconfigure(0, weight=1)
        self.balance_path_entry = ctk.CTkEntry(balance_frame, placeholder_text="Optional...")
        self.balance_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(balance_frame, text="Browse", width=80, command=self._browse_balance_folder).grid(row=0, column=1)
        
        self.balance_locations_var = ctk.BooleanVar(value=True)
        self.balance_actions_var = ctk.BooleanVar(value=True)
        self.balance_weather_var = ctk.BooleanVar(value=True)
        self.balance_cameras_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(left_frame, text="Balance Locations", variable=self.balance_locations_var).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Actions", variable=self.balance_actions_var).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Weather", variable=self.balance_weather_var).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Cameras", variable=self.balance_cameras_var).pack(pady=2, padx=15, anchor="w")
        
        force_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        force_frame.pack(pady=(12, 2), padx=15, fill="x")
        self.force_deficit_closure_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(force_frame, text="⚡ Force Deficit Closure",
                         variable=self.force_deficit_closure_var,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(force_frame, text="?", width=25, height=25,
                       fg_color="gray40", hover_color="gray50",
                       font=ctk.CTkFont(size=12, weight="bold"), corner_radius=15,
                       command=self._show_force_closure_help).pack(side="left", padx=(8, 0))
        
        ctk.CTkFrame(left_frame, height=2).pack(pady=15, padx=15, fill="x")
        
        # 👇 ПОЛИРОВКА: Кнопки растягиваются, высота увеличена, sticky="nsew"
        buttons_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        buttons_frame.pack(fill="both", expand=True, padx=15, pady=10)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        buttons_frame.grid_rowconfigure(0, weight=1)
        
        ctk.CTkButton(buttons_frame, text="🎲 Roll Dice", 
                       fg_color=COLORS['primary_blue'], hover_color=COLORS['primary_blue_hover'],
                       command=self._roll_dice).grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        ctk.CTkButton(buttons_frame, text="🚀 Generate Batch", 
                       fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                       command=self._start_generation).grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        log_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_header, text="📝 Generation Log",
                      font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(log_header, text="📋 Copy All", width=100,
                       command=self._copy_log_to_clipboard).grid(row=0, column=1)
        
        self.log_textbox = ctk.CTkTextbox(right_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.log_textbox.bind("<Key>", self._block_text_edit)
        self.log_textbox.bind("<<Paste>>", self._block_text_edit)
        self.log_textbox.bind("<<Cut>>", self._block_text_edit)
        
        self._log("✅ Dataset Composer готов к работе.\n")
        self._log(f"📂 Output directory: {self.output_directory}\n")

    def _create_analyzer_tab(self):
        tab = self.tabview.tab("Analyzer")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)
        
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # 👇 ПОЛИРОВКА: Описание сразу под заголовком
        ctk.CTkLabel(left_frame, text="📊 Analyzer Settings",
                      font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 5), padx=15, anchor="w")
        
        ctk.CTkLabel(left_frame, 
                      text="ℹ️ Анализатор просканирует папку, построит матрицу покрытия с детекцией дефицита/переизбытка.",
                      wraplength=280, justify="left", anchor="w", text_color="gray").pack(pady=(0, 10), padx=15, fill="x")
        
        ctk.CTkLabel(left_frame, text="📂 Analyze folder:", anchor="w").pack(pady=(10, 0), padx=15, fill="x")
        folder_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        folder_frame.pack(pady=(0, 15), padx=15, fill="x")
        folder_frame.grid_columnconfigure(0, weight=1)
        self.analyze_path_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select folder...")
        self.analyze_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(folder_frame, text="Browse", width=80, command=self._browse_analyze_folder).grid(row=0, column=1)
        
        ctk.CTkButton(left_frame, text="🔍 Analyze Dataset", fg_color="#2563eb", hover_color="#1d4ed8",
                       font=ctk.CTkFont(size=14, weight="bold"), height=45,
                       command=self._run_analysis).pack(pady=20, padx=15, fill="x")
        ctk.CTkButton(left_frame, text="⚡ Auto-Fix Deficit", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                       font=ctk.CTkFont(size=13, weight="bold"), height=40,
                       command=self._auto_fix_deficit).pack(pady=(15, 5), padx=15, fill="x")
        
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        log_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_header, text="📈 Coverage Matrix",
                      font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w")
        
        # 👇 ПОЛИРОВКА: Clear Log рядом с Copy Matrix
        ctk.CTkButton(log_header, text="🗑️ Clear Log", width=100,
                       fg_color="gray40", hover_color="gray50",
                       command=self._clear_analyzer_log).grid(row=0, column=1, padx=(0, 5))
        ctk.CTkButton(log_header, text="📋 Copy Matrix", width=120,
                       command=self._copy_analyzer_to_clipboard).grid(row=0, column=2)
        
        self.analyzer_textbox = ctk.CTkTextbox(right_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.analyzer_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        self._analyzer_log("👋 Добро пожаловать в Dataset Analyzer!\n\n")
        self._analyzer_log("1. Нажмите 'Browse' и выберите папку с промптами\n")
        self._analyzer_log("2. Нажмите '🔍 Analyze Dataset'\n\n")

    def _create_settings_tab(self):
        tab = self.tabview.tab("Settings")
        self._create_placeholder(tab, "⚙️ Settings\n\nПути и интеграции.")

    # ════════════════════════════════════════════════════════════════════════════
    # LIBRARY: Редактор библиотеки тегов
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_library_tree(self):
        """Строит дерево файлов из prompt-library"""
        if self.library_tree is None: return
        
        for w in self.library_tree.winfo_children():
            w.destroy()
        
        library_dir = self.project_root / "prompt-library"
        if not library_dir.exists():
            ctk.CTkLabel(self.library_tree, text=f"⚠️ Папка не найдена: {library_dir}",
                         text_color="red").pack(pady=20)
            return
        
        # Группируем файлы по категориям
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
        
        # Создаём дерево
        for main_cat, subcats in sorted(categories.items()):
            cat_frame = ctk.CTkFrame(self.library_tree, fg_color="transparent")
            cat_frame.pack(fill="x", pady=2)
            
            cat_container = ctk.CTkFrame(cat_frame, fg_color="transparent")
            cat_container.pack(fill="x")
            cat_container.pack_forget()
            
            ctk.CTkButton(cat_frame, text=f"➤ {main_cat.replace('_', ' ').title()}",
                           anchor="w", fg_color="gray30", hover_color="gray40", height=30,
                           font=ctk.CTkFont(size=13, weight="bold"),
                           command=lambda cc=cat_container: self._toggle_library_section(cc)).pack(fill="x")
            
            for sub_cat, files in sorted(subcats.items()):
                sub_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
                sub_frame.pack(fill="x", padx=(20, 0), pady=1)
                
                sub_container = ctk.CTkFrame(sub_frame, fg_color="transparent")
                sub_container.pack(fill="x", padx=(20, 0))
                sub_container.pack_forget()
                
                ctk.CTkButton(sub_frame, text=f"➤ {sub_cat.replace('_', ' ').title()}",
                               anchor="w", fg_color="gray25", hover_color="gray35", height=26,
                               font=ctk.CTkFont(size=12),
                               command=lambda sc=sub_container: self._toggle_library_section(sc)).pack(fill="x")
                
                for txt_file in files:
                    file_btn = ctk.CTkButton(sub_container, text=f"📄 {txt_file.name}",
                                              anchor="w", fg_color="transparent",
                                              text_color=("gray10", "gray90"),
                                              hover_color=("gray85", "gray30"),
                                              command=lambda f=txt_file: self._load_library_file(f))
                    file_btn.pack(fill="x", padx=(20, 0), pady=1)
    
    def _toggle_library_section(self, container):
        """Разворачивает/сворачивает секцию в дереве Library"""
        if container.winfo_ismapped():
            self._hide_container(container)
        else:
            container.pack(fill="x", padx=(20, 0))
    
    def _load_library_file(self, file_path: Path):
        """Загружает теги из выбранного файла"""
        self.library_current_file = file_path
        self.library_tags = []
        
        # Читаем теги
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.library_tags.append(line)
        except Exception as e:
            self._log(f"❌ Ошибка чтения {file_path}: {e}\n")
            return
        
        # Обновляем заголовок
        if self.library_editor_title:
            rel_path = file_path.relative_to(self.project_root / "prompt-library")
            self.library_editor_title.configure(text=f"📝 {rel_path} ({len(self.library_tags)} tags)")
        
        # Показываем теги
        self._display_library_tags()
        
        # Очищаем поиск
        if self.library_search_entry:
            self.library_search_entry.delete(0, "end")
    
    def _display_library_tags(self, filter_text: str = ""):
        """Отображает теги в редакторе"""
        if self.library_tags_container is None: return
        
        for w in self.library_tags_container.winfo_children():
            w.destroy()
        
        if not self.library_tags:
            ctk.CTkLabel(self.library_tags_container, text="(No tags in this file)",
                         text_color="gray").pack(anchor="w", padx=10, pady=10)
            return
        
        # Фильтруем теги
        filtered_tags = self.library_tags
        if filter_text:
            filter_lower = filter_text.lower()
            filtered_tags = [t for t in self.library_tags if filter_lower in t.lower()]
        
        if not filtered_tags:
            ctk.CTkLabel(self.library_tags_container, text=f"(No tags match '{filter_text}')",
                         text_color="gray").pack(anchor="w", padx=10, pady=10)
            return
        
        # Показываем теги
        for i, tag in enumerate(filtered_tags):
            tag_row = ctk.CTkFrame(self.library_tags_container, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(tag_row, text=f"  • {tag}", anchor="w")
            tag_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            delete_btn = ctk.CTkButton(tag_row, text="×", width=30, height=25,
                                        fg_color="#dc2626", hover_color="#991b1b",
                                        command=lambda t=tag: self._delete_library_tag(t))
            delete_btn.pack(side="right", padx=(5, 0))
    
    def _filter_library_tags(self):
        """Фильтрует теги по тексту поиска"""
        if self.library_search_entry is None: return
        filter_text = self.library_search_entry.get().strip()
        self._display_library_tags(filter_text)
    
    def _clear_library_search(self):
        """Очищает поле поиска"""
        if self.library_search_entry:
            self.library_search_entry.delete(0, "end")
            self._display_library_tags()
    
    def _add_library_tag(self):
        """Добавляет новый тег в файл"""
        if self.library_current_file is None:
            messagebox.showwarning("Warning", "Сначала выберите файл")
            return
        
        if not hasattr(self, 'new_tag_entry') or self.new_tag_entry is None:
            return
        
        new_tag = self.new_tag_entry.get().strip()
        if not new_tag:
            return
        
        # Проверяем, что тег ещё не существует
        if new_tag in self.library_tags:
            messagebox.showwarning("Warning", f"Тег '{new_tag}' уже существует")
            return
        
        # Добавляем тег
        self.library_tags.append(new_tag)
        self.new_tag_entry.delete(0, "end")
        
        # Сохраняем в файл
        self._save_library_file()
        
        # Обновляем отображение
        self._display_library_tags()
        
        # Обновляем заголовок
        if self.library_editor_title:
            rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
            self.library_editor_title.configure(text=f"📝 {rel_path} ({len(self.library_tags)} tags)")
        
        self._log(f"➕ Добавлен тег: {new_tag}\n")
    
    def _delete_library_tag(self, tag: str):
        """Удаляет тег из файла"""
        if self.library_current_file is None:
            return
        
        # Подтверждение
        if not messagebox.askyesno("Confirm Delete", f"Удалить тег '{tag}'?"):
            return
        
        # Удаляем тег
        if tag in self.library_tags:
            self.library_tags.remove(tag)
        
        # Сохраняем в файл
        self._save_library_file()
        
        # Обновляем отображение
        filter_text = self.library_search_entry.get().strip() if self.library_search_entry else ""
        self._display_library_tags(filter_text)
        
        # Обновляем заголовок
        if self.library_editor_title:
            rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
            self.library_editor_title.configure(text=f"📝 {rel_path} ({len(self.library_tags)} tags)")
        
        self._log(f"🗑️ Удалён тег: {tag}\n")
    
    def _save_library_file(self):
        """Сохраняет теги обратно в файл"""
        if self.library_current_file is None:
            return
        
        try:
            with open(self.library_current_file, 'w', encoding='utf-8') as f:
                for tag in self.library_tags:
                    f.write(f"{tag}\n")
            
            # Инвалидируем кэш тегов
            cache_key = str(self.library_current_file)
            if cache_key in self._tags_cache:
                del self._tags_cache[cache_key]
            
            self._log(f"💾 Файл сохранён: {self.library_current_file.name}\n")
        except Exception as e:
            self._log(f"❌ Ошибка сохранения: {e}\n")
            messagebox.showerror("Error", f"Не удалось сохранить файл: {e}")

    # ════════════════════════════════════════════════════════════════════════════
    # 3. PROFILES: Управление списком персонажей
    # ════════════════════════════════════════════════════════════════════════════
    
    def _get_available_profiles(self):
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
        if self.profiles_listbox is None: return
        for widget in self.profiles_listbox.winfo_children():
            widget.destroy()
        for profile_name in self._get_available_profiles():
            if profile_name == "No profiles found":
                continue
            # 👇 ПОЛИРОВКА: Обводка вокруг кнопки
            btn = ctk.CTkButton(
                self.profiles_listbox, text=f"👤 {profile_name}", anchor="w", height=35,
                fg_color="transparent", text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray30"),
                border_width=1, border_color=COLORS['border_color'],
                command=lambda p=profile_name: self._select_profile(p)
            )
            btn.pack(fill="x", pady=2)

    def _select_profile(self, profile_name):
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
        
        from tkinter import simpledialog
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
            import shutil
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
        import yaml
        from tkinter import simpledialog
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
            f.write("# Фильтр поверх scene-rules\n\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._log(f"➕ Создан новый профиль: {name}\n")
        self._refresh_profiles_list()
        self._select_profile(name)
        messagebox.showinfo("Success", f"Profile '{name}' created!")

    def _import_profile(self):
        import shutil
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
        if not self.current_profile_name:
            messagebox.showwarning("Warning", "No profile selected")
            return
        if not messagebox.askyesno("Confirm Delete",
                                    f"Are you sure you want to delete '{self.current_profile_name}'?\n\nThis cannot be undone!"):
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

    # ════════════════════════════════════════════════════════════════════════════
    # 4.1 DNA
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_dna_tree(self):
        if self.dna_tree_frame is None: return
        for w in self.dna_tree_frame.winfo_children(): w.destroy()
        self.dna_tag_ui_elements = {}
        for cat_name, cat_file in [
            ("Hair Style", "01_character/hair/style.txt"),
            ("Hair Color", "01_character/hair/color.txt"),
            ("Eye Color", "01_character/eyes/color.txt"),
        ]:
            self._create_dna_category(cat_name, cat_file)
    
    def _create_dna_category(self, cat_name, cat_file):
        if self.dna_tree_frame is None: return
        cat_frame = ctk.CTkFrame(self.dna_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        ctk.CTkButton(cat_frame, text=f"➤ {cat_name}", anchor="w",
                       fg_color="gray30", hover_color="gray40", height=30,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=lambda: self._toggle_dna_category(cat_name)).pack(fill="x")
        tags_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        self.wardrobe_sections_expanded[f"dna.{cat_name}"] = {'frame': tags_frame, 'expanded': False}
        for tag in self._load_tags_from_library(cat_file):
            tag_key = f"dna::{cat_name}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            # 👇 ПОЛИРОВКА: Убрали width=250, чтобы текст растягивался
            tag_label = ctk.CTkLabel(tag_row, text=f"  • {tag.replace('_', ' ')}", anchor="w")
            tag_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            action_btn = ctk.CTkButton(tag_row, text="+", width=30, height=25,
                                        fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        command=lambda t=tag, cn=cat_name, tk=tag_key: self._toggle_dna_tag(t, cn, tk))
            action_btn.pack(side="right", padx=(0, 5))
            self.dna_tag_ui_elements[tag_key] = {'label': tag_label, 'button': action_btn, 'tag': tag, 'category': cat_name}
    
    def _toggle_dna_category(self, cat_name):
        key = f"dna.{cat_name}"
        if key not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[key]
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_dna_tag(self, tag, category, tag_key):
        if tag_key not in self.dna_tag_ui_elements: return
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
        if self.selected_dna_tags_container is None: return
        for w in self.selected_dna_tags_container.winfo_children(): w.destroy()
        if not self.selected_dna_tags:
            ctk.CTkLabel(self.selected_dna_tags_container,
                         text="(No DNA tags selected — разверните категории и нажмите [+])",
                         text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        COLS = 4
        for i, te in enumerate(self.selected_dna_tags):
            chip = ctk.CTkFrame(self.selected_dna_tags_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i//COLS, column=i%COLS, padx=3, pady=3, sticky="ew")
            self.selected_dna_tags_container.grid_columnconfigure(i%COLS, weight=1)
            ctk.CTkLabel(chip, text=f"  {te['tag'].replace('_', ' ')}  ", font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 5), pady=4)
            ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                           hover_color=COLORS['danger_red'], text_color="white",
                           font=ctk.CTkFont(size=14, weight="bold"),
                           command=lambda te=te: self._remove_dna_tag_from_chip(te)).pack(side="right", padx=(0, 5), pady=2)
    
    def _remove_dna_tag_from_chip(self, tag_entry):
        if tag_entry not in self.selected_dna_tags: return
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
        if not self.dna_tag_ui_elements: return
        for tag_key, ui in self.dna_tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'category': ui['category']}
            if tag_entry in self.selected_dna_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    def _sync_lighting_ui_states(self):
        """Синхронизирует UI элементы Lighting с выбранными тегами"""
        if not self.lighting_tag_ui_elements: return
        for tag_key, ui in self.lighting_tag_ui_elements.items():
            tag = ui['tag']
            if tag in self.selected_lighting_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
    
    def _sync_weather_ui_states(self):
        """Синхронизирует UI элементы Weather с выбранными тегами"""
        if not self.weather_tag_ui_elements: return
        for tag_key, ui in self.weather_tag_ui_elements.items():
            tag = ui['tag']
            if tag in self.selected_weather_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    # ════════════════════════════════════════════════════════════════════════════
    # 4.2 Outfits
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_wardrobe_tree(self):
        if self.wardrobe_tree_frame is None: return
        for w in self.wardrobe_tree_frame.winfo_children(): w.destroy()
        self.tag_ui_elements = {}
        clothing_dir = self.project_root / "prompt-library" / "02_clothing"
        if not clothing_dir.exists(): return
        
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
        if self.wardrobe_tree_frame is None: return
        cat_frame = ctk.CTkFrame(self.wardrobe_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        ctk.CTkButton(cat_frame, text=f"➤ {main_cat.replace('_', ' ').title()}", anchor="w",
                       fg_color="gray30", hover_color="gray40", height=30,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=lambda: self._toggle_category(main_cat)).pack(fill="x")
        subcats_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        subcats_frame.pack(fill="x", padx=(20, 0))
        subcats_frame.pack_forget()
        self.wardrobe_sections_expanded[main_cat] = {'frame': subcats_frame, 'expanded': False}
        for sub_cat, file_path in subcats.items():
            self._create_wardrobe_subcategory(subcats_frame, main_cat, sub_cat, file_path)
    
    def _create_wardrobe_subcategory(self, parent_frame, main_cat, sub_cat, file_path):
        sub_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        ctk.CTkButton(sub_frame, text=f"  ➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                       fg_color="gray25", hover_color="gray35", height=26,
                       font=ctk.CTkFont(size=12),
                       command=lambda: self._toggle_subcategory(main_cat, sub_cat)).pack(fill="x")
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        self.wardrobe_sections_expanded[f"{main_cat}.{sub_cat}"] = {'frame': tags_frame, 'expanded': False}
        for tag in self._load_tags_from_file(file_path):
            tag_key = f"{sub_cat}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            # 👇 ПОЛИРОВКА: Убрали width=250
            tag_label = ctk.CTkLabel(tag_row, text=f"    • {tag.replace('_', ' ')}", anchor="w")
            tag_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            action_btn = ctk.CTkButton(tag_row, text="+", width=30, height=25,
                                        fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        command=lambda t=tag, sc=sub_cat, tk=tag_key: self._toggle_wardrobe_tag(t, sc, tk))
            action_btn.pack(side="right", padx=(0, 5))
            self.tag_ui_elements[tag_key] = {'label': tag_label, 'button': action_btn, 'tag': tag, 'subcategory': sub_cat}
    
    def _toggle_category(self, main_cat):
        if main_cat not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[main_cat]
        if section['expanded']:
            section['frame'].pack_forget()
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_subcategory(self, main_cat, sub_cat):
        key = f"{main_cat}.{sub_cat}"
        if key not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[key]
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_wardrobe_tag(self, tag, subcategory, tag_key):
        if tag_key not in self.tag_ui_elements: return
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
        if self.selected_tags_container is None: return
        for w in self.selected_tags_container.winfo_children(): w.destroy()
        if not self.selected_wardrobe_tags:
            ctk.CTkLabel(self.selected_tags_container,
                         text="(No tags selected)", text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        COLS = 4
        for i, te in enumerate(self.selected_wardrobe_tags):
            chip = ctk.CTkFrame(self.selected_tags_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i//COLS, column=i%COLS, padx=3, pady=3, sticky="ew")
            self.selected_tags_container.grid_columnconfigure(i%COLS, weight=1)
            ctk.CTkLabel(chip, text=f"  {te['tag'].replace('_', ' ')}  ", font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 5), pady=4)
            ctk.CTkButton(chip, text="×", width=22, height=22, fg_color="transparent",
                           hover_color=COLORS['danger_red'], text_color="white",
                           font=ctk.CTkFont(size=14, weight="bold"),
                           command=lambda te=te: self._remove_tag_from_chip(te)).pack(side="right", padx=(0, 5), pady=2)
    
    def _remove_tag_from_chip(self, tag_entry):
        if tag_entry not in self.selected_wardrobe_tags: return
        self.selected_wardrobe_tags.remove(tag_entry)
        tag_key = f"{tag_entry['subcategory']}::{tag_entry['tag']}"
        if tag_key in self.tag_ui_elements:
            ui = self.tag_ui_elements[tag_key]
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
        self._debounce_ui_update('wardrobe_chips')
    
    def _sync_tag_ui_states(self):
        if not self.tag_ui_elements: return
        for tag_key, ui in self.tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'subcategory': ui['subcategory']}
            if tag_entry in self.selected_wardrobe_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])

    # ════════════════════════════════════════════════════════════════════════════
    # 4.3 Personality
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_personality_tree(self):
        if self.personality_tree_frame is None: return
        for w in self.personality_tree_frame.winfo_children(): w.destroy()
        self.personality_tag_ui_elements = {}
        categories = [
            ("Expressions", "05_expression", ["mood", "eyes_expr", "mouth"]),
            ("Poses", "03_pose", ["base", "head", "arms", "legs"]),
        ]
        for cat_name, cat_dir, subcat_order in categories:
            self._create_personality_category(cat_name, cat_dir, subcat_order)
    
    def _create_personality_category(self, cat_name, cat_dir, subcat_order):
        if self.personality_tree_frame is None: return
        cat_frame = ctk.CTkFrame(self.personality_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        ctk.CTkButton(cat_frame, text=f"➤ {cat_name}", anchor="w",
                       fg_color="gray30", hover_color="gray40", height=30,
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=lambda: self._toggle_personality_category(cat_name)).pack(fill="x")
        subcats_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        subcats_frame.pack(fill="x", padx=(20, 0))
        subcats_frame.pack_forget()
        self.personality_sections_expanded[f"personality.{cat_name}"] = {'frame': subcats_frame, 'expanded': False}
        
        dir_path = self.project_root / "prompt-library" / cat_dir
        if not dir_path.exists(): return
        
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
        self.personality_sections_expanded[f"personality.{cat_name}.{sub_cat}"] = {'frame': tags_frame, 'expanded': False}
        
        for tag in self._load_tags_from_file(file_path):
            tag_key = f"personality::{cat_name}::{sub_cat}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            ctk.CTkLabel(tag_row, text=f"    • {tag.replace('_', ' ')}", anchor="w", width=220).pack(side="left", padx=(5, 0))
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
                'label': ctk.CTkLabel(tag_row, text=f"    • {tag.replace('_', ' ')}", anchor="w", width=220),
                'prefer_btn': prefer_btn, 'avoid_btn': avoid_btn,
                'tag': tag, 'category': cat_name, 'subcategory': sub_cat
            }
    
    def _toggle_personality_category(self, cat_name):
        key = f"personality.{cat_name}"
        if key not in self.personality_sections_expanded: return
        section = self.personality_sections_expanded[key]
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_personality_subcategory(self, cat_name, sub_cat):
        key = f"personality.{cat_name}.{sub_cat}"
        if key not in self.personality_sections_expanded: return
        section = self.personality_sections_expanded[key]
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_personality_tag(self, tag, category, subcategory, tag_key, action):
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
        if not self.personality_tag_ui_elements: return
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
        if self.prefer_container is None or self.avoid_container is None: return
        for w in self.prefer_container.winfo_children(): w.destroy()
        for w in self.avoid_container.winfo_children(): w.destroy()
        
        def build_chips(container, tags, color):
            if not tags:
                ctk.CTkLabel(container, text="(empty)", text_color="gray").pack(anchor="w", padx=10, pady=5)
                return
            COLS = 2
            for i, entry in enumerate(tags):
                chip = ctk.CTkFrame(container, fg_color="gray30", corner_radius=15)
                chip.grid(row=i//COLS, column=i%COLS, padx=3, pady=3, sticky="ew")
                container.grid_columnconfigure(i%COLS, weight=1)
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

    # ════════════════════════════════════════════════════════════════════════════
    # 4.4 Signature
    # ════════════════════════════════════════════════════════════════════════════
    
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
        if self.props_container is None: return
        for w in self.props_container.winfo_children(): w.destroy()
        if not self.signature_props:
            ctk.CTkLabel(self.props_container, text="(No signature props — нажмите '➕ Add Prop')",
                          text_color="gray").pack(anchor="w", padx=10, pady=5)
            return
        
        for i, prop in enumerate(self.signature_props):
            prop_frame = ctk.CTkFrame(self.props_container, fg_color="gray25", corner_radius=8)
            prop_frame.pack(fill="x", padx=5, pady=5)
            
            header = ctk.CTkFrame(prop_frame, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(5, 5))
            
            # 👇 ПОЛИРОВКА: Prop name над полем
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
            
            # 👇 ПОЛИРОВКА: Tags крупнее и выровнен
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
        if self.hair_rules_container is None: return
        
        if hasattr(self, 'hair_default_btn') and self.hair_default_btn:
            current_default = self.hair_rules_data.get('default', 'hair down')
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " ⭐" if current_default in dna_styles else ""
            self.hair_default_btn.configure(text=f"▼ {current_default}{star}")
        
        for w in self.hair_rules_container.winfo_children(): w.destroy()
        
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
            ctk.CTkLabel(header, text=f"Rule #{i+1}", font=ctk.CTkFont(weight="bold")).pack(side="left")
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
        popup = ctk.CTkToplevel(self)
        popup.title("Browse Tags (Props)")
        popup.geometry("500x600")
        popup.transient(self)
        popup.grab_set()
        
        ctk.CTkLabel(popup, text="🧸 Select tags (multiple allowed):", 
                      font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(popup)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        props_dir = self.project_root / "prompt-library" / "09_props"
        if not props_dir.exists():
            ctk.CTkLabel(scroll_frame, text=f"⚠️ Папка не найдена: {props_dir}",
                          text_color="red").pack(pady=20)
            ctk.CTkButton(popup, text="Close", fg_color="gray", command=popup.destroy).pack(pady=10)
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
        
        for main_cat, subcats in sorted(categories.items()):
            cat_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=2)
            
            cat_container = ctk.CTkFrame(cat_frame, fg_color="transparent")
            cat_container.pack(fill="x")
            cat_container.pack_forget()
            
            ctk.CTkButton(cat_frame, text=f"➤ {main_cat.replace('_', ' ').title()}",
                           anchor="w", fg_color="gray30", hover_color="gray40", height=30,
                           font=ctk.CTkFont(size=13, weight="bold"),
                           command=lambda cc=cat_container: self._toggle_popup_section(cc)).pack(fill="x")
            
            for sub_cat, file_path in sorted(subcats.items()):
                sub_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
                sub_frame.pack(fill="x", padx=(20, 0), pady=1)
                
                sub_container = ctk.CTkFrame(sub_frame, fg_color="transparent")
                sub_container.pack(fill="x", padx=(20, 0))
                sub_container.pack_forget()
                
                ctk.CTkButton(sub_frame, text=f"➤ {sub_cat.replace('_', ' ').title()}",
                               anchor="w", fg_color="gray25", hover_color="gray35", height=26,
                               font=ctk.CTkFont(size=12),
                               command=lambda sc=sub_container: self._toggle_popup_section(sc)).pack(fill="x")
                
                for tag in self._load_tags_from_file(file_path):
                    var = ctk.BooleanVar(value=(tag in current_tags))
                    ctk.CTkCheckBox(sub_container, text=tag, variable=var,
                                     command=lambda t=tag, v=var: self._toggle_tag_selection(t, v)
                                    ).pack(anchor="w", padx=10, pady=2)
        
        def apply():
            new_tags = sorted(list(self._popup_selected_tags))
            self.signature_props[prop_index]['tags'] = new_tags
            self._refresh_signature_props_display()
            popup.destroy()
            self._log(f"✅ Теги обновлены ({len(new_tags)} total)\n")
        
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="✅ Confirm", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                       width=120, command=apply).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="❌ Cancel", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                       width=120, command=popup.destroy).pack(side="left", padx=5)
    
    def _toggle_popup_section(self, container):
        if container.winfo_ismapped():
            self._hide_container(container)
        else:
            container.pack(fill="x", padx=(20, 0))
    
    def _toggle_tag_selection(self, tag, var):
        if var.get():
            self._popup_selected_tags.add(tag)
        else:
            self._popup_selected_tags.discard(tag)
    
    def _open_style_selector(self, rule_index, button_widget):
        popup = ctk.CTkToplevel(self)
        popup.title("Select Hair Style")
        popup.geometry("350x500")
        popup.transient(self)
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
                           command=lambda t=tag: self._select_style(t, rule_index, button_widget, popup)).pack(fill="x", padx=5, pady=1)
        
        ctk.CTkButton(popup, text="Cancel", fg_color="gray", hover_color="darkgray",
                       command=popup.destroy).pack(pady=10)
    
    def _select_style(self, style, rule_index, button_widget, popup):
        self._update_hair_rule_style(rule_index, style)
        dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
        star = " ⭐" if style in dna_styles else ""
        button_widget.configure(text=f"▼ {style}{star}")
        popup.destroy()
    
    def _open_default_style_selector(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Select Default Hair Style")
        popup.geometry("350x500")
        popup.transient(self)
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
                           command=lambda t=tag: self._select_default_style(t, popup)).pack(fill="x", padx=5, pady=1)
        
        ctk.CTkButton(popup, text="Cancel", fg_color="gray", hover_color="darkgray",
                       command=popup.destroy).pack(pady=10)
    
    def _select_default_style(self, style, popup):
        self.hair_rules_data['default'] = style
        if self.hair_default_btn:
            dna_styles = [t['tag'] for t in self.selected_dna_tags if t['category'] == 'Hair Style']
            star = " ⭐" if style in dna_styles else ""
            self.hair_default_btn.configure(text=f"▼ {style}{star}")
        popup.destroy()
    
    def _open_actions_browser(self, rule_index, entry_widget):
        popup = ctk.CTkToplevel(self)
        popup.title("Select Actions")
        popup.geometry("500x600")
        popup.transient(self)
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
        
        if actions_dir.exists():
            for txt_file in sorted(actions_dir.rglob("*.txt")):
                tag_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                tag_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(tag_frame, text=f"➤ {txt_file.stem.replace('_', ' ').title()}",
                              font=ctk.CTkFont(weight="bold"), anchor="w").pack(fill="x", padx=5, pady=2)
                for tag in self._load_tags_from_file(txt_file):
                    var = ctk.BooleanVar(value=(tag in current_actions))
                    ctk.CTkCheckBox(tag_frame, text=tag, variable=var,
                                     command=lambda t=tag, v=var: self._toggle_action_selection(t, v)
                                    ).pack(anchor="w", padx=15, pady=1)
        
        def apply():
            actions_list = sorted(list(self._popup_selected_actions))
            self.hair_rules_data['conditional'][rule_index]['if_action'] = actions_list
            entry_widget.delete(0, "end")
            entry_widget.insert(0, ", ".join(actions_list))
            popup.destroy()
        
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="✅ Confirm", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'],
                       command=apply).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="❌ Cancel", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'],
                       command=popup.destroy).pack(side="left", padx=5)
    
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

    # ════════════════════════════════════════════════════════════════════════════
    # 4.5 Atmosphere
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_lighting_tree(self):
        if self.lighting_tree_frame is None: return
        for w in self.lighting_tree_frame.winfo_children(): w.destroy()
        self.lighting_tag_ui_elements = {}
        
        lighting_dir = self.project_root / "prompt-library" / "07_lighting"
        if not lighting_dir.exists(): return
        
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
        if self.lighting_tree_frame is None: return
        sub_frame = ctk.CTkFrame(self.lighting_tree_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        ctk.CTkButton(sub_frame, text=f"➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                       fg_color="gray30", hover_color="gray40", height=28,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=lambda: self._toggle_lighting_subcategory(sub_cat)).pack(fill="x")
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        self.atmosphere_sections_expanded[f"lighting.{sub_cat}"] = {'frame': tags_frame, 'expanded': False}
        
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
            self.lighting_tag_ui_elements[tag_key] = {'label': tag_row.winfo_children()[0], 'button': action_btn, 'tag': tag}
    
    def _toggle_lighting_subcategory(self, sub_cat):
        key = f"lighting.{sub_cat}"
        if key not in self.atmosphere_sections_expanded: return
        section = self.atmosphere_sections_expanded[key]
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_lighting_tag(self, tag, tag_key):
        if tag_key not in self.lighting_tag_ui_elements: return
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
        if self.selected_lighting_container is None: return
        for w in self.selected_lighting_container.winfo_children(): w.destroy()
        if not self.selected_lighting_tags:
            ctk.CTkLabel(self.selected_lighting_container, text="(No lighting selected)",
                          text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        COLS = 4
        for i, tag in enumerate(self.selected_lighting_tags):
            chip = ctk.CTkFrame(self.selected_lighting_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i//COLS, column=i%COLS, padx=3, pady=3, sticky="ew")
            self.selected_lighting_container.grid_columnconfigure(i%COLS, weight=1)
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
        if self.weather_tree_frame is None: return
        for w in self.weather_tree_frame.winfo_children(): w.destroy()
        self.weather_tag_ui_elements = {}
        
        weather_dir = self.project_root / "prompt-library" / "10_weather"
        if not weather_dir.exists(): return
        
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
        if self.weather_tree_frame is None: return
        sub_frame = ctk.CTkFrame(self.weather_tree_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        ctk.CTkButton(sub_frame, text=f"➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
                       fg_color="gray30", hover_color="gray40", height=28,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=lambda: self._toggle_weather_subcategory(sub_cat)).pack(fill="x")
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        self.atmosphere_sections_expanded[f"weather.{sub_cat}"] = {'frame': tags_frame, 'expanded': False}
        
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
            self.weather_tag_ui_elements[tag_key] = {'label': tag_row.winfo_children()[0], 'button': action_btn, 'tag': tag}
    
    def _toggle_weather_subcategory(self, sub_cat):
        key = f"weather.{sub_cat}"
        if key not in self.atmosphere_sections_expanded: return
        section = self.atmosphere_sections_expanded[key]
        if section['expanded']:
            self._hide_container(section['frame'])
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
        section['expanded'] = not section['expanded']
    
    def _toggle_weather_tag(self, tag, tag_key):
        if tag_key not in self.weather_tag_ui_elements: return
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
        if self.selected_weather_container is None: return
        for w in self.selected_weather_container.winfo_children(): w.destroy()
        if not self.selected_weather_tags:
            ctk.CTkLabel(self.selected_weather_container, text="(No weather selected)",
                          text_color="gray").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        COLS = 4
        for i, tag in enumerate(self.selected_weather_tags):
            chip = ctk.CTkFrame(self.selected_weather_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=i//COLS, column=i%COLS, padx=3, pady=3, sticky="ew")
            self.selected_weather_container.grid_columnconfigure(i%COLS, weight=1)
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

    # ════════════════════════════════════════════════════════════════════════════
    # 4.6 Preview
    # ════════════════════════════════════════════════════════════════════════════
    
    def _refresh_yaml_preview(self):
        if self.yaml_textbox is None or not self.current_profile_name: return
        import yaml
        profile = self._get_default_profile_structure(self.current_profile_name)
        
        # 👇 ПОЛИРОВКА: Сохраняем character данные
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
        header = f"# Character Profile: {self.current_profile_name}\n# Фильтр поверх scene-rules\n\n"
        self.yaml_textbox.delete("1.0", "end")
        self.yaml_textbox.insert("1.0", header + yaml_str)
    
    def _apply_yaml_to_editor(self):
        if self.yaml_textbox is None: return
        import yaml
        try:
            profile = yaml.safe_load(self.yaml_textbox.get("1.0", "end").strip())
            if not profile:
                messagebox.showwarning("Warning", "YAML пустой")
                return
            
            # 👇 ПОЛИРОВКА: Применяем character данные
            character = profile.get('character', {})
            if character:
                self.profile_character_data = character.copy()
                new_name = character.get('name', self.current_profile_name)
                if new_name != self.current_profile_name:
                    # Попытка переименовать файл
                    old_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
                    if not old_path.exists():
                        old_path = self.project_root / "character-profile.yaml"
                    new_path = self.profiles_directory / f"{new_name}.yaml"
                    if old_path.exists() and not new_path.exists():
                        import shutil
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
            for tag_key, ui in self.lighting_tag_ui_elements.items():
                tag = ui['tag']
                if tag in self.selected_lighting_tags:
                    ui['label'].configure(text_color="green")
                    ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
                else:
                    ui['label'].configure(text_color=("gray10", "gray90"))
                    ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
            for tag_key, ui in self.weather_tag_ui_elements.items():
                tag = ui['tag']
                if tag in self.selected_weather_tags:
                    ui['label'].configure(text_color="green")
                    ui['button'].configure(text="-", fg_color=COLORS['danger_red'], hover_color=COLORS['danger_red_hover'])
                else:
                    ui['label'].configure(text_color=("gray10", "gray90"))
                    ui['button'].configure(text="+", fg_color=COLORS['success_green'], hover_color=COLORS['success_green_hover'])
            self._refresh_selected_lighting_display()
            self._refresh_selected_weather_display()
            
            messagebox.showinfo("Success", "YAML применён!")
        except yaml.YAMLError as e:
            messagebox.showerror("YAML Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _copy_yaml_to_clipboard(self):
        if self.yaml_textbox is None: return
        content = self.yaml_textbox.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Info", "YAML пуст")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ YAML скопирован!")

    # ════════════════════════════════════════════════════════════════════════════
    # 5. Load/Save профиля
    # ════════════════════════════════════════════════════════════════════════════
    
    def _load_profile_to_editor(self, profile_name: str):
        """Загружает профиль в редактор с отложенной загрузкой для плавности UI"""
        if self.other_traits_text is None: 
            return
        
        import yaml
        
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        
        if not profile_path.exists():
            messagebox.showerror("Error", f"Profile not found: {profile_name}")
            return
        
        # Загружаем YAML синхронно (это быстро)
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
        
        # 👇 ОТЛОЖЕННАЯ ЗАГРУЗКА: Обновляем UI по частям
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
        
        # Выполняем задачи с задержкой 1мс между ними
        self._batch_load_ui(ui_update_tasks, delay_ms=1)
        
        self._log(f"📥 Загружен профиль: {profile_name}\n")
    
    def _save_profile(self):
        if not self.current_profile_name:
            messagebox.showwarning("Warning", "No profile selected")
            return
        if self.other_traits_text is None: return
        import yaml
        profile_path = self.profiles_directory / f"{self.current_profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = yaml.safe_load(f) or self._get_default_profile_structure(self.current_profile_name)
        else:
            profile = self._get_default_profile_structure(self.current_profile_name)
        
        # 👇 ПОЛИРОВКА: Сохраняем character данные
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
            f.write("# Фильтр поверх scene-rules\n\n")
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        self._log(f"💾 Профиль '{self.current_profile_name}' сохранён\n")
        messagebox.showinfo("Success", f"Profile '{self.current_profile_name}' saved!")

    # ════════════════════════════════════════════════════════════════════════════
    # 6. Утилиты библиотеки тегов
    # ════════════════════════════════════════════════════════════════════════════
    
    def _load_tags_from_library(self, relative_path: str) -> list:
        """Загружает список тегов из файла библиотеки тегов (с кэшированием)"""
        # 👇 Проверяем кэш
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
            
            # 👇 Сохраняем в кэш
            self._tags_cache[relative_path] = tags
            self._log(f"✅ Загружено {len(tags)} тегов из {relative_path}\n")
        except Exception as e:
            self._log(f"❌ Ошибка чтения {relative_path}: {e}\n")
        
        return tags
    
    def _load_tags_from_file(self, file_path) -> list:
        """Загружает теги из конкретного файла (с кэшированием)"""
        # 👇 Преобразуем Path в строку для кэша
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
            
            # 👇 Сохраняем в кэш
            self._tags_cache[cache_key] = tags
        except Exception as e:
            self._log(f"❌ Ошибка чтения {file_path}: {e}\n")
        
        return tags

    def _debounce_ui_update(self, update_type: str, delay_ms: int = 150):
        """Откладывает обновление UI на delay_ms миллисекунд"""
        self._pending_ui_updates.add(update_type)
        
        # Отменяем предыдущий таймер, если он есть
        if self._ui_update_timer:
            self.after_cancel(self._ui_update_timer)
        
        # Создаём новый таймер
        self._ui_update_timer = self.after(delay_ms, self._process_pending_ui_updates)
    
    def _process_pending_ui_updates(self):
        """Обрабатывает все отложенные обновления UI"""
        updates = self._pending_ui_updates.copy()
        self._pending_ui_updates.clear()
        self._ui_update_timer = None
        
        # Выполняем все накопившиеся обновления
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

    # ════════════════════════════════════════════════════════════════════════════
    # 7. GENERATE
    # ════════════════════════════════════════════════════════════════════════════
    
    def _show_force_closure_help(self):
        messagebox.showinfo(
            "⚡ Force Deficit Closure",
            "Этот режим меняет порядок генерации:\n\n"
            "🌿 Natural Mode: сначала локация, потом действие.\n\n"
            "⚡ Aggressive Mode: сначала дефицитное действие, потом локация."
        )

    def _browse_balance_folder(self):
        folder = filedialog.askdirectory(title="Select folder to balance from")
        if folder:
            self.balance_path_entry.delete(0, "end")
            self.balance_path_entry.insert(0, folder)

    def _browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_path_entry.delete(0, "end")
            self.output_path_entry.insert(0, folder)

    def _roll_dice(self):
        self._log("\n🎲 Rolling dice...\n")
        try:
            profile_name = self.character_combobox.get()
            builder = self._init_builder(profile_name)
            available_locs = [k.split('.')[-1] for k in builder.scene_rules.keys() if k.startswith('locations.')]
            import random
            loc = random.choice(available_locs)
            scene = builder.build_scene(loc)
            fixed_traits = builder.full_profile.get('fixed_traits', [])
            prompt = scene.to_prompt(fixed_traits)
            self._log(f"📍 Location: {loc}\n")
            self._log(f"📝 Prompt: {prompt}\n")
        except Exception as e:
            self._log(f"❌ Error: {e}\n")
            messagebox.showerror("Error", str(e))

    def _init_builder(self, profile_name):
        import yaml
        loader = ConfigLoader(project_root=str(self.project_root))
        library = PromptLibrary(library_path=str(self.project_root / "prompt-library"))
        rules = loader.load_scene_rules()
        loader.load_location_types()
        library.load_library()
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_name}")
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        return SceneBuilder(library=library, scene_rules=rules,
                           character_profile=profile, location_types=loader.location_types)

    def _start_generation(self):
        try:
            num_scenes = int(self.scenes_entry.get())
            if num_scenes <= 0:
                raise ValueError("Number must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
            return
        thread = threading.Thread(
            target=self._run_generation,
            args=(self.character_combobox.get(), num_scenes, self.balance_path_entry.get().strip()),
            daemon=True
        )
        thread.start()

    def _run_generation(self, profile_name, num_scenes, balance_folder):
        self.update_idletasks()
        self._log(f"\n{'='*60}\n")
        self._log(f"🚀 Starting generation: {num_scenes} scenes for '{profile_name}'\n")
        try:
            self._log("📦 Initializing engine...\n")
            builder = self._init_builder(profile_name)
            if balance_folder:
                self._log(f"⚖️ Analyzing balance folder: {balance_folder}\n")
                available_locs = [k.split('.')[-1] for k in builder.scene_rules.keys() if k.startswith('locations.')]
                available_acts = [k.split('.')[-1] for k in builder.scene_rules.keys() if k.startswith('actions.')]
                available_weaths = [k.split('.')[-1] for k in builder.scene_rules.keys() if k.startswith('weather.')]
                available_cams = [k.split('.')[-1] for k in builder.scene_rules.keys() if k.startswith('camera.')]
                tracker = CoverageTracker(
                    available_locations=available_locs, available_actions=available_acts,
                    available_weathers=available_weaths, available_cameras=available_cams
                )
                matrix = tracker.scan_folder(balance_folder)
                weights = tracker.calculate_generation_weights(matrix)
                filtered_weights = {}
                if self.balance_locations_var.get(): filtered_weights['location'] = weights.get('location')
                if self.balance_actions_var.get(): filtered_weights['action'] = weights.get('action')
                if self.balance_weather_var.get(): filtered_weights['weather'] = weights.get('weather')
                if self.balance_cameras_var.get(): filtered_weights['camera'] = weights.get('camera')
                builder.generation_weights = filtered_weights
                self._log("✅ Weights calculated.\n")
            output_dir = self.output_path_entry.get().strip()
            if not output_dir:
                raise ValueError("Output directory is not specified")
            self._log(f"🎬 Generating {num_scenes} scenes...\n")
            force_closure = self.force_deficit_closure_var.get()
            if force_closure:
                self._log("⚡ AGGRESSIVE Mode\n")
            else:
                self._log("🌿 NATURAL Mode\n")
            exporter = Exporter(builder, profile_name,
                               generation_weights=builder.generation_weights,
                               log_callback=self._log, verbose=False,
                               force_deficit_closure=force_closure)
            stats = exporter.export_dataset(num_scenes=num_scenes, output_dir=output_dir, create_placeholders=False)
            self._log(f"\n✅ Generation complete! Total: {stats['total_scenes']}\n")
            self._log(f"📂 Saved to: {output_dir}\n")
            messagebox.showinfo("Success", f"Generated {stats['total_scenes']} scenes!\nSaved to:\n{output_dir}")
        except Exception as e:
            self._log(f"\n❌ ERROR: {e}\n")
            import traceback
            self._log(traceback.format_exc())
            messagebox.showerror("Generation Error", str(e))

    # ════════════════════════════════════════════════════════════════════════════
    # 8. ANALYZER
    # ════════════════════════════════════════════════════════════════════════════
    
    def _browse_analyze_folder(self):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            self.analyze_path_entry.delete(0, "end")
            self.analyze_path_entry.insert(0, folder)

    def _auto_fix_deficit(self):
        folder = self.analyze_path_entry.get().strip()
        if not folder:
            messagebox.showwarning("Warning", "Сначала выберите папку")
            return
        self.tabview.set("Generate")
        self.balance_path_entry.delete(0, "end")
        self.balance_path_entry.insert(0, folder)
        self.balance_locations_var.set(True)
        self.balance_actions_var.set(True)
        self.balance_weather_var.set(True)
        self.balance_cameras_var.set(True)
        messagebox.showinfo("Auto-Fix Ready", f"✅ Balance from: {folder}\nНажмите '🚀 Generate Batch'!")

    def _analyzer_log(self, message):
        """Добавляет сообщение в лог анализатора"""
        if self.analyzer_textbox is None: return
        self.analyzer_textbox.insert("end", message)
        self.analyzer_textbox.see("end")
        self._debounced_update()  # 👈 Debounced вместо прямого вызова

    def _clear_analyzer_log(self):
        if self.analyzer_textbox is None: return
        self.analyzer_textbox.delete("1.0", "end")

    def _copy_analyzer_to_clipboard(self):
        if self.analyzer_textbox is None: return
        content = self.analyzer_textbox.get("1.0", "end-1c")
        if not content.strip():
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Скопировано!")

    def _run_analysis(self):
        folder = self.analyze_path_entry.get().strip()
        if not folder:
            messagebox.showwarning("Warning", "Выберите папку")
            return
        threading.Thread(target=self._perform_analysis, args=(folder,), daemon=True).start()

    def _perform_analysis(self, folder):
        self._clear_analyzer_log()
        self._analyzer_log(f"🔍 Сканирование: {folder}\n")
        self._analyzer_log("=" * 70 + "\n\n")
        try:
            loader = ConfigLoader(project_root=str(self.project_root))
            rules = loader.load_scene_rules()
            available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
            available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
            available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
            available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]
            tracker = CoverageTracker(
                available_locations=available_locs, available_actions=available_acts,
                available_weathers=available_weaths, available_cameras=available_cams
            )
            self._analyzer_log("📦 Запуск Coverage Tracker...\n\n")
            matrix = tracker.scan_folder(folder)
            self._format_matrix_for_gui(matrix)
            self._analyzer_log("\n✅ Анализ завершен!\n")
        except Exception as e:
            self._analyzer_log(f"\n❌ Ошибка: {e}\n")
            import traceback
            self._analyzer_log(traceback.format_exc())
            messagebox.showerror("Error", str(e))

    def _format_matrix_for_gui(self, matrix):
        self._analyzer_log(f"📊 МАТРИЦА ПОКРЫТИЯ\n")
        self._analyzer_log(f"📂 Папка: {matrix['folder_path']}\n")
        self._analyzer_log(f"📄 Всего сцен: {matrix['total_scenes']}\n")
        self._analyzer_log("=" * 70 + "\n")
        if matrix["total_scenes"] == 0:
            self._analyzer_log("\n⚠️ Нет валидных промптов.\n")
            return
        for dimension, display_name in {"location": "📍 ЛОКАЦИИ", "action": "🎬 ДЕЙСТВИЯ",
                                          "weather": "🌦️ ПОГОДА", "camera": "📸 КАМЕРЫ"}.items():
            counts = matrix["dimensions"][dimension]
            percentages = matrix["percentages"][dimension]
            if not counts: continue
            self._analyzer_log(f"\n{display_name}:\n" + "-" * 70 + "\n")
            for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                pct = percentages[category]
                bar_length = int(pct / 2)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                status = ""
                if f"{dimension}.{category}" in matrix["status"]["deficits"]:
                    status = " 🔻 ДЕФИЦИТ"
                elif f"{dimension}.{category}" in matrix["status"]["overflows"]:
                    status = " ⚠️ ПЕРЕИЗБЫТОК"
                self._analyzer_log(f"   {category:25s}: {count:3d} ({pct:5.1f}%) [{bar}]{status}\n")
        self._analyzer_log("\n" + "=" * 70 + "\n📋 СВОДКА:\n")
        if matrix["status"]["deficits"]:
            self._analyzer_log(f"   🔻 Дефицит: {', '.join(matrix['status']['deficits'])}\n")
        if matrix["status"]["overflows"]:
            self._analyzer_log(f"   ⚠️ Переизбыток: {', '.join(matrix['status']['overflows'])}\n")
        self._analyzer_log("=" * 70 + "\n")

    # ════════════════════════════════════════════════════════════════════════════
    # 9. LOGGING
    # ════════════════════════════════════════════════════════════════════════════
    
    def _log(self, message):
        """Добавляет сообщение в лог-окно (разрешено копирование, запрещено редактирование)"""
        if not hasattr(self, 'log_textbox') or self.log_textbox is None:
            print(message, end='')
            return
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self._debounced_update()  # 👈 Debounced вместо прямого вызова
    
    def _block_text_edit(self, event):
        if self.log_textbox is None: return "break"
        allowed = ['Control_L', 'Control_R', 'c', 'C', 'a', 'A', 'x', 'X', 'v', 'V',
                   'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next']
        if event.keysym in allowed or event.state == 4:
            return None
        return "break"
    
    def _copy_log_to_clipboard(self):
        if self.log_textbox is None: return
        content = self.log_textbox.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Лог скопирован!")

    def _debounced_update(self, delay_ms: int = 100):
        """Откладывает update_idletasks, вызывая его не чаще 1 раза в delay_ms"""
        # Отменяем предыдущий таймер
        if self._update_timer:
            self.after_cancel(self._update_timer)
        # Создаём новый таймер
        self._update_timer = self.after(delay_ms, self._do_update)

    def _hide_container(self, container):
        """Скрывает контейнер и немедленно обновляет экран (устраняет фантомы)"""
        if container is not None and container.winfo_ismapped():
            self._hide_container(container)
            # Принудительная перерисовка родителя, чтобы избавиться от "призраков"
            try:
                parent = container.master
                if parent:
                    parent.update_idletasks()
            except Exception:
                pass
    
    def _show_container(self, container, padx=(30, 0)):
        """Показывает контейнер"""
        if container is not None and not container.winfo_ismapped():
            container.pack(fill="x", padx=padx)

    def _batch_load_ui(self, tasks: list, delay_ms: int = 1):
        """Выполняет список задач с задержкой между ними для плавной загрузки UI
        
        Args:
            tasks: список функций без аргументов
            delay_ms: задержка между задачами в миллисекундах
        """
        if not tasks:
            return
        
        # Выполняем первую задачу
        task = tasks[0]
        try:
            task()
        except Exception as e:
            self._log(f"❌ Ошибка при загрузке UI: {e}\n")
        
        # Остальные задачи выполняем с задержкой
        if len(tasks) > 1:
            self.after(delay_ms, lambda: self._batch_load_ui(tasks[1:], delay_ms))
    
    def _do_update(self):
        """Выполняет отложенный update_idletasks"""
        self._update_timer = None
        try:
            self.update_idletasks()
        except Exception:
            pass  # Окно могло быть закрыто

    def _on_closing(self):
        """Мгновенное закрытие приложения через os._exit"""
        print("🔄 Закрытие Dataset Composer...")
        os._exit(0)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()