"""Tests for FontProvider class."""

from lucent.font_provider import FontProvider


class TestFontProvider:
    """Tests for FontProvider class."""

    def test_provider_creates_font_list(self, qtbot):
        """FontProvider should create a list of fonts."""
        provider = FontProvider()
        fonts = provider.get_fonts()
        assert isinstance(fonts, list)
        assert len(fonts) > 0

    def test_fonts_are_sorted(self, qtbot):
        """Font list should be sorted alphabetically."""
        provider = FontProvider()
        fonts = provider.get_fonts()
        sorted_fonts = sorted(fonts, key=str.lower)
        assert fonts == sorted_fonts

    def test_font_count_matches_list(self, qtbot):
        """fontCount should return length of font list."""
        provider = FontProvider()
        assert provider.fontCount() == len(provider.get_fonts())

    def test_index_of_existing_font(self, qtbot):
        """indexOf should return correct index for existing font."""
        provider = FontProvider()
        fonts = provider.get_fonts()
        if len(fonts) > 0:
            first_font = fonts[0]
            assert provider.indexOf(first_font) == 0

    def test_index_of_missing_font_returns_zero(self, qtbot):
        """indexOf should return 0 for non-existent font."""
        provider = FontProvider()
        assert provider.indexOf("NonExistentFontXYZ123") == 0

    def test_index_of_case_insensitive(self, qtbot):
        """indexOf should be case-insensitive."""
        provider = FontProvider()
        fonts = provider.get_fonts()
        if len(fonts) > 0:
            first_font = fonts[0]
            assert provider.indexOf(first_font.upper()) == 0
            assert provider.indexOf(first_font.lower()) == 0

    def test_default_font_returns_string(self, qtbot):
        """defaultFont should return a string."""
        provider = FontProvider()
        default = provider.defaultFont()
        assert isinstance(default, str)
        if provider.get_fonts():
            assert default in provider.get_fonts()

    def test_fonts_property_accessible(self, qtbot):
        """fonts property should be accessible."""
        provider = FontProvider()
        fonts = provider.fonts
        assert isinstance(fonts, list)
        assert len(fonts) == provider.fontCount()

    def test_symbol_fonts_excluded(self, qtbot):
        """Symbol and dingbat fonts should be excluded."""
        provider = FontProvider()
        fonts = provider.get_fonts()
        for font in fonts:
            lower = font.lower()
            assert "symbol" not in lower
            assert "dingbat" not in lower
            assert "wingding" not in lower
            assert "webding" not in lower
