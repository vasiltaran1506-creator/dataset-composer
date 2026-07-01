"""
Exporter - сохраняет сгенерированные сцены в датасет для обучения LoRA
"""
import os
import random
from pathlib import Path
from typing import List
from scene import Scene
from scene_builder import SceneBuilder


class Exporter:
    """Экспортирует сцены в файлы для обучения LoRA"""
    
    def __init__(self, builder: SceneBuilder, character_name: str, generation_weights: dict | None = None):
        self.builder = builder
        self.character_name = character_name.lower().replace(' ', '_')
        self.generation_weights = generation_weights or {}
        
    def export_dataset(
        self, 
        num_scenes: int, 
        output_dir: str = "dataset",
        create_placeholders: bool = False
    ) -> dict:
        """
        Генерирует и сохраняет датасет
        
        Args:
            num_scenes: Количество сцен для генерации
            output_dir: Папка для сохранения
            create_placeholders: Создавать ли пустые .png файлы (для визуализации структуры)
            
        Returns:
            Статистика по сгенерированным сценам
        """
        # Создаем папку для датасета
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n📁 Output directory: {output_path.absolute()}")
        print(f"🎬 Generating {num_scenes} scenes for {self.character_name}...")
        print("-" * 60)
        
        # Получаем список всех доступных локаций
        all_locations = [
            key.split('.')[-1] 
            for key in self.builder.scene_rules.keys() 
            if key.startswith('locations.')
        ]
        
        if not all_locations:
            raise ValueError("No locations found in scene rules")
            
        # Статистика
        stats = {
            "total_scenes": 0,
            "locations": {},
            "actions": {},
            "weathers": {}
        }
        
        # Генерируем сцены
        i = 0
        max_retries = 10 # Максимум попыток сгенерировать одну сцену
        
        # Подготовка весов для локаций
        location_weights = self.generation_weights.get('location')
        if location_weights:
            loc_weights_list = [location_weights.get(loc, 0.01) for loc in all_locations]
        else:
            loc_weights_list = None
        
        while i < num_scenes:
            if loc_weights_list:
                location = random.choices(all_locations, weights=loc_weights_list, k=1)[0]
            else:
                location = random.choice(all_locations)
            
            # Получаем hard_constraints для валидации
            hard = self.builder.get_hard_constraints_for_location(location)
            
            # Пытаемся сгенерировать валидную сцену
            scene = None
            for attempt in range(max_retries):
                candidate_scene = self.builder.build_scene(location)
                if self.builder.validate_scene(candidate_scene, hard):
                    scene = candidate_scene
                    break
                    
            if scene is None:
                # Если за 10 попыток не удалось создать идеальную сцену, пропускаем (очень редко)
                continue
                
            # Экспортируем в промпт
            fixed_traits = self.builder.full_profile.get('fixed_traits', [])
            prompt = scene.to_prompt(fixed_traits)
            
            filename = f"{self.character_name}_{location}_{i+1:04d}.txt"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
                
            # Обновляем статистику
            stats["total_scenes"] += 1
            stats["locations"][location] = stats["locations"].get(location, 0) + 1
            stats["actions"][scene.action] = stats["actions"].get(scene.action, 0) + 1
            stats["weathers"][scene.weather] = stats["weathers"].get(scene.weather, 0) + 1
            
            i += 1
            
            if i % 100 == 0 or i == num_scenes:
                print(f"   ✓ Generated {i}/{num_scenes} scenes")
                
        print("-" * 60)
        print(f"✅ Dataset generation complete!")
        
        return stats
        
    def print_statistics(self, stats: dict):
        """Выводит статистику по сгенерированному датасету"""
        print("\n📊 Dataset Statistics:")
        print("=" * 60)
        print(f"Total scenes: {stats['total_scenes']}")
        
        print(f"\n📍 Locations ({len(stats['locations'])} unique):")
        for loc, count in sorted(stats['locations'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_scenes']) * 100
            print(f"   {loc:25s}: {count:4d} ({percentage:5.1f}%)")
            
        print(f"\n🎬 Actions ({len(stats['actions'])} unique):")
        for action, count in sorted(stats['actions'].items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / stats['total_scenes']) * 100
            print(f"   {action:25s}: {count:4d} ({percentage:5.1f}%)")
            
        print(f"\n🌦️ Weathers ({len(stats['weathers'])} unique):")
        for weather, count in sorted(stats['weathers'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_scenes']) * 100
            print(f"   {weather:25s}: {count:4d} ({percentage:5.1f}%)")
            
        print("=" * 60)