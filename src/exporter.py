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
    
    def __init__(self, builder: SceneBuilder, character_name: str, generation_weights: dict | None = None, log_callback=None, verbose: bool = True, force_deficit_closure: bool = False):
        self.builder = builder
        self.character_name = character_name.lower().replace(' ', '_')
        self.generation_weights = generation_weights or {}
        self.log = log_callback if log_callback else print
        self.verbose = verbose
        self.force_deficit_closure = force_deficit_closure
        
        # Передаём флаг в SceneBuilder
        self.builder.force_deficit_closure = force_deficit_closure
        
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
        
        if self.verbose:
            self.log(f"\n📁 Output directory: {output_path.absolute()}\n")
            self.log(f"🎬 Generating {num_scenes} scenes for {self.character_name}...\n")
            self.log("-" * 60 + "\n")
        
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
        
        # Получаем веса для действий (нужны для инверсии приоритетов)
        action_weights_dict = self.generation_weights.get('action') or {}
        
        # КРИТЕРИЙ ИНВЕРСИИ: включён Force Deficit Closure И есть дефицит в actions
        use_inverted_logic = self.force_deficit_closure and bool(action_weights_dict)
        
        # 👇 В Aggressive Mode отключаем веса для weather и camera
        # Это предотвращает каскадную оверкоррекцию (night: 30%, pov: 25%)
        if use_inverted_logic:
            # Сохраняем оригинальные веса для лога
            self._original_weights = dict(self.generation_weights)
            # Очищаем веса weather и camera — они будут выбираться равномерно
            self.generation_weights = {
                k: v for k, v in self.generation_weights.items() 
                if k not in ['weather', 'camera']
            }
            # 👇 КРИТИЧНО: синхронизируем веса с SceneBuilder!
            self.builder.generation_weights = self.generation_weights
            self.log("🔕 Веса для weather и camera отключены (равномерное распределение)\n")
        
        # 👇 Счётчики для диагностики
        inverted_count = 0
        standard_count = 0
        chosen_actions_log: list[str] = []  # 👈 Список выбранных действий для лога
        
        while i < num_scenes:
            forced_action_for_scene: str | None = None
            
            if use_inverted_logic:
                # 🔥 ИНВЕРСИЯ ПРИОРИТЕТОВ: Action → Location
                # 1. Выбираем действие первым (по весам дефицита)
                all_actions = list(action_weights_dict.keys())
                a_weights = [action_weights_dict[a] for a in all_actions]
                chosen_action = random.choices(all_actions, weights=a_weights, k=1)[0]
                
                # 2. Получаем совместимые локации (Aggressive Mode)
                compatible_locs = self.builder.get_compatible_locations(chosen_action, aggressive=True)
                
                # 👇 Логируем первые 15 действий с количеством совместимых локаций
                if inverted_count < 15:
                    self.log(f"   🔍 {chosen_action:20s} → {len(compatible_locs):2d} совместимых локаций\n")
                
                if compatible_locs:
                    # 3. 👇 В AGGRESSIVE MODE ИГНОРИРУЕМ ВЕСА ЛОКАЦИЙ!
                    # Цель: равномерно распределить дефицитное действие по всем совместимым локациям.
                    # Иначе получим каскадную оверкоррекцию (дефицитное действие + дефицитная локация = переизбыток)
                    if self.force_deficit_closure:
                        location = random.choice(compatible_locs)  # Равномерный выбор
                    elif loc_weights_list:
                        filtered_weights = [
                            (loc_weights_list[all_locations.index(loc)] 
                             if loc in all_locations else 0.01)
                            for loc in compatible_locs
                        ]
                        location = random.choices(compatible_locs, weights=filtered_weights, k=1)[0]
                    else:
                        location = random.choice(compatible_locs)
                    
                    # 4. Запоминаем выбранное действие для передачи в build_scene
                    forced_action_for_scene = chosen_action
                    inverted_count += 1  # 👈 Счётчик инверсии
                    
                    # 👇 Логируем выбранное действие (первые 10)
                    if inverted_count <= 10:
                        chosen_actions_log.append(chosen_action)
                else:
                    # Fallback: если нет совместимых локаций (теоретически не должно случиться)
                    if loc_weights_list:
                        location = random.choices(all_locations, weights=loc_weights_list, k=1)[0]
                    else:
                        location = random.choice(all_locations)
                    standard_count += 1  # 👈 Счётчик стандартной логики
            else:
                # 🌿 СТАРАЯ ЛОГИКА: Location → Action
                if loc_weights_list:
                    location = random.choices(all_locations, weights=loc_weights_list, k=1)[0]
                else:
                    location = random.choice(all_locations)
            
            # Получаем hard_constraints для валидации
            hard = self.builder.get_hard_constraints_for_location(location)
            
            # Пытаемся сгенерировать валидную сцену
            scene = None
            for attempt in range(max_retries):
                # 👇 ПЕРЕДАЁМ forced_action (если он был выбран через инверсию)
                candidate_scene = self.builder.build_scene(location, forced_action=forced_action_for_scene)
                if self.builder.validate_scene(candidate_scene, hard):
                    scene = candidate_scene
                    break
                    
            if scene is None:
                # Если за 10 попыток не удалось создать идеальную сцену, пропускаем
                # 👇 Логируем отклонённые сцены (для диагностики)
                self.log(f"   ⚠️ Пропущена сцена: {forced_action_for_scene or 'auto'} в {location} (10 попыток не удались)\n")
                continue
                
            # Экспортируем в промпт
            fixed_traits = self.builder.full_profile.get('fixed_traits', [])
            prompt = scene.to_prompt(fixed_traits)
            
            # 👇 Уникальное имя файла с timestamp (предотвращает перезапись)
            import time
            timestamp = int(time.time())  # Unix timestamp
            filename = f"{self.character_name}_{location}_{timestamp}_{i+1:04d}.txt"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
                
            # Обновляем статистику
            stats["total_scenes"] += 1
            stats["locations"][location] = stats["locations"].get(location, 0) + 1
            stats["actions"][scene.action] = stats["actions"].get(scene.action, 0) + 1
            stats["weathers"][scene.weather] = stats["weathers"].get(scene.weather, 0) + 1
            
            i += 1
            
            if self.verbose and (i % 100 == 0 or i == num_scenes):
                self.log(f"   ✓ Generated {i}/{num_scenes} scenes\n")
                
        if self.verbose:
            self.log("-" * 60 + "\n")
            self.log(f"✅ Dataset generation complete!\n")

        # 👇 Диагностика: сколько сцен через инверсию vs стандарт
        self.log(f"\n🔬 Диагностика генерации:\n")
        self.log(f"   ⚡ Через инверсию (forced_action): {inverted_count} сцен\n")
        self.log(f"   🌿 Через стандартную логику:       {standard_count} сцен\n")
        
        if chosen_actions_log:
            self.log(f"   📋 Первые 10 выбранных действий: {', '.join(chosen_actions_log)}\n")
        if self.force_deficit_closure:
            if inverted_count == 0:
                self.log(f"   ⚠️ ВНИМАНИЕ: Force Deficit Closure включён, но инверсия не сработала ни разу!\n")
                self.log(f"      Проверьте, передаётся ли force_deficit_closure в Exporter.\n")
        
        # 👇 Восстанавливаем оригинальные веса (если были изменены)
        if hasattr(self, '_original_weights'):
            self.generation_weights = self._original_weights
            self.builder.generation_weights = self._original_weights  # 👈 И в SceneBuilder тоже!
            del self._original_weights

        return stats
        
    def print_statistics(self, stats: dict):
        """Выводит статистику по сгенерированному датасету (только для консоли)"""
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