#!/usr/bin/env python3
"""
Полное исправление TOML-файлов локаций:
1. Добавляет excludes_weather для indoor локаций
2. Добавляет excludes_outfit_categories
3. Добавляет excludes_props (кровати, ванны и т.д.)
4. Добавляет excludes_lighting_sources
"""

from pathlib import Path
import tomli
import tomli_w

def fix_all_locations():
    locations_dir = Path("scene-rules/locations")
    if not locations_dir.exists():
        print("❌ Папка locations не найдена")
        return
    
    # Полная матрица ограничений
    location_constraints = {
        "bedroom": {
            "allowed_outfit_categories": ["full_body", "topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["swimsuit"],
            "excludes_weather": ["rain", "snow", "storm", "fog", "sunny", "clear_sky", "cloudy", "overcast"],
            "excludes_lighting_sources": ["sunlight", "bright sunlight", "moonlight", "starlight"],
            "excludes_props": ["frying_pan", "knife", "surfboard", "cooking pot"]
        },
        "kitchen": {
            "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["full_body", "swimsuit"],
            "excludes_weather": ["rain", "snow", "storm", "fog", "sunny", "clear_sky"],
            "excludes_lighting_sources": ["sunlight", "moonlight", "candlelight"],
            "excludes_props": ["bed", "pillow", "blanket", "surfboard", "bathtub", "shower"]
        },
        "bathroom": {
            "allowed_outfit_categories": ["swimsuit"],
            "excludes_outfit_categories": ["topwear", "bottomwear", "full_body", "footwear"],
            "excludes_weather": ["rain", "snow", "storm", "fog", "sunny", "clear_sky"],
            "excludes_lighting_sources": ["sunlight", "bright sunlight"],
            "excludes_props": ["book", "laptop", "frying_pan", "knife", "bed"]
        },
        "library": {
            "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["swimsuit", "full_body"],
            "excludes_weather": ["rain", "snow", "storm", "fog", "sunny", "clear_sky"],
            "excludes_lighting_sources": ["sunlight", "bright sunlight", "neon light"],
            "excludes_props": ["bed", "frying_pan", "knife", "surfboard", "bathtub", "shower", "single bed", "double bed", "bunk bed", "canopy bed"]
        },
        "cafe": {
            "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["swimsuit", "full_body"],
            "excludes_weather": ["rain", "snow", "storm", "fog", "sunny", "clear_sky"],
            "excludes_lighting_sources": ["sunlight", "bright sunlight", "moonlight"],
            "excludes_props": ["bed", "pillow", "blanket", "frying_pan", "knife", "surfboard", "single bed", "double bed", "bunk bed", "canopy bed"]
        },
        "beach": {
            "allowed_outfit_categories": ["swimsuit", "topwear", "bottomwear"],
            "excludes_outfit_categories": ["full_body"],
            "excludes_weather": ["snow", "storm", "fog"],
            "excludes_lighting_sources": ["fluorescent light", "neon light", "lamplight", "candlelight"],
            "excludes_props": ["bed", "laptop", "frying_pan", "knife", "book"]
        },
        "park": {
            "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["swimsuit", "full_body"],
            "excludes_weather": ["storm", "heavy rain", "blizzard"],
            "excludes_lighting_sources": ["fluorescent light", "neon light", "lamplight"],
            "excludes_props": ["bed", "frying_pan", "knife", "laptop", "single bed", "double bed", "bunk bed"]
        },
        "street": {
            "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["swimsuit", "full_body"],
            "excludes_weather": ["storm", "heavy rain", "blizzard"],
            "excludes_lighting_sources": ["candlelight", "firelight"],
            "excludes_props": ["bed", "pillow", "blanket", "frying_pan", "bathtub"]
        },
        "gym": {
            "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
            "excludes_outfit_categories": ["swimsuit", "full_body"],
            "excludes_weather": ["rain", "snow", "storm", "fog"],
            "excludes_lighting_sources": ["candlelight", "firelight", "moonlight"],
            "excludes_props": ["bed", "pillow", "blanket", "frying_pan", "knife", "book", "laptop"]
        }
    }
    
    fixed_count = 0
    
    for filename, constraints in location_constraints.items():
        filepath = locations_dir / f"{filename}.toml"
        if not filepath.exists():
            print(f"⚠️ Файл не найден: {filename}.toml")
            continue
        
        try:
            with open(filepath, 'rb') as f:
                data = tomli.load(f)
            
            changed = False
            
            if 'hard_constraints' not in data:
                data['hard_constraints'] = {}
            
            for field, values in constraints.items():
                if field not in data['hard_constraints']:
                    data['hard_constraints'][field] = values
                    changed = True
                else:
                    existing = set(data['hard_constraints'][field])
                    new_values = set(values)
                    merged = sorted(list(existing.union(new_values)))
                    if merged != data['hard_constraints'][field]:
                        data['hard_constraints'][field] = merged
                        changed = True
            
            if changed:
                with open(filepath, 'wb') as f:
                    tomli_w.dump(data, f)
                print(f"✅ Исправлен: {filename}.toml")
                fixed_count += 1
            else:
                print(f"ℹ️ Без изменений: {filename}.toml")
        
        except Exception as e:
            print(f"❌ Ошибка обработки {filename}.toml: {e}")
    
    print(f"\n📄 Исправлено файлов: {fixed_count}")

if __name__ == "__main__":
    fix_all_locations()