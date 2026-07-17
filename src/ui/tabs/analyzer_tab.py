import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path

from config_loader import ConfigLoader
from coverage_tracker import CoverageTracker


class AnalyzerTab(ctk.CTkFrame):
    """Вкладка анализа покрытия датасета"""

    def __init__(
        self,
        master,
        project_root: Path,
        output_directory: Path,
        log_callback,
        load_tags_callback=None,
        on_auto_fix_deficit=None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        # Сохраняем ссылки
        self.project_root = project_root
        self.output_directory = output_directory
        self._log = log_callback                    # Глобальный лог (в MainWindow)
        self._load_tags_from_file = load_tags_callback or self._fallback_load_tags
        self._on_auto_fix_deficit = on_auto_fix_deficit  # Callback для Generate
        
        # UI-виджеты
        self.analyze_path_entry = None
        self.analyzer_textbox = None
        
        # Строим UI
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Analyzer"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # === ВЕРХНЯЯ ПАНЕЛЬ: Выбор папки + кнопки ===
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top_frame, text="📂 Analyze folder:", 
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, padx=(0, 10))
        
        self.analyze_path_entry = ctk.CTkEntry(top_frame, placeholder_text="Select folder with generated prompts...")
        self.analyze_path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        ctk.CTkButton(top_frame, text="Browse", width=90,
                      command=self._browse_analyze_folder).grid(row=0, column=2, padx=(0, 5))
        
        ctk.CTkButton(top_frame, text="🔍 Analyze", width=110,
                      fg_color="green", hover_color="darkgreen",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._run_analysis).grid(row=0, column=3, padx=(0, 5))
        
        ctk.CTkButton(top_frame, text="⚡ Auto-Fix", width=110,
                      fg_color="#3b82f6", hover_color="#2563eb",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._auto_fix_deficit).grid(row=0, column=4, padx=(0, 5))

        # === НИЖНЯЯ ПАНЕЛЬ: Лог анализа ===
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_header, text="📊 Analysis Results",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(log_header, text="📋 Copy", width=80,
                      command=self._copy_analyzer_to_clipboard).grid(row=0, column=1, padx=(5, 0))
        
        ctk.CTkButton(log_header, text="🗑️ Clear", width=80,
                      fg_color="gray40", hover_color="gray50",
                      command=self._clear_analyzer_log).grid(row=0, column=2, padx=(5, 0))

        self.analyzer_textbox = ctk.CTkTextbox(
            log_frame, 
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.analyzer_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")

    # ═══════════════════════════════════════════════
    # PUBLIC API (для синхронизации извне)
    # ═══════════════════════════════════════════════
    def set_output_directory(self, path):
        """Обновляет output_directory (вызывается из Settings)"""
        self.output_directory = path

    # ═══════════════════════════════════════════════
    # ОБРАБОТЧИКИ UI
    # ═══════════════════════════════════════════════
    def _browse_analyze_folder(self):
        folder = filedialog.askdirectory(title="Select folder to analyze")
        if folder and self.analyze_path_entry:
            self.analyze_path_entry.delete(0, "end")
            self.analyze_path_entry.insert(0, folder)

    def _auto_fix_deficit(self):
        """Передаёт папку анализа во вкладку Generate через callback"""
        if self.analyze_path_entry is None:
            return
        folder = self.analyze_path_entry.get().strip()
        if not folder:
            messagebox.showwarning("Warning", "Сначала выберите папку для анализа")
            return
        
        if self._on_auto_fix_deficit:
            self._on_auto_fix_deficit(folder)
        else:
            messagebox.showwarning("Warning", "Callback для Generate не настроен")

    def _clear_analyzer_log(self):
        if self.analyzer_textbox is None:
            return
        self.analyzer_textbox.delete("1.0", "end")

    def _copy_analyzer_to_clipboard(self):
        if self.analyzer_textbox is None:
            return
        content = self.analyzer_textbox.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Info", "Лог пуст")
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "✅ Скопировано!")

    # ═══════════════════════════════════════════════
    # ЛОГИРОВАНИЕ (локальный лог Analyzer)
    # ═══════════════════════════════════════════════
    def _analyzer_log(self, message: str):
        """
        Локальный лог Analyzer. Потокобезопасный:
        если вызов идёт из фонового потока, используем after().
        """
        if self.analyzer_textbox is None:
            return
        
        def _do_log():
            try:
                if self.analyzer_textbox and self.analyzer_textbox.winfo_exists():
                    self.analyzer_textbox.insert("end", message)
                    self.analyzer_textbox.see("end")
            except Exception:
                pass
        
        # Потокобезопасный вызов: если мы не в главном потоке, идём через after()
        try:
            self.after(0, _do_log)
        except Exception:
            _do_log()

    # ═══════════════════════════════════════════════
    # АНАЛИЗ
    # ═══════════════════════════════════════════════
    def _run_analysis(self):
        """Запускает анализ покрытия в отдельном потоке"""
        if self.analyze_path_entry is None:
            return
        folder = self.analyze_path_entry.get().strip()
        if not folder:
            messagebox.showwarning("Warning", "Выберите папку для анализа")
            return
        
        # Запускаем в фоне, чтобы UI не зависал
        threading.Thread(
            target=self._perform_analysis, 
            args=(folder,), 
            daemon=True
        ).start()

    def _perform_analysis(self, folder: str):
        """Основная логика анализа (выполняется в фоновом потоке)"""
        # Очищаем лог и начинаем анализ
        self.after(0, self._clear_analyzer_log)
        self._analyzer_log(f"🔍 Сканирование: {folder}\n")
        self._analyzer_log("=" * 70 + "\n")

        try:
            loader = ConfigLoader(project_root=str(self.project_root))
            rules = loader.load_scene_rules()
            
            available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
            available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
            available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
            available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]

            # Собираем маппинг тегов одежды -> категории
            outfit_category_map = {}
            clothing_dir = self.project_root / "prompt-library" / "02_clothing"
            if clothing_dir.exists():
                for txt_file in clothing_dir.rglob("*.txt"):
                    category = txt_file.parent.name  # topwear, bottomwear и т.д.
                    tags = self._load_tags_from_file(txt_file)
                    for tag in tags:
                        outfit_category_map[tag] = category

            tracker = CoverageTracker(
                available_locations=available_locs,
                available_actions=available_acts,
                available_weathers=available_weaths,
                available_cameras=available_cams,
                outfit_category_map=outfit_category_map
            )
            
            self._analyzer_log("📦 Запуск Coverage Tracker...\n")
            matrix = tracker.scan_folder(folder)
            
            if matrix["total_scenes"] == 0:
                self._analyzer_log("\n⚠️ Нет валидных промптов в папке.\n")
                return
            
            # Форматируем матрицу и выводим в GUI
            self._format_matrix_for_gui(matrix)
            self._analyzer_log("\n✅ Анализ завершён!\n")

        except Exception as e:
            self._analyzer_log(f"\n❌ Ошибка: {e}\n")
            import traceback
            self._analyzer_log(traceback.format_exc())
            # messagebox в потоке показывать НЕЛЬЗЯ — используем after
            self.after(0, lambda err=str(e): messagebox.showerror("Error", err))

    def _format_matrix_for_gui(self, matrix: dict):
        """Форматирует матрицу покрытия для красивого вывода в текстовое поле"""
        for dimension, display_name in {
            "location": "📍 ЛОКАЦИИ",
            "action": "🎬 ДЕЙСТВИЯ",
            "weather": "🌦️ ПОГОДА",
            "camera": "📸 КАМЕРЫ",
            "outfit": "👗 ОДЕЖДА"
        }.items():
            counts = matrix["dimensions"].get(dimension, {})
            percentages = matrix["percentages"].get(dimension, {})
            
            if not counts:
                continue
            
            self._analyzer_log(f"\n{display_name}:\n" + "-" * 70 + "\n")
            
            for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                pct = percentages.get(category, 0)
                bar_length = int(pct / 2)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                
                status = ""
                deficit_key = f"{dimension}.{category}"
                if deficit_key in matrix["status"].get("deficits", []):
                    status = " 🔻 ДЕФИЦИТ"
                elif deficit_key in matrix["status"].get("overflows", []):
                    status = " ⚠️ ПЕРЕИЗБЫТОК"
                
                self._analyzer_log(
                    f"   {category:25s}: {count:3d} ({pct:5.1f}%) [{bar}]{status}\n"
                )
        
        # Итоговая сводка
        self._analyzer_log("\n" + "=" * 70 + "\n📋 СВОДКА:\n")
        deficits = matrix["status"].get("deficits", [])
        overflows = matrix["status"].get("overflows", [])
        
        if deficits:
            self._analyzer_log(f"   🔻 Дефицит: {', '.join(deficits)}\n")
        if overflows:
            self._analyzer_log(f"   ⚠️ Переизбыток: {', '.join(overflows)}\n")
        if not deficits and not overflows:
            self._analyzer_log("   ✅ Баланс идеален!\n")
        
        self._analyzer_log("=" * 70 + "\n")

    # ═══════════════════════════════════════════════
    # FALLBACK
    # ═══════════════════════════════════════════════
    def _fallback_load_tags(self, file_path) -> list:
        """Запасной вариант загрузки тегов, если callback не передан"""
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