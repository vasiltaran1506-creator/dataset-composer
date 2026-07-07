#!/usr/bin/env python3
"""
Полная регенерация scene-rules на основе реальных тегов из all_tags.json.
Генерирует 100% валидные TOML-файлы с соблюдением матрицы совместимости.
"""

import json
from pathlib import Path
import tomli_w

# Загружаем реальные теги
with open('all_tags.json', 'r', encoding='utf-8') as f:
    all_tags_raw = json.load(f)

# Функция для извлечения тегов (с учётом пробелов в ключах)
def get_tags(category_key, subcategory=None):
    """Извлекает теги из категории"""
    # Пробуем ключ с пробелом
    key_with_space = category_key + ' '
    if key_with_space in all_tags_raw:
        category_data = all_tags_raw[key_with_space]
    elif category_key in all_tags_raw:
        category_data = all_tags_raw[category_key]
    else:
        return []
    
    if subcategory:
        subcat_with_space = subcategory + ' '
        if subcat_with_space in category_data:
            return category_data[subcat_with_space]
        elif subcategory in category_data:
            return category_data[subcategory]
        return []
    
    # Собираем все теги из всех подкатегорий
    all_category_tags = []
    for subcat_tags in category_data.values():
        if isinstance(subcat_tags, list):
            all_category_tags.extend([t.strip() for t in subcat_tags])
    return all_category_tags

# Извлекаем все теги
actions = get_tags('04_action')
locations_indoor = get_tags('08_location', 'indoor')
locations_outdoor = get_tags('08_location', 'outdoor')
all_locations = locations_indoor + locations_outdoor
weather_clear = get_tags('10_weather', 'clear')
weather_rain = get_tags('10_weather', 'rain')
weather_snow = get_tags('10_weather', 'snow')
weather_effects = get_tags('10_weather', 'effects')
all_weather = weather_clear + weather_rain + weather_snow + weather_effects
camera_angle = get_tags('06_camera', 'angle')
camera_framing = get_tags('06_camera', 'framing')
all_camera = camera_angle + camera_framing
poses_base = get_tags('03_pose', 'base')
poses_arms = get_tags('03_pose', 'arms')
poses_head = get_tags('03_pose', 'head')
poses_legs = get_tags('03_pose', 'legs')
all_poses = poses_base + poses_arms + poses_head + poses_legs
lighting_direction = get_tags('07_lighting', 'direction')
lighting_quality = get_tags('07_lighting', 'quality')
lighting_source = get_tags('07_lighting', 'source')
all_lighting = lighting_direction + lighting_quality + lighting_source
expressions_eyes = get_tags('05_expression', 'eyes_expr')
expressions_mood = get_tags('05_expression', 'mood')
expressions_mouth = get_tags('05_expression', 'mouth')
all_expressions = expressions_eyes + expressions_mood + expressions_mouth

# Props по категориям
props_books = get_tags('09_props', 'books')
props_electronics = get_tags('09_props', 'electronics')
props_food = get_tags('09_props', 'food_drink')
props_furniture = get_tags('09_props', 'furniture')
props_kitchen = get_tags('09_props', 'kitchen_tools')
props_nature = get_tags('09_props', 'nature')
props_stationery = get_tags('09_props', 'stationery')
props_tools = get_tags('09_props', 'tools')
props_toys = get_tags('09_props', 'toys')
all_props = props_books + props_electronics + props_food + props_furniture + props_kitchen + props_nature + props_stationery + props_tools + props_toys

print(f"✅ Загружено тегов:")
print(f"   Actions: {len(actions)}")
print(f"   Locations: {len(all_locations)}")
print(f"   Weather: {len(all_weather)}")
print(f"   Camera: {len(all_camera)}")
print(f"   Poses: {len(all_poses)}")
print(f"   Lighting: {len(all_lighting)}")
print(f"   Expressions: {len(all_expressions)}")
print(f"   Props: {len(all_props)}")

# ═══════════════════════════════════════════════════════════════════════════
# МАТРИЦА СОВМЕСТИМОСТИ
# ═══════════════════════════════════════════════════════════════════════════

