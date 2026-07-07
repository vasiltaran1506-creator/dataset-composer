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
from coverage_tracker import CoverageTracker


def main():
    print("🚀 Dataset Composer v1.1 - Coverage Engine Update")
    print("=" * 60)
    
    # 1. Парсинг аргументов командной строки
    mode = "test"
    num_scenes = 5
    analyze_folder: str | None = None
    balance_from_folder: str | None = None
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "generate":
            mode = "generate"
            if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
                try:
                    num_scenes = int(sys.argv[2])
                except ValueError:
                    print("❌ Error: Number of scenes must be an integer")
                    sys.exit(1)
                    
            if "--balance-from" in sys.argv:
                idx = sys.argv.index("--balance-from")
                if idx + 1 < len(sys.argv):
                    balance_from_folder = sys.argv[idx + 1]
                    
        elif sys.argv[1] == "analyze":
            mode = "analyze"
            if len(sys.argv) > 2:
                analyze_folder = sys.argv[2]
            else:
                print("❌ Error: Usage: python main.py analyze <folder_path>")
                sys.exit(1)
    
    project_root = Path("..")
    loader = ConfigLoader(project_root=str(project_root))
    library = PromptLibrary(library_path=str(project_root / "prompt-library"))
    
    try:
        # 2. Загрузка данных
        profile = loader.load_character_profile()
        rules = loader.load_scene_rules()
        loader.load_location_types()  
        library.load_library()
        
        character_name = loader.get_character_name()
        fixed_traits = loader.get_fixed_traits()
        character_trigger = loader.get_character_trigger()
        
        print(f"\n✅ System initialized for: {character_name}")
        print(f"   Rules loaded: {len(rules)}")
        print(f"   Location types loaded: {len(loader.location_types)}")
        print(f"   Tags available: {library.get_stats()['total_tags']}")
        
        # 3. Инициализация компонентов
        builder = SceneBuilder(
            library=library, 
            scene_rules=rules, 
            character_profile=profile,
            location_types=loader.location_types
        )
        
        # Списки для Coverage Tracker
        available_locs = [k.split('.')[-1] for k in rules.keys() if k.startswith('locations.')]
        available_acts = [k.split('.')[-1] for k in rules.keys() if k.startswith('actions.')]
        available_weaths = [k.split('.')[-1] for k in rules.keys() if k.startswith('weather.')]
        available_cams = [k.split('.')[-1] for k in rules.keys() if k.startswith('camera.')]

        # 4. Роутинг по режимам
        if mode == "analyze":
            # Явная проверка для Pylance: если папка не передалась, выходим
            if not analyze_folder:
                print("❌ Error: Folder path is missing.")
                sys.exit(1)
                
            print(f"\n🔍 Analyze Mode: Scanning folder '{analyze_folder}'...")
            tracker = CoverageTracker(
                available_locations=available_locs,
                available_actions=available_acts,
                available_weathers=available_weaths,
                available_cameras=available_cams
            )
            matrix = tracker.scan_folder(analyze_folder)
            tracker.print_report(matrix)
            print("✅ Анализ завершен!")
            
        elif mode == "generate":
            # ЗАХАРКОЖЕННЫЙ ПУТЬ ДЛЯ СОХРАНЕНИЯ (вне репозитория)
            output_directory = r"D:\VASILY\MY GENERATION\Test Generations"
            weights: dict | None = None # Явная типизация для Pylance
            
            # Если указан --balance-from, сначала анализируем папку
            if balance_from_folder:
                print(f"\n⚖️ Балансировка на основе папки: {balance_from_folder}")
                tracker = CoverageTracker(
                    available_locations=available_locs,
                    available_actions=available_acts,
                    available_weathers=available_weaths,
                    available_cameras=available_cams
                )
                matrix = tracker.scan_folder(balance_from_folder)
                weights = tracker.calculate_generation_weights(matrix)
                print("✅ Веса рассчитаны. (Применение весов к генератору будет добавлено на следующем шаге)")
                # TODO: Передать weights в exporter/builder
            
            print(f"\n📦 Generate Mode: Creating dataset with {num_scenes} scenes...")
            print(f"📂 Output directory: {output_directory}")
            
            exporter = Exporter(builder, character_name, generation_weights=weights)
            stats = exporter.export_dataset(
                num_scenes=num_scenes,
                output_dir=output_directory,
                create_placeholders=False
            )
            exporter.print_statistics(stats)
            
            print("\n🎉 Dataset generation complete!")
            print(f"📂 Your prompts are saved at: {output_directory}")
            
        else: # mode == "test"
            print(f"\n🎬 Test Mode: Generating 5 random scenes...")
            print("-" * 60)
            
            print(f"Available locations: {len(available_locs)}")
            print(f"   {', '.join(sorted(available_locs))}\n")
            
            test_locations = random.sample(available_locs, min(5, len(available_locs)))
            print(f"Testing {len(test_locations)} random locations:\n")
            
            for loc in test_locations:
                print(f"\n📍 Location: {loc.capitalize()}")
                scene = builder.build_scene(loc)
                prompt = scene.to_structured_prompt(fixed_traits, character_trigger)
                print(f"📝 Prompt:\n   {prompt}")
                print("-" * 60)

            print("\n🎉 Test complete!")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()