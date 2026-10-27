"""Simulated Annealing – TSP için 2-opt komşuluklu SA."""

from __future__ import annotations

from typing import Generator

import numpy as np

from tsp.problem import AlgorithmStep, TSPProblem


def _two_opt(tour: list[int], i: int, j: int) -> list[int]:
    """i..j aralığını ters çevir (2-opt hareketi)."""
    new_tour = tour.copy()
    new_tour[i : j + 1] = reversed(new_tour[i : j + 1])
    return new_tour


def simulated_annealing(
    problem: TSPProblem,
    t0: float = 100.0,
    t_min: float = 1e-3,
    cooling_rate: float = 0.995,
    max_iterations: int = 2000,
    seed: int = 42,
) -> Generator[AlgorithmStep, None, None]:
    """
    Simulated Annealing.
    Periyodik olarak mevcut tur, en iyi tur ve sıcaklığı yield eder.
    """
    rng = np.random.default_rng(seed)
    n = problem.n_cities

    current = problem.random_tour(rng)
    current_cost = problem.tour_length(current)
    best = current.copy()
    best_cost = current_cost
    temperature = t0

    yield_every = max(1, max_iterations // 80)

    yield AlgorithmStep(
        tour=current.copy(),
        cost=current_cost,
        iteration=0,
        info=f"Başlangıç sıcaklığı: {temperature:.2f}",
        best_tour=best.copy(),
        best_cost=best_cost,
        temperature=temperature,
    )

    iteration = 0
    while temperature > t_min and iteration < max_iterations:
        iteration += 1
        i, j = sorted(rng.integers(0, n, size=2))
        if i == j:
            continue

        candidate = _two_opt(current, i, j)
        candidate_cost = problem.tour_length(candidate)
        delta = candidate_cost - current_cost

        if delta < 0 or rng.random() < np.exp(-delta / temperature):
            current = candidate
            current_cost = candidate_cost
            if current_cost < best_cost:
                best = current.copy()
                best_cost = current_cost

        temperature *= cooling_rate

        if iteration % yield_every == 0 or temperature <= t_min or iteration >= max_iterations:
            yield AlgorithmStep(
                tour=current.copy(),
                cost=current_cost,
                iteration=iteration,
                info=f"T={temperature:.4f} | En iyi: {best_cost:.2f}",
                best_tour=best.copy(),
                best_cost=best_cost,
                temperature=temperature,
                done=(temperature <= t_min or iteration >= max_iterations),
            )
