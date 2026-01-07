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

        # Transform a point
        point = QPointF(0, 0)
        result = qtransform.map(point)
        assert abs(result.x() - 10) < 0.001
        assert abs(result.y() - 20) < 0.001

    def test_to_qtransform_rotation(self):
        """Test to_qtransform applies rotation correctly."""
        transform = Transform(rotate=90)
        qtransform = transform.to_qtransform()

        # Transform a point - 90 degree rotation
        point = QPointF(1, 0)
        result = qtransform.map(point)
        assert abs(result.x()) < 0.001
        assert abs(result.y() - 1) < 0.001

    def test_to_qtransform_scale(self):
        """Test to_qtransform applies scale correctly."""
        transform = Transform(scale_x=2, scale_y=3)
        qtransform = transform.to_qtransform()

        # Transform a point
        point = QPointF(5, 10)
        result = qtransform.map(point)
        assert abs(result.x() - 10) < 0.001
        assert abs(result.y() - 30) < 0.001

    def test_to_qtransform_combined(self):
        """Test to_qtransform with combined transforms."""
        # Translation + scale
        transform = Transform(translate_x=10, scale_x=2)
        qtransform = transform.to_qtransform()

        # Point at origin should be translated then scaled
        point = QPointF(0, 0)
        result = qtransform.map(point)
        # Translation happens first, then scale
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
