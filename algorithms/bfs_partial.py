# algorithms/bfs_partial.py — Nhóm 4: Complex Environment — BFS Partially Observable
"""
BFS Partially Observable — BFS trong môi trường quan sát một phần
══════════════════════════════════════════════════════════════════
Nhóm: Searching in Complex Environments (Môi trường phức tạp)
Bài toán: Tìm đường Start→Goal khi agent CHỈ NHÌN THẤY
          các ô trong bán kính VISIBILITY_RADIUS xung quanh vị trí hiện tại

Trạng thái bắt đầu:
    - Vị trí: Start (r, c)
    - Bản đồ đã biết (known): chỉ những ô trong tầm nhìn của Start
    - Tầm nhìn: bán kính = VISIBILITY_RADIUS ô (Manhattan distance)
    - Fog of War: các ô ngoài tầm nhìn vẽ màu tối

Các bước thực hiện:
    1. Cập nhật known_map từ vị trí hiện tại (reveal cells)
    2. Nếu Goal đã thấy:
       → BFS trên known từ vị trí hiện tại đến Goal
       → Di chuyển từng ô theo đường BFS
    3. Nếu Goal chưa thấy:
       → BFS tìm "frontier cell" (ô known kề với unknown)
       → Di chuyển đến đó để khám phá
    4. Lặp đến Goal hoặc đã khám phá hết

Trạng thái kết thúc:
    - Found: đến Goal (đường dài hơn optimal vì thiếu thông tin)
    - Not found: không thể khám phá thêm

Đặc điểm:
    - FOG OF WAR: ô tối = chưa biết, ô sáng = đã biết
    - Path dài hơn BFS vì phải khám phá trong mù
    - Radius nhỏ → khám phá nhiều hơn, path dài hơn
"""

import time
from collections import deque
from typing import List, Tuple, Set, Optional
from algorithms.base import Step, PathResult, reconstruct_path


DIRECTIONS        = [(-1,0),(1,0),(0,-1),(0,1)]
VISIBILITY_RADIUS = 5    # Tầm nhìn (Manhattan radius)


def manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def reveal_cells(pos: Tuple[int,int], grid: List[List[int]],
                 rows: int, cols: int,
                 known: Set[Tuple[int,int]]) -> int:
    """Thêm tất cả ô trong bán kính vào known. Trả về số ô mới reveal."""
    r, c  = pos
    count = 0
    for dr in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS+1):
        for dc in range(-VISIBILITY_RADIUS, VISIBILITY_RADIUS+1):
            if abs(dr)+abs(dc) <= VISIBILITY_RADIUS:
                nr, nc = r+dr, c+dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    cell = (nr, nc)
                    if cell not in known:
                        known.add(cell)
                        count += 1
    return count


def bfs_on_known(src: Tuple[int,int], dst: Tuple[int,int],
                 grid: List[List[int]], known: Set[Tuple[int,int]],
                 rows: int, cols: int) -> List[Tuple[int,int]]:
    """BFS chỉ đi trên ô đã biết và là sàn (!=0)."""
    if src == dst:
        return [src]
    queue   = deque([src])
    parent  = {src: None}
    visited = {src}
    while queue:
        cur = queue.popleft()
        if cur == dst:
            return reconstruct_path(parent, src, dst)
        r, c = cur
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            npos = (nr, nc)
            if (npos in known and grid[nr][nc] != 0 and npos not in visited):
                visited.add(npos)
                parent[npos] = cur
                queue.append(npos)
    return []


def find_frontier_target(current: Tuple[int,int],
                          grid: List[List[int]],
                          known: Set[Tuple[int,int]],
                          rows: int, cols: int
                          ) -> Optional[Tuple[int,int]]:
    """
    BFS trên known để tìm ô known gần nhất kề với ô CHƯA BIẾT.
    """
    queue   = deque([current])
    vis_bfs = {current}
    while queue:
        pos = queue.popleft()
        r, c = pos
        # Pos kề với ô chưa biết?
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in known:
                return pos
        # Tiếp tục BFS trên known floor
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            npos = (nr, nc)
            if (npos in known and grid[nr][nc] != 0 and npos not in vis_bfs):
                vis_bfs.add(npos)
                queue.append(npos)
    return None


