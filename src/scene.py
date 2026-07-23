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
    # Composite pose (слоты; заполняется на фазе 2, на фазе 1 пусты => не влияют)
    pose_base: str = ""
    pose_head: str = ""
    pose_arms: str = ""
    pose_legs: str = ""
    # Composite face (слоты; имеют приоритет над старым полем expression)
    face_mood: str = ""
    face_eyes: str = ""
    face_mouth: str = ""
    
    def to_prompt(self, fixed_traits: List[str]) -> str:
        """Экспортирует сцену в текстовый промпт (сериализация)"""
        tags = list(fixed_traits)
        
        # Добавляем компоненты сцены в логическом порядке
        if self.location: tags.append(self.location)
        if self.weather: tags.append(self.weather)
        if self.action: tags.append(self.action)
        # Composite pose (base → legs → arms → head). На фазе 1 всё пусто.
        for _p in (self.pose_base, self.pose_legs, self.pose_arms, self.pose_head):
            if _p: tags.append(_p)
        # Composite face имеет приоритет над старым полем expression.
        _face = [x for x in (self.face_mood, self.face_eyes, self.face_mouth) if x]
        if _face:
            tags.extend(_face)
        elif self.expression:
            tags.append(self.expression)
        
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

    
    def to_structured_prompt(self, fixed_traits: List[str], character_trigger: str = "") -> str:
        """
        Генерирует структурированный промпт, оптимизированный для SDXL.
        Теги сгруппированы по 9 семантическим блокам для лучшего attention.
        
        Args:
            fixed_traits: Фиксированные черты персонажа из YAML-профиля
            character_trigger: Триггер-токен для активации LoRA персонажа
        """
        blocks = []
        
        # BLOCK 1: QUALITY & TRIGGER (КРИТИЧНО - первые 75 токенов!)
        block1 = ["masterpiece", "best quality", "absurdres", "highres"]
        if character_trigger:
            block1.append(character_trigger)
        block1.extend(["1girl", "solo"])
        blocks.append(block1)
        
        # BLOCK 2: SUBJECT CORE (базовые черты персонажа)
        block2 = list(fixed_traits)
        if block2:
            blocks.append(block2)
        
        # BLOCK 3: ACTION & POSE (composite pose: base → legs → arms → head)
        block3 = []
        if self.action:
            block3.append(self.action)
        for _p in (self.pose_base, self.pose_legs, self.pose_arms, self.pose_head):
            if _p:
                block3.append(_p)
        if block3:
            blocks.append(block3)
        
        # BLOCK 4: EXPRESSION & MOOD (composite face имеет приоритет над expression)
        block4 = []
        _face = [x for x in (self.face_mood, self.face_eyes, self.face_mouth) if x]
        if _face:
            block4.extend(_face)
        elif self.expression:
            block4.append(self.expression)
        if block4:
            blocks.append(block4)
        
        # BLOCK 5: OUTFIT & APPEARANCE (сортируем: full → top → bottom → legwear → footwear)
        block5 = []
        if self.outfit_full:
            block5.append(self.outfit_full)
        if self.outfit_top:
            block5.append(self.outfit_top)
        if self.outfit_bottom:
            block5.append(self.outfit_bottom)
        if self.outfit_legwear:
            block5.append(self.outfit_legwear)
        if self.outfit_footwear:
            block5.append(self.outfit_footwear)
        if block5:
            blocks.append(block5)
        
        # BLOCK 6: LOCATION & CONTEXT
        block6 = []
        if self.location:
            block6.append(f"in {self.location}")
        if block6:
            blocks.append(block6)
        
        # BLOCK 7: PROPS & INTERACTION
        block7 = list(self.props)
        if block7:
            blocks.append(block7)
        
        # BLOCK 8: LIGHTING & WEATHER
        block8 = []
        if self.lighting_source:
            block8.append(self.lighting_source)
        if self.lighting_quality:
            block8.append(self.lighting_quality)
        if self.weather:
            block8.append(self.weather)
        if block8:
            blocks.append(block8)
        
        # BLOCK 9: CAMERA & COMPOSITION
        block9 = []
        if self.camera:
            block9.append(self.camera)
        if block9:
            blocks.append(block9)
        
        # Собираем все теги из блоков
        all_tags = []
        for block in blocks:
            all_tags.extend(block)
        
        # Добавляем effects в конец
        all_tags.extend(self.effects)
        
        # Убираем дубликаты, сохраняя порядок
        seen = set()
        unique_tags = []
        for tag in all_tags:
            if tag and tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return ", ".join(unique_tags)