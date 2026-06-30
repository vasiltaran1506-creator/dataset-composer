"""
Scene - атомарное описание одного изображения (единственная сущность в системе)
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Scene:
    """Объект сцены. Промпт — это лишь способ его экспорта."""
    
    # Базовые компоненты
    location: str = ""
    action: str = ""
    weather: str = ""
    camera: str = ""
    
    # Одежда
    outfit_full: str = ""
    outfit_top: str = ""
    outfit_bottom: str = ""
    outfit_legwear: str = ""
    outfit_footwear: str = ""
    
    # Освещение
    lighting_source: str = ""
    lighting_quality: str = ""
    
    # Выражение лица
    expression: str = ""
    
    # Реквизит и эффекты
    props: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    
    def to_prompt(self, fixed_traits: List[str]) -> str:
        """Экспортирует сцену в текстовый промпт (сериализация)"""
        tags = list(fixed_traits)
        
        # Добавляем компоненты сцены в логическом порядке
        if self.location: tags.append(self.location)
        if self.weather: tags.append(self.weather)
        if self.action: tags.append(self.action)
        if self.expression: tags.append(self.expression)
        
        # Одежда
        if self.outfit_full: tags.append(self.outfit_full)
        if self.outfit_top: tags.append(self.outfit_top)
        if self.outfit_bottom: tags.append(self.outfit_bottom)
        if self.outfit_legwear: tags.append(self.outfit_legwear)
        if self.outfit_footwear: tags.append(self.outfit_footwear)
        
        # Освещение
        if self.lighting_source: tags.append(self.lighting_source)
        if self.lighting_quality: tags.append(self.lighting_quality)
        
        # Реквизит и эффекты
        tags.extend(self.props)
        tags.extend(self.effects)
        
        # Камера (обычно в конце промпта)
        if self.camera: tags.append(self.camera)
        
        # Убираем дубликаты, сохраняя порядок
        seen = set()
        unique_tags = [x for x in tags if not (x in seen or seen.add(x))]
        
        return ", ".join(unique_tags)