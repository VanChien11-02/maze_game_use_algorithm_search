# algorithms/astar.py — Nhóm 2: Informed Search — A* Search
"""
A* (A-Star Search) — Tìm kiếm có thông tin hướng dẫn
══════════════════════════════════════════════════════
Nhóm: Informed Search (Tìm kiếm có hướng)
Bài toán: Tìm đường đi TỐI ƯU từ Start đến Goal dùng Heuristic

Trạng thái bắt đầu:
    - Start (r, c), goal đã biết
    - Open set: {Start}, g[Start]=0, f[Start]=h(Start)
    - Closed set: {}
    - Heuristic h(n) = Manhattan distance = |r-gr| + |c-gc|

Các bước thực hiện:
    - Lấy ô có f = g + h nhỏ nhất từ Open set
    - Nếu là Goal → truy vết đường đi, kết thúc
    - Chuyển ô sang Closed set
    - Cập nhật các ô kề: nếu g_new < g_cũ → cập nhật
    - Lặp đến khi tìm thấy hoặc Open set rỗng

Trạng thái kết thúc:
    - Found: đường đi TỐI ƯU (ngắn nhất) với ít bước khám phá nhất
    - Not found: không có đường đi

Đặc điểm:
    - TỐI ƯU và ĐẦY ĐỦ với heuristic admissible (Manhattan)
    - Nhanh hơn BFS vì hướng về Goal
    - f(n) = g(n) + h(n): kết hợp chi phí thực + ước tính
"""

import heapq
import time
from typing import List, Tuple, Dict
from algorithms.base import Step, PathResult, reconstruct_path


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def run_astar(grid: List[List[int]],
              start: Tuple[int, int],
              goal: Tuple[int, int],
              rows: int, cols: int) -> PathResult:
    """
    Chạy A* và ghi lại tất cả bước.
    f(n) = g(n) + h(n), h = Manhattan distance.
    """
    t0 = time.time()
    steps: List[Step] = []

    g: Dict[Tuple,float] = {start: 0}
    parent = {start: None}
    visited = set()   # closed set

    # (f_value, tie_breaker, position)
    counter = 0
    open_heap = [(manhattan(start, goal), counter, start)]
    open_set = {start}
    step_num = 0

    # ── Bước 0: Trạng thái bắt đầu ─────────────────────────
    h0 = manhattan(start, goal)
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[start],
        visited=set(),
        path_so_far=[start],
        description=(f"[Bắt đầu] g=0, h={h0}, f={h0} | "
                     f"Open=[{start}] | Closed=rỗng"),
        extra={'g': 0, 'h': h0, 'f': h0}
    ))

    while open_heap:
        f_val, _, current = heapq.heappop(open_heap)

        if current in visited:
            continue
        visited.add(current)
        open_set.discard(current)
        step_num += 1

        g_cur = g.get(current, float('inf'))
        h_cur = manhattan(current, goal)
        path_cur = reconstruct_path(parent, start, current)

        desc = (f"[Bước {step_num}] Xét ô {current} | "
                f"g={g_cur}, h={h_cur}, f={g_cur+h_cur} | "
                f"Open={len(open_set)} | Closed={len(visited)}")

        steps.append(Step(
            step_num=step_num,
            current=current,
            frontier=list(open_set),
            visited=set(visited),
            path_so_far=path_cur,
            description=desc,
            extra={'g': g_cur, 'h': h_cur, 'f': g_cur + h_cur}
        ))

        if current == goal:
            path = reconstruct_path(parent, start, goal)
            elapsed = (time.time() - t0) * 1000
            return PathResult(
                algo_name='A*',
                start=start, goal=goal,
                steps=steps,
                path=path,
                total_visited=len(visited),
                found=True,
                elapsed_ms=elapsed
            )

        r, c = current
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] == 0 or npos in visited:
                continue

            new_g = g_cur + 1
            if new_g < g.get(npos, float('inf')):
                g[npos] = new_g
                parent[npos] = current
                h_new = manhattan(npos, goal)
                counter += 1
                heapq.heappush(open_heap, (new_g + h_new, counter, npos))
                open_set.add(npos)

    elapsed = (time.time() - t0) * 1000
    return PathResult(
        algo_name='A*',
        start=start, goal=goal,
        steps=steps, path=[],
        total_visited=len(visited),
        found=False,
        elapsed_ms=elapsed
    )
