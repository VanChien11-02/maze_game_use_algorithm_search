# algorithms/csp/min_conflicts.py - CSP: Min-Conflicts for maze path search

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
        rows * 1733 + cols * 1777
        + start[0] * 181 + start[1] * 191
        + goal[0] * 193 + goal[1] * 197
    )


def _conflicts(grid: List[List[int]], candidate: Tuple[int, int],
               current: Tuple[int, int], goal: Tuple[int, int],
               path_set: set, rows: int, cols: int) -> int:
    """Lower is better: Manhattan h plus penalties for local CSP violations."""
    score = manhattan(candidate, goal)
    if candidate in path_set:
        score += rows + cols

    onward = [
        n for n in _neighbors(grid, candidate, rows, cols)
        if n != current and n not in path_set
    ]
    if candidate != goal and not onward:
        score += max(3, (rows + cols) // 4)
    return score


def run_min_conflicts(grid: List[List[int]],
                      start: Tuple[int, int],
                      goal: Tuple[int, int],
                      rows: int, cols: int) -> PathResult:
    """
    Adapt Min-Conflicts to the maze CSP.

    Variables are positions in the current path assignment. The conflicted
    variable is the endpoint while it is not Goal. Its domain is the set of
    walkable neighboring cells. CONFLICTS uses Manhattan h and penalties for
    revisiting cells or stepping into a dead end.
    """
    t0 = time.time()
    rng = random.Random(_seed_for(start, goal, rows, cols))
    steps: List[Step] = []
    stack = [(start, set())]
    path = [start]
    path_set = {start}
    visited_all = {start}
    max_steps = min(14000, max(2200, rows * cols * 8))

    h0 = manhattan(start, goal)
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[],
        visited=set(visited_all),
        path_so_far=list(path),
        description=f"[Start] initial assignment=[{start}] | h={h0}",
        extra={'h': h0, 'conflicts': h0, 'mode': 'start'}
    ))

    step_num = 0
    while stack and step_num < max_steps:
        current, tried = stack[-1]
        if current == goal:
            break

        domain = [
            n for n in _neighbors(grid, current, rows, cols)
            if n not in tried and n not in path_set
        ]
        if not domain:
            stack.pop()
            path_set.discard(current)
            if stack:
                path.pop()
                step_num += 1
                back_to = stack[-1][0]
                steps.append(Step(
                    step_num=step_num,
                    current=back_to,
                    frontier=[],
                    visited=set(visited_all),
                    path_so_far=list(path),
                    description=(
                        f"[Step {step_num}] repair conflicted endpoint {current} | "
                        f"no legal value left -> backtrack to {back_to}"
                    ),
                    is_backtrack=True,
                    extra={
                        'h': manhattan(back_to, goal),
                        'conflicts': manhattan(back_to, goal),
                        'mode': 'backtrack',
                    }
                ))
            continue

        scored = [
            (_conflicts(grid, n, current, goal, path_set, rows, cols),
             manhattan(n, goal), n)
            for n in domain
        ]
        scored.sort(key=lambda item: (item[0], item[1], item[2]))

        # Random tie/top-k selection keeps the local-search behavior visible.
        best_score = scored[0][0]
        best_bucket = [item for item in scored if item[0] == best_score]
        if len(scored) > 1 and rng.random() < 0.12:
            top = scored[:min(3, len(scored))]
            _, best_h, chosen = rng.choice(top)
            best_score = _conflicts(grid, chosen, current, goal, path_set, rows, cols)
        else:
            _, best_h, chosen = rng.choice(best_bucket)

        tried.add(chosen)
        stack.append((chosen, set()))
        path.append(chosen)
        path_set.add(chosen)
        visited_all.add(chosen)
        step_num += 1

        desc = (
            f"[Step {step_num}] conflicted var=endpoint {current} | "
            f"set value={chosen} | h={best_h} | conflicts={best_score}"
        )

        steps.append(Step(
            step_num=step_num,
            current=chosen,
            frontier=[item[2] for item in scored if item[2] != chosen],
            visited=set(visited_all),
            path_so_far=list(path),
            description=desc,
            is_backtrack=False,
            extra={
                'h': manhattan(chosen, goal),
                'conflicts': best_score,
                'chosen': chosen,
                'mode': 'assign',
            }
        ))

    found = bool(path and path[-1] == goal)
    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='Min-Conflicts',
        start=start, goal=goal,
        steps=steps,
        path=path if found else [],
        total_visited=len(visited_all),
        found=found,
        elapsed_ms=elapsed
    )
