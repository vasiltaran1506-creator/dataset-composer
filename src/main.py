"""
Main entry point for Dataset Composer
"""
from config_loader import ConfigLoader


def main():
    print("🚀 Dataset Composer v0.1 MVP")
    print("=" * 60)
    
    # Инициализируем загрузчик (указываем "..", так как мы запускаем из папки src, 
    # а файлы лежат в корне репозитория)
    loader = ConfigLoader(project_root="..")
    
    try:
        # Загружаем профиль персонажа
        profile = loader.load_character_profile()
        character_name = loader.get_character_name()
        fixed_traits = loader.get_fixed_traits()
        
        print(f"\n📋 Character Profile:")
        print(f"   Name: {character_name}")
        print(f"   Age: {profile['character']['age']}")
        print(f"   Archetype: {profile['character']['archetype']}")
        print(f"   Fixed traits count: {len(fixed_traits)}")
        
        # Загружаем правила сцен
        print(f"\n📜 Loading scene rules...")
        rules = loader.load_scene_rules()
        print(f"   Loaded {len(rules)} rule files")
        
        print("\n" + "=" * 60)
        print("✅ Configuration loaded successfully!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please make sure character-profile.yaml exists in project root")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()