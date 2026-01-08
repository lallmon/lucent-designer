"""Unit tests for pen_tool_state module."""

from lucent.pen_tool_state import PenToolState


def test_add_points_and_preview_segment():
    state = PenToolState()
    state.add_point(0, 0)
    state.add_point(10, 0)

    preview = state.preview_to(12, 4)
    assert preview == ((10.0, 0.0), (12.0, 4.0))
    assert state.points == [(0.0, 0.0), (10.0, 0.0)]


def test_close_on_first_point_creates_closed_path():
    state = PenToolState()
    state.add_point(0, 0)
    state.add_point(10, 0)
    state.add_point(10, 10)

    closed = state.try_close_on(0, 0)
    assert closed is True
    assert state.closed is True
    assert state.points == [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]


def test_reset_clears_state():
    state = PenToolState()
    state.add_point(0, 0)
    state.preview_to(1, 1)
    state.reset()
    assert state.points == []
    assert state.closed is False
    assert state.preview_point is None


def test_to_item_data_includes_stroke_only_defaults():
    state = PenToolState()
    state.add_point(0, 0)
    state.add_point(5, 0)
    state.try_close_on(0, 0)

    data = state.to_item_data(
        {"strokeWidth": 2, "strokeColor": "#ff00ff", "strokeOpacity": 0.75}
    )
    assert data["type"] == "path"
    # Check geometry
    assert data["geometry"]["closed"] is True
    assert data["geometry"]["points"][0] == {"x": 0.0, "y": 0.0}
    # Check appearances
    fill = data["appearances"][0]
    stroke = data["appearances"][1]
    assert fill["type"] == "fill"
    assert fill["opacity"] == 0.0
    assert stroke["type"] == "stroke"
    assert stroke["width"] == 2
    assert stroke["color"] == "#ff00ff"
    assert stroke["opacity"] == 0.75


def test_to_item_data_respects_fill_settings():
    state = PenToolState()
    state.add_point(0, 0)
    state.add_point(3, 4)
    state.try_close_on(0, 0)

    data = state.to_item_data(
        {
            "strokeWidth": 1,
            "strokeColor": "#00ff00",
            "strokeOpacity": 1.0,
            "fillColor": "#123456",
            "fillOpacity": 0.5,
        }
    )
    fill = data["appearances"][0]
    assert fill["opacity"] == 0.5
    assert fill["color"] == "#123456"
