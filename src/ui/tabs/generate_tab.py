import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os

# Импорты движка генерации
from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter
from coverage_tracker import CoverageTracker

# Палитра цветов (дублируем из MainWindow, чтобы не создавать циклический импорт)
COLORS = {
    'primary_blue': '#3b82f6',
    'primary_blue_hover': '#2563eb',
    'success_green': 'green',
    'success_green_hover': 'darkgreen',
    'danger_red': '#dc2626',
    'danger_red_hover': '#991b1b',
    'border_color': 'gray50',
}


class GenerateTab(ctk.CTkFrame):
    """Вкладка генерации датасета"""

    def __init__(
        self,
        master,
        settings_manager,
        project_root,
        profiles_directory,
        output_directory,
        log_callback,
        on_generate_settings_changed=None,  # callback для синхронизации с Settings
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        # Сохраняем ссылки
        self.settings_manager = settings_manager
        self.project_root = project_root
        self.profiles_directory = profiles_directory
        self.output_directory = output_directory
        self._log = log_callback
        self._on_settings_changed = on_generate_settings_changed
        
        # UI переменные
        self.character_combobox = None
        self.scenes_entry = None
        self.output_path_entry = None
        self.balance_path_entry = None
        self.balance_locations_var = None
        self.balance_actions_var = None
        self.balance_weather_var = None
        self.balance_cameras_var = None
        self.force_deficit_closure_var = None
        self.log_textbox = None
        
        # Строим UI
        self._setup_ui()

    def _setup_ui(self):
        """Создает интерфейс вкладки Generate"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        # === ЛЕВАЯ ПАНЕЛЬ ===
        left_frame = ctk.CTkFrame(self)
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
        default_scenes = self.settings_manager.get('generation_defaults', 'num_scenes')
        self.scenes_entry.insert(0, str(default_scenes))
        self.scenes_entry.bind('<FocusOut>', lambda e: self._save_scenes_from_generate())
        self.scenes_entry.pack(pady=(0, 15), padx=15, fill="x")

        ctk.CTkLabel(left_frame, text="📂 Save to folder:", anchor="w").pack(pady=(10, 0), padx=15, fill="x")
        output_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        output_frame.pack(pady=(0, 15), padx=15, fill="x")
        output_frame.grid_columnconfigure(0, weight=1)
        self.output_path_entry = ctk.CTkEntry(output_frame)
        saved_output = self.settings_manager.get('directories', 'output_directory')
        self.output_path_entry.insert(0, saved_output if saved_output else str(self.output_directory))
        self.output_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(output_frame, text="Browse", width=80,
                      command=self._browse_output_folder).grid(row=0, column=1)

        ctk.CTkFrame(left_frame, height=2).pack(pady=15, padx=15, fill="x")

        ctk.CTkLabel(left_frame, text="⚖️ Coverage Engine:",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(pady=(0, 10), padx=15, fill="x")
        ctk.CTkLabel(left_frame, text="Balance from folder:", anchor="w").pack(pady=(0, 5), padx=15, fill="x")

        balance_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        balance_frame.pack(pady=(0, 10), padx=15, fill="x")
        balance_frame.grid_columnconfigure(0, weight=1)
        self.balance_path_entry = ctk.CTkEntry(balance_frame, placeholder_text="Optional...")
        self.balance_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(balance_frame, text="Browse", width=80,
                      command=self._browse_balance_folder).grid(row=0, column=1)

        # Чекбоксы балансировки
        self.balance_locations_var = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_locations'))
        self.balance_actions_var = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_actions'))
        self.balance_weather_var = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_weather'))
        self.balance_cameras_var = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_cameras'))

        ctk.CTkCheckBox(left_frame, text="Balance Locations",
                        variable=self.balance_locations_var,
                        command=lambda: self._save_balance_from_generate('balance_locations', self.balance_locations_var)
                        ).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Actions",
                        variable=self.balance_actions_var,
                        command=lambda: self._save_balance_from_generate('balance_actions', self.balance_actions_var)
                        ).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Weather",
                        variable=self.balance_weather_var,
                        command=lambda: self._save_balance_from_generate('balance_weather', self.balance_weather_var)
                        ).pack(pady=2, padx=15, anchor="w")
        ctk.CTkCheckBox(left_frame, text="Balance Cameras",
                        variable=self.balance_cameras_var,
                        command=lambda: self._save_balance_from_generate('balance_cameras', self.balance_cameras_var)
                        ).pack(pady=2, padx=15, anchor="w")

        force_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        force_frame.pack(pady=(12, 2), padx=15, fill="x")
        self.force_deficit_closure_var = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'force_deficit_closure'))
        ctk.CTkCheckBox(force_frame, text="⚡ Force Deficit Closure",
                        variable=self.force_deficit_closure_var,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        command=lambda: self._save_balance_from_generate('force_deficit_closure', self.force_deficit_closure_var)
                        ).pack(side="left")
        ctk.CTkButton(force_frame, text="?", width=25, height=25,
                      fg_color="gray40", hover_color="gray50",
                      font=ctk.CTkFont(size=12, weight="bold"), corner_radius=15,
                      command=self._show_force_closure_help).pack(side="left", padx=(8, 0))

        ctk.CTkFrame(left_frame, height=2).pack(pady=15, padx=15, fill="x")

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

        # === ПРАВАЯ ПАНЕЛЬ: Лог ===
        right_frame = ctk.CTkFrame(self)
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

    # ═══════════════════════════════════════════════
    # PUBLIC API для синхронизации с Settings
    # ═══════════════════════════════════════════════
    def set_output_directory(self, path):
        """Обновляет поле Output Directory (вызывается из Settings)"""
        if self.output_path_entry:
            self.output_path_entry.delete(0, "end")
            self.output_path_entry.insert(0, str(path))

    def set_num_scenes(self, value):
        """Обновляет поле Number of Scenes (вызывается из Settings)"""
        if self.scenes_entry:
            self.scenes_entry.delete(0, "end")
            self.scenes_entry.insert(0, str(value))

    def set_balance_var(self, key, value):
        """Обновляет состояние чекбокса балансировки (вызывается из Settings)"""
        var_map = {
            'balance_locations': self.balance_locations_var,
            'balance_actions': self.balance_actions_var,
            'balance_weather': self.balance_weather_var,
            'balance_cameras': self.balance_cameras_var,
            'force_deficit_closure': self.force_deficit_closure_var,
        }
        var = var_map.get(key)
        if var:
            var.set(value)

    def set_balance_folder(self, path):
        """Устанавливает путь к папке балансировки (используется Analyzer'ом)"""
        if self.balance_path_entry:
            self.balance_path_entry.delete(0, "end")
            self.balance_path_entry.insert(0, str(path))
        # Включаем все чекбоксы балансировки
        if self.balance_locations_var: self.balance_locations_var.set(True)
        if self.balance_actions_var: self.balance_actions_var.set(True)
        if self.balance_weather_var: self.balance_weather_var.set(True)
        if self.balance_cameras_var: self.balance_cameras_var.set(True)

    # ═══════════════════════════════════════════════
    # ОБРАБОТЧИКИ UI
    # ═══════════════════════════════════════════════
    def _get_available_profiles(self):
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

    def _show_force_closure_help(self):
        messagebox.showinfo(
            "⚡ Force Deficit Closure",
            "Этот режим меняет порядок генерации:\n"
            "🌿 Natural Mode: сначала локация, потом действие.\n"
            "⚡ Aggressive Mode: сначала дефицитное действие, потом локация."
        )

    def _browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_path_entry.delete(0, "end")
            self.output_path_entry.insert(0, folder)
            self.settings_manager.set('directories', 'output_directory', folder)
            # Уведомляем MainWindow, чтобы он синхронизировал Settings
            if self._on_settings_changed:
                self._on_settings_changed('directories', 'output_directory', folder)

    def _browse_balance_folder(self):
        folder = filedialog.askdirectory(title="Select balance folder")
        if folder:
            self.balance_path_entry.delete(0, "end")
            self.balance_path_entry.insert(0, folder)

    def _save_scenes_from_generate(self):
        try:
            value = int(self.scenes_entry.get())
            if value > 0:
                self.settings_manager.set('generation_defaults', 'num_scenes', value)
                if self._on_settings_changed:
                    self._on_settings_changed('generation_defaults', 'num_scenes', value)
        except ValueError:
            valid_value = self.settings_manager.get('generation_defaults', 'num_scenes')
            self.scenes_entry.delete(0, "end")
            self.scenes_entry.insert(0, str(valid_value))

    def _save_balance_from_generate(self, key, var):
        self.settings_manager.set('generation_defaults', key, var.get())
        if self._on_settings_changed:
            self._on_settings_changed('generation_defaults', key, var.get())

    # ═══════════════════════════════════════════════
    # ГЕНЕРАЦИЯ
    # ═══════════════════════════════════════════════
    def _roll_dice(self):
        """Генерирует один случайный промпт для отладки"""
        self._log("\n🎲 Rolling dice...\n")
        try:
            import random
            profile_name = self.character_combobox.get()
            builder = self._init_builder(profile_name)
            available_locs = [k.split('.')[-1] for k in builder.scene_rules.keys() if k.startswith('locations.')]
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
        import gc
        gc_was_enabled = gc.isenabled()
        if gc_was_enabled:
            gc.disable()

        try:
            # Важно: для потокобезопасного UI используем after()
            self.after(0, lambda: self._log(f"\n{'=' * 60}\n"))
            self.after(0, lambda: self._log(f"🚀 Starting generation: {num_scenes} scenes for '{profile_name}'\n"))
            self.after(0, lambda: self._log("📦 Initializing engine...\n"))

            builder = self._init_builder(profile_name)

            if balance_folder:
                self.after(0, lambda: self._log(f"⚖️ Analyzing balance folder: {balance_folder}\n"))
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

                # Читаем переменные через after для потокобезопасности
                if self.balance_locations_var.get(): filtered_weights['location'] = weights.get('location')
                if self.balance_actions_var.get(): filtered_weights['action'] = weights.get('action')
                if self.balance_weather_var.get(): filtered_weights['weather'] = weights.get('weather')
                if self.balance_cameras_var.get(): filtered_weights['camera'] = weights.get('camera')

                builder.generation_weights = filtered_weights
                self.after(0, lambda: self._log("✅ Weights calculated.\n"))

            output_dir = self.output_path_entry.get().strip()
            if not output_dir:
                raise ValueError("Output directory is not specified")

            self.after(0, lambda: self._log(f"🎬 Generating {num_scenes} scenes...\n"))
            force_closure = self.force_deficit_closure_var.get()
            if force_closure:
                self.after(0, lambda: self._log("⚡ AGGRESSIVE Mode\n"))
            else:
                self.after(0, lambda: self._log("🌿 NATURAL Mode\n"))

            exporter = Exporter(builder, profile_name,
                                generation_weights=builder.generation_weights,
                                log_callback=self._log, verbose=False,
                                force_deficit_closure=force_closure)
            stats = exporter.export_dataset(num_scenes=num_scenes, output_dir=output_dir, create_placeholders=False)

            self.after(0, lambda: self._log(f"\n✅ Generation complete! Total: {stats['total_scenes']}\n"))
            self.after(0, lambda: self._log(f"📂 Saved to: {output_dir}\n"))
            self.after(0, lambda: messagebox.showinfo("Success", f"Generated {stats['total_scenes']} scenes!\nSaved to:\n{output_dir}"))

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            self.after(0, lambda: self._log(f"\n❌ ERROR: {e}\n"))
            self.after(0, lambda: self._log(err_msg))
            self.after(0, lambda: messagebox.showerror("Generation Error", str(e)))
        finally:
            if gc_was_enabled:
                gc.enable()
                gc.collect()

    # ═══════════════════════════════════════════════
    # ЛОГИРОВАНИЕ
    # ═══════════════════════════════════════════════
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