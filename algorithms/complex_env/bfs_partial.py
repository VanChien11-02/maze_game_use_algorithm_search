# algorithms/complex_env/bfs_partial.py — Nhom 4: Complex Environment — Belief State Search
"""
Belief State Search — Tim kiem trong me cung toi (Blind Maze)
==============================================================
Nhom: Searching in Complex Environments (Moi truong phuc tap)
Bai toan: AI bi tha vao me cung toi, KHONG BIET vi tri hien tai.
          Ban do me cung (tuong/san) DA BIET TRUOC, nhung khong co
          dau cham bao vi tri.

Trang thai bat dau:
    - Belief State = tap tat ca cac o san trong me cung
    - AI khong biet minh dang o dau
    - Biet dich Goal o dau tren ban do

Cac buoc thuc hien:
    1. AI chon mot huong di (Len/Xuong/Trai/Phai)
    2. Sau moi buoc, AI quan sat ket qua:
       - Neu di duoc (vi tri thay doi) hoac bi chan (tuong)
    3. Loc Belief State: chi giu lai nhung vi tri ma ket qua
       khop voi quan sat thuc te
    4. Khi Belief State con 1 o -> AI da biet chinh xac vi tri
       -> Dung A* de chay thang ve Goal

Trang thai ket thuc:
    - Found: xac dinh vi tri + den duoc Goal
    - Not found: khong the thu hep Belief State

Dac diem:
    - SU DUNG set() de luu Belief State (hash nhanh)
    - SU DUNG tuple(r, c) lam toa do (immutable, hashable)
    - Chien luoc chon huong di: Chon huong chia Belief State
      khong deu nhat de loai bo nhieu vi tri nhat (Information Gain)
    - Khi bi ket (khong loai bo duoc vi tri nao): di chuyen ngau nhien
      de thay doi trang thai tuong doi giua cac vi tri kha thi
"""

import time
import heapq
import random
from collections import deque
from typing import List, Tuple, Set, Optional
from algorithms.base import Step, PathResult


DIRECTIONS = {
    'UP':    (-1, 0),
    'DOWN':  ( 1, 0),
    'LEFT':  ( 0,-1),
    'RIGHT': ( 0, 1),
}

DIR_NAMES = list(DIRECTIONS.keys())


def get_all_floor_cells(grid: List[List[int]], rows: int, cols: int) -> Set[Tuple[int, int]]:
    """Tra ve tap tat ca cac o san (grid[r][c] != 0) trong me cung."""
    floors: Set[Tuple[int, int]] = set()
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0:
                floors.add((r, c))
    return floors


def can_move(grid: List[List[int]], pos: Tuple[int, int],
             dr: int, dc: int, rows: int, cols: int) -> bool:
    """Kiem tra xem tu pos co the di theo huong (dr, dc) khong."""
    nr, nc = pos[0] + dr, pos[1] + dc
    return 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 0


def apply_move(pos: Tuple[int, int], dr: int, dc: int,
               grid: List[List[int]], rows: int, cols: int) -> Tuple[int, int]:
    """Ap dung buoc di. Neu bi tuong thi dung tai cho."""
    nr, nc = pos[0] + dr, pos[1] + dc
    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 0:
        return (nr, nc)
    return pos


def filter_belief(belief: Set[Tuple[int, int]],
                  dr: int, dc: int,
                  actual_moved: bool,
                  grid: List[List[int]],
                  rows: int, cols: int) -> Set[Tuple[int, int]]:
    """
    Loc Belief State sau mot buoc di:
    - actual_moved = True:  chi giu cac vi tri ma CAN di theo (dr, dc)
    - actual_moved = False: chi giu cac vi tri ma KHONG THE di (bi tuong)
    Sau do cap nhat vi tri moi cho cac o con lai.
    """
    new_belief: Set[Tuple[int, int]] = set()
    for pos in belief:
        could_move = can_move(grid, pos, dr, dc, rows, cols)
        if could_move == actual_moved:
            if actual_moved:
                new_belief.add((pos[0] + dr, pos[1] + dc))
            else:
                new_belief.add(pos)
    return new_belief


