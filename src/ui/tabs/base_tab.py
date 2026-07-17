"""
Базовый класс для всех вкладок.
В Qt это будет наследоваться от QWidget.
"""
import customtkinter as ctk
from typing import Callable, Optional


class BaseTab(ctk.CTkFrame):
    """
    Базовый класс для вкладок Dataset Composer.
    
    Принципы:
    - Наследуется от CTkFrame (в Qt → QWidget)
    - Принимает callbacks для связи с главным окном
    - Управляет только своим UI, не лезет в другие вкладки
    """
    
    def __init__(self, master, log_callback: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.log_callback = log_callback or print
        
        # Настройка grid для растягивания
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _log(self, message: str):
        """Унифицированный логгинг"""
        self.log_callback(message)
    
    def refresh(self):
        """
        Метод для обновления данных вкладки.
        Переопределяется в наследниках.
        """
        pass
    
    def cleanup(self):
        """
        Очистка ресурсов перед уничтожением.
        Переопределяется в наследниках.
        """
        pass