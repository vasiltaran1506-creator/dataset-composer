import os
import re

# Путь к файлу (адаптируй под свою структуру, если нужно)
FILE_PATH = "src/ui/main_window.py" 
if not os.path.exists(FILE_PATH):
    FILE_PATH = "main_window.py"

if not os.path.exists(FILE_PATH):
    print(f"❌ Файл {FILE_PATH} не найден!")
    exit()

with open(FILE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"📖 Читаем файл: {len(lines)} строк.")

# 1. FIX: Убираем бесконечную рекурсию в _hide_container
for i in range(len(lines)):
    if "self._hide_container(container)" in lines[i] and "def _hide_container" not in lines[i-1]:
        lines[i] = lines[i].replace("self._hide_container(container)", "container.pack_forget()")
        lines.insert(i+1, "            # FIX: Убрана бесконечная рекурсия, теперь правильно вызывается pack_forget\n")
        break

# 2. FIX: Заменяем все "голые" pack_forget() на безопасный _hide_container()
replacements = [
    ("cat_container.pack_forget()", "self._hide_container(cat_container)"),
    ("content_frame.pack_forget()", "self._hide_container(content_frame)"),
    ("tags_container.pack_forget()", "self._hide_container(tags_container)"),
    ("cont.pack_forget()", "self._hide_container(cont)"),
    ("sub_container.pack_forget()", "self._hide_container(sub_container)"),
    ("tags_frame.pack_forget()", "self._hide_container(tags_frame)"),
    ("subcats_frame.pack_forget()", "self._hide_container(subcats_frame)"),
    ("section['frame'].pack_forget()", "self._hide_container(section['frame'])")
]

for i in range(len(lines)):
    for old, new in replacements:
        if old in lines[i]:
            lines[i] = lines[i].replace(old, new)

# 3. FIX: Приводим нейминг к единому виду self._tabs_created
for i in range(len(lines)):
    if "self.tabs_created: dict[str, bool] = {}" in lines[i]:
        lines[i] = "        # FIX: Удалено дублирующее объявление, используем только self._tabs_created\n"
    if "self.tabs_created.get(\"Generate\", False)" in lines[i]:
        lines[i] = lines[i].replace("self.tabs_created", "self._tabs_created")
    if "self.tabs_created[\"Generate\"] = True" in lines[i]:
        lines[i] = lines[i].replace("self.tabs_created", "self._tabs_created")

# 4. FIX: Scene Rules UI (Жесткая ширина и перенос длинных имен)
for i in range(len(lines)):
    if "self.scene_rules_list_frame = ctk.CTkScrollableFrame(left_wrapper)" in lines[i]:
        lines[i] = lines[i].replace("ctk.CTkScrollableFrame(left_wrapper)", "ctk.CTkScrollableFrame(left_wrapper, width=260)")
        lines.insert(i+1, "        # FIX: Жестко задаем ширину, чтобы ScrollableFrame не расширялся от длинных имен\n")
    
    if "rule_btn = ctk.CTkButton(" in lines[i]:
        for j in range(i, min(i+15, len(lines))):
            if ")" in lines[j] and "pack(" not in lines[j]:
                lines[j] = lines[j].replace(")", "                    wraplength=240  # FIX: Перенос длинных имен\n)")
                break

    if "text=f\"➤ {category_name.replace('_', ' ').title()} ({len(rules)})\"" in lines[i]:
        for j in range(i, min(i+10, len(lines))):
            if ").pack(side=\"left\", fill=\"x\", expand=True)" in lines[j]:
                lines[j] = lines[j].replace(").pack(side=\"left\", fill=\"x\", expand=True)", ", wraplength=200  # FIX: Перенос текста\n            ).pack(side=\"left\", fill=\"x\", expand=True)")
                break

# Сохраняем результат
with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"✅ Файл успешно обновлен! Применено {len(replacements)} патчей.")