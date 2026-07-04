"""
Менеджер настроек приложения.
Хранит пользовательские настройки в settings.json в корне проекта.
"""
import json
from pathlib import Path


# Значения по умолчанию для всех настроек
DEFAULT_SETTINGS = {
    # Пути к директориям
    'directories': {
        'output_directory': '',       # Пустая строка = использовать дефолт
        'profiles_path': '',
    },
    
    # Параметры генерации по умолчанию
    'generation_defaults': {
        'num_scenes': 30,
        'force_deficit_closure': False,
        'balance_locations': True,
        'balance_actions': True,
        'balance_weather': True,
        'balance_cameras': True,
    },
    
    # Поведение приложения
    'behavior': {
        'confirm_delete': True,
    },
    
    # Информация о программе
    'about': {
        'version': '1.1.0',
        'author': 'Vasily Taran',
        'github': 'https://github.com/vasiltaran1506-creator/dataset-composer',
    },
}


class SettingsManager:
    """Менеджер настроек с автосохранением и значениями по умолчанию."""
    
    def __init__(self, settings_file: Path):
        self.settings_file = settings_file
        self.settings: dict = {}
        self._load()
    
    def _load(self):
        """Загружает настройки из файла, используя дефолты для отсутствующих ключей."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # Мержим загруженные настройки с дефолтами (глубокое объединение)
                self.settings = self._deep_merge(DEFAULT_SETTINGS.copy(), loaded)
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️ Ошибка чтения settings.json: {e}. Используются настройки по умолчанию.")
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            self.settings = DEFAULT_SETTINGS.copy()
            self._save()  # Создаём файл с дефолтами при первом запуске
    
    def _save(self):
        """Сохраняет текущие настройки в файл."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"❌ Ошибка сохранения settings.json: {e}")
    
    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Глубокое объединение двух словарей (override перезаписывает base)."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, section: str, key: str):
        """Возвращает значение настройки: settings[section][key]."""
        return self.settings.get(section, {}).get(key)
    
    def set(self, section: str, key: str, value):
        """Устанавливает значение и автосохраняет файл."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        self._save()
    
    def reset_to_defaults(self):
        """Сбрасывает все настройки к значениям по умолчанию."""
        self.settings = DEFAULT_SETTINGS.copy()
        self._save()
    
    def get_section(self, section: str) -> dict:
        """Возвращает всю секцию настроек."""
        return self.settings.get(section, {}).copy()