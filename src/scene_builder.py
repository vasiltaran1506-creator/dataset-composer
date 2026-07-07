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
        
    def _choose_smart_outfit(self, allowed_categories: list, excluded_categories: list,
                             avoid_categories: list | None = None, preferred_categories: list | None = None) -> dict:
        """Умный выбор одежды с поддержкой мягких банов (avoid) и приоритетов (preferred)"""
        outfit = {"full": "", "top": "", "bottom": "", "legwear": "", "footwear": ""}
        whitelist = self._get_outfit_whitelist()
        avoid_categories = avoid_categories or []
        preferred_categories = preferred_categories or []
        
        if not whitelist:
            return self._choose_random_outfit(allowed_categories, excluded_categories)
        
        # Собираем все доступные варианты одежды из всех стилей
        all_outfit_options = []
        
        for style_name, style_data in whitelist.items():
            if not isinstance(style_data, dict):
                continue
            
            if "full_body" in style_data and isinstance(style_data["full_body"], list):
                all_outfit_options.append({
                    "type": "full_body",
                    "tags": style_data["full_body"],
                    "style": style_name
                })
            
            if "swimsuit" in style_data and isinstance(style_data["swimsuit"], list):
                all_outfit_options.append({
                    "type": "swimsuit",
                    "tags": style_data["swimsuit"],
                    "style": style_name
                })
            
            has_top = "topwear" in style_data and isinstance(style_data["topwear"], list)
            has_bottom = "bottomwear" in style_data and isinstance(style_data["bottomwear"], list)
            if has_top and has_bottom:
                all_outfit_options.append({
                    "type": "topwear_bottomwear",
                    "top_tags": style_data["topwear"],
                    "bottom_tags": style_data["bottomwear"],
                    "style": style_name
                })
        
        valid_options = []
        option_weights = []
        
        for option in all_outfit_options:
            option_type = option["type"]
            is_allowed = False
            
            if allowed_categories:
                if option_type == "full_body":
                    is_allowed = any("full_body" in cat for cat in allowed_categories)
                elif option_type == "swimsuit":
                    is_allowed = any("swimsuit" in cat or "swimsuits" in cat for cat in allowed_categories)
                elif option_type == "topwear_bottomwear":
                    is_allowed = (any("topwear" in cat for cat in allowed_categories) and
                                 any("bottomwear" in cat for cat in allowed_categories))
            else:
                is_allowed = True
                if option_type == "full_body":
                    if any("full_body" in cat for cat in excluded_categories):
                        is_allowed = False
                elif option_type == "swimsuit":
                    if any("swimsuit" in cat or "swimsuits" in cat for cat in excluded_categories):
                        is_allowed = False
                elif option_type == "topwear_bottomwear":
                    if (any("topwear" in cat for cat in excluded_categories) or
                        any("bottomwear" in cat for cat in excluded_categories)):
                        is_allowed = False
            
            if not is_allowed:
                continue
            
            weight = 1.0
            if option_type == "full_body" and any("full_body" in cat for cat in preferred_categories):
                weight *= 5.0
            elif option_type == "swimsuit" and any("swimsuit" in cat or "swimsuits" in cat for cat in preferred_categories):
                weight *= 5.0
            elif option_type == "topwear_bottomwear":
                if any("topwear" in cat for cat in preferred_categories):
                    weight *= 3.0
                if any("bottomwear" in cat for cat in preferred_categories):
                    weight *= 3.0
            
            if option_type == "full_body" and any("full_body" in cat for cat in avoid_categories):
                weight *= 0.1
            elif option_type == "swimsuit" and any("swimsuit" in cat or "swimsuits" in cat for cat in avoid_categories):
                weight *= 0.1
            elif option_type == "topwear_bottomwear":
                if any("topwear" in cat for cat in avoid_categories):
                    weight *= 0.3
                if any("bottomwear" in cat for cat in avoid_categories):
                    weight *= 0.3
            
            valid_options.append(option)
            option_weights.append(weight)
        
        if not valid_options:
            valid_options = all_outfit_options
            option_weights = [1.0 for _ in valid_options]
        
        if not valid_options:
            return self._choose_random_outfit(allowed_categories, excluded_categories)
        
        chosen_option = random.choices(valid_options, weights=option_weights, k=1)[0]
        
        if chosen_option["type"] == "full_body":
            outfit["full"] = random.choice(chosen_option["tags"])
        elif chosen_option["type"] == "swimsuit":
            outfit["full"] = random.choice(chosen_option["tags"])
        elif chosen_option["type"] == "topwear_bottomwear":
            outfit["top"] = random.choice(chosen_option["top_tags"])
            outfit["bottom"] = random.choice(chosen_option["bottom_tags"])
            
            style_data = whitelist[chosen_option["style"]]
            if "legwear" in style_data and isinstance(style_data["legwear"], list) and random.random() < 0.7:
                outfit["legwear"] = random.choice(style_data["legwear"])
            if "footwear" in style_data and isinstance(style_data["footwear"], list) and random.random() < 0.5:
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
        
        # 1. Проверяем, не попала ли запрещенная одежда
        excluded_cats = hard_constraints.get("excludes_outfit_categories", [])
        whitelist = self._get_outfit_whitelist()
        
        # Собираем все теги запрещённых типов одежды
        excluded_tags = set()
        
        for style_name, style_data in whitelist.items():
            if not isinstance(style_data, dict):
                continue
            
            # Проверяем full_body
            if any("full_body" in cat for cat in excluded_cats):
                if "full_body" in style_data and isinstance(style_data["full_body"], list):
                    excluded_tags.update(style_data["full_body"])
            
            # Проверяем swimsuit
            if any("swimsuit" in cat or "swimsuits" in cat for cat in excluded_cats):
                if "swimsuit" in style_data and isinstance(style_data["swimsuit"], list):
                    excluded_tags.update(style_data["swimsuit"])
            
            # Проверяем topwear
            if any("topwear" in cat for cat in excluded_cats):
                if "topwear" in style_data and isinstance(style_data["topwear"], list):
                    excluded_tags.update(style_data["topwear"])
            
            # Проверяем bottomwear
            if any("bottomwear" in cat for cat in excluded_cats):
                if "bottomwear" in style_data and isinstance(style_data["bottomwear"], list):
                    excluded_tags.update(style_data["bottomwear"])
        
        # Проверяем, не попал ли запрещённый тег в промпт
        for tag in excluded_tags:
            if tag in prompt_tags:
                return False  # Найден запрещенный тег!!
                        
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
        
        # ═══════════════════════════════════════════════════
        # 5. КРОСС-ВАЛИДАЦИЯ: проверяем совместимость сущностей
        # ═══════════════════════════════════════════════════
        
        # 5a. Проверяем, не запрещено ли действие в этой локации (action → location)
        if scene.action:
            action_rule = self.scene_rules.get(f"actions.{scene.action}", {})
            action_hard = action_rule.get("hard_constraints", {})
            excluded_locations = action_hard.get("excludes_locations", [])
            if scene.location in excluded_locations:
                return False  # Действие запрещено в этой локации
        
        # 5b. Проверяем, не запрещена ли погода для этого действия (action → weather)
        if scene.action and scene.weather:
            action_rule = self.scene_rules.get(f"actions.{scene.action}", {})
            action_hard = action_rule.get("hard_constraints", {})
            excluded_weather = action_hard.get("excludes_weather", [])
            if scene.weather in excluded_weather:
                return False  # Погода запрещена для этого действия
        
        # 5c. Проверяем, не запрещено ли действие в эту погоду (weather → action)
        if scene.weather and scene.action:
            weather_rule = self.scene_rules.get(f"weather.{scene.weather}", {})
            weather_hard = weather_rule.get("hard_constraints", {})
            excluded_actions = weather_hard.get("excludes_actions", [])
            if scene.action in excluded_actions:
                return False  # Действие запрещено в эту погоду
        
        # 5d. Проверяем, не запрещена ли локация для этой погоды (weather → location)
        if scene.weather and scene.location:
            weather_rule = self.scene_rules.get(f"weather.{scene.weather}", {})
            weather_hard = weather_rule.get("hard_constraints", {})
            excluded_locations = weather_hard.get("excludes_locations", [])
            if scene.location in excluded_locations:
                return False  # Локация запрещена для этой погоды

        # 5e. Проверяем, не запрещена ли камера для этой позы (camera → pose)
        if getattr(scene, 'camera', None) and getattr(scene, 'pose', None):
            camera_rule = self.scene_rules.get(f"camera.{getattr(scene, 'camera')}", {})
            camera_hard = camera_rule.get("hard_constraints", {})
            excluded_poses = camera_hard.get("excludes_poses", [])
            if getattr(scene, 'pose', None) in excluded_poses:
                return False  # Поза запрещена для этой камеры
        
        # 5f. Проверяем, не запрещена ли погода для этой локации (location → weather)
        if scene.weather and scene.location:
            # Это уже проверено через merged hard_constraints, но проверим ещё раз для надёжности
            # Получаем объединённые hard_constraints для локации
            loc_hard = self.get_hard_constraints_for_location(scene.location)
            if scene.weather in loc_hard.get("excludes_weather", []):
                return False
            
        # ═══════════════════════════════════════════════════
        # 6. АВТОЗАЩИТА PROPS: кровати только в bedroom
        # ═══════════════════════════════════════════════════
        bed_tags = {"bed", "single bed", "double bed", "bunk bed", "canopy bed", 
                    "mattress", "pillow", "blanket", "duvet", "sheet", "nightstand"}
        bedroom_only_locations = {"bedroom"}  # Только эти локации могут иметь кровати
        
        if scene.location not in bedroom_only_locations:
            for prop in scene.props:
                if prop.lower() in bed_tags:
                    return False  # Кровать в публичном месте!
        
        # 7. АВТОЗАЩИТА: абсурдное освещение в indoor
        indoor_forbidden_lighting = {"headlights", "bioluminescence", "fireplace light", 
                                      "firelight", "strobe light", "concert lights", 
                                      "stage lights", "laser light", "store lights"}
        location_type = self._get_location_type(scene.location)
        if location_type.startswith("indoor"):
            if scene.lighting_source.lower() in indoor_forbidden_lighting:
                return False
            
        # ═══════════════════════════════════════════════════
        # 8. АВТОЗАЩИТА: экстремальная погода + активные действия
        # ═══════════════════════════════════════════════════
        extreme_weather = {"storm", "heavy rain", "blizzard", "snowstorm", "thunderstorm"}
        outdoor_active_actions = {"dancing", "exercising", "running", "jogging", "shopping"}
        
        if scene.weather in extreme_weather and scene.action in outdoor_active_actions:
            # Активное действие в экстремальную погоду — только если это не street
            if scene.location != "street":
                return False

        return True # Сцена идеальна!
    
    def get_hard_constraints_for_location(self, location_id: str) -> dict:
        """Публичный метод для получения объединенных hard_constraints (нужен для Экспортера)"""
        location_rule = self.scene_rules.get(f"locations.{location_id}", {})
        type_id = location_rule.get("meta", {}).get("type", "")
        type_rule = self.location_types.get(type_id, {})
        merged = self._merge_rules(type_rule, location_rule)
        return merged.get("hard_constraints", {})
    
    def _get_location_type(self, location_id: str) -> str:
        """Возвращает тип локации (например, 'indoor_private', 'outdoor_urban')"""
        loc_rule = self.scene_rules.get(f"locations.{location_id}", {})
        return loc_rule.get("meta", {}).get("type", "")

    def _get_action_compatibility(self, action_id: str) -> dict:
        """
        Парсит TOML-правила действия и возвращает словарь ограничений совместимости.
        Использует кэш для производительности.
        """
        if action_id in self._compatibility_cache:
            return self._compatibility_cache[action_id]
        
        action_rule = self.scene_rules.get(f"actions.{action_id}", {})
        hard = action_rule.get("hard_constraints", {})
        soft = action_rule.get("soft_constraints", {})
        
        result = {
            "preferred": hard.get("preferred_locations", []),         # Жёсткий whitelist (cooking → kitchen)
            "excluded": hard.get("excludes_locations", []),           # Жёсткий blacklist (exercising → library)
            "allowed_types": hard.get("allowed_location_types", []),  # Фильтр по типам (sleeping → indoor_private)
            "excluded_types": hard.get("excludes_location_types", []),# Чёрный список типов
            "preferred_soft": soft.get("prefers_locations", []),      # Мягкие предпочтения (reading → library, cafe)
        }
        
        self._compatibility_cache[action_id] = result
        return result

    def get_compatible_locations(self, action_id: str, aggressive: bool = False) -> list:
        """
        Возвращает список локаций, совместимых с данным действием.
        
        В Natural Mode (aggressive=False):
            - Если есть hard.preferred_locations → только они
            - Иначе если есть soft.prefers_locations → только они
            - Иначе → все доступные локации
            - Во всех случаях применяются жёсткие фильтры excludes и allowed_types
        
        В Aggressive Mode (aggressive=True):
            - Берём ВСЕ локации, которые проходят жёсткие фильтры
            - Игнорируем preferred/prefers — главное, чтобы не было запретов
        """
        compat = self._get_action_compatibility(action_id)
        
        all_locations = [
            k.split('.')[-1] 
            for k in self.scene_rules.keys() 
            if k.startswith('locations.')
        ]
        
        # Вспомогательная функция: проверка через жёсткие ограничения
        def passes_hard_filters(loc):
            if loc in compat['excluded']:
                return False
            loc_type = self._get_location_type(loc)
            if compat['allowed_types'] and loc_type not in compat['allowed_types']:
                return False
            if loc_type in compat['excluded_types']:
                return False
            return True
        
        if aggressive:
            # Aggressive Mode: всё, что не запрещено
            return [loc for loc in all_locations if passes_hard_filters(loc)]
        else:
            # Natural Mode: предпочитаем preferred/prefers, применяя жёсткие фильтры
            if compat['preferred']:
                candidates = compat['preferred']
            elif compat['preferred_soft']:
                candidates = compat['preferred_soft']
            else:
                candidates = all_locations
            
            return [loc for loc in candidates 
                    if loc in all_locations and passes_hard_filters(loc)]    
        
    def build_scene(self, location_id: str, forced_action: str | None = None) -> Scene:
        """
        ГЛАВНЫЙ МЕТОД: Собирает сцену, применяя все правила и наследование.
        
        Args:
            location_id: ID локации
            forced_action: Если передано и совместимо с локацией — используется вместо случайного выбора
                          (нужно для инверсии приоритетов: Action → Location)
        """
        scene = Scene()
        scene.location = location_id
        
        # 1. Загружаем правила локации и её типа
        location_rule = self.scene_rules.get(f"locations.{location_id}", {})
        type_id = location_rule.get("meta", {}).get("type", "")
        type_rule = self.location_types.get(type_id, {})
        
        # 2. МЕРЖИМ ПРАВИЛА!
        merged = self._merge_rules(type_rule, location_rule)
        hard = merged.get("hard_constraints", {})
        soft = merged.get("soft_constraints", {})
        
        # 3. ВЫБОР ДЕЙСТВИЯ (с поддержкой forced_action)
        excludes_actions = hard.get("excludes_actions", [])
        allowed_actions = hard.get("allowed_actions", [])  # НОВОЕ: жёсткий whitelist
        avoid_actions = soft.get("avoid_actions", [])  # НОВОЕ: мягкий бан
        
        # Определяем базовый пул действий
        if allowed_actions:
            # Если есть allowed_actions, используем ТОЛЬКО их
            base_actions = [a for a in allowed_actions if a in self.available_actions]
        else:
            # Иначе берём все доступные
            base_actions = self.available_actions
        
        # Фильтруем через excludes_actions (жёсткий бан)
        valid_actions = [a for a in base_actions if a not in excludes_actions]
        
        # Если после фильтрации ничего не осталось, fallback на все доступные
        if not valid_actions:
            valid_actions = self.available_actions
        
        if forced_action and self.force_deficit_closure:
            # ⚡ AGGRESSIVE MODE: проверяем только через excludes_actions
            if forced_action not in excludes_actions and forced_action in self.available_actions:
                scene.action = forced_action
            else:
                # Fallback: если forced_action запрещён в этой локации
                print(f"⚠️ FALLBACK: '{forced_action}' incompatible with '{location_id}'. "
                      f"Reason: {'in excludes_actions' if forced_action in excludes_actions else 'not in available_actions'}")
                scene.action = random.choice(valid_actions)
        else:
            # 🌿 NATURAL MODE: учитываем prefers_actions и avoid_actions
            
            # Если передан forced_action И он в valid_actions
            if forced_action and forced_action in valid_actions:
                scene.action = forced_action
            else:
                # Применяем prefers_actions (мягкие предпочтения)
                prefers_actions = soft.get("prefers_actions", [])
                if prefers_actions:
                    # Фильтруем prefers через valid_actions
                    preferred_valid = [a for a in prefers_actions if a in valid_actions]
                    if preferred_valid:
                        valid_actions = preferred_valid
                
                # Применяем веса и avoid_actions
                action_weights = self.generation_weights.get('action', {})
                
                if action_weights or avoid_actions:
                    # Рассчитываем веса для каждого действия
                    weights = []
                    for action in valid_actions:
                        # Базовый вес из generation_weights
                        base_weight = action_weights.get(action, 1.0)
                        
                        # Если действие в avoid_actions, уменьшаем вес в 10 раз
                        if action in avoid_actions:
                            base_weight *= 0.1
                        
                        weights.append(base_weight)
                    
                    scene.action = random.choices(valid_actions, weights=weights, k=1)[0]
                else:
                    scene.action = random.choice(valid_actions)
            
        action_rule = self.scene_rules.get(f"actions.{scene.action}", {})
        action_soft = action_rule.get("soft_constraints", {})
        action_hard = action_rule.get("hard_constraints", {})
        
        # 4. ВЫБОР ПОГОДЫ И КАМЕРЫ с учетом весов балансировки и ограничений
        excludes_weather = hard.get("excludes_weather", [])
        avoid_weather = soft.get("avoid_weather", [])

        # 🛡️ АВТОЗАЩИТА: indoor локации автоматически запрещают любую погоду
        location_type = location_rule.get("meta", {}).get("type", "")
        if location_type.startswith("indoor") or type_id.startswith("indoor"):
            auto_exclude_weather = ["sunny", "clear_sky", "rain", "snow", "fog", "storm", 
                                    "cloudy", "overcast", "light rain", "heavy rain", "blizzard"]
            excludes_weather = list(set(excludes_weather + auto_exclude_weather))
        
        # 👇 КРОСС-ВАЛИДАЦИЯ: учитываем excludes_weather из action.toml
        excludes_weather_from_action = action_hard.get("excludes_weather", [])
        all_excludes_weather = list(set(excludes_weather + excludes_weather_from_action))
        
        # 🛑 ИСПРАВЛЕНИЕ: Инициализация переменных погоды (защита от UnboundLocalError)
        weather_rule = {}
        weather_hard = {}
        weather_soft = {}
        
        # Фильтруем доступные погоды через excludes_weather (жёсткий бан)
        valid_weathers = [w for w in self.available_weathers if w not in all_excludes_weather]
        
        # 🛑 ИСПРАВЛЕНИЕ: Если все погоды запрещены (indoor), погода должна быть пустой!
        if not valid_weathers:
            scene.weather = ""
        else:
            weather_weights = self.generation_weights.get('weather', {})
            
            if weather_weights or avoid_weather:
                weights = []
                for weather in valid_weathers:
                    base_weight = weather_weights.get(weather, 1.0)
                    if weather in avoid_weather:
                        base_weight *= 0.1
                    weights.append(base_weight)
                scene.weather = random.choices(valid_weathers, weights=weights, k=1)[0]
            else:
                scene.weather = random.choice(valid_weathers)
                
            # КРОСС-ВАЛИДАЦИЯ: проверяем, не запрещено ли действие в эту погоду
            weather_rule = self.scene_rules.get(f"weather.{scene.weather}", {})
            weather_hard = weather_rule.get("hard_constraints", {})
            weather_soft = weather_rule.get("soft_constraints", {})
            
            excluded_actions_in_weather = weather_hard.get("excludes_actions", [])
            if scene.action in excluded_actions_in_weather:
                for retry in range(5):
                    candidate_weather = random.choice(valid_weathers)
                    candidate_rule = self.scene_rules.get(f"weather.{candidate_weather}", {})
                    candidate_hard = candidate_rule.get("hard_constraints", {})
                    candidate_excluded_actions = candidate_hard.get("excludes_actions", [])
                    
                    if scene.action not in candidate_excluded_actions:
                        scene.weather = candidate_weather
                        weather_rule = candidate_rule
                        weather_hard = candidate_hard
                        weather_soft = candidate_rule.get("soft_constraints", {})
                        break
        
        camera_weights = self.generation_weights.get('camera')
        if camera_weights:
            c_list = [camera_weights.get(c, 0.01) for c in self.available_cameras]
            scene.camera = random.choices(self.available_cameras, weights=c_list, k=1)[0]
        else:
            scene.camera = random.choice(self.available_cameras)

        # 🛡️ АВТОЗАЩИТА: Специфичные действия переопределяют одежду
        action_outfit_overrides = {
            # Плавание и купание — только купальник
            'swimming': {'allowed': ['swimsuit'], 'excluded': ['full_body', 'topwear', 'bottomwear', 'legwear', 'footwear']},
            'bathing': {'allowed': ['swimsuit'], 'excluded': ['full_body', 'topwear', 'bottomwear', 'legwear', 'footwear']},
            'sunbathing': {'allowed': ['swimsuit'], 'excluded': ['full_body', 'topwear', 'bottomwear', 'legwear', 'footwear']},
            # Сон — только пижамы/ночные рубашки
            'sleeping': {'allowed': ['full_body'], 'excluded': ['swimsuit']},
            # Готовка — без купальников и пижам
            'cooking': {'excluded': ['swimsuit', 'full_body']},
        }
        
        allowed_categories = hard.get("allowed_outfit_categories", [])
        excluded_categories = hard.get("excludes_outfit_categories", [])
        
        if scene.action in action_outfit_overrides:
            override = action_outfit_overrides[scene.action]
            if 'allowed' in override:
                allowed_categories = override['allowed']
            if 'excluded' in override:
                excluded_categories = list(set(excluded_categories + override['excluded']))
        avoid_categories = soft.get("avoid_outfit_categories", [])
        preferred_categories = soft.get("preferred_outfit_categories", [])
        
        # Одежда должна выбираться ВСЕГДА, даже если нет жестких ограничений
        outfit_parts = self._choose_smart_outfit(
            allowed_categories, 
            excluded_categories,
            avoid_categories,
            preferred_categories
        )
        scene.outfit_full = outfit_parts["full"]
        scene.outfit_top = outfit_parts["top"]
        scene.outfit_bottom = outfit_parts["bottom"]
        scene.outfit_legwear = outfit_parts["legwear"]
        scene.outfit_footwear = outfit_parts["footwear"]
            
        prefers_expressions = action_soft.get("prefers_expressions", soft.get("prefers_expressions", []))
        if prefers_expressions:
            scene.expression = random.choice(prefers_expressions)
            
        props = []
        
        props = []
        
        # 1. Required Props из Action (100% попадание)
        required_props_action = action_hard.get("required_props", [])
        if required_props_action:
            props.extend(required_props_action)
        
        # 2. Required Props Pool из Action (случайный выбор N из пула)
        required_props_pool_action = action_hard.get("required_props_pool", [])
        required_props_count_action = action_hard.get("required_props_count", 0)
        if required_props_pool_action and required_props_count_action > 0:
            props.extend(random.sample(required_props_pool_action, 
                                      min(required_props_count_action, len(required_props_pool_action))))
        
        # 3. Required Props из Location (100% попадание)
        required_props_location = hard.get("required_props", [])
        if required_props_location:
            props.extend(required_props_location)
        
        # 4. Required Props Pool из Location (случайный выбор N из пула)
        required_props_pool_location = hard.get("required_props_pool", [])
        required_props_count_location = hard.get("required_props_count", 0)
        if required_props_pool_location and required_props_count_location > 0:
            props.extend(random.sample(required_props_pool_location,
                                      min(required_props_count_location, len(required_props_pool_location))))
        
        # 5. Prefers Props из Action (70% шанс добавить один случайный)
        if action_soft.get("prefers_props") and random.random() < 0.7:
            props.append(random.choice(action_soft["prefers_props"]))
            
        # 6. Prefers Props из Location (50% шанс добавить один случайный)
        if soft.get("prefers_props") and random.random() < 0.5:
            props.append(random.choice(soft["prefers_props"]))
        
        # 7. Avoid Props из Action и Location (30% шанс попасть, несмотря на avoid)
        avoid_props_action = action_soft.get("avoid_props", [])
        avoid_props_location = soft.get("avoid_props", [])
        all_avoid = list(set(avoid_props_action + avoid_props_location))
        if all_avoid and random.random() < 0.3:
            props.append(random.choice(all_avoid))
        
        # 8. Фильтрация через Excludes Props (жёсткий бан — 0% попадания)
        excludes_props = hard.get("excludes_props", [])
        excludes_props_action = action_hard.get("excludes_props", [])
        all_excludes = list(set(excludes_props + excludes_props_action))
        
        # Убираем дубликаты и применяем жёсткий бан
        seen = set()
        unique_props = []
        for p in props:
            if p not in all_excludes and p not in seen:
                seen.add(p)
                unique_props.append(p)
        
        scene.props = unique_props
        
        # === ВЫБОР ИСТОЧНИКА ОСВЕЩЕНИЯ ===
        lighting_sources = (
            weather_soft.get("prefers_lighting_sources", []) or
            action_soft.get("prefers_lighting_sources", []) or
            soft.get("prefers_lighting_sources", [])
        )
        excludes_lighting = hard.get("excludes_lighting_sources", [])
        avoid_lighting = soft.get("avoid_lighting_sources", [])

        # 🛡️ АВТОЗАЩИТА ОСВЕЩЕНИЯ: запрещаем абсурдные источники для indoor/outdoor
        location_type = location_rule.get("meta", {}).get("type", "")
        is_indoor = location_type.startswith("indoor")
        is_outdoor = location_type.startswith("outdoor")
        
        auto_exclude_lighting = []
        if is_indoor:
            auto_exclude_lighting = [
                # Уличные источники
                "sunlight", "bright sunlight", "moonlight", "starlight",
                "streetlight", "street lamp", "traffic lights",
                "neon glow", "neon light", "headlights",
                "city lights", "store lights",
                # Атмосферные outdoor-эффекты
                "foggy lighting", "misty lighting", "hazy lighting",
                "gloomy lighting", "ethereal lighting", "dreamy lighting",
                "crepuscular rays", "sunbeams", "god rays",
                "sunrise light", "sunset light", "golden hour", "blue hour", "twilight", "magic hour",
                # Студийные/сценические (для дома не подходят)
                "camera flash", "flash photography", "strobe light",
                "concert lights", "stage lights", "spotlight",
                "laser light", "bioluminescence",
                "blinding light", "harsh lighting"
            ]
        elif is_outdoor:
            auto_exclude_lighting = [
                # Сугубо комнатные источники
                "ring light", "fireplace light", "chandelier", "ceiling light",
                "flash photography", "camera flash", "studio lighting",
                "fairy lights", "paper lantern", "lantern light",
                "lamp light", "lamplight", "desk lamp", "table lamp",
                "monitor glow", "smartphone glow", "screen glow"
            ]
        
        excludes_lighting = list(set(excludes_lighting + auto_exclude_lighting))
        
        # Если нет явных предпочтений — берём все доступные источники освещения из prompt-library
        if not lighting_sources:
            all_lighting = []
            lighting_dir = self.library.library_path / "07_lighting"
            if lighting_dir.exists():
                for txt_file in lighting_dir.rglob("*.txt"):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        all_lighting.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
            lighting_sources = all_lighting
        
        # Фильтруем через excludes (жёсткий бан)
        valid_sources = [s for s in lighting_sources if s not in excludes_lighting]
        
        # 🛑 ИСПРАВЛЕНИЕ: Если предпочтения запрещены, ищем fallback во ВСЕЙ библиотеке, кроме banned
        if not valid_sources:
            all_lighting = []
            lighting_dir = self.library.library_path / "07_lighting"
            if lighting_dir.exists():
                for txt_file in lighting_dir.rglob("*.txt"):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        all_lighting.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
            valid_sources = [s for s in all_lighting if s not in excludes_lighting]
        
        # Применяем веса с учётом avoid (мягкий бан)
        if valid_sources:
            if avoid_lighting:
                weights = []
                for source in valid_sources:
                    weight = 0.1 if source in avoid_lighting else 1.0
                    weights.append(weight)
                scene.lighting_source = random.choices(valid_sources, weights=weights, k=1)[0]
            else:
                scene.lighting_source = random.choice(valid_sources)
        else:
            scene.lighting_source = ""
            
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