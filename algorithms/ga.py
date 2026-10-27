"""Genetic Algorithm – TSP için sıralı GA (OX çaprazlama + swap mutasyon)."""

from __future__ import annotations

from typing import Generator

import numpy as np

from tsp.problem import AlgorithmStep, TSPProblem


def _order_crossover(
    parent1: list[int],
    parent2: list[int],
    rng: np.random.Generator,
) -> list[int]:
    """Order Crossover (OX)."""
    n = len(parent1)
    a, b = sorted(rng.integers(0, n, size=2))
    child = [-1] * n
    child[a : b + 1] = parent1[a : b + 1]
    fill = [gene for gene in parent2 if gene not in child]
    idx = 0
    for i in range(n):
        if child[i] == -1:
            child[i] = fill[idx]
            idx += 1
    return child


def _mutate(tour: list[int], mutation_rate: float, rng: np.random.Generator) -> list[int]:
    result = tour.copy()
    if rng.random() < mutation_rate:
        i, j = rng.integers(0, len(result), size=2)
        result[i], result[j] = result[j], result[i]
    return result


def _tournament_select(
    population: list[list[int]],
    costs: list[float],
    k: int,
    rng: np.random.Generator,
) -> list[int]:
    indices = rng.choice(len(population), size=k, replace=False)
    best = min(indices, key=lambda i: costs[i])
    return population[best].copy()


def genetic_algorithm(
    problem: TSPProblem,
    population_size: int = 50,
    n_generations: int = 100,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.2,
    tournament_size: int = 3,
    elitism: int = 2,
    seed: int = 42,
) -> Generator[AlgorithmStep, None, None]:
    """
    Genetik Algoritma.
    Her nesilde en iyi bireyi yield eder.
    """
    rng = np.random.default_rng(seed)

    population = [problem.random_tour(rng) for _ in range(population_size)]
    costs = [problem.tour_length(ind) for ind in population]

    best_idx = int(np.argmin(costs))
    best = population[best_idx].copy()
    best_cost = costs[best_idx]

    yield AlgorithmStep(
        tour=best.copy(),
        cost=best_cost,
        iteration=0,
        info=f"Başlangıç popülasyonu: {population_size}",
        best_tour=best.copy(),
        best_cost=best_cost,
    )

    for generation in range(1, n_generations + 1):
        # Elitizm
        ranked = sorted(range(population_size), key=lambda i: costs[i])
        new_population = [population[i].copy() for i in ranked[:elitism]]

        while len(new_population) < population_size:
            p1 = _tournament_select(population, costs, tournament_size, rng)
            p2 = _tournament_select(population, costs, tournament_size, rng)
            if rng.random() < crossover_rate:
                child = _order_crossover(p1, p2, rng)
            else:
                child = p1.copy()
            child = _mutate(child, mutation_rate, rng)
            new_population.append(child)

        population = new_population
        costs = [problem.tour_length(ind) for ind in population]

        gen_best_idx = int(np.argmin(costs))
        if costs[gen_best_idx] < best_cost:
            best = population[gen_best_idx].copy()
            best_cost = costs[gen_best_idx]

        yield AlgorithmStep(
            tour=population[gen_best_idx].copy(),
            cost=costs[gen_best_idx],
            iteration=generation,
            info=f"Nesil {generation} | En iyi: {best_cost:.2f}",
            best_tour=best.copy(),
            best_cost=best_cost,
            done=(generation == n_generations),
        )
