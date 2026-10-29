"""
TSP Algoritma Gorsellestiricisi - Bursa Nilufer (Web)
-----------------------------------------------------
Gercek yollar uzerinde 5 algoritmayi HTML/CSS/Leaflet ile
ayni anda animasyonlu karsilastirir.
"""

from __future__ import annotations

import argparse
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
from tsp.web_export import write_odev2_data, write_web_data
from tsp.webapp import WEB_DIR, serve_and_open


def collect_steps(generator) -> tuple[list[AlgorithmStep], float]:
    t0 = time.perf_counter()
    steps = list(generator)
    return steps, time.perf_counter() - t0


def run_pipeline(n_cities: int = 12, seed: int = 42, n_frames: int = 80) -> list[AlgoTrack]:
    print("=" * 64)
    print("  TSP - Bursa Nilufer Algoritma Yarisi (Web)")
    print("  Greedy | PSO | ACO | Simulated Annealing | GA")
    print("=" * 64)

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
    return tracks


def run_odev2_export(n_cities: int = 12, seed: int = 42) -> None:
    """Odev 2: sadece Genetik Algoritma verisini uret."""
    print("=" * 64)
    print("  Odev 2 - TSP + Genetik Algoritma export")
    print("=" * 64)
    print("\nGercek yol agi hazirlaniyor...")
    problem = TSPProblem.nilufer(n_cities=n_cities, seed=seed, use_roads=True)
    params = {
        "population_size": 50,
        "n_generations": 100,
        "crossover_rate": 0.8,
        "mutation_rate": 0.2,
        "tournament_size": 3,
        "elitism": 2,
    }
    print("GA calistiriliyor...")
    steps, elapsed = collect_steps(
        genetic_algorithm(
            problem,
            population_size=params["population_size"],
            n_generations=params["n_generations"],
            crossover_rate=params["crossover_rate"],
            mutation_rate=params["mutation_rate"],
            tournament_size=params["tournament_size"],
            elitism=params["elitism"],
            seed=seed,
        )
    )
    last = steps[-1]
    best = last.best_cost if last.best_cost is not None else last.cost
    print(f"  en iyi {best:.2f} {problem.unit} | {elapsed:.3f}s")
    track = AlgoTrack(
        name="GA",
        steps=steps,
        color=ALGORITHM_COLORS["GA"],
        elapsed_sec=elapsed,
    )
    path = write_odev2_data(problem, track, WEB_DIR, n_frames=100, params=params)
    print(f"Yazildi: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Nilufer TSP web gorsellestirici")
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Sadece web/data.json uret, sunucu acma (GitHub Pages icin)",
    )
    parser.add_argument(
        "--export-odev2",
        action="store_true",
        help="Sadece Odev 2 GA sayfasi icin odev2-data.json uret",
    )
    args = parser.parse_args()

    if args.export_odev2:
        run_odev2_export()
        print("Odev 2 export tamam.")
        return

    run_pipeline()

    if args.export_only:
        print("Export tamam. Sunucu acilmiyor.")
        return

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
