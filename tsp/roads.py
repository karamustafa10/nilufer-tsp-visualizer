"""OpenStreetMap yol agi uzerinden gercek rota ve mesafe hesabi (OSMnx)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import networkx as nx
import numpy as np

try:
    import osmnx as ox
except ImportError as exc:  # pragma: no cover
    raise ImportError("osmnx gerekli: pip install osmnx") from exc

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
GRAPH_PATH = CACHE_DIR / "nilufer_drive.graphml"
GRAPH_PATH_V2 = CACHE_DIR / "nilufer_drive_v2.graphml"

# Pad'li Nilufer bbox
NILUFER_BBOX = {
    "north": 40.275,
    "south": 40.100,
    "east": 29.020,
    "west": 28.720,
}


def _configure_osmnx() -> None:
    ox.settings.use_cache = True
    ox.settings.log_console = False
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_or_download_graph(force: bool = False):
    """Nilufer surus agini indir veya disk onbelleginden yukle."""
    _configure_osmnx()
    # Genis ag varsa onu tercih et; yoksa mevcut onbellegi kullan
    for path in (GRAPH_PATH_V2, GRAPH_PATH):
        if path.exists() and not force:
            print(f"Yol agi onbellekten yukleniyor: {path.name}")
            return ox.load_graphml(path)

    print("OpenStreetMap'ten Nilufer yol agi indiriliyor (ilk sefer uzun surebilir)...")
    # OSMnx 2.x: bbox = (left, bottom, right, top) = (west, south, east, north)
    G = ox.graph_from_bbox(
        bbox=(
            NILUFER_BBOX["west"],
            NILUFER_BBOX["south"],
            NILUFER_BBOX["east"],
            NILUFER_BBOX["north"],
        ),
        network_type="drive",
        simplify=True,
        retain_all=False,
    )
    ox.save_graphml(G, GRAPH_PATH)
    print(f"Yol agi kaydedildi: {GRAPH_PATH} ({len(G.nodes)} dugum, {len(G.edges)} kenar)")
    return G


def snap_points_to_nodes(G, cities: np.ndarray) -> list[int]:
    """
    cities: (N, 2) lon, lat
    Returns: OSM dugum id listesi
    """
    lons = cities[:, 0]
    lats = cities[:, 1]
    # osmnx >= 1.6: nearest_nodes(G, X, Y)
    nodes = ox.distance.nearest_nodes(G, X=lons, Y=lats)
    return [int(n) for n in nodes]


def _path_length_m(G, path: list[int]) -> float:
    total = 0.0
    for u, v in zip(path[:-1], path[1:]):
        data = min(G.get_edge_data(u, v).values(), key=lambda d: d.get("length", 0.0))
        total += float(data.get("length", 0.0))
    return total


def _path_coords(G, path: list[int]) -> list[tuple[float, float]]:
    """Dugum yolunu (lon, lat) polyline'a cevir."""
    if len(path) < 2:
        if not path:
            return []
        node = G.nodes[path[0]]
        return [(node["x"], node["y"])]

    coords: list[tuple[float, float]] = []
    for u, v in zip(path[:-1], path[1:]):
        data = min(G.get_edge_data(u, v).values(), key=lambda d: d.get("length", 0.0))
        if "geometry" in data:
            xs, ys = data["geometry"].xy
            segment = list(zip(xs, ys))
        else:
            segment = [
                (G.nodes[u]["x"], G.nodes[u]["y"]),
                (G.nodes[v]["x"], G.nodes[v]["y"]),
            ]
        if coords and segment and coords[-1] == segment[0]:
            coords.extend(segment[1:])
        else:
            coords.extend(segment)
    return coords


class RoadNetwork:
    """TSP noktalari icin yol mesafeleri ve rota geometrileri."""

    def __init__(self, cities: np.ndarray, graph=None, align_to_roads: bool = True):
        self.cities = np.asarray(cities, dtype=float).copy()
        self.G = graph if graph is not None else load_or_download_graph()
        self.nodes = snap_points_to_nodes(self.G, self.cities)
        self.n = len(self.cities)
        self.snap_distances_m = self._snap_distances_m()

        # Marker'lar rota uzerinde olsun diye noktalari yol dugumune tasi
        if align_to_roads:
            for i, node in enumerate(self.nodes):
                self.cities[i, 0] = float(self.G.nodes[node]["x"])
                self.cities[i, 1] = float(self.G.nodes[node]["y"])

        far = [(i, d) for i, d in enumerate(self.snap_distances_m) if d > 400]
        if far:
            print("Uyari: bazi noktalar yola uzak (snap > 400 m):")
            for i, d in far:
                print(f"  index {i}: {d:.0f} m")

        self._route_cache: dict[tuple[int, int], tuple[float, list[tuple[float, float]]]] = {}
        self.distances_km = self._build_distance_matrix()

    def _snap_distances_m(self) -> list[float]:
        from tsp.geo import haversine_km

        out = []
        for i, node in enumerate(self.nodes):
            lon, lat = self.cities[i]
            nx_ = self.G.nodes[node]["x"]
            ny_ = self.G.nodes[node]["y"]
            out.append(haversine_km(lat, lon, ny_, nx_) * 1000.0)
        return out

    def _route_between(self, i: int, j: int) -> tuple[float, list[tuple[float, float]]]:
        key = (i, j)
        if key in self._route_cache:
            return self._route_cache[key]

        src, dst = self.nodes[i], self.nodes[j]
        if src == dst:
            result = (0.0, [(self.cities[i, 0], self.cities[i, 1])])
            self._route_cache[key] = result
            return result

        try:
            path = nx.shortest_path(self.G, src, dst, weight="length")
            length_m = _path_length_m(self.G, path)
            coords = _path_coords(self.G, path)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # Yol yoksa kus bakisi yedek (km -> m)
            from tsp.geo import haversine_km

            length_m = haversine_km(
                self.cities[i, 1], self.cities[i, 0],
                self.cities[j, 1], self.cities[j, 0],
            ) * 1000.0
            coords = [
                (self.cities[i, 0], self.cities[i, 1]),
                (self.cities[j, 0], self.cities[j, 1]),
            ]

        result = (length_m / 1000.0, coords)
        self._route_cache[key] = result
        return result

    def _build_distance_matrix(self) -> np.ndarray:
        print("Noktalar arasi gercek yol mesafeleri hesaplaniyor...")
        dist = np.zeros((self.n, self.n), dtype=float)
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue
                km, _ = self._route_between(i, j)
                dist[i, j] = km
        return dist

    def tour_polyline(self, tour: list[int], closed: bool = True) -> tuple[np.ndarray, np.ndarray]:
        """Tur icin birlesik (lon, lat) polyline dondur."""
        if len(tour) == 0:
            return np.array([]), np.array([])
        if len(tour) == 1:
            return np.array([self.cities[tour[0], 0]]), np.array([self.cities[tour[0], 1]])

        sequence = list(tour)
        if closed and len(sequence) > 1:
            sequence = sequence + [sequence[0]]

        all_coords: list[tuple[float, float]] = []
        for a, b in zip(sequence[:-1], sequence[1:]):
            _, coords = self._route_between(a, b)
            if all_coords and coords and all_coords[-1] == coords[0]:
                all_coords.extend(coords[1:])
            else:
                all_coords.extend(coords)

        if not all_coords:
            return np.array([]), np.array([])
        arr = np.asarray(all_coords, dtype=float)
        return arr[:, 0], arr[:, 1]
