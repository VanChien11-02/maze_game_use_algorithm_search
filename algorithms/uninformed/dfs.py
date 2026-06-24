# algorithms/dfs.py — Nhóm 1: Uninformed Search — Depth First Search
"""
DFS (Depth-First Search) — Tìm kiếm theo chiều sâu
════════════════════════════════════════════════════
Nhóm: Uninformed Search (Tìm kiếm mù)
Bài toán: Tìm đường đi từ Start đến Goal trong mê cung

Trạng thái bắt đầu:
    - Vị trí: Start (r, c)
    - Stack: [Start]
    - Explored: {}

Các bước thực hiện:
    - Nếu Start là Goal → kết thúc thành công
    - Pop ô cuối stack → là ô hiện tại
    - Đưa ô hiện tại vào explored
    - Sinh các ô kề chưa có trong explored/frontier
    - Nếu child là Goal → kết thúc thành công
    - Nếu chưa phải Goal → push child vào stack
    - Lặp đến khi stack rỗng hoặc tìm thấy Goal

Trạng thái kết thúc:
    - Found: đường đi từ Start→Goal (không nhất thiết ngắn nhất)
    - Not found: không tồn tại đường đi

Đặc điểm:
    - KHÔNG đảm bảo đường ngắn nhất
    - Tiêu tốn ít bộ nhớ hơn BFS (O(depth))
    - Có thể đi lòng vòng nếu không đánh dấu visited
"""

import time
from typing import List, Tuple
from algorithms.base import Step, PathResult, reconstruct_path


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def run_dfs(grid: List[List[int]],
            start: Tuple[int, int],
            goal: Tuple[int, int],
            rows: int, cols: int) -> PathResult:
    """
    Chạy DFS và ghi lại tất cả các bước.
    
    Args:
        grid: Ma trận mê cung (0=tường, 1=sàn)
        start: Ô xuất phát (row, col)
        goal: Ô đích (row, col)
        rows, cols: Kích thước lưới
    
    Returns:
        PathResult chứa toàn bộ steps và đường đi cuối
    """
    t0 = time.time()
    steps: List[Step] = []
    parent = {start: None}
    explored = set()
    stack = [start]       # Stack: LIFO — ô được thêm sau cùng xét trước
    frontier_set = {start}
    step_num = 0

    # ── Bước 0: Trạng thái bắt đầu ─────────────────────────
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=list(stack),
        visited=set(explored),
        path_so_far=[start],
        description=f"[Bắt đầu] LIFO stack = [{start}] | explored = rỗng",
    ))

    if start == goal:
        elapsed = (time.time() - t0) * 1000
        return PathResult(
            algo_name='DFS',
            start=start, goal=goal,
            steps=steps,
            path=[start],
            total_visited=0,
            found=True,
            elapsed_ms=elapsed
        )

    while stack:
        current = stack.pop()   # LIFO — lấy phần tử cuối stack
        frontier_set.discard(current)
        explored.add(current)
        step_num += 1

        # Tái tạo đường đến current
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
                path = reconstruct_path(parent, start, goal)
                steps.append(Step(
                    step_num=step_num,
                    current=current,
                    frontier=list(stack),
                    visited=set(explored),
                    path_so_far=path,
                    description=(
                        f"[Bước {step_num}] Mở rộng {current}; tìm thấy goal {goal}. "
                        f"Stack={len(stack)} | explored={len(explored)}"
                    ),
                    extra={
                        'stack_size': len(stack),
                        'children_added': list(children_added),
                        'goal_found': True,
                    }
                ))
                elapsed = (time.time() - t0) * 1000
                return PathResult(
                    algo_name='DFS',
                    start=start, goal=goal,
                    steps=steps,
                    path=path,
                    total_visited=len(explored),
                    found=True,
                    elapsed_ms=elapsed
                )

            stack.append(child)
            frontier_set.add(child)

        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(stack),
            visited=set(explored),
            path_so_far=path_cur,
            description=(
                f"[Bước {step_num}] Mở rộng {current}; thêm {len(children_added)} child nodes. "
                f"Stack={len(stack)} | explored={len(explored)}"
            ),
            extra={
                'stack_size': len(stack),
                'children_added': list(children_added),
                'goal_found': False,
            }
        ))

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='DFS',
        start=start, goal=goal,
        steps=steps, path=[],
        total_visited=len(explored),
        found=False,
        elapsed_ms=elapsed
    )
