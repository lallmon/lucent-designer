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
