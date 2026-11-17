"""Karınca Kolonisi Algoritması – 0-1 Sırt Çantası için."""

from __future__ import annotations

from typing import Generator

import numpy as np

from algorithms.knapsack import KnapsackProblem, KnapsackStep


def ant_colony_knapsack(
    problem: KnapsackProblem,
    n_ants: int = 30,
    n_iterations: int = 60,
    alpha: float = 1.0,
    beta: float = 2.0,
    rho: float = 0.15,
    q: float = 100.0,
    seed: int = 42,
) -> Generator[KnapsackStep, None, None]:
    """
    ACO ile 0-1 knapsack çözümü.

    Her eşya bir düğüm; feromon τ_i eşyanın seçilme eğilimini,
    sezgisel η_i = değer/ağırlık oranını temsil eder.
    Karıncalar kapasite dolana kadar olasılıksal eşya seçer.
    """
    rng = np.random.default_rng(seed)
    n = problem.n_items
    weights = problem.weights
    values = problem.values
    heuristic = problem.ratios.copy()
    heuristic[heuristic <= 0] = 1e-10

    pheromone = np.ones(n, dtype=float)

    best_selected: list[int] = []
    best_value = 0.0
    best_weight = 0.0

    yield KnapsackStep(
        selected=[],
        total_value=0.0,
        total_weight=0.0,
        iteration=0,
        info=f"Başlangıç – {n_ants} karınca, kapasite {problem.capacity:.1f} {problem.unit_weight}",
        best_selected=[],
        best_value=0.0,
        best_weight=0.0,
        pheromone=pheromone.copy(),
    )

    for iteration in range(1, n_iterations + 1):
        all_solutions: list[list[int]] = []
        all_values: list[float] = []
        all_weights: list[float] = []

        for _ in range(n_ants):
            selected = _construct_solution(
                pheromone, heuristic, weights, problem.capacity, alpha, beta, rng
            )
            value, weight = problem.evaluate(selected)
            all_solutions.append(selected)
            all_values.append(value)
            all_weights.append(weight)
            if value > best_value or (value == best_value and weight < best_weight):
                best_value = value
                best_weight = weight
                best_selected = selected.copy()

        # Buharlaşma
        pheromone *= 1.0 - rho

        # Biriktirme – daha yüksek değer daha fazla feromon
        for selected, value in zip(all_solutions, all_values):
            if value <= 0:
                continue
            deposit = q * (value / max(best_value, 1.0))
            for i in selected:
                pheromone[i] += deposit

        # En iyi çözüme ekstra takviye
        if best_selected:
            elite = q * 1.5
            for i in best_selected:
                pheromone[i] += elite

        pheromone = np.clip(pheromone, 0.05, None)

        yield KnapsackStep(
            selected=best_selected.copy(),
            total_value=best_value,
            total_weight=best_weight,
            iteration=iteration,
            info=f"En iyi değer: {best_value:.0f} {problem.unit_value} / {best_weight:.1f} {problem.unit_weight}",
            best_selected=best_selected.copy(),
            best_value=best_value,
            best_weight=best_weight,
            pheromone=pheromone.copy(),
            done=(iteration == n_iterations),
        )


def _construct_solution(
    pheromone: np.ndarray,
    heuristic: np.ndarray,
    weights: np.ndarray,
    capacity: float,
    alpha: float,
    beta: float,
    rng: np.random.Generator,
) -> list[int]:
    """Kapasite dolana kadar olasılıksal eşya seçimi."""
    n = len(pheromone)
    remaining = set(range(n))
    selected: list[int] = []
    used = 0.0

    while remaining:
        feasible = [i for i in remaining if used + weights[i] <= capacity + 1e-9]
        if not feasible:
            break

        probs = np.array(
            [(pheromone[i] ** alpha) * (heuristic[i] ** beta) for i in feasible],
            dtype=float,
        )
        total = probs.sum()
        if total <= 0 or not np.isfinite(total):
            probs = np.ones(len(feasible)) / len(feasible)
        else:
            probs = probs / total

        choice = int(rng.choice(feasible, p=probs))
        selected.append(choice)
        remaining.remove(choice)
        used += float(weights[choice])

    return selected
