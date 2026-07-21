"""
Design Tokens for Dataset Composer UI.
All visual constants are defined here and referenced throughout the codebase.

Reference: Dataset Composer UI Design System, Chapter 11 — Design Tokens
"""

from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════
# §11.1 COLOR TOKENS
# Graphite-blue palette (cool tones with subtle blue tint, no pure black)
# ═══════════════════════════════════════════════════════════════
class Colors:
    # Base palette — cold blue-graphite, anchored to concept mockup (#171d2b)
    WINDOW_BG       = "#131824"   # chrome / passe-partout (thin window edge)
    WORKSPACE_BG    = "#171d2b"   # canvas — measured from concept mockup
    SIDEBAR_BG      = "#171d2b"   # same as canvas
    CARD_BG         = "#1f2738"   # raised slabs (cards, inputs, buttons)
    CARD_ELEVATED   = "#283145"   # elevated / hover
    HOVER_SURFACE   = "#283145"
    PRESSED_SURFACE = "#313b52"
    BORDER          = "#313a4d"
    BORDER_STRONG   = "#414c63"
    DIVIDER         = "#283145"



    # Text colors
    TEXT_PRIMARY    = "#e6e9f0"
    TEXT_SECONDARY  = "#98a0b3"
    TEXT_DISABLED   = "#5a6378"
    TEXT_INVERSE    = "#131824"

    # Accent (indigo-blue)
    ACCENT          = "#4f6df5"   # indigo-blue (per design doc §11.1)
    ACCENT_HOVER    = "#6b85f7"
    ACCENT_PRESSED  = "#3d5ae0"

    # Semantic colors
    SUCCESS         = "#3dd68c"
    WARNING         = "#f5a623"
    ERROR           = "#f5475b"

    # Opacity variants (RGBA)
    ACCENT_SUBTLE        = "rgba(79, 109, 245, 0.15)"
    ACCENT_HOVER_SUBTLE  = "rgba(79, 109, 245, 0.25)"
    SUCCESS_SUBTLE       = "rgba(61, 214, 140, 0.15)"
    WARNING_SUBTLE       = "rgba(245, 166, 35, 0.15)"
    ERROR_SUBTLE         = "rgba(245, 71, 91, 0.15)"
    SELECTION       = "rgba(79, 109, 245, 0.30)"
    FOCUS_RING      = "rgba(79, 109, 245, 0.40)"
    BACKDROP             = "rgba(0, 0, 0, 0.40)"


# ═══════════════════════════════════════════════════════════════
# §11.6 CATEGORY COLOR TOKENS
# Used for DNA trait categories and similar categorical data
# ═══════════════════════════════════════════════════════════════
class CategoryColors:
    # DNA categories (Profiles workspace)
    FACE  = "#a78bfa"   # violet
    HAIR  = "#34d399"   # emerald
    EYES  = "#fbbf24"   # amber
    BODY  = "#f472b6"   # pink
    SKIN  = "#fb923c"   # coral

    FACE_SUBTLE  = "rgba(167, 139, 250, 0.15)"
    HAIR_SUBTLE  = "rgba(52, 211, 153, 0.15)"
    EYES_SUBTLE  = "rgba(251, 191, 36, 0.15)"
    BODY_SUBTLE  = "rgba(244, 114, 182, 0.15)"
    SKIN_SUBTLE  = "rgba(251, 146, 60, 0.15)"

    @classmethod
    def get_for_category(cls, category_name: str) -> tuple[str, str]:
        """Returns (full_color, subtle_color) tuple for a DNA category name."""
        mapping = {
            "Body Type":      (cls.BODY, cls.BODY_SUBTLE),
            "Body Features":  (cls.BODY, cls.BODY_SUBTLE),
            "Eye Color":      (cls.EYES, cls.EYES_SUBTLE),
            "Eye Shape":      (cls.EYES, cls.EYES_SUBTLE),
            "Face Features":  (cls.FACE, cls.FACE_SUBTLE),
            "Hair Style":     (cls.HAIR, cls.HAIR_SUBTLE),
            "Hair Color":     (cls.HAIR, cls.HAIR_SUBTLE),
            "Hair Length":    (cls.HAIR, cls.HAIR_SUBTLE),
            "Skin Tone":      (cls.SKIN, cls.SKIN_SUBTLE),
        }
        return mapping.get(category_name, (cls.FACE, cls.FACE_SUBTLE))

# ═══════════════════════════════════════════════════════════════
# §11.6 (расширение) WARDROBE / OUTFIT CATEGORY COLORS
# Цвета отделов гардероба (Profiles → Outfits). Единый источник
# истины: department_tabs.py и profiles_tab.py берут цвета отсюда.
# ═══════════════════════════════════════════════════════════════
class WardrobeColors:
    FULL_BODY   = "#a78bfa"   # violet
    TOPWEAR     = "#38bdf8"   # sky
    BOTTOMWEAR  = "#34d399"   # emerald
    LEGWEAR     = "#fbbf24"   # amber
    FOOTWEAR    = "#fb923c"   # orange
    UNDERWEAR   = "#f472b6"   # pink
    ACCESSORIES = "#22d3ee"   # cyan

    # Порядок отделов слева направо в ряде пилюль
    ORDER = [
        "full_body", "topwear", "bottomwear", "legwear",
        "footwear", "underwear", "accessories",
    ]

    # Человекочитаемые подписи отделов
    LABELS = {
        "full_body":   "Full Body",
        "topwear":     "Topwear",
        "bottomwear":  "Bottomwear",
        "legwear":     "Legwear",
        "footwear":    "Footwear",
        "underwear":   "Underwear",
        "accessories": "Accessories",
    }

    _MAP = {
        "full_body":   FULL_BODY,
        "topwear":     TOPWEAR,
        "bottomwear":  BOTTOMWEAR,
        "legwear":     LEGWEAR,
        "footwear":    FOOTWEAR,
        "underwear":   UNDERWEAR,
        "accessories": ACCESSORIES,
    }

    @classmethod
    def get(cls, department_key: str) -> str:
        """Цвет отдела по ключу; fallback — общий accent."""
        return cls._MAP.get(department_key, "#4f6df5")

