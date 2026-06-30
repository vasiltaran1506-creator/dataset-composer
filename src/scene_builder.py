"""
Scene Builder v4 - Полная интеграция всех правил (Locations, Actions, Weather, Camera)
"""
import random
from scene import Scene
from prompt_library import PromptLibrary


class SceneBuilder:
    """Строит логически согласованные сцены на основе всех TOML-правил"""
    
    def __init__(self, library: PromptLibrary, scene_rules: dict, character_profile: dict):
        self.library = library
        self.scene_rules = scene_rules
        self.full_profile = character_profile
        
        # Кэшируем списки доступных правил по категориям
        self.available_actions = [k.split('.')[-1] for k in scene_rules.keys() if k.startswith('actions.')]
        self.available_weathers = [k.split('.')[-1] for k in scene_rules.keys() if k.startswith('weather.')]
        self.available_cameras = [k.split('.')[-1] for k in scene_rules.keys() if k.startswith('camera.')]
        
    def _get_outfit_whitelist(self) -> dict:
        """Возвращает whitelist одежды из character-profile.yaml"""
        if 'outfit_whitelist' in self.full_profile:
            return self.full_profile['outfit_whitelist']
        return self.full_profile.get('character', {}).get('outfit_whitelist', {})
        
    def _choose_smart_outfit(self, allowed_categories: list, excluded_categories: list) -> dict:
        """
        Умный выбор одежды v6: Точная проверка совместимости стилей.
        """
        outfit = {"full": "", "top": "", "bottom": "", "legwear": "", "footwear": ""}
        whitelist = self._get_outfit_whitelist()
        
        if not whitelist:
            return self._choose_random_outfit(allowed_categories, excluded_categories)
            
        compatible_styles = []
        
        for style_name, style_data in whitelist.items():
            if not isinstance(style_data, dict):
                continue
                
            style_compatible = False
            
            if allowed_categories:
                # РЕЖИМ 1: Whitelist - проверяем ТОЧНОЕ соответствие
                if "full_body" in style_data:
                    # Для full_body стилей (pajamas, loungewear) проверяем, что ИМЕННО этот стиль разрешен
                    # style_name = "pajamas", "loungewear" и т.д.
                    if any(style_name in cat for cat in allowed_categories):
                        style_compatible = True
                elif "swimsuit" in style_data:
                    # Для swimsuit проверяем swimsuits
                    if any("swimsuits" in cat for cat in allowed_categories):
                        style_compatible = True
                else:
                    # Для top_bottom комплектов проверяем наличие topwear И bottomwear
                    if any("topwear" in cat for cat in allowed_categories) and any("bottomwear" in cat for cat in allowed_categories):
                        style_compatible = True
            else:
                # РЕЖИМ 2: Blacklist - проверяем, не запрещен ли стиль
                if "full_body" in style_data:
                    # Проверяем, не запрещен ли именно этот стиль
                    if not any(style_name in cat for cat in excluded_categories):
                        style_compatible = True
                elif "swimsuit" in style_data:
                    if not any("swimsuits" in cat for cat in excluded_categories):
                        style_compatible = True
                else:
                    # Для top_bottom проверяем, не запрещены ли topwear или bottomwear
                    if not any(any(exc in cat for exc in ["coats", "jackets"]) for cat in excluded_categories):
                        style_compatible = True
                        
            if style_compatible:
                compatible_styles.append(style_name)
                
        # Если нет совместимых стилей, берем все из whitelist
        if not compatible_styles:
            compatible_styles = list(whitelist.keys())
            
        if not compatible_styles:
            return self._choose_random_outfit(allowed_categories, excluded_categories)
            
        chosen_style = random.choice(compatible_styles)
        style_data = whitelist[chosen_style]
        
        if "full_body" in style_data:
            outfit["full"] = random.choice(style_data["full_body"])
        elif "swimsuit" in style_data:
            outfit["full"] = random.choice(style_data["swimsuit"])
        else:
            if "topwear" in style_data:
                outfit["top"] = random.choice(style_data["topwear"])
            if "bottomwear" in style_data:
                outfit["bottom"] = random.choice(style_data["bottomwear"])
                
        if "legwear" in style_data and random.random() < 0.7:
            outfit["legwear"] = random.choice(style_data["legwear"])
        if "footwear" in style_data and random.random() < 0.5:
            outfit["footwear"] = random.choice(style_data["footwear"])
                
        return outfit
        
    def _choose_random_outfit(self, allowed_categories: list, excluded_categories: list) -> dict:
        """Fallback: случайная сборка одежды из библиотеки"""
        outfit = {"full": "", "top": "", "bottom": "", "legwear": "", "footwear": ""}
        
        if allowed_categories:
            pool = allowed_categories
        else:
            all_clothing_cats = [k for k in self.library.categories.keys() if k.startswith("02_clothing/")]
            pool = [c for c in all_clothing_cats if c not in excluded_categories]
            
        if not pool:
            return outfit
            
        full_body_cats = [c for c in pool if "full_body" in c]
        top_cats = [c for c in pool if "topwear" in c]
        bottom_cats = [c for c in pool if "bottomwear" in c]
        legwear_cats = [c for c in pool if "legwear" in c]
        footwear_cats = [c for c in pool if "footwear" in c]
        
        if full_body_cats and random.random() < 0.4:
            outfit["full"] = self.library.get_random_tag(random.choice(full_body_cats)) or ""
            return outfit
            
        if top_cats:
            outfit["top"] = self.library.get_random_tag(random.choice(top_cats)) or ""
        if bottom_cats:
            outfit["bottom"] = self.library.get_random_tag(random.choice(bottom_cats)) or ""
        if legwear_cats and random.random() < 0.7:
            outfit["legwear"] = self.library.get_random_tag(random.choice(legwear_cats)) or ""
        if footwear_cats and not outfit["full"] and random.random() < 0.5:
            outfit["footwear"] = self.library.get_random_tag(random.choice(footwear_cats)) or ""
            
        return outfit
        
    def build_scene(self, location_id: str) -> Scene:
        """
        ГЛАВНЫЙ МЕТОД: Собирает сцену, применяя все правила
        """
        scene = Scene()
        scene.location = location_id
        
        # Загружаем правила для выбранной локации
        location_rule = self.scene_rules.get(f"locations.{location_id}", {})
        location_soft = location_rule.get("soft_constraints", {})
        location_hard = location_rule.get("hard_constraints", {})
        
        # 1. ВЫБОР ДЕЙСТВИЯ (Action)
        # Берем из prefers_actions локации, если есть
        prefers_actions = location_soft.get("prefers_actions", self.available_actions)
        scene.action = random.choice(prefers_actions)
        
        # Загружаем правила для выбранного действия
        action_rule = self.scene_rules.get(f"actions.{scene.action}", {})
        action_soft = action_rule.get("soft_constraints", {})
        action_hard = action_rule.get("hard_constraints", {})
        
        # 2. ВЫБОР ПОГОДЫ (Weather) - случайно из доступных
        scene.weather = random.choice(self.available_weathers)
        weather_rule = self.scene_rules.get(f"weather.{scene.weather}", {})
        weather_soft = weather_rule.get("soft_constraints", {})
        
        # 3. ВЫБОР КАМЕРЫ (Camera) - случайно из доступных
        scene.camera = random.choice(self.available_cameras)
        camera_rule = self.scene_rules.get(f"camera.{scene.camera}", {})
        camera_soft = camera_rule.get("soft_constraints", {})
        
        # 4. ВЫБОР ОДЕЖДЫ (Outfit)
        allowed_categories = location_hard.get("allowed_outfit_categories", [])
        excluded_categories = location_hard.get("excludes_outfit_categories", [])
        
        if allowed_categories or excluded_categories:
            outfit_parts = self._choose_smart_outfit(allowed_categories, excluded_categories)
            scene.outfit_full = outfit_parts["full"]
            scene.outfit_top = outfit_parts["top"]
            scene.outfit_bottom = outfit_parts["bottom"]
            scene.outfit_legwear = outfit_parts["legwear"]
            scene.outfit_footwear = outfit_parts["footwear"]
            
        # 5. ВЫБОР ВЫРАЖЕНИЯ ЛИЦА (Expression)
        # Приоритет: action > location > случайный
        prefers_expressions = action_soft.get("prefers_expressions", location_soft.get("prefers_expressions", []))
        if prefers_expressions:
            scene.expression = random.choice(prefers_expressions)
            
        # 6. ВЫБОР РЕКВИЗИТА (Props)
        props = []
        
        # 6a. Обязательный реквизит из action (requires_prop_categories)
        requires_prop_cats = action_hard.get("requires_prop_categories", [])
        for cat in requires_prop_cats:
            tag = self.library.get_random_tag(cat)
            if tag:
                props.append(tag)
                
        # 6b. Предпочитаемый реквизит из action
        prefers_props_action = action_soft.get("prefers_props", [])
        if prefers_props_action and random.random() < 0.7:
            props.append(random.choice(prefers_props_action))
            
        # 6c. Предпочитаемый реквизит из location
        prefers_props_location = location_soft.get("prefers_props", [])
        if prefers_props_location and random.random() < 0.5:
            props.append(random.choice(prefers_props_location))
            
        scene.props = props
        
        # 7. ВЫБОР ОСВЕЩЕНИЯ (Lighting)
        # Приоритет: weather > action > location
        lighting_sources = (
            weather_soft.get("prefers_lighting_sources", []) or
            action_soft.get("prefers_lighting_sources", []) or
            location_soft.get("prefers_lighting_sources", [])
        )
        if lighting_sources:
            scene.lighting_source = random.choice(lighting_sources)
            
        lighting_quality = (
            weather_soft.get("prefers_lighting_quality", []) or
            action_soft.get("prefers_lighting_quality", []) or
            location_soft.get("prefers_lighting_quality", [])
        )
        if lighting_quality:
            scene.lighting_quality = random.choice(lighting_quality)
            
        # 8. ЭФФЕКТЫ (Effects) - из weather
        prefers_effects = weather_soft.get("prefers_effects", [])
        if prefers_effects and random.random() < 0.6:
            scene.effects.append(random.choice(prefers_effects))
            
        return scene