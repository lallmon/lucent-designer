# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TextureCache - rasterizes canvas items to GPU-ready textures."""

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage

from lucent.texture_cache import TextureCache, TextureCacheEntry
from lucent.canvas_items import RectangleItem, EllipseItem, ArtboardItem, GroupItem
from lucent.geometry import RectGeometry, EllipseGeometry
from lucent.appearances import Fill, Stroke
from lucent.transforms import Transform


def make_rect_item(
    x: float = 0,
    y: float = 0,
    width: float = 100,
    height: float = 100,
    fill_color: str = "#ff0000",
    stroke_color: str = "#000000",
    stroke_width: float = 1.0,
) -> RectangleItem:
    """Create a test rectangle item."""
    return RectangleItem(
        name="TestRect",
        geometry=RectGeometry(x, y, width, height),
        appearances=[
            Fill(color=fill_color),
            Stroke(color=stroke_color, width=stroke_width),
        ],
        transform=Transform(),
        visible=True,
        locked=False,
    )


def make_ellipse_item(
    x: float = 0,
    y: float = 0,
    width: float = 100,
    height: float = 100,
) -> EllipseItem:
    """Create a test ellipse item."""
    return EllipseItem(
        name="TestEllipse",
        geometry=EllipseGeometry(x, y, width, height),
        appearances=[Fill(color="#00ff00")],
        transform=Transform(),
        visible=True,
        locked=False,
    )


class TestTextureCacheEntry:
    """Tests for TextureCacheEntry data class."""

    def test_entry_stores_image_bounds_version(self):
        """Entry stores image, bounds, and version."""
        image = QImage(100, 100, QImage.Format.Format_ARGB32_Premultiplied)
        bounds = QRectF(10, 20, 100, 100)
        entry = TextureCacheEntry(image, bounds, item_version=42)

        assert entry.image is image
        assert entry.bounds == bounds
        assert entry.item_version == 42

    def test_entry_width_height_from_image(self):
        """Entry width/height properties delegate to image."""
        image = QImage(150, 200, QImage.Format.Format_ARGB32_Premultiplied)
        entry = TextureCacheEntry(image, QRectF(0, 0, 50, 50), item_version=1)

        assert entry.width == 150
        assert entry.height == 200


class TestTextureCacheBasics:
    """Tests for TextureCache basic operations."""

    def test_initial_state_empty(self):
        """Cache starts empty."""
        cache = TextureCache()
        assert len(cache._cache) == 0
        assert len(cache._item_versions) == 0

    def test_constants_defined(self):
        """Cache has expected constants."""
        assert TextureCache.PADDING == 4
        assert TextureCache.RENDER_SCALE == 2.0

    def test_clear_empties_cache(self):
        """clear() removes all entries."""
        cache = TextureCache()
        item = make_rect_item()
        cache.get_or_create(item, "test-id")

        assert len(cache._cache) > 0
        cache.clear()
        assert len(cache._cache) == 0
        assert len(cache._item_versions) == 0

    def test_invalidate_removes_entry(self):
        """invalidate() removes specific entry."""
        cache = TextureCache()
        item = make_rect_item()
        cache.get_or_create(item, "test-id")

        assert "test-id" in cache._cache
        cache.invalidate("test-id")
        assert "test-id" not in cache._cache

    def test_invalidate_nonexistent_id_no_error(self):
        """invalidate() on missing ID doesn't raise."""
        cache = TextureCache()
        cache.invalidate("nonexistent")  # Should not raise


class TestTextureCacheGetOrCreate:
    """Tests for get_or_create rasterization."""

    def test_creates_entry_for_rectangle(self):
        """Creates texture entry for rectangle item."""
        cache = TextureCache()
        item = make_rect_item(x=10, y=20, width=50, height=30)

        entry = cache.get_or_create(item, "rect-1")

        assert entry is not None
        assert isinstance(entry, TextureCacheEntry)
        assert isinstance(entry.image, QImage)
        assert not entry.image.isNull()

    def test_creates_entry_for_ellipse(self):
        """Creates texture entry for ellipse item."""
        cache = TextureCache()
        item = make_ellipse_item(x=0, y=0, width=80, height=60)

        entry = cache.get_or_create(item, "ellipse-1")

        assert entry is not None
        assert isinstance(entry.image, QImage)

    def test_returns_cached_entry_on_second_call(self):
        """Returns same entry if item unchanged."""
        cache = TextureCache()
        item = make_rect_item()

        entry1 = cache.get_or_create(item, "rect-1")
        entry2 = cache.get_or_create(item, "rect-1")

        assert entry1 is entry2

    def test_creates_entry_for_artboard(self):
        """Artboards render with a border (transparent background)."""
        cache = TextureCache()
        artboard = ArtboardItem(
            x=0, y=0, width=100, height=80, name="Artboard 1", visible=True
        )

        entry = cache.get_or_create(artboard, "artboard-1")

        assert entry is not None
        # Bounds are expanded by 2pt stroke on each side
        assert entry.bounds.width() == 104  # 100 + 2*2
        assert entry.bounds.height() == 84  # 80 + 2*2

    def test_returns_none_for_group_item(self):
        """Groups can't be textured - returns None."""
        cache = TextureCache()
        group = GroupItem(name="Group 1", visible=True, locked=False, parent_id="")

        entry = cache.get_or_create(group, "group-1")

        assert entry is None

    def test_texture_size_includes_padding_and_scale(self):
        """Texture dimensions account for padding and render scale."""
        cache = TextureCache()
        item = make_rect_item(width=100, height=50, stroke_width=0)

        entry = cache.get_or_create(item, "rect-1")

        # Expected: (width + padding*2) * scale = (100 + 8) * 2 = 216
        # Expected: (height + padding*2) * scale = (50 + 8) * 2 = 116
        assert entry.width == 216
        assert entry.height == 116

    def test_texture_bounds_include_stroke(self):
        """Entry bounds include stroke width for accurate rendering."""
        cache = TextureCache()
        item = make_rect_item(x=25, y=35, width=100, height=80, stroke_width=1.0)

        entry = cache.get_or_create(item, "rect-1")

        # Bounds should be expanded by half stroke width on each side (center align)
        assert entry.bounds.x() < 25
        assert entry.bounds.y() < 35
        assert entry.bounds.width() > 100
        assert entry.bounds.height() > 80


