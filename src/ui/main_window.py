import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
from pathlib import Path
import threading

# Добавляем путь к src для импорта наших модулей
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter
from coverage_tracker import CoverageTracker

# Глобальные настройки темы
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):

    # ════════════════════════════════════════════════════════════════════════════
    # 1. ИНИЦИАЛИЗАЦИЯ
    # ════════════════════════════════════════════════════════════════════════════
    
    def __init__(self):
        super().__init__()

        # 1. Настройки главного окна
        self.title("Dataset Composer v1.1 - Character LoRA Pipeline")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 2. Пути проекта
        self.project_root = Path(__file__).parent.parent.parent
        self.output_directory = r"D:\VASILY\MY GENERATION\Test Generations"
        self.profiles_directory = self.project_root / "character-profiles"
        self.profiles_directory.mkdir(exist_ok=True)

        # 3. Переменные состояния
        self.current_profile_name: str | None = None
        
        # DNA состояние
        self.selected_dna_tags: list[dict] = []
        self.dna_tag_ui_elements: dict[str, dict] = {}
        
        # Wardrobe состояние
        self.selected_wardrobe_tags: list[dict] = []
        self.tag_ui_elements: dict[str, dict] = {}
        self.wardrobe_sections_expanded: dict[str, dict] = {}
        
        # === UI элементы Profiles (с полной типизацией) ===
        self.profiles_listbox: ctk.CTkScrollableFrame | None = None
        self.editor_title: ctk.CTkLabel | None = None
        self.editor_tabview: ctk.CTkTabview | None = None
        
        # DNA UI
        self.dna_scroll: ctk.CTkScrollableFrame | None = None
        self.dna_tree_frame: ctk.CTkFrame | None = None
        self.selected_dna_tags_container: ctk.CTkScrollableFrame | None = None
        self.other_traits_text: ctk.CTkTextbox | None = None
        
        # Outfits UI
        self.outfits_scroll: ctk.CTkScrollableFrame | None = None
        self.wardrobe_tree_frame: ctk.CTkFrame | None = None
        self.selected_tags_container: ctk.CTkScrollableFrame | None = None
        
        # Custom UI
        self.custom_scroll: ctk.CTkScrollableFrame | None = None

        # Personality UI
        self.personality_scroll: ctk.CTkScrollableFrame | None = None
        self.personality_tree_frame: ctk.CTkFrame | None = None
        self.prefer_container: ctk.CTkScrollableFrame | None = None
        self.avoid_container: ctk.CTkScrollableFrame | None = None
        
        # Personality состояние
        self.preferred_personality_tags: list[dict] = []
        self.avoided_personality_tags: list[dict] = []
        self.personality_tag_ui_elements: dict[str, dict] = {}

        # 4. Создание системы вкладок
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview.add("Profiles")
        self.tabview.add("Library")
        self.tabview.add("Generate")
        self.tabview.add("Analyzer")
        self.tabview.add("Settings")

        # 5. Создание контента вкладок
        self._create_profiles_tab()
        self._create_library_tab()
        self._create_generate_tab()
        self._create_analyzer_tab()
        self._create_settings_tab()

    def _create_placeholder(self, tab, text):
        """Вспомогательный метод для заглушек"""
        label = ctk.CTkLabel(tab, text=text, font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(expand=True)

    # ════════════════════════════════════════════════════════════════════════════
    # 2. СОЗДАНИЕ ВКЛАДОК (UI)
    # ════════════════════════════════════════════════════════════════════════════
    
    def _create_profiles_tab(self):
        """Создает вкладку управления профилями персонажей"""
        tab = self.tabview.tab("Profiles")
        
        # Двухколоночный layout
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=3)
        tab.grid_rowconfigure(0, weight=1)
        
        # === ЛЕВАЯ ПАНЕЛЬ: Список персонажей ===
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        list_title = ctk.CTkLabel(left_frame, text="📋 Characters",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        list_title.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        self.profiles_listbox = ctk.CTkScrollableFrame(left_frame, width=200)
        self.profiles_listbox.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        buttons_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        create_btn = ctk.CTkButton(buttons_frame, text="➕ New", width=70,
                                     fg_color="green", hover_color="darkgreen",
                                     command=self._create_new_profile)
        create_btn.grid(row=0, column=0, padx=(0, 3))
        
        import_btn = ctk.CTkButton(buttons_frame, text="📥", width=40,
                                    fg_color="gray40", hover_color="gray50",
                                    command=self._import_profile)
        import_btn.grid(row=0, column=1, padx=3)
        
        delete_btn = ctk.CTkButton(buttons_frame, text="🗑️", width=40,
                                    fg_color="#dc2626", hover_color="#991b1b",
                                    command=self._delete_profile)
        delete_btn.grid(row=0, column=2, padx=(3, 0))
        
        # === ПРАВАЯ ПАНЕЛЬ: Редактор с субвкладками ===
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Заголовок + кнопка Save справа
        title_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        self.editor_title = ctk.CTkLabel(title_frame, text="👤 Editing: (no selection)",
                                          font=ctk.CTkFont(size=18, weight="bold"))
        self.editor_title.grid(row=0, column=0, sticky="w")
        
        save_btn = ctk.CTkButton(title_frame, text="💾 Save Profile",
                                   fg_color="green", hover_color="darkgreen",
                                   font=ctk.CTkFont(size=13, weight="bold"),
                                   width=130, height=35,
                                   command=self._save_profile)
        save_btn.grid(row=0, column=1)       
        
        # 👇 ВОССТАНАВЛИВАЕМ: Субвкладки редактора
        self.editor_tabview = ctk.CTkTabview(right_frame)
        self.editor_tabview.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        self.editor_tabview.add("🧬 DNA")
        self.editor_tabview.add("👗 Outfits")
        self.editor_tabview.add("🎭 Personality")
        self.editor_tabview.add("✨ Signature")
        self.editor_tabview.add("🌍 Atmosphere")
        self.editor_tabview.add("✍️ Custom")
        self.editor_tabview.add("📄 Preview")
        
        # DNA вкладка — скроллируемая
        self.dna_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("🧬 DNA"))
        self.dna_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Outfits вкладка — скроллируемая
        self.outfits_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("👗 Outfits"))
        self.outfits_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 👇 Personality вкладка (реальный редактор)
        self.personality_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("🎭 Personality"))
        self.personality_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заглушки для остальных вкладок
        for tab_name in ["✨ Signature", "🌍 Atmosphere", "📄 Preview"]:
            placeholder = ctk.CTkLabel(
                self.editor_tabview.tab(tab_name),
                text=f"{tab_name}\n\nДоступно в следующей итерации.",
                font=ctk.CTkFont(size=14), justify="center"
            )
            placeholder.pack(expand=True)
        
        # 👇 Custom вкладка создаётся отдельно (не заглушка!)
        self.custom_scroll = ctk.CTkScrollableFrame(self.editor_tabview.tab("✍️ Custom"))
        self.custom_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- DNA секция ---
        dna_frame = ctk.CTkFrame(self.dna_scroll)
        dna_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(dna_frame, text="🧬 Character DNA",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.dna_tree_frame = ctk.CTkFrame(dna_frame, fg_color="transparent")
        self.dna_tree_frame.pack(fill="x", padx=20, pady=5)
        
        self._build_dna_tree()
        
        # Selected DNA Tags
        selected_dna_frame = ctk.CTkFrame(dna_frame)
        selected_dna_frame.pack(fill="x", padx=10, pady=(10, 10))
        
        ctk.CTkLabel(selected_dna_frame, text="✅ Selected DNA Tags:",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_dna_tags_container = ctk.CTkScrollableFrame(
            selected_dna_frame,
            fg_color="transparent",
            height=120
        )
        self.selected_dna_tags_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_selected_dna_tags_display()
        
        # --- Custom Traits секция ---
        custom_frame = ctk.CTkFrame(self.custom_scroll)
        custom_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(custom_frame, text="✍️ Custom Traits (Advanced)",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Информативное описание для продвинутых пользователей
        description_frame = ctk.CTkFrame(custom_frame, fg_color="gray20", corner_radius=10)
        description_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(description_frame, 
                      text="⚙️ Для продвинутых пользователей\n\n"
                           "Эта вкладка позволяет добавить произвольные теги, которые не помещаются "
                           "в стандартные категории (DNA, Outfits, Personality).\n\n"
                           "💡 Примеры использования:\n"
                           "• Составные описания внешности: 'long straight light blue hair'\n"
                           "• Редкие теги из библиотеки: 'freckles', 'beauty mark', 'heterochromia'\n"
                           "• Пользовательские модификаторы: 'cinematic lighting', 'film grain'\n\n"
                           "Все теги из этого поля будут добавлены в КАЖДЫЙ промпт вместе с DNA.",
                      text_color="gray80", 
                      justify="left",
                      wraplength=600).pack(anchor="w", padx=15, pady=15)
        
        ctk.CTkLabel(custom_frame, 
                      text="   Введите теги через запятую:",
                      text_color="gray", justify="left").pack(anchor="w", padx=20, pady=(5, 5))
        
        self.other_traits_text = ctk.CTkTextbox(custom_frame, height=150)
        self.other_traits_text.pack(fill="x", padx=20, pady=(0, 10))
        
        # Подсказка внизу
        hint_frame = ctk.CTkFrame(custom_frame, fg_color="transparent")
        hint_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(hint_frame, 
                      text="💾 Не забудьте нажать 'Save Profile' после внесения изменений",
                      text_color="gray60", 
                      font=ctk.CTkFont(size=11, slant="italic")).pack(anchor="w")

        # --- Outfits секция ---
        wardrobe_frame = ctk.CTkFrame(self.outfits_scroll)
        wardrobe_frame.pack(fill="x", pady=5, padx=5)
        self.outfits_scroll.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(wardrobe_frame, text="👗 Wardrobe (Whitelist)",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(wardrobe_frame, 
                      text="   Разверните категории и подкатегории. Используйте [+] для добавления, [-] для удаления.",
                      text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))
        
        self.wardrobe_tree_frame = ctk.CTkFrame(wardrobe_frame, fg_color="transparent")
        self.wardrobe_tree_frame.pack(fill="x", padx=20, pady=5)
        
        self._build_wardrobe_tree()
        
        # Selected Wardrobe Tags
        selected_wardrobe_frame = ctk.CTkFrame(wardrobe_frame)
        selected_wardrobe_frame.pack(fill="x", padx=10, pady=(10, 10))
        
        ctk.CTkLabel(selected_wardrobe_frame, text="✅ Selected Wardrobe Tags:",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        
        self.selected_tags_container = ctk.CTkScrollableFrame(
            selected_wardrobe_frame,
            fg_color="transparent",
            height=120
        )
        self.selected_tags_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_selected_tags_display()

        # --- Personality секция ---
        personality_frame = ctk.CTkFrame(self.personality_scroll)
        personality_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(personality_frame, text="🎭 Personality Filters (Prefer / Avoid)",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(personality_frame, 
                      text="   Разверните категории. Используйте [+] для предпочтений, [-] для запретов.",
                      text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))
        
        self.personality_tree_frame = ctk.CTkFrame(personality_frame, fg_color="transparent")
        self.personality_tree_frame.pack(fill="x", padx=20, pady=5)
        
        self._build_personality_tree()
        
        # Двухколоночный layout для Prefer / Avoid
        summary_frame = ctk.CTkFrame(personality_frame, fg_color="transparent")
        summary_frame.pack(fill="x", padx=10, pady=(10, 10))
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=1)
        
        # Prefer колонка
        prefer_frame = ctk.CTkFrame(summary_frame)
        prefer_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(prefer_frame, text="✅ Preferred:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        self.prefer_container = ctk.CTkScrollableFrame(prefer_frame, fg_color="transparent", height=120)
        self.prefer_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # Avoid колонка
        avoid_frame = ctk.CTkFrame(summary_frame)
        avoid_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(avoid_frame, text="🚫 Avoided:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5, 5))
        self.avoid_container = ctk.CTkScrollableFrame(avoid_frame, fg_color="transparent", height=120)
        self.avoid_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self._refresh_personality_tags_display()
        
        # Заполняем список персонажей
        self._refresh_profiles_list()

    def _create_library_tab(self):
        tab = self.tabview.tab("Library")
        self._create_placeholder(tab, "📚 Library\n\nЗдесь будет редактор тегов и TOML-правил.")

    def _create_generate_tab(self):
        tab = self.tabview.tab("Generate")

        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(2, weight=1)

        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")

        title_label = ctk.CTkLabel(left_frame, text="⚙️ Generation Settings",
                                    font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 10), padx=15, anchor="w")

        char_label = ctk.CTkLabel(left_frame, text="👤 Character Profile:", anchor="w")
        char_label.pack(pady=(10, 0), padx=15, fill="x")

        self.character_combobox = ctk.CTkComboBox(left_frame, values=self._get_available_profiles())
        self.character_combobox.pack(pady=(0, 15), padx=15, fill="x")

        profiles = self._get_available_profiles()
        if profiles:
            self.character_combobox.set(profiles[0])

        scenes_label = ctk.CTkLabel(left_frame, text="🎬 Number of Scenes:", anchor="w")
        scenes_label.pack(pady=(10, 0), padx=15, fill="x")

        self.scenes_entry = ctk.CTkEntry(left_frame, placeholder_text="100")
        self.scenes_entry.insert(0, "30")
        self.scenes_entry.pack(pady=(0, 15), padx=15, fill="x")

        output_label = ctk.CTkLabel(left_frame, text="📂 Save to folder:", anchor="w")
        output_label.pack(pady=(10, 0), padx=15, fill="x")

        output_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        output_frame.pack(pady=(0, 15), padx=15, fill="x")
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_path_entry = ctk.CTkEntry(output_frame)
        self.output_path_entry.insert(0, self.output_directory)
        self.output_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        output_browse_btn = ctk.CTkButton(output_frame, text="Browse", width=80,
                                          command=self._browse_output_folder)
        output_browse_btn.grid(row=0, column=1)

        separator = ctk.CTkFrame(left_frame, height=2)
        separator.pack(pady=15, padx=15, fill="x")

        coverage_label = ctk.CTkLabel(left_frame, text="⚖️ Coverage Engine:",
                                       font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        coverage_label.pack(pady=(0, 10), padx=15, fill="x")

        balance_path_label = ctk.CTkLabel(left_frame, text="Balance from folder:", anchor="w")
        balance_path_label.pack(pady=(0, 5), padx=15, fill="x")

        balance_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        balance_frame.pack(pady=(0, 10), padx=15, fill="x")
        balance_frame.grid_columnconfigure(0, weight=1)

        self.balance_path_entry = ctk.CTkEntry(balance_frame, placeholder_text="Optional...")
        self.balance_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        browse_btn = ctk.CTkButton(balance_frame, text="Browse", width=80,
                                    command=self._browse_balance_folder)
        browse_btn.grid(row=0, column=1)

        self.balance_locations_var = ctk.BooleanVar(value=True)
        self.balance_actions_var = ctk.BooleanVar(value=True)
        self.balance_weather_var = ctk.BooleanVar(value=True)
        self.balance_cameras_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(left_frame, text="Balance Locations",
                        variable=self.balance_locations_var).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Actions",
                        variable=self.balance_actions_var).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Weather",
                        variable=self.balance_weather_var).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Cameras",
                        variable=self.balance_cameras_var).pack(pady=2, padx=15, anchor="w")

        force_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        force_frame.pack(pady=(12, 2), padx=15, fill="x")
        
        self.force_deficit_closure_var = ctk.BooleanVar(value=False)
        force_checkbox = ctk.CTkCheckBox(force_frame, 
                                          text="⚡ Force Deficit Closure",
                                          variable=self.force_deficit_closure_var,
                                          font=ctk.CTkFont(size=13, weight="bold"))
        force_checkbox.pack(side="left")
        
        help_btn = ctk.CTkButton(force_frame, text="?", width=25, height=25,
                                 fg_color="gray40", hover_color="gray50",
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 corner_radius=15,
                                 command=self._show_force_closure_help)
        help_btn.pack(side="left", padx=(8, 0))

        separator2 = ctk.CTkFrame(left_frame, height=2)
        separator2.pack(pady=15, padx=15, fill="x")

        buttons_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        buttons_frame.pack(pady=10, padx=15, fill="x")
        buttons_frame.grid_columnconfigure((0, 1), weight=1)

        roll_dice_btn = ctk.CTkButton(buttons_frame, text="🎲 Roll Dice",
                                       fg_color="gray", hover_color="darkgray",
                                       command=self._roll_dice)
        roll_dice_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        generate_btn = ctk.CTkButton(buttons_frame, text="🚀 Generate Batch",
                                      fg_color="green", hover_color="darkgreen",
                                      command=self._start_generation)
        generate_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)
        
        log_label = ctk.CTkLabel(log_header, text="📝 Generation Log",
                                  font=ctk.CTkFont(size=18, weight="bold"))
        log_label.grid(row=0, column=0, sticky="w")
        
        copy_btn = ctk.CTkButton(log_header, text="📋 Copy All", width=100,
                                  command=self._copy_log_to_clipboard)
        copy_btn.grid(row=0, column=1)

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
        
        title_label = ctk.CTkLabel(left_frame, text="📊 Analyzer Settings",
                                    font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 10), padx=15, anchor="w")
        
        folder_label = ctk.CTkLabel(left_frame, text="📂 Analyze folder:", anchor="w")
        folder_label.pack(pady=(10, 0), padx=15, fill="x")
        
        folder_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        folder_frame.pack(pady=(0, 15), padx=15, fill="x")
        folder_frame.grid_columnconfigure(0, weight=1)
        
        self.analyze_path_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select folder...")
        self.analyze_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        analyze_browse_btn = ctk.CTkButton(folder_frame, text="Browse", width=80,
                                           command=self._browse_analyze_folder)
        analyze_browse_btn.grid(row=0, column=1)
        
        analyze_btn = ctk.CTkButton(left_frame, text="🔍 Analyze Dataset",
                                      fg_color="#2563eb", hover_color="#1d4ed8",
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      height=45,
                                      command=self._run_analysis)
        analyze_btn.pack(pady=20, padx=15, fill="x")
        
        clear_btn = ctk.CTkButton(left_frame, text="🗑️ Clear Log",
                                   fg_color="gray", hover_color="darkgray",
                                   command=self._clear_analyzer_log)
        clear_btn.pack(pady=5, padx=15, fill="x")
        
        autofix_btn = ctk.CTkButton(left_frame, text="⚡ Auto-Fix Deficit",
                                     fg_color="#dc2626", hover_color="#991b1b",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     height=40,
                                     command=self._auto_fix_deficit)
        autofix_btn.pack(pady=(15, 5), padx=15, fill="x")
        
        info_label = ctk.CTkLabel(left_frame, 
                                   text="ℹ️ Анализатор просканирует выбранную папку, "
                                        "прочитает все .txt файлы и построит матрицу "
                                        "покрытия с детекцией дефицита/переизбытка.",
                                   wraplength=280, justify="left", anchor="w",
                                   text_color="gray")
        info_label.pack(pady=(20, 10), padx=15, fill="x")
        
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        log_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)
        
        result_label = ctk.CTkLabel(log_header, text="📈 Coverage Matrix",
                                     font=ctk.CTkFont(size=18, weight="bold"))
        result_label.grid(row=0, column=0, sticky="w")
        
        copy_btn = ctk.CTkButton(log_header, text="📋 Copy Matrix", width=120,
                                  command=self._copy_analyzer_to_clipboard)
        copy_btn.grid(row=0, column=1)
        
        self.analyzer_textbox = ctk.CTkTextbox(right_frame, 
                                                font=ctk.CTkFont(family="Consolas", size=12))
        self.analyzer_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        self._analyzer_log("👋 Добро пожаловать в Dataset Analyzer!\n\n")
        self._analyzer_log("1. Нажмите 'Browse' и выберите папку с промптами\n")
        self._analyzer_log("2. Нажмите '🔍 Analyze Dataset'\n")
        self._analyzer_log("3. Изучите матрицу покрытия ниже\n\n")
        self._analyzer_log("ℹ️ Подсказка: 🔻 ДЕФИЦИТ = нужно догенерировать\n")
        self._analyzer_log("              ⚠️ ПЕРЕИЗБЫТОК = можно удалить лишнее\n")

    def _create_settings_tab(self):
        tab = self.tabview.tab("Settings")
        self._create_placeholder(tab, "⚙️ Settings\n\nПути и интеграции.")

    # ════════════════════════════════════════════════════════════════════════════
    # 3. PROFILES: Управление списком персонажей
    # ════════════════════════════════════════════════════════════════════════════
    
    def _get_available_profiles(self):
        """Сканирует папку character-profiles и возвращает список имен"""
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
        """Обновляет список персонажей в левой панели"""
        if self.profiles_listbox is None: return
        for widget in self.profiles_listbox.winfo_children():
            widget.destroy()
        
        profiles = self._get_available_profiles()
        
        for profile_name in profiles:
            if profile_name == "No profiles found":
                continue
                
            btn = ctk.CTkButton(
                self.profiles_listbox,
                text=f"👤 {profile_name}",
                anchor="w",
                height=35,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray30"),
                command=lambda p=profile_name: self._select_profile(p)
            )
            btn.pack(fill="x", pady=2)

    def _select_profile(self, profile_name):
        """Вызывается при клике на персонажа в списке"""
        self.current_profile_name = profile_name
        if self.editor_title:
            self.editor_title.configure(text=f"👤 Editing: {profile_name}")
        self._load_profile_to_editor(profile_name)

    def _create_new_profile(self):
        """Создает новый профиль персонажа с полной структурой"""
        import yaml
        from tkinter import simpledialog
        
        name = simpledialog.askstring("New Profile", "Enter character name:")
        if not name:
            return
        
        name = name.strip().lower().replace(' ', '_')
        
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
            f.write("# Этот файл служит ФИЛЬТРОМ поверх универсальных scene-rules\n")
            f.write("# Scene Builder будет брать ТОЛЬКО те теги, которые разрешены здесь\n\n")
            
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        self._log(f"➕ Создан новый профиль: {name}\n")
        
        self._refresh_profiles_list()
        self._select_profile(name)
        
        messagebox.showinfo("Success", f"Profile '{name}' created with full structure!")

    def _import_profile(self):
        """Импортирует профиль из внешнего YAML-файла"""
        import shutil
        from pathlib import Path
        
        file_path = filedialog.askopenfilename(
            title="Import Character Profile",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        source = Path(file_path)
        
        name = source.stem.lower().replace(' ', '_')
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
            
            messagebox.showinfo("Success", 
                               f"Profile imported as '{dest.stem}'!\n\n"
                               f"Source: {source.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import profile: {e}")

    def _delete_profile(self):
        """Удаляет выбранный профиль"""
        if not self.current_profile_name:
            messagebox.showwarning("Warning", "No profile selected")
            return
        
        if not messagebox.askyesno("Confirm Delete", 
                                    f"Are you sure you want to delete profile '{self.current_profile_name}'?\n\n"
                                    f"This action cannot be undone!"):
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
            if self.editor_title:
                self.editor_title.configure(text="👤 Editing: (no selection)")
            
            # Очищаем редактор
            if self.other_traits_text:
                self.other_traits_text.delete("1.0", "end")
            
            # Очищаем DNA
            self.selected_dna_tags = []
            self._sync_dna_tag_ui_states()
            self._refresh_selected_dna_tags_display()
            
            # Очищаем wardrobe
            self.selected_wardrobe_tags = []
            self._sync_tag_ui_states()
            self._refresh_selected_tags_display()
            
            self._refresh_profiles_list()
            
            messagebox.showinfo("Success", "Profile deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete profile: {e}")

    def _get_default_profile_structure(self, name: str = "New Character") -> dict:
        """Возвращает полную структуру профиля со всеми секциями"""
        return {
            'character': {
                'name': name,
                'age': 18,
                'archetype': 'custom character'
            },
            'fixed_traits': [],
            'outfit_whitelist': {},
            'underwear_whitelist': {},
            'signature_props': [],
            'hair_rules': {
                'default': 'hair down',
                'conditional': []
            },
            'expression_filter': {
                'prefer': [],
                'avoid': []
            },
            'pose_filter': {
                'prefer': [],
                'avoid': []
            },
            'atmosphere_preferences': {
                'lighting': [],
                'weather': []
            }
        }

    # ════════════════════════════════════════════════════════════════════════════
    # 4. PROFILES: Редактор DNA (древовидная структура)
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_dna_tree(self):
        """Строит дерево категорий для DNA (Hair Style, Hair Color, Eye Color)"""
        if self.dna_tree_frame is None: return
        for widget in self.dna_tree_frame.winfo_children():
            widget.destroy()
        self.dna_tag_ui_elements = {}
        
        categories = [
            ("Hair Style", "01_character/hair/style.txt"),
            ("Hair Color", "01_character/hair/color.txt"),
            ("Eye Color", "01_character/eyes/color.txt"),
        ]
        
        for cat_name, cat_file in categories:
            self._create_dna_category(cat_name, cat_file)
    
    def _create_dna_category(self, cat_name: str, cat_file: str):
        """Создаёт категорию DNA с прокручиваемым списком тегов"""
        if self.dna_tree_frame is None: return
        cat_frame = ctk.CTkFrame(self.dna_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        header_btn = ctk.CTkButton(
            cat_frame,
            text=f"➤ {cat_name}",
            anchor="w",
            fg_color="gray30",
            hover_color="gray40",
            height=30,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._toggle_dna_category(cat_name)
        )
        header_btn.pack(fill="x")
        
        tags_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        
        key = f"dna.{cat_name}"
        self.wardrobe_sections_expanded[key] = {
            'frame': tags_frame,
            'expanded': False
        }
        
        tags = self._load_tags_from_library(cat_file)
        
        for tag in tags:
            tag_key = f"dna::{cat_name}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(
                tag_row,
                text=f"  • {tag.replace('_', ' ')}",
                anchor="w",
                width=250
            )
            tag_label.pack(side="left", padx=(5, 0))
            
            action_btn = ctk.CTkButton(
                tag_row,
                text="+",
                width=30,
                height=25,
                fg_color="green",
                hover_color="darkgreen",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda t=tag, cn=cat_name, tk=tag_key: self._toggle_dna_tag(t, cn, tk)
            )
            action_btn.pack(side="right", padx=(0, 5))
            
            self.dna_tag_ui_elements[tag_key] = {
                'label': tag_label,
                'button': action_btn,
                'tag': tag,
                'category': cat_name
            }
    
    def _toggle_dna_category(self, cat_name: str):
        """Разворачивает/сворачивает категорию DNA"""
        key = f"dna.{cat_name}"
        if key not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[key]
        if section['expanded']:
            section['frame'].pack_forget()
            section['expanded'] = False
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
            section['expanded'] = True
    
    def _toggle_dna_tag(self, tag: str, category: str, tag_key: str):
        """Переключает состояние DNA-тега"""
        if tag_key not in self.dna_tag_ui_elements: return
        tag_entry = {'tag': tag, 'category': category}
        ui = self.dna_tag_ui_elements[tag_key]
        
        if tag_entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(tag_entry)
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color="green", hover_color="darkgreen")
            self._log(f"➖ Удалён DNA-тег: {tag}\n")
        else:
            self.selected_dna_tags.append(tag_entry)
            ui['label'].configure(text_color="green")
            ui['button'].configure(text="-", fg_color="#dc2626", hover_color="#991b1b")
            self._log(f"➕ Добавлен DNA-тег: {tag}\n")
        
        self._refresh_selected_dna_tags_display()
    
    def _refresh_selected_dna_tags_display(self):
        """Обновляет отображение выбранных DNA-тегов"""
        if self.selected_dna_tags_container is None: return
        for widget in self.selected_dna_tags_container.winfo_children():
            widget.destroy()
        
        if not self.selected_dna_tags:
            empty_label = ctk.CTkLabel(
                self.selected_dna_tags_container,
                text="(No DNA tags selected — разверните категории и нажмите [+])",
                text_color="gray"
            )
            empty_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        
        COLS = 4
        for i, tag_entry in enumerate(self.selected_dna_tags):
            row = i // COLS
            col = i % COLS
            
            chip = ctk.CTkFrame(self.selected_dna_tags_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self.selected_dna_tags_container.grid_columnconfigure(col, weight=1)
            
            tag_label = ctk.CTkLabel(
                chip,
                text=f"  {tag_entry['tag'].replace('_', ' ')}  ",
                font=ctk.CTkFont(size=11)
            )
            tag_label.pack(side="left", padx=(8, 5), pady=4)
            
            remove_btn = ctk.CTkButton(
                chip,
                text="×",
                width=22,
                height=22,
                fg_color="transparent",
                hover_color="#dc2626",
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda te=tag_entry: self._remove_dna_tag_from_chip(te)
            )
            remove_btn.pack(side="right", padx=(0, 5), pady=2)
    
    def _remove_dna_tag_from_chip(self, tag_entry: dict):
        """Удаляет DNA-тег при клике на ×"""
        if tag_entry not in self.selected_dna_tags: return
        if tag_entry in self.selected_dna_tags:
            self.selected_dna_tags.remove(tag_entry)
            
            tag_key = f"dna::{tag_entry['category']}::{tag_entry['tag']}"
            if tag_key in self.dna_tag_ui_elements:
                ui = self.dna_tag_ui_elements[tag_key]
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color="green", hover_color="darkgreen")
            
            self._refresh_selected_dna_tags_display()
            self._log(f"➖ Удалён DNA-тег: {tag_entry['tag']}\n")
    
    def _sync_dna_tag_ui_states(self):
        """Синхронизирует UI DNA-тегов с текущим списком selected"""
        if not self.dna_tag_ui_elements: return
        for tag_key, ui in self.dna_tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'category': ui['category']}
            if tag_entry in self.selected_dna_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color="#dc2626", hover_color="#991b1b")
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color="green", hover_color="darkgreen")

    # ════════════════════════════════════════════════════════════════════════════
    # 6. PROFILES: Редактор Outfits/Wardrobe (древовидная структура)
    # ════════════════════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════════════════════
    # 4.5 PROFILES: Редактор Personality (трёхуровневая структура)
    # ════════════════════════════════════════════════════════════════════════════
    
    def _build_personality_tree(self):
        """Строит трёхуровневое дерево для Personality (Категория → Подкатегория → Теги)"""
        if self.personality_tree_frame is None: return
        for widget in self.personality_tree_frame.winfo_children():
            widget.destroy()
        self.personality_tag_ui_elements = {}
        
        categories = [
            ("Expressions", "05_expression"),
            ("Poses", "03_pose")
        ]
        
        for cat_name, cat_dir in categories:
            self._create_personality_category(cat_name, cat_dir)
    
    def _create_personality_category(self, cat_name: str, cat_dir: str):
        """Уровень 1: Главная категория (разворачивается, показывает подкатегории)"""
        if self.personality_tree_frame is None: return
        
        cat_frame = ctk.CTkFrame(self.personality_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        # Заголовок категории
        header_btn = ctk.CTkButton(
            cat_frame, text=f"➤ {cat_name}", anchor="w",
            fg_color="gray30", hover_color="gray40", height=30,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._toggle_personality_category(cat_name)
        )
        header_btn.pack(fill="x")
        
        # 👇 Контейнер для подкатегорий (изначально скрыт) — обычный Frame, не Scrollable!
        subcats_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        subcats_frame.pack(fill="x", padx=(20, 0))
        subcats_frame.pack_forget()
        
        key = f"personality.{cat_name}"
        self.wardrobe_sections_expanded[key] = {
            'frame': subcats_frame,
            'expanded': False
        }
        
        # Группируем файлы по подпапкам
        dir_path = self.project_root / "prompt-library" / cat_dir
        if not dir_path.exists():
            self._log(f"⚠️ Папка не найдена: {dir_path}\n")
            return
        
        subcats = {}
        for txt_file in sorted(dir_path.rglob("*.txt")):
            parts = txt_file.relative_to(dir_path).parts
            if len(parts) == 1:
                # Файл в корне категории: 05_expression/mood.txt → "mood"
                sub_cat = parts[0].replace('.txt', '')
            elif len(parts) >= 2:
                # Файл в подпапке: 03_pose/arms/arms.txt → "arms"
                sub_cat = parts[0]
            else:
                continue
            subcats[sub_cat] = txt_file
        
        # Создаём подкатегории (Уровень 2)
        for sub_cat, file_path in sorted(subcats.items()):
            self._create_personality_subcategory(subcats_frame, cat_name, sub_cat, file_path)
    
    def _create_personality_subcategory(self, parent_frame, cat_name: str, sub_cat: str, file_path):
        """Уровень 2: Подкатегория (разворачивается, показывает теги)"""
        sub_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        
        # Заголовок подкатегории
        sub_header_btn = ctk.CTkButton(
            sub_frame, text=f"  ➤ {sub_cat.replace('_', ' ').title()}", anchor="w",
            fg_color="gray25", hover_color="gray35", height=26,
            font=ctk.CTkFont(size=12),
            command=lambda: self._toggle_personality_subcategory(cat_name, sub_cat)
        )
        sub_header_btn.pack(fill="x")
        
        # 👇 Контейнер для тегов — обычный Frame, НЕ Scrollable (избегаем ошибки menu window)
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        
        key = f"personality.{cat_name}.{sub_cat}"
        self.wardrobe_sections_expanded[key] = {
            'frame': tags_frame,
            'expanded': False
        }
        
        # Загружаем теги
        tags = self._load_tags_from_file(file_path)
        
        # Создаём строки тегов с кнопками [+] и [-]
        for tag in tags:
            tag_key = f"personality::{cat_name}::{sub_cat}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(
                tag_row,
                text=f"    • {tag.replace('_', ' ')}",
                anchor="w", width=220
            )
            tag_label.pack(side="left", padx=(5, 0))
            
            # Кнопка [-] Avoid (справа)
            avoid_btn = ctk.CTkButton(
                tag_row, text="-", width=25, height=22,
                fg_color="#dc2626", hover_color="#991b1b",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda t=tag, cn=cat_name, sc=sub_cat, tk=tag_key: 
                    self._toggle_personality_tag(t, cn, sc, tk, 'avoid')
            )
            avoid_btn.pack(side="right", padx=(0, 2))
            
            # Кнопка [+] Prefer (слева от Avoid)
            prefer_btn = ctk.CTkButton(
                tag_row, text="+", width=25, height=22,
                fg_color="green", hover_color="darkgreen",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda t=tag, cn=cat_name, sc=sub_cat, tk=tag_key: 
                    self._toggle_personality_tag(t, cn, sc, tk, 'prefer')
            )
            prefer_btn.pack(side="right", padx=(0, 2))
            
            self.personality_tag_ui_elements[tag_key] = {
                'label': tag_label,
                'prefer_btn': prefer_btn,
                'avoid_btn': avoid_btn,
                'tag': tag,
                'category': cat_name,
                'subcategory': sub_cat
            }
    
    def _toggle_personality_category(self, cat_name: str):
        """Разворачивает/сворачивает главную категорию Personality"""
        key = f"personality.{cat_name}"
        if key not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[key]
        if section['expanded']:
            section['frame'].pack_forget()
            section['expanded'] = False
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
            section['expanded'] = True
    
    def _toggle_personality_subcategory(self, cat_name: str, sub_cat: str):
        """Разворачивает/сворачивает подкатегорию Personality"""
        key = f"personality.{cat_name}.{sub_cat}"
        if key not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[key]
        if section['expanded']:
            section['frame'].pack_forget()
            section['expanded'] = False
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
            section['expanded'] = True
    
    def _toggle_personality_tag(self, tag: str, category: str, subcategory: str, 
                                 tag_key: str, action: str):
        """Переключает состояние тега: prefer / avoid / none"""
        tag_entry = {'tag': tag, 'category': category, 'subcategory': subcategory}
        
        # Проверяем, где тег сейчас
        was_in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
        was_in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
        
        # Очищаем предыдущее состояние (тег может быть только в одном списке)
        self.preferred_personality_tags = [t for t in self.preferred_personality_tags if t['tag'] != tag]
        self.avoided_personality_tags = [t for t in self.avoided_personality_tags if t['tag'] != tag]
        
        # Добавляем в новый список (если это не повторный клик для снятия)
        if action == 'prefer' and not was_in_prefer:
            self.preferred_personality_tags.append(tag_entry)
        elif action == 'avoid' and not was_in_avoid:
            self.avoided_personality_tags.append(tag_entry)
        
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()
    
    def _sync_personality_ui_states(self):
        """Синхронизирует цвета и кнопки тегов Personality"""
        if not self.personality_tag_ui_elements: return
        for tag_key, ui in self.personality_tag_ui_elements.items():
            tag = ui['tag']
            in_prefer = any(t['tag'] == tag for t in self.preferred_personality_tags)
            in_avoid = any(t['tag'] == tag for t in self.avoided_personality_tags)
            
            if in_prefer:
                ui['label'].configure(text_color="green")
                ui['prefer_btn'].configure(text="✓", fg_color="darkgreen", hover_color="darkgreen")
                ui['avoid_btn'].configure(text="-", fg_color="#dc2626", hover_color="#991b1b")
            elif in_avoid:
                ui['label'].configure(text_color="#dc2626")
                ui['prefer_btn'].configure(text="+", fg_color="green", hover_color="darkgreen")
                ui['avoid_btn'].configure(text="✓", fg_color="#991b1b", hover_color="#991b1b")
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['prefer_btn'].configure(text="+", fg_color="green", hover_color="darkgreen")
                ui['avoid_btn'].configure(text="-", fg_color="#dc2626", hover_color="#991b1b")
    
    def _refresh_personality_tags_display(self):
        """Обновляет чипы в блоках Prefer и Avoid"""
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
                                    font=ctk.CTkFont(size=11), text_color=color)
                lbl.pack(side="left", padx=(8, 5), pady=4)
                
                def remove(t=entry['tag']):
                    self.preferred_personality_tags = [x for x in self.preferred_personality_tags if x['tag'] != t]
                    self.avoided_personality_tags = [x for x in self.avoided_personality_tags if x['tag'] != t]
                    self._sync_personality_ui_states()
                    self._refresh_personality_tags_display()
                
                btn = ctk.CTkButton(chip, text="×", width=20, height=20, fg_color="transparent",
                                    hover_color="#dc2626", text_color="white",
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    command=remove)
                btn.pack(side="right", padx=(0, 5), pady=2)
        
        build_chips(self.prefer_container, self.preferred_personality_tags, "green")
        build_chips(self.avoid_container, self.avoided_personality_tags, "#dc2626")

    # ════════════════════════════════════════════════════════════════════════════
    # 6. PROFILES: Редактор Outfits/Wardrobe (древовидная структура)
    # ════════════════════════════════════════════════════════════════════════════
    
    def _load_wardrobe_categories(self) -> list:
        """Сканирует папку 02_clothing/ и возвращает список (display_name, relative_path)"""
        clothing_dir = self.project_root / "prompt-library" / "02_clothing"
        categories = []
        
        if not clothing_dir.exists():
            self._log(f"⚠️ Папка не найдена: {clothing_dir}\n")
            return categories
        
        for txt_file in sorted(clothing_dir.rglob("*.txt")):
            rel_path = str(txt_file.relative_to(self.project_root / "prompt-library"))
            parts = txt_file.relative_to(clothing_dir).parts
            display_name = " / ".join(p.replace('.txt', '').replace('_', ' ').title() for p in parts)
            categories.append((display_name, rel_path))
        
        self._log(f"✅ Загружено {len(categories)} категорий одежды\n")
        return categories

    def _build_wardrobe_tree(self):
        """Строит двухуровневое дерево категорий одежды"""
        if self.wardrobe_tree_frame is None: return
        for widget in self.wardrobe_tree_frame.winfo_children():
            widget.destroy()
        self.tag_ui_elements = {}
        
        clothing_dir = self.project_root / "prompt-library" / "02_clothing"
        if not clothing_dir.exists():
            self._log(f"⚠️ Папка не найдена: {clothing_dir}\n")
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
        
        for main_cat, subcats in sorted(categories.items()):
            self._create_wardrobe_category(main_cat, subcats)
    
    def _create_wardrobe_category(self, main_cat: str, subcats: dict):
        """Уровень 1: Главная категория (разворачивается)"""
        if self.wardrobe_tree_frame is None: return
        cat_frame = ctk.CTkFrame(self.wardrobe_tree_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=2)
        
        header_btn = ctk.CTkButton(
            cat_frame,
            text=f"➤ {main_cat.replace('_', ' ').title()}",
            anchor="w",
            fg_color="gray30",
            hover_color="gray40",
            height=30,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._toggle_category(main_cat)
        )
        header_btn.pack(fill="x")
        
        subcats_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
        subcats_frame.pack(fill="x", padx=(20, 0))
        subcats_frame.pack_forget()
        
        self.wardrobe_sections_expanded[main_cat] = {
            'frame': subcats_frame,
            'expanded': False
        }
        
        for sub_cat, file_path in subcats.items():
            self._create_wardrobe_subcategory(subcats_frame, main_cat, sub_cat, file_path)
    
    def _create_wardrobe_subcategory(self, parent_frame, main_cat: str, sub_cat: str, file_path):
        """Уровень 2: Подкатегория (тоже разворачивается)"""
        sub_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        sub_frame.pack(fill="x", pady=1)
        
        sub_header_btn = ctk.CTkButton(
            sub_frame,
            text=f"  ➤ {sub_cat.replace('_', ' ').title()}",
            anchor="w",
            fg_color="gray25",
            hover_color="gray35",
            height=26,
            font=ctk.CTkFont(size=12),
            command=lambda: self._toggle_subcategory(main_cat, sub_cat)
        )
        sub_header_btn.pack(fill="x")
        
        tags_frame = ctk.CTkFrame(sub_frame, fg_color="transparent")
        tags_frame.pack(fill="x", padx=(20, 0))
        tags_frame.pack_forget()
        
        key = f"{main_cat}.{sub_cat}"
        self.wardrobe_sections_expanded[key] = {
            'frame': tags_frame,
            'expanded': False
        }
        
        tags = self._load_tags_from_file(file_path)
        
        for tag in tags:
            tag_key = f"{sub_cat}::{tag}"
            tag_row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(
                tag_row,
                text=f"    • {tag.replace('_', ' ')}",
                anchor="w",
                width=250
            )
            tag_label.pack(side="left", padx=(5, 0))
            
            action_btn = ctk.CTkButton(
                tag_row,
                text="+",
                width=30,
                height=25,
                fg_color="green",
                hover_color="darkgreen",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda t=tag, sc=sub_cat, tk=tag_key: self._toggle_wardrobe_tag(t, sc, tk)
            )
            action_btn.pack(side="right", padx=(0, 5))
            
            self.tag_ui_elements[tag_key] = {
                'label': tag_label,
                'button': action_btn,
                'tag': tag,
                'subcategory': sub_cat
            }
    
    def _toggle_category(self, main_cat: str):
        """Разворачивает/сворачивает главную категорию"""
        if main_cat not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[main_cat]
        if section['expanded']:
            section['frame'].pack_forget()
            section['expanded'] = False
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
            section['expanded'] = True
    
    def _toggle_subcategory(self, main_cat: str, sub_cat: str):
        """Разворачивает/сворачивает подкатегорию"""
        key = f"{main_cat}.{sub_cat}"
        if key not in self.wardrobe_sections_expanded: return
        section = self.wardrobe_sections_expanded[key]
        if section['expanded']:
            section['frame'].pack_forget()
            section['expanded'] = False
        else:
            section['frame'].pack(fill="x", padx=(20, 0))
            section['expanded'] = True
    
    def _toggle_wardrobe_tag(self, tag: str, subcategory: str, tag_key: str):
        """Переключает состояние тега: добавляет/удаляет с визуальным откликом"""
        if tag_key not in self.tag_ui_elements: return
        tag_entry = {'tag': tag, 'subcategory': subcategory}
        ui = self.tag_ui_elements[tag_key]
        
        if tag_entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(tag_entry)
            ui['label'].configure(text_color=("gray10", "gray90"))
            ui['button'].configure(text="+", fg_color="green", hover_color="darkgreen")
            self._log(f"➖ Удалён тег: {tag}\n")
        else:
            self.selected_wardrobe_tags.append(tag_entry)
            ui['label'].configure(text_color="green")
            ui['button'].configure(text="-", fg_color="#dc2626", hover_color="#991b1b")
            self._log(f"➕ Добавлен тег: {tag}\n")
        
        self._refresh_selected_tags_display()
    
    def _refresh_selected_tags_display(self):
        """Обновляет отображение выбранных тегов с grid-раскладкой и прокруткой"""
        if self.selected_tags_container is None: return
        for widget in self.selected_tags_container.winfo_children():
            widget.destroy()
        
        if not self.selected_wardrobe_tags:
            empty_label = ctk.CTkLabel(
                self.selected_tags_container,
                text="(No tags selected — разверните категории и нажмите [+])",
                text_color="gray"
            )
            empty_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            return
        
        COLS = 4
        for i, tag_entry in enumerate(self.selected_wardrobe_tags):
            row = i // COLS
            col = i % COLS
            
            chip = ctk.CTkFrame(self.selected_tags_container, fg_color="gray30", corner_radius=15)
            chip.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self.selected_tags_container.grid_columnconfigure(col, weight=1)
            
            tag_label = ctk.CTkLabel(
                chip,
                text=f"  {tag_entry['tag'].replace('_', ' ')}  ",
                font=ctk.CTkFont(size=11)
            )
            tag_label.pack(side="left", padx=(8, 5), pady=4)
            
            remove_btn = ctk.CTkButton(
                chip,
                text="×",
                width=22,
                height=22,
                fg_color="transparent",
                hover_color="#dc2626",
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda te=tag_entry: self._remove_tag_from_chip(te)
            )
            remove_btn.pack(side="right", padx=(0, 5), pady=2)
    
    def _remove_tag_from_chip(self, tag_entry: dict):
        """Удаляет тег при клике на × в чипе"""
        if tag_entry not in self.selected_wardrobe_tags: return
        if tag_entry in self.selected_wardrobe_tags:
            self.selected_wardrobe_tags.remove(tag_entry)
            
            tag_key = f"{tag_entry['subcategory']}::{tag_entry['tag']}"
            if tag_key in self.tag_ui_elements:
                ui = self.tag_ui_elements[tag_key]
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color="green", hover_color="darkgreen")
            
            self._refresh_selected_tags_display()
            self._log(f"➖ Удалён тег: {tag_entry['tag']}\n")
    
    def _sync_tag_ui_states(self):
        """Синхронизирует визуальное состояние всех тегов с текущим списком selected"""
        if not self.tag_ui_elements: return
        for tag_key, ui in self.tag_ui_elements.items():
            tag_entry = {'tag': ui['tag'], 'subcategory': ui['subcategory']}
            if tag_entry in self.selected_wardrobe_tags:
                ui['label'].configure(text_color="green")
                ui['button'].configure(text="-", fg_color="#dc2626", hover_color="#991b1b")
            else:
                ui['label'].configure(text_color=("gray10", "gray90"))
                ui['button'].configure(text="+", fg_color="green", hover_color="darkgreen")

    # ════════════════════════════════════════════════════════════════════════════
    # 6. PROFILES: Загрузка и сохранение профиля
    # ════════════════════════════════════════════════════════════════════════════
    
    def _load_profile_to_editor(self, profile_name: str):
        """Загружает данные профиля в редактор"""
        if self.other_traits_text is None: 
            return
        import yaml
        
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            profile_path = self.project_root / "character-profile.yaml"
        
        if not profile_path.exists():
            messagebox.showerror("Error", f"Profile file not found: {profile_name}")
            return
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        
        # === DNA ===
        self.selected_dna_tags = []
        
        fixed_traits = profile.get('fixed_traits', [])
        all_dna_tags = {ui['tag']: ui['category'] for ui in self.dna_tag_ui_elements.values()}
        
        other_traits = []
        for trait in fixed_traits:
            if trait in all_dna_tags:
                self.selected_dna_tags.append({
                    'tag': trait,
                    'category': all_dna_tags[trait]
                })
            else:
                other_traits.append(trait)
        
        self._sync_dna_tag_ui_states()
        self._refresh_selected_dna_tags_display()
        
        self.other_traits_text.delete("1.0", "end")
        if other_traits:
            self.other_traits_text.insert("1.0", ", ".join(other_traits))
        
        # === WARDROBE ===
        self.selected_wardrobe_tags = []
        
        outfit_whitelist = profile.get('outfit_whitelist', {})
        for outfit_name, subcats in outfit_whitelist.items():
            if isinstance(subcats, dict):
                for subcategory, tags in subcats.items():
                    if isinstance(tags, list):
                        for tag in tags:
                            self.selected_wardrobe_tags.append({
                                'tag': tag,
                                'subcategory': subcategory
                            })
        
        self._sync_tag_ui_states()
        self._refresh_selected_tags_display()
        
        # === PERSONALITY ===
        self.preferred_personality_tags = []
        self.avoided_personality_tags = []
        
        expr = profile.get('expression_filter', {})
        for t in expr.get('prefer', []): self.preferred_personality_tags.append({'tag': t, 'category': 'Expressions'})
        for t in expr.get('avoid', []): self.avoided_personality_tags.append({'tag': t, 'category': 'Expressions'})
        
        pose = profile.get('pose_filter', {})
        for t in pose.get('prefer', []): self.preferred_personality_tags.append({'tag': t, 'category': 'Poses'})
        for t in pose.get('avoid', []): self.avoided_personality_tags.append({'tag': t, 'category': 'Poses'})
        
        self._sync_personality_ui_states()
        self._refresh_personality_tags_display()

        self.current_profile_name = profile_name
        self._log(f"📥 Загружен профиль: {profile_name} "
                  f"({len(self.selected_dna_tags)} DNA, {len(self.selected_wardrobe_tags)} wardrobe)\n")
    
    def _save_profile(self):
        """Сохраняет текущий профиль в YAML-файл, сохраняя все секции"""
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
        
        # === Собираем fixed_traits ===
        selected_traits = [entry['tag'] for entry in self.selected_dna_tags]
        
        other_text = self.other_traits_text.get("1.0", "end").strip()
        if other_text:
            other_traits = [t.strip() for t in other_text.split(',') if t.strip()]
            selected_traits.extend(other_traits)
        
        profile['fixed_traits'] = selected_traits
        
        # === Собираем wardrobe ===
        wardrobe_by_subcat = {}
        for entry in self.selected_wardrobe_tags:
            subcat = entry['subcategory']
            tag = entry['tag']
            if subcat not in wardrobe_by_subcat:
                wardrobe_by_subcat[subcat] = []
            wardrobe_by_subcat[subcat].append(tag)
        
        profile['outfit_whitelist'] = {'default': wardrobe_by_subcat}

        # === Собираем personality ===
        profile['expression_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t['category'] == 'Expressions'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t['category'] == 'Expressions']
        }
        profile['pose_filter'] = {
            'prefer': [t['tag'] for t in self.preferred_personality_tags if t['category'] == 'Poses'],
            'avoid': [t['tag'] for t in self.avoided_personality_tags if t['category'] == 'Poses']
        }
        
        # === Сохраняем ===
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(f"# Character Profile: {self.current_profile_name}\n")
            f.write("# Этот файл служит ФИЛЬТРОМ поверх универсальных scene-rules\n")
            f.write("# Scene Builder будет брать ТОЛЬКО те теги, которые разрешены здесь\n\n")
            
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        self._log(f"💾 Профиль '{self.current_profile_name}' сохранён "
                  f"({len(selected_traits)} DNA, {len(self.selected_wardrobe_tags)} wardrobe)\n")
        messagebox.showinfo("Success", 
                           f"Profile '{self.current_profile_name}' saved!\n\n"
                           f"DNA tags: {len(selected_traits)}\n"
                           f"Wardrobe tags: {len(self.selected_wardrobe_tags)}")

    # ════════════════════════════════════════════════════════════════════════════
    # 7. PROFILES: Общие утилиты для работы с библиотекой тегов
    # ════════════════════════════════════════════════════════════════════════════
    
    def _load_tags_from_library(self, relative_path: str) -> list:
        """Загружает список тегов из файла библиотеки тегов"""
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
            
            self._log(f"✅ Загружено {len(tags)} тегов из {relative_path}\n")
        except Exception as e:
            self._log(f"❌ Ошибка чтения {relative_path}: {e}\n")
        
        return tags
    
    def _load_tags_from_file(self, file_path) -> list:
        """Загружает теги из конкретного файла"""
        tags = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        tags.append(line)
        except Exception as e:
            self._log(f"❌ Ошибка чтения {file_path}: {e}\n")
        return tags

    # ════════════════════════════════════════════════════════════════════════════
    # 8. GENERATE: Управление генерацией
    # ════════════════════════════════════════════════════════════════════════════
    
    def _show_force_closure_help(self):
        """Показывает описание агрессивного режима"""
        messagebox.showinfo(
            "⚡ Force Deficit Closure",
            "Этот режим меняет порядок генерации сцен:\n\n"
            
            "🌿 Natural Mode (выключено):\n"
            "Сначала выбирается локация, затем из её предпочтительных действий "
            "берётся конкретное действие. Это даёт естественные, кинематографичные сцены.\n\n"
            
            "⚡ Aggressive Mode (включено):\n"
            "Если в датасете есть дефицит действий, программа сначала выбирает "
            "ДЕФИЦИТНОЕ ДЕЙСТВИЕ, а затем подбирает под него подходящую локацию "
            "(даже если это действие там не является предпочтительным).\n\n"
            
            "Рекомендуется включать при добалансировке датасета после курирования, "
            "чтобы гарантированно закрыть дыры в покрытии."
        )

    def _browse_balance_folder(self):
        """Открывает диалог выбора папки для балансировки"""
        folder = filedialog.askdirectory(title="Select folder to balance from")
        if folder:
            self.balance_path_entry.delete(0, "end")
            self.balance_path_entry.insert(0, folder)

    def _browse_output_folder(self):
        """Открывает диалог выбора папки для сохранения"""
        folder = filedialog.askdirectory(title="Select output folder for generated prompts")
        if folder:
            self.output_path_entry.delete(0, "end")
            self.output_path_entry.insert(0, folder)

    def _roll_dice(self):
        """Генерирует одну тестовую сцену"""
        self._log("\n🎲 Rolling dice...\n")
        try:
            profile_name = self.character_combobox.get()
            builder = self._init_builder(profile_name)

            available_locs = [k.split('.')[-1] for k in builder.scene_rules.keys()
                             if k.startswith('locations.')]
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
        """Инициализирует SceneBuilder для выбранного профиля"""
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

        builder = SceneBuilder(
            library=library,
            scene_rules=rules,
            character_profile=profile,
            location_types=loader.location_types
        )
        return builder

    def _start_generation(self):
        """Запускает генерацию батча в отдельном потоке (чтобы не блокировать UI)"""
        try:
            num_scenes = int(self.scenes_entry.get())
            if num_scenes <= 0:
                raise ValueError("Number must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of scenes")
            return

        profile_name = self.character_combobox.get()
        balance_folder = self.balance_path_entry.get().strip()

        thread = threading.Thread(
            target=self._run_generation,
            args=(profile_name, num_scenes, balance_folder),
            daemon=True
        )
        thread.start()

    def _run_generation(self, profile_name, num_scenes, balance_folder):
        """Основная логика генерации (выполняется в фоне)"""
        self._log(f"\n{'='*60}\n")
        self._log(f"🚀 _run_generation STARTED\n")
        self._log(f"   num_scenes = {num_scenes}\n")
        self._log(f"   profile_name = {profile_name}\n")
        self._log(f"🚀 Starting generation: {num_scenes} scenes for '{profile_name}'\n")

        try:
            self._log("📦 Initializing engine...\n")
            builder = self._init_builder(profile_name)

            weights = None
            if balance_folder:
                self._log(f"⚖️ Analyzing balance folder: {balance_folder}\n")
                available_locs = [k.split('.')[-1] for k in builder.scene_rules.keys()
                                  if k.startswith('locations.')]
                available_acts = [k.split('.')[-1] for k in builder.scene_rules.keys()
                                  if k.startswith('actions.')]
                available_weaths = [k.split('.')[-1] for k in builder.scene_rules.keys()
                                    if k.startswith('weather.')]
                available_cams = [k.split('.')[-1] for k in builder.scene_rules.keys()
                                  if k.startswith('camera.')]

                tracker = CoverageTracker(
                    available_locations=available_locs,
                    available_actions=available_acts,
                    available_weathers=available_weaths,
                    available_cameras=available_cams
                )

                matrix = tracker.scan_folder(balance_folder)
                weights = tracker.calculate_generation_weights(matrix)

                filtered_weights = {}
                if self.balance_locations_var.get(): filtered_weights['location'] = weights.get('location')
                if self.balance_actions_var.get(): filtered_weights['action'] = weights.get('action')
                if self.balance_weather_var.get(): filtered_weights['weather'] = weights.get('weather')
                if self.balance_cameras_var.get(): filtered_weights['camera'] = weights.get('camera')

                builder.generation_weights = filtered_weights
                self._log("✅ Weights calculated and applied.\n")

            output_dir = self.output_path_entry.get().strip()
            if not output_dir:
                raise ValueError("Output directory is not specified")

            self._log(f"🎬 Generating {num_scenes} scenes...\n")
            self._log(f"📂 Output: {output_dir}\n")

            force_closure = self.force_deficit_closure_var.get()
            if force_closure:
                self._log("⚡ Режим: AGGRESSIVE (инверсия приоритетов Action → Location)\n")
            else:
                self._log("🌿 Режим: NATURAL (стандартная логика Location → Action)\n")

            exporter = Exporter(
                builder,
                profile_name,
                generation_weights=builder.generation_weights,
                log_callback=self._log,
                verbose=False,
                force_deficit_closure=force_closure
            )

            stats = exporter.export_dataset(
                num_scenes=num_scenes,
                output_dir=output_dir,
                create_placeholders=False
            )

            self._log(f"\n✅ Generation complete!\n")
            self._log(f"📊 Total: {stats['total_scenes']} scenes\n")
            self._log(f"📂 Saved to: {output_dir}\n")

            messagebox.showinfo("Success",
                                f"Successfully generated {stats['total_scenes']} scenes!\n\n"
                                f"Saved to:\n{output_dir}")

        except Exception as e:
            self._log(f"\n❌ ERROR: {e}\n")
            import traceback
            self._log(traceback.format_exc())
            messagebox.showerror("Generation Error", str(e))

    # ════════════════════════════════════════════════════════════════════════════
    # 9. ANALYZER: Анализ покрытия датасета
    # ════════════════════════════════════════════════════════════════════════════
    
    def _browse_analyze_folder(self):
        """Открывает диалог выбора папки для анализа"""
        folder = filedialog.askdirectory(title="Select folder with prompt files")
        if folder:
            self.analyze_path_entry.delete(0, "end")
            self.analyze_path_entry.insert(0, folder)

    def _auto_fix_deficit(self):
        """Автоматически переключает на Generate с преднастроенной балансировкой"""
        folder = self.analyze_path_entry.get().strip()
        
        if not folder:
            messagebox.showwarning("Warning", "Сначала выберите папку и выполните анализ")
            return
        
        self.tabview.set("Generate")
        
        self.balance_path_entry.delete(0, "end")
        self.balance_path_entry.insert(0, folder)
        
        self.balance_locations_var.set(True)
        self.balance_actions_var.set(True)
        self.balance_weather_var.set(True)
        self.balance_cameras_var.set(True)
        
        messagebox.showinfo(
            "Auto-Fix Ready",
            f"✅ Настройки применены!\n\n"
            f"📂 Balance from: {folder}\n"
            f"⚖️ Все 4 измерения включены\n\n"
            f"Теперь просто нажмите '🚀 Generate Batch'!"
        )

    def _analyzer_log(self, message):
        """Добавляет сообщение в лог анализатора"""
        if self.analyzer_textbox is None: return
        self.analyzer_textbox.insert("end", message)
        self.analyzer_textbox.see("end")
        self.update_idletasks()

    def _clear_analyzer_log(self):
        """Очищает лог анализатора"""
        if self.analyzer_textbox is None: return
        self.analyzer_textbox.delete("1.0", "end")

    def _copy_analyzer_to_clipboard(self):
        """Копирует всю матрицу покрытия в буфер обмена"""
        if self.analyzer_textbox is None: return
        content = self.analyzer_textbox.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Info", "Лог пуст — нечего копировать")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Матрица покрытия скопирована в буфер обмена!")

    def _run_analysis(self):
        """Запускает анализ папки в отдельном потоке"""
        folder = self.analyze_path_entry.get().strip()
        if not folder:
            messagebox.showwarning("Warning", "Сначала выберите папку для анализа")
            return
            
        thread = threading.Thread(
            target=self._perform_analysis,
            args=(folder,),
            daemon=True
        )
        thread.start()

    def _perform_analysis(self, folder):
        """Основная логика анализа (выполняется в фоне)"""
        self._clear_analyzer_log()
        self._analyzer_log(f"🔍 Сканирование папки: {folder}\n")
        self._analyzer_log("=" * 70 + "\n\n")
        
        try:
            loader = ConfigLoader(project_root=str(self.project_root))
            rules = loader.load_scene_rules()
            
            available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
            available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
            available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
            available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]
            
            tracker = CoverageTracker(
                available_locations=available_locs,
                available_actions=available_acts,
                available_weathers=available_weaths,
                available_cameras=available_cams
            )
            
            self._analyzer_log("📦 Запуск Coverage Tracker...\n\n")
            matrix = tracker.scan_folder(folder)
            
            self._format_matrix_for_gui(matrix)
            
            self._analyzer_log("\n✅ Анализ успешно завершен!\n")
            
        except ValueError as e:
            self._analyzer_log(f"\n❌ Ошибка: {e}\n")
            messagebox.showerror("Analysis Error", str(e))
        except Exception as e:
            self._analyzer_log(f"\n❌ Непредвиденная ошибка: {e}\n")
            import traceback
            self._analyzer_log(traceback.format_exc())
            messagebox.showerror("Analysis Error", str(e))

    def _format_matrix_for_gui(self, matrix: dict):
        """Форматирует матрицу покрытия в красивый текст для GUI"""
        self._analyzer_log(f"📊 МАТРИЦА ПОКРЫТИЯ\n")
        self._analyzer_log(f"📂 Папка: {matrix['folder_path']}\n")
        self._analyzer_log(f"📄 Всего сцен: {matrix['total_scenes']}\n")
        self._analyzer_log("=" * 70 + "\n")
        
        if matrix["total_scenes"] == 0:
            self._analyzer_log("\n⚠️ В папке не найдено валидных промптов.\n")
            return
        
        if matrix.get("malformed_files"):
            self._analyzer_log(f"\n⚠️ Пропущено битых файлов: {len(matrix['malformed_files'])}\n")
        
        dimension_names = {
            "location": "📍 ЛОКАЦИИ",
            "action": "🎬 ДЕЙСТВИЯ",
            "weather": "🌦️ ПОГОДА",
            "camera": "📸 КАМЕРЫ"
        }
        
        for dimension, display_name in dimension_names.items():
            counts = matrix["dimensions"][dimension]
            percentages = matrix["percentages"][dimension]
            
            if not counts:
                continue
                
            self._analyzer_log(f"\n{display_name}:\n")
            self._analyzer_log("-" * 70 + "\n")
            
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            
            for category, count in sorted_items:
                pct = percentages[category]
                bar_length = int(pct / 2)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                
                status_icon = ""
                if f"{dimension}.{category}" in matrix["status"]["deficits"]:
                    status_icon = " 🔻 ДЕФИЦИТ"
                elif f"{dimension}.{category}" in matrix["status"]["overflows"]:
                    status_icon = " ⚠️ ПЕРЕИЗБЫТОК"
                    
                self._analyzer_log(f"   {category:25s}: {count:3d} ({pct:5.1f}%) [{bar}]{status_icon}\n")
        
        self._analyzer_log("\n" + "=" * 70 + "\n")
        self._analyzer_log("📋 СВОДКА:\n")
        if matrix["status"]["deficits"]:
            self._analyzer_log(f"   🔻 Дефицит: {', '.join(matrix['status']['deficits'])}\n")
        if matrix["status"]["overflows"]:
            self._analyzer_log(f"   ⚠️ Переизбыток: {', '.join(matrix['status']['overflows'])}\n")
        if not matrix["status"]["deficits"] and not matrix["status"]["overflows"]:
            self._analyzer_log("   ✅ Датасет идеально сбалансирован!\n")
        self._analyzer_log("=" * 70 + "\n")

    # ════════════════════════════════════════════════════════════════════════════
    # 10. LOGGING: Общие методы логирования
    # ════════════════════════════════════════════════════════════════════════════
    
    def _log(self, message):
        """Добавляет сообщение в лог-окно (разрешено копирование, запрещено редактирование)"""
        if not hasattr(self, 'log_textbox') or self.log_textbox is None:
            print(message, end='')
            return
        
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self.update_idletasks()
        
    def _block_text_edit(self, event):
        """Блокирует редактирование текста, но разрешает копирование и выделение"""
        if self.log_textbox is None: return "break"
        allowed_keys = ['Control_L', 'Control_R', 'c', 'C', 'a', 'A', 'x', 'X', 'v', 'V',
                        'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next']
        
        if event.keysym in allowed_keys or event.state == 4:
            return None
        
        return "break"

    def _copy_log_to_clipboard(self):
        """Копирует весь лог в буфер обмена"""
        if self.log_textbox is None: return
        content = self.log_textbox.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Весь лог скопирован в буфер обмена!")

    def _log_statistics(self, stats: dict):
        """Выводит статистику по сгенерированному датасету"""
        self._log("\n📊 Dataset Statistics:\n")
        self._log("=" * 60 + "\n")
        self._log(f"Total scenes: {stats['total_scenes']}\n")

        self._log(f"\n📍 Locations ({len(stats['locations'])} unique):\n")
        for loc, count in sorted(stats['locations'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_scenes']) * 100
            self._log(f"   {loc:25s}: {count:4d} ({percentage:5.1f}%)\n")

        self._log(f"\n🎬 Actions ({len(stats['actions'])} unique):\n")
        for action, count in sorted(stats['actions'].items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / stats['total_scenes']) * 100
            self._log(f"   {action:25s}: {count:4d} ({percentage:5.1f}%)\n")

        self._log(f"\n🌦️ Weathers ({len(stats['weathers'])} unique):\n")
        for weather, count in sorted(stats['weathers'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_scenes']) * 100
            self._log(f"   {weather:25s}: {count:4d} ({percentage:5.1f}%)\n")

        self._log("=" * 60 + "\n")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()