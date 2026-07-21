"""CategoryCard — accordion-карточка категории DNA (§6.4 + §8.24)
с вложенным grid кликабельных плиток (§6.7 grid-cell + §8.26).
Цвета категории — через _CAT_FULL / _rgba (robust, без жёсткой зависимости от theme.py).
Статический вид карточки — через variant + theme.qss.
Счётчик 'N selected' — _PillLabel (капсула рисуется вручную в paintEvent).
"""
from PySide6.QtWidgets import (QFrame, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QSizePolicy)
# QGraphicsOpacityEffect в PySide6 (Qt6) живёт в QtWidgets, НЕ в QtGui.
try:
    from PySide6.QtWidgets import QGraphicsOpacityEffect
except ImportError:
    QGraphicsOpacityEffect = None
# QRectF / QSize в Qt6 живут в QtCore (НЕ в QtGui!).
from PySide6.QtCore import (Qt, Signal, QSize, QRectF, QPropertyAnimation,
                            QEasingCurve, QParallelAnimationGroup,
                            QSequentialAnimationGroup, QPauseAnimation)
# QPainter / QPainterPath / QColor / QFont / QFontMetrics — в QtGui.
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QFontMetrics
from ui_qt.components.flow_layout import FlowLayout
from ui_qt.icon_manager import IconManager


# ── Цвета категорий (с безопасным fallback на §11.6) ──
try:
    from ui_qt.theme import CategoryColors as _CC
    def _g(name, fb):
        return getattr(_CC, name, fb)
except Exception:
    def _g(name, fb):
        return fb

_CAT_FULL = {
    "Body Type":     _g("BODY", "#f472b6"),
    "Body Features": _g("BODY", "#f472b6"),
    "Eye Color":     _g("EYES", "#fbbf24"),
    "Eye Shape":     _g("EYES", "#fbbf24"),
    "Face Features": _g("FACE", "#a78bfa"),
    "Hair Style":    _g("HAIR", "#34d399"),
    "Hair Color":    _g("HAIR", "#34d399"),
    "Hair Length":   _g("HAIR", "#34d399"),
    "Skin Tone":     _g("SKIN", "#fb923c"),
}

_CAT_KEY = {
    "Body Type": "body", "Body Features": "body",
    "Eye Color": "eyes", "Eye Shape": "eyes",
    "Face Features": "face",
    "Hair Style": "hair", "Hair Color": "hair", "Hair Length": "hair",
    "Skin Tone": "skin",
}


