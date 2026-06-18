# algorithms/base.py — Data classes dùng chung cho tất cả thuật toán
"""
Cấu trúc dữ liệu chung để lưu trạng thái từng bước của thuật toán.
Mỗi thuật toán phải trả về PathResult chứa các Step.

Trạng thái bắt đầu (Initial State):
    start, goal, maze grid

Các bước thực hiện (Execution Steps):
    danh sách Step — mỗi Step là snapshot của thuật toán tại 1 thời điểm

Trạng thái kết thúc (Final State):
    path (đường đi), total_visited, found
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional


@dataclass
class Step:
    """Snapshot trạng thái thuật toán tại bước thứ step_num."""
    step_num:    int                              # Bước thứ mấy
    current:     Tuple[int, int]                  # Ô đang được xét
    frontier:    List[Tuple[int, int]]            # Frontier (queue/stack/heap)
    visited:     Set[Tuple[int, int]]             # Tập ô đã duyệt
    path_so_far: List[Tuple[int, int]]            # Đường đến current
    description: str = ""                         # Mô tả bước
    is_backtrack: bool = False                    # True nếu đang quay lui
    extra: dict = field(default_factory=dict)     # Dữ liệu thêm (g, f, v.v.)


@dataclass
class PathResult:
    """Kết quả chạy thuật toán."""
    algo_name:     str
    start:         Tuple[int, int]
    goal:          Tuple[int, int]
    steps:         List[Step]          # Tất cả bước thực hiện
    path:          List[Tuple[int, int]]   # Đường đi cuối cùng ([] nếu không tìm thấy)
    total_visited: int = 0
    found:         bool = False
    elapsed_ms:    float = 0.0
    memory_kb:     float = 0.0

    @property
    def path_length(self) -> int:
        return len(self.path)

    @property
    def path_cost(self) -> int:
        return max(0, len(self.path) - 1)

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    def summary(self) -> str:
        if self.found:
            return (f"Tìm thấy! Đường đi: {self.path_length} bước | "
                    f"Đã duyệt: {self.total_visited} ô | "
                    f"Bước thuật toán: {self.total_steps}")
        return f"Không tìm thấy đường đi. Đã duyệt: {self.total_visited} ô"


def reconstruct_path(parent: dict, start: Tuple[int,int],
                     goal: Tuple[int,int]) -> List[Tuple[int,int]]:
    """Truy vết đường đi từ parent map."""
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    if path and path[0] == start:
        return path
    return []
