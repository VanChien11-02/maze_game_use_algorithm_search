# algorithms/adversarial/minimax.py — Nhóm 6: Tìm kiếm đối kháng — Minimax
"""
Minimax — Thuật toán tìm kiếm đối kháng với Alpha-Beta Pruning.
════════════════════════════════════════════════════
Nhóm: Adversarial Search (Tìm kiếm đối kháng)
Bài toán: MAX (Người chơi) tìm đường tới Goal, MIN (Quái vật) chủ động săn đuổi MAX.

Hàm đánh giá (Evaluation Function):
    Score = (Khoảng cách tới quái vật) * 1.5 - (Khoảng cách tới đích) - (Hình phạt lặp ô)

Nếu bị quái vật bắt (cùng ô): -99999
Nếu đến đích (Goal): 99999
"""

import time
from collections import deque
from typing import List, Tuple
from algorithms.base import Step, PathResult


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_valid_moves(grid: List[List[int]], pos: Tuple[int, int], rows: int, cols: int) -> List[Tuple[int, int]]:
    r, c = pos
    moves = []
    # Thứ tự di chuyển: Lên, Xuống, Trái, Phải
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
            moves.append((nr, nc))
    return moves


def find_path_bfs(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int], rows: int, cols: int) -> List[Tuple[int, int]]:
    """Tìm đường ngắn nhất đơn giản bằng BFS để xác định vị trí xuất phát cho quái vật."""
    queue = deque([start])
    parent = {start: None}
    while queue:
        curr = queue.popleft()
        if curr == goal:
            break
        r, c = curr
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and npos not in parent:
                parent[npos] = curr
                queue.append(npos)
    path = []
    curr = goal
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)
    path.reverse()
    if path and path[0] == start:
        return path
    return []


def minimax_search(p_pos: Tuple[int, int],
                   g_pos: Tuple[int, int],
                   depth: int,
                   alpha: float,
                   beta: float,
                   is_max_turn: bool,
                   grid: List[List[int]],
                   goal: Tuple[int, int],
                   rows: int, cols: int,
                   path_so_far: List[Tuple[int, int]]) -> Tuple[float, Tuple[int, int]]:
    """
    Tìm kiếm cây trò chơi Minimax với cắt tỉa Alpha-Beta.
    MAX = Người chơi, MIN = Quái vật.
    """
    if p_pos == goal:
        return 100000.0 + depth, p_pos
    if p_pos == g_pos:
        return -100000.0 - depth, p_pos
    if depth == 0:
        dist_ghost = manhattan(p_pos, g_pos)
        dist_goal = manhattan(p_pos, goal)
        score = dist_ghost * 1.5 - dist_goal
        
        # Hình phạt lặp ô dựa trên độ gần của bước đi (recency penalty) để chống vòng lặp và giúp thoát ngõ cụt
        recency_penalty = 0.0
        for idx, visited_pos in enumerate(reversed(path_so_far[-15:])):
            if p_pos == visited_pos:
                recency_penalty += (15 - idx) * 12.0
        score -= recency_penalty
        return score, p_pos

    if is_max_turn:
        max_val = -float('inf')
        best_move = p_pos
        moves = get_valid_moves(grid, p_pos, rows, cols)
        if not moves:
            return -100000.0, p_pos
        for mv in moves:
            val, _ = minimax_search(mv, g_pos, depth - 1, alpha, beta, False, grid, goal, rows, cols, path_so_far)
            if val > max_val:
                max_val = val
                best_move = mv
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_val, best_move
    else:
        min_val = float('inf')
        best_move = g_pos
        moves = get_valid_moves(grid, g_pos, rows, cols)
        if not moves:
            return 100000.0, g_pos
        for mv in moves:
            val, _ = minimax_search(p_pos, mv, depth - 1, alpha, beta, True, grid, goal, rows, cols, path_so_far)
            if val < min_val:
                min_val = val
                best_move = mv
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_val, best_move


