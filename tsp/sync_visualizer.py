"""Nilüfer haritasında 5 algoritmayı senkron gösteren animasyon."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Axes

from tsp.common import ALGORITHM_COLORS, AlgoTrack, resample_steps
from tsp.problem import AlgorithmStep, TSPProblem

try:
    import contextily as cx
except ImportError:  # pragma: no cover
    cx = None


# Geriye donuk uyumluluk
_resample = resample_steps


def _tour_lonlat(
    cities: np.ndarray,
    tour: list[int],
    road_network=None,
) -> tuple[np.ndarray, np.ndarray]:
    """Tur koordinatlari: varsa gercek yol geometrisi, yoksa kus bakisi."""
    if road_network is not None and len(tour) >= 2:
        return road_network.tour_polyline(tour, closed=True)
    if len(tour) == 0:
        return np.array([]), np.array([])
    if len(tour) == 1:
        pts = cities[tour]
        return pts[:, 0], pts[:, 1]
    closed = tour + [tour[0]]
    pts = cities[closed]
    return pts[:, 0], pts[:, 1]


def _provider_candidates():
    if cx is None:
        return []
    providers = []
    for path in (
        ("Esri", "WorldStreetMap"),
        ("Esri", "WorldTopoMap"),
        ("OpenStreetMap", "Mapnik"),
        ("OpenTopoMap",),
    ):
        try:
            node = cx.providers
            for key in path:
                node = getattr(node, key)
            providers.append(node)
        except Exception:
            continue
    return providers


def _fetch_basemap(extent: tuple[float, float, float, float]):
    """
    Harita karolarını bir kez indir.
    extent = (lon_min, lon_max, lat_min, lat_max)
    Returns (img, extent) in EPSG:4326 or None.
    """
    if cx is None:
        return None
    headers = {"User-Agent": "NiluferTSPVisualizer/1.0 (educational homework)"}
    west, east, south, north = extent
    for source in _provider_candidates():
        try:
            img, bound = cx.bounds2img(
                west,
                south,
                east,
                north,
                ll=True,
                source=source,
                zoom="auto",
                headers=headers,
            )
            # bound Web Mercator; lat/lon eksene basmak için yeniden projekte et
            img_wgs, extent_wgs = cx.warp_tiles(img, bound, "EPSG:4326")
            return img_wgs, extent_wgs
        except Exception:
            continue
    return None


def _add_basemap(ax: Axes, basemap=None, extent=None) -> None:
    if basemap is not None and extent is not None:
        ax.imshow(basemap, extent=extent, interpolation="bilinear", zorder=0)
        return
    if cx is None:
        ax.set_facecolor("#e8eef2")
        return
    headers = {"User-Agent": "NiluferTSPVisualizer/1.0 (educational homework)"}
    for source in _provider_candidates():
        try:
            cx.add_basemap(
                ax,
                crs="EPSG:4326",
                source=source,
                attribution=False,
                zoom="auto",
                headers=headers,
            )
            return
        except Exception:
            continue
    ax.set_facecolor("#e8eef2")


def _map_extent(problem: TSPProblem) -> tuple[float, float, float, float]:
    lons = problem.cities[:, 0]
    lats = problem.cities[:, 1]
    pad_lon = (lons.max() - lons.min()) * 0.18 + 0.01
    pad_lat = (lats.max() - lats.min()) * 0.18 + 0.01
    return (
        float(lons.min() - pad_lon),
        float(lons.max() + pad_lon),
        float(lats.min() - pad_lat),
        float(lats.max() + pad_lat),
    )


def _setup_map_axis(
    ax: Axes,
    problem: TSPProblem,
    title: str,
    color: str,
    basemap=None,
    basemap_extent=None,
) -> None:
    lon_min, lon_max, lat_min, lat_max = _map_extent(problem)
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    _add_basemap(ax, basemap=basemap, extent=basemap_extent)

    lons = problem.cities[:, 0]
    lats = problem.cities[:, 1]
    ax.scatter(
        lons,
        lats,
        c="#1565c0",
        s=55,
        zorder=6,
        edgecolors="white",
        linewidths=1.0,
    )
    for i, (lon, lat) in enumerate(problem.cities):
        label = problem.labels[i] if i < len(problem.labels) else str(i)
        ax.annotate(
            label,
            (lon, lat),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=7,
            color="#263238",
            fontweight="bold",
            zorder=7,
            path_effects=None,
        )

    ax.set_title(title, fontsize=11, color=color, fontweight="bold", pad=8)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(color)
        spine.set_linewidth(2.0)


class SyncMapVisualizer:
    """Tüm algoritmaları Nilüfer haritasında aynı anda animasyonlar."""

    def __init__(self, problem: TSPProblem, n_frames: int = 90, interval: int = 120):
        self.problem = problem
        self.n_frames = n_frames
        self.interval = interval

    def animate(self, tracks: list[AlgoTrack]) -> None:
        aligned = {
            t.name: _resample(t.steps, self.n_frames) for t in tracks
        }

        print("Harita karoları indiriliyor...")
        fetched = _fetch_basemap(_map_extent(self.problem))
        basemap_img, basemap_ext = (fetched if fetched else (None, None))

        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        fig.patch.set_facecolor("#f5f7fa")
        region = self.problem.region_name or "TSP"
        fig.suptitle(
            f"{region} – Algoritmalar Yan Yana",
            fontsize=16,
            fontweight="bold",
            color="#1a237e",
            y=0.98,
        )

        map_axes = [
            axes[0, 0],
            axes[0, 1],
            axes[0, 2],
            axes[1, 0],
            axes[1, 1],
        ]
        score_ax = axes[1, 2]

        best_lines = []
        current_lines = []
        info_texts = []

        for ax, track in zip(map_axes, tracks):
            _setup_map_axis(
                ax,
                self.problem,
                track.name,
                track.color,
                basemap=basemap_img,
                basemap_extent=basemap_ext,
            )
            (best_line,) = ax.plot(
                [], [], color=track.color, linewidth=2.8, alpha=0.95, zorder=5
            )
            (curr_line,) = ax.plot(
                [], [], color="#455a64", linewidth=1.2, alpha=0.45, linestyle="--", zorder=4
            )
            info = ax.text(
                0.02,
                0.02,
                "",
                transform=ax.transAxes,
                fontsize=8,
                color="#212121",
                va="bottom",
                fontfamily="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.35",
                    facecolor="white",
                    alpha=0.88,
                    edgecolor=track.color,
                ),
                zorder=8,
            )
            best_lines.append(best_line)
            current_lines.append(curr_line)
            info_texts.append(info)

        # Skor paneli
        score_ax.set_facecolor("#ffffff")
        score_ax.set_xlim(0, 1)
        score_ax.set_ylim(0, 1)
        score_ax.set_xticks([])
        score_ax.set_yticks([])
        for spine in score_ax.spines.values():
            spine.set_color("#90a4ae")
        score_ax.set_title("Canlı Skorlar", fontsize=11, color="#37474f", fontweight="bold")
        score_text = score_ax.text(
            0.05,
            0.95,
            "",
            transform=score_ax.transAxes,
            fontsize=10,
            color="#212121",
            va="top",
            fontfamily="monospace",
            linespacing=1.6,
        )
        unit = self.problem.unit or "birim"

        def update(frame: int):
            score_lines = [f"{'Algoritma':<10} {'En iyi':>8}  {'Durum'}"]
            score_lines.append("-" * 32)
            costs = []

            roads = self.problem.road_network
            for i, track in enumerate(tracks):
                step = aligned[track.name][frame]
                tour = step.tour
                best = step.best_tour if step.best_tour is not None else tour
                best_cost = step.best_cost if step.best_cost is not None else step.cost

                xs, ys = _tour_lonlat(self.problem.cities, best, road_network=roads)
                best_lines[i].set_data(xs, ys)

                cxs, cys = _tour_lonlat(self.problem.cities, tour, road_network=roads)
                current_lines[i].set_data(cxs, cys)

                info_texts[i].set_text(
                    f"iter {step.iteration}\nen iyi {best_cost:.2f} {unit}"
                )
                costs.append((track.name, best_cost, track.color))
                score_lines.append(f"{track.name:<10} {best_cost:>7.2f}  {step.info[:18]}")

            costs_sorted = sorted(costs, key=lambda x: x[1])
            score_lines.append("")
            score_lines.append(f"Lider: {costs_sorted[0][0]} ({costs_sorted[0][1]:.2f} {unit})")
            score_lines.append(f"Kare: {frame + 1}/{self.n_frames}")
            score_text.set_text("\n".join(score_lines))
            return best_lines + current_lines + info_texts + [score_text]

        anim = FuncAnimation(
            fig,
            update,
            frames=self.n_frames,
            interval=self.interval,
            blit=False,
            repeat=False,
        )
        fig._tsp_anim = anim  # type: ignore[attr-defined]
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()

    def show_comparison(self, tracks: list[AlgoTrack]) -> None:
        """Sonuç ekranı: maliyetler + en iyi turun Nilüfer haritası."""
        results = []
        for t in tracks:
            last = t.steps[-1]
            best_cost = last.best_cost if last.best_cost is not None else last.cost
            best_tour = last.best_tour if last.best_tour is not None else last.tour
            results.append((t.name, best_cost, best_tour, t.color, t.elapsed_sec, last.iteration))

        best_overall = min(results, key=lambda r: r[1])
        unit = self.problem.unit or ""

        fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
        fig.patch.set_facecolor("#f5f7fa")
        fig.suptitle(
            f"{self.problem.region_name} – Sonuç Karşılaştırması",
            fontsize=15,
            fontweight="bold",
            color="#1a237e",
        )

        names = [r[0] for r in results]
        costs = [r[1] for r in results]
        times = [r[4] for r in results]
        bar_colors = [r[3] for r in results]

        ax0 = axes[0]
        bars = ax0.bar(names, costs, color=bar_colors, edgecolor="white")
        ax0.set_ylabel(f"Tur uzunluğu ({unit})")
        ax0.set_title("En İyi Maliyet")
        ax0.set_facecolor("#ffffff")
        for bar, cost in zip(bars, costs):
            ax0.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{cost:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax1 = axes[1]
        ax1.bar(names, times, color=bar_colors, edgecolor="white")
        ax1.set_ylabel("Süre (s)")
        ax1.set_title("Çalışma Süresi")
        ax1.set_facecolor("#ffffff")

        ax2 = axes[2]
        fetched = _fetch_basemap(_map_extent(self.problem))
        bm_img, bm_ext = (fetched if fetched else (None, None))
        _setup_map_axis(
            ax2,
            self.problem,
            f"En iyi: {best_overall[0]}",
            best_overall[3],
            basemap=bm_img,
            basemap_extent=bm_ext,
        )
        xs, ys = _tour_lonlat(
            self.problem.cities,
            best_overall[2],
            road_network=self.problem.road_network,
        )
        ax2.plot(xs, ys, color=best_overall[3], linewidth=3.0, zorder=5)

        plt.tight_layout(rect=[0, 0, 1, 0.94])
        plt.show()

        print("\n" + "=" * 64)
        print(f"{'Algoritma':<20} {f'Maliyet({unit})':>14} {'İter.':>8} {'Süre(s)':>10}")
        print("-" * 64)
        for name, cost, _tour, _c, elapsed, iters in sorted(results, key=lambda x: x[1]):
            mark = " *" if name == best_overall[0] else ""
            print(f"{name:<20} {cost:>14.2f} {iters:>8} {elapsed:>10.3f}{mark}")
        print("=" * 64)
        print(f"* En iyi: {best_overall[0]} ({best_overall[1]:.2f} {unit})\n")
