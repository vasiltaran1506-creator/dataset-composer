"""
Config Loader - читает character-profile.yaml и scene-rules/*.toml
"""
import yaml
import toml
from pathlib import Path
from typing import Dict, List, Any


class ConfigLoader:
    """Загружает конфигурацию проекта"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.character_profile = None
        self.scene_rules = {}
        
    def load_character_profile(self, filename: str = "character-profile.yaml") -> Dict[str, Any]:
        """Загружает профиль персонажа"""
        profile_path = self.project_root / filename
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Character profile not found: {profile_path}")
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.character_profile = yaml.safe_load(f)
        
        print(f"✓ Loaded character profile: {self.character_profile['character']['name']}")
        return self.character_profile
    
    def load_scene_rules(self, rules_dir: str = "scene-rules") -> Dict[str, Any]:
        """Загружает все TOML-файлы из папки scene-rules"""
        rules_path = self.project_root / rules_dir
        
        if not rules_path.exists():
            print(f"⚠ Warning: Scene rules directory not found: {rules_path}")
            return {}
        
        # Рекурсивно обходим все .toml файлы
        for toml_file in rules_path.rglob("*.toml"):
            # Создаем ключ вида "locations.bedroom"
            relative_path = toml_file.relative_to(rules_path)
            key = str(relative_path.with_suffix('')).replace('\\', '.').replace('/', '.')
            
            with open(toml_file, 'r', encoding='utf-8') as f:
                self.scene_rules[key] = toml.load(f)
            
            print(f"✓ Loaded scene rule: {key}")
        
        return self.scene_rules
    
    def get_character_name(self) -> str:
        """Возвращает имя персонажа"""
        if not self.character_profile:
            raise ValueError("Character profile not loaded")
        return self.character_profile['character']['name']
    
    def get_fixed_traits(self) -> List[str]:
        """Возвращает неизменяемые черты персонажа"""
        if not self.character_profile:
            raise ValueError("Character profile not loaded")
        # fixed_traits лежит на корневом уровне, не внутри character
        return self.character_profile.get('fixed_traits', [])
    
    def get_outfit_whitelist(self) -> Dict[str, Any]:
        """Возвращает разрешенные стили одежды"""
        if not self.character_profile:
            raise ValueError("Character profile not loaded")
        return self.character_profile.get('outfit_whitelist', {})
    
    def load_location_types(self, types_dir: str = "scene-rules/location_types") -> Dict[str, Any]:
        """Загружает правила типов локаций"""
        types_path = self.project_root / types_dir
        self.location_types = {}
        
        if not types_path.exists():
            print(f"⚠ Warning: Location types directory not found: {types_path}")
            return {}
            
        for toml_file in types_path.rglob("*.toml"):
            key = toml_file.stem # Например, "indoor_cultural"
            with open(toml_file, 'r', encoding='utf-8') as f:
                self.location_types[key] = toml.load(f)
            print(f"✓ Loaded location type: {key}")
            
        return self.location_types


# Тестовый запуск (если запускать этот файл напрямую)
if __name__ == "__main__":
    loader = ConfigLoader("..")  # Указываем путь на уровень выше, к корню репозитория
    
    print("=" * 60)
    print("Dataset Composer - Config Loader Test")
    print("=" * 60)
    
    try:
        profile = loader.load_character_profile()
        rules = loader.load_scene_rules()
        print(f"\n✓ Success! Loaded profile and {len(rules)} rules.")
    except Exception as e:
        print(f"\n❌ Error: {e}")