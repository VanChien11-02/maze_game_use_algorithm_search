# algorithms/local/simulated_annealing.py - Local Search: Simulated Annealing

import math
import random
import time
from typing import List, Tuple

from algorithms.base import PathResult, Step


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbors(grid: List[List[int]], pos: Tuple[int, int],
               rows: int, cols: int) -> List[Tuple[int, int]]:
    r, c = pos
    result = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 0:
            result.append((nr, nc))
    return result


def _seed_for(start: Tuple[int, int], goal: Tuple[int, int], rows: int, cols: int) -> int:
    return (
        rows * 1009 + cols * 917
        + start[0] * 131 + start[1] * 137
        + goal[0] * 149 + goal[1] * 151
    )


def _loop_erased_path(path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Remove random-walk loops while keeping a legal start-to-goal path."""
    compact: List[Tuple[int, int]] = []
    index = {}
    for pos in path:
        if pos in index:
            keep_to = index[pos] + 1
            for removed in compact[keep_to:]:
                index.pop(removed, None)
            compact = compact[:keep_to]
        else:
            index[pos] = len(compact)
            compact.append(pos)
    return compact


def run_simulated_annealing(grid: List[List[int]],
                            start: Tuple[int, int],
                            goal: Tuple[int, int],
                            rows: int, cols: int) -> PathResult:
    """Run Simulated Annealing using h(n) = Manhattan distance."""
    t0 = time.time()
    rng = random.Random(_seed_for(start, goal, rows, cols))
    steps: List[Step] = []

    current = start
    path = [start]
    visited = {start}

    initial_temperature = max(8.0, float(rows + cols))
    temperature = initial_temperature
    min_temperature = 0.001
    alpha = 0.995
    step_num = 0
    h_start = manhattan(start, goal)

    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[],
        visited=set(visited),
        path_so_far=list(path),
        description=f"[Start] current={start} | T0={temperature:.2f} | h(Start)={h_start}",
        extra={'h': h_start, 'temperature': temperature, 'mode': 'start'}
    ))

    while temperature > min_temperature:
        if current == goal:
            elapsed = (time.time() - t0) * 1000
            return PathResult(
                algo_name='SA',
                start=start, goal=goal,
                steps=steps,
                path=_loop_erased_path(path),
                total_visited=len(visited),
                found=True,
                elapsed_ms=elapsed
            )

        choices = _neighbors(grid, current, rows, cols)
        if not choices:
            break

        step_num += 1
        next_pos = rng.choice(choices)
        h_cur = manhattan(current, goal)
        h_next = manhattan(next_pos, goal)
        delta = h_next - h_cur

        probability = None
        accepted = delta < 0
        if not accepted:
            probability = math.exp(-delta / temperature)
            accepted = rng.random() < probability

        if accepted:
            current = next_pos
            path.append(current)
            visited.add(current)

        desc = (
            f"[Step {step_num}] next={next_pos} | h: {h_cur}->{h_next} | "
            f"delta={delta} | T={temperature:.2f} | "
            f"{'accept' if accepted else 'reject'}"
        )
        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=[p for p in choices if p != next_pos],
            visited=set(visited),
            path_so_far=list(path),
            description=desc,
            extra={
                'h': manhattan(current, goal),
                'h_next': h_next,
                'delta': delta,
                'temperature': temperature,
                'probability': probability,
                'accepted': accepted,
            }
        ))

        temperature *= alpha

    found = current == goal
    final_path = _loop_erased_path(path) if found else []
    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='SA',
        start=start, goal=goal,
        steps=steps,
        path=final_path,
        total_visited=len(visited),
        found=found,
        elapsed_ms=elapsed
    )
