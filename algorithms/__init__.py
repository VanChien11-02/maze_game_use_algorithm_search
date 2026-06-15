# algorithms/__init__.py — Package thuật toán AI Maze Solver
"""
5 Thuật toán AI — Cùng giải bài toán tìm đường Start → Goal (30×30)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nhóm 1 – Uninformed Search  : DFS          (dfs.py)
Nhóm 2 – Informed Search    : A*           (astar.py)
Nhóm 3 – Local Search       : Steepest HC  (steepest_hc.py)
Nhóm 4 – Complex Environment: BFS-PO       (bfs_partial.py)
Nhóm 5 – CSP                : Backtracking (backtracking.py)

Để thêm thuật toán mới vào nhóm X:
  1. Tạo file algorithms/ten_algo.py với hàm run_ten_algo(grid, start, goal, rows, cols)
  2. Import và thêm vào ALGO_RUNNERS bên dưới
  3. Thêm tên vào config.ALGO_GROUPS[nhomX]['algorithms']
"""

from algorithms.dfs          import run_dfs
from algorithms.astar        import run_astar
from algorithms.steepest_hc  import run_steepest_hc
from algorithms.bfs_partial  import run_bfs_partial
from algorithms.backtracking import run_backtracking

# Map: key (dùng trong config.ALGO_GROUPS) → hàm chạy
ALGO_RUNNERS = {
    'DFS':         run_dfs,
    'A*':          run_astar,
    'Steepest HC': run_steepest_hc,
    'BFS-PO':      run_bfs_partial,
    'Backtrack':   run_backtracking,
}
