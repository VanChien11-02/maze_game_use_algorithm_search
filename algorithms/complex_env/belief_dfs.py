# algorithms/complex_env/belief_dfs.py - Complex Environment: Belief-State DFS
"""
Belief-State DFS for cases where Start and/or Goal may be hidden.

Unlike normal DFS, this algorithm keeps possible Start states (BS) and
possible Goal states (BG). It then tries DFS on each hypothesis and uses
environment feedback to reject wrong hypotheses.
"""

import time
from typing import Dict, List, Set, Tuple

from algorithms.base import PathResult, Step, reconstruct_path


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
MAX_FALSE_PREVIEW = 18


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _walkable_cells(grid: List[List[int]], rows: int, cols: int) -> List[Tuple[int, int]]:
    cells = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0:
                cells.append((r, c))
    return cells


def _belief_candidates(
    cells: List[Tuple[int, int]],
    truth: Tuple[int, int],
    avoid: Tuple[int, int],
    limit: int,
) -> List[Tuple[int, int]]:
    """Build a small belief set and keep the true state as the last candidate."""
    false_cells = [cell for cell in cells if cell not in (truth, avoid)]
    false_cells.sort(key=lambda cell: (manhattan(cell, truth), cell), reverse=True)
    picks = false_cells[:max(0, limit - 1)]
    return picks + [truth]


def _make_beliefs(
    cells: List[Tuple[int, int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    see_start: bool,
    see_goal: bool,
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    bs = [start] if see_start else _belief_candidates(cells, start, goal, 4)
    bg = [goal] if see_goal else _belief_candidates(cells, goal, start, 4)
    return bs, bg


def _dfs_preview(
    grid: List[List[int]],
    src: Tuple[int, int],
    dst: Tuple[int, int],
    rows: int,
    cols: int,
    max_expand: int,
) -> Tuple[List[Step], List[Tuple[int, int]], Set[Tuple[int, int]], bool]:
    steps: List[Step] = []
    parent: Dict[Tuple[int, int], Tuple[int, int] | None] = {src: None}
    visited: Set[Tuple[int, int]] = set()
    stack = [src]
    local_step = 0

    while stack and local_step < max_expand:
        current = stack.pop()
        if current in visited:
            continue

        visited.add(current)
        local_step += 1
        path_cur = reconstruct_path(parent, src, current)
        steps.append(Step(
            step_num=local_step,
            current=current,
            frontier=list(stack),
            visited=set(visited),
            path_so_far=path_cur,
            description=(
                f"[DFS hypothesis] {src} -> {dst} | expand {current} | "
                f"stack={len(stack)} | visited={len(visited)}"
            ),
            extra={'hyp_start': src, 'hyp_goal': dst, 'mode': 'belief_dfs'}
        ))

        if current == dst:
            return steps, reconstruct_path(parent, src, dst), visited, True

        r, c = current
        neighbors = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if (0 <= nr < rows and 0 <= nc < cols
                    and grid[nr][nc] != 0
                    and npos not in visited
                    and npos not in parent):
                neighbors.append(npos)

        neighbors.sort(key=lambda pos: manhattan(pos, dst), reverse=True)
        for npos in neighbors:
            parent[npos] = current
            stack.append(npos)

    best_path = reconstruct_path(parent, src, stack[-1]) if stack else [src]
    return steps, best_path, visited, False


def _renumber(step: Step, step_num: int, description: str = None) -> Step:
    return Step(
        step_num=step_num,
        current=step.current,
        frontier=step.frontier,
        visited=step.visited,
        path_so_far=step.path_so_far,
        description=description if description is not None else step.description,
        is_backtrack=step.is_backtrack,
        extra=step.extra,
    )


def run_belief_dfs(grid: List[List[int]],
                   start: Tuple[int, int],
                   goal: Tuple[int, int],
                   rows: int, cols: int) -> PathResult:
    """
    Run DFS over belief states.

    Main demo case: Start hidden and Goal hidden. The algorithm also records
    short setup steps for the other classroom cases:
    - see S, hide G
    - hide S, see G
    - see S, see G
    """
    t0 = time.time()
    cells = _walkable_cells(grid, rows, cols)
    steps: List[Step] = []
    global_visited: Set[Tuple[int, int]] = set()
    step_num = 0

    case_notes = [
        ("Thay S, khong thay G", True, False),
        ("Khong thay S, thay G", False, True),
        ("Khong thay ca S va G", False, False),
        ("Thay ca S va G", True, True),
    ]

    for label, see_s, see_g in case_notes:
        bs, bg = _make_beliefs(cells, start, goal, see_s, see_g)
        steps.append(Step(
            step_num=step_num,
            current=start,
            frontier=bs + bg,
            visited=set(),
            path_so_far=[start],
            description=(
                f"[Case] {label} | BS={len(bs)} candidate(s), "
                f"BG={len(bg)} candidate(s)"
            ),
            extra={
                'case': label,
                'belief_starts': list(bs),
                'belief_goals': list(bg),
                'see_start': see_s,
                'see_goal': see_g,
            }
        ))
        step_num += 1

    # Main result uses the hardest case: neither S nor G is directly observed.
    bs, bg = _make_beliefs(cells, start, goal, see_start=False, see_goal=False)
    final_path: List[Tuple[int, int]] = []

    for hyp_s in bs:
        for hyp_g in bg:
            if hyp_s == hyp_g:
                continue

            is_true_pair = hyp_s == start and hyp_g == goal
            preview_limit = rows * cols if is_true_pair else MAX_FALSE_PREVIEW
            local_steps, path, visited, reached = _dfs_preview(
                grid, hyp_s, hyp_g, rows, cols, preview_limit
            )
            global_visited.update(visited)

            steps.append(Step(
                step_num=step_num,
                current=hyp_s,
                frontier=list(bg),
                visited=set(global_visited),
                path_so_far=[hyp_s],
                description=(
                    f"[Belief] Thu gia thuyet S={hyp_s}, G={hyp_g} | "
                    f"true_pair={is_true_pair}"
                ),
                extra={'belief_starts': list(bs), 'belief_goals': list(bg)}
            ))
            step_num += 1

            for local in local_steps:
                desc = local.description
                if is_true_pair:
                    desc = "[Confirmed] " + desc
                steps.append(_renumber(local, step_num, desc))
                step_num += 1

            if is_true_pair and reached:
                final_path = path
                break

            steps.append(Step(
                step_num=step_num,
                current=hyp_s,
                frontier=list(bg),
                visited=set(global_visited),
                path_so_far=path if path else [hyp_s],
                description=(
                    f"[Reject] Gia thuyet S={hyp_s}, G={hyp_g} "
                    f"khong khop quan sat moi truong"
                ),
                is_backtrack=True,
                extra={'rejected_start': hyp_s, 'rejected_goal': hyp_g}
            ))
            step_num += 1

        if final_path:
            break

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='BS-DFS',
        start=start,
        goal=goal,
        steps=steps,
        path=final_path,
        total_visited=len(global_visited),
        found=bool(final_path),
        elapsed_ms=elapsed,
    )
