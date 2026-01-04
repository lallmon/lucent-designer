"""Font provider for exposing system fonts to QML."""

from typing import List, Optional
from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QFontDatabase


class FontProvider(QObject):
    """Provides a list of available system fonts to QML."""

    fontsChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._fonts: List[str] = []
        self._load_fonts()

    def _load_fonts(self) -> None:
        """Load available font families from the system."""
        # Get all font families from the system
        all_families = QFontDatabase.families()

        # Filter to include only reasonable fonts (exclude symbol/dingbat fonts)
        # and sort alphabetically
        filtered_fonts: List[str] = []
        for family in all_families:
            # Skip fonts that are likely symbol or special fonts
            lower_name = family.lower()
            if any(
                skip in lower_name
                for skip in ["symbol", "dingbat", "wingding", "webding", "emoji"]
            ):
                continue
            filtered_fonts.append(family)

        # Sort alphabetically, case-insensitive
        self._fonts = sorted(filtered_fonts, key=str.lower)

    def get_fonts(self) -> List[str]:
        """Return the list of available font families."""
        return self._fonts

    fonts = Property(list, get_fonts, notify=fontsChanged)  # type: ignore[assignment]

    @Slot(result=int)
    def fontCount(self) -> int:
        """Return the number of available fonts."""
        return len(self._fonts)

    @Slot(str, result=int)
    def indexOf(self, font_family: str) -> int:
        """Return the index of a font family, or 0 if not found."""
        try:
            return self._fonts.index(font_family)
        except ValueError:
            # If exact match not found, try case-insensitive search
            lower_family = font_family.lower()
            for i, font in enumerate(self._fonts):
                if font.lower() == lower_family:
                    return i
            return 0

    @Slot(result=str)
    def defaultFont(self) -> str:
        """Return a sensible default font family."""
        # Try to find a good default sans-serif font
        preferred = [
            "Ubuntu",
            "Noto Sans",
            "DejaVu Sans",
            "Liberation Sans",
            "Arial",
            "Helvetica",
            "Sans Serif",
        ]
        for pref in preferred:
            if pref in self._fonts:
                return pref
        # Fall back to first font or empty string
        return self._fonts[0] if self._fonts else ""
