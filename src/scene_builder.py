"""
Scene Builder - собирает сцены на основе правил и библиотеки
"""
import random
from scene import Scene
from prompt_library import PromptLibrary


class SceneBuilder:
    """Строит логически согласованные сцены"""
    
    def __init__(self, library: PromptLibrary, scene_rules: dict, character_profile: dict):
        self.library = library
        self.scene_rules = scene_rules
        self.character_profile = character_profile
        
    def build_scene(self, location_id: str) -> Scene:
        scene = Scene()
        scene.location = location_id # Используем ID как базовый тег (например, "bedroom")
        
        rule_key = f"locations.{location_id}"
        rule = self.scene_rules.get(rule_key, {})
        
        soft_constraints = rule.get("soft_constraints", {})
        hard_constraints = rule.get("hard_constraints", {})
        
        # 1. Выбор действия (Action)
        prefers_actions = soft_constraints.get("prefers_actions", ["standing", "sitting"])
        scene.action = random.choice(prefers_actions)
        
        # 2. Выбор одежды (Outfit) на основе Whitelist из TOML
        allowed_categories = hard_constraints.get("allowed_outfit_categories", [])
        
        if allowed_categories:
            chosen_category = random.choice(allowed_categories)
            outfit_tag = self.library.get_random_tag(chosen_category)
            
            if outfit_tag:
                if "full_body" in chosen_category:
                    scene.outfit_full = outfit_tag
                elif "topwear" in chosen_category:
                    scene.outfit_top = outfit_tag
                    # Если выбрали верх, попробуем подобрать низ из разрешенных
                    bottom_cats = [c for c in allowed_categories if "bottomwear" in c]
                    if bottom_cats:
                        scene.outfit_bottom = self.library.get_random_tag(random.choice(bottom_cats))
                elif "bottomwear" in chosen_category:
                    scene.outfit_bottom = outfit_tag
                    
            # Подберем legwear (носки/чулки), если есть в разрешенных (70% шанс)
            legwear_cats = [c for c in allowed_categories if "legwear" in c]
            if legwear_cats and random.random() > 0.3: 
                scene.outfit_legwear = self.library.get_random_tag(random.choice(legwear_cats))
        
        # 3. Выбор реквизита (Props)
        prefers_props = soft_constraints.get("prefers_props", [])
        if prefers_props:
            num_props = random.choice([1, 2])
            # Берем 1 или 2 случайных предмета из рекомендованных
            scene.props = random.sample(prefers_props, min(num_props, len(prefers_props)))
            
        # 4. Выбор освещения (Lighting)
        prefers_lighting_sources = soft_constraints.get("prefers_lighting_sources", [])
        if prefers_lighting_sources:
            scene.lighting_source = random.choice(prefers_lighting_sources)
            
        prefers_lighting_quality = soft_constraints.get("prefers_lighting_quality", [])
        if prefers_lighting_quality:
            scene.lighting_quality = random.choice(prefers_lighting_quality)
            
        return scene