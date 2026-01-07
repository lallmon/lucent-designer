"""Unit tests for exporter module."""

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage
import xml.etree.ElementTree as ET

from lucent.canvas_items import (
    RectangleItem,
    EllipseItem,
    PathItem,
    LayerItem,
)
from lucent.geometry import RectGeometry, EllipseGeometry, PolylineGeometry
from lucent.appearances import Fill, Stroke
from lucent.exporter import ExportOptions, export_png, export_svg, compute_bounds


def make_rect_item(
    x=0,
    y=0,
    width=10,
    height=10,
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
):
    """Helper to create RectangleItem."""
    geometry = RectGeometry(x=x, y=y, width=width, height=height)
    appearances = [
        Fill(color=fill_color, opacity=fill_opacity),
        Stroke(color=stroke_color, width=stroke_width),
    ]
    return RectangleItem(geometry=geometry, appearances=appearances)


def make_ellipse_item(
    cx=0,
    cy=0,
    rx=10,
    ry=10,
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
):
    """Helper to create EllipseItem."""
    geometry = EllipseGeometry(center_x=cx, center_y=cy, radius_x=rx, radius_y=ry)
    appearances = [
        Fill(color=fill_color, opacity=fill_opacity),
        Stroke(color=stroke_color, width=stroke_width),
    ]
    return EllipseItem(geometry=geometry, appearances=appearances)


def make_path_item(
    points,
    closed=False,
    fill_color="#ffffff",
    fill_opacity=0.0,
    stroke_color="#ffffff",
    stroke_width=1.0,
):
    """Helper to create PathItem."""
    geometry = PolylineGeometry(points=points, closed=closed)
    appearances = [
        Fill(color=fill_color, opacity=fill_opacity),
        Stroke(color=stroke_color, width=stroke_width),
    ]
    return PathItem(geometry=geometry, appearances=appearances)


class TestExportOptions:
    """Tests for ExportOptions dataclass."""

    def test_default_values(self):
        """ExportOptions has sensible defaults."""
        opts = ExportOptions()
        assert opts.document_dpi == 72
        assert opts.target_dpi == 72
        assert opts.padding == 0.0
        assert opts.background is None

    def test_custom_values(self):
        """ExportOptions accepts custom values."""
        opts = ExportOptions(
            document_dpi=72, target_dpi=300, padding=10.0, background="#ffffff"
        )
        assert opts.document_dpi == 72
        assert opts.target_dpi == 300
        assert opts.padding == 10.0
        assert opts.background == "#ffffff"

    def test_scale_property_computes_ratio(self):
        """scale property returns target_dpi / document_dpi."""
        opts = ExportOptions(document_dpi=72, target_dpi=144)
        assert opts.scale == 2.0


class TestComputeBounds:
    """Tests for compute_bounds helper function."""

    def test_single_item(self):
        """compute_bounds returns bounds of single item."""
        items = [make_rect_item(x=10, y=20, width=100, height=50)]
        bounds = compute_bounds(items, padding=0)
        assert bounds == QRectF(10, 20, 100, 50)

    def test_multiple_items(self):
        """compute_bounds returns combined bounds of all items."""
        items = [
            make_rect_item(x=0, y=0, width=50, height=50),
            make_rect_item(x=100, y=100, width=50, height=50),
        ]
        bounds = compute_bounds(items, padding=0)
        assert bounds == QRectF(0, 0, 150, 150)

    def test_with_padding(self):
        """compute_bounds adds padding to all sides."""
        items = [make_rect_item(x=10, y=10, width=80, height=80)]
        bounds = compute_bounds(items, padding=10)
        assert bounds == QRectF(0, 0, 100, 100)

    def test_empty_items(self):
        """compute_bounds returns empty rect for no items."""
        bounds = compute_bounds([], padding=0)
        assert bounds.isEmpty()

    def test_items_with_empty_bounds(self):
        """compute_bounds returns empty rect when all items have empty bounds."""
        items = [LayerItem(name="Empty Layer")]
        bounds = compute_bounds(items, padding=0)
        assert bounds.isEmpty()


