"""Unit tests for transforms module."""

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QTransform

from lucent.transforms import Transform


class TestTransform:
    """Tests for Transform class."""

    def test_basic_creation(self):
        """Test creating a basic transform with default parameters."""
        transform = Transform()
        assert transform.translate_x == 0
        assert transform.translate_y == 0
        assert transform.rotate == 0
        assert transform.scale_x == 1
        assert transform.scale_y == 1

    def test_creation_with_parameters(self):
        """Test creating a transform with custom parameters."""
        transform = Transform(
            translate_x=10,
            translate_y=20,
            rotate=45,
            scale_x=2.0,
            scale_y=0.5,
        )
        assert transform.translate_x == 10
        assert transform.translate_y == 20
        assert transform.rotate == 45
        assert transform.scale_x == 2.0
        assert transform.scale_y == 0.5

    def test_is_identity_default(self):
        """Test that default transform is identity."""
        transform = Transform()
        assert transform.is_identity() is True

    def test_is_identity_with_translation(self):
        """Test that translation makes transform non-identity."""
        transform = Transform(translate_x=5)
        assert transform.is_identity() is False

    def test_is_identity_with_rotation(self):
        """Test that rotation makes transform non-identity."""
        transform = Transform(rotate=45)
        assert transform.is_identity() is False

    def test_is_identity_with_scale(self):
        """Test that non-unit scale makes transform non-identity."""
        transform = Transform(scale_x=2)
        assert transform.is_identity() is False

    def test_to_qtransform_identity(self):
        """Test to_qtransform returns identity for default transform."""
        transform = Transform()
        qtransform = transform.to_qtransform()
        assert isinstance(qtransform, QTransform)
        assert qtransform.isIdentity()

    def test_to_qtransform_translation(self):
        """Test to_qtransform applies translation correctly."""
        transform = Transform(translate_x=10, translate_y=20)
        qtransform = transform.to_qtransform()

        point = QPointF(0, 0)
        result = qtransform.map(point)
        assert abs(result.x() - 10) < 0.001
        assert abs(result.y() - 20) < 0.001

    def test_to_qtransform_rotation(self):
        """Test to_qtransform applies rotation correctly."""
        transform = Transform(rotate=90)
        qtransform = transform.to_qtransform()

        point = QPointF(1, 0)
        result = qtransform.map(point)
        assert abs(result.x()) < 0.001
        assert abs(result.y() - 1) < 0.001

    def test_to_qtransform_scale(self):
        """Test to_qtransform applies scale correctly."""
        transform = Transform(scale_x=2, scale_y=3)
        qtransform = transform.to_qtransform()

        point = QPointF(5, 10)
        result = qtransform.map(point)
        assert abs(result.x() - 10) < 0.001
        assert abs(result.y() - 30) < 0.001

    def test_to_qtransform_combined(self):
        """Test to_qtransform with combined transforms."""
        transform = Transform(translate_x=10, scale_x=2)
        qtransform = transform.to_qtransform()

        point = QPointF(0, 0)
        result = qtransform.map(point)
        assert abs(result.x() - 10) < 0.001

    def test_to_dict(self):
        """Test serialization to dictionary."""
        transform = Transform(
            translate_x=10,
            translate_y=20,
            rotate=45,
            scale_x=2.0,
            scale_y=0.5,
        )
        data = transform.to_dict()
        assert data == {
            "translateX": 10,
            "translateY": 20,
            "rotate": 45,
            "scaleX": 2.0,
            "scaleY": 0.5,
            "originX": 0.0,
            "originY": 0.0,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "translateX": 15,
            "translateY": 25,
            "rotate": 30,
            "scaleX": 1.5,
            "scaleY": 0.75,
        }
        transform = Transform.from_dict(data)
        assert transform.translate_x == 15
        assert transform.translate_y == 25
        assert transform.rotate == 30
        assert transform.scale_x == 1.5
        assert transform.scale_y == 0.75

    def test_from_dict_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {}
        transform = Transform.from_dict(data)
        assert transform.translate_x == 0
        assert transform.translate_y == 0
        assert transform.rotate == 0
        assert transform.scale_x == 1
        assert transform.scale_y == 1

    def test_from_dict_partial(self):
        """Test from_dict with partial data."""
        data = {"translateX": 10, "rotate": 45}
        transform = Transform.from_dict(data)
        assert transform.translate_x == 10
        assert transform.translate_y == 0
        assert transform.rotate == 45
        assert transform.scale_x == 1
        assert transform.scale_y == 1

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = Transform(
            translate_x=100,
            translate_y=-50,
            rotate=180,
            scale_x=0.5,
            scale_y=2.0,
        )
        data = original.to_dict()
        restored = Transform.from_dict(data)
        assert restored.translate_x == original.translate_x
        assert restored.translate_y == original.translate_y
        assert restored.rotate == original.rotate
        assert restored.scale_x == original.scale_x
        assert restored.scale_y == original.scale_y

    def test_map_rect(self):
        """Test transforming a rectangle."""
        transform = Transform(translate_x=10, translate_y=20)
        qtransform = transform.to_qtransform()

        rect = QRectF(0, 0, 50, 30)
        result = qtransform.mapRect(rect)

        assert abs(result.x() - 10) < 0.001
        assert abs(result.y() - 20) < 0.001
        assert abs(result.width() - 50) < 0.001
        assert abs(result.height() - 30) < 0.001

    def test_negative_scale(self):
        """Test that negative scale (mirroring) works."""
        transform = Transform(scale_x=-1, scale_y=1)
        qtransform = transform.to_qtransform()

        point = QPointF(10, 5)
        result = qtransform.map(point)
        assert abs(result.x() + 10) < 0.001
        assert abs(result.y() - 5) < 0.001

    def test_rotation_180_degrees(self):
        """Test 180 degree rotation."""
        transform = Transform(rotate=180)
        qtransform = transform.to_qtransform()

        point = QPointF(1, 1)
        result = qtransform.map(point)
        assert abs(result.x() + 1) < 0.001
        assert abs(result.y() + 1) < 0.001

    def test_to_qtransform_centered_identity(self):
        """Identity transform should not move center point."""
        transform = Transform()
        qtransform = transform.to_qtransform_centered(50, 50)
        assert qtransform.isIdentity()

    def test_to_qtransform_centered_rotation_keeps_center(self):
        """90 degree rotation around center should keep center stationary."""
        transform = Transform(rotate=90)
        qtransform = transform.to_qtransform_centered(50, 50)

        center = QPointF(50, 50)
        result = qtransform.map(center)
        assert abs(result.x() - 50) < 0.001
        assert abs(result.y() - 50) < 0.001

    def test_to_qtransform_centered_rotation_moves_corners(self):
        """90 degree rotation should move corners appropriately."""
        transform = Transform(rotate=90)
        qtransform = transform.to_qtransform_centered(50, 50)

        top_left = QPointF(0, 0)
        result = qtransform.map(top_left)
        assert abs(result.x() - 100) < 0.001
        assert abs(result.y() - 0) < 0.001

    def test_to_qtransform_centered_scale_keeps_center(self):
        """Scale around center should keep center stationary."""
        transform = Transform(scale_x=2, scale_y=2)
        qtransform = transform.to_qtransform_centered(50, 50)

        center = QPointF(50, 50)
        result = qtransform.map(center)
        assert abs(result.x() - 50) < 0.001
        assert abs(result.y() - 50) < 0.001

    def test_to_qtransform_centered_scale_moves_edges(self):
        """Scale 2x around center should double distance from center."""
        transform = Transform(scale_x=2, scale_y=2)
        qtransform = transform.to_qtransform_centered(50, 50)

        # Point at origin is 50 units from center, should move to -50
        origin = QPointF(0, 0)
        result = qtransform.map(origin)
        assert abs(result.x() + 50) < 0.001
        assert abs(result.y() + 50) < 0.001

    def test_to_qtransform_centered_with_translation(self):
        """Translation should be applied after center-based rotation/scale."""
        transform = Transform(translate_x=10, translate_y=20, rotate=0)
        qtransform = transform.to_qtransform_centered(50, 50)

        origin = QPointF(0, 0)
        result = qtransform.map(origin)
        assert abs(result.x() - 10) < 0.001
        assert abs(result.y() - 20) < 0.001


