"""
Скрипт v2: Полная зачистка старых параметров и внедрение расширенных стилей
"""
import os
import re
import glob

# 🌟 РАСШИРЕННЫЙ МАППИНГ: Больше вариативности для каждого места!
style_mapping = {
    "bedroom": ["pajamas", "loungewear", "casual_shirt_skirt", "sportswear"],
    "library": ["casual_shirt_skirt", "sportswear"],
    "school_classroom": ["casual_shirt_skirt", "sportswear"],
    "bathroom": ["bikini", "pajamas", "loungewear"],
    "balcony": ["pajamas", "loungewear", "casual_shirt_skirt", "sportswear"],
    "kitchen": ["pajamas", "loungewear", "casual_shirt_skirt", "sportswear"],
    "beach": ["bikini", "casual_shirt_skirt", "sportswear"],
    "street": ["casual_shirt_skirt", "sportswear", "loungewear"],
    "park": ["casual_shirt_skirt", "sportswear"],
    "cafe": ["casual_shirt_skirt", "sportswear"]
}

toml_dir = os.path.join("..", "scene-rules", "locations")

if not os.path.exists(toml_dir):
    print(f"❌ Ошибка: Папка {toml_dir} не найдена!")
    exit()

print("🚀 Начинаю глобальное обновление .toml файлов...")

for filepath in glob.glob(os.path.join(toml_dir, "*.toml")):
    filename = os.path.basename(filepath).replace(".toml", "")
    if filename not in style_mapping:
        continue
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Жестко удаляем старые allowed_outfit_categories (флаг re.DOTALL позволяет удалять многострочные массивы!)
    content = re.sub(r'allowed_outfit_categories\s*=\s*\[.*?\]\n?', '', content, flags=re.DOTALL)
    
    # 2. Удаляем старые allowed_outfit_styles (если они были добавлены криво)
    content = re.sub(r'allowed_outfit_styles\s*=\s*\[.*?\]\n?', '', content, flags=re.DOTALL)
    
    # 3. Формируем новую строку с расширенными стилями
    styles = style_mapping[filename]
    styles_str = ', '.join([f'"{s}"' for s in styles])
    new_line = f'allowed_outfit_styles = [{styles_str}]\n'
    
    # 4. Аккуратно вставляем в блок [hard_constraints]
    if "[hard_constraints]" in content:
        content = content.replace("[hard_constraints]", f"[hard_constraints]\n# ✅ Разрешенные стили (Character Profile)\n{new_line}", 1)
    else:
        content = f"[hard_constraints]\n# ✅ Разрешенные стили (Character Profile)\n{new_line}\n" + content
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ {filename}.toml обновлен (доступно стилей: {len(styles)})")

print(f"\n🎉 Готово! Файлы очищены от старых путей и наполнены новыми стилями.")
print("Теперь запусти 'python main.py' и наслаждайся результатом!")