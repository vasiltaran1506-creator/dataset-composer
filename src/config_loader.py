"""
Config Loader - читает character-profile.yaml и scene-rules/*.toml
"""
import yaml
try:
    import tomli as toml  # Для Python < 3.11
except ImportError:
    import tomllib as toml  # Для Python 3.11+
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random

# ═══════════════════════════════════════════════════════════════
# CHARACTER PERSONALITY MODEL  (Character Behavior Model §5/§8)
# Характер = взвешенные слоты по режимам. Движок пока НЕ использует
# эту модель (фаза 1 — только данные); влияние появится на фазе 2.
# Модель не зависит от prompt-library: хранит веса по именам слотов.
# ═══════════════════════════════════════════════════════════════

# Вес «по умолчанию» для тега, не упомянутого в слоте. 1.0 = нейтрально
# (не меняет произведение весов в формуле финального веса, §6.2).
NEUTRAL_WEIGHT = 1.0

# Контракт имён слотов. Группировка (expression/pose/atmosphere) — это
# синтаксический сахар yaml; парсер разворачивает её в плоские слоты.
# 'action' — плоская ось (один слот), остальные — составные.
AXIS_LAYOUT = {
    'expression': ['mood', 'eyes', 'mouth'],
    'pose':       ['base', 'head', 'arms', 'legs'],
    'atmosphere': ['lighting', 'weather'],   # опциональная ось
    # 'action' обрабатывается отдельно (плоский dict tag->weight)
}


@dataclass
class PersonalityMode:
    """Один режим характера. weight — вероятность режима между сценами
    (для стабильного персонажа режим один; для биполярного — несколько).
    slot_weights: {slot_name: {tag: weight}}. Вес 0.0 = мягкий бан,
    вес > 1.0 = буст, отсутствующий тег = NEUTRAL_WEIGHT."""
    id: str = "default"
    weight: float = 1.0
    slot_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class CharacterPersonality:
    """Характер персонажа как набор режимов. Нейтральный профиль
    (блока personality нет) = один пустой режим => все веса нейтральны."""
    modes: List[PersonalityMode] = field(default_factory=list)

    # ── конструкторы ──
    @classmethod
    def neutral(cls) -> "CharacterPersonality":
        return cls(modes=[PersonalityMode(id="default", weight=1.0, slot_weights={})])

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "CharacterPersonality":
        """Парсит блок yaml 'personality'. Если блока/режимов нет — neutral()."""
        if not d or not isinstance(d, dict):
            return cls.neutral()
        raw_modes = d.get('modes')
        if not raw_modes or not isinstance(raw_modes, list):
            return cls.neutral()

        modes: List[PersonalityMode] = []
        for md in raw_modes:
            if not isinstance(md, dict):
                continue
            slot_weights: Dict[str, Dict[str, float]] = {}
            axes = md.get('axes') or {}
            if isinstance(axes, dict):
                for axis_name, axis_val in axes.items():
                    if axis_name == 'action':
                        # плоская ось: значение само есть {tag: weight}
                        if isinstance(axis_val, dict):
                            slot_weights['action'] = {
                                str(k): float(v) for k, v in axis_val.items()
                            }
                        continue
                    slots = AXIS_LAYOUT.get(axis_name, [])
                    if not slots or not isinstance(axis_val, dict):
                        continue
                    for slot in slots:
                        w = axis_val.get(slot)
                        if isinstance(w, dict):
                            slot_weights[slot] = {
                                str(k): float(v) for k, v in w.items()
                            }
            modes.append(PersonalityMode(
                id=str(md.get('id', f'mode_{len(modes)}')),
                weight=float(md.get('weight', 1.0)),
                slot_weights=slot_weights,
            ))

        if not modes:
            return cls.neutral()
        return cls(modes=modes)

    # ── запросы (их будет звать PreferenceResolver на фазе 2) ──
    def is_neutral(self) -> bool:
        """True, если ни один режим не несёт ненулевых весов (характер не задан)."""
        return all(not m.slot_weights for m in self.modes)

    def weight_for(self, mode: PersonalityMode, slot: str, tag: str) -> float:
        """Вес тега в слоте для данного режима; отсутствующий = NEUTRAL_WEIGHT."""
        return mode.slot_weights.get(slot, {}).get(tag, NEUTRAL_WEIGHT)

    def sample_mode(self, rng: random.Random) -> PersonalityMode:
        """Выбирает режим по weight (вероятность переключения между сценами).
        Один режим => возвращается без зависимости от rng."""
        if len(self.modes) == 1:
            return self.modes[0]
        weights = [max(0.0, m.weight) for m in self.modes]
        total = sum(weights)
        if total <= 0.0:
            return self.modes[0]
        return rng.choices(self.modes, weights=weights, k=1)[0]

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
            
            with open(toml_file, 'rb') as f:
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
    
    def get_character_trigger(self) -> str:
        """Возвращает trigger-токен для активации LoRA персонажа"""
        if not self.character_profile:
            raise ValueError("Character profile not loaded")
        # character_trigger лежит на корневом уровне
        return self.character_profile.get('character_trigger', '')
    
    def get_outfit_whitelist(self) -> Dict[str, Any]:
        """Возвращает разрешенные стили одежды"""
        if not self.character_profile:
            raise ValueError("Character profile not loaded")
        return self.character_profile.get('outfit_whitelist', {})

    def get_personality(self) -> CharacterPersonality:
        """Возвращает модель характера (блок 'personality'). Если блока нет —
        нейтральный профиль (характер не влияет). Старые поля
        expression_filter / pose_filter УСТАРЕЛИ и движком как характер
        НЕ читаются (см. Character Behavior Model §10) — они остаются в yaml
        только потому, что текущий UI их ещё пишет; UI перейдёт на новый блок
        на фазе 4."""
        if not self.character_profile:
            raise ValueError("Character profile not loaded")
        return CharacterPersonality.from_dict(
            self.character_profile.get('personality')
        )
    
    def load_location_types(self, types_dir: str = "scene-rules/location_types") -> Dict[str, Any]:
        """Загружает правила типов локаций"""
        types_path = self.project_root / types_dir
        self.location_types = {}
        
        if not types_path.exists():
            print(f"⚠ Warning: Location types directory not found: {types_path}")
            return {}
            
        for toml_file in types_path.rglob("*.toml"):
            key = toml_file.stem # Например, "indoor_cultural"
            with open(toml_file, 'rb') as f:
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