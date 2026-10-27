"""Greedy Search – En Yakın Komşu (Nearest Neighbor) algoritması."""

from __future__ import annotations

from typing import Generator

from tsp.problem import AlgorithmStep, TSPProblem


def greedy_search(
    problem: TSPProblem,
    start: int = 0,
) -> Generator[AlgorithmStep, None, None]:
    """
    En yakın komşu sezgisi ile TSP turu oluşturur.
    Her şehir seçiminde bir adım yield eder.
    """
    n = problem.n_cities
    visited = [False] * n
    tour = [start]
    visited[start] = True
    current = start

    yield AlgorithmStep(
        tour=tour.copy(),
        cost=0.0,
        iteration=0,
        info=f"Başlangıç şehri: {start}",
        best_tour=tour.copy(),
        best_cost=0.0,
    )

    for step in range(1, n):
        nearest = None
        nearest_dist = float("inf")
        for city in range(n):
            if not visited[city]:
                d = problem.distances[current, city]
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = city

        assert nearest is not None
        tour.append(nearest)
        visited[nearest] = True
        current = nearest
        cost = problem.tour_length(tour) if len(tour) == n else _partial_cost(problem, tour)

        yield AlgorithmStep(
            tour=tour.copy(),
            cost=cost,
            iteration=step,
            info=f"Şehir {nearest} eklendi (mesafe: {nearest_dist:.2f})",
            best_tour=tour.copy(),
            best_cost=cost,
            done=(step == n - 1),
        )

    # Kapalı tur maliyeti
    final_cost = problem.tour_length(tour)
    yield AlgorithmStep(
        tour=tour.copy(),
        cost=final_cost,
        iteration=n,
        info=f"Tur tamamlandı. Toplam maliyet: {final_cost:.2f}",
        best_tour=tour.copy(),
        best_cost=final_cost,
        done=True,
    )


def _partial_cost(problem: TSPProblem, tour: list[int]) -> float:
    total = 0.0
    for i in range(len(tour) - 1):
        total += problem.distances[tour[i], tour[i + 1]]
    return float(total)