class TestTextureCacheVersioning:
    """Tests for cache invalidation via version tracking."""

    def test_geometry_change_invalidates_cache(self):
        """Changing geometry creates new entry."""
        cache = TextureCache()
        item = make_rect_item(width=100)

        entry1 = cache.get_or_create(item, "rect-1")

        # Modify geometry
        item.geometry = RectGeometry(0, 0, 200, 100)
        entry2 = cache.get_or_create(item, "rect-1")

        assert entry1 is not entry2

    def test_fill_color_change_invalidates_cache(self):
        """Changing fill color creates new entry."""
        cache = TextureCache()
        item = make_rect_item(fill_color="#ff0000")

        entry1 = cache.get_or_create(item, "rect-1")

        # Modify fill color
        item.fill.color = "#00ff00"
        entry2 = cache.get_or_create(item, "rect-1")

        assert entry1 is not entry2

    def test_stroke_change_invalidates_cache(self):
        """Changing stroke properties creates new entry."""
        cache = TextureCache()
        item = make_rect_item(stroke_width=1.0)

        entry1 = cache.get_or_create(item, "rect-1")

        # Modify stroke width
        item.stroke.width = 5.0
        entry2 = cache.get_or_create(item, "rect-1")

        assert entry1 is not entry2

    def test_transform_change_does_not_invalidate(self):
        """Transform changes don't invalidate (GPU handles transforms)."""
        cache = TextureCache()
        item = make_rect_item()

        entry1 = cache.get_or_create(item, "rect-1")

        # Modify transform (GPU handles this, no re-rasterization needed)
        item.transform = Transform(rotate=45.0)
        entry2 = cache.get_or_create(item, "rect-1")

        # Same entry because transform changes don't affect rasterized texture
        assert entry1 is entry2

    def test_artboard_background_change_does_not_invalidate_cache(self):
        """Changing artboard background does not alter outline texture."""
        cache = TextureCache()
        artboard = ArtboardItem(
            x=0,
            y=0,
            width=100,
            height=80,
            name="Artboard 1",
            background_color="#ffffff",
            visible=True,
        )

        entry1 = cache.get_or_create(artboard, "artboard-1")
        artboard.background_color = "#112233"
        entry2 = cache.get_or_create(artboard, "artboard-1")

        assert entry1 is entry2


class TestTextureCacheOffsetAndSize:
    """Tests for texture offset and size calculations."""

    def test_get_texture_offset_accounts_for_padding(self):
        """Offset adjusts for padding so content aligns correctly."""
        cache = TextureCache()
        item = make_rect_item(x=100, y=50, stroke_width=0)
        entry = cache.get_or_create(item, "rect-1")

        offset = cache.get_texture_offset(entry)

        # offset = bounds - padding = (100-4, 50-4) = (96, 46)
        assert offset == (96, 46)

    def test_get_texture_size_accounts_for_scale(self):
        """Display size accounts for render scale."""
        cache = TextureCache()
        item = make_rect_item(width=100, height=50, stroke_width=0)
        entry = cache.get_or_create(item, "rect-1")

        size = cache.get_texture_size(entry)

        # size = image_size / RENDER_SCALE = (216/2, 116/2) = (108, 58)
        assert size == (108, 58)


class TestTextureCacheEdgeCases:
    """Tests for edge cases in rasterization."""

    def test_empty_bounds_returns_none(self):
        """Items with empty geometry return None."""
        cache = TextureCache()
        # Zero-size rectangle has empty bounds
        item = make_rect_item(width=0, height=0)

        entry = cache.get_or_create(item, "empty")

        assert entry is None


class TestTextureCacheRasterization:
    """Tests for the actual rasterization quality."""

    def test_image_format_is_premultiplied_alpha(self):
        """Textures use premultiplied alpha for GPU blending."""
        cache = TextureCache()
        item = make_rect_item()
        entry = cache.get_or_create(item, "rect-1")

        assert entry.image.format() == QImage.Format.Format_ARGB32_Premultiplied

    def test_rasterizes_with_identity_transform(self):
        """Item is rasterized without its transform applied."""
        cache = TextureCache()
        # Item with rotation - texture should NOT include rotation
        item = make_rect_item()
        item.transform = Transform(rotate=45.0)

        entry = cache.get_or_create(item, "rect-1")

        # Bounds should be close to original geometry (plus stroke), not rotated
        # A 45-degree rotation of 100x100 would give ~141x141 bounds
        assert entry.bounds.width() < 110  # Not rotated
        assert entry.bounds.height() < 110  # Not rotated

    def test_minimum_texture_size_enforced(self):
        """Very small items still get minimum texture size."""
        cache = TextureCache()
        # Tiny 1x1 item
        item = make_rect_item(width=1, height=1)

        entry = cache.get_or_create(item, "tiny")

        # Should be at least 4x4 (minimum size)
        assert entry.width >= 4
        assert entry.height >= 4
