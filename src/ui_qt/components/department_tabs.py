"""DepartmentTabs — ряд пилюль-отделов гардероба (Паттерн 1 для Outfits).
Цвета/порядок/подписи берутся из theme.WardrobeColors (с fallback-словарём,
чтобы импорт не уронил программу, если класс ещё не заведён).
"""
from PySide6.QtWidgets import (QFrame, QWidget, QHBoxLayout, QLabel,
                               QSizePolicy)
from PySide6.QtCore import Qt, Signal

# ── Палитра отделов: из theme, иначе локальный fallback (§11.6 расшир.) ──
try:
    from ui_qt.theme import WardrobeColors as _WC
    def _wc_get(key):
        return _WC.get(key)
    def _wc_label(key):
        return getattr(_WC, "LABELS", {}).get(key, key.replace('_', ' ').title())
    _WC_ORDER = list(getattr(_WC, "ORDER", []))
except Exception:
    _FB = {
        "full_body": "#a78bfa", "topwear": "#38bdf8", "bottomwear": "#34d399",
        "legwear": "#fbbf24", "footwear": "#fb923c", "underwear": "#f472b6",
        "accessories": "#22d3ee",
    }
    _FB_L = {
        "full_body": "Full Body", "topwear": "Topwear", "bottomwear": "Bottomwear",
        "legwear": "Legwear", "footwear": "Footwear", "underwear": "Underwear",
        "accessories": "Accessories",
    }
    def _wc_get(key):
        return _FB.get(key, "#4f6df5")
    def _wc_label(key):
        return _FB_L.get(key, key.replace('_', ' ').title())
    _WC_ORDER = list(_FB.keys())

# Порядок по умолчанию, если реестр пуст
_DEFAULT_ORDER = _WC_ORDER or [
    "full_body", "topwear", "bottomwear", "legwear",
    "footwear", "underwear", "accessories",
]


def _tint(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ═══════════════════════════════════════════════
# ОДНА ПИЛЮЛЯ-ОТДЕЛ
# ═══════════════════════════════════════════════
class _DeptPill(QFrame):
    clicked = Signal()

    def __init__(self, key: str, label: str, color: str, parent=None):
        super().__init__(parent)
        self.key = key
        self._color = color
        self._active = False
        # objectName нужен, чтобы селектор QFrame#DeptPill НЕ затрагивал
        # QLabel-потомков (точка и текст) — иначе они унаследуют рамку.
        self.setObjectName("DeptPill")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)

        self._bullet = QLabel("●")
        self._bullet.setStyleSheet(
            f"color: {color}; font-size: 9px; background: transparent; border: none;"
        )
        lay.addWidget(self._bullet)

        self._label = QLabel(label)
        self._label.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self._label)

        self._apply()

    def set_active(self, active: bool):
        if self._active == active:
            return
        self._active = active
        self._apply()

    def _apply(self):
        c = self._color
        if self._active:
            # Селектор с #id => рамка только на самой пилюле, не на потомках.
            self.setStyleSheet(f"""
                QFrame#DeptPill {{
                    background-color: {_tint(c, 0.15)};
                    border: 1px solid {_tint(c, 0.40)};
                    border-bottom: 2px solid {c};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#DeptPill {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-bottom: 2px solid transparent;
                    border-radius: 8px;
                }
                QFrame#DeptPill:hover { background-color: #283145; }
            """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ═══════════════════════════════════════════════
# РЯД ОТДЕЛОВ
# ═══════════════════════════════════════════════
class DepartmentTabs(QWidget):
    department_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pills = {}
        self._active = None
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)

    def set_departments(self, keys=None):
        for p in self._pills.values():
            self._layout.removeWidget(p)
            p.deleteLater()
        self._pills.clear()
        while self._layout.count():
            self._layout.takeAt(0)

        order = keys if keys else _DEFAULT_ORDER
        for key in order:
            label = _wc_label(key)
            color = _wc_get(key)
            pill = _DeptPill(key, label, color)
            pill.clicked.connect(lambda k=key: self._on_click(k))
            self._pills[key] = pill
            self._layout.addWidget(pill, 0, Qt.AlignVCenter)
        self._layout.addStretch(1)

        if order:
            self.set_active(self._active if self._active in self._pills else order[0])

    def set_active(self, key: str):
        if key not in self._pills:
            return
        self._active = key
        for k, pill in self._pills.items():
            pill.set_active(k == key)

    def active(self) -> str:
        return self._active

    def _on_click(self, key: str):
        self.set_active(key)
        self.department_changed.emit(key)