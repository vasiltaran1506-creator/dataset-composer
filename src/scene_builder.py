"""
Scene Builder v5.1 - С поддержкой наследования правил и Валидатором сцен
"""
import random
from scene import Scene
from prompt_library import PromptLibrary


class SceneBuilder:
    """Строит логически согласованные сцены на основе всех TOML-правил и типов локаций"""
    
    def __init__(self, library: PromptLibrary, scene_rules: dict, character_profile: dict, location_types: dict, generation_weights: dict | None = None):
        self.library = library
        self.scene_rules = scene_rules
        self.location_types = location_types
        self.full_profile = character_profile
        self.generation_weights = generation_weights or {}
        self.force_deficit_closure = False  # Устанавливается из Exporter
        
        # Кэш матрицы совместимости (локация → список разрешенных действий)
        self._compatibility_cache = {}
        
        # Кэшируем списки доступных правил по категориям
        self.available_actions = [k.split('.')[-1] for k in scene_rules.keys() if k.startswith('actions.')]
        self.available_weathers = [k.split('.')[-1] for k in scene_rules.keys() if k.startswith('weather.')]
        self.available_cameras = [k.split('.')[-1] for k in scene_rules.keys() if k.startswith('camera.')]
        
    def _get_outfit_whitelist(self) -> dict:
        """Возвращает whitelist одежды из character-profile.yaml"""
        if 'outfit_whitelist' in self.full_profile:
            return self.full_profile['outfit_whitelist']
        return self.full_profile.get('character', {}).get('outfit_whitelist', {})

    def _merge_rules(self, type_rule: dict, location_rule: dict) -> dict:
        """Объединяет правила типа локации и конкретной локации."""
        merged = {"hard_constraints": {}, "soft_constraints": {}}
        
        type_hard = type_rule.get("hard_constraints", {})
        loc_hard = location_rule.get("hard_constraints", {})
        
        for key in ["excludes_outfit_categories", "excludes_actions", "excludes_props", "excludes_lighting_sources", "excludes_weather"]:
            list1 = type_hard.get(key, [])
            list2 = loc_hard.get(key, [])
            merged["hard_constraints"][key] = list(set(list1 + list2))
            
        for key in ["allowed_outfit_categories", "allowed_actions"]:
            if key in loc_hard:
                merged["hard_constraints"][key] = loc_hard[key]
            elif key in type_hard:
                merged["hard_constraints"][key] = type_hard[key]
                
        type_soft = type_rule.get("soft_constraints", {})
        loc_soft = location_rule.get("soft_constraints", {})
        
        all_soft_keys = set(list(type_soft.keys()) + list(loc_soft.keys()))
        for key in all_soft_keys:
            list1 = type_soft.get(key, [])
            list2 = loc_soft.get(key, [])
            if isinstance(list1, list) and isinstance(list2, list):
                merged["soft_constraints"][key] = list(set(list1 + list2))
            else:
                merged["soft_constraints"][key] = loc_soft.get(key, type_soft.get(key))
                
        if "weather_rules" in location_rule:
            merged["weather_rules"] = location_rule["weather_rules"]
            
        return merged
        
    def _choose_smart_outfit(self, allowed_categories: list, excluded_categories: list) -> dict:
        """Умный выбор одежды"""
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
                if "full_body" in style_data:
                    if any(style_name in cat for cat in allowed_categories):
                        style_compatible = True
                elif "swimsuit" in style_data:
                    if any("swimsuits" in cat for cat in allowed_categories):
                        style_compatible = True
                else:
                    if any("topwear" in cat for cat in allowed_categories) and any("bottomwear" in cat for cat in allowed_categories):
                        style_compatible = True
            else:
                if "full_body" in style_data:
                    if not any(style_name in cat for cat in excluded_categories):
                        style_compatible = True
                elif "swimsuit" in style_data:
                    if not any("swimsuits" in cat for cat in excluded_categories):
                        style_compatible = True
                else:
                    general_excluded = any(any(exc in cat for exc in ["coats", "jackets"]) for cat in excluded_categories)
                    style_excluded = any(style_name in cat for cat in excluded_categories)
                    if not general_excluded and not style_excluded:
                        style_compatible = True
                        
            if style_compatible:
                compatible_styles.append(style_name)
                
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
        """Fallback: случайная сборка одежды"""
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

    def validate_scene(self, scene: Scene, hard_constraints: dict) -> bool:
        """
        Валидатор: проверяет сцену на наличие запрещенных тегов.
        Возвращает True, если сцена идеальна, и False, если её нужно перегенерировать.
        """
        prompt = scene.to_prompt(self.full_profile.get('fixed_traits', []))
        prompt_tags = [tag.strip() for tag in prompt.split(',')]
        
        # 1. Проверяем, не попала ли запрещенная одежда (например, loungewear в Cafe)
        excluded_cats = hard_constraints.get("excludes_outfit_categories", [])
        whitelist = self._get_outfit_whitelist()
        
        for style_name, style_data in whitelist.items():
            is_style_excluded = any(style_name in cat for cat in excluded_cats)
            
            if is_style_excluded:
                all_style_tags = []
                for category_tags in style_data.values():
                    if isinstance(category_tags, list):
                        all_style_tags.extend(category_tags)
                        
                for tag in all_style_tags:
                    if tag in prompt_tags:
                        return False # Найден запрещенный тег!
                        
        # 2. Проверяем, не попало ли запрещенное действие
        excluded_actions = hard_constraints.get("excludes_actions", [])
        if scene.action in excluded_actions:
            return False
            
        # 3. Проверяем, не попал ли запрещенный реквизит
        excluded_props = hard_constraints.get("excludes_props", [])
        for prop in scene.props:
            if prop in excluded_props:
                return False
                
        # 4. Базовая проверка: у персонажа должна быть хоть какая-то одежда
        if not scene.outfit_full and not scene.outfit_top and not scene.outfit_bottom:
            return False
            
        return True # Сцена идеальна!
    
    def get_hard_constraints_for_location(self, location_id: str) -> dict:
        """Публичный метод для получения объединенных hard_constraints (нужен для Экспортера)"""
        location_rule = self.scene_rules.get(f"locations.{location_id}", {})
        type_id = location_rule.get("meta", {}).get("type", "")
        type_rule = self.location_types.get(type_id, {})
        merged = self._merge_rules(type_rule, location_rule)
        return merged.get("hard_constraints", {})
        
    def build_scene(self, location_id: str) -> Scene:
        """ГЛАВНЫЙ МЕТОД: Собирает сцену"""
        scene = Scene()
        scene.location = location_id
        
        location_rule = self.scene_rules.get(f"locations.{location_id}", {})
        type_id = location_rule.get("meta", {}).get("type", "")
        type_rule = self.location_types.get(type_id, {})
        
        merged = self._merge_rules(type_rule, location_rule)
        hard = merged.get("hard_constraints", {})
        soft = merged.get("soft_constraints", {})
        
        # 3. ВЫБОР ДЕЙСТВИЯ (Action) с учетом весов балансировки
        prefers_actions = soft.get("prefers_actions", self.available_actions)
        excludes_actions = hard.get("excludes_actions", [])
        valid_actions = [a for a in prefers_actions if a not in excludes_actions and a in self.available_actions]
        
        if not valid_actions:
            valid_actions = self.available_actions
            
        action_weights = self.generation_weights.get('action')
        if action_weights and valid_actions:
            a_list = [action_weights.get(a, 0.01) for a in valid_actions]
            scene.action = random.choices(valid_actions, weights=a_list, k=1)[0]
        else:
            scene.action = random.choice(valid_actions)
            
        action_rule = self.scene_rules.get(f"actions.{scene.action}", {})
        action_soft = action_rule.get("soft_constraints", {})
        action_hard = action_rule.get("hard_constraints", {})
        
        # 4. ВЫБОР ПОГОДЫ И КАМЕРЫ с учетом весов балансировки
        weather_weights = self.generation_weights.get('weather')
        if weather_weights:
            w_list = [weather_weights.get(w, 0.01) for w in self.available_weathers]
            scene.weather = random.choices(self.available_weathers, weights=w_list, k=1)[0]
        else:
            scene.weather = random.choice(self.available_weathers)
            
        weather_rule = self.scene_rules.get(f"weather.{scene.weather}", {})
        weather_soft = weather_rule.get("soft_constraints", {})
        
        camera_weights = self.generation_weights.get('camera')
        if camera_weights:
            c_list = [camera_weights.get(c, 0.01) for c in self.available_cameras]
            scene.camera = random.choices(self.available_cameras, weights=c_list, k=1)[0]
        else:
            scene.camera = random.choice(self.available_cameras)
        
        allowed_categories = hard.get("allowed_outfit_categories", [])
        excluded_categories = hard.get("excludes_outfit_categories", [])
        
        if allowed_categories or excluded_categories:
            outfit_parts = self._choose_smart_outfit(allowed_categories, excluded_categories)
            scene.outfit_full = outfit_parts["full"]
            scene.outfit_top = outfit_parts["top"]
            scene.outfit_bottom = outfit_parts["bottom"]
            scene.outfit_legwear = outfit_parts["legwear"]
            scene.outfit_footwear = outfit_parts["footwear"]
            
        prefers_expressions = action_soft.get("prefers_expressions", soft.get("prefers_expressions", []))
        if prefers_expressions:
            scene.expression = random.choice(prefers_expressions)
            
        props = []
        
        for cat in action_hard.get("requires_prop_categories", []):
            tag = self.library.get_random_tag(cat)
            if tag:
                props.append(tag)
                
        if action_soft.get("prefers_props") and random.random() < 0.7:
            props.append(random.choice(action_soft["prefers_props"]))
            
        if soft.get("prefers_props") and random.random() < 0.5:
            props.append(random.choice(soft["prefers_props"]))
            
        excludes_props = hard.get("excludes_props", [])
        scene.props = [p for p in props if p not in excludes_props]
        
        lighting_sources = (
            weather_soft.get("prefers_lighting_sources", []) or
            action_soft.get("prefers_lighting_sources", []) or
            soft.get("prefers_lighting_sources", [])
        )
        excludes_lighting = hard.get("excludes_lighting_sources", [])
        valid_sources = [s for s in lighting_sources if s not in excludes_lighting]
        if valid_sources:
            scene.lighting_source = random.choice(valid_sources)
            
        lighting_quality = (
            weather_soft.get("prefers_lighting_quality", []) or
            action_soft.get("prefers_lighting_quality", []) or
            soft.get("prefers_lighting_quality", [])
        )
        if lighting_quality:
            scene.lighting_quality = random.choice(lighting_quality)
            
        prefers_effects = weather_soft.get("prefers_effects", [])
        if prefers_effects and random.random() < 0.6:
            scene.effects.append(random.choice(prefers_effects))
            
        weather_rules = merged.get("weather_rules", {})
        weather_key = f"if_weather_is_{scene.weather}"
        if weather_key in weather_rules:
            weather_specific_rules = weather_rules[weather_key]
            if "prefers_props" in weather_specific_rules:
                for prop in weather_specific_rules["prefers_props"]:
                    if random.random() < 0.8:
                        scene.props.append(prop)
            if "prefers_lighting_quality" in weather_specific_rules:
                scene.lighting_quality = random.choice(weather_specific_rules["prefers_lighting_quality"])
                
        return scene