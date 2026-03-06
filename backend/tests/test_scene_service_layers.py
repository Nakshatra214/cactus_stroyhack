from services.scene_service import _deserialize_visual_layers, _serialize_visual_layers


def test_visual_layers_serialize_and_deserialize_round_trip():
    raw = [" background ", "diagram", "", "labels"]
    serialized = _serialize_visual_layers(raw)
    parsed = _deserialize_visual_layers(serialized)
    assert parsed == ["background", "diagram", "labels"]


def test_visual_layers_deserialize_from_csv():
    parsed = _deserialize_visual_layers("bg, chart, labels")
    assert parsed == ["bg", "chart", "labels"]
