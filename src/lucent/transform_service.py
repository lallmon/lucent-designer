# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Transform and edit-mapping helpers for CanvasModel."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple
import math

from lucent.canvas_items import CanvasItem
from lucent.edit_context import EditContext
from lucent.model_geometry import compute_geometry_bounds


class TransformService:
    """Pure transform/edit-mapping logic for CanvasModel."""

    def __init__(
        self,
        get_item: Callable[[int], Optional[CanvasItem]],
        is_valid_index: Callable[[int], bool],
        edit_context: EditContext,
        item_to_dict: Callable[[CanvasItem], Dict[str, Any]],
        update_item: Callable[[int, Dict[str, Any]], None],
        emit_transform_changed: Callable[[int], None],
        begin_transaction: Optional[Callable[[], None]] = None,
        end_transaction: Optional[Callable[[], None]] = None,
    ) -> None:
        self._get_item = get_item
        self._is_valid_index = is_valid_index
        self._edit_context = edit_context
        self._item_to_dict = item_to_dict
        self._update_item = update_item
        self._emit_transform_changed = emit_transform_changed
        self._begin_transaction = begin_transaction
        self._end_transaction = end_transaction

    @staticmethod
    def _normalize_rotation(degrees: float) -> float:
        """Normalize rotation to 0-360° range."""
        normalized = degrees % 360
        if normalized < 0:
            normalized += 360
        return normalized

    @staticmethod
    def _derive_origin_from_pivot(
        bounds: Dict[str, float], pivot_x: float, pivot_y: float
    ) -> Tuple[float, float]:
        """Convert absolute pivot coords into normalized origin for UI."""
        origin_x = 0.0
        origin_y = 0.0
        if bounds["width"] != 0:
            origin_x = (pivot_x - bounds["x"]) / bounds["width"]
        if bounds["height"] != 0:
            origin_y = (pivot_y - bounds["y"]) / bounds["height"]
        return origin_x, origin_y

    @staticmethod
    def _pivot_from_origin(
        bounds: Dict[str, float], origin_x: float, origin_y: float
    ) -> Tuple[float, float]:
        pivot_x = bounds["x"] + bounds["width"] * origin_x
        pivot_y = bounds["y"] + bounds["height"] * origin_y
        return pivot_x, pivot_y

    def get_item_transform(self, index: int) -> Optional[Dict[str, Any]]:
        if not self._is_valid_index(index):
            return None
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return None

        transform_dict = item.transform.to_dict()
        bounds = compute_geometry_bounds(item)
        if not bounds:
            transform_dict["originX"] = 0
            transform_dict["originY"] = 0
            return transform_dict

        origin_x, origin_y = self._derive_origin_from_pivot(
            bounds, item.transform.pivot_x, item.transform.pivot_y
        )
        transform_dict["originX"] = origin_x
        transform_dict["originY"] = origin_y
        return transform_dict

    def set_item_transform(self, index: int, transform: Dict[str, Any]) -> None:
        if not self._is_valid_index(index):
            return
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return

        if "rotate" in transform:
            transform = dict(transform)
            transform["rotate"] = self._normalize_rotation(transform["rotate"])

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        if "pivotX" not in transform or "pivotY" not in transform:
            transform = dict(transform)
            transform["pivotX"] = item.transform.pivot_x
            transform["pivotY"] = item.transform.pivot_y

        current_data = self._item_to_dict(item)
        current_data["transform"] = transform
        self._update_item(index, current_data)
        self._emit_transform_changed(index)

    def update_transform_property(self, index: int, prop: str, value: float) -> None:
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return

        new_transform = {
            "translateX": item.transform.translate_x,
            "translateY": item.transform.translate_y,
            "rotate": item.transform.rotate,
            "scaleX": item.transform.scale_x,
            "scaleY": item.transform.scale_y,
            "pivotX": item.transform.pivot_x,
            "pivotY": item.transform.pivot_y,
        }
        new_transform[prop] = value
        self.set_item_transform(index, new_transform)

    def rotate_item(self, index: int, angle: float) -> None:
        if not self._is_valid_index(index):
            return
        self.update_transform_property(index, "rotate", angle)

    def get_displayed_position(self, index: int) -> Optional[Dict[str, float]]:
        if not self._is_valid_index(index):
            return None
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return None
        bounds = compute_geometry_bounds(item)
        if not bounds:
            return None
        return {
            "x": item.transform.pivot_x + item.transform.translate_x,
            "y": item.transform.pivot_y + item.transform.translate_y,
        }

    def get_displayed_size(self, index: int) -> Optional[Dict[str, float]]:
        if not self._is_valid_index(index):
            return None
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return None
        bounds = compute_geometry_bounds(item)
        if not bounds:
            return None

        current = self.get_item_transform(index) or {}
        scale_x = current.get("scaleX", 1)
        scale_y = current.get("scaleY", 1)

        return {
            "width": bounds["width"] * scale_x,
            "height": bounds["height"] * scale_y,
        }

    def transform_point_to_geometry(
        self, index: int, screen_x: float, screen_y: float
    ) -> Optional[Dict[str, float]]:
        if not self._is_valid_index(index):
            return None
        item = self._get_item(index)
        if not item or not hasattr(item, "transform") or not hasattr(item, "geometry"):
            return None

        return self._edit_context.map_screen_to_geometry(
            item.transform, screen_x, screen_y
        )

    def lock_edit_transform(self, index: int) -> None:
        if not self._is_valid_index(index):
            return
        item = self._get_item(index)
        if not item or not hasattr(item, "transform") or not hasattr(item, "geometry"):
            return

        self._edit_context.lock_pivot(
            index, item.transform.pivot_x, item.transform.pivot_y
        )

    def unlock_edit_transform(self, index: int) -> None:
        self._edit_context.unlock_pivot(index)

    def update_geometry_with_origin_compensation(
        self, index: int, geometry_data: Dict[str, Any]
    ) -> None:
        if not self._is_valid_index(index):
            return
        self._update_item(index, {"geometry": geometry_data})

    def update_geometry_locked(self, index: int, geometry_data: Dict[str, Any]) -> None:
        self.update_geometry_with_origin_compensation(index, geometry_data)

    def transform_point_to_geometry_locked(
        self, index: int, screen_x: float, screen_y: float
    ) -> Optional[Dict[str, float]]:
        if not self._is_valid_index(index):
            return None
        item = self._get_item(index)
        if not item or not hasattr(item, "transform") or not hasattr(item, "geometry"):
            return None

        locked_pivot = self._edit_context.get_locked_pivot(index)
        if locked_pivot:
            return self._edit_context.map_screen_to_geometry(
                item.transform, screen_x, screen_y, locked_pivot
            )

        return self._edit_context.map_screen_to_geometry(
            item.transform, screen_x, screen_y
        )

    def has_non_identity_transform(self, index: int) -> bool:
        if not self._is_valid_index(index):
            return False
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return False

        current = self.get_item_transform(index) or {}
        return (
            current.get("rotate", 0) != 0
            or current.get("scaleX", 1) != 1
            or current.get("scaleY", 1) != 1
            or current.get("translateX", 0) != 0
            or current.get("translateY", 0) != 0
        )

    def set_item_position(self, index: int, axis: str, value: float) -> None:
        if not self._is_valid_index(index):
            return
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        new_transform = {
            "translateX": item.transform.translate_x,
            "translateY": item.transform.translate_y,
            "rotate": item.transform.rotate,
            "scaleX": item.transform.scale_x,
            "scaleY": item.transform.scale_y,
            "pivotX": item.transform.pivot_x,
            "pivotY": item.transform.pivot_y,
        }
        if axis == "x":
            new_transform["translateX"] = value - item.transform.pivot_x
        elif axis == "y":
            new_transform["translateY"] = value - item.transform.pivot_y
        else:
            return

        self.set_item_transform(index, new_transform)

    def set_item_origin(self, index: int, new_ox: float, new_oy: float) -> None:
        if not self._is_valid_index(index):
            return
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        rotation = item.transform.rotate
        scale_x = item.transform.scale_x
        scale_y = item.transform.scale_y
        old_tx = item.transform.translate_x
        old_ty = item.transform.translate_y

        old_pivot_x = item.transform.pivot_x
        old_pivot_y = item.transform.pivot_y
        new_pivot_x, new_pivot_y = self._pivot_from_origin(bounds, new_ox, new_oy)

        dx = old_pivot_x - new_pivot_x
        dy = old_pivot_y - new_pivot_y

        scaled_dx = dx * scale_x
        scaled_dy = dy * scale_y

        radians = rotation * math.pi / 180
        cos_r = math.cos(radians)
        sin_r = math.sin(radians)
        rotated_scaled_dx = scaled_dx * cos_r - scaled_dy * sin_r
        rotated_scaled_dy = scaled_dx * sin_r + scaled_dy * cos_r

        new_transform = {
            "translateX": old_tx + dx - rotated_scaled_dx,
            "translateY": old_ty + dy - rotated_scaled_dy,
            "rotate": rotation,
            "scaleX": scale_x,
            "scaleY": scale_y,
            "pivotX": new_pivot_x,
            "pivotY": new_pivot_y,
        }

        self.set_item_transform(index, new_transform)

    def set_displayed_size(
        self, index: int, dimension: str, value: float, proportional: bool
    ) -> None:
        if not self._is_valid_index(index):
            return
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        if bounds["width"] <= 0 or bounds["height"] <= 0:
            return

        value = max(1.0, value)

        current = self.get_item_transform(index) or {}
        current_scale_x = current.get("scaleX", 1)
        current_scale_y = current.get("scaleY", 1)

        if dimension == "width":
            new_scale_x = value / bounds["width"]
            if proportional:
                ratio = new_scale_x / current_scale_x
                new_scale_y = current_scale_y * ratio
                if self._begin_transaction:
                    self._begin_transaction()
                self.update_transform_property(index, "scaleX", new_scale_x)
                self.update_transform_property(index, "scaleY", new_scale_y)
                if self._end_transaction:
                    self._end_transaction()
            else:
                self.update_transform_property(index, "scaleX", new_scale_x)
        elif dimension == "height":
            new_scale_y = value / bounds["height"]
            if proportional:
                ratio = new_scale_y / current_scale_y
                new_scale_x = current_scale_x * ratio
                if self._begin_transaction:
                    self._begin_transaction()
                self.update_transform_property(index, "scaleX", new_scale_x)
                self.update_transform_property(index, "scaleY", new_scale_y)
                if self._end_transaction:
                    self._end_transaction()
            else:
                self.update_transform_property(index, "scaleY", new_scale_y)

    def scale_item(
        self,
        index: int,
        new_scale_x: float,
        new_scale_y: float,
        anchor_x: float,
        anchor_y: float,
    ) -> None:
        self.apply_scale_resize(index, new_scale_x, new_scale_y, anchor_x, anchor_y)

    def apply_scale_resize(
        self,
        index: int,
        new_scale_x: float,
        new_scale_y: float,
        anchor_x: float,
        anchor_y: float,
    ) -> None:
        if not self._is_valid_index(index):
            return
        item = self._get_item(index)
        if not item or not hasattr(item, "transform"):
            return

        bounds = compute_geometry_bounds(item)
        if not bounds:
            return

        pivot_x = item.transform.pivot_x
        pivot_y = item.transform.pivot_y
        old_scale_x = item.transform.scale_x
        old_scale_y = item.transform.scale_y
        rotation = item.transform.rotate
        old_tx = item.transform.translate_x
        old_ty = item.transform.translate_y

        anchor_geom_x = bounds["x"] + bounds["width"] * anchor_x
        anchor_geom_y = bounds["y"] + bounds["height"] * anchor_y

        d_x = anchor_geom_x - pivot_x
        d_y = anchor_geom_y - pivot_y

        scaled_old_x = d_x * old_scale_x
        scaled_old_y = d_y * old_scale_y
        scaled_new_x = d_x * new_scale_x
        scaled_new_y = d_y * new_scale_y

        radians = rotation * math.pi / 180
        cos_r = math.cos(radians)
        sin_r = math.sin(radians)
        rotated_old_x = scaled_old_x * cos_r - scaled_old_y * sin_r
        rotated_old_y = scaled_old_x * sin_r + scaled_old_y * cos_r
        rotated_new_x = scaled_new_x * cos_r - scaled_new_y * sin_r
        rotated_new_y = scaled_new_x * sin_r + scaled_new_y * cos_r

        new_tx = old_tx + (rotated_old_x - rotated_new_x)
        new_ty = old_ty + (rotated_old_y - rotated_new_y)

        new_transform = {
            "translateX": new_tx,
            "translateY": new_ty,
            "rotate": rotation,
            "scaleX": new_scale_x,
            "scaleY": new_scale_y,
            "pivotX": pivot_x,
            "pivotY": pivot_y,
        }

        self.set_item_transform(index, new_transform)
