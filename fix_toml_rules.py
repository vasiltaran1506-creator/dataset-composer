#!/usr/bin/env python3
"""
Исправляет location_types и конкретные локации для предотвращения абсурдных комбинаций.
"""

from pathlib import Path
import tomli
import tomli_w

def fix_location_types():
    """Добавляет excludes_weather и excludes_outfit_categories в location_types"""
    
    location_types_dir = Path("scene-rules/location_types")
    if not location_types_dir.exists():
        print("❌ Папка location_types не найдена")
        return
    
    fixes = {
        "indoor_private.toml": {
            "hard_constraints": {
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky", "overcast", "cloudy"],
                "excludes_lighting_sources": ["sunlight", "bright sunlight", "moonlight", "starlight"],
                "allowed_outfit_categories": ["full_body", "topwear", "bottomwear", "legwear", "footwear", "underwear"],
            }
        },
        "indoor_commercial.toml": {
            "hard_constraints": {
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky", "overcast", "cloudy"],
                "excludes_lighting_sources": ["sunlight", "bright sunlight", "moonlight", "starlight"],
                "excludes_outfit_categories": ["full_body", "swimsuit", "underwear"],
            }
        },
        "indoor_cultural.toml": {
            "hard_constraints": {
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky", "overcast", "cloudy"],
                "excludes_lighting_sources": ["sunlight", "bright sunlight", "moonlight", "starlight"],
                "excludes_outfit_categories": ["full_body", "swimsuit", "underwear"],
            }
        },
        "indoor_institutional.toml": {
            "hard_constraints": {
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky", "overcast", "cloudy"],
                "excludes_lighting_sources": ["sunlight", "bright sunlight", "moonlight", "starlight"],
                "excludes_outfit_categories": ["full_body", "swimsuit", "underwear"],
            }
        },
        "outdoor_nature.toml": {
            "hard_constraints": {
                "excludes_lighting_sources": ["fluorescent light", "neon light", "lamplight", "candlelight"],
            },
            "soft_constraints": {
                "prefers_weather": ["sunny", "clear sky", "cloudy", "overcast", "partly cloudy"],
                "avoid_weather": ["storm", "heavy rain", "blizzard"],
            }
        },
        "outdoor_urban.toml": {
            "hard_constraints": {
                "excludes_outfit_categories": ["full_body", "swimsuit", "underwear"],
            },
            "soft_constraints": {
                "prefers_weather": ["clear sky", "sunny", "cloudy", "overcast", "light rain"],
                "avoid_weather": ["heavy rain", "storm", "blizzard", "dense fog"],
            }
        },
        "outdoor_recreational.toml": {
            "hard_constraints": {
                "excludes_outfit_categories": ["full_body", "underwear"],
            },
            "soft_constraints": {
                "prefers_weather": ["sunny", "clear sky", "cloudy", "partly cloudy"],
                "avoid_weather": ["storm", "heavy rain", "blizzard"],
            }
        },
        "outdoor_aquatic.toml": {
            "hard_constraints": {
                "excludes_weather": ["snow", "blizzard", "fog"],
                "excludes_outfit_categories": ["full_body", "topwear", "bottomwear", "footwear"],
            },
            "soft_constraints": {
                "prefers_weather": ["sunny", "clear sky"],
            }
        },
        "transit.toml": {
            "hard_constraints": {
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky"],
                "excludes_outfit_categories": ["swimsuit", "underwear"],
            }
        },
    }
    
    fixed_count = 0
    
    for filename, updates in fixes.items():
        filepath = location_types_dir / filename
        if not filepath.exists():
            print(f"⚠️ Файл не найден: {filename}")
            continue
        
        try:
            with open(filepath, 'rb') as f:
                data = tomli.load(f)
            
            changed = False
            
            for section, fields in updates.items():
                if section not in data:
                    data[section] = {}
                
                for field, values in fields.items():
                    if field not in data[section]:
                        data[section][field] = values
                        changed = True
                    else:
                        # Объединяем существующие значения с новыми
                        existing = set(data[section][field])
                        new_values = set(values)
                        merged = sorted(list(existing.union(new_values)))
                        if merged != data[section][field]:
                            data[section][field] = merged
                            changed = True
            
            if changed:
                with open(filepath, 'wb') as f:
                    tomli_w.dump(data, f)
                print(f"✅ Исправлен: {filename}")
                fixed_count += 1
            else:
                print(f"ℹ️ Без изменений: {filename}")
        
        except Exception as e:
            print(f"❌ Ошибка обработки {filename}: {e}")
    
    print(f"\n📄 Исправлено файлов location_types: {fixed_count}")

