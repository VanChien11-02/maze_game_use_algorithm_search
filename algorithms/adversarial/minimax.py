# algorithms/adversarial/minimax.py — Nhóm 6: Tìm kiếm đối kháng — Minimax
"""
Minimax — Thuật toán tìm kiếm đối kháng với Alpha-Beta Pruning kết hợp mô hình FSM.
════════════════════════════════════════════════════
Nhóm: Adversarial Search (Tìm kiếm đối kháng)
Bài toán: MAX (Người chơi) tìm đường tới Goal, MIN (Quái vật) săn đuổi MAX.

FSM:
    - Quái vật (Monster): WANDER (đi random chậm) hoặc CHASE (đuổi sát bằng A*)
    - Người chơi (Player): NORMAL (chạy nhanh bằng A*) hoặc ESCAPE (né bằng Minimax)
"""

import time
import heapq
import random
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


def find_path_astar(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int], rows: int, cols: int) -> List[Tuple[int, int]]:
    """Thuật toán A* để tìm đường đi ngắn nhất hoàn chỉnh."""
    if start == goal:
        return [start]
    open_set = []
    # Lưu dạng: (f_score, g_score, current, path)
    heapq.heappush(open_set, (manhattan(start, goal), 0, start, [start]))
    visited = {start: 0}
    
    while open_set:
        f, g, curr, path = heapq.heappop(open_set)
        if curr == goal:
            return path
        
        r, c = curr
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                new_g = g + 1
                if npos not in visited or new_g < visited[npos]:
                    visited[npos] = new_g
                    h = manhattan(npos, goal)
                    heapq.heappush(open_set, (new_g + h, new_g, npos, path + [npos]))
    return []


def minimax_search(p_pos: Tuple[int, int],
                   g_pos: Tuple[int, int],
                   depth: int,
                   is_max_turn: bool,
                   grid: List[List[int]],
                   goal: Tuple[int, int],
                   rows: int, cols: int,
                   path_so_far: List[Tuple[int, int]],
                   simulated_steps: int) -> Tuple[float, Tuple[int, int]]:
    """
    Tìm kiếm cây trò chơi Minimax thuần túy (không cắt tỉa Alpha-Beta) và hình phạt số bước.
    """
    if p_pos == goal:
        return 100000.0 + depth - simulated_steps, p_pos
    if p_pos == g_pos:
        return -100000.0 - depth - simulated_steps, p_pos
    if depth == 0:
        dist_ghost = manhattan(p_pos, g_pos)
        dist_goal = manhattan(p_pos, goal)
        
        # Hình phạt lặp ô (recency penalty)
        recency_penalty = 0.0
        for idx, visited_pos in enumerate(reversed(path_so_far[-15:])):
            if p_pos == visited_pos:
                recency_penalty += (15 - idx) * 12.0
                
        # Trừ điểm số bước đi để ép AI tối ưu thời gian (step penalty)
        step_penalty = simulated_steps * 2.0
        
        score = dist_ghost * 1.5 - dist_goal - step_penalty - recency_penalty
        return score, p_pos

    if is_max_turn:
        max_val = -float('inf')
        best_move = p_pos
        moves = get_valid_moves(grid, p_pos, rows, cols)
        if not moves:
            return -100000.0 - simulated_steps, p_pos
        for mv in moves:
            val, _ = minimax_search(mv, g_pos, depth - 1, False, grid, goal, rows, cols, path_so_far, simulated_steps + 1)
            if val > max_val:
                max_val = val
                best_move = mv
        return max_val, best_move
    else:
        min_val = float('inf')
        best_move = g_pos
        moves = get_valid_moves(grid, g_pos, rows, cols)
        if not moves:
            return 100000.0 - simulated_steps, g_pos
        for mv in moves:
            val, _ = minimax_search(p_pos, mv, depth - 1, True, grid, goal, rows, cols, path_so_far, simulated_steps + 1)
            if val < min_val:
                min_val = val
                best_move = mv
        return min_val, best_move


