import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import json

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

class LibraryTab(ctk.CTkFrame):
    """Вкладка редактирования библиотеки тегов и scene-rules"""

    # Константы для бейджей (дублируем из MainWindow)
    BADGE_GROUPS = {
        'outfit': ['allowed_outfit_categories', 'excludes_outfit_categories', 'preferred_outfit_categories', 'avoid_outfit_categories'],
        'actions': ['allowed_actions', 'excludes_actions', 'prefers_actions', 'avoid_actions'],
        'props': ['required_props', 'required_props_pool', 'prefers_props', 'excludes_props', 'avoid_props'],
        'lighting': ['excludes_lighting_sources', 'prefers_lighting_sources', 'avoid_lighting_sources'],
        'weather': ['excludes_weather', 'prefers_weather', 'avoid_weather'],
        'locations': ['allowed_locations', 'excluded_locations', 'prefers_locations', 'avoid_locations'],
        'poses': ['allowed_poses', 'excludes_poses', 'prefers_poses', 'avoid_poses'],
        'camera': ['excludes_camera', 'prefers_camera', 'avoid_camera'],
    }
    
    BADGE_PRIORITY = {
        'allowed': 4, 'required': 4, 'excluded': 3, 'preferred': 2, 'avoided': 1,
    }
    
    BADGE_COLORS = {
        'allowed': '#4ade80', 'required': '#4ade80', 'excluded': '#f87171',
        'preferred': '#60a5fa', 'avoided': '#fb923c',
    }

    def __init__(
        self,
        master,
        project_root: Path,
        log_callback,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.project_root = project_root
        self._log = log_callback
        
        # Состояние
        self.library_tree = None
        self.library_editor_frame = None
        self.library_tags_container = None
        self.library_search_entry = None
        self.library_current_file = None
        self.library_tags = []
        
        # Scene Rules
        self.scene_rules_scroll = None
        self.scene_rules_list_frame = None
        self.scene_rules_editor_frame = None
        self.auto_sync_var = None
        self.scene_rules_data = {}
        self.current_rule_file = None
        self._badge_widgets = {}
        self._current_checkboxes = {}
        
        # Кэш
        self._tags_cache = {}
        self._all_tags_category_cache = {}
        
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт интерфейс вкладки Library"""
        library_tabview = ctk.CTkTabview(self)
        library_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        library_tabview.add("📚 Tag Editor")
        library_tabview.add("🎬 Scene Rules")
        
        self._create_tag_editor_content(library_tabview.tab("📚 Tag Editor"))
        self._create_scene_rules_content(library_tabview.tab("🎬 Scene Rules"))

    # ═══════════════════════════════════════════════
    # TAG EDITOR
    # ═══════════════════════════════════════════════
    def _create_tag_editor_content(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)
        
        # Левая панель
        left_frame = ctk.CTkFrame(tab)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(left_frame, text="📚 Prompt Library",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        self.library_tree = ctk.CTkScrollableFrame(left_frame)
        self.library_tree.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        self._build_library_tree()
        
        # Правая панель
        right_frame = ctk.CTkFrame(tab)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(2, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self.library_editor_title = ctk.CTkLabel(right_frame, text="📝 Tag Editor (select a file)",
                                                 font=ctk.CTkFont(size=18, weight="bold"))
        self.library_editor_title.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        search_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.library_search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search tags...")
        self.library_search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.library_search_entry.bind('<KeyRelease>', lambda e: self._filter_library_tags())
        
        ctk.CTkButton(search_frame, text="Clear", width=60,
                      command=self._clear_library_search).grid(row=0, column=1)
        
        self.library_tags_container = ctk.CTkScrollableFrame(right_frame)
        self.library_tags_container.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="nsew")
        
        add_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        add_frame.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        add_frame.grid_columnconfigure(0, weight=1)
        
        self.new_tag_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter new tag...")
        self.new_tag_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.new_tag_entry.bind('<Return>', lambda e: self._add_library_tag())
        
        ctk.CTkButton(add_frame, text="➕ Add Tag", width=100,
                      fg_color="green", hover_color="darkgreen",
                      command=self._add_library_tag).grid(row=0, column=1)
        
        self.library_editor_frame = right_frame

    def _build_library_tree(self):
        if self.library_tree is None:
            return
        for w in self.library_tree.winfo_children():
            w.destroy()
        
        library_dir = self.project_root / "prompt-library"
        if not library_dir.exists():
            ctk.CTkLabel(self.library_tree, text=f"⚠️ Папка не найдена: {library_dir}",
                         text_color="red").pack(pady=20)
            return
        
        categories = {}
        for txt_file in sorted(library_dir.rglob("*.txt")):
            parts = txt_file.relative_to(library_dir).parts
            if len(parts) >= 2:
                main_cat, sub_cat = parts[0], parts[1].replace('.txt', '')
            elif len(parts) == 1:
                main_cat, sub_cat = "general", parts[0].replace('.txt', '')
            else:
                continue
            
            if main_cat not in categories:
                categories[main_cat] = {}
            if sub_cat not in categories[main_cat]:
                categories[main_cat][sub_cat] = []
            categories[main_cat][sub_cat].append(txt_file)
        
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
                    ctk.CTkButton(sub_container, text=f"📄 {txt_file.name}",
                                  anchor="w", fg_color="transparent",
                                  text_color=("gray10", "gray90"),
                                  hover_color=("gray85", "gray30"),
                                  command=lambda f=txt_file: self._load_library_file(f)).pack(fill="x", padx=(20, 0), pady=1)

    def _toggle_library_section(self, container):
        if container.winfo_ismapped():
            self._hide_container(container)
        else:
            self._show_container(container, padx=(20, 0))

    def _load_library_file(self, file_path: Path):
        self.library_current_file = file_path
        self.library_tags = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.library_tags.append(line)
        except Exception as e:
            self._log(f"❌ Ошибка чтения {file_path}: {e}\n")
            return
        
        if self.library_editor_title:
            rel_path = file_path.relative_to(self.project_root / "prompt-library")
            self.library_editor_title.configure(text=f"📝 {rel_path} ({len(self.library_tags)} tags)")
        
        self._display_library_tags()
        if self.library_search_entry:
            self.library_search_entry.delete(0, "end")

    def _display_library_tags(self, filter_text: str = ""):
        if self.library_tags_container is None:
            return
        for w in self.library_tags_container.winfo_children():
            w.destroy()
        
        if not self.library_tags:
            ctk.CTkLabel(self.library_tags_container, text="(No tags in this file)",
                         text_color="gray").pack(anchor="w", padx=10, pady=10)
            return
        
        filtered_tags = self.library_tags
        if filter_text:
            filter_lower = filter_text.lower()
            filtered_tags = [t for t in self.library_tags if filter_lower in t.lower()]
        
        if not filtered_tags:
            ctk.CTkLabel(self.library_tags_container, text=f"(No tags match '{filter_text}')",
                         text_color="gray").pack(anchor="w", padx=10, pady=10)
            return
        
        for i, tag in enumerate(filtered_tags):
            tag_row = ctk.CTkFrame(self.library_tags_container, fg_color="transparent")
            tag_row.pack(fill="x", pady=1)
            
            tag_label = ctk.CTkLabel(tag_row, text=f"  • {tag}", anchor="w")
            tag_label.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            ctk.CTkButton(tag_row, text="×", width=30, height=25,
                          fg_color="#dc2626", hover_color="#991b1b",
                          command=lambda t=tag: self._delete_library_tag(t)).pack(side="right", padx=(5, 0))

    def _filter_library_tags(self):
        if self.library_search_entry is None:
            return
        filter_text = self.library_search_entry.get().strip()
        self._display_library_tags(filter_text)

    def _clear_library_search(self):
        if self.library_search_entry:
            self.library_search_entry.delete(0, "end")
            self._display_library_tags()

    def _add_library_tag(self):
        if self.library_current_file is None:
            messagebox.showwarning("Warning", "Сначала выберите файл")
            return
        if not hasattr(self, 'new_tag_entry') or self.new_tag_entry is None:
            return
        
        new_tag = self.new_tag_entry.get().strip()
        if not new_tag:
            return
        if new_tag in self.library_tags:
            messagebox.showwarning("Warning", f"Тег '{new_tag}' уже существует")
            return
        
        self.library_tags.append(new_tag)
        self.new_tag_entry.delete(0, "end")
        self._save_library_file()
        self._display_library_tags()
        
        if self.library_editor_title:
            rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
            self.library_editor_title.configure(text=f"📝 {rel_path} ({len(self.library_tags)} tags)")
        
        self._log(f"➕ Добавлен тег: {new_tag}\n")

    def _delete_library_tag(self, tag: str):
        if self.library_current_file is None:
            return
        
        if not messagebox.askyesno("Confirm Delete", f"Удалить тег '{tag}'?"):
            return
        
        if tag in self.library_tags:
            self.library_tags.remove(tag)
            self._save_library_file()
        
        filter_text = self.library_search_entry.get().strip() if self.library_search_entry else ""
        self._display_library_tags(filter_text)
        
        if self.library_editor_title:
            rel_path = self.library_current_file.relative_to(self.project_root / "prompt-library")
            self.library_editor_title.configure(text=f"📝 {rel_path} ({len(self.library_tags)} tags)")
        
        self._log(f"🗑️ Удалён тег: {tag}\n")

    def _save_library_file(self):
        if self.library_current_file is None:
            return
        try:
            with open(self.library_current_file, 'w', encoding='utf-8') as f:
                for tag in self.library_tags:
                    f.write(f"{tag}\n")
            
            cache_key = str(self.library_current_file)
            if cache_key in self._tags_cache:
                del self._tags_cache[cache_key]
            
            self._invalidate_category_cache()
            self._log(f"💾 Файл сохранён: {self.library_current_file.name}\n")
        except Exception as e:
            self._log(f"❌ Ошибка сохранения: {e}\n")
            messagebox.showerror("Error", f"Не удалось сохранить файл: {e}")

    # ═══════════════════════════════════════════════
    # SCENE RULES
    # ═══════════════════════════════════════════════
    def _create_scene_rules_content(self, tab):
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))
        top_frame.grid_columnconfigure(1, weight=1)
        
        sync_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        sync_frame.pack(side="left", padx=(10, 5))
        
        self.auto_sync_var = ctk.BooleanVar(value=True)
        sync_switch = ctk.CTkSwitch(sync_frame, text="Auto-sync", variable=self.auto_sync_var,
                                    command=self._on_auto_sync_toggled)
        sync_switch.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(sync_frame, text="?", width=25, height=25,
                      fg_color="gray40", hover_color="gray50",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      corner_radius=12,
                      command=self._show_auto_sync_help).pack(side="left")
        
        ctk.CTkButton(top_frame, text="🔄 Reload", width=100,
                      fg_color="gray40", hover_color="gray50",
                      command=self._reload_scene_rules).pack(side="right", padx=(5, 10))
        
        ctk.CTkButton(top_frame, text="💾 Save All", width=100,
                      fg_color="green", hover_color="darkgreen",
                      command=self._save_scene_rules).pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(top_frame, text="✅ Validate", width=100,
                      fg_color="#3b82f6", hover_color="#2563eb",
                      command=self._validate_scene_rules_integrity).pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(top_frame, text="🔧 Auto-fix", width=100,
                      fg_color="#3b82f6", hover_color="#2563eb",
                      command=self._auto_fix_tag_format).pack(side="right", padx=(5, 0))
        
        content_frame = ctk.CTkFrame(tab)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        left_wrapper = ctk.CTkFrame(content_frame, width=280)
        left_wrapper.grid(row=0, column=0, padx=(5, 2), pady=5, sticky="nsew")
        left_wrapper.grid_propagate(False)
        left_wrapper.grid_rowconfigure(0, weight=1)
        left_wrapper.grid_columnconfigure(0, weight=1)
        
        self.scene_rules_list_frame = ctk.CTkScrollableFrame(left_wrapper, width=260)
        self.scene_rules_list_frame.grid(row=0, column=0, sticky="nsew")
        
        self.scene_rules_editor_frame = ctk.CTkFrame(content_frame)
        self.scene_rules_editor_frame.grid(row=0, column=1, padx=(2, 5), pady=5, sticky="nsew")
        
        placeholder = ctk.CTkLabel(self.scene_rules_editor_frame,
                                   text="👈 Выберите правило слева для редактирования",
                                   font=ctk.CTkFont(size=14),
                                   text_color="gray")
        placeholder.pack(expand=True)
        
        self._load_scene_rules()
        self._build_scene_rules_list()

    def _show_auto_sync_help(self):
        help_text = (
            "🔄 Автосинхронизация связей\n\n"
            "Когда ВКЛЮЧЕНА:\n"
            "• Если вы добавляете действие 'reading' в список предпочтений локации 'library'\n"
            "• Программа автоматически добавит 'library' в список предпочтений действия 'reading'\n"
            "• Это обеспечивает консистентность данных\n\n"
            "Когда ВЫКЛЮЧЕНА:\n"
            "• Вы полностью контролируете все связи вручную\n"
            "• Изменения в одном файле не влияют на другие\n"
            "• Полезно для тонкой настройки или исправления ошибок\n\n"
            "Рекомендация:\n"
            "Оставьте включенной для большинства случаев. "
            "Отключайте только если нужно создать асимметричные связи."
        )
        messagebox.showinfo("Auto-sync Help", help_text)

    def _on_auto_sync_toggled(self):
        if self.auto_sync_var is None:
            return
        if self.auto_sync_var.get():
            self._log("🔄 Автосинхронизация ВКЛЮЧЕНА\n")
        else:
            self._log("🔒 Автосинхронизация ВЫКЛЮЧЕНА (ручной режим)\n")

    def _load_scene_rules(self):
        """Загружает все TOML-файлы из папки scene-rules"""
        self.scene_rules_data = {}
        rules_dir = self.project_root / "scene-rules"
        if not rules_dir.exists():
            self._log(f"⚠️ Папка scene-rules не найдена: {rules_dir}\n")
            return
        
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
        
        total_files = sum(len(v) for v in self.scene_rules_data.values())
        self._log(f"✅ Загружено {total_files} scene-rules файлов\n")

    def _build_scene_rules_list(self):
        """Строит список правил в левой панели с кнопками добавления"""
        if self.scene_rules_list_frame is None:
            return
        
        for w in self.scene_rules_list_frame.winfo_children():
            w.destroy()
        
        if not self.scene_rules_data:
            ctk.CTkLabel(self.scene_rules_list_frame,
                         text="(No rules loaded)",
                         text_color="gray").pack(pady=10)
            return
        
        for category_name, rules in sorted(self.scene_rules_data.items()):
            cat_frame = ctk.CTkFrame(self.scene_rules_list_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=2)
            
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
                rule_row = ctk.CTkFrame(cat_container, fg_color="transparent")
                rule_row.pack(fill="x", padx=(20, 0), pady=1)
                
                rule_btn = ctk.CTkButton(
                    rule_row,
                    text=f"📄 {rule_name}",
                    anchor="w", fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray85", "gray30"),
                    command=lambda c=category_name, r=rule_name: self._select_scene_rule(c, r)
                )
                rule_btn.pack(side="left", fill="x", expand=True)
                
                delete_btn = ctk.CTkButton(
                    rule_row,
                    text="🗑️",
                    width=30, height=30,
                    fg_color="gray40", hover_color="gray50",
                    font=ctk.CTkFont(size=12),
                    command=lambda c=category_name, r=rule_name: self._delete_scene_rule(c, r)
                )
                delete_btn.pack(side="right", padx=(5, 0))

    def _create_new_rule(self, category: str):
        """Создает новое правило"""
        new_name = f"new_{category.lower().replace(' ', '_')}_rule"
        
        if new_name in self.scene_rules_data.get(category, {}):
            counter = 1
            while f"{new_name}_{counter}" in self.scene_rules_data.get(category, {}):
                counter += 1
            new_name = f"{new_name}_{counter}"
        
        rules_dir = self.project_root / "scene-rules" / category
        rules_dir.mkdir(parents=True, exist_ok=True)
        new_file_path = rules_dir / f"{new_name}.toml"
        
        new_data = {
            'meta': {
                'id': new_name,
                'display_name': new_name.replace('_', ' ').title(),
            },
            'soft_constraints': {},
            'hard_constraints': {}
        }
        
        if category == 'locations':
            new_data['meta']['type'] = 'indoor_private'
        
        try:
            import tomli_w
            with open(new_file_path, 'wb') as f:
                tomli_w.dump(new_data, f)
        except ImportError:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(f'[meta]\nid = "{new_name}"\n')
                f.write(f'display_name = "{new_data["meta"]["display_name"]}"\n')
                if category == 'locations':
                    f.write('type = "indoor_private"\n')
                f.write("\n[soft_constraints]\n[hard_constraints]\n")
        except Exception as e:
            self._log(f"❌ Ошибка создания: {e}\n")
            messagebox.showerror("Error", f"Failed: {e}")
            return
        
        if category not in self.scene_rules_data:
            self.scene_rules_data[category] = {}
        self.scene_rules_data[category][new_name] = {
            'path': new_file_path,
            'data': new_data
        }
        
        if self.scene_rules_list_frame is not None:
            self._add_rule_button_to_list(category, new_name)
        
        self._select_scene_rule(category, new_name)
        self._log(f"➕ Создано новое правило: {category}/{new_name}\n")
        messagebox.showinfo("Success", f"New rule '{new_name}' created!")

    def _add_rule_button_to_list(self, category: str, rule_name: str):
        """Добавляет ОДНУ кнопку правила в существующий список"""
        if self.scene_rules_list_frame is None:
            return
        
        target_container = None
        for cat_frame in self.scene_rules_list_frame.winfo_children():
            if not isinstance(cat_frame, ctk.CTkFrame):
                continue
            for child in cat_frame.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    text = child.cget("text")
                    if category.replace('_', ' ').title() in text:
                        children = cat_frame.winfo_children()
                        if len(children) >= 2:
                            target_container = children[-1]
                            break
        
        if target_container is None:
            for cat_frame in self.scene_rules_list_frame.winfo_children():
                for child in cat_frame.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkButton):
                                target_container = child
                                break
                        if target_container:
                            break
                if target_container:
                    break
        
        if target_container is None:
            target_container = ctk.CTkFrame(self.scene_rules_list_frame, fg_color="transparent")
            target_container.pack(fill="x", padx=(20, 0))
        
        if not target_container.winfo_ismapped():
            target_container.pack(fill="x", padx=(20, 0))
        
        rule_btn = ctk.CTkButton(
            target_container,
            text=f"📄 {rule_name}",
            anchor="w", fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray30"),
            command=lambda c=category, r=rule_name: self._select_scene_rule(c, r)
        )
        rule_btn.pack(fill="x", padx=(20, 0), pady=1)

    def _toggle_scene_rules_section(self, container):
        """Разворачивает/сворачивает категорию в списке"""
        if container.winfo_ismapped():
            self._hide_container(container)
        else:
            self._show_container(container, padx=(20, 0))
        self.after(10, lambda: self.update_idletasks())

    def _select_scene_rule(self, category: str, rule_name: str):
        """Обработчик выбора правила из списка"""
        editor_frame = self.scene_rules_editor_frame
        if editor_frame is None:
            return
        
        if hasattr(self, '_current_checkboxes'):
            self._current_checkboxes = {}
        
        for w in editor_frame.winfo_children():
            w.destroy()
        
        editor_frame.update_idletasks()
        self.after(10, lambda: self.update())
        
        rule_data = self.scene_rules_data[category][rule_name]
        self.current_rule_file = rule_data['path']
        data = rule_data['data']
        meta = data.get('meta', {})
        
        self._log(f"📄 Редактирование: {category}/{rule_name}\n")
        
        header_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(header_frame,
                     text=f"📝 {meta.get('display_name', rule_name)}",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkLabel(header_frame,
                     text=f"({category}/{rule_name}.toml)",
                     text_color="gray60").pack(side="left", padx=(10, 0))
        
        loading_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        loading_frame.pack(fill="both", expand=True, padx=10, pady=50)
        ctk.CTkLabel(loading_frame,
                     text="⏳ Загрузка...",
                     font=ctk.CTkFont(size=16),
                     text_color="gray60").pack(expand=True)
        
        editor_frame.update_idletasks()
        self.after(10, lambda: self._render_scene_rule_content(
            category, rule_name, rule_data, data, meta, loading_frame))

    def _render_scene_rule_content(self, category, rule_name, rule_data, data, meta, loading_frame):
        """Отложенный рендеринг содержимого Scene Rule"""
        if loading_frame and loading_frame.winfo_exists():
            loading_frame.destroy()
        
        try:
            scroll_frame = ctk.CTkScrollableFrame(self.scene_rules_editor_frame)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            self._render_meta_section(scroll_frame, meta, category)
            
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
            
            if self.scene_rules_editor_frame is not None:
                self.scene_rules_editor_frame.update_idletasks()
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self._log(f"\n❌ ОШИБКА при рендеринге {category}/{rule_name}:\n{error_msg}\n")
            
            if self.scene_rules_editor_frame is not None:
                error_frame = ctk.CTkFrame(self.scene_rules_editor_frame, fg_color="#2d1b1b")
                error_frame.pack(fill="both", expand=True, padx=10, pady=10)
                ctk.CTkLabel(
                    error_frame,
                    text=f"❌ Ошибка рендеринга: {e}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#ff6b6b"
                ).pack(anchor="w", padx=15, pady=(15, 5))
                ctk.CTkLabel(
                    error_frame,
                    text=f"Категория: {category}/{rule_name}\nСмотри лог для деталей.",
                    text_color="#ff9999",
                    justify="left"
                ).pack(anchor="w", padx=15, pady=(0, 15))

    def _render_meta_section(self, parent, meta: dict, category: str):
        """Рендерит секцию meta-информации"""
        meta_frame = ctk.CTkFrame(parent)
        meta_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(meta_frame, text="🏷️ Meta Information",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 5))
        
        id_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
        id_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(id_row, text="ID:", width=120, anchor="w").pack(side="left")
        id_entry = ctk.CTkEntry(id_row, width=300)
        id_entry.pack(side="left")
        id_entry.insert(0, meta.get('id', ''))
        id_entry.bind('<FocusOut>', lambda e: self._save_meta_changes('id', id_entry.get()))
        
        name_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
        name_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(name_row, text="Display Name:", width=120, anchor="w").pack(side="left")
        name_entry = ctk.CTkEntry(name_row, width=300)
        name_entry.pack(side="left")
        name_entry.insert(0, meta.get('display_name', ''))
        name_entry.bind('<FocusOut>', lambda e: self._save_meta_changes('display_name', name_entry.get()))
        
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
        
        try:
            rel_path = self.current_rule_file.relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) < 2:
                return
            category = parts[0]
            rule_name = parts[1].replace('.toml', '')
        except Exception:
            return
        
        rule_data = self.scene_rules_data.get(category, {}).get(rule_name, {}).get('data', {})
        if not rule_data:
            return
        
        if 'meta' not in rule_data:
            rule_data['meta'] = {}
        
        old_value = rule_data['meta'].get(field, '')
        if old_value == new_value:
            return
        
        rule_data['meta'][field] = new_value
        
        try:
            import tomli_w
            with open(self.current_rule_file, 'wb') as f:
                tomli_w.dump(rule_data, f)
        except ImportError:
            self._write_toml_manually(self.current_rule_file, rule_data)
        
        if field == 'id' and new_value != rule_name:
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
                self.scene_rules_data[category][safe_name] = self.scene_rules_data[category].pop(rule_name)
                self.scene_rules_data[category][safe_name]['path'] = new_file_path
                self.scene_rules_data[category][safe_name]['data']['meta']['id'] = safe_name
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

    def _render_section_header(self, parent, title: str, emoji: str = "📋"):
        """Рендерит визуальный разделитель секции"""
        separator_frame = ctk.CTkFrame(parent, fg_color="transparent")
        separator_frame.pack(fill="x", padx=5, pady=(20, 5))
        
        top_line = ctk.CTkFrame(separator_frame, height=2, fg_color="gray40")
        top_line.pack(fill="x", padx=10, pady=(0, 5))
        
        header_frame = ctk.CTkFrame(separator_frame, fg_color="gray30", corner_radius=8)
        header_frame.pack(fill="x", padx=5, pady=(0, 5))
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{emoji} {title}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white"
        )
        title_label.pack(anchor="w", padx=15, pady=8)
        
        bottom_line = ctk.CTkFrame(separator_frame, height=2, fg_color="gray40")
        bottom_line.pack(fill="x", padx=10, pady=(5, 0))

    def _get_badge_group(self, constraint_key: str) -> str | None:
        """Определяет группу для constraint_key"""
        for group_name, keys in self.BADGE_GROUPS.items():
            if constraint_key in keys:
                return group_name
        return None

    def _get_status_from_key(self, constraint_key: str) -> str:
        """Определяет статус по названию constraint_key"""
        if 'allowed' in constraint_key or 'required' in constraint_key:
            return 'allowed' if 'allowed' in constraint_key else 'required'
        elif 'excluded' in constraint_key or 'excludes' in constraint_key:
            return 'excluded'
        elif 'preferred' in constraint_key or 'prefers' in constraint_key:
            return 'preferred'
        elif 'avoid' in constraint_key:
            return 'avoided'
        return ''

    def _update_badge_for_tag(self, tag: str, current_constraint_key: str):
        """Обновляет бейдж для конкретного тега"""
        group = self._get_badge_group(current_constraint_key)
        if not group:
            return
        
        current_status = None
        current_priority = 0
        for constraint_key in self.BADGE_GROUPS.get(group, []):
            if constraint_key not in self._current_checkboxes:
                continue
            checkboxes_dict = self._current_checkboxes[constraint_key]
            if tag in checkboxes_dict:
                var = checkboxes_dict[tag]
                if var.get():
                    status = self._get_status_from_key(constraint_key)
                    priority = self.BADGE_PRIORITY.get(status, 0)
                    if priority > current_priority:
                        current_status = status
                        current_priority = priority
        
        for constraint_key in self.BADGE_GROUPS.get(group, []):
            if constraint_key not in self._badge_widgets:
                continue
            badge_dict = self._badge_widgets[constraint_key]
            if tag not in badge_dict:
                continue
            badge = badge_dict[tag]
            this_status = self._get_status_from_key(constraint_key)
            
            if current_status and current_status != this_status:
                text = f"[{current_status.upper()}]"
                color = self.BADGE_COLORS.get(current_status, "gray")
                badge.configure(text=text, text_color=color)
            else:
                badge.configure(text="")

    def _update_badges_for_group(self, group: str):
        """Обновляет все бейджи в группе"""
        if group not in self.BADGE_GROUPS:
            return
        
        all_tags = set()
        for constraint_key in self.BADGE_GROUPS[group]:
            if constraint_key in self._current_checkboxes:
                all_tags.update(self._current_checkboxes[constraint_key].keys())
        
        for tag in all_tags:
            for constraint_key in self.BADGE_GROUPS[group]:
                if constraint_key in self._current_checkboxes:
                    self._update_badge_for_tag(tag, constraint_key)
                    break

    def _render_location_editor(self, parent, data: dict):
        """Рендерит редактор для локации"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        self._render_section_header(parent, "OUTFIT (Одежда)", "👗")
        all_outfit_styles = self._load_all_tags_from_category("02_clothing")
        self._render_checklist_section(parent, "✅ Allowed Outfit Styles (Hard Whitelist)",
            all_outfit_styles, hard.get('allowed_outfit_categories', []),
            'allowed_outfit_categories', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Outfit Styles (Hard Ban)",
            all_outfit_styles, hard.get('excludes_outfit_categories', []),
            'excludes_outfit_categories', bg_color="gray25")
        self._render_checklist_section(parent, "⭐ Preferred Outfit Styles (Soft Priority)",
            all_outfit_styles, soft.get('preferred_outfit_categories', []),
            'preferred_outfit_categories', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Outfit Styles (Soft Ban)",
            all_outfit_styles, soft.get('avoid_outfit_categories', []),
            'avoid_outfit_categories', bg_color="gray25")
        
        self._render_section_header(parent, "ACTIONS (Действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent, "✅ Allowed Actions (Hard Whitelist)",
            all_actions, hard.get('allowed_actions', []),
            'allowed_actions', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Actions (Hard Ban)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="gray25")
        self._render_checklist_section(parent, "🎬 Prefers Actions (Soft Priority)",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Actions (Soft Ban)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="gray25")
        
        self._render_section_header(parent, "PROPS (Реквизит)", "📦")
        all_props = self._load_all_tags_from_category("09_props")
        self._render_checklist_section(parent, "📦 Required Props (100% попадание)",
            all_props, hard.get('required_props', []),
            'required_props', bg_color="gray25")
        self._render_checklist_section(parent, "🎲 Required Props Pool (случайный выбор)",
            all_props, hard.get('required_props_pool', []),
            'required_props_pool', bg_color="gray25")
        
        count_frame = ctk.CTkFrame(parent, fg_color="gray25")
        count_frame.pack(fill="x", padx=5, pady=8)
        count_header = ctk.CTkFrame(count_frame, fg_color="transparent")
        count_header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(count_header, text="🔢 Required Props Count (сколько выбрать из пула)",
            font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        count_entry = ctk.CTkEntry(count_header, width=100)
        count_entry.pack(side="left", padx=(10, 0))
        current_count = hard.get('required_props_count', 0)
        count_entry.insert(0, str(current_count))
        
        if not hasattr(self, '_props_count_entries'):
            self._props_count_entries = {}
        self._props_count_entries['required_props_count'] = count_entry
        
        self._render_checklist_section(parent, "🧸 Prefers Props (высокий приоритет)",
            all_props, soft.get('prefers_props', []),
            'prefers_props', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Props (жёсткий бан)",
            all_props, hard.get('excludes_props', []),
            'excludes_props', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Props (мягкий бан - 30% шанс)",
            all_props, soft.get('avoid_props', []),
            'avoid_props', bg_color="gray25")
        
        self._render_section_header(parent, "LIGHTING & WEATHER (Освещение и Погода)", "🌤️")
        all_lighting = self._load_all_tags_from_category("07_lighting")
        self._render_checklist_section(parent, "🚫 Excluded Lighting Sources (жёсткий бан)",
            all_lighting, hard.get('excludes_lighting_sources', []),
            'excludes_lighting_sources', bg_color="gray25")
        self._render_checklist_section(parent, "💡 Prefers Lighting (высокий приоритет)",
            all_lighting, soft.get('prefers_lighting_sources', []),
            'prefers_lighting_sources', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Lighting Sources (мягкий бан)",
            all_lighting, soft.get('avoid_lighting_sources', []),
            'avoid_lighting_sources', bg_color="gray25")
        
        all_weather = self._load_all_tags_from_category("10_weather")
        self._render_checklist_section(parent, "🚫 Excluded Weather (жёсткий бан)",
            all_weather, hard.get('excludes_weather', []),
            'excludes_weather', bg_color="gray25")
        self._render_checklist_section(parent, "🌦️ Prefers Weather (высокий приоритет)",
            all_weather, soft.get('prefers_weather', []),
            'prefers_weather', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Weather (мягкий бан)",
            all_weather, soft.get('avoid_weather', []),
            'avoid_weather', bg_color="gray25")

    def _render_action_editor(self, parent, data: dict):
        """Рендерит редактор для действия"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        self._render_section_header(parent, "LOCATIONS (Локации)", "📍")
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(parent, "✅ Allowed Locations (Hard Whitelist)",
            all_locations, hard.get('allowed_locations', []),
            'allowed_locations', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Locations (Hard Ban)",
            all_locations, hard.get('excluded_locations', []),
            'excluded_locations', bg_color="gray25")
        self._render_checklist_section(parent, "📍 Prefers Locations (Soft Priority)",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Locations (Soft Ban)",
            all_locations, soft.get('avoid_locations', []),
            'avoid_locations', bg_color="gray25")
        
        self._render_section_header(parent, "POSES & EXPRESSIONS (Позы и Эмоции)", "🎭")
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent, "🎭 Prefers Poses",
            all_poses, soft.get('prefers_poses', []),
            'prefers_poses', bg_color="gray25")
        all_expressions = self._load_all_tags_from_category("05_expression")
        self._render_checklist_section(parent, "😊 Prefers Expressions",
            all_expressions, soft.get('prefers_expressions', []),
            'prefers_expressions', bg_color="gray25")
        
        self._render_section_header(parent, "PROPS (Реквизит)", "📦")
        all_props = self._load_all_tags_from_category("09_props")
        self._render_checklist_section(parent, "📦 Required Props (100% попадание)",
            all_props, hard.get('required_props', []),
            'required_props', bg_color="gray25")
        self._render_checklist_section(parent, "🎲 Required Props Pool (случайный выбор)",
            all_props, hard.get('required_props_pool', []),
            'required_props_pool', bg_color="gray25")
        
        count_frame = ctk.CTkFrame(parent, fg_color="gray25")
        count_frame.pack(fill="x", padx=5, pady=8)
        count_header = ctk.CTkFrame(count_frame, fg_color="transparent")
        count_header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(count_header, text="🔢 Required Props Count (сколько выбрать из пула)",
            font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        count_entry = ctk.CTkEntry(count_header, width=100)
        count_entry.pack(side="left", padx=(10, 0))
        current_count = hard.get('required_props_count', 0)
        count_entry.insert(0, str(current_count))
        
        if not hasattr(self, '_props_count_entries'):
            self._props_count_entries = {}
        self._props_count_entries['required_props_count'] = count_entry
        
        self._render_checklist_section(parent, "🧸 Prefers Props (высокий приоритет)",
            all_props, soft.get('prefers_props', []),
            'prefers_props', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Props (жёсткий бан)",
            all_props, hard.get('excludes_props', []),
            'excludes_props', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Props (мягкий бан - 30% шанс)",
            all_props, soft.get('avoid_props', []),
            'avoid_props', bg_color="gray25")
        
        self._render_section_header(parent, "ACTIONS (Взаимоисключающие действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent, "🚫 Excludes Actions (жёсткий бан)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Actions (мягкий бан)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="gray25")

    def _render_weather_editor(self, parent, data: dict):
        """Рендерит редактор для погоды"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        self._render_section_header(parent, "LOCATIONS (Локации)", "📍")
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(parent, "✅ Allowed Locations (Hard Whitelist)",
            all_locations, hard.get('allowed_locations', []),
            'allowed_locations', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Locations (Hard Ban)",
            all_locations, hard.get('excluded_locations', []),
            'excluded_locations', bg_color="gray25")
        self._render_checklist_section(parent, "📍 Prefers Locations (Soft Priority)",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Locations (Soft Ban)",
            all_locations, soft.get('avoid_locations', []),
            'avoid_locations', bg_color="gray25")
        
        self._render_section_header(parent, "ACTIONS (Действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent, "✅ Allowed Actions (Hard Whitelist)",
            all_actions, hard.get('allowed_actions', []),
            'allowed_actions', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Actions (Hard Ban)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="gray25")
        self._render_checklist_section(parent, "🎬 Prefers Actions (Soft Priority)",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Actions (Soft Ban)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="gray25")
        
        self._render_section_header(parent, "LIGHTING (Освещение)", "💡")
        all_lighting = self._load_all_tags_from_category("07_lighting")
        self._render_checklist_section(parent, "🚫 Excluded Lighting Sources (жёсткий бан)",
            all_lighting, hard.get('excludes_lighting_sources', []),
            'excludes_lighting_sources', bg_color="gray25")
        self._render_checklist_section(parent, "💡 Prefers Lighting (высокий приоритет)",
            all_lighting, soft.get('prefers_lighting_sources', []),
            'prefers_lighting_sources', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Lighting Sources (мягкий бан)",
            all_lighting, soft.get('avoid_lighting_sources', []),
            'avoid_lighting_sources', bg_color="gray25")
        
        self._render_section_header(parent, "WEATHER (Собственные ограничения)", "🌦️")
        all_weather = self._load_all_tags_from_category("10_weather")
        self._render_checklist_section(parent, "🚫 Excludes Weather (жёсткий бан)",
            all_weather, hard.get('excludes_weather', []),
            'excludes_weather', bg_color="gray25")
        self._render_checklist_section(parent, "🌦️ Prefers Weather (высокий приоритет)",
            all_weather, soft.get('prefers_weather', []),
            'prefers_weather', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Weather (мягкий бан)",
            all_weather, soft.get('avoid_weather', []),
            'avoid_weather', bg_color="gray25")

    def _render_camera_editor(self, parent, data: dict):
        """Рендерит редактор для камеры"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        
        self._render_section_header(parent, "LOCATIONS (Локации)", "📍")
        all_locations = self._load_all_tags_from_category("08_location")
        self._render_checklist_section(parent, "✅ Allowed Locations (Hard Whitelist)",
            all_locations, hard.get('allowed_locations', []),
            'allowed_locations', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Locations (Hard Ban)",
            all_locations, hard.get('excluded_locations', []),
            'excluded_locations', bg_color="gray25")
        self._render_checklist_section(parent, "📍 Prefers Locations (Soft Priority)",
            all_locations, soft.get('prefers_locations', []),
            'prefers_locations', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Locations (Soft Ban)",
            all_locations, soft.get('avoid_locations', []),
            'avoid_locations', bg_color="gray25")
        
        self._render_section_header(parent, "ACTIONS (Действия)", "🎬")
        all_actions = self._load_all_tags_from_category("04_action")
        if not all_actions:
            all_actions = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent, "✅ Allowed Actions (Hard Whitelist)",
            all_actions, hard.get('allowed_actions', []),
            'allowed_actions', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Actions (Hard Ban)",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions', bg_color="gray25")
        self._render_checklist_section(parent, "🎬 Prefers Actions (Soft Priority)",
            all_actions, soft.get('prefers_actions', []),
            'prefers_actions', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Actions (Soft Ban)",
            all_actions, soft.get('avoid_actions', []),
            'avoid_actions', bg_color="gray25")
        
        self._render_section_header(parent, "POSES (Позы)", "🎭")
        all_poses = self._load_all_tags_from_category("03_pose")
        self._render_checklist_section(parent, "✅ Allowed Poses (Hard Whitelist)",
            all_poses, hard.get('allowed_poses', []),
            'allowed_poses', bg_color="gray25")
        self._render_checklist_section(parent, "🚫 Excluded Poses (Hard Ban)",
            all_poses, hard.get('excludes_poses', []),
            'excludes_poses', bg_color="gray25")
        self._render_checklist_section(parent, "🎭 Prefers Poses (Soft Priority)",
            all_poses, soft.get('prefers_poses', []),
            'prefers_poses', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Poses (Soft Ban)",
            all_poses, soft.get('avoid_poses', []),
            'avoid_poses', bg_color="gray25")
        
        self._render_section_header(parent, "CAMERA (Собственные ограничения)", "📸")
        all_camera = self._load_all_tags_from_category("06_camera")
        self._render_checklist_section(parent, "🚫 Excludes Camera (жёсткий бан)",
            all_camera, hard.get('excludes_camera', []),
            'excludes_camera', bg_color="gray25")
        self._render_checklist_section(parent, "📸 Prefers Camera (высокий приоритет)",
            all_camera, soft.get('prefers_camera', []),
            'prefers_camera', bg_color="gray25")
        self._render_checklist_section(parent, "⚠️ Avoid Camera (мягкий бан)",
            all_camera, soft.get('avoid_camera', []),
            'avoid_camera', bg_color="gray25")

    def _render_location_type_editor(self, parent, data: dict):
        """Рендерит редактор для типа локации"""
        soft = data.get('soft_constraints', {})
        hard = data.get('hard_constraints', {})
        all_actions = sorted(self.scene_rules_data.get('actions', {}).keys())
        self._render_checklist_section(parent, "🚫 Excludes Actions",
            all_actions, hard.get('excludes_actions', []),
            'excludes_actions')
        self._render_checklist_section(parent, "🎬 Prefers Actions",
            all_actions, soft.get('prefers_actions', []),
            'actions')

    def _render_checklist_section(self, parent, title: str, all_items,
                                  selected_items: list, constraint_key: str,
                                  bg_color="gray20"):
        """Рендерит сворачиваемую секцию с чекбоксами"""
        section = ctk.CTkFrame(parent, fg_color=bg_color)
        section.pack(fill="x", padx=5, pady=8)
        
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        if not hasattr(self, '_current_checkboxes'):
            self._current_checkboxes = {}
        
        if isinstance(all_items, dict):
            total_count = 0
            selected_count = 0
            for main_cat, subcats in all_items.items():
                if isinstance(subcats, dict):
                    for subcat_name, tags in subcats.items():
                        total_count += len(tags)
                        selected_count += len([s for s in selected_items if s in tags])
                else:
                    total_count += len(subcats)
                    selected_count += len([s for s in selected_items if s in subcats])
        else:
            total_count = len(all_items) if all_items else 0
            selected_count = len([s for s in selected_items if s in (all_items or [])])
        
        toggle_btn = ctk.CTkButton(header, text=f"▶ {title} ({selected_count}/{total_count})",
            width=400, height=28,
            fg_color="gray30", hover_color="gray40",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        toggle_btn.pack(side="left")
        
        content_frame = ctk.CTkFrame(section, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=(0, 10))
        content_frame.pack_forget()
        
        checkbox_scroll = ctk.CTkScrollableFrame(content_frame, height=300)
        checkbox_scroll.pack(fill="both", expand=True)
        
        checkboxes: dict[str, ctk.BooleanVar] = {}
        tag_widgets: dict[str, ctk.CTkCheckBox] = {}
        
        if isinstance(all_items, dict):
            for main_cat_name, subcats in sorted(all_items.items()):
                if not isinstance(subcats, dict):
                    continue
                for subcat_name, tags in sorted(subcats.items()):
                    subcat_label = ctk.CTkLabel(checkbox_scroll,
                        text=f"📁 {subcat_name.replace('_', ' ').title()}",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        anchor="w")
                    subcat_label.pack(fill="x", padx=10, pady=(10, 2))
                    
                    for tag in sorted(tags):
                        var = ctk.BooleanVar(value=(tag in selected_items))
                        cb = ctk.CTkCheckBox(checkbox_scroll, text=tag.replace('_', ' '),
                            variable=var,
                            command=lambda i=tag, v=var:
                                self._on_checkbox_toggled(i, v, constraint_key, None, all_items))
                        cb.pack(anchor="w", padx=20, pady=1)
                        checkboxes[tag] = var
                        tag_widgets[tag] = cb
        else:
            if all_items:
                for item in sorted(all_items):
                    var = ctk.BooleanVar(value=(item in selected_items))
                    cb = ctk.CTkCheckBox(checkbox_scroll, text=item.replace('_', ' '),
                        variable=var,
                        command=lambda i=item, v=var:
                            self._on_checkbox_toggled(i, v, constraint_key, None, all_items))
                    cb.pack(anchor="w", padx=10, pady=1)
                    checkboxes[item] = var
                    tag_widgets[item] = cb
        
        def toggle_visibility():
            if content_frame.winfo_ismapped():
                self._hide_container(content_frame)
                toggle_btn.configure(text=f"▶ {title} ({selected_count}/{total_count})")
            else:
                content_frame.pack(fill="x", padx=10, pady=(0, 10))
                toggle_btn.configure(text=f"▼ {title} ({selected_count}/{total_count})")
        
        toggle_btn.configure(command=toggle_visibility)
        self._current_checkboxes[constraint_key] = checkboxes

    def _on_checkbox_toggled(self, item: str, var, constraint_key: str, count_label, all_items):
        """Обработчик чекбокса"""
        if isinstance(all_items, dict):
            all_tags = []
            for tags in all_items.values():
                all_tags.extend(tags)
            selected_count = sum(
                1 for tag in all_tags
                if self._current_checkboxes[constraint_key].get(tag, ctk.BooleanVar(value=False)).get()
            )
            total_count = len(all_tags)
        else:
            selected_count = sum(1 for v in self._current_checkboxes[constraint_key].values() if v.get())
            total_count = len(all_items) if all_items else 0
        
        count_label.configure(text=f"({selected_count}/{total_count})")
        
        self._log(f"{'☑' if var.get() else '☐'} {constraint_key}: {item}\n")
        
        if self.current_rule_file:
            self._save_current_rule_silently()

    def _load_all_tags_from_category(self, category: str) -> dict:
        """Загружает все теги из категории prompt-library"""
        if not hasattr(self, '_all_tags_category_cache'):
            self._all_tags_category_cache = {}
        
        if category in self._all_tags_category_cache:
            return self._all_tags_category_cache[category]
        
        result = {}
        cat_dir = self.project_root / "prompt-library" / category
        if not cat_dir.exists():
            self._all_tags_category_cache[category] = result
            return result
        
        for txt_file in sorted(cat_dir.rglob("*.txt")):
            rel_path = txt_file.relative_to(cat_dir)
            if len(rel_path.parts) >= 2:
                main_cat = rel_path.parts[0]
                sub_cat = txt_file.stem
            else:
                main_cat = "general"
                sub_cat = txt_file.stem
            
            tags = self._load_tags_from_file(txt_file)
            if tags:
                if main_cat not in result:
                    result[main_cat] = {}
                result[main_cat][sub_cat] = tags
        
        self._all_tags_category_cache[category] = result
        return result

    def _invalidate_category_cache(self, category: str | None = None):
        """Инвалидирует кэш категорий"""
        if not hasattr(self, '_all_tags_category_cache'):
            return
        
        if category is None:
            self._all_tags_category_cache.clear()
            self._log("🔄 Кэш всех категорий тегов очищен\n")
        else:
            for key in list(self._all_tags_category_cache.keys()):
                if category in key or key in category:
                    del self._all_tags_category_cache[key]
            self._log(f"🔄 Кэш категории '{category}' очищен\n")

    def _reload_scene_rules(self):
        """Перезагружает все TOML-файлы"""
        self._load_scene_rules()
        self._build_scene_rules_list()
        self._log("🔄 Scene rules перезагружены\n")

    def _validate_scene_rules_integrity(self):
        """Проверяет целостность scene-rules"""
        self._log("\n🔍 Проверка целостности scene-rules...\n")
        issues_format = 0
        issues_missing = 0
        files_checked = 0
        
        available_tags = {
            'actions': set(), 'locations': set(), 'weather': set(),
            'camera': set(), 'props': set(), 'lighting': set(),
            'poses': set(), 'expressions': set(),
        }
        normalized_tags = {
            'actions': {}, 'locations': {}, 'weather': {},
            'camera': {}, 'props': {}, 'lighting': {},
            'poses': {}, 'expressions': {},
        }
        tag_mapping = {
            '04_action': 'actions', '08_location': 'locations',
            '10_weather': 'weather', '06_camera': 'camera',
            '09_props': 'props', '07_lighting': 'lighting',
            '03_pose': 'poses', '05_expression': 'expressions',
        }
        
        library_path = self.project_root / "prompt-library"
        for folder_name, tag_type in tag_mapping.items():
            folder = library_path / folder_name
            if folder.exists():
                for txt_file in folder.rglob("*.txt"):
                    tags = self._load_tags_from_file(txt_file)
                    available_tags[tag_type].update(tags)
                    for tag in tags:
                        norm = tag.strip().lower().replace('_', ' ')
                        normalized_tags[tag_type][norm] = tag
        
        field_to_type = {
            'prefers_actions': 'actions', 'prefers_locations': 'locations',
            'prefers_weather': 'weather', 'prefers_camera': 'camera',
            'prefers_props': 'props', 'prefers_lighting': 'lighting',
            'prefers_poses': 'poses', 'prefers_expressions': 'expressions',
            'excludes_actions': 'actions', 'excludes_locations': 'locations',
            'excludes_weather': 'weather', 'excludes_camera': 'camera',
            'excludes_props': 'props', 'excludes_lighting': 'lighting',
            'excludes_poses': 'poses', 'excludes_expressions': 'expressions',
            'requires_props': 'props', 'requires_actions': 'actions',
            'requires_locations': 'locations',
        }
        
        rules_dir = self.project_root / "scene-rules"
        if not rules_dir.exists():
            messagebox.showwarning("Warning", "Папка scene-rules не найдена")
            return
        
        for category_dir in sorted(rules_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category_name = category_dir.name
            for toml_file in sorted(category_dir.glob("*.toml")):
                files_checked += 1
                file_issues = []
                try:
                    import tomli
                    with open(toml_file, 'rb') as f:
                        data = tomli.load(f)
                except Exception as e:
                    file_issues.append(f"❌ Ошибка чтения TOML: {e}")
                    issues_missing += 1
                    self._log(f"\n❌ {category_name}/{toml_file.name}: Ошибка чтения: {e}\n")
                    continue
                
                all_tag_fields = {}
                for section_name in ['soft_constraints', 'hard_constraints']:
                    section = data.get(section_name, {})
                    for field, tags in section.items():
                        if field in field_to_type and isinstance(tags, list):
                            full_key = f"{section_name}.{field}"
                            all_tag_fields[full_key] = (tags, field_to_type[field])
                
                for field_key, (tags, tag_type) in all_tag_fields.items():
                    for tag in tags:
                        if tag in available_tags[tag_type]:
                            continue
                        norm_tag = tag.strip().lower().replace('_', ' ')
                        if norm_tag in normalized_tags[tag_type]:
                            real_tag = normalized_tags[tag_type][norm_tag]
                            file_issues.append(
                                f"🔄 {field_key}: '{tag}' → найдено как '{real_tag}' (проблема с форматом)"
                            )
                            issues_format += 1
                        else:
                            file_issues.append(
                                f"❌ {field_key}: тег '{tag}' НЕ СУЩЕСТВУЕТ в библиотеке"
                            )
                            issues_missing += 1
                
                if file_issues:
                    self._log(f"\n⚠️ {category_name}/{toml_file.name}:\n")
                    for issue in file_issues:
                        self._log(f"   {issue}\n")
        
        self._log(f"\n{'='*60}\n")
        total_issues = issues_format + issues_missing
        if total_issues == 0:
            self._log(f"✅ Проверка завершена: {files_checked} файлов, проблем не найдено\n")
            messagebox.showinfo("Validation Complete",
                f"✅ Все {files_checked} файлов прошли проверку!\nПроблем не найдено.")
        else:
            self._log(f"\n📊 ИТОГО:\n")
            self._log(f"   📁 Проверено файлов: {files_checked}\n")
            self._log(f"   🔄 Проблем с форматом: {issues_format}\n")
            self._log(f"   ❌ Отсутствующих тегов: {issues_missing}\n")
            self._log(f"   📌 Всего проблем: {total_issues}\n")
            
            msg = (
                f"📊 Проверка завершена\n"
                f"📁 Файлов проверено: {files_checked}\n"
                f"🔄 Проблем с форматом: {issues_format}\n"
                f"❌ Отсутствующих тегов: {issues_missing}\n"
                f"Смотрите лог для деталей."
            )
            if issues_missing > 0 and issues_format > 0:
                messagebox.showwarning("Validation Complete", msg)
            elif issues_format > 0:
                messagebox.showinfo("Validation Complete",
                    msg + "\n💡 Все теги найдены, но формат различается.\n"
                    "Рекомендуется привести к единому формату.")
            else:
                messagebox.showwarning("Validation Complete", msg)

    def _auto_fix_tag_format(self):
        """Автоматически исправляет формат тегов"""
        self._log("\n🔧 Запуск Auto-fix формата тегов...\n")
        
        available_tags_normalized = {
            'actions': {}, 'locations': {}, 'weather': {},
            'camera': {}, 'props': {}, 'lighting': {},
            'poses': {}, 'expressions': {},
        }
        tag_mapping = {
            '04_action': 'actions', '08_location': 'locations',
            '10_weather': 'weather', '06_camera': 'camera',
            '09_props': 'props', '07_lighting': 'lighting',
            '03_pose': 'poses', '05_expression': 'expressions',
        }
        
        library_path = self.project_root / "prompt-library"
        for folder_name, tag_type in tag_mapping.items():
            folder = library_path / folder_name
            if folder.exists():
                for txt_file in folder.rglob("*.txt"):
                    tags = self._load_tags_from_file(txt_file)
                    for tag in tags:
                        norm = tag.strip().lower().replace('_', ' ')
                        available_tags_normalized[tag_type][norm] = tag
        
        field_to_type = {
            'prefers_actions': 'actions', 'prefers_locations': 'locations',
            'prefers_weather': 'weather', 'prefers_camera': 'camera',
            'prefers_props': 'props', 'prefers_lighting': 'lighting',
            'prefers_poses': 'poses', 'prefers_expressions': 'expressions',
            'excludes_actions': 'actions', 'excludes_locations': 'locations',
            'excludes_weather': 'weather', 'excludes_camera': 'camera',
            'excludes_props': 'props', 'excludes_lighting': 'lighting',
            'excludes_poses': 'poses', 'excludes_expressions': 'expressions',
            'requires_props': 'props', 'requires_actions': 'actions',
            'requires_locations': 'locations',
        }
        
        rules_dir = self.project_root / "scene-rules"
        if not rules_dir.exists():
            messagebox.showwarning("Warning", "Папка scene-rules не найдена")
            return
        
        fixed_count = 0
        files_fixed = 0
        
        for category_dir in sorted(rules_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            for toml_file in sorted(category_dir.glob("*.toml")):
                try:
                    import tomli
                    import tomli_w
                    with open(toml_file, 'rb') as f:
                        data = tomli.load(f)
                    changed = False
                    
                    for section_name in ['soft_constraints', 'hard_constraints']:
                        section = data.get(section_name, {})
                        for field, tags in section.items():
                            if field in field_to_type and isinstance(tags, list):
                                tag_type = field_to_type[field]
                                new_tags = []
                                for tag in tags:
                                    norm_tag = tag.strip().lower().replace('_', ' ')
                                    if norm_tag in available_tags_normalized[tag_type]:
                                        correct_tag = available_tags_normalized[tag_type][norm_tag]
                                        if correct_tag != tag:
                                            fixed_count += 1
                                            changed = True
                                        new_tags.append(correct_tag)
                                    else:
                                        new_tags.append(tag)
                                section[field] = new_tags
                    
                    if changed:
                        with open(toml_file, 'wb') as f:
                            tomli_w.dump(data, f)
                        files_fixed += 1
                        
                        rel_path = toml_file.relative_to(rules_dir)
                        category = rel_path.parts[0]
                        rule_name = toml_file.stem
                        if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                            self.scene_rules_data[category][rule_name]['data'] = data
                except Exception as e:
                    self._log(f"❌ Ошибка обработки {toml_file.name}: {e}\n")
        
        self._log(f"\n✅ Auto-fix завершён!\n")
        self._log(f"📄 Исправлено файлов: {files_fixed}\n")
        self._log(f"🔧 Исправлено тегов: {fixed_count}\n")
        messagebox.showinfo("Auto-fix Complete",
            f"✅ Исправлено {fixed_count} тегов в {files_fixed} файлах!\n"
            f"Запустите Validate заново для проверки.")

    def _save_scene_rules(self):
        """Сохраняет все изменения чекбоксов"""
        if not hasattr(self, '_current_checkboxes') or not self._current_checkboxes:
            messagebox.showinfo("Info", "Нет изменений для сохранения")
            return
        
        try:
            import tomli
            import tomli_w
        except ImportError:
            messagebox.showerror("Error", "Установите tomli и tomli-w:\npip install tomli tomli-w")
            return
        
        if not self.current_rule_file:
            messagebox.showwarning("Warning", "Сначала выберите правило для редактирования")
            return
        
        changes = self._collect_checkbox_changes()
        if not changes:
            messagebox.showinfo("Info", "Нет изменений для сохранения")
            return
        
        saved_count = 0
        errors = []
        
        props_count_value = 0
        if hasattr(self, '_props_count_entries') and 'required_props_count' in self._props_count_entries:
            try:
                props_count_value = int(self._props_count_entries['required_props_count'].get())
            except ValueError:
                props_count_value = 0
        
        for category, rule_name, field, new_values in changes:
            file_path = self.project_root / "scene-rules" / category / f"{rule_name}.toml"
            if not file_path.exists():
                errors.append(f"Файл не найден: {file_path.name}")
                continue
            
            try:
                with open(file_path, 'rb') as f:
                    data = tomli.load(f)
                target_section = 'hard_constraints' if 'excludes' in field or 'required' in field or 'allowed' in field else 'soft_constraints'
                if target_section not in data:
                    data[target_section] = {}
                data[target_section][field] = new_values
                
                if field == 'required_props_pool':
                    data[target_section]['required_props_count'] = props_count_value
                
                with open(file_path, 'wb') as f:
                    tomli_w.dump(data, f)
                
                if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                    self.scene_rules_data[category][rule_name]['data'] = data
                saved_count += 1
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
        
        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... и ещё {len(errors) - 5} ошибок"
            messagebox.showerror("Ошибки сохранения", error_msg)
            self._log(f"⚠️ Сохранено {saved_count} файлов, {len(errors)} ошибок\n")
        else:
            messagebox.showinfo("Success", f"✅ Сохранено {saved_count} файлов!")
            self._log(f"💾 Успешно сохранено {saved_count} TOML-файлов\n")

    def _save_current_rule_silently(self):
        """Тихое сохранение текущего правила"""
        if not self.current_rule_file or not self.current_rule_file.exists():
            return
        if not hasattr(self, '_current_checkboxes') or not self._current_checkboxes:
            return
        
        try:
            import tomli
            import tomli_w
        except ImportError:
            return
        
        try:
            with open(self.current_rule_file, 'rb') as f:
                data = tomli.load(f)
            
            changes = self._collect_checkbox_changes()
            if not changes:
                return
            
            for category, rule_name, field, new_values in changes:
                target_section = 'hard_constraints' if 'excludes' in field or 'required' in field or 'allowed' in field else 'soft_constraints'
                if target_section not in data:
                    data[target_section] = {}
                data[target_section][field] = new_values
                
                if field == 'required_props_pool':
                    props_count_value = 0
                    if hasattr(self, '_props_count_entries') and 'required_props_count' in self._props_count_entries:
                        try:
                            props_count_value = int(self._props_count_entries['required_props_count'].get())
                        except ValueError:
                            props_count_value = 0
                    data[target_section]['required_props_count'] = props_count_value
            
            with open(self.current_rule_file, 'wb') as f:
                tomli_w.dump(data, f)
            
            rel_path = self.current_rule_file.relative_to(self.project_root / "scene-rules")
            parts = rel_path.parts
            if len(parts) >= 2:
                category = parts[0]
                rule_name = parts[1].replace('.toml', '')
                if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                    self.scene_rules_data[category][rule_name]['data'] = data
        except Exception as e:
            self._log(f"⚠️ Автосохранение не удалось: {e}\n")

    def _collect_checkbox_changes(self) -> list:
        """Собирает все изменения из чекбоксов"""
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
        
        for constraint_key, checkboxes in self._current_checkboxes.items():
            selected_values = [tag for tag, var in checkboxes.items() if var.get()]
            changes.append((current_category, current_rule_name, constraint_key, sorted(selected_values)))
        
        return changes

    def _delete_scene_rule(self, category: str, rule_name: str):
        """Удаляет файл правила"""
        rule_path = self.project_root / "scene-rules" / category / f"{rule_name}.toml"
        if not rule_path.exists():
            self._log(f"⚠️ Файл не найден: {rule_path}\n")
            return
        
        if not messagebox.askyesno(
            "Удаление правила",
            f"Вы уверены, что хотите удалить правило?\n"
            f"📄 {category}/{rule_name}.toml\n"
            f"Это действие нельзя отменить!"
        ):
            return
        
        try:
            rule_path.unlink()
            if category in self.scene_rules_data and rule_name in self.scene_rules_data[category]:
                del self.scene_rules_data[category][rule_name]
            
            self._build_scene_rules_list()
            
            if self.scene_rules_editor_frame:
                for w in self.scene_rules_editor_frame.winfo_children():
                    w.destroy()
                placeholder = ctk.CTkLabel(self.scene_rules_editor_frame,
                    text="👈 Выберите правило слева для редактирования",
                    font=ctk.CTkFont(size=14),
                    text_color="gray")
                placeholder.pack(expand=True)
            
            self.current_rule_file = None
            self._log(f"🗑️ Удалено правило: {category}/{rule_name}\n")
            messagebox.showinfo("Success", f"Правило '{rule_name}' удалено!")
        except Exception as e:
            self._log(f"❌ Ошибка удаления: {e}\n")
            messagebox.showerror("Error", f"Не удалось удалить: {e}")

    # ═══════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════
    def _load_tags_from_file(self, file_path) -> list:
        """Загружает теги из конкретного файла"""
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