# algorithms/csp/forward_checking.py - CSP: Forward Checking for maze path search

from collections import deque
import sys
import time
from typing import List, Set, Tuple

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


def _reachable_to_goal(grid: List[List[int]], start: Tuple[int, int],
                       goal: Tuple[int, int], blocked: Set[Tuple[int, int]],
                       rows: int, cols: int) -> bool:
    if start == goal:
        return True

    blocked = set(blocked)
    blocked.discard(start)
    blocked.discard(goal)

    queue = deque([start])
    seen = {start}

    while queue:
        current = queue.popleft()
        for nxt in _neighbors(grid, current, rows, cols):
            if nxt in seen or nxt in blocked:
                continue
            if nxt == goal:
                return True
            seen.add(nxt)
            queue.append(nxt)

    return False


def _free_degree(grid: List[List[int]], pos: Tuple[int, int],
                 blocked: Set[Tuple[int, int]], rows: int, cols: int) -> int:
    return sum(1 for nxt in _neighbors(grid, pos, rows, cols)
               if nxt not in blocked)


def _ordered_domain(grid: List[List[int]], current: Tuple[int, int],
                    goal: Tuple[int, int], assigned: Set[Tuple[int, int]],
                    rows: int, cols: int) -> List[Tuple[int, int]]:
    domain = [nxt for nxt in _neighbors(grid, current, rows, cols)
              if nxt not in assigned]
    return sorted(
        domain,
        key=lambda pos: (
            manhattan(pos, goal),
            -_free_degree(grid, pos, assigned | {pos}, rows, cols),
            pos,
        ),
    )


def _forward_check(grid: List[List[int]], value: Tuple[int, int],
                   goal: Tuple[int, int], assigned_after_value: Set[Tuple[int, int]],
                   rows: int, cols: int):
    """Return (ok, removed_values, future_domain, reason)."""
    if value == goal:
        return True, set(), [], "goal reached"

    removed = set()
    future_domain = []

    for nxt in _neighbors(grid, value, rows, cols):
        if nxt in assigned_after_value:
            removed.add(nxt)
            continue

        blocked_after_next = assigned_after_value | {nxt}
        if _reachable_to_goal(grid, nxt, goal, blocked_after_next, rows, cols):
            future_domain.append(nxt)
        else:
            removed.add(nxt)

    future_domain.sort(
        key=lambda pos: (
            manhattan(pos, goal),
            -_free_degree(grid, pos, assigned_after_value | {pos}, rows, cols),
            pos,
        )
    )

    if not future_domain:
        return False, removed, [], "future domain empty"

    return True, removed, future_domain, "future domain reduced"


def run_forward_checking(grid: List[List[int]],
                         start: Tuple[int, int],
                         goal: Tuple[int, int],
                         rows: int, cols: int) -> PathResult:
    """
    Forward Checking Search adapted to the maze CSP.

    Assignment:
        X0 = start, X1..Xk = positions on the path.
    Domain:
        legal unvisited neighbors of the current assigned position.
    Forward checking:
        after assigning Xi = value, reduce Domain[Xi+1]. If no future value
        can still reach Goal, reject the assignment immediately.
    """
    t0 = time.time()
    sys.setrecursionlimit(max(sys.getrecursionlimit(), rows * cols + 1000))

    steps: List[Step] = []
    visited_global = {start}
    result_path = [None]
    step_num = [0]
    max_steps = min(24000, max(3000, rows * cols * 12))

    first_domain = _ordered_domain(grid, start, goal, {start}, rows, cols)
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=first_domain,
        visited=set(visited_global),
        path_so_far=[start],
        description=(
            f"[Start] assignment X0={start} | "
            f"Domain[X1]={len(first_domain)} values"
        ),
        extra={
            "mode": "start",
            "var": "X0",
            "value": start,
            "domain": first_domain,
        },
    ))

    def add_step(current, frontier, path, description,
                 is_backtrack=False, extra=None):
        if step_num[0] >= max_steps:
            return False
        step_num[0] += 1
        steps.append(Step(
            step_num=step_num[0],
            current=current,
            frontier=list(frontier),
            visited=set(visited_global),
            path_so_far=list(path),
            description=description,
            is_backtrack=is_backtrack,
            extra=extra or {},
        ))
        return True

    def forward_check_search(current: Tuple[int, int],
                             path: List[Tuple[int, int]],
                             assigned: Set[Tuple[int, int]]) -> bool:
        if current == goal:
            result_path[0] = list(path)
            return True
        if step_num[0] >= max_steps:
            return False

        var_name = f"X{len(path)}"
        domain = _ordered_domain(grid, current, goal, assigned, rows, cols)

        if not domain:
            add_step(
                current,
                [],
                path,
                f"[Step {step_num[0] + 1}] {var_name} has empty domain -> backtrack",
                is_backtrack=True,
                extra={
                    "mode": "empty_domain",
                    "var": var_name,
                    "domain": [],
                    "pruned_cells": set(),
                },
            )
            return False

        for value in domain:
            if step_num[0] >= max_steps:
                return False

            next_path = path + [value]
            assigned_after_value = assigned | {value}
            visited_global.add(value)

            ok, removed, future_domain, reason = _forward_check(
                grid,
                value,
                goal,
                assigned_after_value,
                rows,
                cols,
            )

            desc = (
                f"[Step {step_num[0] + 1}] select {var_name}={value} | "
                f"domain={len(domain)} | removed={len(removed)} | "
                f"next_domain={len(future_domain)} | {reason}"
            )

            if not add_step(
                value,
                future_domain,
                next_path,
                desc,
                is_backtrack=not ok,
                extra={
                    "mode": "assign" if ok else "forward_check_fail",
                    "var": var_name,
                    "value": value,
                    "domain": list(domain),
                    "removed_values": set(removed),
                    "pruned_cells": set(removed),
                    "future_domain": list(future_domain),
                    "h": manhattan(value, goal),
                    "reason": reason,
                },
            ):
                return False

            if ok and forward_check_search(value, next_path, assigned_after_value):
                return True

            if step_num[0] >= max_steps:
                return False

            restore_desc = (
                f"[Step {step_num[0] + 1}] restore removed values | "
                f"remove {var_name}={value} -> backtrack to {current}"
            )
            add_step(
                current,
                [candidate for candidate in domain if candidate != value],
                path,
                restore_desc,
                is_backtrack=True,
                extra={
                    "mode": "restore",
                    "var": var_name,
                    "removed_assignment": value,
                    "restored_values": set(removed),
                    "pruned_cells": set(removed),
                    "h": manhattan(current, goal),
                },
            )

        return False

    forward_check_search(start, [start], {start})

    found = result_path[0] is not None
    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name="Forward Checking",
        start=start,
        goal=goal,
        steps=steps,
        path=result_path[0] if found else [],
        total_visited=len(visited_global),
        found=found,
        elapsed_ms=elapsed,
    )
