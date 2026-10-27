"""Bursa Nilüfer konum üretimi ve coğrafi mesafe hesapları."""

from __future__ import annotations

import numpy as np

# Yol agi kapsamina guvenle dusen mahalleler (lat, lon).
# Not: Fadilli (~28.71) ag batisinda kaldigi icin listeden cikarildi;
# aksi halde marker ile rota birbirinden uzak dusuyordu.
NILUFER_LANDMARKS: list[tuple[str, float, float]] = [
    ("Beşevler", 40.20000, 28.95000),
    ("Görükle", 40.23114, 28.84017),
    ("Özlüce", 40.23791, 28.91001),
    ("İhsaniye", 40.21667, 28.98333),
    ("Ertuğrul", 40.21396, 28.92449),
    ("Çalı", 40.16861, 28.92083),
    ("Kayapa", 40.17179, 28.83945),
    ("Kültür", 40.20310, 28.96331),
    ("Misi", 40.17912, 28.97039),
    ("Tahtalı", 40.17535, 28.87707),
    ("Yaylacık", 40.17333, 28.90176),
    ("Atlas", 40.12240, 28.88430),
    ("İrfaniye", 40.21658, 28.81714),
    ("Yolçatı", 40.25827, 28.86994),
    ("Başköy", 40.21239, 28.75294),
    ("Üçpınar", 40.10407, 28.84167),
    ("Konaklı", 40.25623, 28.75817),
]

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki WGS84 noktası arasındaki büyük daire mesafesi (km)."""
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)))


def haversine_matrix(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """N nokta için NxN haversine mesafe matrisi (km)."""
    n = len(lats)
    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(lats[i], lons[i], lats[j], lons[j])
            dist[i, j] = dist[j, i] = d
    return dist


def sample_nilufer_locations(
    n: int = 12,
    seed: int = 42,
    jitter_deg: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Nilüfer mahalle merkezlerinden rastgele noktalar seçer.

    Not: Konumlar kırpılmaz; gerçek koordinatlar korunur.
    jitter_deg varsayılan 0 (doğruluk için).

    Returns
    -------
    cities : (N, 2) array of (lon, lat)
    distances : (N, N) haversine km
    labels : nokta etiketleri
    """
    rng = np.random.default_rng(seed)
    if n > len(NILUFER_LANDMARKS):
        raise ValueError(f"En fazla {len(NILUFER_LANDMARKS)} mahalle var.")

    indices = rng.choice(len(NILUFER_LANDMARKS), size=n, replace=False)
    labels: list[str] = []
    lats = np.zeros(n)
    lons = np.zeros(n)

    for k, idx in enumerate(indices):
        name, lat, lon = NILUFER_LANDMARKS[idx]
        if jitter_deg:
            lat += rng.uniform(-jitter_deg, jitter_deg)
            lon += rng.uniform(-jitter_deg, jitter_deg)
        lats[k] = float(lat)
        lons[k] = float(lon)
        labels.append(name)

    cities = np.column_stack([lons, lats])  # (lon, lat)
    distances = haversine_matrix(lats, lons)
    return cities, distances, labels