action_configs = {
    'reading': {
        'allowed_locations': ['library', 'cafe', 'bedroom', 'living room', 'office', 'train interior', 'classroom'],
        'excludes_locations': ['kitchen', 'bathroom', 'beach', 'gym', 'street', 'park'],
        'prefers_poses': ['sitting', 'sitting on chair', 'sitting on floor', 'lying on back', 'leaning forward'],
        'prefers_props': props_books[:8],
        'prefers_expressions': ['focused', 'thoughtful', 'calm', 'gentle smile', 'looking down'],
    },
    'cooking': {
        'allowed_locations': ['kitchen'],
        'excludes_locations': ['bedroom', 'bathroom', 'library', 'cafe', 'beach', 'gym', 'street', 'park'],
        'prefers_poses': ['standing', 'bending forward', 'reaching forward'],
        'prefers_props': props_kitchen[:10],
        'prefers_expressions': ['focused', 'smile', 'determined', 'happy'],
    },
    'sleeping': {
        'allowed_locations': ['bedroom', 'train interior', 'hotel room', 'living room'],
        'excludes_locations': ['kitchen', 'bathroom', 'library', 'cafe', 'beach', 'gym', 'street', 'park', 'classroom'],
        'prefers_poses': ['lying on back', 'lying on side', 'curled up', 'fetal position'],
        'prefers_props': ['bed', 'pillow', 'blanket', 'stuffed animal'],
        'prefers_expressions': ['peaceful', 'relaxed', 'sleepy'],
    },
    'swimming': {
        'allowed_locations': ['beach', 'indoor pool', 'lake', 'river'],
        'excludes_locations': ['bedroom', 'kitchen', 'bathroom', 'library', 'cafe', 'gym', 'street', 'park', 'classroom'],
        'prefers_poses': ['floating', 'arms up', 'arms spread'],
        'prefers_props': [],
        'prefers_expressions': ['happy', 'excited', 'smile', 'joyful'],
    },
    'exercising': {
        'allowed_locations': ['gym', 'park', 'beach', 'running track', 'sports field'],
        'excludes_locations': ['library', 'cafe', 'bedroom', 'bathroom', 'kitchen', 'classroom'],
        'prefers_poses': ['standing', 'stretching', 'yoga_pose', 'plank_position', 'full_body_stretch'],
        'prefers_props': ['water_bottle'],
        'prefers_expressions': ['focused', 'determined', 'energetic', 'confident'],
    },
    'eating': {
        'allowed_locations': ['kitchen', 'cafe', 'restaurant', 'dining room', 'bedroom'],
        'excludes_locations': ['bathroom', 'library', 'gym', 'street', 'park'],
        'prefers_poses': ['sitting', 'sitting_at_table', 'sitting on chair'],
        'prefers_props': props_food[:8] + ['fork', 'spoon', 'chopsticks'],
        'prefers_expressions': ['happy', 'satisfied', 'smile', 'joyful'],
    },
    'drinking': {
        'allowed_locations': ['cafe', 'kitchen', 'bar', 'balcony', 'bedroom', 'restaurant'],
        'excludes_locations': ['bathroom', 'library', 'gym', 'street', 'park'],
        'prefers_poses': ['sitting', 'standing', 'sitting_at_table'],
        'prefers_props': ['coffee cup', 'teacup', 'mug', 'glass', 'wine glass'],
        'prefers_expressions': ['relaxed', 'smile', 'content', 'thoughtful'],
    },
    'walking': {
        'allowed_locations': ['street', 'park', 'beach', 'sidewalk', 'forest', 'mountain', 'shopping mall'],
        'excludes_locations': ['bathroom', 'kitchen', 'bedroom', 'library', 'gym', 'classroom'],
        'prefers_poses': ['standing', 'casual_stance'],
        'prefers_props': ['bag', 'backpack', 'smartphone'],
        'prefers_expressions': ['calm', 'thoughtful', 'smile', 'relaxed'],
    },
    'studying': {
        'allowed_locations': ['library', 'cafe', 'classroom', 'bedroom', 'office'],
        'excludes_locations': ['kitchen', 'bathroom', 'beach', 'gym', 'street', 'park'],
        'prefers_poses': ['sitting', 'sitting_at_desk', 'leaning forward', 'hunched_over'],
        'prefers_props': props_stationery[:8] + props_books[:4],
        'prefers_expressions': ['focused', 'thoughtful', 'concentrated', 'determined'],
    },
    'bathing': {
        'allowed_locations': ['bathroom'],
        'excludes_locations': ['kitchen', 'bedroom', 'library', 'cafe', 'street', 'beach', 'gym', 'park', 'classroom'],
        'prefers_poses': ['sitting_in_tub', 'reclining_in_tub', 'lying_in_tub'],
        'prefers_props': [],
        'prefers_expressions': ['relaxed', 'peaceful', 'calm', 'content'],
    },
    'working': {
        'allowed_locations': ['office', 'cafe', 'library', 'bedroom', 'classroom'],
        'excludes_locations': ['bathroom', 'kitchen', 'beach', 'gym', 'street', 'park'],
        'prefers_poses': ['sitting', 'sitting_at_desk', 'typing on keyboard'],
        'prefers_props': ['laptop', 'desktop computer', 'notebook', 'coffee cup'],
        'prefers_expressions': ['focused', 'thoughtful', 'determined', 'concentrated'],
    },
    'shopping': {
        'allowed_locations': ['shopping mall', 'boutique', 'supermarket', 'street', 'marketplace'],
        'excludes_locations': ['bedroom', 'bathroom', 'kitchen', 'library', 'gym', 'classroom'],
        'prefers_poses': ['standing', 'walking', 'casual_stance'],
        'prefers_props': ['shopping bag', 'bag', 'wallet'],
        'prefers_expressions': ['happy', 'excited', 'smile', 'joyful'],
    },
    'photography': {
        'allowed_locations': ['street', 'park', 'beach', 'mountain', 'forest', 'rooftop', 'balcony'],
        'excludes_locations': ['bathroom', 'kitchen', 'bedroom', 'library', 'gym', 'classroom'],
        'prefers_poses': ['standing', 'holding object'],
        'prefers_props': ['camera', 'dslr', 'tripod'],
        'prefers_expressions': ['focused', 'concentrated', 'determined'],
    },
    'dancing': {
        'allowed_locations': ['street', 'beach', 'park', 'nightclub', 'dance studio', 'balcony', 'bedroom'],
        'excludes_locations': ['bathroom', 'kitchen', 'library', 'cafe', 'classroom', 'gym'],
        'prefers_poses': ['arms up', 'arms spread', 'spinning', 'jumping'],
        'prefers_props': [],
        'prefers_expressions': ['happy', 'joyful', 'excited', 'ecstatic', 'smile'],
    },
    'playing music': {
        'allowed_locations': ['bedroom', 'street', 'park', 'cafe', 'balcony', 'concert hall', 'recording studio'],
        'excludes_locations': ['bathroom', 'kitchen', 'library', 'gym', 'classroom'],
        'prefers_poses': ['sitting', 'standing', 'holding object'],
        'prefers_props': ['guitar', 'playing guitar', 'playing piano', 'playing violin', 'microphone'],
        'prefers_expressions': ['focused', 'peaceful', 'relaxed', 'smile'],
    },
    'writing': {
        'allowed_locations': ['library', 'cafe', 'bedroom', 'classroom', 'office', 'balcony'],
        'excludes_locations': ['kitchen', 'bathroom', 'beach', 'gym', 'street', 'park'],
        'prefers_poses': ['sitting', 'sitting_at_desk', 'leaning forward', 'writing with pen'],
        'prefers_props': ['pen', 'pencil', 'fountain_pen', 'notebook', 'diary'],
        'prefers_expressions': ['focused', 'thoughtful', 'concentrated', 'determined'],
    },
    'sunbathing': {
        'allowed_locations': ['beach', 'balcony', 'rooftop', 'park', 'pool'],
        'excludes_locations': ['kitchen', 'bathroom', 'library', 'cafe', 'gym', 'classroom', 'street'],
        'prefers_poses': ['lying on back', 'reclining', 'lying on stomach'],
        'prefers_props': ['sunscreen', 'sunglasses', 'beach towel'],
        'prefers_expressions': ['relaxed', 'peaceful', 'content', 'sleepy'],
    },
}

