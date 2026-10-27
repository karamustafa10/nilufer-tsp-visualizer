"""Paylasilan sabitler ve yardimci tipler."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tsp.problem import AlgorithmStep

ALGORITHM_COLORS = {
    "Greedy": "#ef5350",
    "PSO": "#42a5f5",
    "ACO": "#ffb74d",
    "SA": "#ab47bc",
    "GA": "#66bb6a",
}


@dataclass
class AlgoTrack:
    name: str
    steps: list[AlgorithmStep]
    color: str
    elapsed_sec: float = 0.0


def resample_steps(steps: list[AlgorithmStep], n_frames: int) -> list[AlgorithmStep]:
    """Farkli uzunluktaki adim listelerini ayni kare sayisina hizala."""
    if not steps:
        raise ValueError("Bos adim listesi")
    if len(steps) == 1:
        return steps * n_frames
    indices = np.linspace(0, len(steps) - 1, n_frames)
    return [steps[int(round(i))] for i in indices]
