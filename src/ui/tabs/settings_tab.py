"""
Settings Tab - Настройки приложения (пути, генерация, поведение)
Qt-ready архитектура: наследуется от CTkFrame, принимает dependencies через конструктор.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable
import webbrowser


# Палитра цветов (дублируем для автономности модуля)
COLORS = {
    'primary_blue': '#3b82f6',
    'primary_blue_hover': '#2563eb',
    'success_green': 'green',
    'success_green_hover': 'darkgreen',
    'danger_red': '#dc2626',
    'danger_red_hover': '#991b1b',
}


class SettingsTab(ctk.CTkFrame):
    """
    Вкладка настроек приложения.
    
    Dependencies:
        settings_manager: Менеджер настроек (сохранение в settings.json)
        project_root: Корень проекта
        output_directory: Текущая output директория
        profiles_directory: Текущая директория профилей
        
    Callbacks (для синхронизации с другими вкладками):
        on_settings_changed(section, key, value): Вызывается при изменении настройки
        log_callback(message): Для логирования
    """
    
    def __init__(
        self,
        master,
        settings_manager,
        project_root: Path,
        output_directory: str,
        profiles_directory: Path,
        log_callback: Optional[Callable] = None,
        on_settings_changed: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        # Сохраняем dependencies
        self.settings_manager = settings_manager
        self.project_root = project_root
        self.output_directory = output_directory
        self.profiles_directory = profiles_directory
        
        # Callbacks
        self.log_callback = log_callback or print
        self.on_settings_changed = on_settings_changed or (lambda *args: None)
        
        # Настраиваем grid для растягивания
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # UI переменные
        self.settings_output_dir_var: ctk.StringVar = ctk.StringVar()
        self.settings_profiles_dir_var: ctk.StringVar = ctk.StringVar()
        self.settings_scenes_var: ctk.StringVar = ctk.StringVar()
        self.settings_balance_locs: ctk.BooleanVar = ctk.BooleanVar()
        self.settings_balance_acts: ctk.BooleanVar = ctk.BooleanVar()
        self.settings_balance_weath: ctk.BooleanVar = ctk.BooleanVar()
        self.settings_balance_cams: ctk.BooleanVar = ctk.BooleanVar()
        self.settings_force_closure: ctk.BooleanVar = ctk.BooleanVar()
        self.settings_confirm_delete: ctk.BooleanVar = ctk.BooleanVar()
        
        # Строим UI
        self._build_ui()
    
    def _log(self, message: str):
        """Унифицированный логгинг"""
        self.log_callback(message)
    
    def _build_ui(self):
        """Строит весь UI вкладки Settings"""
        # Скроллируемая область для всех секций
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        
        # СЕКЦИЯ 1: Пути к директориям
        self._build_directories_section(scroll)
        
        # СЕКЦИЯ 2: Параметры генерации по умолчанию
        self._build_generation_defaults_section(scroll)
        
        # СЕКЦИЯ 3: Поведение приложения
        self._build_behavior_section(scroll)
        
        # КНОПКА СБРОСА ВСЕХ НАСТРОЕК
        reset_all_btn = ctk.CTkButton(
            scroll,
            text="🔄 Сбросить все настройки к значениям по умолчанию",
            fg_color=COLORS['danger_red'],
            hover_color=COLORS['danger_red_hover'],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=self._reset_all_settings
        )
        reset_all_btn.pack(fill="x", pady=(5, 15), padx=5)
        
        # СЕКЦИЯ 4: О программе (About)
        self._build_about_section(scroll)
    
    def _build_directories_section(self, parent):
        """Секция путей к директориям"""
        dirs_frame = ctk.CTkFrame(parent)
        dirs_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        ctk.CTkLabel(
            dirs_frame,
            text="📂 Пути к директориям",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        # Output directory
        self.settings_output_dir_var = ctk.StringVar(
            value=self.settings_manager.get('directories', 'output_directory') 
                  or self.output_directory
        )
        self._create_path_row(
            dirs_frame,
            "Output (генерация):",
            self.settings_output_dir_var,
            self._browse_settings_output,
            'directories', 'output_directory'
        )
        
        # Profiles path
        self.settings_profiles_dir_var = ctk.StringVar(
            value=self.settings_manager.get('directories', 'profiles_path') 
                  or str(self.profiles_directory)
        )
        self._create_path_row(
            dirs_frame,
            "Profiles (персонажи):",
            self.settings_profiles_dir_var,
            self._browse_settings_profiles,
            'directories', 'profiles_path'
        )
        
        # Кнопка сброса путей
        reset_paths_btn = ctk.CTkButton(
            dirs_frame,
            text="🔄 Сбросить пути к дефолтным",
            fg_color="gray40",
            hover_color="gray50",
            width=250,
            height=32,
            command=self._reset_paths_to_defaults
        )
        reset_paths_btn.pack(anchor="w", padx=15, pady=(10, 12))
    
    def _build_generation_defaults_section(self, parent):
        """Секция параметров генерации по умолчанию"""
        gen_frame = ctk.CTkFrame(parent)
        gen_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        ctk.CTkLabel(
            gen_frame,
            text="🎬 Параметры генерации по умолчанию",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        # Количество сцен
        scenes_row = ctk.CTkFrame(gen_frame, fg_color="transparent")
        scenes_row.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            scenes_row,
            text="Количество сцен:",
            width=180,
            anchor="w"
        ).pack(side="left")
        
        self.settings_scenes_var = ctk.StringVar(
            value=str(self.settings_manager.get('generation_defaults', 'num_scenes'))
        )
        scenes_entry = ctk.CTkEntry(
            scenes_row,
            textvariable=self.settings_scenes_var,
            width=120
        )
        scenes_entry.pack(side="left")
        scenes_entry.bind('<FocusOut>', lambda e: self._save_scenes_default())
        
        # Чекбоксы балансировки
        self.settings_balance_locs = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_locations')
        )
        self.settings_balance_acts = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_actions')
        )
        self.settings_balance_weath = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_weather')
        )
        self.settings_balance_cams = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'balance_cameras')
        )
        
        ctk.CTkLabel(
            gen_frame,
            text="Включить балансировку по умолчанию:",
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        balance_frame = ctk.CTkFrame(gen_frame, fg_color="transparent")
        balance_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        ctk.CTkCheckBox(
            balance_frame,
            text="Locations",
            variable=self.settings_balance_locs,
            command=lambda: self._save_balance_default(
                'balance_locations', self.settings_balance_locs
            )
        ).pack(anchor="w", pady=2)
        
        ctk.CTkCheckBox(
            balance_frame,
            text="Actions",
            variable=self.settings_balance_acts,
            command=lambda: self._save_balance_default(
                'balance_actions', self.settings_balance_acts
            )
        ).pack(anchor="w", pady=2)
        
        ctk.CTkCheckBox(
            balance_frame,
            text="Weather",
            variable=self.settings_balance_weath,
            command=lambda: self._save_balance_default(
                'balance_weather', self.settings_balance_weath
            )
        ).pack(anchor="w", pady=2)
        
        ctk.CTkCheckBox(
            balance_frame,
            text="Cameras",
            variable=self.settings_balance_cams,
            command=lambda: self._save_balance_default(
                'balance_cameras', self.settings_balance_cams
            )
        ).pack(anchor="w", pady=(2, 10))
        
        # Force Deficit Closure
        self.settings_force_closure = ctk.BooleanVar(
            value=self.settings_manager.get('generation_defaults', 'force_deficit_closure')
        )
        ctk.CTkCheckBox(
            gen_frame,
            text="⚡ Force Deficit Closure по умолчанию",
            variable=self.settings_force_closure,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._save_balance_default(
                'force_deficit_closure', self.settings_force_closure
            )
        ).pack(anchor="w", padx=15, pady=(5, 12))
    
    def _build_behavior_section(self, parent):
        """Секция поведения приложения"""
        behavior_frame = ctk.CTkFrame(parent)
        behavior_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        ctk.CTkLabel(
            behavior_frame,
            text="⚙️ Поведение приложения",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        self.settings_confirm_delete = ctk.BooleanVar(
            value=self.settings_manager.get('behavior', 'confirm_delete')
        )
        ctk.CTkCheckBox(
            behavior_frame,
            text="Подтверждение перед удалением",
            variable=self.settings_confirm_delete,
            command=lambda: self._save_behavior(
                'confirm_delete', self.settings_confirm_delete
            )
        ).pack(anchor="w", padx=15, pady=3)
    
    def _build_about_section(self, parent):
        """Секция информации о программе"""
        about_frame = ctk.CTkFrame(parent)
        about_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        ctk.CTkLabel(
            about_frame,
            text="ℹ️ О программе",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        # Версия
        ctk.CTkLabel(
            about_frame,
            text="Dataset Composer v1.1",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        # Описание
        ctk.CTkLabel(
            about_frame,
            text="Инструмент для создания и балансировки датасетов\n"
                 "для обучения Character LoRA моделей",
            text_color="gray70",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Автор
        author_row = ctk.CTkFrame(about_frame, fg_color="transparent")
        author_row.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(author_row, text="Автор:", width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(author_row, text="Vasily Taran", anchor="w").pack(side="left")
        
        # GitHub
        github_row = ctk.CTkFrame(about_frame, fg_color="transparent")
        github_row.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(github_row, text="GitHub:", width=120, anchor="w").pack(side="left")
        
        github_link = ctk.CTkLabel(
            github_row,
            text="dataset-composer",
            text_color=COLORS['primary_blue'],
            cursor="hand2"
        )
        github_link.pack(side="left")
        github_link.bind("<Button-1>", lambda e: self._open_github_link())
        
        # Используемые библиотеки
        libs_label = ctk.CTkLabel(
            about_frame,
            text="Используемые библиотеки:",
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        libs_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        libs_text = ctk.CTkLabel(
            about_frame,
            text="• CustomTkinter — современный UI фреймворк\n"
                 "• PyYAML — работа с YAML файлами\n"
                 "• tomli / tomli-w — работа с TOML файлами\n"
                 "• threading — многопоточность для генерации",
            text_color="gray70",
            justify="left",
            anchor="w"
        )
        libs_text.pack(anchor="w", padx=15, pady=(0, 12))
    
    # ════════════════════════════════════════════════════════════════
    # UI HELPERS
    # ════════════════════════════════════════════════════════════════
    
    def _create_path_row(
        self,
        parent,
        label: str,
        var: ctk.StringVar,
        browse_command,
        section: str,
        key: str
    ):
        """Создаёт строку с меткой, полем пути и кнопкой Browse."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=3)
        
        ctk.CTkLabel(row, text=label, width=180, anchor="w").pack(side="left")
        
        entry = ctk.CTkEntry(row, textvariable=var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        entry.bind(
            '<FocusOut>',
            lambda e, s=section, k=key, v=var: self._save_path(s, k, v.get())
        )
        
        ctk.CTkButton(
            row,
            text="Browse",
            width=80,
            command=browse_command
        ).pack(side="left")
    
    # ════════════════════════════════════════════════════════════════
    # ОБРАБОТЧИКИ СОБЫТИЙ
    # ════════════════════════════════════════════════════════════════
    
    def _save_path(self, section: str, key: str, value: str):
        """Сохраняет путь в настройки и уведомляет другие вкладки."""
        value = value.strip()
        self.settings_manager.set(section, key, value)
        self.on_settings_changed(section, key, value)
    
    def _browse_settings_output(self):
        """Выбор output папки через диалог."""
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.settings_output_dir_var.set(folder)
            self._save_path('directories', 'output_directory', folder)
    
    def _browse_settings_profiles(self):
        """Выбор profiles папки через диалог."""
        folder = filedialog.askdirectory(title="Select profiles folder")
        if folder:
            self.settings_profiles_dir_var.set(folder)
            self._save_path('directories', 'profiles_path', folder)
    
    def _reset_paths_to_defaults(self):
        """Сбрасывает все пути к дефолтным."""
        self.settings_manager.set('directories', 'output_directory', '')
        self.settings_manager.set('directories', 'profiles_path', '')
        
        # Обновляем UI
        self.settings_output_dir_var.set(self.output_directory)
        self.settings_profiles_dir_var.set(str(self.profiles_directory))
        
        # Уведомляем другие вкладки
        self.on_settings_changed('directories', 'output_directory', self.output_directory)
        self.on_settings_changed('directories', 'profiles_path', str(self.profiles_directory))
        
        self._log("🔄 Пути сброшены к значениям по умолчанию\n")
    
    def _save_scenes_default(self):
        """Сохраняет количество сцен по умолчанию."""
        try:
            value = int(self.settings_scenes_var.get())
            if value > 0:
                self.settings_manager.set('generation_defaults', 'num_scenes', value)
                self.on_settings_changed('generation_defaults', 'num_scenes', value)
        except ValueError:
            # Восстанавливаем предыдущее значение
            valid_value = self.settings_manager.get('generation_defaults', 'num_scenes')
            self.settings_scenes_var.set(str(valid_value))
    
    def _save_balance_default(self, key: str, var: ctk.BooleanVar | None):
        """Сохраняет настройку балансировки."""
        if var is None:
            return
        value = var.get()
        self.settings_manager.set('generation_defaults', key, value)
        self.on_settings_changed('generation_defaults', key, value)
    
    def _save_behavior(self, key: str, var: ctk.BooleanVar | None):
        """Сохраняет настройку поведения."""
        if var is None:
            return
        value = var.get()
        self.settings_manager.set('behavior', key, value)
        self.on_settings_changed('behavior', key, value)
    
    def _reset_all_settings(self):
        """Сбрасывает ВСЕ настройки к значениям по умолчанию."""
        if not messagebox.askyesno(
            "Сброс настроек",
            "Вы уверены, что хотите сбросить ВСЕ настройки?\n"
            "Это действие нельзя отменить."
        ):
            return
        
        self.settings_manager.reset_to_defaults()
        messagebox.showinfo(
            "Success",
            "Все настройки сброшены.\n"
            "Перезапустите приложение для полного применения."
        )
        self._log("🔄 Все настройки сброшены к значениям по умолчанию\n")
    
    def _open_github_link(self):
        """Открывает ссылку на GitHub в браузере."""
        github_url = self.settings_manager.get('about', 'github')
        if not github_url:
            github_url = "https://github.com/vasiltaran1506-creator/dataset-composer"
        
        webbrowser.open(github_url)
        self._log(f"🌐 Открыта ссылка: {github_url}\n")
    
    # ════════════════════════════════════════════════════════════════
    # ПУБЛИЧНЫЕ МЕТОДЫ
    # ════════════════════════════════════════════════════════════════
    
    def refresh(self):
        """
        Обновляет UI из settings_manager.
        Вызывается при переключении на вкладку или после внешних изменений.
        """
        if self.settings_output_dir_var:
            value = self.settings_manager.get('directories', 'output_directory') \
                    or self.output_directory
            self.settings_output_dir_var.set(value)
        
        if self.settings_profiles_dir_var:
            value = self.settings_manager.get('directories', 'profiles_path') \
                    or str(self.profiles_directory)
            self.settings_profiles_dir_var.set(value)
        
        if self.settings_scenes_var:
            value = self.settings_manager.get('generation_defaults', 'num_scenes')
            self.settings_scenes_var.set(str(value))
        
        if self.settings_balance_locs:
            self.settings_balance_locs.set(
                self.settings_manager.get('generation_defaults', 'balance_locations')
            )
        if self.settings_balance_acts:
            self.settings_balance_acts.set(
                self.settings_manager.get('generation_defaults', 'balance_actions')
            )
        if self.settings_balance_weath:
            self.settings_balance_weath.set(
                self.settings_manager.get('generation_defaults', 'balance_weather')
            )
        if self.settings_balance_cams:
            self.settings_balance_cams.set(
                self.settings_manager.get('generation_defaults', 'balance_cameras')
            )
        if self.settings_force_closure:
            self.settings_force_closure.set(
                self.settings_manager.get('generation_defaults', 'force_deficit_closure')
            )
        if self.settings_confirm_delete:
            self.settings_confirm_delete.set(
                self.settings_manager.get('behavior', 'confirm_delete')
            )
    
    def get_output_directory(self) -> str:
        """Возвращает текущий output путь."""
        if self.settings_output_dir_var:
            return self.settings_output_dir_var.get()
        return self.output_directory
    
    def get_num_scenes(self) -> int:
        """Возвращает количество сцен по умолчанию."""
        if self.settings_scenes_var:
            try:
                return int(self.settings_scenes_var.get())
            except ValueError:
                pass
        return self.settings_manager.get('generation_defaults', 'num_scenes') or 100
    
    def get_balance_flags(self) -> dict:
        """Возвращает словарь флагов балансировки."""
        return {
            'balance_locations': self.settings_balance_locs.get() 
                                 if self.settings_balance_locs else False,
            'balance_actions': self.settings_balance_acts.get() 
                               if self.settings_balance_acts else False,
            'balance_weather': self.settings_balance_weath.get() 
                               if self.settings_balance_weath else False,
            'balance_cameras': self.settings_balance_cams.get() 
                               if self.settings_balance_cams else False,
            'force_deficit_closure': self.settings_force_closure.get() 
                                     if self.settings_force_closure else False,
        }
    
    def should_confirm_delete(self) -> bool:
        """Возвращает флаг необходимости подтверждения удаления."""
        if self.settings_confirm_delete:
            return self.settings_confirm_delete.get()
        return self.settings_manager.get('behavior', 'confirm_delete')