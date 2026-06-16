# algorithms/__init__.py — Registry trung tâm cho tất cả thuật toán
"""
Cấu trúc thư mục thuật toán (có thể mở rộng):

  algorithms/
    uninformed/          <- Nhom 1: Uninformed Search
      dfs.py
      __init__.py
    informed/            <- Nhom 2: Informed Search
      astar.py
      __init__.py
    local/               <- Nhom 3: Local Search
      steepest_hc.py
      __init__.py
    complex_env/         <- Nhom 4: Complex Environment
      bfs_partial.py
      __init__.py
    csp/                 <- Nhom 5: CSP
      backtracking.py
      __init__.py
    base.py              <- Data types chung (Step, PathResult)
    __init__.py          <- File nay: ALGO_RUNNERS registry

De them thuat toan moi vao nhom X:
  1. Tao file algorithms/<nhom>/ten_algo.py
  2. Import va them vao ALGO_RUNNERS ben duoi
  3. Them vao config.ALGO_GROUPS[nhomX]['algorithms']
"""

from algorithms.uninformed.dfs      import run_dfs
from algorithms.informed.astar      import run_astar
from algorithms.local.steepest_hc   import run_steepest_hc
from algorithms.complex_env.bfs_partial import run_bfs_partial
from algorithms.csp.backtracking    import run_backtracking

# Map: key (khop voi config.ALGO_GROUPS) -> ham chay
ALGO_RUNNERS = {
    'DFS':         run_dfs,
    'A*':          run_astar,
    'Steepest HC': run_steepest_hc,
    'BFS-PO':      run_bfs_partial,
    'Backtrack':   run_backtracking,
}
