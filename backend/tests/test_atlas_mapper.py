import numpy as np
import pytest
from unittest.mock import patch, MagicMock


def _make_fake_atlas(n_labels=10, n_verts_per_hemi=10242):
    label_names = [
        b"unknown", b"G_cuneus", b"G_oc-temp_lat-fusifor",
        b"G_front_inf-Opercular", b"G_precentral", b"G_front_sup",
        b"G_occipital_sup", b"G_temp_sup-Lateral", b"S_calcarine", b"G_orbital",
    ]
    rng = np.random.default_rng(42)
    atlas = MagicMock()
    atlas.labels = label_names
    atlas.map_left = rng.integers(0, n_labels, size=n_verts_per_hemi)
    atlas.map_right = rng.integers(0, n_labels, size=n_verts_per_hemi)
    return atlas


def test_get_vertex_masks_gives_five_regions():
    fake = _make_fake_atlas()
    with patch("nilearn.datasets.fetch_atlas_surf_destrieux", return_value=fake):
        from app.atlas_mapper import _load_atlas, get_vertex_masks
        _load_atlas.cache_clear()
        masks = get_vertex_masks()
    assert set(masks.keys()) == {
        "visual_cortex", "face_social", "language_areas", "motor_action", "prefrontal"
    }


def test_vertex_masks_have_bool_dtype_and_correct_shape():
    fake = _make_fake_atlas()
    with patch("nilearn.datasets.fetch_atlas_surf_destrieux", return_value=fake):
        from app.atlas_mapper import _load_atlas, get_vertex_masks
        _load_atlas.cache_clear()
        masks = get_vertex_masks()
    for name, mask in masks.items():
        assert mask.dtype == bool, f"{name} mask is not bool"
        assert mask.shape == (20484,), f"{name} mask shape is {mask.shape}"


def test_vertex_activations_to_scores_gives_correct_keys():
    from app.atlas_mapper import vertex_activations_to_scores
    masks = {
        "visual_cortex": np.array([True, False, False, False]),
        "face_social": np.array([False, True, False, False]),
        "language_areas": np.array([False, False, True, False]),
        "motor_action": np.array([False, False, False, True]),
        "prefrontal": np.array([True, True, False, False]),
    }
    scores = vertex_activations_to_scores(np.ones((5, 4)), masks)
    assert set(scores.keys()) == {
        "visual_cortex", "face_social", "language_areas", "motor_action", "prefrontal"
    }


def test_uniform_activation_gives_50_for_all_regions():
    from app.atlas_mapper import vertex_activations_to_scores
    masks = {
        "visual_cortex": np.array([True, False, False, False]),
        "face_social": np.array([False, True, False, False]),
        "language_areas": np.array([False, False, True, False]),
        "motor_action": np.array([False, False, False, True]),
        "prefrontal": np.array([True, False, True, False]),
    }
    scores = vertex_activations_to_scores(np.ones((3, 4)), masks)
    for region, score in scores.items():
        assert score == 50, f"{region} expected 50, got {score}"


def test_scores_stay_within_0_100():
    from app.atlas_mapper import vertex_activations_to_scores
    rng = np.random.default_rng(0)
    masks = {k: rng.integers(0, 2, size=100).astype(bool)
             for k in ["visual_cortex", "face_social", "language_areas", "motor_action", "prefrontal"]}
    scores = vertex_activations_to_scores(rng.standard_normal((10, 100)), masks)
    for region, score in scores.items():
        assert 0 <= score <= 100, f"{region} score {score} out of range"


def test_high_activation_region_scores_above_50():
    from app.atlas_mapper import vertex_activations_to_scores
    n = 100
    masks = {
        "visual_cortex": np.array([True] * 20 + [False] * 80),
        "face_social": np.array([False] * 20 + [True] * 20 + [False] * 60),
        "language_areas": np.array([False] * 40 + [True] * 20 + [False] * 40),
        "motor_action": np.array([False] * 60 + [True] * 20 + [False] * 20),
        "prefrontal": np.array([False] * 80 + [True] * 20),
    }
    preds = np.zeros((5, n))
    preds[:, :20] = 10.0  # visual_cortex vertices strongly active
    scores = vertex_activations_to_scores(preds, masks)
    assert scores["visual_cortex"] > 50
