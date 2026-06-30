"""
Main entry point for Dataset Composer
"""
from pathlib import Path
from config_loader import ConfigLoader
from prompt_library import PromptLibrary


def main():
    print("🚀 Dataset Composer v0.2 MVP")
    print("=" * 60)
    
    # Определяем корень проекта (на уровень выше папки src)
    project_root = Path("..")
    
    # 1. Инициализируем загрузчик конфигурации
    loader = ConfigLoader(project_root=str(project_root))
    
    # 2. Инициализируем библиотеку промптов
    library = PromptLibrary(library_path=str(project_root / "prompt-library"))
    
    try:
        # --- Загрузка Конфигурации ---
        profile = loader.load_character_profile()
        character_name = loader.get_character_name()
        fixed_traits = loader.get_fixed_traits()
        
        print(f"\n📋 Character Profile:")
        print(f"   Name: {character_name}")
        print(f"   Archetype: {profile['character']['archetype']}")
        print(f"   Fixed traits count: {len(fixed_traits)}")
        
        print(f"\n📜 Loading scene rules...")
        rules = loader.load_scene_rules()
        print(f"   Loaded {len(rules)} rule files")
        
        # --- Загрузка Библиотеки Промптов ---
        print(f"\n📚 Loading prompt library...")
        library.load_library()
        stats = library.get_stats()
        
        print(f"   Indexed {stats['total_files']} categories (.txt files)")
        print(f"   Total tags available: {stats['total_tags']}")
        
        # --- Тестовый запрос к библиотеке ---
        print(f"\n🎲 Testing library retrieval:")
        
        # Попытаемся достать случайную рубашку
        shirt_category = "02_clothing/topwear/shirts.txt"
        random_shirt = library.get_random_tag(shirt_category)
        print(f"   Random shirt: {random_shirt}")
        
        # Попытаемся достать случайную локацию
        location_category = "08_location/indoor.txt"
        random_location = library.get_random_tag(location_category)
        print(f"   Random indoor location: {random_location}")
        
        # Попытаемся достать действие
        action_category = "04_action/daily.txt"
        random_action = library.get_random_tag(action_category)
        print(f"   Random daily action: {random_action}")

        print("\n" + "=" * 60)
        print("✅ System initialized successfully!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()