def _rgba(hex_color: str, alpha: float) -> str:
    """#rrggbb + alpha -> rgba(...)"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def category_full(name: str) -> str:
    return _CAT_FULL.get(name, _g("FACE", "#a78bfa"))


def category_chip_variant(name: str) -> str:
    return f"chip-category-{_CAT_KEY.get(name, 'face')}"


# ═══════════════════════════════════════════════
# PILL BADGE — счётчик-пилюля 'N selected' (§8.24 counter)
# ═══════════════════════════════════════════════
class _PillLabel(QFrame):
    """Счётчик в виде овальной капсулы. Фон рисуем вручную через QPainterPath,
    потому что кастомный tint-фон надёжнее отрисовать самим, чем полагаться на QSS."""
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self._text = ""
        f = self.font()
        f.setPixelSize(11)
        f.setWeight(QFont.Weight.DemiBold)
        self.setFont(f)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def setText(self, text: str):
        self._text = text
        self.updateGeometry()
        self.update()

    def text(self) -> str:
        return self._text

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._text) + 20
        h = fm.height() + 6
        return QSize(max(w, 12), h)

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        except Exception:
            pass
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2.0  # половина высоты => капсула
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        bg = QColor(self._color)
        bg.setAlphaF(0.15)
        p.fillPath(path, bg)
        p.setPen(QColor(self._color))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self._text)
        p.end()


# ═══════════════════════════════════════════════
# CHECK CELL — кликабельная плитка тега (§8.26 grid-cell)
# ═══════════════════════════════════════════════
class CheckCell(QFrame):
    """Плитка тега. Кликабельна вся. Выбор = цвет категории."""
    clicked = Signal(bool)

    def __init__(self, tag: str, color_full: str, parent=None):
        super().__init__(parent)
        self.tag = tag
        self._color = color_full
        self._selected = False
        self.setObjectName("CheckCell")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(140)
        self.setProperty("selected", "false")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        self._indicator = QLabel("○")
        self._indicator.setFixedWidth(14)
        self._indicator.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._indicator)

        self._label = QLabel(tag.replace('_', ' '))
        self._label.setWordWrap(False)
        lay.addWidget(self._label, 1)

        self._apply_style()

    def set_selected(self, selected: bool, emit_signal: bool = False):
        if self._selected == selected:
            return
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self._apply_style()
        if emit_signal:
            self.clicked.emit(selected)

    def is_selected(self) -> bool:
        return self._selected

    def _apply_style(self):
        if self._selected:
            self._indicator.setText("●")
            self._indicator.setStyleSheet(f"color: {self._color}; font-size: 12px;")
            self.setStyleSheet(f"""
                QFrame#CheckCell {{
                    background-color: {_rgba(self._color, 0.15)};
                    border: 1px solid {_rgba(self._color, 0.50)};
                    border-radius: 9999px;
                }}
                QFrame#CheckCell:hover {{
                    background-color: {_rgba(self._color, 0.22)};
                }}
                QLabel {{ color: #e6e9f0; }}
            """)
        else:
            self._indicator.setText("○")
            self._indicator.setStyleSheet("color: #98a0b3; font-size: 12px;")
            self.setStyleSheet("""
                QFrame#CheckCell {
                    background-color: #1f2738;
                    border: 1px solid #313a4d;
                    border-radius: 9999px;
                }
                QFrame#CheckCell:hover {
                    background-color: #283145;
                    border: 1px solid rgba(79, 109, 245, 0.50);
                }
                QLabel { color: #e6e9f0; }
            """)

    def mousePressEvent(self, event):
        self.set_selected(not self._selected, emit_signal=True)
        super().mousePressEvent(event)


# ═══════════════════════════════════════════════
# CATEGORY CARD — аккордеон-карточка (§8.24)
# ═══════════════════════════════════════════════
class CategoryCard(QFrame):
    """Аккордеон-карточка одной DNA-категории."""
    toggled = Signal(str, bool)

    def __init__(self, category_name: str, description: str,
                 tags: list, selected_tags: set, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self._color = category_full(category_name)
        self._tags = list(tags)
        self._cells: dict = {}
        self._expanded = False
        self._anim = None

        self.setObjectName("CategoryCard")
        self.setProperty("variant", "card")
        self.setStyleSheet("""
            QFrame#CategoryCard {
                background-color: #1f2738;
                border: 1px solid #313a4d;
                border-radius: 12px;
            }
        """)

        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self._accent_bar = QFrame()
        self._accent_bar.setFixedWidth(3)
        self._accent_bar.setStyleSheet(
            f"background-color: {self._color}; border-radius: 2px;"
        )
        self._accent_bar.hide()
        card_layout.addWidget(self._accent_bar)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        header = QWidget()
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header.setCursor(Qt.PointingHandCursor)
        header.setStyleSheet("background: transparent;")

        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(16, 12, 16, 12)
        hlay.setSpacing(12)

        badge = QFrame()
        badge.setFixedSize(16, 16)
        badge.setStyleSheet(
            f"background-color: {self._color}; border-radius: 4px;"
        )
        hlay.addWidget(badge)

        titles = QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(2)
        t = QLabel(category_name)
        t.setObjectName("CategoryTitle")
        titles.addWidget(t)
        d = QLabel(description)
        d.setObjectName("Subtitle")
        titles.addWidget(d)
        hlay.addLayout(titles, 1)

        # Счётчик — овальная пилюля, рисуемая вручную
        self._counter = _PillLabel(self._color)
        self._counter.setText("0 selected")
        hlay.addWidget(self._counter)

        self._chevron = QLabel(IconManager.get('chevron-right'))
        self._chevron.setObjectName("Subtitle")
        hlay.addWidget(self._chevron)

        header.mousePressEvent = lambda e: self.toggle()
        body.addWidget(header)

        self._content = QWidget()
        self._content.setMaximumHeight(0)
        self._content.hide()

        self._grid = FlowLayout(self._content, margin=16, h_spacing=8, v_spacing=8)
        for tag in self._tags:
            cell = CheckCell(tag, self._color)
            cell.clicked.connect(lambda sel, tg=tag: self._on_cell(tg, sel))
            self._cells[tag] = cell
            self._grid.addWidget(cell)

        # Opacity-эффект для fade (если доступен в этой сборке PySide6)
        self._opacity = None
        if QGraphicsOpacityEffect is not None:
            self._opacity = QGraphicsOpacityEffect(self._content)
            self._opacity.setOpacity(0.0)
            self._content.setGraphicsEffect(self._opacity)

        body.addWidget(self._content)
        card_layout.addLayout(body, 1)

        if selected_tags:
            self.set_selected_set(selected_tags)

    # ── публичный API ──
    def all_tags(self) -> list:
        return list(self._tags)

    def set_selected_set(self, tags: set):
        for tag, cell in self._cells.items():
            cell.set_selected(tag in tags, emit_signal=False)
        self._update_counter()

    def set_filter(self, text: str) -> bool:
        fl = text.strip().lower()
        if not fl:
            for cell in self._cells.values():
                cell.setVisible(True)
            self.set_expanded(False, animate=False)
            return False
        any_visible = False
        for tag, cell in self._cells.items():
            match = fl in tag.lower()
            cell.setVisible(match)
            if match:
                any_visible = True
        self.set_expanded(any_visible, animate=False)
        return any_visible

    def set_expanded(self, expanded: bool, animate: bool = True):
        if expanded == self._expanded and self._content.isVisible() == expanded:
            return
        self._expanded = expanded
        self._chevron.setText(
            IconManager.get('chevron-down') if expanded else IconManager.get('chevron-right')
        )
        if expanded:
            self._accent_bar.show()
            self._expand(animate)
        else:
            self._accent_bar.hide()
            self._collapse(animate)

    def toggle(self):
        self.set_expanded(not self._expanded, animate=True)

    # ── внутреннее ──
    def _on_cell(self, tag: str, selected: bool):
        self._update_counter()
        self.toggled.emit(tag, selected)

    def _update_counter(self):
        n = sum(1 for c in self._cells.values() if c.is_selected())
        self._counter.setText(f"{n} selected" if n else "0 selected")

    def _target_height(self) -> int:
        w = self._content.width()
        if w <= 0:
            w = 600
        return self._content.heightForWidth(w)

    def _expand(self, animate: bool):
        self._content.setMaximumHeight(0)
        self._content.show()
        if not animate:
            self._content.setMaximumHeight(16777215)
            if self._opacity is not None:
                self._opacity.setOpacity(1.0)
            return
        target = self._target_height()
        self._stop_anim()

        h_anim = QPropertyAnimation(self._content, b"maximumHeight")
        h_anim.setDuration(220)
        h_anim.setStartValue(0)
        h_anim.setEndValue(target)
        h_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if self._opacity is not None:
            o_anim = QPropertyAnimation(self._opacity, b"opacity")
            o_anim.setDuration(160)
            o_anim.setStartValue(0.0)
            o_anim.setEndValue(1.0)
            o_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            fade_seq = QSequentialAnimationGroup(self)
            fade_seq.addPause(60)
            fade_seq.addAnimation(o_anim)
            self._anim = QParallelAnimationGroup(self)
            self._anim.addAnimation(h_anim)
            self._anim.addAnimation(fade_seq)
        else:
            self._anim = QParallelAnimationGroup(self)
            self._anim.addAnimation(h_anim)

        self._anim.finished.connect(lambda: self._content.setMaximumHeight(16777215))
        self._anim.start()

    def _collapse(self, animate: bool):
        if not animate:
            self._content.setMaximumHeight(0)
            self._content.hide()
            if self._opacity is not None:
                self._opacity.setOpacity(0.0)
            return
        self._stop_anim()

        cur = self._content.height()
        h_anim = QPropertyAnimation(self._content, b"maximumHeight")
        h_anim.setDuration(200)
        h_anim.setStartValue(cur)
        h_anim.setEndValue(0)
        h_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if self._opacity is not None:
            o_anim = QPropertyAnimation(self._opacity, b"opacity")
            o_anim.setDuration(120)
            o_anim.setStartValue(self._opacity.opacity())
            o_anim.setEndValue(0.0)
            o_anim.setEasingCurve(QEasingCurve.Type.InCubic)
            self._anim = QParallelAnimationGroup(self)
            self._anim.addAnimation(h_anim)
            self._anim.addAnimation(o_anim)
        else:
            self._anim = QParallelAnimationGroup(self)
            self._anim.addAnimation(h_anim)

        self._anim.finished.connect(self._content.hide)
        self._anim.start()

    def _stop_anim(self):
        if self._anim is not None:
            self._anim.stop()
            self._anim = None