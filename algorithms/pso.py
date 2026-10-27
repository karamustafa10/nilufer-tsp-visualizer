"""Particle Swarm Optimization – TSP için permütasyon tabanlı PSO."""

from __future__ import annotations

from typing import Generator

import numpy as np

from tsp.problem import AlgorithmStep, TSPProblem


def _move_toward(current: list[int], target: list[int], strength: float, rng: np.random.Generator) -> list[int]:
    """
    Mevcut turu hedef tura yaklaştır.
    strength kadar rastgele pozisyonda hedefteki komşuluk ilişkilerini uygular.
    """
    result = current.copy()
    n = len(result)
    n_moves = max(1, int(strength * n))
    for _ in range(n_moves):
        # Hedefteki bir şehrin ardılını mevcut turda da ardıl yap
        pos = int(rng.integers(0, n))
        city = target[pos]
        next_city = target[(pos + 1) % n]
        i = result.index(city)
        j = result.index(next_city)
        # next_city'yi city'nin hemen sonrasına taşı
        result.pop(j)
        if j < i:
            i -= 1
        insert_at = (i + 1) % n
        result.insert(insert_at, next_city)
    return result


def _two_opt_random(tour: list[int], rng: np.random.Generator) -> list[int]:
    result = tour.copy()
    i, j = sorted(rng.integers(0, len(result), size=2))
    if i != j:
        result[i : j + 1] = reversed(result[i : j + 1])
    return result


def particle_swarm_optimization(
    problem: TSPProblem,
    n_particles: int = 40,
    n_iterations: int = 100,
    w: float = 0.3,
    c1: float = 0.35,
    c2: float = 0.35,
    seed: int = 42,
) -> Generator[AlgorithmStep, None, None]:
    """
    Permütasyon tabanlı PSO.
    Her iterasyonda parçacıkların en iyi turunu yield eder.
    """
    rng = np.random.default_rng(seed)

    # Normalize ağırlıklar
    total = w + c1 + c2
    w, c1, c2 = w / total, c1 / total, c2 / total

    particles = [problem.random_tour(rng) for _ in range(n_particles)]
    personal_best = [p.copy() for p in particles]
    personal_best_cost = [problem.tour_length(p) for p in personal_best]

    best_idx = int(np.argmin(personal_best_cost))
    global_best = personal_best[best_idx].copy()
    global_best_cost = personal_best_cost[best_idx]

    yield AlgorithmStep(
        tour=global_best.copy(),
        cost=global_best_cost,
        iteration=0,
        info=f"Başlangıç – {n_particles} parçacık",
        best_tour=global_best.copy(),
        best_cost=global_best_cost,
        particles=[p.copy() for p in particles],
    )

    for iteration in range(1, n_iterations + 1):
        for i in range(n_particles):
            r = rng.random()
            if r < w:
                candidate = _two_opt_random(particles[i], rng)
            elif r < w + c1:
                candidate = _move_toward(particles[i], personal_best[i], strength=0.3, rng=rng)
            else:
                candidate = _move_toward(particles[i], global_best, strength=0.3, rng=rng)

            # Küçük rastgele keşif
            if rng.random() < 0.2:
                candidate = _two_opt_random(candidate, rng)

            cost = problem.tour_length(candidate)
            particles[i] = candidate

            if cost < personal_best_cost[i]:
                personal_best[i] = candidate.copy()
                personal_best_cost[i] = cost
                if cost < global_best_cost:
                    global_best = candidate.copy()
                    global_best_cost = cost

        yield AlgorithmStep(
            tour=global_best.copy(),
            cost=global_best_cost,
            iteration=iteration,
            info=f"En iyi maliyet: {global_best_cost:.2f}",
            best_tour=global_best.copy(),
            best_cost=global_best_cost,
            particles=[p.copy() for p in particles],
            done=(iteration == n_iterations),
        )
