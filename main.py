"""
TSP Algoritma Gorsellestiricisi - Bursa Nilufer (Web)
-----------------------------------------------------
Gercek yollar uzerinde 5 algoritmayi HTML/CSS/Leaflet ile
ayni anda animasyonlu karsilastirir.
"""

from __future__ import annotations

import time

from algorithms import (
    ant_colony_optimization,
    genetic_algorithm,
    greedy_search,
    particle_swarm_optimization,
    simulated_annealing,
)
from tsp.problem import AlgorithmStep, TSPProblem
from tsp.common import ALGORITHM_COLORS, AlgoTrack
from tsp.web_export import write_web_data
from tsp.webapp import WEB_DIR, serve_and_open


def collect_steps(generator) -> tuple[list[AlgorithmStep], float]:
    t0 = time.perf_counter()
    steps = list(generator)
    return steps, time.perf_counter() - t0


def main() -> None:
    print("=" * 64)
    print("  TSP - Bursa Nilufer Algoritma Yarisi (Web)")
    print("  Greedy | PSO | ACO | Simulated Annealing | GA")
    print("=" * 64)

    n_cities = 12
    seed = 42
    n_frames = 80

    print("\nGercek yol agi (OpenStreetMap) hazirlaniyor...")
    problem = TSPProblem.nilufer(n_cities=n_cities, seed=seed, use_roads=True)

    print(f"\nBolge : {problem.region_name}")
    print(f"Nokta : {problem.n_cities} mahalle (seed={seed})")
    for i, label in enumerate(problem.labels):
        lon, lat = problem.cities[i]
        print(f"  {i:2d}. {label:<12}  {lat:.5f}, {lon:.5f}")
    print("\nAlgoritmalar calistiriliyor...\n")

    runs = [
        ("Greedy", greedy_search(problem, start=0)),
        ("PSO", particle_swarm_optimization(problem, n_particles=40, n_iterations=100, seed=seed)),
        ("ACO", ant_colony_optimization(problem, n_ants=20, n_iterations=60, seed=seed)),
        (
            "SA",
            simulated_annealing(
                problem, t0=50.0, cooling_rate=0.995, max_iterations=2000, seed=seed
            ),
        ),
        ("GA", genetic_algorithm(problem, population_size=50, n_generations=100, seed=seed)),
    ]

    tracks: list[AlgoTrack] = []
    for name, gen in runs:
        print(f"  > {name}...")
        steps, elapsed = collect_steps(gen)
        last = steps[-1]
        best = last.best_cost if last.best_cost is not None else last.cost
        print(f"     en iyi {best:.2f} {problem.unit} | {elapsed:.3f}s | {len(steps)} adim")
        tracks.append(
            AlgoTrack(
                name=name,
                steps=steps,
                color=ALGORITHM_COLORS[name],
                elapsed_sec=elapsed,
            )
        )

    print("\nWeb verisi hazirlaniyor (rota geometrileri)...")
    data_path = write_web_data(problem, tracks, WEB_DIR, n_frames=n_frames)
    print(f"  Yazildi: {data_path}")

    httpd = serve_and_open(port=8765, open_browser=True)
    print("\nArayuz acik. Kontroller:")
    print("  - Tam Ekran / Duraklat / kaydirici")
    print("  - Sonuclari Goster (pencereyi kapatmaya gerek yok)")
    print("  - Durdurmak icin bu terminalde Ctrl+C\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKapatiliyor...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