def choose_best_direction(belief: Set[Tuple[int, int]],
                          grid: List[List[int]],
                          rows: int, cols: int,
                          goal: Tuple[int, int],
                          stall_count: int) -> str:
    """
    Chon huong di tot nhat de thu hep Belief State nhieu nhat.
    Neu da xac dinh vi tri (belief size = 1), chon huong huong ve Goal.
    Khi bi ket (stall), xoay vong qua cac huong de pha doi xung.
    """
    if len(belief) == 1:
        pos = next(iter(belief))
        best_dir = DIR_NAMES[0]
        best_dist = float('inf')
        for name, (dr, dc) in DIRECTIONS.items():
            new_pos = apply_move(pos, dr, dc, grid, rows, cols)
            d = abs(new_pos[0] - goal[0]) + abs(new_pos[1] - goal[1])
            if d < best_dist:
                best_dist = d
                best_dir = name
        return best_dir

    best_dir = DIR_NAMES[0]
    best_score = -1

    for name, (dr, dc) in DIRECTIONS.items():
        can_count = 0
        blocked_count = 0
        for pos in belief:
            if can_move(grid, pos, dr, dc, rows, cols):
                can_count += 1
            else:
                blocked_count += 1
        minority = min(can_count, blocked_count)
        if minority > best_score:
            best_score = minority
            best_dir = name

    # Khi bi ket (khong huong nao loai bo vi tri):
    # Di chuyen de thay doi vi tri tuong doi giua cac vi tri kha thi.
    # Uu tien huong ma DA SO vi tri trong belief co the di duoc,
    # de sau khi di, cac vi tri se "tach ra" o nhung vi tri khac nhau
    # va co the duoc phan biet boi buoc di tiep theo.
    if best_score == 0:
        dir_cycle = ['UP', 'RIGHT', 'DOWN', 'LEFT']
        # Xoay vong dua tren stall_count de thu cac huong khac nhau
        moved_dirs = []
        for offset in range(4):
            name = dir_cycle[(stall_count + offset) % 4]
            dr, dc = DIRECTIONS[name]
            can_count = sum(1 for pos in belief if can_move(grid, pos, dr, dc, rows, cols))
            if can_count > 0:
                moved_dirs.append((can_count, name))
        
        if moved_dirs:
            # Chon huong ma nhieu vi tri nhat co the di duoc
            moved_dirs.sort(key=lambda x: -x[0])
            # Xoay vong qua cac huong di duoc de tang co hoi pha doi xung
            idx = stall_count % len(moved_dirs)
            return moved_dirs[idx][1]

    return best_dir


def find_path_bfs(grid: List[List[int]], start: Tuple[int, int],
                  goal: Tuple[int, int], rows: int, cols: int) -> List[Tuple[int, int]]:
    """BFS tim duong ngan nhat tu start den goal."""
    if start == goal:
        return [start]
    queue = deque([start])
    parent = {start: None}
    visited = {start}
    
    while queue:
        curr = queue.popleft()
        if curr == goal:
            # Reconstruct path
            path = []
            while curr is not None:
                path.append(curr)
                curr = parent[curr]
            return path[::-1]
            
        r, c = curr
        for dr, dc in DIRECTIONS.values():
            nr, nc = r + dr, c + dc
            npos = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 0:
                if npos not in visited:
                    visited.add(npos)
                    parent[npos] = curr
                    queue.append(npos)
    return []


