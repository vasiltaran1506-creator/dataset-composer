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
        
        # Создаем папку для профилей, если её нет
        self.profiles_directory.mkdir(exist_ok=True)

        # 3. Создание системы вкладок
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview.add("Profiles")
        self.tabview.add("Library")
        self.tabview.add("Generate")
        self.tabview.add("Analyzer")
        self.tabview.add("Settings")

        # 4. Создание контента вкладок
        self._create_profiles_tab()
        self._create_library_tab()
        self._create_generate_tab()
        self._create_analyzer_tab()
        self._create_settings_tab()

    def _create_placeholder(self, tab, text):
        """Вспомогательный метод для заглушек"""
        label = ctk.CTkLabel(tab, text=text, font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(expand=True)

    # ============================================================
    # ВКЛАДКА: PROFILES (Заглушка)
    # ============================================================
    def _create_profiles_tab(self):
        tab = self.tabview.tab("Profiles")
        self._create_placeholder(tab, "👤 Profiles\n\nЗдесь будет управление ДНК персонажей.")

    # ============================================================
    # ВКЛАДКА: LIBRARY (Заглушка)
    # ============================================================
    def _create_library_tab(self):
        tab = self.tabview.tab("Library")
        self._create_placeholder(tab, "📚 Library\n\nЗдесь будет редактор тегов и TOML-правил.")

    # ============================================================
    # ВКЛАДКА: GENERATE (ПОЛНАЯ ФУНКЦИОНАЛЬНОСТЬ)
    # ============================================================
    def _create_generate_tab(self):
        tab = self.tabview.tab("Generate")
        
        # Настройка сетки вкладки
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(2, weight=1)

        # === ЛЕВАЯ ПАНЕЛЬ: Настройки ===
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")
        
        # Заголовок
        title_label = ctk.CTkLabel(left_frame, text="⚙️ Generation Settings", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 10), padx=15, anchor="w")

        # 1. Выбор персонажа
        char_label = ctk.CTkLabel(left_frame, text="👤 Character Profile:", anchor="w")
        char_label.pack(pady=(10, 0), padx=15, fill="x")
        
        self.character_combobox = ctk.CTkComboBox(left_frame, values=self._get_available_profiles())
        self.character_combobox.pack(pady=(0, 15), padx=15, fill="x")
        
        # Если есть профили, выбираем первый
        profiles = self._get_available_profiles()
        if profiles:
            self.character_combobox.set(profiles[0])

        # 2. Количество сцен
        scenes_label = ctk.CTkLabel(left_frame, text="🎬 Number of Scenes:", anchor="w")
        scenes_label.pack(pady=(10, 0), padx=15, fill="x")
        
        self.scenes_entry = ctk.CTkEntry(left_frame, placeholder_text="100")
        self.scenes_entry.insert(0, "30")
        self.scenes_entry.pack(pady=(0, 15), padx=15, fill="x")

        # 3. Output Directory (НОВОЕ ПОЛЕ)
        output_label = ctk.CTkLabel(left_frame, text="📂 Save to folder:", anchor="w")
        output_label.pack(pady=(10, 0), padx=15, fill="x")
        
        output_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        output_frame.pack(pady=(0, 15), padx=15, fill="x")
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.output_path_entry = ctk.CTkEntry(output_frame)
        self.output_path_entry.insert(0, self.output_directory)  # Путь по умолчанию
        self.output_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        output_browse_btn = ctk.CTkButton(output_frame, text="Browse", width=80,
                                          command=self._browse_output_folder)
        output_browse_btn.grid(row=0, column=1)

        # Разделитель
        separator = ctk.CTkFrame(left_frame, height=2)
        separator.pack(pady=15, padx=15, fill="x")

        # 3. Coverage Engine Settings
        coverage_label = ctk.CTkLabel(left_frame, text="⚖️ Coverage Engine:", 
                                       font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        coverage_label.pack(pady=(0, 10), padx=15, fill="x")

        # Путь для балансировки
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

        # Чекбоксы для балансировки
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

        # Разделитель
        separator2 = ctk.CTkFrame(left_frame, height=2)
        separator2.pack(pady=15, padx=15, fill="x")

        # Кнопки действий
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

        # === ПРАВАЯ ПАНЕЛЬ: Лог ===
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        log_label = ctk.CTkLabel(right_frame, text="📝 Generation Log", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        log_label.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")

        self.log_textbox = ctk.CTkTextbox(right_frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        self._log("✅ Dataset Composer готов к работе.\n")
        self._log(f"📂 Output directory: {self.output_directory}\n")

    # ============================================================
    # ВКЛАДКА: ANALYZER (Заглушка)
    # ============================================================
    def _create_analyzer_tab(self):
        tab = self.tabview.tab("Analyzer")
        self._create_placeholder(tab, "📊 Analyzer\n\nМатрица покрытия и Auto-Fix.")

    # ============================================================
    # ВКЛАДКА: SETTINGS (Заглушка)
    # ============================================================
    def _create_settings_tab(self):
        tab = self.tabview.tab("Settings")
        self._create_placeholder(tab, "⚙️ Settings\n\nПути и интеграции.")

    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ============================================================
    def _get_available_profiles(self):
        """Сканирует папку character-profiles и возвращает список имен"""
        profiles = []
        if self.profiles_directory.exists():
            for file in self.profiles_directory.glob("*.yaml"):
                profiles.append(file.stem)
        
        # Fallback: если папка пустая, проверяем корень
        if not profiles:
            root_yaml = self.project_root / "character-profile.yaml"
            if root_yaml.exists():
                profiles.append("luna")  # default name
                
        return profiles if profiles else ["No profiles found"]
    
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

    def _log(self, message):
        """Добавляет сообщение в лог-окно"""
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self.update_idletasks()  # Обновляем UI, чтобы лог отображался сразу

    def _roll_dice(self):
        """Генерирует одну тестовую сцену"""
        self._log("\n🎲 Rolling dice...\n")
        try:
            profile_name = self.character_combobox.get()
            builder = self._init_builder(profile_name)
            
            # Выбираем случайную локацию
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
        import yaml  # Импортируем здесь, чтобы не засорять глобальные импорты
        
        loader = ConfigLoader(project_root=str(self.project_root))
        library = PromptLibrary(library_path=str(self.project_root / "prompt-library"))
        
        # 1. Загружаем правила и библиотеку тегов
        rules = loader.load_scene_rules()
        loader.load_location_types()
        library.load_library()
        
        # 2. Загружаем профиль персонажа напрямую через yaml
        profile_path = self.profiles_directory / f"{profile_name}.yaml"
        if not profile_path.exists():
            # Fallback: ищем в корне проекта
            profile_path = self.project_root / "character-profile.yaml"
            
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_name}")
            
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        
        # 3. Создаем SceneBuilder
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

        # Запускаем генерацию в отдельном потоке, чтобы UI не зависал
        thread = threading.Thread(
            target=self._run_generation,
            args=(profile_name, num_scenes, balance_folder),
            daemon=True
        )
        thread.start()

    def _run_generation(self, profile_name, num_scenes, balance_folder):
        """Основная логика генерации (выполняется в фоне)"""
        self._log(f"\n{'='*60}\n")
        self._log(f"🚀 Starting generation: {num_scenes} scenes for '{profile_name}'\n")
        
        try:
            # 1. Инициализация
            self._log("📦 Initializing engine...\n")
            builder = self._init_builder(profile_name)
            
            # 2. Coverage Engine (если нужно)
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
                
                # Фильтруем веса по чекбоксам
                filtered_weights = {}
                if self.balance_locations_var.get(): filtered_weights['location'] = weights.get('location')
                if self.balance_actions_var.get(): filtered_weights['action'] = weights.get('action')
                if self.balance_weather_var.get(): filtered_weights['weather'] = weights.get('weather')
                if self.balance_cameras_var.get(): filtered_weights['camera'] = weights.get('camera')
                
                builder.generation_weights = filtered_weights
                self._log("✅ Weights calculated and applied.\n")

            # 3. Генерация
            output_dir = self.output_path_entry.get().strip()
            if not output_dir:
                raise ValueError("Output directory is not specified")
                
            self._log(f"🎬 Generating {num_scenes} scenes...\n")
            self._log(f"📂 Output: {output_dir}\n")
            exporter = Exporter(builder, profile_name, generation_weights=builder.generation_weights)
            
            stats = exporter.export_dataset(
                num_scenes=num_scenes,
                output_dir=output_dir,
                create_placeholders=False
            )
            
            self._log(f"\n✅ Generation complete!\n")
            self._log(f"📊 Total: {stats['total_scenes']} scenes\n")
            self._log(f"📂 Saved to: {self.output_directory}\n")
            
            messagebox.showinfo("Success", 
                               f"Successfully generated {stats['total_scenes']} scenes!\n\n"
                               f"Saved to:\n{self.output_directory}")
            
        except Exception as e:
            self._log(f"\n❌ ERROR: {e}\n")
            import traceback
            self._log(traceback.format_exc())
            messagebox.showerror("Generation Error", str(e))


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()