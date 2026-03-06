from video.scene_animator import _normalize_effect


def test_animation_mapping_native_and_fallback():
    assert _normalize_effect("zoom", "") == "zoom"
    assert _normalize_effect("pan_left", "") == "pan_left"
    assert _normalize_effect("pan right", "") == "pan_right"

    assert _normalize_effect("parallax", "") == "pan_right"
    assert _normalize_effect("infographic animation", "") == "zoom"
    assert _normalize_effect("diagram drawing animation", "") == "pan_left"


def test_motion_direction_overrides_mapping():
    assert _normalize_effect("parallax", "pan left") == "pan_left"
    assert _normalize_effect("diagram drawing animation", "slow zoom in") == "zoom"