def run_minimax(grid: List[List[int]],
                start: Tuple[int, int],
                goal: Tuple[int, int],
                rows: int, cols: int) -> PathResult:
    """
    Chạy mô phỏng trận đấu sử dụng Máy trạng thái hữu hạn (FSM).
    """
    t0 = time.time()
    steps: List[Step] = []
    
    # Sinh quái vật tại 1/3 đường đi BFS ban đầu
    bfs_path = find_path_bfs(grid, start, goal, rows, cols)
    if len(bfs_path) > 9:
        ghost_start = bfs_path[max(len(bfs_path) // 3, 4)]
    else:
        ghost_start = goal
        
    p_pos = start
    g_pos = ghost_start
    path_so_far = [start]
    visited = {start}
    step_num = 0
    max_steps = 250
    found = False
    
    aggro_radius = 6

    # Đưa bước 0 vào
    steps.append(Step(
        step_num=0,
        current=p_pos,
        frontier=get_valid_moves(grid, p_pos, rows, cols),
        visited=set(visited),
        path_so_far=list(path_so_far),
        description=f"[Bắt đầu] Người chơi tại {p_pos}, Quái vật tại {g_pos}.",
        extra={
            'ghost': g_pos,
            'dist_ghost': manhattan(p_pos, g_pos),
            'player_state': 'NORMAL',
            'ghost_state': 'WANDER',
            'dist_goal': manhattan(p_pos, goal)
        }
    ))

    while step_num < max_steps:
        # Cập nhật FSM
        dist = manhattan(p_pos, g_pos)
        is_aggro = (dist <= aggro_radius)
        
        p_state = 'ESCAPE' if is_aggro else 'NORMAL'
        g_state = 'CHASE' if is_aggro else 'WANDER'
        
        # 1. Lượt Người chơi (AI)
        if p_state == 'NORMAL':
            # Đi bình thường bằng A* thẳng tới goal
            p_path = find_path_astar(grid, p_pos, goal, rows, cols)
            if len(p_path) >= 2:
                p_pos = p_path[1]
            else:
                # Fallback di chuyển ngẫu nhiên
                valid = get_valid_moves(grid, p_pos, rows, cols)
                if valid:
                    p_pos = random.choice(valid)
            score_desc = "A* dẫn đường"
        else:
            # Gặp nguy hiểm, kích hoạt Minimax thuần túy
            score, best_move = minimax_search(p_pos, g_pos, 3, True, grid, goal, rows, cols, path_so_far, step_num)
            if best_move and best_move != p_pos:
                p_pos = best_move
            else:
                valid = get_valid_moves(grid, p_pos, rows, cols)
                if valid:
                    p_pos = random.choice(valid)
            score_desc = f"Minimax đ.giá {score:.1f}"

        path_so_far.append(p_pos)
        visited.add(p_pos)
        step_num += 1

        # Kiểm tra thắng cuộc ngay khi người chơi di chuyển
        if p_pos == goal:
            steps.append(Step(
                step_num=step_num,
                current=p_pos,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path_so_far),
                description=f"[Bước {step_num}] AI ({p_state}) đến đích thành công!",
                extra={
                    'ghost': g_pos,
                    'dist_ghost': manhattan(p_pos, g_pos),
                    'player_state': p_state,
                    'ghost_state': g_state,
                    'dist_goal': 0
                }
            ))
            found = True
            break

        # Kiểm tra va chạm
        if p_pos == g_pos:
            steps.append(Step(
                step_num=step_num,
                current=p_pos,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path_so_far),
                description=f"[Bước {step_num}] AI va phải quái vật tại {p_pos} và BỊ BẮT!",
                extra={
                    'ghost': g_pos,
                    'dist_ghost': 0,
                    'player_state': p_state,
                    'ghost_state': g_state,
                    'dist_goal': manhattan(p_pos, goal)
                }
            ))
            found = False
            break

        # 2. Lượt Quái vật
        # Nếu WANDER, quái đi random và chỉ di chuyển mỗi 2 bước (bước chẵn)
        if g_state == 'WANDER':
            if step_num % 2 == 0:
                g_moves = get_valid_moves(grid, g_pos, rows, cols)
                if g_moves:
                    g_pos = random.choice(g_moves)
                g_desc = "Quái dạo chơi (WANDER)"
            else:
                g_desc = "Quái đứng yên (tốc độ 1/2)"
        else:
            # CHASE: quái dùng A* đuổi theo sát nút AI
            g_path = find_path_astar(grid, g_pos, p_pos, rows, cols)
            if len(g_path) >= 2:
                g_pos = g_path[1]
            g_desc = "Quái đuổi gấp (CHASE bằng A*)"

        # Kiểm tra nếu quái bắt được AI
        if g_pos == p_pos:
            steps.append(Step(
                step_num=step_num,
                current=p_pos,
                frontier=[],
                visited=set(visited),
                path_so_far=list(path_so_far),
                description=f"[Bước {step_num}] Quái bắt được AI tại {g_pos}!",
                extra={
                    'ghost': g_pos,
                    'dist_ghost': 0,
                    'player_state': p_state,
                    'ghost_state': g_state,
                    'dist_goal': manhattan(p_pos, goal)
                }
            ))
            found = False
            break

        # Ghi nhận bước đi bình thường
        desc = (f"[Bước {step_num}] AI ở trạng thái {p_state} ({score_desc}). "
                f"{g_desc} tại {g_pos}.")
        steps.append(Step(
            step_num=step_num,
            current=p_pos,
            frontier=get_valid_moves(grid, p_pos, rows, cols),
            visited=set(visited),
            path_so_far=list(path_so_far),
            description=desc,
            extra={
                'ghost': g_pos,
                'dist_ghost': manhattan(p_pos, g_pos),
                'player_state': p_state,
                'ghost_state': g_state,
                'dist_goal': manhattan(p_pos, goal)
            }
        ))

    elapsed = (time.time() - t0) * 1000
    if step_num >= max_steps and not found:
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
