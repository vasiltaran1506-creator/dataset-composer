"""
Scene - атомарное описание одного изображения (единственная сущность в системе)
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Scene:
    """Объект сцены. Промпт — это лишь способ его экспорта."""
    location: str = ""
    action: str = ""
    outfit_full: str = ""
    outfit_top: str = ""
    outfit_bottom: str = ""
    outfit_legwear: str = ""
    lighting_source: str = ""
    lighting_quality: str = ""
    props: List[str] = field(default_factory=list)
    
    def to_prompt(self, fixed_traits: List[str]) -> str:
        """Экспортирует сцену в текстовый промпт (сериализация)"""
        tags = list(fixed_traits)
        
        # Добавляем компоненты сцены
        if self.location: tags.append(self.location)
        if self.action: tags.append(self.action)
        if self.outfit_full: tags.append(self.outfit_full)
        if self.outfit_top: tags.append(self.outfit_top)
        if self.outfit_bottom: tags.append(self.outfit_bottom)
        if self.outfit_legwear: tags.append(self.outfit_legwear)
        if self.lighting_source: tags.append(self.lighting_source)
        if self.lighting_quality: tags.append(self.lighting_quality)
        tags.extend(self.props)
        
        # Убираем дубликаты, сохраняя порядок (важно для Danbooru-тегов)
        seen = set()
        unique_tags = [x for x in tags if not (x in seen or seen.add(x))]
        
        return ", ".join(unique_tags)