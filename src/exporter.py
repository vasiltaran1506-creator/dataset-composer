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
    
    def __init__(self, builder: SceneBuilder, character_name: str):
        self.builder = builder
        self.character_name = character_name.lower().replace(' ', '_')
        
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
        for i in range(num_scenes):
            # Выбираем случайную локацию
            location = random.choice(all_locations)
            
            # Строим сцену
            scene = self.builder.build_scene(location)
            
            # Экспортируем в промпт
            fixed_traits = self.builder.full_profile.get('fixed_traits', [])
            prompt = scene.to_prompt(fixed_traits)
            
            # Генерируем имя файла
            filename = f"{self.character_name}_{location}_{i+1:04d}.txt"
            filepath = output_path / filename
            
            # Сохраняем промпт
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
                
            # Опционально: создаем пустышку для картинки
            if create_placeholders:
                img_filename = f"{self.character_name}_{location}_{i+1:04d}.png"
                img_filepath = output_path / img_filename
                # Создаем пустой файл (1x1 пиксель PNG)
                with open(img_filepath, 'wb') as f:
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                           b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
                           b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            
            # Обновляем статистику
            stats["total_scenes"] += 1
            stats["locations"][location] = stats["locations"].get(location, 0) + 1
            stats["actions"][scene.action] = stats["actions"].get(scene.action, 0) + 1
            stats["weathers"][scene.weather] = stats["weathers"].get(scene.weather, 0) + 1
            
            # Прогресс-бар
            if (i + 1) % 100 == 0 or i == num_scenes - 1:
                print(f"   ✓ Generated {i + 1}/{num_scenes} scenes")
                
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