"""Matplotlib tabanlı TSP animasyon motoru."""

from __future__ import annotations

from typing import Callable, Generator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection

from tsp.problem import AlgorithmStep, TSPProblem


class TSPVisualizer:
    """Algoritma adımlarını animasyonlu olarak gösterir."""

    def __init__(self, problem: TSPProblem, interval: int = 80):
        self.problem = problem
        self.interval = interval
        self.cities = problem.cities

    def animate(
        self,
        steps: list[AlgorithmStep],
        title: str,
        show_pheromone: bool = False,
    ) -> AlgorithmStep:
        """Adım listesini animasyon olarak oynatır, son adımı döndürür."""
        if not steps:
            raise ValueError("Animasyon için en az bir adım gerekli.")

        fig, ax = plt.subplots(figsize=(9, 7))
        fig.patch.set_facecolor("#0f1419")
        ax.set_facecolor("#1a2332")

        # Şehir noktaları
        ax.scatter(
            self.cities[:, 0],
            self.cities[:, 1],
            c="#4fc3f7",
            s=80,
            zorder=5,
            edgecolors="white",
            linewidths=0.8,
        )
        for i, (x, y) in enumerate(self.cities):
            ax.annotate(
                str(i),
                (x, y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                color="#b0bec5",
            )

        margin = self.problem.size * 0.05
        ax.set_xlim(-margin, self.problem.size + margin)
        ax.set_ylim(-margin, self.problem.size + margin)
        ax.set_aspect("equal")
        ax.tick_params(colors="#78909c")
        for spine in ax.spines.values():
            spine.set_color("#37474f")

        # Çizgi nesneleri
        (current_line,) = ax.plot([], [], color="#ef5350", linewidth=1.5, alpha=0.7, zorder=3, label="Mevcut")
        (best_line,) = ax.plot([], [], color="#66bb6a", linewidth=2.5, alpha=0.9, zorder=4, label="En iyi")
        pheromone_collection = LineCollection([], colors="#ffb74d", alpha=0.3, zorder=1)
        ax.add_collection(pheromone_collection)

        info_text = ax.text(
            0.02,
            0.98,
            "",
            transform=ax.transAxes,
            fontsize=10,
            color="#eceff1",
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#263238", alpha=0.85, edgecolor="#455a64"),
        )

        ax.set_title(title, color="#eceff1", fontsize=14, pad=12)
        ax.legend(loc="lower right", facecolor="#263238", edgecolor="#455a64", labelcolor="#eceff1")

        def _tour_xy(tour: list[int]) -> tuple[np.ndarray, np.ndarray]:
            if len(tour) < 2:
                pts = self.cities[tour]
                return pts[:, 0], pts[:, 1]
            closed = tour + [tour[0]]
            pts = self.cities[closed]
            return pts[:, 0], pts[:, 1]

        def update(frame: int):
            step = steps[frame]
            xs, ys = _tour_xy(step.tour)
            current_line.set_data(xs, ys)

            best = step.best_tour if step.best_tour is not None else step.tour
            bxs, bys = _tour_xy(best)
            best_line.set_data(bxs, bys)

            if show_pheromone and step.pheromone is not None:
                segments = []
                widths = []
                ph = step.pheromone
                max_ph = ph.max() if ph.max() > 0 else 1.0
                n = self.problem.n_cities
                threshold = 0.15 * max_ph
                for i in range(n):
                    for j in range(i + 1, n):
                        if ph[i, j] > threshold:
                            segments.append([self.cities[i], self.cities[j]])
                            widths.append(0.5 + 3.0 * (ph[i, j] / max_ph))
                pheromone_collection.set_segments(segments)
                if widths:
                    pheromone_collection.set_linewidths(widths)

            best_cost = step.best_cost if step.best_cost is not None else step.cost
            lines = [
                f"İterasyon : {step.iteration}",
                f"Mevcut    : {step.cost:.2f}",
                f"En iyi    : {best_cost:.2f}",
            ]
            if step.temperature is not None:
                lines.append(f"Sıcaklık  : {step.temperature:.4f}")
            if step.info:
                lines.append(step.info)
            info_text.set_text("\n".join(lines))
            return current_line, best_line, pheromone_collection, info_text

        anim = FuncAnimation(
            fig,
            update,
            frames=len(steps),
            interval=self.interval,
            blit=False,
            repeat=False,
        )
        # Referansı tut (GC önlemek için)
        fig._tsp_anim = anim  # type: ignore[attr-defined]
        plt.tight_layout()
        plt.show()
        return steps[-1]

    def run_algorithm(
        self,
        algorithm_fn: Callable[..., Generator[AlgorithmStep, None, None]],
        title: str,
        show_pheromone: bool = False,
        **kwargs,
    ) -> AlgorithmStep:
        """Algoritmayı çalıştırıp adımları toplar ve animasyonu gösterir."""
        steps = list(algorithm_fn(self.problem, **kwargs))
        return self.animate(steps, title=title, show_pheromone=show_pheromone)