def fix_specific_locations():
    """Добавляет специфичные ограничения для конкретных локаций"""
    
    locations_dir = Path("scene-rules/locations")
    if not locations_dir.exists():
        print("❌ Папка locations не найдена")
        return
    
    fixes = {
        "beach.toml": {
            "hard_constraints": {
                "allowed_outfit_categories": ["swimsuit", "topwear", "bottomwear"],
                "excludes_weather": ["snow", "blizzard", "storm", "fog"],
            },
            "soft_constraints": {
                "prefers_weather": ["sunny", "clear sky", "partly cloudy"],
                "avoid_weather": ["rain", "overcast", "cloudy"],
            }
        },
        "park.toml": {
            "hard_constraints": {
                "excludes_outfit_categories": ["swimsuit", "full_body", "underwear"],
            },
            "soft_constraints": {
                "prefers_weather": ["sunny", "clear sky", "partly cloudy"],
            }
        },
        "pool.toml": {
            "hard_constraints": {
                "allowed_outfit_categories": ["swimsuit"],
                "excludes_weather": ["snow", "blizzard", "storm", "rain", "fog"],
            }
        },
        "street.toml": {
            "hard_constraints": {
                "excludes_outfit_categories": ["swimsuit", "full_body", "underwear"],
            }
        },
        "cafe.toml": {
            "hard_constraints": {
                "excludes_outfit_categories": ["swimsuit", "full_body", "underwear"],
            }
        },
        "library.toml": {
            "hard_constraints": {
                "excludes_outfit_categories": ["swimsuit", "full_body", "underwear"],
            }
        },
        "gym.toml": {
            "hard_constraints": {
                "allowed_outfit_categories": ["topwear", "bottomwear", "legwear", "footwear"],
                "excludes_outfit_categories": ["swimsuit", "full_body", "underwear", "footwear/boots"],
            }
        },
        "bathroom.toml": {
            "hard_constraints": {
                "allowed_outfit_categories": ["swimsuit", "underwear"],
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky"],
            }
        },
        "bedroom.toml": {
            "hard_constraints": {
                "allowed_outfit_categories": ["full_body", "topwear", "bottomwear", "legwear", "footwear", "underwear"],
                "excludes_weather": ["rain", "snow", "fog", "storm", "sunny", "clear sky"],
            }
        },
    }
    
    fixed_count = 0
    
    for filename, updates in fixes.items():
        filepath = locations_dir / filename
        if not filepath.exists():
            print(f"⚠️ Файл не найден: {filename}")
            continue
        
        try:
            with open(filepath, 'rb') as f:
                data = tomli.load(f)
            
            changed = False
            
            for section, fields in updates.items():
                if section not in data:
                    data[section] = {}
                
                for field, values in fields.items():
                    if field not in data[section]:
                        data[section][field] = values
                        changed = True
                    else:
                        # Объединяем существующие значения с новыми
                        existing = set(data[section][field])
                        new_values = set(values)
                        merged = sorted(list(existing.union(new_values)))
                        if merged != data[section][field]:
                            data[section][field] = merged
                            changed = True
            
            if changed:
                with open(filepath, 'wb') as f:
                    tomli_w.dump(data, f)
                print(f"✅ Исправлен: {filename}")
                fixed_count += 1
            else:
                print(f"ℹ️ Без изменений: {filename}")
        
        except Exception as e:
            print(f"❌ Ошибка обработки {filename}: {e}")
    
    print(f"\n📄 Исправлено файлов locations: {fixed_count}")

if __name__ == "__main__":
    print("🔧 Исправление location_types...")
    print("=" * 60)
    fix_location_types()
    
    print("\n🔧 Исправление конкретных локаций...")
    print("=" * 60)
    fix_specific_locations()
    
    print("\n" + "=" * 60)
    print("✅ Все исправления применены!")
    print("\nТеперь перезапусти программу и сгенерируй новые промпты.")
    print("Снега в библиотеке и пижам в кафе больше не будет! 🎉")