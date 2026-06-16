# algorithms/backtracking.py — Nhóm 4: CSP — Backtracking Search
"""
Backtracking Search — Tìm kiếm có quay lui (CSP)
══════════════════════════════════════════════════
Nhóm: Constraint Satisfaction Problem (CSP)
Bài toán: Tìm đường đi từ Start đến Goal bằng cách
          xây dựng đường đi từng bước, quay lui khi gặp ngõ cụt

Trạng thái bắt đầu:
    - Vị trí: Start (r, c)
    - Đường đi hiện tại: [Start]
    - Các biến: vị trí từng bước đi
    - Ràng buộc: ô tiếp theo phải là sàn, chưa trong đường đi hiện tại

Các bước thực hiện:
    - Tại ô hiện tại, thử từng hướng đi (ưu tiên hướng gần Goal)
    - Nếu hướng hợp lệ → di chuyển, ghi nhận bước FORWARD
    - Nếu tất cả hướng bị chặn → BACKTRACK (quay lại ô trước)
    - Bước BACKTRACK được hiển thị màu đỏ rõ ràng
    - Tiếp tục đến khi đến Goal hoặc đã thử hết

Trạng thái kết thúc:
    - Found: đường đi từ Start→Goal (tìm theo thứ tự cố định)
    - Not found: đã thử mọi hướng, không có đường

Đặc điểm:
    - Minh họa rõ backtrack: thấy đường đi ngắn lại khi quay lui
    - Tương đương DFS nhưng HIỂN THỊ rõ ràng bước quay lui
    - Phù hợp giải CSP dạng maze (tìm assignment thỏa ràng buộc)
"""

import time
from typing import List, Tuple
from algorithms.base import Step, PathResult


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def run_backtracking(grid: List[List[int]],
                     start: Tuple[int, int],
                     goal: Tuple[int, int],
                     rows: int, cols: int) -> PathResult:
    """
    Backtracking đệ quy, ghi lại từng bước FORWARD và BACKTRACK.
    Hướng đi được sắp xếp theo heuristic (gần Goal trước).
    """
    t0 = time.time()
    steps: List[Step] = []
    visited_global = set()  # tất cả ô đã thử (kể cả đã backtrack)
    step_num = [0]
    result_path = [None]

    # Bước 0 - trạng thái ban đầu
    steps.append(Step(
        step_num=0,
        current=start,
        frontier=[],
        visited=set(),
        path_so_far=[start],
        description=f"[Bắt đầu] Tại {start} | Đường hiện tại = [{start}]",
    ))

    def backtrack(current: Tuple[int,int], path: List[Tuple[int,int]],
                  on_path: set) -> bool:
        """
        Đệ quy backtracking.
        path: đường đi hiện tại (list có thứ tự)
        on_path: tập ô trong đường hiện tại (để kiểm tra nhanh)
        """
        if current == goal:
            result_path[0] = path[:]
            return True

        r, c = current
        # Sắp xếp hướng: ưu tiên ô gần Goal (heuristic)
        dirs_sorted = sorted(
            DIRECTIONS,
            key=lambda d: manhattan((r+d[0], c+d[1]), goal)
        )

        for dr, dc in dirs_sorted:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)

            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] == 0:
                continue
            if npos in on_path:   # Ràng buộc: không lặp lại
                continue

            visited_global.add(npos)
            step_num[0] += 1
            path.append(npos)
            on_path.add(npos)

            h_cur = manhattan(npos, goal)
            desc = (f"[Bước {step_num[0]}] FORWARD → {npos} | "
                    f"h={h_cur} | Độ sâu={len(path)-1} | "
                    f"Đường đi: {len(path)} bước")

            steps.append(Step(
                step_num=step_num[0],
                current=npos,
                frontier=[],
                visited=set(visited_global),
                path_so_far=path[:],
                description=desc,
                is_backtrack=False,
                extra={'depth': len(path)-1, 'h': h_cur}
            ))

            if backtrack(npos, path, on_path):
                return True

            # BACKTRACK
            path.pop()
            on_path.discard(npos)
            step_num[0] += 1

            desc_bt = (f"[Bước {step_num[0]}] BACKTRACK ← {npos} | "
                       f"Quay về {current} | Đường đi: {len(path)} bước")

            steps.append(Step(
                step_num=step_num[0],
                current=current,
                frontier=[],
                visited=set(visited_global),
                path_so_far=path[:],
                description=desc_bt,
                is_backtrack=True,
                extra={'backtrack_from': npos}
            ))

        return False

    on_path_init = {start}
    backtrack(start, [start], on_path_init)

    elapsed = (time.time() - t0) * 1000
    found = result_path[0] is not None
    return PathResult(
        algo_name='Backtrack',
        start=start, goal=goal,
        steps=steps,
        path=result_path[0] if found else [],
        total_visited=len(visited_global),
        found=found,
        elapsed_ms=elapsed
    )
