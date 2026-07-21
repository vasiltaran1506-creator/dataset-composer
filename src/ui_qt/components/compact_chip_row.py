"""CompactChipRow — однострочный ряд чипов с переполнением (§6.5 + §8.25 Compact).
Цвет пилюли берётся через _resolve_color: сначала descriptor['color'],
иначе маппинг по descriptor['variant'], иначе синий акцент. Форма-капсула
рисуется вручную через QPainterPath => не зависит от border-radius в QSS.
"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen
from ui_qt.icon_manager import IconManager


# ── variant -> цвет (fallback, если descriptor не несёт 'color') ──
_VARIANT_COLOR = {
    "chip-category-face": "#a78bfa",
    "chip-category-hair": "#34d399",
    "chip-category-eyes": "#fbbf24",
    "chip-category-body": "#f472b6",
    "chip-category-skin": "#fb923c",
    "chip-success": "#3dd68c",
    "chip-danger": "#f5475b",
    "chip-warning": "#f5a623",
    "chip": "#4f6df5",
}


def _resolve_color(descriptor: dict) -> str:
    """Приоритет: явный 'color' в дескрипторе, иначе маппинг по 'variant'."""
    color = descriptor.get("color")
    if color:
        return color
    return _VARIANT_COLOR.get(descriptor.get("variant", ""), "#4f6df5")


# ═══════════════════════════════════════════════
# CHIP WIDGET — пилюля, рисуемая вручную (§8.25)
# ═══════════════════════════════════════════════
class ChipWidget(QFrame):
    """Пилюля-чип. Фон (tint 15%) + рамка (30%) + левая полоска (полный цвет)
    рисуются скруглённым QPainterPath => капсула гарантирована."""
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color or "#4f6df5"

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        except Exception:
            pass
        w, h = float(self.width()), float(self.height())
        r = h / 2.0  # fully rounded => капсула

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)

        bg = QColor(self._color)
        bg.setAlphaF(0.15)
        p.fillPath(path, bg)

        border = QColor(self._color)
        border.setAlphaF(0.30)
        pen = QPen(border)
        pen.setWidthF(1.0)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        p.save()
        p.setClipPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillRect(QRectF(0, 0, 3.0, h), QColor(self._color))
        p.restore()
        p.end()


# ═══════════════════════════════════════════════
# COMPACT ROW — одна строка + overflow-индикатор
# ═══════════════════════════════════════════════
class CompactChipRow(QWidget):
    """Однострочный compact-ряд чипов с overflow-индикатором и popup."""
    remove_requested = Signal(object)

    _CHIP_H = 22
    _ROW_H = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self._ROW_H)
        self._chips = []
        self._chip_widgets = []
        self._popup = None
        self._popup_list_layout = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self._empty = QLabel("—")
        self._empty.setObjectName("Subtitle")
        self._layout.addWidget(self._empty, 0, Qt.AlignVCenter)

        self._indicator = QPushButton("")
        self._indicator.setProperty("variant", "chip-overflow")
        self._indicator.setCursor(Qt.PointingHandCursor)
        self._indicator.setFixedSize(self._CHIP_H, self._CHIP_H)
        self._indicator.hide()
        self._indicator.clicked.connect(self._show_popup)
        self._layout.addWidget(self._indicator, 0, Qt.AlignVCenter)

        self._layout.addStretch(1)

    def set_empty_text(self, text: str):
        self._empty.setText(text)

    def set_chips(self, descriptors: list):
        for w in self._chip_widgets:
            self._layout.removeWidget(w)
            w.deleteLater()
        self._chip_widgets = []
        self._chips = list(descriptors)
        for d in self._chips:
            chip = self._build_chip_widget(d)
            idx = self._layout.indexOf(self._indicator)
            self._layout.insertWidget(idx, chip, 0, Qt.AlignVCenter)
            self._chip_widgets.append(chip)
        if self._popup is not None and self._popup.isVisible():
            self._populate_popup()
        QTimer.singleShot(0, self._relayout)

    def _build_chip_widget(self, descriptor: dict) -> QWidget:
        color = _resolve_color(descriptor)
        chip = ChipWidget(color)
        chip.setFixedHeight(self._CHIP_H)
        chip.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        lay = QHBoxLayout(chip)
        lay.setContentsMargins(10, 0, 4, 0)  # слева отступ под полоску
        lay.setSpacing(4)

        label = QLabel(descriptor.get("text", ""))
        lay.addWidget(label)

        close = QPushButton(IconManager.get('close'))
        close.setProperty("variant", "chip-remove")
        close.setFixedSize(14, 14)
        close.setCursor(Qt.PointingHandCursor)
        payload = descriptor.get("payload")
        close.clicked.connect(
            lambda checked=False, p=payload: self.remove_requested.emit(p)
        )
        lay.addWidget(close)
        return chip

    def _relayout(self):
        self._empty.setVisible(not self._chips)
        if not self._chip_widgets:
            self._indicator.hide()
            return
        avail = self.width()
        if avail <= 0:
            return
        spacing = self._layout.spacing()
        widths = [w.sizeHint().width() for w in self._chip_widgets]
        shown = len(widths)
        for _ in range(4):
            if shown >= len(widths):
                reserve = 0
            else:
                reserve = self._measure_indicator(f"+{len(widths) - shown}") + spacing
            budget = avail - reserve
            n = 0
            acc = 0
            for wd in widths:
                add = wd + (spacing if n > 0 else 0)
                if acc + add <= budget:
                    acc += add
                    n += 1
                else:
                    break
            if reserve == 0:
                if n >= len(widths):
                    for w in self._chip_widgets:
                        w.show()
                    self._indicator.hide()
                    return
                shown = n
                continue
            if n == shown:
                break
            shown = n
        for i, w in enumerate(self._chip_widgets):
            w.setVisible(i < shown)
        hidden = len(widths) - shown
        self._indicator.setText(f"+{hidden}")
        self._indicator.adjustSize()
        self._indicator.show()

    def _measure_indicator(self, text: str) -> int:
        self._indicator.setText(text)
        self._indicator.adjustSize()
        return self._indicator.sizeHint().width()

    def _show_popup(self):
        if self._popup is not None and self._popup.isVisible():
            self._populate_popup()
            return
        self._popup = QWidget(self, Qt.Popup | Qt.FramelessWindowHint)
        self._popup.setObjectName("ChipOverflowPopup")
        outer = QVBoxLayout(self._popup)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)
        title = QLabel(f"All selected ({len(self._chips)})")
        title.setObjectName("Subtitle")
        outer.addWidget(title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(320)
        inner = QWidget()
        self._popup_list_layout = QVBoxLayout(inner)
        self._popup_list_layout.setContentsMargins(0, 0, 0, 0)
        self._popup_list_layout.setSpacing(6)
        self._popup_list_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        self._populate_popup()
        w = max(240, min(self.width() or 300, 360))
        self._popup.setFixedWidth(w)
        self._popup.adjustSize()
        gp = self.mapToGlobal(QPoint(0, self.height() + 4))
        self._popup.move(gp)
        self._popup.show()

    def _populate_popup(self):
        if self._popup_list_layout is None:
            return
        while self._popup_list_layout.count():
            it = self._popup_list_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for d in self._chips:
            chip = self._build_chip_widget(d)
            self._popup_list_layout.addWidget(chip, 0, Qt.AlignLeft)
        self._popup_list_layout.addStretch(1)
        if self._popup is not None:
            self._popup.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def showEvent(self, event):
        super().showEvent(event)
        self._relayout()