# Конфигурация локаций
location_configs = {
    'bedroom': {
        'allowed_actions': ['sleeping', 'reading', 'studying', 'working', 'eating', 'drinking', 'playing music', 'writing', 'dancing'],
        'excluded_actions': ['cooking', 'bathing', 'swimming', 'exercising', 'sunbathing', 'shopping', 'photography', 'walking'],
        'prefers_props': props_furniture[:10] + props_electronics[:3] + ['book', 'smartphone', 'pillow', 'blanket'],
    },
    'kitchen': {
        'allowed_actions': ['cooking', 'eating', 'drinking'],
        'excluded_actions': ['sleeping', 'bathing', 'swimming', 'exercising', 'studying', 'reading', 'working', 'shopping', 'photography', 'walking', 'dancing', 'sunbathing', 'playing music'],
        'prefers_props': props_kitchen + props_furniture[:5],
    },
    'bathroom': {
        'allowed_actions': ['bathing'],
        'excluded_actions': ['cooking', 'sleeping', 'reading', 'studying', 'eating', 'drinking', 'exercising', 'swimming', 'working', 'shopping', 'photography', 'walking', 'dancing', 'sunbathing', 'playing music', 'writing'],
        'prefers_props': ['bathtub', 'shower', 'mirror', 'towel', 'soap'],
    },
    'library': {
        'allowed_actions': ['reading', 'studying', 'working', 'writing'],
        'excluded_actions': ['sleeping', 'cooking', 'bathing', 'swimming', 'exercising', 'eating', 'drinking', 'sunbathing', 'shopping', 'dancing', 'photography', 'playing music', 'walking'],
        'prefers_props': props_books[:15] + props_furniture[:8] + props_stationery[:5],
    },
    'cafe': {
        'allowed_actions': ['reading', 'eating', 'drinking', 'working', 'studying', 'writing', 'playing music'],
        'excluded_actions': ['sleeping', 'cooking', 'bathing', 'swimming', 'exercising', 'sunbathing', 'shopping', 'dancing', 'walking', 'photography'],
        'prefers_props': props_food[:10] + props_furniture[:5] + ['coffee cup', 'teacup', 'laptop', 'book'],
    },
    'beach': {
        'allowed_actions': ['swimming', 'walking', 'sunbathing', 'exercising', 'photography', 'dancing'],
        'excluded_actions': ['cooking', 'sleeping', 'bathing', 'reading', 'studying', 'working', 'shopping', 'writing', 'playing music'],
        'prefers_props': ['sand', 'beach towel', 'sunglasses', 'sunscreen', 'surfboard', 'beach umbrella'],
    },
    'park': {
        'allowed_actions': ['walking', 'exercising', 'reading', 'photography', 'dancing', 'playing music'],
        'excluded_actions': ['cooking', 'sleeping', 'bathing', 'working', 'shopping', 'sunbathing', 'swimming'],
        'prefers_props': props_nature[:10] + props_furniture[:3] + ['bench', 'tree'],
    },
    'street': {
        'allowed_actions': ['walking', 'shopping', 'photography', 'dancing'],
        'excluded_actions': ['sleeping', 'cooking', 'bathing', 'studying', 'reading', 'working', 'exercising', 'sunbathing', 'writing', 'playing music', 'swimming'],
        'prefers_props': ['smartphone', 'bag', 'backpack', 'shopping bag'],
    },
    'gym': {
        'allowed_actions': ['exercising'],
        'excluded_actions': ['sleeping', 'cooking', 'bathing', 'reading', 'studying', 'working', 'shopping', 'photography', 'walking', 'dancing', 'sunbathing', 'eating', 'drinking'],
        'prefers_props': ['water_bottle', 'towel', 'yoga mat', 'dumbbell'],
    },
}

