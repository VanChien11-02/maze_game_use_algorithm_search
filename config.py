# config.py — Hằng số toàn cục (AI Maze Solver)

# ── Cửa sổ & Lưới ──────────────────────────────────────────
import os

GRID_OPTIONS = [15, 20, 30, 40]
GRID_SIZE  = 30
COLS       = GRID_SIZE
ROWS       = GRID_SIZE
MAP_W      = 720
MAP_H      = 720
TILE_SIZE  = MAP_W // GRID_SIZE
HUD_W      = 580
SCREEN_W   = MAP_W + HUD_W      # 1300
SCREEN_H   = MAP_H              # 720
FPS        = 60
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(BASE_DIR, 'assets', 'hcmute_logo.png')
SHOW_ALGO_TRACE = False
SHOW_ROUTE_LINE = True

DIFFICULTY_PRESETS = {
    'Classic':  {'extra_ratio': 0.015, 'extra_min': 5,  'braid_ratio': 0.10},
    'Balanced': {'extra_ratio': 0.040, 'extra_min': 8,  'braid_ratio': 0.35},
    'Open':     {'extra_ratio': 0.070, 'extra_min': 12, 'braid_ratio': 0.55},
}
DIFFICULTY_NAMES = list(DIFFICULTY_PRESETS.keys())
CURRENT_DIFFICULTY_IDX = DIFFICULTY_NAMES.index('Balanced')


def set_grid_size(size: int):
    """Doi kich thuoc ma tran nhung giu nguyen viewport 720x720."""
    global GRID_SIZE, COLS, ROWS, TILE_SIZE
    if size not in GRID_OPTIONS:
        return
    GRID_SIZE = size
    COLS = size
    ROWS = size
    TILE_SIZE = MAP_W // size


def current_difficulty_name() -> str:
    return DIFFICULTY_NAMES[CURRENT_DIFFICULTY_IDX % len(DIFFICULTY_NAMES)]


def set_difficulty(name: str):
    global CURRENT_DIFFICULTY_IDX
    if name in DIFFICULTY_NAMES:
        CURRENT_DIFFICULTY_IDX = DIFFICULTY_NAMES.index(name)


def current_difficulty_settings() -> dict:
    return DIFFICULTY_PRESETS[current_difficulty_name()]

# Tốc độ animation
ALGO_STEP_FAST   = 0.03
ALGO_STEP_NORMAL = 0.08
ALGO_STEP_SLOW   = 0.22

# ── Màu sắc ────────────────────────────────────────────────
BLACK         = (0,   0,   0)
WHITE         = (255, 255, 255)
BG_COLOR      = (5,   9,  18)

WALL_COLOR    = (48,  52,  58)
WALL_EDGE     = (82,  88,  96)
WALL_LIGHT    = (112, 118, 126)
WALL_SHADOW   = (22,  24,  28)
WALL_MORTAR   = (66,  70,  76)
FLOOR_COLOR   = (126, 108,  82)
FLOOR_DOT     = (178, 154, 112)
FLOOR_EDGE    = (96,  80,  60)
FLOOR_LIGHT   = (156, 136, 100)
FLOOR_HILITE  = (140, 120,  88)
UNKNOWN_COLOR = (4,   6,  12)   # Ô chưa nhìn thấy (BFS-PO)

START_COLOR   = (50,  220, 120)
START_GLOW    = (80,  255, 160)
GOAL_COLOR    = (255, 180,   0)
GOAL_GLOW     = (255, 220,  80)
PLAYER_COLOR  = (90,  210, 255)
PLAYER_OUT    = (210, 245, 255)
MONSTER_COLOR = (255,  65, 110)
MONSTER_GLOW  = (255, 120, 185)

# Algorithm visualization
VIZ_VISITED   = (0,   130, 255)
VIZ_FRONTIER  = (255, 145,  35)
VIZ_CURRENT   = (255, 245,  95)
VIZ_PATH      = (255, 224, 145)
VIZ_PATH_DARK = (118,  82,  32)
ROUTE_CORE    = (255, 248, 215)
ROUTE_NODE_DARK = (72, 48, 18)
VIZ_BACKTRACK = (255,  75,  90)
VIZ_STUCK     = (255, 100,  50)   # Steepest HC bị kẹt

