"""Algoritma sonucunu web arayuzu icin JSON'a cevir."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from tsp.common import AlgoTrack, resample_steps
from tsp.problem import TSPProblem


def _simplify_polyline(
    lons: np.ndarray,
    lats: np.ndarray,
    max_points: int = 180,
) -> list[list[float]]:
    """Leaflet icin [lat, lon] listesi; fazla noktayi seyrelt."""
    if len(lons) == 0:
        return []
    if len(lons) <= max_points:
        return [[float(lat), float(lon)] for lon, lat in zip(lons, lats)]
    idx = np.linspace(0, len(lons) - 1, max_points).astype(int)
    return [[float(lats[i]), float(lons[i])] for i in idx]


def _route_coords(
    problem: TSPProblem,
    tour: list[int],
    cache: dict[tuple[int, ...], list[list[float]]],
) -> list[list[float]]:
    key = tuple(tour)
    if key in cache:
        return cache[key]
    if problem.road_network is not None and len(tour) >= 2:
        lons, lats = problem.road_network.tour_polyline(tour, closed=True)
    else:
        closed = tour + [tour[0]] if len(tour) > 1 else tour
        pts = problem.cities[closed]
        lons, lats = pts[:, 0], pts[:, 1]
    coords = _simplify_polyline(np.asarray(lons), np.asarray(lats))
    cache[key] = coords
    return coords


def build_payload(
    problem: TSPProblem,
    tracks: list[AlgoTrack],
    n_frames: int = 80,
) -> dict[str, Any]:
    route_cache: dict[tuple[int, ...], list[list[float]]] = {}
    algorithms = []

    for track in tracks:
        aligned = resample_steps(track.steps, n_frames)
        frames = []
        for step in aligned:
            best_tour = step.best_tour if step.best_tour is not None else step.tour
            best_cost = step.best_cost if step.best_cost is not None else step.cost
            frames.append(
                {
                    "iteration": int(step.iteration),
                    "cost": float(step.cost),
                    "best_cost": float(best_cost),
                    "info": step.info,
                    "route": _route_coords(problem, best_tour, route_cache),
                }
            )

        last = track.steps[-1]
        final_tour = last.best_tour if last.best_tour is not None else last.tour
        final_cost = last.best_cost if last.best_cost is not None else last.cost
        algorithms.append(
            {
                "name": track.name,
                "color": track.color,
                "elapsed_sec": float(track.elapsed_sec),
                "final_cost": float(final_cost),
                "final_iterations": int(last.iteration),
                "final_route": _route_coords(problem, final_tour, route_cache),
                "frames": frames,
            }
        )

    points = []
    for i, label in enumerate(problem.labels):
        lon, lat = problem.cities[i]
        points.append({"id": i, "label": label, "lat": float(lat), "lon": float(lon)})

    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    return {
        "meta": {
            "region": problem.region_name,
            "unit": problem.unit or "km",
            "n_frames": n_frames,
            "interval_ms": 140,
            "seed": problem.seed,
            "n_points": problem.n_cities,
        },
        "bounds": {
            "south": min(lats) - 0.01,
            "north": max(lats) + 0.01,
            "west": min(lons) - 0.01,
            "east": max(lons) + 0.01,
        },
        "points": points,
        "algorithms": algorithms,
    }


def write_web_data(
    problem: TSPProblem,
    tracks: list[AlgoTrack],
    out_dir: Path,
    n_frames: int = 80,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(problem, tracks, n_frames=n_frames)
    data_path = out_dir / "data.json"
    data_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return data_path
