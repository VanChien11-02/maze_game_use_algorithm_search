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
from algorithms.uninformed.bfs      import run_bfs
from algorithms.informed.astar      import run_astar
from algorithms.informed.greedy     import run_greedy
from algorithms.local.steepest_hc   import run_steepest_hc
from algorithms.local.simulated_annealing import run_simulated_annealing
from algorithms.complex_env.bfs_partial import run_bfs_partial
from algorithms.complex_env.belief_dfs import run_belief_dfs
from algorithms.csp.backtracking    import run_backtracking
from algorithms.csp.min_conflicts   import run_min_conflicts
from algorithms.adversarial.alpha_beta import run_alpha_beta

# Map: key (khop voi config.ALGO_GROUPS) -> ham chay
ALGO_RUNNERS = {
    'BFS':         run_bfs,
    'DFS':         run_dfs,
    'A*':          run_astar,
    'Greedy':      run_greedy,
    'Steepest HC': run_steepest_hc,
    'SA':          run_simulated_annealing,
    'BFS-PO':      run_bfs_partial,
    'BS-DFS':      run_belief_dfs,
    'Backtrack':   run_backtracking,
    'Min-Conflicts': run_min_conflicts,
    'Alpha-Beta':  run_alpha_beta,
}
