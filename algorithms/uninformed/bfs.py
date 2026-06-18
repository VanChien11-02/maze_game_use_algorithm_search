# algorithms/uninformed/bfs.py - Uninformed Search: Breadth-First Search
"""
BFS (Breadth-First Search)

Implements the classroom pseudocode:
    node <- initial state
    if goal-test(node.state) return node
    frontier <- FIFO queue with node
    explored <- empty set
    while frontier is not empty:
        node <- frontier.remove()
        explored <- explored union {node.state}
        for each action in actions(node.state):
            child <- child-node(problem, node, action)
            if child.state not in explored and not in frontier:
                if goal-test(child.state) return child
                frontier.insert(child)
"""

import time
from collections import deque
from typing import List, Tuple

from algorithms.base import PathResult, Step, reconstruct_path


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def run_bfs(grid: List[List[int]],
            start: Tuple[int, int],
            goal: Tuple[int, int],
            rows: int, cols: int) -> PathResult:
    """Run BFS and record every algorithm snapshot for visualization."""
    t0 = time.time()
    steps: List[Step] = []
    parent = {start: None}
    explored = set()
    frontier = deque([start])
    frontier_set = {start}
    step_num = 0

    steps.append(Step(
        step_num=0,
        current=start,
        frontier=list(frontier),
        visited=set(explored),
        path_so_far=[start],
        description=f"[Start] FIFO queue = [{start}] | explored = empty",
        extra={'queue_size': len(frontier), 'expanded': 0}
    ))

    if start == goal:
        elapsed = (time.time() - t0) * 1000
        return PathResult(
            algo_name='BFS',
            start=start, goal=goal,
            steps=steps,
            path=[start],
            total_visited=0,
            found=True,
            elapsed_ms=elapsed
        )

    while frontier:
        current = frontier.popleft()
        frontier_set.discard(current)
        explored.add(current)
        step_num += 1

        path_cur = reconstruct_path(parent, start, current)
        children_added = []

        r, c = current
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            child = (nr, nc)
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] == 0:
                continue
            if child in explored or child in frontier_set:
                continue

            parent[child] = current
            children_added.append(child)

            if child == goal:
                frontier.append(child)
                frontier_set.add(child)
                path = reconstruct_path(parent, start, goal)
                steps.append(Step(
                    step_num=step_num,
                    current=current,
                    frontier=list(frontier),
                    visited=set(explored),
                    path_so_far=path,
                    description=(
                        f"[Step {step_num}] Expand {current}; found goal {goal}. "
                        f"Queue={len(frontier)} | explored={len(explored)}"
                    ),
                    extra={
                        'queue_size': len(frontier),
                        'children_added': list(children_added),
                        'goal_found': True,
                    }
                ))
                elapsed = (time.time() - t0) * 1000
                return PathResult(
                    algo_name='BFS',
                    start=start, goal=goal,
                    steps=steps,
                    path=path,
                    total_visited=len(explored),
                    found=True,
                    elapsed_ms=elapsed
                )

            frontier.append(child)
            frontier_set.add(child)

        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(frontier),
            visited=set(explored),
            path_so_far=path_cur,
            description=(
                f"[Step {step_num}] Expand {current}; add {len(children_added)} child nodes. "
                f"Queue={len(frontier)} | explored={len(explored)}"
            ),
            extra={
                'queue_size': len(frontier),
                'children_added': list(children_added),
                'goal_found': False,
            }
        ))

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='BFS',
        start=start, goal=goal,
        steps=steps,
        path=[],
        total_visited=len(explored),
        found=False,
        elapsed_ms=elapsed
    )
