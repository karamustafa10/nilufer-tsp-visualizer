"""TSP (Travelling Salesman Problem) problem tanımı ve yardımcı fonksiyonlar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class AlgorithmStep:
    """Algoritmanın her adımında görselleştiriciye gönderilen durum."""

    tour: list[int]
    cost: float
    iteration: int
    info: str = ""
    best_tour: Optional[list[int]] = None
    best_cost: Optional[float] = None
    pheromone: Optional[np.ndarray] = None
    particles: Optional[list[list[int]]] = None
    temperature: Optional[float] = None
    done: bool = False


class TSPProblem:
    """Rastgele şehirler ve mesafe matrisi üreten TSP problemi."""

    def __init__(
        self,
        n_cities: int = 15,
        seed: int = 42,
        size: float = 100.0,
        cities: Optional[np.ndarray] = None,
        distances: Optional[np.ndarray] = None,
        labels: Optional[list[str]] = None,
        unit: str = "",
        region_name: str = "",
        road_network=None,
    ):
        self.n_cities = n_cities
        self.seed = seed
        self.size = size
        self.unit = unit
        self.region_name = region_name
        self.labels = labels or [str(i) for i in range(n_cities)]
        self.road_network = road_network

        if cities is not None and distances is not None:
            self.cities = np.asarray(cities, dtype=float)
            self.distances = np.asarray(distances, dtype=float)
            self.n_cities = len(self.cities)
            if labels is not None:
                self.labels = labels
        else:
            rng = np.random.default_rng(seed)
            self.cities = rng.uniform(0, size, size=(n_cities, 2))
            self.distances = self._compute_distance_matrix()

    @classmethod
    def nilufer(
        cls,
        n_cities: int = 12,
        seed: int = 42,
        use_roads: bool = True,
    ) -> "TSPProblem":
        """Bursa Nilüfer mahallelerinden rastgele TSP örneği oluştur."""
        from tsp.geo import sample_nilufer_locations

        cities, distances, labels = sample_nilufer_locations(n=n_cities, seed=seed)
        road_network = None
        region = "Bursa Nilüfer"

        if use_roads:
            from tsp.roads import RoadNetwork

            road_network = RoadNetwork(cities, align_to_roads=True)
            # Gorselde marker = yol dugumu (rota gercekten noktaya ugrar)
            cities = road_network.cities
            distances = road_network.distances_km
            region = "Bursa Nilüfer (gercek yollar)"

        return cls(
            n_cities=n_cities,
            seed=seed,
            cities=cities,
            distances=distances,
            labels=labels,
            unit="km",
            region_name=region,
            road_network=road_network,
        )

    def _compute_distance_matrix(self) -> np.ndarray:
        diff = self.cities[:, None, :] - self.cities[None, :, :]
        return np.sqrt(np.sum(diff ** 2, axis=-1))

    def tour_length(self, tour: list[int] | np.ndarray) -> float:
        """Kapalı turun toplam uzunluğunu hesapla."""
        tour = list(tour)
        total = 0.0
        for i in range(len(tour)):
            a = tour[i]
            b = tour[(i + 1) % len(tour)]
            total += self.distances[a, b]
        return float(total)

    def random_tour(self, rng: Optional[np.random.Generator] = None) -> list[int]:
        if rng is None:
            rng = np.random.default_rng()
        tour = list(range(self.n_cities))
        rng.shuffle(tour)
        return tour
