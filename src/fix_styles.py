"""
Скрипт для автоматического обновления всех .toml файлов
Переводит их со старых 'categories' на новые 'styles' из character-profile.yaml
"""
import os
import re
import glob

# Маппинг локаций к разрешенным стилям Луны
style_mapping = {
    "bedroom": ["pajamas", "loungewear", "casual_shirt_skirt"],
    "library": ["casual_shirt_skirt"],
    "school_classroom": ["casual_shirt_skirt"],
    "bathroom": ["bikini"],
    "balcony": ["loungewear", "casual_shirt_skirt", "sportswear"],
    "kitchen": ["pajamas", "loungewear", "casual_shirt_skirt"],
    "beach": ["bikini", "casual_shirt_skirt"],
    "street": ["casual_shirt_skirt", "sportswear"],
    "park": ["casual_shirt_skirt", "sportswear"],
    "cafe": ["casual_shirt_skirt"]
}

# Путь к папке с правилами (на уровень выше папки src)
toml_dir = os.path.join("..", "scene-rules", "locations")

if not os.path.exists(toml_dir):
    print(f"❌ Ошибка: Папка {toml_dir} не найдена!")
    exit()

print("🚀 Начинаю обновление .toml файлов...")
updated_count = 0

for filepath in glob.glob(os.path.join(toml_dir, "*.toml")):
    filename = os.path.basename(filepath).replace(".toml", "")
    if filename not in style_mapping:
        continue
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Удаляем старый allowed_outfit_categories (вместе со всем массивом)
    content = re.sub(r'allowed_outfit_categories\s*=\s*\[[^\]]*\]\n?', '', content)
    
    # 2. Формируем новую строку со стилями
    styles = style_mapping[filename]
    styles_str = ', '.join([f'"{s}"' for s in styles])
    new_line = f'allowed_outfit_styles = [{styles_str}]\n'
    
    # 3. Вставляем новую строку в блок [hard_constraints]
    if "[hard_constraints]" in content:
        if "allowed_outfit_styles" not in content:
            content = content.replace("[hard_constraints]", f"[hard_constraints]\n# ✅ Разрешенные стили одежды для Луны\n{new_line}", 1)
    else:
        content = f"[hard_constraints]\n# ✅ Разрешенные стили одежды для Луны\n{new_line}\n" + content
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ {filename}.toml обновлен")
    updated_count += 1

print(f"\n🎉 Готово! Обновлено файлов: {updated_count}")
print("Теперь зайди в GitHub Desktop и нажми Commit -> Push!")