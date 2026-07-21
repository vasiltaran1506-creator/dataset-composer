"""SummaryPanel — правая context-панель Profiles workspace (§7.4, §8.31).

Показывает портрет, имя персонажа, общий счётчик тегов и — главное —
укрупнённые группы (Body / Eyes / Face / Hair / Skin) с КОНКРЕТНЫМИ
выбранными тегами внутри, а не счётчики категорий (это не дублирует центр).
Группы совпадают с цветами CategoryColors из theme.py.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QFontMetrics
from ui_qt.components.flow_layout import FlowLayout
from ui_qt.icon_manager import IconManager


# ── Цвета групп (с безопасным fallback на §11.6) ──
try:
    from ui_qt.theme import CategoryColors as _CC
    def _g(name, fb):
        return getattr(_CC, name, fb)
except Exception:
    def _g(name, fb):
        return fb

_BODY = _g("BODY", "#f472b6")
_EYES = _g("EYES", "#fbbf24")
_FACE = _g("FACE", "#a78bfa")
_HAIR = _g("HAIR", "#34d399")
_SKIN = _g("SKIN", "#fb923c")

# Укрупнённые группы: (название, цвет, [категории DNA])
_GROUPS = [
    ("Body", _BODY, ["Body Type", "Body Features"]),
    ("Eyes", _EYES, ["Eye Color", "Eye Shape"]),
    ("Face", _FACE, ["Face Features"]),
    ("Hair", _HAIR, ["Hair Style", "Hair Color", "Hair Length"]),
    ("Skin", _SKIN, ["Skin Tone"]),
]


def _rgba(hex_color: str, alpha: float) -> QColor:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    c = QColor(r, g, b)
    c.setAlphaF(alpha)
    return c


# ═══════════════════════════════════════════════
# MINI TAG — read-only пилюля тега (без крестика)
# ═══════════════════════════════════════════════
class _MiniTag(QFrame):
    """Маленькая пилюля-тег для summary. Фон рисуем вручную => капсула гарантирована."""
    def __init__(self, text: str, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedHeight(20)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(9, 0, 9, 0)
        lay.setSpacing(0)
        label = QLabel(text)
        label.setStyleSheet(
            "color: #e6e9f0; background: transparent; font-size: 11px;"
        )
        lay.addWidget(label)

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        except Exception:
            pass
        w, h = float(self.width()), float(self.height())
        r = h / 2.0
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, w, h, r, r)
        p.fillPath(path, _rgba(self._color, 0.15))
        p.setPen(Qt.PenStyle.NoPen)
        p.end()


# ═══════════════════════════════════════════════
# PORTRAIT PLACEHOLDER
# ═══════════════════════════════════════════════
class _PortraitPlaceholder(QFrame):
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
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setAlignment(Qt.AlignCenter)
        icon = QLabel(IconManager.get('user'))
        icon.setStyleSheet(
            "font-size: 48px; color: #5a6378; background: transparent; border: none;"
        )
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)
        text = QLabel("Add portrait")
        text.setStyleSheet(
            "color: #98a0b3; font-size: 12px; background: transparent; border: none;"
        )
        text.setAlignment(Qt.AlignCenter)
        lay.addWidget(text)


# ═══════════════════════════════════════════════
# SUMMARY PANEL
# ═══════════════════════════════════════════════
class SummaryPanel(QWidget):
    scroll_to_category = Signal(str)  # пока не используется, зарезервировано

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setMaximumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Портрет
        self.portrait = _PortraitPlaceholder()
        layout.addWidget(self.portrait)

        # Имя + общий бейдж
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self.name_label = QLabel("No profile selected")
        self.name_label.setStyleSheet(
            "color: #e6e9f0; font-size: 16px; font-weight: 600; background: transparent;"
        )
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
        layout.addWidget(header)

        # Разделитель
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #313a4d; max-height: 1px;")
        layout.addWidget(divider)

        # Заголовок секции
        section_label = QLabel("CHARACTER SUMMARY")
        section_label.setStyleSheet(
            "color: #98a0b3; font-size: 11px; font-weight: 600; "
            "letter-spacing: 0.5px; background: transparent;"
        )
        layout.addWidget(section_label)

        # Скроллируемая область с группами
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._groups_widget = QWidget()
        self._groups_widget.setStyleSheet("background: transparent;")
        self._groups_layout = QVBoxLayout(self._groups_widget)
        self._groups_layout.setContentsMargins(0, 0, 0, 0)
        self._groups_layout.setSpacing(14)
        self._groups_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._groups_widget)
        layout.addWidget(scroll, 1)

        # Стартовое пустое состояние
        self._render_groups([])

    # ── публичный API ──
    def set_profile_name(self, name: str):
        self.name_label.setText(name if name else "No profile selected")

    def update_summary(self, selected_tags: list):
        """selected_tags: list[dict] вида {'tag': str, 'category': str}."""
        total = len(selected_tags)
        self.total_badge.setText(f"{total} traits" if total else "0 traits")
        self._render_groups(selected_tags)

    # ── внутреннее ──
    def _render_groups(self, selected_tags: list):
        # очищаем
        while self._groups_layout.count():
            it = self._groups_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        any_group = False
        for group_name, color, cats in _GROUPS:
            tags = [e.get('tag', '') for e in selected_tags if e.get('category') in cats]
            if not tags:
                continue
            any_group = True
            self._groups_layout.addWidget(self._build_group(group_name, color, tags))

        if not any_group:
            empty = QLabel("No traits selected yet")
            empty.setStyleSheet(
                "color: #5a6378; font-size: 12px; font-style: italic; "
                "background: transparent;"
            )
            empty.setAlignment(Qt.AlignCenter)
            self._groups_layout.addWidget(empty)

        self._groups_layout.addStretch(1)

    def _build_group(self, group_name: str, color: str, tags: list) -> QWidget:
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        vlay = QVBoxLayout(wrap)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(8)

        # Заголовок группы: буллета + имя
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        bullet = QLabel("●")
        bullet.setStyleSheet(
            f"color: {color}; font-size: 10px; background: transparent;"
        )
        head.addWidget(bullet)
        title = QLabel(group_name)
        title.setStyleSheet(
            "color: #e6e9f0; font-size: 12px; font-weight: 600; background: transparent;"
        )
        head.addWidget(title)
        head.addStretch(1)
        vlay.addLayout(head)

        # Поток пилюль-тегов
        flow_host = QWidget()
        flow_host.setStyleSheet("background: transparent;")
        flow = FlowLayout(flow_host, margin=0, h_spacing=6, v_spacing=6)
        for tag in tags:
            flow.addWidget(_MiniTag(tag.replace('_', ' '), color))
        vlay.addWidget(flow_host)

        return wrap