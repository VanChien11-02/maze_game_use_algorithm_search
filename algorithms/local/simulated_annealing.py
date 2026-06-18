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


def _weighted_neighbor(rng: random.Random, candidates: List[Tuple[int, int]],
                       goal: Tuple[int, int], temperature: float) -> Tuple[int, int]:
    scale = max(1.0, temperature / 3.0)
    weights = [math.exp(-manhattan(pos, goal) / scale) for pos in candidates]
    total = sum(weights)
    pick = rng.random() * total
    acc = 0.0
    for pos, weight in zip(candidates, weights):
        acc += weight
        if acc >= pick:
            return pos
    return candidates[-1]


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
    best = start
    best_h = manhattan(start, goal)
    rejected_streak = 0

    initial_temperature = max(8.0, float(rows + cols))
    temperature = initial_temperature
    min_temperature = 0.001
    alpha = 0.9995
    max_steps = min(45000, max(10000, rows * cols * 60))
    sample_stride = max(1, max_steps // 1400)
    restarts = 0
    max_restarts = 4

    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[],
        visited=set(visited),
        path_so_far=list(path),
        description=f"[Start] T={temperature:.2f} | h(Start)={best_h} | current={start}",
        extra={'h': best_h, 'temperature': temperature, 'mode': 'start'}
    ))

    for step_num in range(1, max_steps + 1):
        if current == goal:
            break
        if temperature <= min_temperature:
            if restarts >= max_restarts:
                break
            restarts += 1
            current = start
            path = [start]
            visited = {start}
            temperature = initial_temperature
            rejected_streak = 0
            steps.append(Step(
                step_num=step_num,
                current=start,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path),
                description=f"[Step {step_num}] restart annealing #{restarts} | T={temperature:.2f}",
                is_backtrack=True,
                extra={'h': manhattan(start, goal), 'temperature': temperature, 'restart': restarts}
            ))
            continue

        choices = _neighbors(grid, current, rows, cols)
        if not choices:
            break

        # Keep the random-neighbor spirit, but bias away from immediate loops.
        fresh = [p for p in choices if p not in visited]
        must_escape_dead_end = not fresh
        pool = fresh or choices
        if rng.random() < 0.72:
            next_pos = _weighted_neighbor(rng, pool, goal, temperature)
        else:
            next_pos = rng.choice(pool)
        h_cur = manhattan(current, goal)
        h_next = manhattan(next_pos, goal)
        delta = h_next - h_cur

        accepted = False
        improved_best = False
        probability = 1.0 if delta < 0 else math.exp(-delta / max(temperature, 1e-9))
        if must_escape_dead_end or delta < 0 or rng.random() < probability:
            current = next_pos
            path.append(current)
            visited.add(current)
            accepted = True
            rejected_streak = 0
            if h_next < best_h:
                best = current
                best_h = h_next
                improved_best = True
        else:
            rejected_streak += 1

        reheated = False
        if rejected_streak >= max(20, rows + cols):
            temperature = max(temperature, max(4.0, (rows + cols) * 0.45))
            rejected_streak = 0
            reheated = True

        desc = (
            f"[Step {step_num}] next={next_pos} | h: {h_cur}->{h_next} | "
            f"delta={delta} | T={temperature:.2f} | "
            f"{'accept' if accepted else 'reject'}"
        )
        if reheated:
            desc += " | reheat"
        should_record = (
            step_num % sample_stride == 0
            or current == goal
            or reheated
            or improved_best
        )
        if should_record:
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
                    'forced_escape': must_escape_dead_end,
                    'reheated': reheated,
                    'best': best,
                    'best_h': best_h,
                    'sample_stride': sample_stride,
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