def run_minimax(grid: List[List[int]],
                start: Tuple[int, int],
                goal: Tuple[int, int],
                rows: int, cols: int) -> PathResult:
    """
    Chạy mô phỏng trận đấu đối kháng giữa Player (Minimax) và Ghost (Chasing).
    """
    t0 = time.time()
    steps: List[Step] = []
    
    # Tìm vị trí xuất phát cho quái vật (khoảng 1/3 quãng đường của BFS path)
    bfs_path = find_path_bfs(grid, start, goal, rows, cols)
    if len(bfs_path) > 9:
        ghost_start = bfs_path[max(len(bfs_path) // 3, 4)]
    else:
        # Nếu đường đi quá ngắn, lấy một ô sàn bất kỳ xa start
        ghost_start = goal
        
    p_pos = start
    g_pos = ghost_start
    path_so_far = [start]
    visited = {start}
    step_num = 0
    max_steps = 250
    found = False

    # Bước 0: Khởi đầu
    steps.append(Step(
        step_num=0,
        current=p_pos,
        frontier=get_valid_moves(grid, p_pos, rows, cols),
        visited=set(visited),
        path_so_far=list(path_so_far),
        description=f"[Bắt đầu] Người chơi tại {p_pos}, Quái vật tại {g_pos}.",
        extra={
            'ghost': g_pos,
            'dist_goal': manhattan(p_pos, goal),
            'dist_ghost': manhattan(p_pos, g_pos),
            'score': 0.0
        }
    ))

    while step_num < max_steps:
        # 1. Người chơi (MAX) chọn bước đi bằng Minimax
        # Sử dụng depth=3 hoặc 4 để đảm bảo phản hồi nhanh chóng
        score, best_move = minimax_search(p_pos, g_pos, 3, -float('inf'), float('inf'), True, grid, goal, rows, cols, path_so_far)
        
        if best_move is None or best_move == p_pos:
            valid_moves = get_valid_moves(grid, p_pos, rows, cols)
            p_pos = valid_moves[0] if valid_moves else p_pos
        else:
            p_pos = best_move
            
        path_so_far.append(p_pos)
        visited.add(p_pos)
        step_num += 1

        # Kiểm tra nếu người chơi chạm đích trước khi quái vật di chuyển
        if p_pos == goal:
            steps.append(Step(
                step_num=step_num,
                current=p_pos,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path_so_far),
                description=f"[Bước {step_num}] Người chơi di chuyển đến {p_pos} và THÀNH CÔNG đến đích!",
                extra={
                    'ghost': g_pos,
                    'dist_goal': 0,
                    'dist_ghost': manhattan(p_pos, g_pos),
                    'score': 99999.0
                }
            ))
            found = True
            break

        # Kiểm tra nếu người chơi tự đi vào quái vật
        if p_pos == g_pos:
            steps.append(Step(
                step_num=step_num,
                current=p_pos,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path_so_far),
                description=f"[Bước {step_num}] Người chơi đi nhầm vào quái vật tại {p_pos} và BỊ BẮT!",
                extra={
                    'ghost': g_pos,
                    'dist_goal': manhattan(p_pos, goal),
                    'dist_ghost': 0,
                    'score': -99999.0
                }
            ))
            found = False
            break

        # 2. Quái vật (MIN) di chuyển đuổi theo người chơi (Greedy Chasing)
        g_moves = get_valid_moves(grid, g_pos, rows, cols)
        best_g_move = g_pos
        min_g_dist = float('inf')
        for mv in g_moves:
            d = manhattan(mv, p_pos)
            if d < min_g_dist:
                min_g_dist = d
                best_g_move = mv
        g_pos = best_g_move

        # Kiểm tra nếu quái vật vồ trúng người chơi
        if g_pos == p_pos:
            steps.append(Step(
                step_num=step_num,
                current=p_pos,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path_so_far),
                description=f"[Bước {step_num}] Quái vật di chuyển đến {g_pos} và BẮT được người chơi!",
                extra={
                    'ghost': g_pos,
                    'dist_goal': manhattan(p_pos, goal),
                    'dist_ghost': 0,
                    'score': -99999.0
                }
            ))
            found = False
            break

        # Lưu bước đi bình thường
        desc = (f"[Bước {step_num}] Người chơi đi đến {p_pos} (Minimax đ.giá {score:.1f}). "
                f"Quái vật đuổi tới {g_pos}.")
        steps.append(Step(
            step_num=step_num,
            current=p_pos,
            frontier=get_valid_moves(grid, p_pos, rows, cols),
            visited=set(visited),
            path_so_far=list(path_so_far),
            description=desc,
            extra={
                'ghost': g_pos,
                'dist_goal': manhattan(p_pos, goal),
                'dist_ghost': manhattan(p_pos, g_pos),
                'score': score
            }
        ))

    elapsed = (time.time() - t0) * 1000
    # Nếu hết số bước tối đa mà chưa về đích/bị bắt
    if step_num >= max_steps and not found:
        # Ghi đè mô tả cuối cùng
        steps[-1].description = f"[Hết giờ] Không thể đến đích sau {max_steps} bước."

    return PathResult(
        algo_name='Minimax',
        start=start,
        goal=goal,
        steps=steps,
        path=path_so_far if found else [],
        total_visited=len(visited),
        found=found,
        elapsed_ms=elapsed
    )
