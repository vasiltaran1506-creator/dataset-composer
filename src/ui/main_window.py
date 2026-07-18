import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
from pathlib import Path
import threading

# === FIX для PyInstaller ===
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))
meipass = getattr(sys, '_MEIPASS', None)
if meipass is not None:
    sys.path.insert(0, meipass)
# ============================

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
        if os.name == 'nt':
            import ctypes
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(handle, 0x00008000)
        else:
            os.nice(-5)
    except Exception:
        pass


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
        self.title("Dataset Composer v1.1 - Character LoRA Pipeline")
        self.geometry("1600x1000")
        self.minsize(1400, 900)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Пути к директориям проекта ===
        if hasattr(sys, '_MEIPASS'):
            self.project_root = Path(sys.executable).parent
        else:
            self.project_root = Path(__file__).parent.parent.parent

        # === Менеджер настроек ===
        self.settings_manager = SettingsManager(self.project_root / "settings.json")

        # === Пути к папкам ===
        saved_output = self.settings_manager.get('directories', 'output_directory')
        self.output_directory = Path(saved_output) if saved_output else Path(r"D:\VASILY\MY GENERATION\Test Generations")

        saved_profiles = self.settings_manager.get('directories', 'profiles_path')
        self.profiles_directory = Path(saved_profiles) if saved_profiles else self.project_root / "character-profiles"
        self.profiles_directory.mkdir(exist_ok=True)

        # === Ссылки на виджеты вкладок (для синхронизации) ===
        self.profiles_tab_widget = None
        self.library_tab_widget = None
        self.generate_tab_widget = None
        self.analyzer_tab_widget = None
        self.settings_tab_widget = None

        # === Кэш тегов (используется Analyzer и Profiles) ===
        self._tags_cache = {}

        # === Debouncing ===
        self._update_timer = None
        self._configure_timer = None

        # === Флаги инициализации вкладок ===
        self._tabs_created = {
            'Profiles': False,
            'Library': False,
            'Generate': False,
            'Analyzer': False,
            'Settings': False
        }

        # === Главный TabView ===
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Profiles")
        self.tabview.add("Library")
        self.tabview.add("Generate")
        self.tabview.add("Analyzer")
        self.tabview.add("Settings")

        # 👇 Создаём только Profiles и Generate сразу (часто используемые)
        self._create_profiles_tab()
        self._create_generate_tab()

        # Обработчики
        self.tabview.configure(command=self._on_main_tab_changed)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.bind('<Configure>', self._on_window_configure)

        # 👇 ФИКС ФАНТОМОВ ПРИ СТАРТЕ
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 1600) // 2
        y = (screen_height - 1000) // 2
        self.geometry(f"+{x}+{y}")
        self.withdraw()
        self.deiconify()
        self.update()
        self.update()
        self.after(100, lambda: self.update_idletasks())

    # ════════════════════════════════════════════════════════════════════════
    # 2. СОЗДАНИЕ ВКЛАДОК (ленивая инициализация через импорты)
    # ════════════════════════════════════════════════════════════════════════
    def _on_main_tab_changed(self):
        """Обработчик смены вкладки с ленивой инициализацией"""
        try:
            current_tab = self.tabview.get()
            if current_tab == "Library" and not self._tabs_created.get('Library', False):
                self._create_library_tab()
            elif current_tab == "Analyzer" and not self._tabs_created.get('Analyzer', False):
                self._create_analyzer_tab()
            elif current_tab == "Settings" and not self._tabs_created.get('Settings', False):
                self._create_settings_tab()
            self.update_idletasks()
            self.after(10, lambda: self.update_idletasks())
        except Exception as e:
            import traceback
            print(f"⚠️ Ошибка при создании вкладки: {e}")
            traceback.print_exc()

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

    def _create_generate_tab(self):
        """Создает вкладку Generate через GenerateTab класс"""
        if self._tabs_created.get('Generate', False):
            return
        self._tabs_created['Generate'] = True

        tab = self.tabview.tab("Generate")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        from ui.tabs.generate_tab import GenerateTab

        self.generate_tab_widget = GenerateTab(
            master=tab,
            settings_manager=self.settings_manager,
            project_root=self.project_root,
            profiles_directory=self.profiles_directory,
            # SettingsTab expects a string path for output_directory
            output_directory=(str(self.output_directory) if isinstance(self.output_directory, Path) else self.output_directory),
            log_callback=self._log,
            on_generate_settings_changed=self._on_generate_settings_changed
        )
        self.generate_tab_widget.grid(row=0, column=0, sticky="nsew")

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
            output_directory=Path(self.output_directory),
            log_callback=self._log,
            load_tags_callback=self._load_tags_from_file,
            on_auto_fix_deficit=self._on_analyzer_auto_fix,
        )
        self.analyzer_tab_widget.grid(row=0, column=0, sticky="nsew")

    def _create_settings_tab(self):
        """Создает вкладку Settings через SettingsTab класс"""
        if self._tabs_created.get("Settings", False):
            return
        self._tabs_created["Settings"] = True

        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        from ui.tabs.settings_tab import SettingsTab

        self.settings_tab_widget = SettingsTab(
            master=tab,
            settings_manager=self.settings_manager,
            project_root=self.project_root,
            output_directory=str(self.output_directory),
            profiles_directory=self.profiles_directory,
            log_callback=self._log,
            on_settings_changed=self._on_settings_changed
        )
        self.settings_tab_widget.grid(row=0, column=0, sticky="nsew")

    # ════════════════════════════════════════════════════════════════════════
    # 3. СИНХРОНИЗАЦИЯ МЕЖДУ ВКЛАДКАМИ (Callbacks)
    # ════════════════════════════════════════════════════════════════════════
    def _on_settings_changed(self, section: str, key: str, value):
        """Callback от SettingsTab: синхронизируем изменения с Generate и Analyzer"""
        if section == 'directories' and key == 'output_directory':
            self.output_directory = Path(value) if not isinstance(value, Path) else value
            if self.generate_tab_widget:
                self.generate_tab_widget.set_output_directory(value)
            if self.analyzer_tab_widget:
                self.analyzer_tab_widget.set_output_directory(value)
        elif section == 'generation_defaults' and key == 'num_scenes':
            if self.generate_tab_widget:
                self.generate_tab_widget.set_num_scenes(value)
        elif section == 'generation_defaults':
            if self.generate_tab_widget:
                self.generate_tab_widget.set_balance_var(key, value)

    def _on_generate_settings_changed(self, section: str, key: str, value):
        """Callback от GenerateTab: синхронизируем изменения с Settings"""
        if section == 'directories' and key == 'output_directory':
            self.output_directory = Path(value) if not isinstance(value, Path) else value
            # Use safe getattr calls to avoid static analysis issues when SettingsTab
            # may not expose all optional methods.
            if self.settings_tab_widget:
                getattr(self.settings_tab_widget, 'set_output_directory', lambda v: None)(value)
            if self.analyzer_tab_widget:
                self.analyzer_tab_widget.set_output_directory(value)
        elif section == 'generation_defaults':
            if self.settings_tab_widget:
                if key == 'num_scenes':
                    getattr(self.settings_tab_widget, 'set_num_scenes', lambda v: None)(value)
                else:
                    getattr(self.settings_tab_widget, 'set_balance_var', lambda k, v: None)(key, value)

    def _on_analyzer_auto_fix(self, folder: str):
        """Callback от AnalyzerTab: передаём папку анализа во вкладку Generate"""
        self.tabview.set("Generate")

        if self.generate_tab_widget:
            self.generate_tab_widget.set_balance_folder(folder)
            messagebox.showinfo(
                "Auto-Fix Ready",
                f"✅ Balance from: {folder}\nНажмите '🚀 Generate Batch'!"
            )
        else:
            messagebox.showwarning("Warning", "Вкладка Generate ещё не инициализирована.")

    # ════════════════════════════════════════════════════════════════════════
    # 4. УТИЛИТЫ (общие для всех вкладок)
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
    # 5. ЛОГИРОВАНИЕ И WINDOW MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════
    def _log(self, message):
        """Глобальный лог: печатает в консоль (UI-логи теперь внутри отдельных вкладок)"""
        print(message, end='')

    def _debounced_update(self, delay_ms: int = 100):
        """Откладывает update_idletasks, вызывая его не чаще 1 раза в delay_ms"""
        if self._update_timer:
            self.after_cancel(self._update_timer)
        self._update_timer = self.after(delay_ms, self._do_update)

    def _do_update(self):
        """Выполняет отложенный update_idletasks"""
        self._update_timer = None
        try:
            self.update_idletasks()
        except Exception:
            pass

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

    def _on_window_configure(self, event):
        """Обработчик изменения размера/позиции окна (debounced redraw)."""
        if event.widget != self:
            return
        if self._configure_timer:
            self.after_cancel(self._configure_timer)
        self._configure_timer = self.after(50, self._force_redraw_after_configure)

    def _force_redraw_after_configure(self):
        """Принудительная перерисовка после остановки движения окна"""
        self._configure_timer = None
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