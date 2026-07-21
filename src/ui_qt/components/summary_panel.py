"""SummaryPanel — правая context-панель Profiles workspace (§7.4, §8.31).
Отображает портрет, имя персонажа, общий счётчик выбранных тегов
и разбивку по категориям с цветными буллетами.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QColor
from ui_qt.icon_manager import IconManager


# ── Цвета категорий (те же, что в category_card.py) ──
try:
    from ui_qt.theme import CategoryColors as _CC
    def _g(name, fb):
        return getattr(_CC, name, fb)
except Exception:
    def _g(name, fb):
        return fb

_CAT_COLORS = {
    "Body Type": _g("BODY", "#f472b6"),
    "Body Features": _g("BODY", "#f472b6"),
    "Eye Color": _g("EYES", "#fbbf24"),
    "Eye Shape": _g("EYES", "#fbbf24"),
    "Face Features": _g("FACE", "#a78bfa"),
    "Hair Style": _g("HAIR", "#34d399"),
    "Hair Color": _g("HAIR", "#34d399"),
    "Hair Length": _g("HAIR", "#34d399"),
    "Skin Tone": _g("SKIN", "#fb923c"),
}


class _PortraitPlaceholder(QFrame):
    """Пустой плейсхолдер портрета с иконкой и текстом 'Add portrait'."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QFrame {
                background-color: #283145;
                border-radius: 12px;
                border: 2px dashed #414c63;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel(IconManager.get('user'))
        icon.setStyleSheet("font-size: 48px; color: #5a6378; background: transparent; border: none;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        text = QLabel("Add portrait")
        text.setStyleSheet("color: #98a0b3; font-size: 12px; background: transparent; border: none;")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)


class _CategoryRow(QWidget):
    """Одна строка разбивки: цветная буллета + название + счётчик."""
    clicked = Signal(str)  # category_name
    
    def __init__(self, category_name: str, count: int, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.count = count
        
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QWidget:hover {
                background-color: #283145;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Цветная буллета
        color = _CAT_COLORS.get(category_name, "#4f6df5")
        bullet = QLabel("●")
        bullet.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent; border: none;")
        layout.addWidget(bullet)
        
        # Название категории
        name_label = QLabel(category_name)
        name_label.setStyleSheet("color: #e6e9f0; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(name_label, 1)
        
        # Счётчик
        count_label = QLabel(f"{count} selected")
        count_label.setStyleSheet("color: #98a0b3; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(count_label)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.category_name)
        super().mousePressEvent(event)


class SummaryPanel(QWidget):
    """Правая context-панель Profiles workspace."""
    scroll_to_category = Signal(str)  # category_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setMaximumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Портрет (плейсхолдер)
        self.portrait = _PortraitPlaceholder()
        layout.addWidget(self.portrait)
        
        # Имя персонажа + общий счётчик
        header_frame = QWidget()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        self.name_label = QLabel("No profile selected")
        self.name_label.setStyleSheet("color: #e6e9f0; font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.name_label)
        
        self.total_badge = QLabel("0 traits")
        self.total_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(79, 109, 245, 0.15);
                color: #4f6df5;
                border-radius: 9999px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        self.total_badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header_layout.addWidget(self.total_badge)
        
        layout.addWidget(header_frame)
        
        # Разделитель
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #313a4d; max-height: 1px;")
        layout.addWidget(divider)
        
        # Заголовок секции
        section_label = QLabel("Character Summary")
        section_label.setStyleSheet("color: #98a0b3; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        layout.addWidget(section_label)
        
        # Скроллируемый список категорий
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.categories_widget = QWidget()
        self.categories_layout = QVBoxLayout(self.categories_widget)
        self.categories_layout.setContentsMargins(0, 0, 0, 0)
        self.categories_layout.setSpacing(2)
        self.categories_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.categories_widget)
        layout.addWidget(scroll, 1)
        
        # Ссылка "View Full Summary"
        self.full_summary_link = QPushButton("View Full Summary ›")
        self.full_summary_link.setCursor(Qt.PointingHandCursor)
        self.full_summary_link.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4f6df5;
                border: none;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
                padding: 8px 0;
            }
            QPushButton:hover {
                color: #6b85f7;
                text-decoration: underline;
            }
        """)
        layout.addWidget(self.full_summary_link)
        
        self._category_rows = {}
    
    def set_profile_name(self, name: str):
        """Обновляет имя персонажа в заголовке."""
        self.name_label.setText(name if name else "No profile selected")
    
    def update_summary(self, selected_tags: list):
        """Обновляет разбивку по категориям на основе выбранных тегов.
        
        Args:
            selected_tags: Список dict вида {'tag': str, 'category': str}
        """
        # Считаем по категориям
        counts = {}
        for entry in selected_tags:
            cat = entry.get('category', '')
            counts[cat] = counts.get(cat, 0) + 1
        
        # Обновляем общий счётчик
        total = sum(counts.values())
        self.total_badge.setText(f"{total} traits" if total else "0 traits")
        
        # Очищаем старые строки
        for row in self._category_rows.values():
            row.deleteLater()
        self._category_rows.clear()
        
        # Создаём новые строки для категорий с count > 0
        for cat_name, count in sorted(counts.items()):
            if count > 0:
                row = _CategoryRow(cat_name, count)
                row.clicked.connect(self.scroll_to_category.emit)
                self.categories_layout.addWidget(row)
                self._category_rows[cat_name] = row
        
        # Если ничего не выбрано — показываем placeholder
        if not counts:
            empty_label = QLabel("No traits selected yet")
            empty_label.setStyleSheet("color: #5a6378; font-size: 12px; font-style: italic;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.categories_layout.addWidget(empty_label)
            self._category_rows['__empty__'] = empty_label