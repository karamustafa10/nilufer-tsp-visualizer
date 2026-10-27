"""Ant Colony Optimization – TSP için klasik ACO (AS)."""

from __future__ import annotations

from typing import Generator

import numpy as np

from tsp.problem import AlgorithmStep, TSPProblem


def ant_colony_optimization(
    problem: TSPProblem,
    n_ants: int = 20,
    n_iterations: int = 60,
    alpha: float = 1.0,
    beta: float = 2.0,
    rho: float = 0.1,
    q: float = 100.0,
    seed: int = 42,
) -> Generator[AlgorithmStep, None, None]:
    """
    Ant System tabanlı ACO.
    Her iterasyonda feromon matrisi ve en iyi turu yield eder.
    """
    rng = np.random.default_rng(seed)
    n = problem.n_cities
    dist = problem.distances.copy()
    dist[dist == 0] = 1e-10  # sıfır bölme koruması

    pheromone = np.ones((n, n))
    heuristic = 1.0 / dist
    np.fill_diagonal(heuristic, 0.0)

    best_tour: list[int] = list(range(n))
    best_cost = float("inf")

    yield AlgorithmStep(
        tour=best_tour.copy(),
        cost=problem.tour_length(best_tour),
        iteration=0,
        info=f"Başlangıç – {n_ants} karınca",
        best_tour=best_tour.copy(),
        best_cost=problem.tour_length(best_tour),
        pheromone=pheromone.copy(),
    )

    for iteration in range(1, n_iterations + 1):
        all_tours: list[list[int]] = []
        all_costs: list[float] = []

        for _ in range(n_ants):
            tour = _construct_tour(pheromone, heuristic, alpha, beta, rng)
            cost = problem.tour_length(tour)
            all_tours.append(tour)
            all_costs.append(cost)
            if cost < best_cost:
                best_cost = cost
                best_tour = tour.copy()

        # Feromon buharlaşma
        pheromone *= 1.0 - rho

        # Feromon biriktirme
        for tour, cost in zip(all_tours, all_costs):
            deposit = q / cost
            for i in range(n):
                a, b = tour[i], tour[(i + 1) % n]
                pheromone[a, b] += deposit
                pheromone[b, a] += deposit

        yield AlgorithmStep(
            tour=best_tour.copy(),
            cost=best_cost,
            iteration=iteration,
            info=f"En iyi maliyet: {best_cost:.2f}",
            best_tour=best_tour.copy(),
            best_cost=best_cost,
            pheromone=pheromone.copy(),
            done=(iteration == n_iterations),
        )


def _construct_tour(
    pheromone: np.ndarray,
    heuristic: np.ndarray,
    alpha: float,
    beta: float,
    rng: np.random.Generator,
) -> list[int]:
    n = pheromone.shape[0]
    start = int(rng.integers(0, n))
    tour = [start]
    unvisited = set(range(n)) - {start}
    current = start

    while unvisited:
        candidates = list(unvisited)
        probs = np.array(
            [
                (pheromone[current, j] ** alpha) * (heuristic[current, j] ** beta)
                for j in candidates
            ]
        )
        total = probs.sum()
        if total <= 0 or not np.isfinite(total):
            probs = np.ones(len(candidates)) / len(candidates)
        else:
            probs = probs / total

        next_city = int(rng.choice(candidates, p=probs))
        tour.append(next_city)
        unvisited.remove(next_city)
        current = next_city

    return tour
