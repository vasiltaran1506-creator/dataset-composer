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

        # 👇 НОВЫЙ БЛОК: Aggressive mode checkbox + help button
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

        # Заголовок лога + кнопка копирования
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
        # Привязываем обработчики для блокировки редактирования (но разрешения копирования)
        self.log_textbox.bind("<Key>", self._block_text_edit)
        self.log_textbox.bind("<<Paste>>", self._block_text_edit)
        self.log_textbox.bind("<<Cut>>", self._block_text_edit)

        self._log("✅ Dataset Composer готов к работе.\n")
        self._log(f"📂 Output directory: {self.output_directory}\n")

    # ============================================================
    # ВКЛАДКА: ANALYZER (ПОЛНАЯ ФУНКЦИОНАЛЬНОСТЬ)
    # ============================================================
    def _create_analyzer_tab(self):
        tab = self.tabview.tab("Analyzer")
        
        # Настройка сетки вкладки (двухколоночный layout как в Generate)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)
        
        # === ЛЕВАЯ ПАНЕЛЬ: Настройки ===
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        title_label = ctk.CTkLabel(left_frame, text="📊 Analyzer Settings",
                                    font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 10), padx=15, anchor="w")
        
        # Поле выбора папки
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
        
        # Кнопка запуска анализа
        analyze_btn = ctk.CTkButton(left_frame, text="🔍 Analyze Dataset",
                                      fg_color="#2563eb", hover_color="#1d4ed8",
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      height=45,
                                      command=self._run_analysis)
        analyze_btn.pack(pady=20, padx=15, fill="x")
        
        # Кнопка очистки лога
        clear_btn = ctk.CTkButton(left_frame, text="🗑️ Clear Log",
                                   fg_color="gray", hover_color="darkgray",
                                   command=self._clear_analyzer_log)
        clear_btn.pack(pady=5, padx=15, fill="x")
        
        # 👇 НОВАЯ КНОПКА: Auto-Fix Deficit
        autofix_btn = ctk.CTkButton(left_frame, text="⚡ Auto-Fix Deficit",
                                     fg_color="#dc2626", hover_color="#991b1b",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     height=40,
                                     command=self._auto_fix_deficit)
        autofix_btn.pack(pady=(15, 5), padx=15, fill="x")
        
        # Справка
        info_label = ctk.CTkLabel(left_frame, 
                                   text="ℹ️ Анализатор просканирует выбранную папку, "
                                        "прочитает все .txt файлы и построит матрицу "
                                        "покрытия с детекцией дефицита/переизбытка.",
                                   wraplength=280, justify="left", anchor="w",
                                   text_color="gray")
        info_label.pack(pady=(20, 10), padx=15, fill="x")
        
        # === ПРАВАЯ ПАНЕЛЬ: Результат ===
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Заголовок + кнопка копирования
        log_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)
        
        result_label = ctk.CTkLabel(log_header, text="📈 Coverage Matrix",
                                     font=ctk.CTkFont(size=18, weight="bold"))
        result_label.grid(row=0, column=0, sticky="w")
        
        copy_btn = ctk.CTkButton(log_header, text="📋 Copy Matrix", width=120,
                                  command=self._copy_analyzer_to_clipboard)
        copy_btn.grid(row=0, column=1)
        
        # Textbox для вывода матрицы
        self.analyzer_textbox = ctk.CTkTextbox(right_frame, 
                                                font=ctk.CTkFont(family="Consolas", size=12))
        self.analyzer_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Приветственное сообщение
        self._analyzer_log("👋 Добро пожаловать в Dataset Analyzer!\n\n")
        self._analyzer_log("1. Нажмите 'Browse' и выберите папку с промптами\n")
        self._analyzer_log("2. Нажмите '🔍 Analyze Dataset'\n")
        self._analyzer_log("3. Изучите матрицу покрытия ниже\n\n")
        self._analyzer_log("ℹ️ Подсказка: 🔻 ДЕФИЦИТ = нужно догенерировать\n")
        self._analyzer_log("              ⚠️ ПЕРЕИЗБЫТОК = можно удалить лишнее\n")

    def _copy_log_to_clipboard(self):
        """Копирует весь лог в буфер обмена"""
        content = self.log_textbox.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Весь лог скопирован в буфер обмена!")

    def _auto_fix_deficit(self):
        """Автоматически переключает на Generate с преднастроенной балансировкой"""
        folder = self.analyze_path_entry.get().strip()
        
        if not folder:
            messagebox.showwarning("Warning", "Сначала выберите папку и выполните анализ")
            return
        
        # 1. Переключаемся на вкладку Generate
        self.tabview.set("Generate")
        
        # 2. Заполняем поле "Balance from folder"
        self.balance_path_entry.delete(0, "end")
        self.balance_path_entry.insert(0, folder)
        
        # 3. Включаем все чекбоксы балансировки
        self.balance_locations_var.set(True)
        self.balance_actions_var.set(True)
        self.balance_weather_var.set(True)
        self.balance_cameras_var.set(True)
        
        # 4. Уведомляем пользователя
        messagebox.showinfo(
            "Auto-Fix Ready",
            f"✅ Настройки применены!\n\n"
            f"📂 Balance from: {folder}\n"
            f"⚖️ Все 4 измерения включены\n\n"
            f"Теперь просто нажмите '🚀 Generate Batch'!"
        )

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

    def _browse_analyze_folder(self):
        """Открывает диалог выбора папки для анализа"""
        folder = filedialog.askdirectory(title="Select folder with prompt files")
        if folder:
            self.analyze_path_entry.delete(0, "end")
            self.analyze_path_entry.insert(0, folder)

    def _analyzer_log(self, message):
        """Добавляет сообщение в лог анализатора"""
        self.analyzer_textbox.insert("end", message)
        self.analyzer_textbox.see("end")
        self.update_idletasks()

    def _clear_analyzer_log(self):
        """Очищает лог анализатора"""
        self.analyzer_textbox.delete("1.0", "end")

    def _copy_analyzer_to_clipboard(self):
        """Копирует всю матрицу покрытия в буфер обмена"""
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
            # Инициализируем loader, чтобы получить списки известных тегов
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
            
            # Выводим результат в textbox
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
        
        # Сводка
        self._analyzer_log("\n" + "=" * 70 + "\n")
        self._analyzer_log("📋 СВОДКА:\n")
        if matrix["status"]["deficits"]:
            self._analyzer_log(f"   🔻 Дефицит: {', '.join(matrix['status']['deficits'])}\n")
        if matrix["status"]["overflows"]:
            self._analyzer_log(f"   ⚠️ Переизбыток: {', '.join(matrix['status']['overflows'])}\n")
        if not matrix["status"]["deficits"] and not matrix["status"]["overflows"]:
            self._analyzer_log("   ✅ Датасет идеально сбалансирован!\n")
        self._analyzer_log("=" * 70 + "\n")

    def _log(self, message):
        """Добавляет сообщение в лог-окно (разрешено копирование, запрещено редактирование)"""
        self.log_textbox.insert("end", message)
        self.log_textbox.see("end")
        self.update_idletasks()
        
    def _block_text_edit(self, event):
        """Блокирует редактирование текста, но разрешает копирование и выделение"""
        # Разрешаем только копирование (Ctrl+C, Ctrl+A) и навигацию (стрелки, Home, End)
        allowed_keys = ['Control_L', 'Control_R', 'c', 'C', 'a', 'A', 'x', 'X', 'v', 'V',
                        'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next']
        
        if event.keysym in allowed_keys or event.state == 4:  # state == 4 означает зажатый Ctrl
            return None  # Разрешаем событие
        
        return "break"  # Блокируем все остальные события клавиатуры

    def _log_statistics(self, stats: dict):
        """👇 ИСПРАВЛЕНИЕ 3: Добавлен недостающий метод для вывода статистики"""
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
            
            # 👇 КРИТИЧНО: читаем состояние галочки
            force_closure = self.force_deficit_closure_var.get()
            if force_closure:
                self._log("⚡ Режим: AGGRESSIVE (инверсия приоритетов Action → Location)\n")
            else:
                self._log("🌿 Режим: NATURAL (стандартная логика Location → Action)\n")
            
            # 👇 КРИТИЧНО: передаём force_deficit_closure
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
            
            if force_closure:
                self._log("⚡ Force Deficit Closure: ENABLED\n")
            else:
                self._log("🌿 Natural Mode (standard generation)\n")

            stats = exporter.export_dataset(
                num_scenes=num_scenes,
                output_dir=output_dir,
                create_placeholders=False
            )

            self._log(f"\n✅ Generation complete!\n")
            # 👇 ИСПРАВЛЕНИЕ 3: Вызываем метод для вывода статистики
            self._log_statistics(stats)
            # 👇 ИСПРАВЛЕНИЕ 5: Используем output_dir вместо hardcoded self.output_directory
            self._log(f"📂 Saved to: {output_dir}\n")

            messagebox.showinfo("Success",
                               f"Successfully generated {stats['total_scenes']} scenes!\n\n"
                               f"Saved to:\n{output_dir}")

        except Exception as e:
            self._log(f"\n❌ ERROR: {e}\n")
            import traceback
            self._log(traceback.format_exc())
            messagebox.showerror("Generation Error", str(e))


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()