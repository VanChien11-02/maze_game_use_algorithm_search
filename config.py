# config.py — Hằng số toàn cục (AI Maze Solver)

# ── Cửa sổ & Lưới ──────────────────────────────────────────
TILE_SIZE  = 24
COLS       = 30
ROWS       = 30
MAP_W      = COLS * TILE_SIZE   # 720
MAP_H      = ROWS * TILE_SIZE   # 720
HUD_W      = 304
SCREEN_W   = MAP_W + HUD_W      # 1024
SCREEN_H   = MAP_H              # 720
FPS        = 60

# Tốc độ animation
ALGO_STEP_FAST   = 0.03
ALGO_STEP_NORMAL = 0.08
ALGO_STEP_SLOW   = 0.22

# ── Màu sắc ────────────────────────────────────────────────
BLACK         = (0,   0,   0)
WHITE         = (255, 255, 255)
BG_COLOR      = (8,   8,  18)

WALL_COLOR    = (30,  35,  55)
WALL_EDGE     = (50,  60,  90)
FLOOR_COLOR   = (18,  18,  30)
FLOOR_DOT     = (28,  28,  45)
UNKNOWN_COLOR = (10,  10,  18)   # Ô chưa nhìn thấy (BFS-PO)

START_COLOR   = (50,  220, 120)
START_GLOW    = (80,  255, 160)
GOAL_COLOR    = (255, 180,   0)
GOAL_GLOW     = (255, 220,  80)
PLAYER_COLOR  = (100, 200, 255)
PLAYER_OUT    = (160, 230, 255)

# Algorithm visualization
VIZ_VISITED   = (40,  80,  140)
VIZ_FRONTIER  = (200, 100,  50)
VIZ_CURRENT   = (255, 255, 100)
VIZ_PATH      = (100, 255, 200)
VIZ_BACKTRACK = (180,  50,  50)
VIZ_STUCK     = (255, 100,  50)   # Steepest HC bị kẹt

# HUD
HUD_BG        = (12,  12,  24)
HUD_BORDER    = (55,  68, 110)
HUD_TEXT      = (215, 225, 255)   # Sang hon de doc ro hon
HUD_TITLE     = (130, 190, 255)   # Tieu de noi bat
GOLD_COLOR    = (255, 215,  65)   # Vang sang

# Combobox
CB_BG         = (20,  22,  40)
CB_BORDER     = (60,  80, 140)
CB_HOVER      = (35,  40,  70)
CB_SELECT     = (50,  80, 160)
CB_TEXT       = (210, 220, 255)
CB_ARROW      = (120, 160, 255)

# Play button
PLAY_BG       = (30,  90,  50)
PLAY_HOVER    = (50, 140,  80)
PLAY_BORDER   = (80, 200, 120)

# Tile values
TILE_WALL  = 0
TILE_FLOOR = 1

# ── CẤU TRÚC NHÓM & THUẬT TOÁN ─────────────────────────────
# Dễ mở rộng: thêm thuật toán vào 'algorithms' của mỗi nhóm,
# tạo file .py tương ứng, import vào algorithms/__init__.py
ALGO_GROUPS = {
    'Uninformed Search': {
        'vi_name': 'Tìm kiếm mù',
        'color':   (180,  60,  60),
        'algorithms': {
            'DFS': 'Depth-First Search',
            # Thêm: 'UCS': 'Uniform Cost Search',
            # Thêm: 'IDDFS': 'Iterative Deepening DFS',
        },
    },
    'Informed Search': {
        'vi_name': 'Tìm kiếm kinh nghiệm',
        'color':   ( 50, 130, 210),
        'algorithms': {
            'A*': 'A* Search',
            # Thêm: 'IDA*': 'Iterative Deepening A*',
            # Thêm: 'GBFS': 'Greedy Best-First Search',
        },
    },
    'Local Search': {
        'vi_name': 'Tìm kiếm cục bộ',
        'color':   (180, 120,  40),
        'algorithms': {
            'Steepest HC': 'Steepest Hill Climbing',
            # Thêm: 'SA':  'Simulated Annealing',
            # Thêm: 'RHC': 'Random Restart Hill Climbing',
        },
    },
    'Complex Environment': {
        'vi_name': 'Môi trường phức tạp',
        'color':   ( 40, 160, 170),
        'algorithms': {
            'BFS-PO': 'BFS Partially Observable',
            # Thêm: 'Online-DFS': 'Online DFS Agent',
        },
    },
    'CSP': {
        'vi_name': 'Thỏa mãn ràng buộc',
        'color':   (130,  60, 180),
        'algorithms': {
            'Backtrack': 'Backtracking Search',
            # Thêm: 'AC3': 'Arc Consistency (AC-3)',
            # Thêm: 'FC':  'Forward Checking',
        },
    },
    'Adversarial Search': {
        'vi_name': 'Tìm kiếm đối kháng',
        'color':   (210,  50, 100),
        'algorithms': {
            'Minimax': 'Minimax Algorithm',
        },
    },
}

# Danh sách nhóm (giữ thứ tự)
GROUP_NAMES = list(ALGO_GROUPS.keys())


def get_algo_color(algo_name: str) -> tuple:
    """Lấy màu của thuật toán theo nhóm."""
    for info in ALGO_GROUPS.values():
        if algo_name in info['algorithms']:
            return info['color']
    return (100, 100, 100)


def get_algo_group(algo_name: str) -> str:
    """Lấy tên nhóm của thuật toán."""
    for g, info in ALGO_GROUPS.items():
        if algo_name in info['algorithms']:
            return g
    return ''
