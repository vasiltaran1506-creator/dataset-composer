"""
Main entry point for Dataset Composer
"""
from pathlib import Path
from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder


def main():
    print("🚀 Dataset Composer v0.3 MVP - Scene Generation")
    print("=" * 60)
    
    project_root = Path("..")
    
    loader = ConfigLoader(project_root=str(project_root))
    library = PromptLibrary(library_path=str(project_root / "prompt-library"))
    
    try:
        # 1. Загрузка данных
        profile = loader.load_character_profile()
        rules = loader.load_scene_rules()
        library.load_library()
        
        character_name = loader.get_character_name()
        fixed_traits = loader.get_fixed_traits()
        
        print(f"\n✅ System initialized for: {character_name}")
        print(f"   Rules loaded: {len(rules)}")
        print(f"   Tags available: {library.get_stats()['total_tags']}")
        
        # 2. Инициализация Сборщика Сцен
        builder = SceneBuilder(
            library=library, 
            scene_rules=rules, 
            character_profile=profile
        )
        
        # 3. Генерация тестовых сцен
        print(f"\n🎬 Generating test scenes...")
        print("-" * 60)
        
        test_locations = ["bedroom", "library", "balcony"]
        
        for loc in test_locations:
            print(f"\n📍 Location: {loc.capitalize()}")
            
            # Строим объект Scene
            scene = builder.build_scene(loc)
            
            # Экспортируем Scene в Prompt
            prompt = scene.to_prompt(fixed_traits)
            
            print(f"📝 Prompt:\n   {prompt}")
            print("-" * 60)

        print("\n🎉 Generation complete!")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()