def run_bfs_partial(grid: List[List[int]],
                    start: Tuple[int, int],
                    goal: Tuple[int, int],
                    rows: int, cols: int) -> PathResult:
    """
    Belief State Search: AI bi tha vao me cung toi,
    phai tu khoanh vung vi tri bang cach di chuyen va quan sat.
    """
    t0 = time.time()
    steps: List[Step] = []
    step_num = 0

    # Chon dung 3 trang thai ngau nhien lam Belief State (start dai dien)
    all_floors = list(get_all_floor_cells(grid, rows, cols))
    belief_list = random.sample(all_floors, min(3, len(all_floors)))
    belief: Set[Tuple[int, int]] = set(belief_list)
    initial_size = len(belief)

    # Chon ngau nhien mot trong 3 trang thai lam vi tri thuc te cua player
    actual_pos = random.choice(belief_list)
    start = actual_pos
    full_path = [start]
    visited_pos = {start}
    localized = False

    # Tap hop tat ca cac o trong me cung de lam minimap hien thi toan bo kien truc
    all_cells = {(r, c) for r in range(rows) for c in range(cols)}

    # Tinh duong di ban dau cho tung candidate den Goal
    candidate_paths = []
    for cand in belief:
        path = find_path_bfs(grid, cand, goal, rows, cols)
        if path:
            candidate_paths.append(path)

    # Buoc 0: Trang thai ban dau
    steps.append(Step(
        step_num=0,
        current=actual_pos,
        frontier=list(belief),
        visited={actual_pos},
        path_so_far=[actual_pos],
        description=(f"[Bat dau] Me cung toi! AI co {len(belief)} vi tri nghi van. "
                     f"Cung di BFS den Goal."),
        extra={
            'belief_size': len(belief),
            'localized': False,
            'phase': 'LOCALIZE',
            'known_cells': all_cells,
            'candidate_paths': candidate_paths
        }
    ))

    MAX_MOVES = 500

    # Di chuyen trong mot vong lap duy nhat cho den khi thuc su cham dich
    while step_num < MAX_MOVES and actual_pos != goal:
        # 1. Chon buoc di tiep theo
        if len(belief) > 1:
            # Giai doan LOCALIZE: Cung di theo candidate tot nhat den Goal
            best_cand = None
            best_path = None
            for cand in belief:
                path = find_path_bfs(grid, cand, goal, rows, cols)
                if path and len(path) >= 2:
                    if best_path is None or len(path) < len(best_path):
                        best_path = path
                        best_cand = cand

            if not best_path:
                direction = 'UP'
                for name, (dr, dc) in DIRECTIONS.items():
                    if any(can_move(grid, cand, dr, dc, rows, cols) for cand in belief):
                        direction = name
                        break
            else:
                next_step = best_path[1]
                move_dr = next_step[0] - best_cand[0]
                move_dc = next_step[1] - best_cand[1]
                direction = 'UP'
                for name, (ddr, ddc) in DIRECTIONS.items():
                    if (ddr, ddc) == (move_dr, move_dc):
                        direction = name
                        break
        else:
            # Giai doan NAVIGATE: Da xac dinh vi tri, di chuyen theo BFS den Goal
            path = find_path_bfs(grid, actual_pos, goal, rows, cols)
            if path and len(path) >= 2:
                next_step = path[1]
                move_dr = next_step[0] - actual_pos[0]
                move_dc = next_step[1] - actual_pos[1]
                direction = 'UP'
                for name, (ddr, ddc) in DIRECTIONS.items():
                    if (ddr, ddc) == (move_dr, move_dc):
                        direction = name
                        break
            else:
                break  # Ket duong di den Goal

        dr, dc = DIRECTIONS[direction]

        # Thuc hien di chuyen thuc te
        new_pos = apply_move(actual_pos, dr, dc, grid, rows, cols)
        actually_moved = (new_pos != actual_pos)
        actual_pos = new_pos
        full_path.append(actual_pos)
        visited_pos.add(actual_pos)

        # Loc Belief State neu van con nhieu hon 1 candidate
        if len(belief) > 1:
            old_size = len(belief)
            belief = filter_belief(belief, dr, dc, actually_moved, grid, rows, cols)
            new_size = len(belief)
            eliminated = old_size - new_size

            if new_size <= 1:
                localized = True
                if new_size == 1:
                    located_at = next(iter(belief))
                    if located_at != actual_pos:
                        belief = {actual_pos}
                else:
                    belief = {actual_pos}
        else:
            belief = {actual_pos}
            new_size = 1
            eliminated = 0
            localized = True

        step_num += 1

        move_result = "di duoc" if actually_moved else "bi chan (tuong)"
        desc = (f"[Buoc {step_num}] Cung di {direction} ({move_result}). "
                f"Belief con {new_size} vi tri.")

        if localized:
            dist_to_goal = abs(actual_pos[0] - goal[0]) + abs(actual_pos[1] - goal[1])
            desc = f"[Buoc {step_num}] BFS dan duong -> {actual_pos}. Con {dist_to_goal} o den Goal."
            if actual_pos == goal:
                desc = f"[Buoc {step_num}] DA DEN GOAL tai {actual_pos}! Tong: {step_num} buoc."

        # Tinh lai candidate paths moi cho buoc hien tai
        candidate_paths = []
        for cand in belief:
            p = find_path_bfs(grid, cand, goal, rows, cols)
            if p:
                candidate_paths.append(p)

        steps.append(Step(
            step_num=step_num,
            current=actual_pos,
            frontier=list(belief),
            visited=set(visited_pos),
            path_so_far=list(full_path),
            description=desc,
            extra={
                'belief_size': new_size,
                'eliminated': eliminated,
                'direction': direction,
                'moved': actually_moved,
                'localized': localized,
                'phase': 'LOCALIZE' if not localized else 'NAVIGATE',
                'known_cells': all_cells,
                'candidate_paths': candidate_paths
            }
        ))

    elapsed = (time.time() - t0) * 1000
    found = (actual_pos == goal)

    return PathResult(
        algo_name='BFS-PO',
        start=start, goal=goal,
        steps=steps,
        path=full_path if found else [],
        total_visited=len(visited_pos),
        found=found,
        elapsed_ms=elapsed
    )
