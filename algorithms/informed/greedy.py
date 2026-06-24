# algorithms/informed/greedy.py - Informed Search: Greedy Best-First Search

import heapq
import time
from typing import Dict, List, Tuple

from algorithms.base import PathResult, Step, reconstruct_path


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def run_greedy(grid: List[List[int]],
               start: Tuple[int, int],
               goal: Tuple[int, int],
               rows: int, cols: int) -> PathResult:
    """Run Greedy Best-First Search using h(n) = Manhattan distance."""
    t0 = time.time()
    steps: List[Step] = []
    parent: Dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}
    reached = set()
    frontier_heap = []
    frontier_set = {start}
    counter = 0
    h0 = manhattan(start, goal)
    heapq.heappush(frontier_heap, (h0, counter, start))

    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[start],
        visited=set(),
        path_so_far=[start],
        description=f"[Start] Frontier={{Start}} | h(Start)={h0} | Reached=empty",
        extra={'h': h0, 'mode': 'start'}
    ))

    step_num = 0
    while frontier_heap:
        while frontier_heap and frontier_heap[0][2] not in frontier_set:
            heapq.heappop(frontier_heap)
        if not frontier_heap:
            break

        _, _, current = frontier_heap[0]
        step_num += 1

        h_cur = manhattan(current, goal)
        path_cur = reconstruct_path(parent, start, current)
        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(frontier_set),
            visited=set(reached),
            path_so_far=path_cur,
            description=(
                f"[Step {step_num}] Choose {current} with smallest h={h_cur} | "
                f"Frontier={len(frontier_set)} | Reached={len(reached)}"
            ),
            extra={'h': h_cur, 'mode': 'select'}
        ))

        if current == goal:
            path = reconstruct_path(parent, start, goal)
            elapsed = (time.time() - t0) * 1000
            return PathResult(
                algo_name='Greedy',
                start=start, goal=goal,
                steps=steps, path=path,
                total_visited=len(reached),
                found=True,
                elapsed_ms=elapsed
            )

        heapq.heappop(frontier_heap)
        frontier_set.discard(current)
        reached.add(current)

        r, c = current
        added = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] == 0:
                continue
            if npos in reached or npos in frontier_set:
                continue

            parent[npos] = current
            counter += 1
            h_new = manhattan(npos, goal)
            heapq.heappush(frontier_heap, (h_new, counter, npos))
            frontier_set.add(npos)
            added.append((npos, h_new))

        step_num += 1
        added_text = ", ".join(f"{pos}:h={h}" for pos, h in added[:4]) or "none"
        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(frontier_set),
            visited=set(reached),
            path_so_far=path_cur,
            description=(
                f"[Step {step_num}] Move {current} to Reached; "
                f"add neighbors by Manhattan h | {added_text}"
            ),
            extra={
                'h': h_cur,
                'children_added': [pos for pos, _ in added],
                'mode': 'expand',
            }
        ))

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='Greedy',
        start=start, goal=goal,
        steps=steps, path=[],
        total_visited=len(reached),
        found=False,
        elapsed_ms=elapsed
    )