# Конфигурация погоды
weather_configs = {
    'sunny': {
        'prefers_locations': ['beach', 'park', 'street', 'balcony', 'rooftop', 'garden'],
        'prefers_actions': ['walking', 'swimming', 'sunbathing', 'photography', 'exercising'],
        'prefers_lighting': ['sunlight', 'bright sunlight', 'natural lighting', 'golden hour'],
    },
    'rain': {
        'prefers_locations': ['cafe', 'library', 'bedroom', 'office', 'classroom', 'train interior'],
        'prefers_actions': ['reading', 'studying', 'working', 'drinking'],
        'prefers_lighting': ['overcast lighting', 'soft lighting', 'diffused lighting', 'gloomy lighting'],
        'prefers_props': ['umbrella', 'raincoat', 'rain boots'],
    },
    'snow': {
        'prefers_locations': ['street', 'park', 'mountain', 'forest', 'beach'],
        'prefers_actions': ['walking', 'photography'],
        'prefers_lighting': ['soft lighting', 'diffused lighting', 'overcast lighting'],
        'prefers_props': ['scarf', 'gloves', 'winter coat'],
    },
    'fog': {
        'prefers_locations': ['forest', 'mountain', 'lake', 'street', 'park'],
        'prefers_actions': ['walking', 'photography'],
        'prefers_lighting': ['misty lighting', 'foggy lighting', 'ethereal lighting', 'dreamy lighting', 'gloomy lighting'],
    },
    'overcast': {
        'prefers_locations': ['street', 'park', 'cafe', 'beach', 'mountain'],
        'prefers_actions': ['walking', 'photography', 'reading', 'working'],
        'prefers_lighting': ['overcast lighting', 'soft lighting', 'diffused lighting', 'cloudy lighting'],
    },
    'clear_sky': {
        'prefers_locations': ['park', 'street', 'beach', 'mountain', 'balcony', 'rooftop'],
        'prefers_actions': ['walking', 'photography', 'exercising', 'sunbathing'],
        'prefers_lighting': ['sunlight', 'bright sunlight', 'natural lighting', 'blue hour'],
    },
    'cloudy': {
        'prefers_locations': ['street', 'park', 'cafe', 'beach', 'mountain'],
        'prefers_actions': ['walking', 'photography', 'reading', 'working'],
        'prefers_lighting': ['cloudy lighting', 'soft lighting', 'diffused lighting', 'overcast lighting'],
    },
    'storm': {
        'prefers_locations': ['bedroom', 'cafe', 'library', 'office', 'classroom', 'train interior'],
        'prefers_actions': ['reading', 'studying', 'working', 'sleeping'],
        'prefers_lighting': ['dramatic lighting', 'moody lighting', 'dim lighting', 'gloomy lighting'],
    },
}

