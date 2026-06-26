# generation/maze_generator.py — Sinh mê cung 30x30 bằng DFS recursive backtracking
"""
Sinh mê cung hoàn hảo (Perfect Maze) bằng DFS Recursive Backtracking.
Đảm bảo có đúng 1 đường đi giữa 2 ô bất kỳ → thuật toán luôn tìm thấy đường.
"""

import random
from typing import List, Tuple
from collections import deque


def generate_maze(cols: int, rows: int, seed: int = None) -> List[List[int]]:
    """
    Sinh mê cung perfect maze bằng DFS Recursive Backtracking.
    grid[r][c] = 0: tường | 1: sàn (có thể đi)
    Cols và Rows nên là số lẻ để thuật toán hoạt động đúng.
    """
    if seed is not None:
        random.seed(seed)

    # Đảm bảo số lẻ
    gc = cols if cols % 2 == 1 else cols - 1
    gr = rows if rows % 2 == 1 else rows - 1

    # Khởi tạo toàn tường
    grid = [[0] * gc for _ in range(gr)]

    def in_bounds(r, c):
        return 0 < r < gr - 1 and 0 < c < gc - 1

    def carve(r, c):
        grid[r][c] = 1
        dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and grid[nr][nc] == 0:
                grid[r + dr//2][c + dc//2] = 1
                carve(nr, nc)

    import sys
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(20000)
    carve(1, 1)
    sys.setrecursionlimit(old)

    # Điều chỉnh kích thước nếu cần
    final = [[0] * cols for _ in range(rows)]
    for r in range(min(gr, rows)):
        for c in range(min(gc, cols)):
            final[r][c] = grid[r][c]

    return final


def find_start_exit(grid: List[List[int]], rows: int, cols: int
                    ) -> Tuple[Tuple[int,int], Tuple[int,int]]:
    """
    Chọn ngẫu nhiên điểm Start và Goal từ tập các ô sàn,
    đảm bảo chúng cách nhau ít nhất một khoảng cách Manhattan nhất định.
    """
    floors = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0:
                floors.append((r, c))

    if len(floors) < 2:
        return (1, 1), (rows-2, cols-2)

    # Đảm bảo khoảng cách Manhattan tối thiểu giữa Start và Goal
    min_dist = max(10, min(rows, cols) * 2 // 3)

    for _ in range(300):
        start = random.choice(floors)
        goal = random.choice(floors)
        if start != goal and abs(start[0] - goal[0]) + abs(start[1] - goal[1]) >= min_dist:
            return start, goal

    # Fallback
    start = random.choice(floors)
    goal = random.choice(floors)
    while start == goal:
        goal = random.choice(floors)
    return start, goal


def add_extra_passages(grid: List[List[int]], rows: int, cols: int,
                        extra: int = 5) -> List[List[int]]:
    """
    Thêm một số đường thông để mê cung không quá tuyến tính.
    Tạo nhiều lựa chọn đường đi → thú vị hơn khi so sánh các thuật toán.
    """
    walls = []
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 0:
                has_h = (c > 0 and c < cols-1 and
                         grid[r][c-1] == 1 and grid[r][c+1] == 1)
                has_v = (r > 0 and r < rows-1 and
                         grid[r-1][c] == 1 and grid[r+1][c] == 1)
                if has_h or has_v:
                    walls.append((r, c))

    random.shuffle(walls)
    for r, c in walls[:extra]:
        grid[r][c] = 1

    return grid


def braid_maze(grid: List[List[int]], rows: int, cols: int,
               ratio: float = 0.35) -> List[List[int]]:
    """
    Reduce dead ends by opening one nearby wall for a portion of cul-de-sacs.
    This creates loops and side routes while keeping the maze structure readable.
    """
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def floor_neighbor_count(r: int, c: int) -> int:
        return sum(
            1
            for dr, dc in directions
            if 0 <= r + dr < rows and 0 <= c + dc < cols
            and grid[r + dr][c + dc] != 0
        )

    dead_ends = [
        (r, c)
        for r in range(1, rows - 1)
        for c in range(1, cols - 1)
        if grid[r][c] != 0 and floor_neighbor_count(r, c) == 1
    ]
    random.shuffle(dead_ends)

    openings = max(0, int(len(dead_ends) * ratio))
    for r, c in dead_ends[:openings]:
        candidates = []
        for dr, dc in directions:
            wr, wc = r + dr, c + dc
            br, bc = r + 2 * dr, c + 2 * dc
            if not (1 <= wr < rows - 1 and 1 <= wc < cols - 1):
                continue
            if not (1 <= br < rows - 1 and 1 <= bc < cols - 1):
                continue
            if grid[wr][wc] == 0 and grid[br][bc] != 0:
                candidates.append((wr, wc))

        if candidates:
            wr, wc = random.choice(candidates)
            grid[wr][wc] = 1

    return grid
