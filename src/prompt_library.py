"""
Prompt Library - индексирует все .txt файлы из папки prompt-library
"""
import random
from pathlib import Path
from typing import Dict, List, Optional


class PromptLibrary:
    """Загружает и индексирует библиотеку промптов"""
    
    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
        self.categories: Dict[str, List[str]] = {}
        
    def load_library(self) -> Dict[str, List[str]]:
        """Сканирует папку и загружает все .txt файлы"""
        if not self.library_path.exists():
            raise FileNotFoundError(f"Prompt library not found: {self.library_path}")
            
        # Рекурсивно ищем все .txt файлы
        for txt_file in self.library_path.rglob("*.txt"):
            # Создаем относительный путь как ключ категории
            # Например: "02_clothing/topwear/shirts.txt"
            # Используем replace('\\', '/'), чтобы пути работали и на Windows, и на Linux
            relative_path = str(txt_file.relative_to(self.library_path)).replace('\\', '/')
            
            tags = []
            with open(txt_file, 'r', encoding='utf-8') as f:
                for line in f:
                    tag = line.strip()
                    if tag: # Игнорируем пустые строки
                        tags.append(tag)
            
            if tags:
                self.categories[relative_path] = tags
                
        return self.categories
        
    def get_tags(self, category: str) -> List[str]:
        """Возвращает все теги для указанной категории"""
        return self.categories.get(category, [])
        
    def get_random_tag(self, category: str) -> Optional[str]:
        """Возвращает случайный тег из категории"""
        tags = self.get_tags(category)
        if not tags:
            return None
        return random.choice(tags)
        
    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику по библиотеке"""
        total_files = len(self.categories)
        total_tags = sum(len(tags) for tags in self.categories.values())
        return {
            "total_files": total_files,
            "total_tags": total_tags
        }