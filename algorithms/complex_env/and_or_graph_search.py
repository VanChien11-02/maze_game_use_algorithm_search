# algorithms/complex_env/and_or_graph_search.py - Complex Environment: AND-OR Graph Search
"""
AND-OR Graph Search.

This replaces the old belief-hypothesis DFS demo with the classroom
pseudocode:

    AND_OR_GRAPH_SEARCH(problem)
    OR_SEARCH(state, problem, path)
    AND_SEARCH(states, problem, path)

The maze itself is deterministic, so results(state, action) returns one
successor state. The AND_SEARCH function is still kept explicitly so the
implementation follows the pseudocode shape.
"""

import sys
import time
from typing import Dict, List, Optional, Set, Tuple

from algorithms.base import PathResult, Step


State = Tuple[int, int]
Action = str
Plan = object

ACTIONS: List[Tuple[Action, Tuple[int, int]]] = [
    ("UP", (-1, 0)),
    ("DOWN", (1, 0)),
    ("LEFT", (0, -1)),
    ("RIGHT", (0, 1)),
]


def manhattan(a: State, b: State) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _is_walkable(grid: List[List[int]], state: State, rows: int, cols: int) -> bool:
    r, c = state
    return 0 <= r < rows and 0 <= c < cols and grid[r][c] != 0


def _actions(grid: List[List[int]], state: State,
             rows: int, cols: int, goal: State) -> List[Tuple[Action, State]]:
    legal: List[Tuple[Action, State]] = []
    r, c = state
    for name, (dr, dc) in ACTIONS:
        nxt = (r + dr, c + dc)
        if _is_walkable(grid, nxt, rows, cols):
            legal.append((name, nxt))

    # The pseudocode says "for each action"; this ordering only makes the
    # classroom demo reach the goal sooner on large mazes.
    legal.sort(key=lambda item: (manhattan(item[1], goal), item[0]))
    return legal


def _results(state: State, action: Action) -> List[State]:
    for name, (dr, dc) in ACTIONS:
        if name == action:
            return [(state[0] + dr, state[1] + dc)]
    return []


def _plan_to_path(plan: Plan, start: State, goal: State) -> List[State]:
    if start == goal:
        return [start]
    if plan is None or plan == []:
        return []

    path = [start]
    current = start
    current_plan = plan
    guard = 0

    while current != goal and current_plan not in (None, []):
        try:
            action, branch_plans = current_plan
        except (TypeError, ValueError):
            return []

        result_states = _results(current, action)
        if not result_states:
            return []

        # Maze actions are deterministic, so there is one actual branch.
        current = result_states[0]
        path.append(current)

        if not isinstance(branch_plans, dict) or current not in branch_plans:
            return []
        current_plan = branch_plans[current]

        guard += 1
        if guard > 10000:
            return []

    return path if path and path[-1] == goal else []


def run_and_or_graph_search(grid: List[List[int]],
                            start: State,
                            goal: State,
                            rows: int, cols: int) -> PathResult:
    """Run AND-OR Graph Search and record OR/AND recursion steps."""
    t0 = time.time()
    sys.setrecursionlimit(max(sys.getrecursionlimit(), rows * cols * 4 + 100))

    steps: List[Step] = []
    visited_for_display: Set[State] = set()
    step_num = 0

    def add_step(current: State,
                 frontier: List[State],
                 path: List[State],
                 description: str,
                 *,
                 is_backtrack: bool = False,
                 extra: Optional[dict] = None) -> None:
        nonlocal step_num
        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(frontier),
            visited=set(visited_for_display),
            path_so_far=list(path),
            description=description,
            is_backtrack=is_backtrack,
            extra=extra or {},
        ))
        step_num += 1

    def and_search(states: List[State], path: List[State]) -> Optional[Dict[State, Plan]]:
        display_state = states[0] if states else path[-1]
        add_step(
            display_state,
            states,
            path,
            f"[AND_SEARCH] states={states} | build plan for every result state",
            extra={'mode': 'and_search', 'states': list(states)},
        )

        plans: Dict[State, Plan] = {}
        for state in states:
            plan_s = or_search(state, path)
            if plan_s is None:
                add_step(
                    state,
                    states,
                    path + [state],
                    f"[AND_SEARCH] state {state} failed -> return failure",
                    is_backtrack=True,
                    extra={'mode': 'and_failure', 'failed_state': state},
                )
                return None
            plans[state] = plan_s

        add_step(
            display_state,
            states,
            path,
            f"[AND_SEARCH] all result states solved -> return plans",
            extra={'mode': 'and_success', 'states': list(states)},
        )
        return plans

    def or_search(state: State, path: List[State]) -> Optional[Plan]:
        visited_for_display.add(state)
        path_with_state = path + [state]
        legal_actions = _actions(grid, state, rows, cols, goal)
        action_targets = [target for _, target in legal_actions]

        add_step(
            state,
            action_targets,
            path_with_state,
            f"[OR_SEARCH] state={state} | path={path}",
            extra={
                'mode': 'or_search',
                'state': state,
                'path': list(path),
                'actions': [name for name, _ in legal_actions],
            },
        )

        if state == goal:
            add_step(
                state,
                [],
                path_with_state,
                f"[OR_SEARCH] {state} is Goal -> return empty plan",
                extra={'mode': 'goal', 'state': state},
            )
            return []

        if state in path:
            add_step(
                state,
                action_targets,
                path_with_state,
                f"[OR_SEARCH] {state} already in path -> return failure",
                is_backtrack=True,
                extra={'mode': 'loop_failure', 'state': state},
            )
            return None

        for action, target in legal_actions:
            result_states = _results(state, action)
            result_states = [
                result for result in result_states
                if _is_walkable(grid, result, rows, cols)
            ]

            add_step(
                state,
                result_states,
                path_with_state,
                f"[OR_SEARCH] try action {action} -> results={result_states}",
                extra={
                    'mode': 'try_action',
                    'state': state,
                    'action': action,
                    'target': target,
                    'result_states': list(result_states),
                },
            )

            plan = and_search(result_states, path_with_state)
            if plan is not None:
                add_step(
                    state,
                    result_states,
                    path_with_state,
                    f"[OR_SEARCH] action {action} works -> return [action, plan]",
                    extra={
                        'mode': 'or_success',
                        'state': state,
                        'action': action,
                        'result_states': list(result_states),
                    },
                )
                return (action, plan)

            add_step(
                state,
                result_states,
                path_with_state,
                f"[OR_SEARCH] action {action} failed -> try next action",
                is_backtrack=True,
                extra={
                    'mode': 'action_failure',
                    'state': state,
                    'action': action,
                    'result_states': list(result_states),
                },
            )

        add_step(
            state,
            [],
            path_with_state,
            f"[OR_SEARCH] no action works at {state} -> return failure",
            is_backtrack=True,
            extra={'mode': 'or_failure', 'state': state},
        )
        return None

    add_step(
        start,
        [start],
        [start],
        f"[AND_OR_GRAPH_SEARCH] initial={start}, goal={goal}",
        extra={'mode': 'start', 'initial': start, 'goal': goal},
    )

    plan = or_search(start, [])
    final_path = _plan_to_path(plan, start, goal)

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='AND-OR',
        start=start,
        goal=goal,
        steps=steps,
        path=final_path,
        total_visited=len(visited_for_display),
        found=bool(final_path),
        elapsed_ms=elapsed,
    )
