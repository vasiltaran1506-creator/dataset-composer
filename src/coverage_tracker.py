"""
Coverage Tracker - Stateless анализ и балансировка датасета
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class CoverageTracker:
    """
    Сканирует папку с промптами, строит матрицу покрытия и рассчитывает веса для балансировки.
    """
    
    def __init__(self, available_locations: List[str], available_actions: List[str],
                 available_weathers: List[str], available_cameras: List[str],
                 outfit_category_map: Optional[Dict[str, str]] = None):
        """
        Инициализация с списками известных тегов для классификации.

        Args:
            outfit_category_map: Словарь {tag: category} для одежды.
                Пример: {"white shirt": "topwear", "black jeans": "bottomwear"}
        """
        self.location_set = set(available_locations)
        self.action_set = set(available_actions)
        self.weather_set = set(available_weathers)
        self.camera_set = set(available_cameras)
        self.outfit_category_map = outfit_category_map or {}
        
    def scan_folder(self, folder_path: str) -> Dict:
        """
        Сканирует папку, читает все .txt файлы и строит матрицу покрытия.
        
        Returns:
            Словарь с полной статистикой покрытия
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise ValueError(f"Папка не существует: {folder_path}")
            
        if not folder.is_dir():
            raise ValueError(f"Путь не является папкой: {folder_path}")
            
        # Инициализация матрицы
        matrix = {
            "folder_path": str(folder.absolute()),
            "total_scenes": 0,
            "dimensions": {
                "location": {},
                "action": {},
                "weather": {},
                "camera": {},
                "outfit": {}
            },
            "unmatched_tags_count": 0,
            "malformed_files": [],
            "scan_timestamp": datetime.now().isoformat()
        }
        
        # Сканирование файлов
        txt_files = list(folder.glob("*.txt"))
        
        if not txt_files:
            print(f"⚠️ Warning: В папке {folder_path} не найдено .txt файлов")
            return matrix
            
        print(f"🔍 Сканирование {len(txt_files)} файлов...")
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                if not content:
                    matrix["malformed_files"].append(txt_file.name)
                    continue
                    
                # Парсинг тегов
                tags = [tag.strip() for tag in content.split(',')]
                
                # Классификация тегов
                found_location = None
                found_action = None
                found_weather = None
                found_camera = None
                found_outfit_category = None
                
                for tag in tags:
                    if tag in self.location_set and not found_location:
                        found_location = tag
                    elif tag in self.action_set and not found_action:
                        found_action = tag
                    elif tag in self.weather_set and not found_weather:
                        found_weather = tag
                    elif tag in self.camera_set and not found_camera:
                        found_camera = tag
                    elif tag in self.outfit_category_map and not found_outfit_category:
                        found_outfit_category = self.outfit_category_map[tag]
                        
                # Обновление матрицы
                if found_location:
                    matrix["dimensions"]["location"][found_location] = \
                        matrix["dimensions"]["location"].get(found_location, 0) + 1
                
                if found_action:
                    matrix["dimensions"]["action"][found_action] = \
                        matrix["dimensions"]["action"].get(found_action, 0) + 1
                
                if found_weather:
                    matrix["dimensions"]["weather"][found_weather] = \
                        matrix["dimensions"]["weather"].get(found_weather, 0) + 1
                
                if found_camera:
                    matrix["dimensions"]["camera"][found_camera] = \
                        matrix["dimensions"]["camera"].get(found_camera, 0) + 1
                
                if found_outfit_category:
                    matrix["dimensions"]["outfit"][found_outfit_category] = \
                        matrix["dimensions"]["outfit"].get(found_outfit_category, 0) + 1
                
                matrix["total_scenes"] += 1
                
            except Exception as e:
                matrix["malformed_files"].append(txt_file.name)
                print(f"⚠️ Warning: Пропущен файл {txt_file.name}: {e}")
                
        # Расчет процентов
        matrix["percentages"] = {}
        for dimension, counts in matrix["dimensions"].items():
            if matrix["total_scenes"] > 0:
                matrix["percentages"][dimension] = {
                    k: (v / matrix["total_scenes"]) * 100 
                    for k, v in counts.items()
                }
            else:
                matrix["percentages"][dimension] = {}
                
        # Определение дефицита и переизбытка
        matrix["status"] = self._calculate_deficits(matrix)
        
        return matrix
        
    def _calculate_deficits(self, matrix: Dict) -> Dict:
        """
        Рассчитывает дефицит и переизбыток для каждой категории.
        """
        status = {"deficits": [], "overflows": []}
        
        for dimension, percentages in matrix["percentages"].items():
            if not percentages:
                continue
                
            # Целевой процент (равномерное распределение)
            target_pct = 100.0 / len(percentages)
            
            for category, pct in percentages.items():
                if pct < target_pct * 0.5:  # Меньше 50% от цели = дефицит
                    status["deficits"].append(f"{dimension}.{category}")
                elif pct > target_pct * 1.5:  # Больше 150% от цели = переизбыток
                    status["overflows"].append(f"{dimension}.{category}")
                    
        return status
        
    def print_report(self, matrix: Dict):
        """
        Выводит красивый ASCII-отчет в консоль.
        """
        print("\n" + "=" * 70)
        print(f"📊 МАТРИЦА ПОКРЫТИЯ ДЛЯ: {matrix['folder_path']}")
        print("=" * 70)
        print(f"Всего сцен проанализировано: {matrix['total_scenes']}")
        
        if matrix["malformed_files"]:
            print(f"\n⚠️ Пропущено битых файлов: {len(matrix['malformed_files'])}")
            
        # Вывод по каждому измерению
        dimension_names = {
            "location": "📍 ЛОКАЦИИ",
            "action": "🎬 ДЕЙСТВИЯ",
            "weather": "🌦️ ПОГОДА",
            "camera": "📸 КАМЕРЫ",
            "outfit": "👕 ОДЕЖДА"
        }
        
        for dimension, display_name in dimension_names.items():
            counts = matrix["dimensions"][dimension]
            percentages = matrix["percentages"][dimension]
            
            if not counts:
                continue
                
            print(f"\n{display_name}:")
            print("-" * 70)
            
            # Сортировка по убыванию
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            
            for category, count in sorted_items:
                pct = percentages[category]
                
                # Визуальный барчарт
                bar_length = int(pct / 2)  # 50% = 25 символов
                bar = "█" * bar_length + "░" * (50 - bar_length)
                
                # Индикаторы статуса
                status_icon = ""
                if f"{dimension}.{category}" in matrix["status"]["deficits"]:
                    status_icon = " 🔻 ДЕФИЦИТ"
                elif f"{dimension}.{category}" in matrix["status"]["overflows"]:
                    status_icon = " ⚠️ ПЕРЕИЗБЫТОК"
                    
                print(f"   {category:25s}: {count:3d} ({pct:5.1f}%) [{bar}]{status_icon}")
                
        # Сводка
        print("\n" + "=" * 70)
        print("📋 СВОДКА:")
        if matrix["status"]["deficits"]:
            print(f"   🔻 Дефицитные категории: {', '.join(matrix['status']['deficits'])}")
        if matrix["status"]["overflows"]:
            print(f"   ⚠️ Категории с переизбытком: {', '.join(matrix['status']['overflows'])}")
        if not matrix["status"]["deficits"] and not matrix["status"]["overflows"]:
            print("   ✅ Датасет идеально сбалансирован!")
        print("=" * 70 + "\n")
        
    def calculate_generation_weights(self, matrix: Dict) -> Dict[str, Dict[str, float]]:
        """
        Рассчитывает веса для взвешенной генерации, чтобы исправить дефицит.
        
        Returns:
            Словарь весов для каждого измерения
        """
        weights = {}
        
        for dimension, percentages in matrix["percentages"].items():
            if not percentages:
                continue
                
            # Целевой процент (равномерное распределение)
            target_pct = 100.0 / len(percentages)
            
            # Расчет deficit_score для каждой категории
            deficit_scores = {}
            for category, current_pct in percentages.items():
                deficit_score = max(0, target_pct - current_pct)
                deficit_scores[category] = deficit_score
                
            # Нормализация в вероятности
            total_deficit = sum(deficit_scores.values())
            
            if total_deficit > 0:
                # Нормализуем и добавляем минимальный "пол" (0.02)
                weights[dimension] = {}
                raw_weights = {}
                for category, score in deficit_scores.items():
                    normalized = (score / total_deficit) * 0.98 + 0.02
                    raw_weights[category] = normalized
                
                # 👇 ОЧЕНЬ АГРЕССИВНОЕ СГЛАЖИВАНИЕ: макс. вес 15%
                # Это гарантирует, что ни одно действие не будет генерироваться чаще 15%
                # даже если оно в критическом дефиците
                MAX_WEIGHT = 0.15
                MIN_WEIGHT = 0.05  # Минимальный вес для всех категорий
                
                # Применяем min-max ограничения
                capped_weights = {}
                for k, v in raw_weights.items():
                    capped_weights[k] = max(MIN_WEIGHT, min(v, MAX_WEIGHT))
                
                # Перенормализуем после сглаживания
                total_capped = sum(capped_weights.values())
                for category, weight in capped_weights.items():
                    weights[dimension][category] = weight / total_capped
            else:
                # Если дефицита нет, равномерное распределение
                weights[dimension] = {cat: 1.0 / len(percentages) for cat in percentages}
                
        return weights