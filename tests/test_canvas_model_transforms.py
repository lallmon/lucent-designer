"""CanvasModel transform getters/setters."""

from test_helpers import make_rectangle, make_layer


class TestCanvasModelTransforms:
    """Tests for getItemTransform and setItemTransform methods."""

    def test_get_item_transform_rectangle(self, canvas_model):
        rect_data = make_rectangle(x=0, y=0, width=100, height=50)
        rect_data["transform"] = {
            "translateX": 10,
            "translateY": 20,
            "rotate": 45,
            "scaleX": 1.5,
            "scaleY": 2.0,
        }
        canvas_model.addItem(rect_data)

        transform = canvas_model.getItemTransform(0)
        assert transform is not None
        assert transform["translateX"] == 10
        assert transform["translateY"] == 20
        assert transform["rotate"] == 45
        assert transform["scaleX"] == 1.5
        assert transform["scaleY"] == 2.0

    def test_get_item_transform_invalid_index(self, canvas_model):
        assert canvas_model.getItemTransform(-1) is None
        assert canvas_model.getItemTransform(999) is None

    def test_get_item_transform_layer_returns_none(self, canvas_model):
        canvas_model.addItem(make_layer(name="Test Layer"))
        assert canvas_model.getItemTransform(0) is None

    def test_set_item_transform(self, canvas_model, qtbot):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))

        new_transform = {
            "translateX": 50,
            "translateY": 25,
            "rotate": 90,
            "scaleX": 2.0,
            "scaleY": 2.0,
        }

        with qtbot.waitSignal(
            canvas_model.itemTransformChanged, timeout=1000
        ) as blocker:
            canvas_model.setItemTransform(0, new_transform)

        assert blocker.args == [0]

        transform = canvas_model.getItemTransform(0)
        assert transform["translateX"] == 50
        assert transform["rotate"] == 90

    def test_set_item_transform_invalid_index(self, canvas_model):
        canvas_model.addItem(make_rectangle(x=0, y=0, width=100, height=50))
        canvas_model.setItemTransform(-1, {"rotate": 45})
        canvas_model.setItemTransform(999, {"rotate": 45})

    def test_set_item_transform_layer_no_op(self, canvas_model):
        canvas_model.addItem(make_layer(name="Test Layer"))
        canvas_model.setItemTransform(0, {"rotate": 45})
