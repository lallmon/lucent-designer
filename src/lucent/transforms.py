"""
Transform class for Lucent canvas items.

This module provides non-destructive 2D transforms that can be applied
to geometry without modifying the original geometry data.
"""

from typing import Dict, Any

from PySide6.QtGui import QTransform


class Transform:
    """Non-destructive 2D transform.

    Transforms are applied in this order: translate, rotate, scale.
    """

    def __init__(
        self,
        translate_x: float = 0,
        translate_y: float = 0,
        rotate: float = 0,
        scale_x: float = 1,
        scale_y: float = 1,
    ) -> None:
        self.translate_x = float(translate_x)
        self.translate_y = float(translate_y)
        self.rotate = float(rotate)  # degrees
        self.scale_x = float(scale_x)
        self.scale_y = float(scale_y)

    def is_identity(self) -> bool:
        """Check if this transform is the identity transform."""
        return (
            self.translate_x == 0
            and self.translate_y == 0
            and self.rotate == 0
            and self.scale_x == 1
            and self.scale_y == 1
        )

    def to_qtransform(self) -> QTransform:
        """Convert to Qt transform matrix.

        Order of operations: translate, then rotate, then scale.
        """
        t = QTransform()
        t.translate(self.translate_x, self.translate_y)
        t.rotate(self.rotate)
        t.scale(self.scale_x, self.scale_y)
        return t

    def to_qtransform_centered(self, center_x: float, center_y: float) -> QTransform:
        """Convert to Qt transform with rotation/scale around a center point.

        Order of operations:
        1. Translate by translate_x/translate_y
        2. Move origin to center
        3. Apply rotation
        4. Apply scale
        5. Move origin back from center

        Args:
            center_x: X coordinate of the center point for rotation/scale.
            center_y: Y coordinate of the center point for rotation/scale.

        Returns:
            QTransform matrix with transforms applied around center.
        """
        if self.is_identity():
            return QTransform()

        t = QTransform()
        # Apply translation
        t.translate(self.translate_x, self.translate_y)
        # Move to center
        t.translate(center_x, center_y)
        # Apply rotation and scale around center
        t.rotate(self.rotate)
        t.scale(self.scale_x, self.scale_y)
        # Move back from center
        t.translate(-center_x, -center_y)
        return t

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "translateX": self.translate_x,
            "translateY": self.translate_y,
            "rotate": self.rotate,
            "scaleX": self.scale_x,
            "scaleY": self.scale_y,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Transform":
        """Deserialize from dictionary."""
        return Transform(
            translate_x=float(data.get("translateX", 0)),
            translate_y=float(data.get("translateY", 0)),
            rotate=float(data.get("rotate", 0)),
            scale_x=float(data.get("scaleX", 1)),
            scale_y=float(data.get("scaleY", 1)),
        )
