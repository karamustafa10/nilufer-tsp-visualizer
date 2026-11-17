"""0-1 Sırt Çantası (Knapsack) problemi tanımı."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class KnapsackItem:
    id: int
    weight: float
    value: float

    @property
    def ratio(self) -> float:
        return self.value / self.weight if self.weight > 0 else 0.0


@dataclass
class KnapsackStep:
    """ACO iterasyon adımı – web animasyonu için."""

    selected: list[int]
    total_value: float
    total_weight: float
    iteration: int
    info: str = ""
    best_selected: list[int] | None = None
    best_value: float | None = None
    best_weight: float | None = None
    pheromone: np.ndarray | None = None
    done: bool = False


@dataclass
class KnapsackProblem:
    items: list[KnapsackItem]
    capacity: float
    seed: int = 42
    unit_value: str = "TL"
    unit_weight: str = "kg"

    @property
    def n_items(self) -> int:
        return len(self.items)

    @property
    def weights(self) -> np.ndarray:
        return np.array([it.weight for it in self.items], dtype=float)

    @property
    def values(self) -> np.ndarray:
        return np.array([it.value for it in self.items], dtype=float)

    @property
    def ratios(self) -> np.ndarray:
        return np.array([it.ratio for it in self.items], dtype=float)

    def evaluate(self, selected: list[int]) -> tuple[float, float]:
        """Seçilen eşyaların (değer, ağırlık) toplamını döndür."""
        w = sum(self.items[i].weight for i in selected)
        v = sum(self.items[i].value for i in selected)
        return float(v), float(w)

    def is_feasible(self, selected: list[int]) -> bool:
        _, w = self.evaluate(selected)
        return w <= self.capacity + 1e-9

    def to_dict(self) -> dict[str, Any]:
        return {
            "capacity": float(self.capacity),
            "seed": self.seed,
            "unit_value": self.unit_value,
            "unit_weight": self.unit_weight,
            "items": [
                {
                    "id": it.id,
                    "label": f"Eşya {it.id + 1}",
                    "weight": float(it.weight),
                    "value": float(it.value),
                    "ratio": float(it.ratio),
                }
                for it in self.items
            ],
        }

    @classmethod
    def random(
        cls,
        n_items: int = 18,
        capacity_ratio: float = 0.45,
        seed: int = 42,
        weight_range: tuple[float, float] = (1.0, 15.0),
        value_range: tuple[float, float] = (10.0, 100.0),
    ) -> KnapsackProblem:
        """Rastgele eşyalarla örnek problem üret."""
        rng = np.random.default_rng(seed)
        weights = rng.uniform(weight_range[0], weight_range[1], size=n_items)
        values = rng.uniform(value_range[0], value_range[1], size=n_items)
        # Daha okunaklı sayılar
        weights = np.round(weights, 1)
        values = np.round(values, 0)
        items = [
            KnapsackItem(id=i, weight=float(weights[i]), value=float(values[i]))
            for i in range(n_items)
        ]
        capacity = float(np.round(weights.sum() * capacity_ratio, 1))
        return cls(items=items, capacity=capacity, seed=seed)
