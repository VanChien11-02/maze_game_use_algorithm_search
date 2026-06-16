# algorithms/dfs.py — Nhóm 1: Uninformed Search — Depth First Search
"""
DFS (Depth-First Search) — Tìm kiếm theo chiều sâu
════════════════════════════════════════════════════
Nhóm: Uninformed Search (Tìm kiếm mù)
Bài toán: Tìm đường đi từ Start đến Goal trong mê cung

Trạng thái bắt đầu:
    - Vị trí: Start (r, c)
    - Stack: [Start]
    - Visited: {}

Các bước thực hiện:
    - Pop ô đầu stack → là ô hiện tại
    - Nếu là Goal → kết thúc thành công
    - Duyệt các ô kề chưa thăm → push vào stack
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
    visited = set()
    stack = [start]       # Stack: LIFO — ô được thêm sau cùng xét trước
    step_num = 0

    # ── Bước 0: Trạng thái bắt đầu ─────────────────────────
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=list(stack),
        visited=set(visited),
        path_so_far=[start],
        description=f"[Bắt đầu] Stack = [{start}] | Visited = rỗng",
    ))

    while stack:
        current = stack.pop()   # LIFO — lấy phần tử cuối stack

        if current in visited:
            continue
        visited.add(current)
        step_num += 1

        # Tái tạo đường đến current
        path_cur = reconstruct_path(parent, start, current)

        desc = (f"[Bước {step_num}] Xét ô {current} | "
                f"Stack còn {len(stack)} ô | Visited: {len(visited)}")

        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(stack),
            visited=set(visited),
            path_so_far=path_cur,
            description=desc,
        ))

        # Kiểm tra Goal
        if current == goal:
            path = reconstruct_path(parent, start, goal)
            elapsed = (time.time() - t0) * 1000
            return PathResult(
                algo_name='DFS',
                start=start, goal=goal,
                steps=steps,
                path=path,
                total_visited=len(visited),
                found=True,
                elapsed_ms=elapsed
            )

        # Mở rộng các ô kề
        r, c = current
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if (0 <= nr < rows and 0 <= nc < cols
                    and grid[nr][nc] != 0
                    and npos not in visited
                    and npos not in parent):
                parent[npos] = current
                stack.append(npos)

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='DFS',
        start=start, goal=goal,
        steps=steps, path=[],
        total_visited=len(visited),
        found=False,
        elapsed_ms=elapsed
    )
