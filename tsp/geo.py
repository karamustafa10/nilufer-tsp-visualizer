"""Bursa Nilüfer konum üretimi ve coğrafi mesafe hesapları."""

from __future__ import annotations

import numpy as np

# Bilinen Nilüfer mahalle / semt merkezleri (lat, lon)
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
    ("Atlas", 40.12237, 28.88512),
    ("İrfaniye", 40.21658, 28.81714),
    ("Konaklı", 40.25623, 28.75817),
    ("Yolçatı", 40.25827, 28.86994),
    ("Başköy", 40.21175, 28.75272),
    ("Üçpınar", 40.10407, 28.84167),
    ("Fadıllı", 40.15363, 28.70969),
]

# Daha yoğun kentsel alan (haritada daha okunaklı)
NILUFER_URBAN_BBOX = {
    "lat_min": 40.15,
    "lat_max": 40.26,
    "lon_min": 28.82,
    "lon_max": 28.99,
}


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
    jitter_deg: float = 0.008,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Nilüfer mahalle merkezlerinden rastgele noktalar seçer ve hafif kaydırır.

    Returns
    -------
    cities : (N, 2) array of (lon, lat)  — matplotlib x/y için
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
        lat += rng.uniform(-jitter_deg, jitter_deg)
        lon += rng.uniform(-jitter_deg, jitter_deg)
        # Kentsel bbox içinde tut
        lat = float(np.clip(lat, NILUFER_URBAN_BBOX["lat_min"], NILUFER_URBAN_BBOX["lat_max"]))
        lon = float(np.clip(lon, NILUFER_URBAN_BBOX["lon_min"], NILUFER_URBAN_BBOX["lon_max"]))
        lats[k] = lat
        lons[k] = lon
        labels.append(name)

    cities = np.column_stack([lons, lats])  # (lon, lat)
    distances = haversine_matrix(lats, lons)
    return cities, distances, labels