def run_bfs_partial(grid: List[List[int]],
                    start: Tuple[int,int],
                    goal: Tuple[int,int],
                    rows: int, cols: int) -> PathResult:
    """
    BFS Partially Observable: agent di chuyển từng ô,
    mở rộng tầm nhìn khi đến ô mới.
    """
    t0 = time.time()
    steps: List[Step] = []
    step_num = 0

    known: Set[Tuple[int,int]] = set()
    current    = start
    full_path  = [start]
    visited_pos = {start}

    # Reveal xung quanh start
    reveal_cells(start, grid, rows, cols, known)
    goal_visible = goal in known

    steps.append(Step(
        step_num=0,
        current=start,
        frontier=list(known),
        visited={start},
        path_so_far=[start],
        description=(f"[Bắt đầu] Vị trí: {start} | "
                     f"Tầm nhìn R={VISIBILITY_RADIUS} | "
                     f"Nhìn thấy {len(known)} ô | "
                     f"Goal {'đã thấy!' if goal_visible else 'chưa thấy (fog)'}"),
        extra={'known_count': len(known), 'goal_visible': goal_visible,
               'radius': VISIBILITY_RADIUS,
               'known_cells': set(known)}
    ))

    MAX_MOVES = 8000
    for _ in range(MAX_MOVES):
        if current == goal:
            break

        goal_visible = goal in known

        if goal_visible:
            # BFS đến goal trên known map
            sub_path = bfs_on_known(current, goal, grid, known, rows, cols)
            if sub_path and len(sub_path) >= 2:
                # Di chuyển theo đường BFS đến Goal
                for next_pos in sub_path[1:]:
                    if current == goal:
                        break
                    current = next_pos
                    full_path.append(current)
                    visited_pos.add(current)
                    new_cnt = reveal_cells(current, grid, rows, cols, known)
                    step_num += 1
                    steps.append(Step(
                        step_num=step_num,
                        current=current,
                        frontier=list(known - visited_pos),
                        visited=set(visited_pos),
                        path_so_far=list(full_path),
                        description=(f"[Bước {step_num}] Goal visible → BFS → {current} | "
                                     f"Biết: {len(known)} ô | Mới: {new_cnt}"),
                        extra={'known_count': len(known), 'goal_visible': True,
                               'known_cells': set(known)}
                    ))
            else:
                # Goal visible nhưng chưa có đường known đến đó
                # → Tiếp tục khám phá frontier gần goal nhất
                target = find_frontier_target(current, grid, known, rows, cols)
                if target is None:
                    break
                sub_path2 = bfs_on_known(current, target, grid, known, rows, cols)
                if not sub_path2 or len(sub_path2) < 2:
                    break
                next_pos = sub_path2[1]
                current  = next_pos
                full_path.append(current)
                visited_pos.add(current)
                new_cnt = reveal_cells(current, grid, rows, cols, known)
                step_num += 1
                goal_now = goal in known
                steps.append(Step(
                    step_num=step_num,
                    current=current,
                    frontier=list(known - visited_pos),
                    visited=set(visited_pos),
                    path_so_far=list(full_path),
                    description=(f"[Bước {step_num}] Goal thấy nhưng chưa thể đến! → "
                                 f"Tiếp tục khám phá → {current} | "
                                 f"Biết: {len(known)} ô"),
                    extra={'known_count': len(known), 'goal_visible': goal_now,
                           'known_cells': set(known)}
                ))

        else:
            # Tìm frontier cell để khám phá
            target = find_frontier_target(current, grid, known, rows, cols)
            if target is None:
                # Đã biết toàn bộ connected component → không còn gì để khám phá
                break
            sub_path = bfs_on_known(current, target, grid, known, rows, cols)
            if not sub_path or len(sub_path) < 2:
                break
            # Di chuyển từng bước đến frontier target
            next_pos = sub_path[1]
            current  = next_pos
            full_path.append(current)
            visited_pos.add(current)
            new_cnt = reveal_cells(current, grid, rows, cols, known)
            step_num += 1
            goal_now = goal in known
            steps.append(Step(
                step_num=step_num,
                current=current,
                frontier=list(known - visited_pos),
                visited=set(visited_pos),
                path_so_far=list(full_path),
                description=(f"[Bước {step_num}] Khám phá → {current} | "
                             f"Biết: {len(known)} ô | Mới: {new_cnt} | "
                             f"Goal {'THẤY RỒI!' if goal_now else 'vẫn ẩn'}"),
                extra={'known_count': len(known), 'goal_visible': goal_now,
                       'known_cells': set(known)}
            ))

    elapsed = (time.time() - t0) * 1000
    found   = (current == goal)

    return PathResult(
        algo_name='BFS-PO',
        start=start, goal=goal,
        steps=steps,
        path=full_path if found else [],
        total_visited=len(visited_pos),
        found=found,
        elapsed_ms=elapsed
    )