class TestTransformOrigin:
    """Tests for transform origin point handling."""

    def test_origin_defaults_to_zero(self):
        """Default origin should be (0, 0) = top-left."""
        transform = Transform()
        assert transform.origin_x == 0
        assert transform.origin_y == 0

    def test_origin_in_constructor(self):
        """Origin can be set in constructor."""
        transform = Transform(origin_x=0.5, origin_y=0.5)
        assert transform.origin_x == 0.5
        assert transform.origin_y == 0.5

    def test_origin_serialization(self):
        """Origin is serialized to dict."""
        transform = Transform(origin_x=0.5, origin_y=1.0)
        data = transform.to_dict()
        assert data["originX"] == 0.5
        assert data["originY"] == 1.0

    def test_origin_deserialization(self):
        """Origin is deserialized from dict."""
        data = {"originX": 0.25, "originY": 0.75}
        transform = Transform.from_dict(data)
        assert transform.origin_x == 0.25
        assert transform.origin_y == 0.75

    def test_origin_defaults_in_deserialization(self):
        """Missing origin defaults to 0."""
        data = {"rotate": 45}
        transform = Transform.from_dict(data)
        assert transform.origin_x == 0
        assert transform.origin_y == 0

    def test_rotation_around_topleft_origin(self):
        """Rotation around top-left moves the shape."""
        transform = Transform(rotate=90)
        qtransform = transform.to_qtransform_centered(0, 0)

        top_left = QPointF(0, 0)
        result = qtransform.map(top_left)
        assert abs(result.x()) < 0.001
        assert abs(result.y()) < 0.001

        bottom_right = QPointF(100, 50)
        result = qtransform.map(bottom_right)
        assert abs(result.x() + 50) < 0.001  # y becomes -x
        assert abs(result.y() - 100) < 0.001  # x becomes y

    def test_rotation_around_bottomright_origin(self):
        """Rotation around bottom-right corner."""
        transform = Transform(rotate=180)
        qtransform = transform.to_qtransform_centered(100, 50)

        bottom_right = QPointF(100, 50)
        result = qtransform.map(bottom_right)
        assert abs(result.x() - 100) < 0.001
        assert abs(result.y() - 50) < 0.001

        # Rotating top-left around (100, 50) should land at (200, 100)
        top_left = QPointF(0, 0)
        result = qtransform.map(top_left)
        assert abs(result.x() - 200) < 0.001
        assert abs(result.y() - 100) < 0.001
