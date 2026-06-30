"""
Scene Builder v3 - Универсальный сборщик сцен с фильтрацией через Character Profile
"""
import random
from scene import Scene
from prompt_library import PromptLibrary


class SceneBuilder:
    """Строит логически согласованные сцены на основе универсальных TOML-правил"""
    
    def __init__(self, library: PromptLibrary, scene_rules: dict, character_profile: dict):
        self.library = library
        self.scene_rules = scene_rules
        # Храним весь профиль для доступа к outfit_whitelist
        self.full_profile = character_profile 
        
    def _get_outfit_whitelist(self) -> dict:
        """Возвращает whitelist одежды из character-profile.yaml"""
        if 'outfit_whitelist' in self.full_profile:
            return self.full_profile['outfit_whitelist']
        return self.full_profile.get('character', {}).get('outfit_whitelist', {})
        
    def _choose_smart_outfit(self, allowed_categories: list, excluded_categories: list) -> dict:
        """
        Умный выбор одежды v5: Исправлена логика Blacklist режима.
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
            
            # Определяем тип стиля
            has_full_body = "full_body" in style_data
            has_swimsuit = "swimsuit" in style_data
            has_top_bottom = "topwear" in style_data or "bottomwear" in style_data
            
            if allowed_categories:
                # РЕЖИМ 1: Whitelist (проверяем, разрешено ли в локации)
                if has_full_body:
                    if any("full_body" in cat for cat in allowed_categories):
                        style_compatible = True
                elif has_swimsuit:
                    if any("swimsuits" in cat for cat in allowed_categories):
                        style_compatible = True
                elif has_top_bottom:
                    has_top = any("topwear" in cat for cat in allowed_categories)
                    has_bottom = any("bottomwear" in cat for cat in allowed_categories)
                    if has_top and has_bottom:
                        style_compatible = True
            else:
                # РЕЖИМ 2: Blacklist (проверяем, не запрещено ли в локации)
                # ИСПРАВЛЕНО: Теперь правильно проверяем каждый элемент стиля
                if has_full_body:
                    # Проверяем, не запрещены ли full_body
                    full_body_excluded = any(
                        any(exc in cat for exc in ["pajamas", "swimsuits", "loungewear"])
                        for cat in excluded_categories
                    )
                    if not full_body_excluded:
                        style_compatible = True
                elif has_swimsuit:
                    # Проверяем, не запрещены ли swimsuits
                    swimsuit_excluded = any("swimsuits" in cat for cat in excluded_categories)
                    if not swimsuit_excluded:
                        style_compatible = True
                elif has_top_bottom:
                    # Проверяем, не запрещены ли topwear или bottomwear
                    # ИСПРАВЛЕНО: Теперь проверяем конкретные подкатегории
                    top_excluded = any(
                        any(exc in cat for exc in ["coats", "jackets"])
                        for cat in excluded_categories
                    )
                    bottom_excluded = any(
                        any(exc in cat for exc in ["pants"])
                        for cat in excluded_categories
                    )
                    if not top_excluded and not bottom_excluded:
                        style_compatible = True
                        
            if style_compatible:
                compatible_styles.append(style_name)
                
        if not compatible_styles:
            # ИСПРАВЛЕНО: Если нет совместимых стилей, ВСЕ РАВНО пытаемся выбрать из whitelist
            # вместо случайной одежды из библиотеки
            all_styles = list(whitelist.keys())
            if all_styles:
                compatible_styles = all_styles
                
        if not compatible_styles:
            return self._choose_random_outfit(allowed_categories, excluded_categories)
            
        chosen_style = random.choice(compatible_styles)
        style_data = whitelist[chosen_style]
        
        # Наполняем outfit
        if "full_body" in style_data:
            outfit["full"] = random.choice(style_data["full_body"])
        elif "swimsuit" in style_data:
            outfit["full"] = random.choice(style_data["swimsuit"])
        else:
            if "topwear" in style_data:
                outfit["top"] = random.choice(style_data["topwear"])
            if "bottomwear" in style_data:
                outfit["bottom"] = random.choice(style_data["bottomwear"])
                
        # Legwear и Footwear
        if "legwear" in style_data and random.random() < 0.7:
            outfit["legwear"] = random.choice(style_data["legwear"])
        if "footwear" in style_data and random.random() < 0.5:
            outfit["footwear"] = random.choice(style_data["footwear"])
                
        return outfit
    
    def _choose_random_outfit(self, allowed_categories: list, excluded_categories: list) -> dict:
        """
        Fallback: Случайная сборка одежды из библиотеки (если у персонажа нет whitelist)
        """
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
    def _get_filtered_tag(self, category: str, whitelist: dict) -> str:
        """
        Магия фильтрации! 
        Берет тег из библиотеки, но проверяет, есть ли у персонажа жесткие требования к этой категории.
        """
        parts = category.split('/')
        if len(parts) < 2:
            return self.library.get_random_tag(category) or ""
            
        folder = parts[-2]  # Например: 'full_body', 'topwear', 'bottomwear'
        file_name = parts[-1].replace('.txt', '') # Например: 'pajamas', 'shirts'
        
        allowed_tags = []
        
        # Ищем подходящие теги в whitelist персонажа
        for style_name, style_data in whitelist.items():
            if not isinstance(style_data, dict):
                continue
                
            # Совпадение по папке (например, ищем все разрешенные topwear)
            if folder in style_data:
                allowed_tags.extend(style_data[folder])
                
            # Совпадение по стилю и файлу (например, стиль 'pajamas' и файл 'pajamas.txt')
            elif style_name == file_name and folder in style_data:
                allowed_tags.extend(style_data[folder])
                
        # Если в профиле персонажа есть жесткие теги для этой категории - берем из них!
        if allowed_tags:
            return random.choice(allowed_tags)
            
        # Fallback: Если ограничений нет (например, это реквизит или у персонажа нет спец. требований)
        # берем случайный тег из общей библиотеки
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
        excluded_categories = hard_constraints.get("excludes_outfit_categories", [])
        
        if allowed_categories or excluded_categories:
            outfit_parts = self._choose_smart_outfit(allowed_categories, excluded_categories)
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