# Конфигурация камеры
camera_configs = {
    'pov': {
        'prefers_locations': ['bedroom', 'bathroom', 'cafe', 'kitchen', 'train interior'],
        'prefers_actions': ['reading', 'drinking', 'eating', 'using smartphone', 'holding object'],
    },
    'close_up': {
        'prefers_locations': ['bedroom', 'library', 'cafe', 'classroom', 'office', 'kitchen'],
        'prefers_actions': ['reading', 'studying', 'thinking', 'writing', 'drinking', 'eating'],
    },
    'full_body': {
        'prefers_locations': ['street', 'park', 'beach', 'gym', 'classroom', 'sports field'],
        'prefers_actions': ['walking', 'standing', 'exercising', 'dancing', 'shopping'],
    },
    'portrait': {
        'prefers_locations': ['bedroom', 'library', 'cafe', 'park', 'street', 'beach', 'balcony'],
        'prefers_actions': ['posing', 'looking at viewer', 'thinking', 'smiling', 'reading'],
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# ГЕНЕРАЦИЯ TOML-ФАЙЛОВ
# ═══════════════════════════════════════════════════════════════════════════

def create_toml_file(filepath, data):
    """Создаёт TOML-файл"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        tomli_w.dump(data, f)

# Очистка старых файлов
import shutil
rules_dir = Path('scene-rules')
if rules_dir.exists():
    shutil.rmtree(rules_dir)
rules_dir.mkdir(parents=True)

# Генерация Actions
print("\n📝 Генерация Actions...")
for action_name, config in action_configs.items():
    safe_name = action_name.replace(' ', '_')
    data = {
        'meta': {
            'id': safe_name,
            'display_name': action_name.title(),
        },
        'hard_constraints': {
            'allowed_locations': [loc.strip() for loc in config['allowed_locations'] if loc.strip() in all_locations],
            'excludes_locations': [loc.strip() for loc in config['excludes_locations'] if loc.strip() in all_locations],
        },
        'soft_constraints': {
            'prefers_locations': [loc.strip() for loc in config['allowed_locations'][:3] if loc.strip() in all_locations],
            'prefers_poses': [p.strip() for p in config['prefers_poses'] if p.strip() in all_poses],
            'prefers_props': [p.strip() for p in config['prefers_props'] if p.strip() in all_props],
            'prefers_expressions': [e.strip() for e in config['prefers_expressions'] if e.strip() in all_expressions],
        }
    }
    filepath = rules_dir / 'actions' / f'{safe_name}.toml'
    create_toml_file(filepath, data)
    print(f"   ✅ {safe_name}.toml")

# Генерация Locations
print("\n📝 Генерация Locations...")
for location_name, config in location_configs.items():
    safe_name = location_name.replace(' ', '_')
    data = {
        'meta': {
            'id': safe_name,
            'display_name': location_name.title(),
            'type': 'indoor_private' if location_name in ['bedroom', 'kitchen', 'bathroom'] else 'indoor_public' if location_name in ['library', 'cafe', 'classroom'] else 'outdoor_nature' if location_name in ['beach', 'park'] else 'outdoor_urban',
        },
        'hard_constraints': {
            'allowed_actions': [a.strip() for a in config['allowed_actions'] if a.strip() in actions],
            'excluded_actions': [a.strip() for a in config['excluded_actions'] if a.strip() in actions],
        },
        'soft_constraints': {
            'prefers_actions': [a.strip() for a in config['allowed_actions'][:5] if a.strip() in actions],
            'prefers_props': [p.strip() for p in config['prefers_props'] if p.strip() in all_props],
        }
    }
    filepath = rules_dir / 'locations' / f'{safe_name}.toml'
    create_toml_file(filepath, data)
    print(f"   ✅ {safe_name}.toml")

# Генерация Weather
print("\n📝 Генерация Weather...")
for weather_name, config in weather_configs.items():
    safe_name = weather_name.replace(' ', '_')
    data = {
        'meta': {
            'id': safe_name,
            'display_name': weather_name.replace('_', ' ').title(),
        },
        'soft_constraints': {
            'prefers_locations': [loc.strip() for loc in config['prefers_locations'] if loc.strip() in all_locations],
            'prefers_actions': [a.strip() for a in config['prefers_actions'] if a.strip() in actions],
            'prefers_lighting_sources': [l.strip() for l in config['prefers_lighting'] if l.strip() in all_lighting],
        }
    }
    if 'prefers_props' in config:
        data['soft_constraints']['prefers_props'] = [p.strip() for p in config['prefers_props'] if p.strip() in all_props]
    
    filepath = rules_dir / 'weather' / f'{safe_name}.toml'
    create_toml_file(filepath, data)
    print(f"   ✅ {safe_name}.toml")

# Генерация Camera
print("\n📝 Генерация Camera...")
for camera_name, config in camera_configs.items():
    safe_name = camera_name.replace(' ', '_')
    data = {
        'meta': {
            'id': safe_name,
            'display_name': camera_name.replace('_', ' ').title(),
        },
        'soft_constraints': {
            'prefers_locations': [loc.strip() for loc in config['prefers_locations'] if loc.strip() in all_locations],
            'prefers_actions': [a.strip() for a in config['prefers_actions'] if a.strip() in actions],
        }
    }
    filepath = rules_dir / 'camera' / f'{safe_name}.toml'
    create_toml_file(filepath, data)
    print(f"   ✅ {safe_name}.toml")

print("\n" + "="*60)
print("✅ Регенерация завершена!")
print(f"📂 Файлы сохранены в: {rules_dir.absolute()}")
print("\nТеперь запусти Validate в программе — все теги должны быть валидными!")