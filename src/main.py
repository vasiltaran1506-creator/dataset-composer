"""
Main entry point for Dataset Composer
"""
import sys
import random
from pathlib import Path
from config_loader import ConfigLoader
from prompt_library import PromptLibrary
from scene_builder import SceneBuilder
from exporter import Exporter


def main():
    print("🚀 Dataset Composer v0.4 - Export Mode")
    print("=" * 60)
    
    # Проверяем аргументы командной строки
    # python main.py              → test mode (5 сцен)
    # python main.py generate     → generate mode (1000 сцен)
    # python main.py generate 500 → generate mode (500 сцен)
    mode = "test"
    num_scenes = 5
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "generate":
            mode = "generate"
            if len(sys.argv) > 2:
                try:
                    num_scenes = int(sys.argv[2])
                except ValueError:
                    print("❌ Error: Number of scenes must be an integer")
                    sys.exit(1)
    
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
        
        # 2. Инициализация компонентов
        builder = SceneBuilder(
            library=library, 
            scene_rules=rules, 
            character_profile=profile
        )
        
        if mode == "test":
            # TEST MODE: Генерируем 5 случайных сцен для проверки
            print(f"\n🎬 Test Mode: Generating 5 random scenes...")
            print("-" * 60)
            
            all_locations = [
                key.split('.')[-1] 
                for key in rules.keys() 
                if key.startswith('locations.')
            ]
            
            print(f"Available locations: {len(all_locations)}")
            print(f"   {', '.join(sorted(all_locations))}\n")
            
            test_locations = random.sample(all_locations, min(5, len(all_locations)))
            
            print(f"Testing {len(test_locations)} random locations:\n")
            
            for loc in test_locations:
                print(f"\n📍 Location: {loc.capitalize()}")
                scene = builder.build_scene(loc)
                prompt = scene.to_prompt(fixed_traits)
                print(f"📝 Prompt:\n   {prompt}")
                print("-" * 60)

            print("\n🎉 Test complete!")
            
        elif mode == "generate":
            # GENERATE MODE: Массовая генерация датасета
            print(f"\n📦 Generate Mode: Creating dataset with {num_scenes} scenes...")
            
            exporter = Exporter(builder, character_name)
            
            # Генерируем и сохраняем датасет
            stats = exporter.export_dataset(
                num_scenes=num_scenes,
                output_dir=str(project_root / "dataset"),
                create_placeholders=False  # Можно включить для визуализации
            )
            
            # Выводим статистику
            exporter.print_statistics(stats)
            
            print("\n🎉 Dataset generation complete!")
            print(f"📂 Dataset location: {(project_root / 'dataset').absolute()}")
            print("\nNext steps:")
            print("   1. Generate images using your preferred tool (ComfyUI, A1111, etc.)")
            print("   2. Train LoRA using Kohya_ss or OneTrainer")
            print("   3. Enjoy your high-quality character model!")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()