# HUD
HUD_BG        = (8,   12,  24)
HUD_BORDER    = (68,  92, 155)
HUD_TEXT      = (235, 242, 255)   # Chu sang hon, de doc ro hon
HUD_MUTED     = (160, 178, 220)
HUD_DIM       = (100, 118, 160)
HUD_TITLE     = (95, 225, 255)    # Tieu de neon
HUD_ACCENT    = (0, 255, 210)
HUD_WARN      = (255, 190, 65)
HUD_DANGER    = (255, 90, 115)
GOLD_COLOR    = (255, 225,  80)   # Vang sang

# Combobox
CB_BG         = (20,  22,  40)
CB_BORDER     = (60,  80, 140)
CB_HOVER      = (35,  40,  70)
CB_SELECT     = (50,  80, 160)
CB_TEXT       = (210, 220, 255)
CB_ARROW      = (120, 160, 255)

# Play button
PLAY_BG       = (0,   105,  82)
PLAY_HOVER    = (0,   155, 115)
PLAY_BORDER   = (0,   255, 185)

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
            'BFS': 'Breadth-First Search',
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
            'Greedy': 'Greedy Best-First Search',
            # Thêm: 'IDA*': 'Iterative Deepening A*',
        },
    },
    'Local Search': {
        'vi_name': 'Tìm kiếm cục bộ',
        'color':   (180, 120,  40),
        'algorithms': {
            'Steepest HC': 'Steepest Hill Climbing',
            'SA': 'Simulated Annealing',
            # Thêm: 'RHC': 'Random Restart Hill Climbing',
        },
    },
    'Complex Environment': {
        'vi_name': 'Môi trường phức tạp',
        'color':   ( 40, 160, 170),
        'algorithms': {
            'BFS-PO': 'BFS Partially Observable',
            'BS-DFS': 'Belief-State DFS',
            # Thêm: 'Online-DFS': 'Online DFS Agent',
        },
    },
    'CSP': {
        'vi_name': 'Thỏa mãn ràng buộc',
        'color':   (130,  60, 180),
        'algorithms': {
            'Backtrack': 'Backtracking Search',
            'Min-Conflicts': 'Min-Conflicts',
            # Thêm: 'AC3': 'Arc Consistency (AC-3)',
            # Thêm: 'FC':  'Forward Checking',
        },
    },
    'Adversarial Search': {
        'vi_name': 'Tìm kiếm đối kháng',
        'color':   (225,  80, 115),
        'algorithms': {
            'Alpha-Beta': 'Alpha-Beta Pruning Monster',
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

# ── Theme system: nhấn H để đổi phong cách maze ─────────────
THEME_NAMES = ['Stone Maze', 'Dungeon', 'Neon', 'Space']
CURRENT_THEME_IDX = 0
_THEMES = {
    'Stone Maze': {
        'BG_COLOR': (5, 9, 18), 'WALL_COLOR': (48,52,58), 'WALL_LIGHT': (112,118,126),
        'WALL_SHADOW': (22,24,28), 'WALL_MORTAR': (66,70,76), 'FLOOR_COLOR': (126,108,82),
        'FLOOR_DOT': (178,154,112), 'FLOOR_EDGE': (96,80,60), 'FLOOR_LIGHT': (156,136,100),
        'FLOOR_HILITE': (140,120,88), 'START_COLOR': (50,220,120), 'START_GLOW': (80,255,160),
        'GOAL_COLOR': (255,180,0), 'GOAL_GLOW': (255,220,80), 'VIZ_VISITED': (0,130,255),
        'VIZ_FRONTIER': (255,145,35), 'VIZ_PATH': (255,224,145), 'VIZ_PATH_DARK': (118,82,32),
        'ROUTE_CORE': (255,248,215), 'ROUTE_NODE_DARK': (72,48,18), 'HUD_TITLE': (95,225,255),
        'PLAY_BG': (0,105,82), 'PLAY_HOVER': (0,155,115), 'PLAY_BORDER': (0,255,185)
    },
    'Dungeon': {
        'BG_COLOR': (15, 10, 9), 'WALL_COLOR': (75,61,54), 'WALL_LIGHT': (150,121,91),
        'WALL_SHADOW': (20,14,12), 'WALL_MORTAR': (42,34,32), 'FLOOR_COLOR': (32,24,22),
        'FLOOR_DOT': (108,84,62), 'FLOOR_EDGE': (72,54,44), 'FLOOR_LIGHT': (95,73,56),
        'FLOOR_HILITE': (54,42,35), 'START_COLOR': (60,205,100), 'START_GLOW': (120,255,130),
        'GOAL_COLOR': (255,198,61), 'GOAL_GLOW': (255,231,120), 'VIZ_VISITED': (66,145,240),
        'VIZ_FRONTIER': (255,133,62), 'VIZ_PATH': (85,255,150), 'HUD_TITLE': (255,190,95),
        'PLAY_BG': (112,68,34), 'PLAY_HOVER': (155,88,40), 'PLAY_BORDER': (255,180,84)
    },
    'Neon': {
        'BG_COLOR': (8, 4, 22), 'WALL_COLOR': (50,26,92), 'WALL_LIGHT': (210,95,255),
        'WALL_SHADOW': (16,5,34), 'WALL_MORTAR': (94,44,150), 'FLOOR_COLOR': (12,8,36),
        'FLOOR_DOT': (74,230,255), 'FLOOR_EDGE': (72,33,125), 'FLOOR_LIGHT': (110,55,180),
        'FLOOR_HILITE': (38,24,82), 'START_COLOR': (0,255,165), 'START_GLOW': (60,255,210),
        'GOAL_COLOR': (255,72,210), 'GOAL_GLOW': (255,150,235), 'VIZ_VISITED': (58,125,255),
        'VIZ_FRONTIER': (255,75,200), 'VIZ_PATH': (0,255,240), 'HUD_TITLE': (225,95,255),
        'PLAY_BG': (105,0,105), 'PLAY_HOVER': (160,0,155), 'PLAY_BORDER': (255,85,240)
    },
    'Space': {
        'BG_COLOR': (2, 4, 14), 'WALL_COLOR': (18,30,64), 'WALL_LIGHT': (92,140,255),
        'WALL_SHADOW': (2,5,18), 'WALL_MORTAR': (32,50,102), 'FLOOR_COLOR': (4,7,20),
        'FLOOR_DOT': (175,210,255), 'FLOOR_EDGE': (14,25,55), 'FLOOR_LIGHT': (24,44,86),
        'FLOOR_HILITE': (10,18,38), 'START_COLOR': (87,255,245), 'START_GLOW': (130,255,255),
        'GOAL_COLOR': (255,236,120), 'GOAL_GLOW': (255,255,180), 'VIZ_VISITED': (95,175,255),
        'VIZ_FRONTIER': (255,210,92), 'VIZ_PATH': (162,120,255), 'HUD_TITLE': (135,190,255),
        'PLAY_BG': (24,70,132), 'PLAY_HOVER': (36,105,190), 'PLAY_BORDER': (115,190,255)
    },
}

def current_theme_name() -> str:
    return THEME_NAMES[CURRENT_THEME_IDX % len(THEME_NAMES)]

def apply_theme(name: str = None) -> str:
    global CURRENT_THEME_IDX
    if name in THEME_NAMES:
        CURRENT_THEME_IDX = THEME_NAMES.index(name)
    theme = _THEMES[current_theme_name()]
    globals().update(theme)
    return current_theme_name()

def next_theme() -> str:
    global CURRENT_THEME_IDX
    CURRENT_THEME_IDX = (CURRENT_THEME_IDX + 1) % len(THEME_NAMES)
    return apply_theme()
