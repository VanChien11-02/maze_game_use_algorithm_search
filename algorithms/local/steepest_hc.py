# algorithms/steepest_hc.py — Nhóm 3: Local Search — Steepest Hill Climbing
"""
Steepest Hill Climbing — Leo đồi dốc nhất
══════════════════════════════════════════
Nhóm: Local Search (Tìm kiếm cục bộ)
Bài toán: Tìm đường Start→Goal bằng cách luôn chọn bước cải thiện
          NHIỀU NHẤT (dốc nhất) về phía Goal.

Trạng thái bắt đầu:
    - Vị trí: Start (r, c)
    - Hàm đánh giá: h(n) = Manhattan(n, Goal)  [muốn tối thiểu hóa]

Các bước thực hiện:
    1. Tại ô hiện tại, đánh giá TẤT CẢ ô kề hợp lệ
    2. Tìm ô có h(n) NHỎ NHẤT (cải thiện nhiều nhất / dốc nhất)
    3a. Nếu h(best_neighbor) < h(current) → DI CHUYỂN (leo dốc)
    3b. Nếu bị kẹt (không cải thiện) → Ghi nhận BÍ
        → Quay lui đến vị trí trước, thử hướng khác (thoát local optimum)
    4. Lặp đến khi đến Goal hoặc hết bước

Trạng thái kết thúc:
    - Found: đến Goal
    - Stuck: bị kẹt vĩnh viễn ở cực trị cục bộ

Khác biệt với Greedy Best-First:
    - Steepest HC: PHẢI cải thiện h mỗi bước, báo BÍ rõ ràng
    - Greedy BFS:  dùng priority queue toàn cục, không bị bí
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
    Steepest Hill Climbing với backtracking khi bị kẹt.
    Dùng stack để quay lui: giống leo đồi nhưng khi bí → thử hướng khác.
    """
    t0 = time.time()
    steps: List[Step] = []
    step_num = 0

    # Dùng stack chứa (position, tried_neighbors)
    # để cho phép backtrack khi bị kẹt
    stack = [(start, [])]    # (current_pos, neighbors_already_tried)
    path  = [start]
    path_set = {start}
    visited_all = {start}

    h_start = manhattan(start, goal)
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[],
        visited={start},
        path_so_far=[start],
        description=(f"[Bắt đầu] Vị trí: {start} | h={h_start} | "
                     f"Chiến lược: LUÔN chọn bước CẢI THIỆN DỐC NHẤT"),
        extra={'h': h_start, 'mode': 'start'}
    ))

    max_steps = 8000
    for _ in range(max_steps):
        if not stack:
            break

        current, tried = stack[-1]

        if current == goal:
            break

        r, c = current
        h_cur = manhattan(current, goal)

        # Tìm tất cả ô kề hợp lệ chưa thử
        candidates = []
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            npos = (nr, nc)
            if (0 <= nr < rows and 0 <= nc < cols
                    and grid[nr][nc] != 0
                    and npos not in path_set
                    and npos not in tried):
                candidates.append((manhattan(npos, goal), npos))

        # Sắp xếp: dốc nhất trước (h nhỏ nhất)
        candidates.sort()

        if not candidates:
            # Bị kẹt hoàn toàn tại đây → BACKTRACK
            stack.pop()
            if stack:
                path.pop()
                path_set.discard(current)
                backtrack_to = stack[-1][0]

                step_num += 1
                steps.append(Step(
                    step_num=step_num,
                    current=backtrack_to,
                    frontier=[],
                    visited=set(visited_all),
                    path_so_far=list(path),
                    description=(f"[Bước {step_num}] BÍ hoàn toàn tại {current} → "
                                 f"BACKTRACK về {backtrack_to} | "
                                 f"Thử hướng khác"),
                    is_backtrack=True,
                    extra={'h': manhattan(backtrack_to, goal), 'mode': 'backtrack',
                           'stuck_at': current}
                ))
            continue

        # Lấy ô tốt nhất (dốc nhất)
        best_h, best_n = candidates[0]

        # Đánh dấu ô này đã thử
        tried.append(best_n)
        visited_all.add(best_n)

        if best_h < h_cur:
            # Di chuyen duoc (cai thien)
            stack.append((best_n, []))
            path.append(best_n)
            path_set.add(best_n)

            step_num += 1
            all_h_str = ", ".join(f"h={h}" for h,_ in candidates[:3])
            desc = (f"[Bước {step_num}] DI CHUYỂN → {best_n} | "
                    f"h: {h_cur}→{best_h} (dốc nhất) | "
                    f"Tất cả kề: [{all_h_str}] | "
                    f"Độ sâu: {len(path)-1}")
            steps.append(Step(
                step_num=step_num,
                current=best_n,
                frontier=[n for _,n in candidates[1:]],
                visited=set(visited_all),
                path_so_far=list(path),
                description=desc,
                is_backtrack=False,
                extra={'h': best_h, 'mode': 'climb',
                       'h_prev': h_cur, 'improvement': h_cur - best_h}
            ))
        else:
            # Khong cai thien - bi cuc bo
            stack.append((best_n, []))
            path.append(best_n)
            path_set.add(best_n)

            step_num += 1
            steps.append(Step(
                step_num=step_num,
                current=best_n,
                frontier=[n for _,n in candidates[1:]],
                visited=set(visited_all),
                path_so_far=list(path),
                description=(f"[Buoc {step_num}] CUC TRI CUC BO tai {current} | "
                             f"h_cur={h_cur}, h_best={best_h} (khong cai thien!) | "
                             f"Buoc sang {best_n}"),
                is_backtrack=True,
                extra={'h': best_h, 'mode': 'stuck',
                       'h_prev': h_cur, 'delta': best_h - h_cur}
            ))

    elapsed = (time.time() - t0) * 1000
    current_final = stack[-1][0] if stack else path[-1] if path else start
    found = (current_final == goal)

    return PathResult(
        algo_name='Steepest HC',
        start=start, goal=goal,
        steps=steps,
        path=path if found else [],
        total_visited=len(visited_all),
        found=found,
        elapsed_ms=elapsed
    )
