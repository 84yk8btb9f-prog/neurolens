from __future__ import annotations
import logging
import numpy as np
from functools import lru_cache

_log = logging.getLogger(__name__)

CORTICAL_REGIONS = frozenset(
    ["visual_cortex", "face_social", "language_areas", "motor_action", "prefrontal"]
)

_DESTRIEUX_LABELS: dict[str, list[str]] = {
    "visual_cortex": [
        "G_cuneus", "G_occipital_sup", "G_occipital_middle",
        "G_oc-temp_med-Lingual", "G_and_S_occipital_inf",
        "Pole_occipital", "S_calcarine", "S_oc_middle_and_Lunatus",
        "S_oc_sup_and_transversal", "S_occipital_ant", "S_parieto_occipital",
    ],
    "face_social": [
        "G_oc-temp_lat-fusifor",
        "G_temp_sup-Lateral",
        "S_temporal_sup",
        "G_temp_sup-G_T_transv",
        "G_temp_sup-Plan_tempo",
    ],
    "language_areas": [
        "G_front_inf-Opercular",
        "G_front_inf-Triangul",
        "G_front_inf-Orbital",
        "G_temp_sup-Lateral",
        "S_temporal_sup",
        "G_temporal_middle",
        "G_pariet_inf-Angular",
        "G_pariet_inf-Supramar",
        "S_front_inf",
    ],
    "motor_action": [
        "G_precentral",
        "S_precentral-inf-part",
        "S_precentral-sup-part",
        "G_and_S_paracentral",
        "G_and_S_subcentral",
    ],
    "prefrontal": [
        "G_front_sup",
        "G_front_middle",
        "S_front_sup",
        "S_front_middle",
        "G_and_S_cingul-Ant",
        "G_and_S_cingul-Mid-Ant",
        "G_orbital",
        "G_rectus",
        "G_and_S_frontomargin",
        "G_and_S_transv_frontopol",
        "S_front_inf",
    ],
}


@lru_cache(maxsize=1)
def _load_atlas() -> tuple[np.ndarray, list[str]]:
    from nilearn import datasets
    atlas = datasets.fetch_atlas_surf_destrieux()
    label_names = [
        lbl.decode() if isinstance(lbl, bytes) else lbl
        for lbl in atlas.labels
    ]
    labels = np.concatenate([atlas.map_left, atlas.map_right])
    return labels, label_names


def get_vertex_masks() -> dict[str, np.ndarray]:
    """Bool mask per cortical region, shape (20484,), using Destrieux atlas."""
    labels, label_names = _load_atlas()
    masks: dict[str, np.ndarray] = {}
    for region, region_label_names in _DESTRIEUX_LABELS.items():
        label_ids = {i for i, name in enumerate(label_names) if name in region_label_names}
        masks[region] = np.isin(labels, list(label_ids))
    return masks


def vertex_activations_to_scores(
    preds: np.ndarray,
    masks: dict[str, np.ndarray],
) -> dict[str, int]:
    """
    Convert TRIBE vertex predictions (n_timesteps, n_vertices) to 0-100 scores.
    Z-score normalises region means vs global brain mean/std. z=0 -> 50, z=+2 -> 100.
    """
    mean_act = preds.mean(axis=0)
    global_mean = float(mean_act.mean())
    global_std = float(mean_act.std())
    if not np.isfinite(global_std) or global_std == 0.0:
        global_std = 1.0
    scores: dict[str, int] = {}
    for region, mask in masks.items():
        if mask.any():
            region_mean = float(mean_act[mask].mean())
        else:
            _log.warning("Atlas region '%s' has no vertices — using global mean", region)
            region_mean = global_mean
        z = (region_mean - global_mean) / global_std
        scores[region] = int(np.clip(round(50.0 + z * 25.0), 0, 100))
    return scores
