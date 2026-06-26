# algorithms/local/steepest_hc.py — Nhóm 3: Local Search — Steepest Hill Climbing
"""
Steepest Hill Climbing — Leo đồi dốc nhất (Bản thuần túy)
==========================================================
Nhóm: Local Search (Tìm kiếm cục bộ)
Bài toán: Tìm đường Start→Goal bằng cách luôn chọn bước cải thiện
          NHIỀU NHẤT (dốc nhất) về phía Goal.
          Nếu gặp Cực trị cục bộ (Local Minimum) hoặc Ngõ cụt, thuật toán
          sẽ dừng lại và BÁO THẤT BẠI ngay lập tức (không quay lui, không vượt dốc).

Trạng thái bắt đầu:
    - Vị trí: Start (r, c)
    - Hàm đánh giá: h(n) = Manhattan(n, Goal)  [muốn tối thiểu hóa]

Các bước thực hiện:
    1. Tại ô hiện tại, đánh giá TẤT CẢ ô kề hợp lệ chưa đi qua.
    2. Tìm ô kề tốt nhất có h(best_neighbor) nhỏ nhất.
    3. Nếu h(best_neighbor) < h(current):
       - Di chuyển sang ô kề tốt nhất đó (Leo đồi).
    4. Nếu h(best_neighbor) >= h(current) hoặc không còn ô kề:
       - AI rơi vào Cực trị cục bộ (hoặc ngõ cụt) -> Báo Thất Bại và DỪNG THUẬT TOÁN.
"""

import time
from typing import List, Tuple, Set
from algorithms.base import Step, PathResult


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def run_steepest_hc(grid: List[List[int]],
                    start: Tuple[int,int],
                    goal: Tuple[int,int],
                    rows: int, cols: int) -> PathResult:
    """
    Steepest Hill Climbing bản thuần túy: dừng và báo thất bại ngay khi gặp cực trị cục bộ.
    """
    t0 = time.time()
    steps: List[Step] = []
    step_num = 0

    current = start
    path = [start]
    visited_all = {start}

    h_start = manhattan(start, goal)
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[],
        visited={start},
        path_so_far=[start],
        description=(f"[Bắt đầu] Vị trí: {start} | h={h_start} | "
                     f"Chiến lược: Chỉ di chuyển nếu bước đi tiếp theo CẢI THIỆN dốc nhất"),
        extra={'h': h_start, 'mode': 'start'}
    ))

    max_steps = 1000
    found = False
    stuck = False

    for _ in range(max_steps):
        if current == goal:
            found = True
            break

        r, c = current
        h_cur = manhattan(current, goal)

        # Tìm tất cả ô kề hợp lệ chưa nằm trên đường đi (path)
        candidates = []
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            npos = (nr, nc)
            if (0 <= nr < rows and 0 <= nc < cols
                    and grid[nr][nc] != 0
                    and npos not in visited_all):
                candidates.append((manhattan(npos, goal), npos))

        # Sắp xếp để lấy ô có h nhỏ nhất (tốt nhất)
        candidates.sort()

        # Nếu không còn hướng nào đi được nữa
        if not candidates:
            stuck = True
            step_num += 1
            steps.append(Step(
                step_num=step_num,
                current=current,
                frontier=[],
                visited=set(visited_all),
                path_so_far=list(path),
                description=(f"[Bước {step_num}] THẤT BẠI: Hết đường đi tại {current}! "
                             f"Rơi vào ngõ cụt."),
                is_backtrack=True,
                extra={'h': h_cur, 'mode': 'stuck'}
            ))
            break

        best_h, best_n = candidates[0]

        # Kiểm tra xem có cải thiện heuristic (h) không
        if best_h < h_cur:
            # Di chuyển thành công
            current = best_n
            path.append(best_n)
            visited_all.add(best_n)

            step_num += 1
            all_h_str = ", ".join(f"h={h}" for h, _ in candidates[:3])
            desc = (f"[Bước {step_num}] DI CHUYỂN -> {best_n} | "
                    f"h: {h_cur} -> {best_h} (cải thiện) | "
                    f"Tất cả kề: [{all_h_str}]")
            steps.append(Step(
                step_num=step_num,
                current=best_n,
                frontier=[n for _, n in candidates[1:]],
                visited=set(visited_all),
                path_so_far=list(path),
                description=desc,
                is_backtrack=False,
                extra={'h': best_h, 'mode': 'climb', 'h_prev': h_cur}
            ))
        else:
            # Bị kẹt ở cực trị cục bộ (best_h >= h_cur) -> Dừng và báo thất bại luôn!
            stuck = True
            step_num += 1
            steps.append(Step(
                step_num=step_num,
                current=current,
                frontier=[n for _, n in candidates],
                visited=set(visited_all),
                path_so_far=list(path),
                description=(f"[Bước {step_num}] THẤT BẠI: Dính CỰC TRỊ CỤC BỘ tại {current}! "
                             f"h hiện tại ({h_cur}) <= h tốt nhất của ô kề ({best_h})."),
                is_backtrack=True,
                extra={'h': h_cur, 'mode': 'stuck'}
            ))
            break

    elapsed = (time.time() - t0) * 1000

    return PathResult(
        algo_name='Steepest HC',
        start=start, goal=goal,
        steps=steps,
        path=path if found else [],
        total_visited=len(visited_all),
        found=found,
        elapsed_ms=elapsed
    )