# ═══════════════════════════════════════════════════════════════
# §11.2 TYPOGRAPHY TOKENS
# ═══════════════════════════════════════════════════════════════
class Typography:
    FONT_PRIMARY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    FONT_MONO    = "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"

    # Sizes (px)
    SIZE_WINDOW_TITLE   = 20
    SIZE_SECTION_TITLE  = 16
    SIZE_CATEGORY_TITLE = 14
    SIZE_BODY           = 13
    SIZE_SECONDARY      = 12
    SIZE_CAPTION        = 11

    # Weights
    WEIGHT_REGULAR  = 400
    WEIGHT_MEDIUM   = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD     = 700

    # Line heights
    LH_TIGHT    = 1.2
    LH_NORMAL   = 1.5
    LH_RELAXED  = 1.7


# ═══════════════════════════════════════════════════════════════
# §11.3 SPACING TOKENS
# 4 px base unit
# ═══════════════════════════════════════════════════════════════
class Spacing:
    SPACE_1  = 4    # tight
    SPACE_2  = 8    # default between controls
    SPACE_3  = 12   # grouped sections
    SPACE_4  = 16   # card padding
    SPACE_5  = 20   # larger separation
    SPACE_6  = 24   # workspace-level
    SPACE_8  = 32   # major breaks
    SPACE_12 = 48   # page margins


# ═══════════════════════════════════════════════════════════════
# §11.4 RADIUS TOKENS
# ═══════════════════════════════════════════════════════════════
class Radius:
    SMALL   = 8     # checkboxes, toggles
    MEDIUM  = 10    # buttons, inputs
    LARGE   = 12    # cards, panels
    XLARGE  = 14    # dialogs, modals
    FULL    = 9999  # chips, badges (fully rounded)


# ═══════════════════════════════════════════════════════════════
# §11.5 EASING TOKENS
# ═══════════════════════════════════════════════════════════════
class Easing:
    # Note: Qt QPropertyAnimation uses QEasingCurve presets, not CSS beziers.
    # We map semantic names to QEasingCurve.Type values.
    # These constants are used when constructing QPropertyAnimation objects.

    # Names for documentation purposes — actual Qt enum values
    # are referenced in code via QEasingCurve.Type
    EASE_OUT_NAME    = "OutCubic"    # Elements entering (fade-in, slide-in, expand)
    EASE_IN_NAME     = "InCubic"     # Elements leaving (fade-out, slide-out, collapse)
    EASE_IN_OUT_NAME = "InOutCubic"  # Continuous motion, state transitions
    EASE_SPRING_NAME = "OutBack"     # Playful, bouncy (rare)


# ═══════════════════════════════════════════════════════════════
# §8.2 DURATION TOKENS
# ═══════════════════════════════════════════════════════════════
class Duration:
    INSTANT = 80    # press feedback, immediate state changes
    FAST    = 120   # hover transitions, icon appearance
    NORMAL  = 160   # selection, focus, standard transitions
    SLOW    = 220   # expand/collapse, dialog appearance
    SLOWER  = 280   # complex animations, workspace transitions

    # Specialized (from §8.2)
    HOVER_MIN       = 120
    HOVER_MAX       = 160
    SELECTION_MIN   = 140
    SELECTION_MAX   = 180
    PRESS_MIN       = 80
    PRESS_MAX       = 120
    EXPAND_MIN      = 180
    EXPAND_MAX      = 220
    DIALOG_MIN      = 220
    DIALOG_MAX      = 260
    NOTIFICATION_MIN = 200
    NOTIFICATION_MAX = 250


# ═══════════════════════════════════════════════════════════════
# LAYOUT CONSTANTS (from §5.6, §7.1)
# ═══════════════════════════════════════════════════════════════
class Layout:
    # §7.1 sidebar dimensions
    SIDEBAR_MIN_WIDTH     = 240
    SIDEBAR_MAX_WIDTH     = 320
    SIDEBAR_COLLAPSED     = 56

    # Context panel dimensions (§7.4)
    CONTEXT_PANEL_WIDTH   = 320

    # §9.6 Touch targets (accessibility)
    MIN_TOUCH_TARGET      = 44
    RECOMMENDED_TOUCH     = 48

    # Focus ring (§9.2)
    FOCUS_RING_WIDTH      = 2
    FOCUS_RING_OFFSET     = 2

    # §11.3 Common patterns
    CARD_PADDING          = Spacing.SPACE_4
    ACCORDION_HEADER_V    = Spacing.SPACE_3
    ACCORDION_HEADER_H    = Spacing.SPACE_4
    BUTTON_PADDING_V      = Spacing.SPACE_2
    BUTTON_PADDING_H      = Spacing.SPACE_4
    INPUT_PADDING_V       = Spacing.SPACE_2
    INPUT_PADDING_H       = Spacing.SPACE_3
    CHIP_PADDING_V        = Spacing.SPACE_1
    CHIP_PADDING_H        = Spacing.SPACE_3