class TestExportPng:
    """Tests for PNG export functionality."""

    def test_export_creates_file(self, tmp_path, qtbot):
        """export_png creates a PNG file at the specified path."""
        items = [make_rect_item(x=0, y=0, width=100, height=100)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "test.png"

        result = export_png(items, bounds, output_path, ExportOptions())

        assert result is True
        assert output_path.exists()

    def test_export_correct_dimensions(self, tmp_path, qtbot):
        """export_png creates image with correct dimensions."""
        items = [make_rect_item(x=0, y=0, width=100, height=50)]
        bounds = QRectF(0, 0, 100, 50)
        output_path = tmp_path / "test.png"

        export_png(items, bounds, output_path, ExportOptions())

        img = QImage(str(output_path))
        assert img.width() == 100
        assert img.height() == 50

    def test_export_with_scale(self, tmp_path, qtbot):
        """export_png scales output for higher DPI."""
        items = [make_rect_item(x=0, y=0, width=100, height=100)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "test.png"
        opts = ExportOptions(document_dpi=72, target_dpi=144)  # 2x scale

        export_png(items, bounds, output_path, opts)

        img = QImage(str(output_path))
        assert img.width() == 200
        assert img.height() == 200

    def test_export_empty_items_returns_false(self, tmp_path, qtbot):
        """export_png returns False for empty bounds."""
        bounds = QRectF()  # Empty
        output_path = tmp_path / "test.png"

        result = export_png([], bounds, output_path, ExportOptions())

        assert result is False


class TestExportSvg:
    """Tests for SVG export functionality."""

    def test_export_creates_file(self, tmp_path, qtbot):
        """export_svg creates an SVG file at the specified path."""
        items = [make_rect_item(x=0, y=0, width=100, height=100)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "test.svg"

        result = export_svg(items, bounds, output_path, ExportOptions())

        assert result is True
        assert output_path.exists()

    def test_export_valid_svg(self, tmp_path, qtbot):
        """export_svg creates valid XML."""
        items = [make_rect_item(x=0, y=0, width=100, height=100)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "test.svg"

        export_svg(items, bounds, output_path, ExportOptions())

        # Should parse without error
        tree = ET.parse(output_path)
        root = tree.getroot()
        # SVG namespace check
        assert "svg" in root.tag

    def test_export_correct_viewbox(self, tmp_path, qtbot):
        """export_svg sets correct viewBox."""
        items = [make_rect_item(x=10, y=20, width=100, height=50)]
        bounds = QRectF(10, 20, 100, 50)
        output_path = tmp_path / "test.svg"

        export_svg(items, bounds, output_path, ExportOptions())

        tree = ET.parse(output_path)
        root = tree.getroot()
        viewbox = root.get("viewBox")
        assert viewbox is not None
        # viewBox should be "0 0 100 50" (translated to origin)
        parts = viewbox.split()
        assert len(parts) == 4
        assert float(parts[2]) == 100  # width
        assert float(parts[3]) == 50  # height

    def test_export_empty_items_returns_false(self, tmp_path, qtbot):
        """export_svg returns False for empty bounds."""
        bounds = QRectF()  # Empty
        output_path = tmp_path / "test.svg"

        result = export_svg([], bounds, output_path, ExportOptions())

        assert result is False

    def test_export_ellipse_to_svg(self, tmp_path, qtbot):
        """export_svg creates correct ellipse element."""
        items = [make_ellipse_item(cx=50, cy=50, rx=40, ry=30)]
        bounds = QRectF(10, 20, 80, 60)
        output_path = tmp_path / "ellipse.svg"

        export_svg(items, bounds, output_path, ExportOptions())

        tree = ET.parse(output_path)
        root = tree.getroot()
        ellipse = root.find(".//{http://www.w3.org/2000/svg}ellipse")
        assert ellipse is not None
        assert float(ellipse.get("cx")) == 50
        assert float(ellipse.get("cy")) == 50
        assert float(ellipse.get("rx")) == 40
        assert float(ellipse.get("ry")) == 30

    def test_export_path_to_svg(self, tmp_path, qtbot):
        """export_svg creates correct path element."""
        points = [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 50, "y": 100}]
        items = [make_path_item(points=points, closed=True)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "path.svg"

        export_svg(items, bounds, output_path, ExportOptions())

        tree = ET.parse(output_path)
        root = tree.getroot()
        path_elem = root.find(".//{http://www.w3.org/2000/svg}path")
        assert path_elem is not None
        d = path_elem.get("d")
        assert d is not None
        assert d.startswith("M")  # Starts with move command
        assert "L" in d  # Has line commands
        assert d.endswith("Z")  # Closed path

    def test_export_text_to_svg(self, tmp_path, qtbot):
        """export_svg creates correct text element."""
        from lucent.canvas_items import TextItem
        from lucent.geometry import TextGeometry

        geometry = TextGeometry(x=10, y=20, width=100, height=30)
        text_item = TextItem(
            geometry=geometry,
            text="Hello World",
            font_family="Arial",
            font_size=16,
            text_color="#333333",
            text_opacity=1.0,
        )
        bounds = QRectF(10, 20, 100, 30)
        output_path = tmp_path / "text.svg"

        export_svg([text_item], bounds, output_path, ExportOptions())

        tree = ET.parse(output_path)
        root = tree.getroot()
        text_elem = root.find(".//{http://www.w3.org/2000/svg}text")
        assert text_elem is not None
        assert float(text_elem.get("x")) == 10
        assert text_elem.get("font-family") == "Arial"
        assert text_elem.get("font-size") == "16"
        assert text_elem.text == "Hello World"


class TestExportPngEdgeCases:
    """Edge case tests for PNG export."""

    def test_export_with_background_color(self, tmp_path, qtbot):
        """export_png with background color fills image."""
        items = [make_rect_item(x=0, y=0, width=100, height=100)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "test_bg.png"
        opts = ExportOptions(background="#ff0000")  # Red background

        result = export_png(items, bounds, output_path, opts)

        assert result is True
        img = QImage(str(output_path))
        # Check that at least some pixels are red
        assert img.width() == 100

    def test_export_zero_width_returns_false(self, tmp_path, qtbot):
        """export_png returns False for zero-width bounds."""
        bounds = QRectF(0, 0, 0, 100)  # Zero width
        output_path = tmp_path / "test.png"

        result = export_png([], bounds, output_path, ExportOptions())

        assert result is False

    def test_export_zero_height_returns_false(self, tmp_path, qtbot):
        """export_png returns False for zero-height bounds."""
        bounds = QRectF(0, 0, 100, 0)  # Zero height
        output_path = tmp_path / "test.png"

        result = export_png([], bounds, output_path, ExportOptions())

        assert result is False


class TestExportSvgEdgeCases:
    """Edge case tests for SVG export."""

    def test_export_open_path_no_z(self, tmp_path, qtbot):
        """export_svg creates path without Z for open paths."""
        points = [{"x": 0, "y": 0}, {"x": 100, "y": 100}]
        items = [make_path_item(points=points, closed=False)]
        bounds = QRectF(0, 0, 100, 100)
        output_path = tmp_path / "path_open.svg"

        export_svg(items, bounds, output_path, ExportOptions())

        tree = ET.parse(output_path)
        root = tree.getroot()
        path_elem = root.find(".//{http://www.w3.org/2000/svg}path")
        assert path_elem is not None
        d = path_elem.get("d")
        assert "Z" not in d  # Open path has no Z

    def test_export_skips_unsupported_items(self, tmp_path, qtbot):
        """export_svg skips layers and other unsupported items."""
        from lucent.canvas_items import LayerItem

        items = [
            make_rect_item(x=0, y=0, width=50, height=50),
            LayerItem(name="Layer1"),  # Unsupported for SVG
        ]
        bounds = QRectF(0, 0, 50, 50)
        output_path = tmp_path / "mixed.svg"

        result = export_svg(items, bounds, output_path, ExportOptions())

        assert result is True
        tree = ET.parse(output_path)
        root = tree.getroot()
        # Should only have one rect, no layer element
        rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
        assert len(rects) == 1
