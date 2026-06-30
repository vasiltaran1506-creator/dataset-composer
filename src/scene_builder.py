"""
Scene Builder v2 - собирает сцены с умной логикой одежды и учетом Character Profile
"""
import random
from scene import Scene
from prompt_library import PromptLibrary


class SceneBuilder:
    """Строит логически согласованные сцены"""
    
    def __init__(self, library: PromptLibrary, scene_rules: dict, character_profile: dict):
        self.library = library
        self.scene_rules = scene_rules
        # Извлекаем профиль персонажа (поддерживаем оба формата YAML)
        self.char_profile = character_profile.get('character', character_profile)
        
    def _get_outfit_whitelist(self) -> dict:
        """Возвращает whitelist одежды из character-profile"""
        return self.char_profile.get('outfit_whitelist', {})
        
    def _choose_smart_outfit(self, allowed_categories: list) -> dict:
        """
        Умный выбор одежды: собирает полный комплект (Top + Bottom + Legwear)
        и фильтрует его через character-profile.yaml
        """
        outfit = {"full": "", "top": "", "bottom": "", "legwear": "", "footwear": ""}
        whitelist = self._get_outfit_whitelist()
        
        # Группируем разрешенные категории по типам
        tops = [c for c in allowed_categories if "topwear" in c]
        bottoms = [c for c in allowed_categories if "bottomwear" in c]
        legwears = [c for c in allowed_categories if "legwear" in c]
        full_body = [c for c in allowed_categories if "full_body" in c]
        footwears = [c for c in allowed_categories if "footwear" in c]
        
        # ШАНС 1: Выбрать цельный наряд (full_body: пижама, платье, купальник)
        if full_body and random.random() < 0.4:
            chosen_cat = random.choice(full_body)
            # Пытаемся найти тег, который есть в whitelist Луны
            outfit["full"] = self._get_filtered_tag(chosen_cat, whitelist)
            return outfit # Если выбрали пижаму, верх и низ не нужны
            
        # ШАНС 2: Собрать комплект из частей (Top + Bottom)
        if tops:
            chosen_cat = random.choice(tops)
            outfit["top"] = self._get_filtered_tag(chosen_cat, whitelist)
            
        if bottoms:
            chosen_cat = random.choice(bottoms)
            outfit["bottom"] = self._get_filtered_tag(chosen_cat, whitelist)
            
        # Legwear (70% шанс, если разрешено)
        if legwears and random.random() < 0.7:
            chosen_cat = random.choice(legwears)
            outfit["legwear"] = self._get_filtered_tag(chosen_cat, whitelist)
            
        # Footwear (50% шанс, если разрешено и не пижама)
        if footwears and not outfit["full"] and random.random() < 0.5:
            chosen_cat = random.choice(footwears)
            outfit["footwear"] = self._get_filtered_tag(chosen_cat, whitelist)
            
        return outfit
        
    def _get_filtered_tag(self, category: str, whitelist: dict) -> str:
        """
        Умный маппинг: связывает путь из TOML (например, 02_clothing/full_body/pajamas.txt)
        с гардеробом из YAML (pajamas -> full_body).
        """
        parts = category.split('/')
        if len(parts) < 2:
            return self.library.get_random_tag(category) or ""
            
        folder = parts[-2]  # Например: 'full_body', 'topwear', 'bottomwear'
        file_name = parts[-1].replace('.txt', '') # Например: 'pajamas', 'shirts', 'skirts'
        
        allowed_tags = []
        
        # Ищем подходящие теги в whitelist персонажа
        for style_name, style_data in whitelist.items():
            if not isinstance(style_data, dict):
                continue
                
            # Ситуация 1: Прямое совпадение стиля и файла (например, стиль "pajamas" и файл "pajamas.txt")
            if style_name == file_name and folder in style_data:
                allowed_tags.extend(style_data[folder])
                
            # Ситуация 2: Ищем по папке (например, folder='topwear'). 
            # Собираем все разрешенные топы из всех её стилей (и casual, и sportswear).
            elif folder in style_data:
                allowed_tags.extend(style_data[folder])
                
        # Если мы нашли теги в её личном гардеробе - берем случайный из них
        if allowed_tags:
            return random.choice(allowed_tags)
            
        # Fallback: если в whitelist этого нет (или whitelist пуст), берем случайный из общей библиотеки
        tag = self.library.get_random_tag(category)
        return tag if tag else ""
        
    def build_scene(self, location_id: str) -> Scene:
        scene = Scene()
        scene.location = location_id
        
        rule_key = f"locations.{location_id}"
        rule = self.scene_rules.get(rule_key, {})
        
        soft_constraints = rule.get("soft_constraints", {})
        hard_constraints = rule.get("hard_constraints", {})
        
        # 1. Выбор действия (Action)
        prefers_actions = soft_constraints.get("prefers_actions", ["standing", "sitting"])
        scene.action = random.choice(prefers_actions)
        
        # 2. УМНЫЙ выбор одежды (Outfit)
        allowed_categories = hard_constraints.get("allowed_outfit_categories", [])
        if allowed_categories:
            outfit_parts = self._choose_smart_outfit(allowed_categories)
            scene.outfit_full = outfit_parts["full"]
            scene.outfit_top = outfit_parts["top"]
            scene.outfit_bottom = outfit_parts["bottom"]
            scene.outfit_legwear = outfit_parts["legwear"]
        
        # 3. Выбор реквизита (Props)
        prefers_props = soft_constraints.get("prefers_props", [])
        if prefers_props:
            num_props = random.choice([1, 2])
            scene.props = random.sample(prefers_props, min(num_props, len(prefers_props)))
            
        # 4. Выбор освещения (Lighting)
        prefers_lighting_sources = soft_constraints.get("prefers_lighting_sources", [])
        if prefers_lighting_sources:
            scene.lighting_source = random.choice(prefers_lighting_sources)
            
        prefers_lighting_quality = soft_constraints.get("prefers_lighting_quality", [])
        if prefers_lighting_quality:
            scene.lighting_quality = random.choice(prefers_lighting_quality)
            
        return scene