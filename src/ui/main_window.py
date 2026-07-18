import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
from pathlib import Path
import threading

# === FIX для PyInstaller ===
# Добавляем папку со скриптом и папку выше в sys.path.
# Это гарантирует, что импорты найдутся и в dev-режиме, и в .exe
current_dir = Path(__file__).parent
parent_dir = current_dir.parent

sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))

# Если запущено через PyInstaller, добавляем корневую папку бандла
meipass = getattr(sys, '_MEIPASS', None)
if meipass is not None:
    sys.path.insert(0, meipass)
# ============================

from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter
from coverage_tracker import CoverageTracker
from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter
from coverage_tracker import CoverageTracker
from settings_manager import SettingsManager

# ════════════════════════════════════════════════════════════════════════════
# ОПТИМИЗАЦИЯ: Повышение приоритета процесса
# ════════════════════════════════════════════════════════════════════════════
def set_high_priority():
    """Повышает приоритет процесса для лучшей отзывчивости UI"""
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            # ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(handle, 0x00008000)
        else:  # Linux/Mac
            os.nice(-5)  # Понижаем значение nice = повышаем приоритет
    except Exception:
        pass  # Тихо пропускаем, если нет прав

# Вызываем сразу после импортов
set_high_priority()

# ════════════════════════════════════════════════════════════════════════════
# Глобальная настройка CustomTkinter
# ════════════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Палитра цветов, используемая во всем UI
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

    # ════════════════════════════════════════════════════════════════════════
    # 1. ИНИЦИАЛИЗАЦИЯ
    # ════════════════════════════════════════════════════════════════════════
    def __init__(self):
        super().__init__()

        # 👇 ФИКС "ЖЕЛЕ": Включаем двойную буферизацию для всего окна (только Windows)
       # if os.name == 'nt':
       #     try:
       #         import ctypes
       #         hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
       #         GWL_EXSTYLE = -20
       #         WS_EX_COMPOSITED = 0x02000000
       #         style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
       #         ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_COMPOSITED)
       #     except Exception:
       #         pass  # Тихо пропускаем, если WinAPI недоступен

        self.title("Dataset Composer v1.1 - Character LoRA Pipeline")
        # Фиксированный базовый размер — окно не меняет размер при переключении вкладок
        self.geometry("1600x1000")
        self.minsize(1400, 900)
        # Растягиваем главный контейнер по сетке
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Пути к директориям проекта ===
        # Определяем корень проекта по-разному для dev и .exe режимов
        if hasattr(sys, '_MEIPASS'):
            # Режим .exe: .exe находится в папке dist/Dataset Composer/
            self.project_root = Path(sys.executable).parent
        else:
            # Dev режим: main_window.py в src/ui/, корень на 2 уровня выше
            self.project_root = Path(__file__).parent.parent.parent
        
        # === Менеджер настроек ===
        self.settings_manager = SettingsManager(self.project_root / "settings.json")
        
        # === Пути к папкам ===
        # Output directory (по умолчанию в корне проекта, можно изменить через Settings)
        saved_output = self.settings_manager.get('directories', 'output_directory')
        self.output_directory = saved_output if saved_output else r"D:\VASILY\MY GENERATION\Test Generations"
        
        # Папка с профилями персонажей
        saved_profiles = self.settings_manager.get('directories', 'profiles_path')
        if saved_profiles:
            self.profiles_directory = Path(saved_profiles)
        else:
            self.profiles_directory = self.project_root / "character-profiles"
        
        # Создаём папку профилей, если её нет
        self.profiles_directory.mkdir(parents=True, exist_ok=True)
        
        # Загружаем пути из настроек (или используем дефолты)
        saved_output = self.settings_manager.get('directories', 'output_directory')
        self.output_directory = saved_output if saved_output else r"D:\VASILY\MY GENERATION\Test Generations"
        
        saved_profiles = self.settings_manager.get('directories', 'profiles_path')
        self.profiles_directory = Path(saved_profiles) if saved_profiles else self.project_root / "character-profiles"
        self.profiles_directory.mkdir(exist_ok=True)

        # === Состояние редактора профиля ===
        self.current_profile_name: str | None = None
        self.profile_character_data: dict = {}

        # === Главный TabView ===
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Profiles")
        self.tabview.add("Library")
        self.tabview.add("Generate")
        self.tabview.add("Analyzer")
        self.tabview.add("Settings")

        # Кэш тегов (чтобы не читать диск при каждом клике)
        self._tags_cache = {}

        # Debouncing для update_idletasks (борьба с "плаванием" окна)
        self._update_timer = None
        # Debouncing для поиска в Scene Rules
        self._search_timer = None
        # Debouncing для UI обновлений (chips)

        # Флаги инициализации вкладок (защита от повторного создания)
        self._tabs_created = {
            'Profiles': False,
            'Library': False,
            'Generate': False,
            'Analyzer': False,
            'Settings': False
        }

        # 👇 ОПТИМИЗАЦИЯ: Создаём только Profiles и Generate (часто используемые)
        # Остальные вкладки создаются при первом переключении
        self._create_profiles_tab()
        self._create_generate_tab()

        # Обработчик переключения вкладок (для борьбы с фантомами при смене)
        self.tabview.configure(command=self._on_main_tab_changed)

        # Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # ════════════════════════════════════════════════════════════════
        # 👇 ФИКС "ЖЕЛЕ": Debounced redraw при перемещении/ресайзе окна
        # ════════════════════════════════════════════════════════════════
        self._configure_timer = None
        self.bind('<Configure>', self._on_window_configure)

        # ════════════════════════════════════════════════════════════════
        # 👇 ФИКС ФАНТОМОВ ПРИ СТАРТЕ (радикальный метод)
        # ════════════════════════════════════════════════════════════════
        # Ждём, пока все виджеты рассчитают свои размеры
        self.update_idletasks()
        
        # Центрирование окна ПОСЛЕ всех расчётов
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 1600) // 2
        y = (screen_height - 1000) // 2
        self.geometry(f"+{x}+{y}")
        
        # Трюк: прячем окно из Windows и показываем заново.
        # Это форсирует ОС пересоздать оконный хэндл и перерисовать
        # все Canvas CustomTkinter без артефактов.
        self.withdraw()
        self.deiconify()
        
        # Финальная полная перерисовка
        self.update()
        self.update()
        
        # Дополнительная перерисовка через 100мс (для полной гарантии)
        self.after(100, lambda: self.update_idletasks())


    def _create_placeholder(self, tab, text):
        label = ctk.CTkLabel(tab, text=text, font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(expand=True)


    def _on_main_tab_changed(self):
        """Обработчик смены вкладки с ленивой инициализацией"""
        try:
            # 👇 ОПТИМИЗАЦИЯ: Создаём вкладку при первом переключении
            current_tab = self.tabview.get()
            if current_tab == "Library" and not self._tabs_created.get('Library', False):
                self._create_library_tab()
            elif current_tab == "Analyzer" and not self._tabs_created.get('Analyzer', False):
                self._create_analyzer_tab()
            elif current_tab == "Settings" and not self._tabs_created.get('Settings', False):
                self._create_settings_tab()
            
            self.update_idletasks()
            self.after(10, lambda: self.update_idletasks())
        except Exception:
            pass

    def _on_window_configure(self, event):
        """
        Обработчик изменения размера/позиции окна.
        Запускает таймер на 50мс для debounced redraw.
        Это устраняет артефакты 'желе' при движении окна,
        НЕ ломая popup-окна (в отличие от WS_EX_COMPOSITED).
        """
        # Обрабатываем только события главного окна, а не дочерних виджетов
        if event.widget != self:
            return
        
        # Сбрасываем предыдущий таймер (debounce)
        if self._configure_timer:
            self.after_cancel(self._configure_timer)
        
        # Запускаем новый таймер на 50мс
        self._configure_timer = self.after(50, self._force_redraw_after_configure)
    
    def _force_redraw_after_configure(self):
        """Принудительная перерисовка после остановки движения окна"""
        self._configure_timer = None
        try:
            self.update_idletasks()
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════════════════
    # 2. СОЗДАНИЕ ВКЛАДОК (UI)
    # ════════════════════════════════════════════════════════════════════════
    def _create_profiles_tab(self):
        """Создает вкладку Profiles через ProfilesTab класс"""
        if self._tabs_created.get('Profiles', False):
            return
        self._tabs_created['Profiles'] = True

        tab = self.tabview.tab("Profiles")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        from ui.tabs.profiles_tab import ProfilesTab

        self.profiles_tab_widget = ProfilesTab(
            master=tab,
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            settings_manager=self.settings_manager,
            log_callback=self._log,
        )
        self.profiles_tab_widget.grid(row=0, column=0, sticky="nsew")

    # ════════════════════════════════════════════════════════════════════════
    # GENERATE TAB
    # ════════════════════════════════════════════════════════════════════════

    def _create_generate_tab(self):
        """Создает вкладку Generate через GenerateTab класс"""
        if self._tabs_created.get("Generate", False):
            return
        self._tabs_created["Generate"] = True

        tab = self.tabview.tab("Generate")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        from ui.tabs.generate_tab import GenerateTab

        self.generate_tab_widget = GenerateTab(
            master=tab,
            settings_manager=self.settings_manager,
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            output_directory=self.output_directory,
            log_callback=self._log,
            on_generate_settings_changed=self._on_generate_settings_changed
        )
        self.generate_tab_widget.grid(row=0, column=0, sticky="nsew")

    def _on_generate_settings_changed(self, section: str, key: str, value):
        """Callback: когда пользователь меняет что-то во вкладке Generate, 
        мы синхронизируем это с вкладкой Settings"""
        # Обновляем старые атрибуты MainWindow для обратной совместимости
        if section == 'directories' and key == 'output_directory':
            self.output_directory = value
            # Если Settings уже открыт, обновляем его переменную
            if hasattr(self, 'settings_tab_widget') and self.settings_tab_widget:
                self.settings_tab_widget.set_output_directory(value)
        elif section == 'generation_defaults':
            if key == 'num_scenes':
                if hasattr(self, 'settings_tab_widget') and self.settings_tab_widget:
                    self.settings_tab_widget.set_num_scenes(value)
            else:
                if hasattr(self, 'settings_tab_widget') and self.settings_tab_widget:
                    self.settings_tab_widget.set_balance_var(key, value)

    # ════════════════════════════════════════════════════════════════════════
    # ANALYZER TAB
    # ════════════════════════════════════════════════════════════════════════

    def _create_settings_tab(self):
        """Создает вкладку Settings через SettingsTab класс"""
        if self._tabs_created.get("Settings", False):
            return
        self._tabs_created["Settings"] = True

        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Создаём SettingsTab и добавляем в tab
        from ui.tabs import SettingsTab

        self.settings_tab_widget = SettingsTab(
            master=tab,
            settings_manager=self.settings_manager,
            project_root=self.project_root,
            output_directory=self.output_directory,
            profiles_directory=self.profiles_directory,
            log_callback=self._log,
            on_settings_changed=self._on_settings_changed
        )
        self.settings_tab_widget.grid(row=0, column=0, sticky="nsew")

    # ═══════════════════════════════════════════════
    # ОБРАБОТЧИКИ НАСТРОЕК (Settings Tab)
    # ═══════════════════════════════════════════════

    def _on_settings_changed(self, section: str, key: str, value):
        """Callback для синхронизации настроек между вкладками"""
        if not hasattr(self, 'generate_tab_widget'):
            return

        if section == 'directories' and key == 'output_directory':
            self.generate_tab_widget.set_output_directory(value)
            # Синхронизируем с Analyzer
            if hasattr(self, 'analyzer_tab_widget') and self.analyzer_tab_widget:
                self.analyzer_tab_widget.set_output_directory(value)
        elif section == 'generation_defaults' and key == 'num_scenes':
            self.generate_tab_widget.set_num_scenes(value)
        elif section == 'generation_defaults':
            self.generate_tab_widget.set_balance_var(key, value)

    # ════════════════════════════════════════════════════════════════════════
    # ОБРАБОТЧИК АНАЛИЗАТОРА (Analyzer Tab)
    # ════════════════════════════════════════════════════════════════════════

    def _on_analyzer_auto_fix(self, folder: str):
        """
        Callback от AnalyzerTab: пользователь нажал 'Auto-Fix'.
        Мы переключаемся на вкладку Generate и передаём ей папку.
        """
        self.tabview.set("Generate")

        # Проверяем, создан ли GenerateTab
        if hasattr(self, 'generate_tab_widget') and self.generate_tab_widget:
            self.generate_tab_widget.set_balance_folder(folder)
            messagebox.showinfo(
                "Auto-Fix Ready", 
                f"✅ Balance from: {folder}\nНажмите '🚀 Generate Batch'!"
            )
        else:
            messagebox.showwarning(
                "Warning", 
                "Вкладка Generate ещё не инициализирована."
            )


    # ════════════════════════════════════════════════════════════════════════
    # UTILS: Утилиты библиотеки тегов и debouncing
    # ════════════════════════════════════════════════════════════════════════

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
            self._log(f"✅ Загружено {len(tags)} тегов из {relative_path}\n")
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

    # ════════════════════════════════════════════════════════════════════════
    # GENERATE
    # ════════════════════════════════════════════════════════════════════════

    def _show_force_closure_help(self):
        messagebox.showinfo(
            "⚡ Force Deficit Closure",
            "Этот режим меняет порядок генерации:\n"
            "🌿 Natural Mode: сначала локация, потом действие.\n"
            "⚡ Aggressive Mode: сначала дефицитное действие, потом локация."
        )

    def _browse_output_folder(self):
        """Обработчик выбора папки вывода во вкладке Generate"""
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_path_entry.delete(0, "end")
            self.output_path_entry.insert(0, folder)
            # 👇 ОБРАТНАЯ СИНХРОНИЗАЦИЯ: сохраняем в настройки
            self.settings_manager.set('directories', 'output_directory', folder)
            # Обновляем поле в Settings (если вкладка уже открыта)
            if hasattr(self, 'settings_output_dir_var') and self.settings_output_dir_var:
                self.settings_output_dir_var.set(folder)

    def _browse_balance_folder(self):
        """Обработчик выбора папки балансировки во вкладке Generate"""
        folder = filedialog.askdirectory(title="Select balance folder")
        if folder:
            self.balance_path_entry.delete(0, "end")
            self.balance_path_entry.insert(0, folder)

    def _save_scenes_from_generate(self):
        """Сохраняет количество сцен из поля Generate в настройки и синхронизирует с Settings"""
        try:
            value = int(self.scenes_entry.get())
            if value > 0:
                self.settings_manager.set('generation_defaults', 'num_scenes', value)
                # Обновляем поле в Settings (если вкладка уже открыта)
                if hasattr(self, 'settings_scenes_var') and self.settings_scenes_var:
                    self.settings_scenes_var.set(str(value))
        except ValueError:
            # Восстанавливаем предыдущее корректное значение
            valid_value = self.settings_manager.get('generation_defaults', 'num_scenes')
            self.scenes_entry.delete(0, "end")
            self.scenes_entry.insert(0, str(valid_value))

    def _save_balance_from_generate(self, key: str, var):
        """Сохраняет состояние чекбокса балансировки из Generate в настройки и синхронизирует с Settings"""
        self.settings_manager.set('generation_defaults', key, var.get())
        # Маппинг ключей настроек на переменные UI в Settings
        var_mapping = {
            'balance_locations': 'settings_balance_locs',
            'balance_actions': 'settings_balance_acts',
            'balance_weather': 'settings_balance_weath',
            'balance_cameras': 'settings_balance_cams',
            'force_deficit_closure': 'settings_force_closure',
        }
        # Обновляем соответствующую переменную в Settings (если вкладка уже открыта)
        if key in var_mapping:
            target_var_name = var_mapping[key]
            if hasattr(self, target_var_name):
                target_var = getattr(self, target_var_name)
                if target_var is not None:
                    target_var.set(var.get())

    def _roll_dice(self):
        """Генерирует один случайный промпт для отладки"""
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
        """Инициализирует SceneBuilder для генерации"""
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
        """Запускает батчевую генерацию в отдельном потоке"""
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
        """Основная логика генерации датасета (выполняется в thread)"""
        # 👇 ОПТИМИЗАЦИЯ: Отключаем GC на время генерации (устраняет микро-фризы)
        import gc
        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            self.update_idletasks()
            self._log(f"\n{'=' * 60}\n")
            self._log(f"🚀 Starting generation: {num_scenes} scenes for '{profile_name}'\n")
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
        finally:
            # 👇 Возвращаем GC в исходное состояние
            if gc_was_enabled:
                gc.enable()
                gc.collect()  # Однократная очистка в конце

    # ════════════════════════════════════════════════════════════════════════
    # ANALYZER
    # ════════════════════════════════════════════════════════════════════════

    def _create_analyzer_tab(self):
        """Создает вкладку Analyzer через AnalyzerTab класс"""
        if self._tabs_created.get("Analyzer", False):
            return
        self._tabs_created["Analyzer"] = True

        tab = self.tabview.tab("Analyzer")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        from ui.tabs.analyzer_tab import AnalyzerTab

        self.analyzer_tab_widget = AnalyzerTab(
            master=tab,
            project_root=self.project_root,
            output_directory=self.output_directory,
            log_callback=self._log,
            load_tags_callback=self._load_tags_from_file,
            on_auto_fix_deficit=self._on_analyzer_auto_fix,  # 👈 НОВЫЙ callback
        )
        self.analyzer_tab_widget.grid(row=0, column=0, sticky="nsew")

    # ════════════════════════════════════════════════════════════════════════
    # LIBRARY
    # ════════════════════════════════════════════════════════════════════════

    def _create_library_tab(self):
        """Создает вкладку Library через LibraryTab класс"""
        if self._tabs_created.get('Library', False):
            return
        self._tabs_created['Library'] = True
        
        tab = self.tabview.tab("Library")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        from ui.tabs.library_tab import LibraryTab
        
        self.library_tab_widget = LibraryTab(
            master=tab,
            project_root=self.project_root,
            log_callback=self._log,
        )
        self.library_tab_widget.grid(row=0, column=0, sticky="nsew")

    # ════════════════════════════════════════════════════════════════════════
    # LOGGING & UTILS
    # ════════════════════════════════════════════════════════════════════════

    def _log(self, message):
        """Добавляет сообщение в лог-окно (разрешено копирование, запрещено редактирование)"""
        if not hasattr(self, 'log_textbox') or self.log_textbox is None:
            print(message, end='')
            return
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self._debounced_update()

    def _block_text_edit(self, event):
        """Блокирует редактирование лога, разрешая только копирование"""
        if self.log_textbox is None:
            return "break"
        allowed = ['Control_L', 'Control_R', 'c', 'C', 'a', 'A', 'x', 'X', 'v', 'V',
                   'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next']
        if event.keysym in allowed or event.state == 4:
            return None
        return "break"

    def _copy_log_to_clipboard(self):
        if self.log_textbox is None:
            return
        content = self.log_textbox.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Лог скопирован!")

    def _debounced_update(self, delay_ms: int = 100):
        """Откладывает update_idletasks, вызывая его не чаще 1 раза в delay_ms"""
        if self._update_timer:
            self.after_cancel(self._update_timer)
        self._update_timer = self.after(delay_ms, self._do_update)

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

    def _do_update(self):
        """Выполняет отложенный update_idletasks"""
        self._update_timer = None
        try:
            self.update_idletasks()
        except Exception:
            pass

    def _on_closing(self):
        """Мгновенное закрытие приложения через os._exit (защита от зависаний)"""
        print("🔄 Закрытие Dataset Composer...")
        os._exit(0)


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()