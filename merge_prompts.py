#!/usr/bin/env python3
"""
Объединяет все .txt файлы из папки с генерациями в один файл.
Формат:
    [имя_файла]
    содержимое_файла
    
    [имя_файла_2]
    содержимое_файла_2
    ...
"""

from pathlib import Path

# Папка с генерациями
INPUT_DIR = Path(r"D:\VASILY\MY GENERATION\Test Generations")
OUTPUT_FILE = INPUT_DIR / "merged_prompts.txt"

def merge_prompts():
    """Объединяет все .txt файлы в один"""
    if not INPUT_DIR.exists():
        print(f"❌ Папка не найдена: {INPUT_DIR}")
        return
    
    # Собираем все .txt файлы (исключая наш собственный merged_prompts.txt)
    txt_files = sorted([
        f for f in INPUT_DIR.glob("*.txt")
        if f.name != OUTPUT_FILE.name
    ])
    
    if not txt_files:
        print(f"⚠️ В папке {INPUT_DIR} не найдено .txt файлов")
        return
    
    print(f"📂 Найдено файлов: {len(txt_files)}")
    print(f"📝 Объединение в: {OUTPUT_FILE}")
    print("-" * 60)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        for i, txt_file in enumerate(txt_files, start=1):
            try:
                content = txt_file.read_text(encoding='utf-8').strip()
                
                # Формат: [имя файла]
                out.write(f"[{txt_file.name}]\n")
                # Содержимое файла
                out.write(f"{content}\n")
                
                # Разделитель между файлами (кроме последнего)
                if i < len(txt_files):
                    out.write("\n" + "=" * 60 + "\n\n")
                
                # Прогресс в консоль (каждые 50 файлов)
                if i % 50 == 0:
                    print(f"   ✅ Обработано: {i}/{len(txt_files)}")
            
            except Exception as e:
                print(f"   ⚠️ Ошибка чтения {txt_file.name}: {e}")
                out.write(f"[{txt_file.name}]\n")
                out.write(f"[ОШИБКА ЧТЕНИЯ: {e}]\n")
                if i < len(txt_files):
                    out.write("\n" + "=" * 60 + "\n\n")
    
    # Финальная статистика
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print("-" * 60)
    print(f"✅ Готово! Файл создан: {OUTPUT_FILE}")
    print(f"📊 Размер: {file_size_mb:.2f} МБ")
    print(f"📄 Всего файлов объединено: {len(txt_files)}")

if __name__ == "__main__":
    merge_prompts()