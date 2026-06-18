# core/game.py — Game State Manager (AI Maze Solver)
"""
Quản lý trạng thái: maze, player, thuật toán, animation.
"""

import random
import tracemalloc
from typing import Optional, Tuple

import config as C
from core.maze import Maze
from generation.maze_generator import generate_maze, find_start_exit, add_extra_passages
from algorithms.base import PathResult, Step
from algorithms import ALGO_RUNNERS


FAST_MEMORY_ESTIMATE = {'SA', 'BFS-PO'}


class PlaybackState:
    IDLE    = 'idle'
    RUNNING = 'running'
    PAUSED  = 'paused'
    DONE    = 'done'


class Game:
    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 99999)
        self._init_maze()

        self.player_pos: Tuple[int,int] = self.maze.start

        self.current_algo:    Optional[str]         = None
        self.result:          Optional[PathResult]  = None
        self.compare_algo:    Optional[str]         = None
        self.compare_result:  Optional[PathResult]  = None
        self.playback_state   = PlaybackState.IDLE
        self.current_step_idx = 0
        self._step_timer      = 0.0
        self.step_delay       = C.ALGO_STEP_NORMAL

        self.message       = "Chọn nhóm và thuật toán → nhấn PLAY"
        self.message_color = C.HUD_TEXT
        self._tick         = 0.0

        self.race_mode = False
        self.compare_step_idx = 0
        self._compare_step_timer = 0.0

    def _init_maze(self):
        grid  = generate_maze(C.COLS, C.ROWS, seed=self.seed)
        grid  = add_extra_passages(grid, C.ROWS, C.COLS, extra=8)
        start, goal = find_start_exit(grid, C.ROWS, C.COLS)
        self.maze = Maze(grid, C.ROWS, C.COLS, start, goal)

    def new_maze(self):
        self.seed = random.randint(0, 99999)
        self._init_maze()
        self.player_pos = self.maze.start
        self.reset_algo()
        self.message = f"Mê cung mới! Seed={self.seed}"
        self.message_color = C.GOAL_COLOR

    def resize_matrix(self, size: int):
        if size == C.GRID_SIZE:
            return
        C.set_grid_size(size)
        self.seed = random.randint(0, 99999)
        self._init_maze()
        self.player_pos = self.maze.start
        self.reset_algo()
        self.message = f"Matrix {size}x{size} | Tile={C.TILE_SIZE}px"
        self.message_color = C.HUD_TITLE

    def run_algorithm(self, algo_name: str):
        if algo_name not in ALGO_RUNNERS:
            self.message = f"Thuật toán '{algo_name}' không tồn tại!"
            return

        self.current_algo     = algo_name
        self.result           = self._execute_algorithm(algo_name)
        self.current_step_idx = 0
        self.playback_state   = PlaybackState.RUNNING
        self._step_timer      = 0.0

        group = C.get_algo_group(algo_name)
        self.message = (f"[{algo_name}] | {group} | "
                        f"Tong {self.result.total_steps} buoc")
        self.message_color = C.get_algo_color(algo_name)

    def run_comparison(self, algo_a: str, algo_b: str = None):
        self.run_algorithm(algo_a)

        self.compare_algo = (
            algo_b if algo_b and algo_b != algo_a and algo_b in ALGO_RUNNERS
            else None
        )

        self.compare_result = None
        self.compare_step_idx = 0
        self._compare_step_timer = 0.0

        if self.compare_algo:
            self.compare_result = self._execute_algorithm(self.compare_algo)

            if self.race_mode:
                self.message = f"RACE MODE: {algo_a} vs {self.compare_algo}"
            else:
                self.message = (
                    f"So sanh {algo_a} vs {self.compare_algo} | "
                    f"A steps={self.result.total_steps}, "
                    f"B steps={self.compare_result.total_steps}"
                )

    def toggle_race_mode(self):
        self.race_mode = not self.race_mode

        if self.race_mode:
            self.compare_step_idx = 0
            self._compare_step_timer = 0.0
            self.message = "Race Mode ON: 2 thuật toán chạy cùng lúc"
            self.message_color = C.START_COLOR
        else:
            self.message = "Race Mode OFF: so sánh số liệu bình thường"
            self.message_color = C.HUD_TEXT

    def _execute_algorithm(self, algo_name: str) -> PathResult:
        runner = ALGO_RUNNERS[algo_name]
        if algo_name in FAST_MEMORY_ESTIMATE:
            result = runner(self.maze.grid,
                            self.maze.start, self.maze.goal,
                            C.ROWS, C.COLS)
            result.memory_kb = self._estimate_memory_kb(result)
            return result

        tracemalloc.start()
        try:
            result = runner(self.maze.grid,
                            self.maze.start, self.maze.goal,
                            C.ROWS, C.COLS)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        result.memory_kb = peak / 1024
        return result

    def _estimate_memory_kb(self, result: PathResult) -> float:
        cells = len(result.path)
        for step in result.steps:
            cells += len(step.frontier) + len(step.visited) + len(step.path_so_far)
        return (len(result.steps) * 256 + cells * 16) / 1024

    def reset_algo(self):
        self.result           = None
        self.current_algo     = None
        self.compare_result   = None
        self.compare_algo     = None
        self.playback_state   = PlaybackState.IDLE
        self.current_step_idx = 0
        self.message          = "Chon nhom va thuat toan -> nhan PLAY"
        self.message_color    = C.HUD_TEXT
        self.compare_step_idx = 0
        self._compare_step_timer = 0.0

    def replay_algo(self):
        if self.current_algo:
            self.run_comparison(self.current_algo, self.compare_algo)

    def step_forward(self):
        if self.result and self.current_step_idx < len(self.result.steps):
            self.current_step_idx += 1
            self._on_step_changed()

    def step_backward(self):
        if self.current_step_idx > 0:
            self.current_step_idx -= 1

    def toggle_pause(self):
        if self.playback_state == PlaybackState.RUNNING:
            self.playback_state = PlaybackState.PAUSED
        elif self.playback_state == PlaybackState.PAUSED:
            self.playback_state = PlaybackState.RUNNING

    def toggle_theme(self):
        name = C.next_theme()
        if self.maze:
            self.maze._tile_surf = self.maze._build_tiles()
        self.message = f"Theme: {name} | Cyber/Dungeon/Neon/Space"
        self.message_color = C.HUD_TITLE

    def toggle_speed(self):
        speeds = [C.ALGO_STEP_FAST, C.ALGO_STEP_NORMAL, C.ALGO_STEP_SLOW]
        labels = ["NHANH", "BÌNH THƯỜNG", "CHẬM"]
        try:
            idx = speeds.index(self.step_delay)
        except ValueError:
            idx = 1
        idx = (idx + 1) % len(speeds)
        self.step_delay    = speeds[idx]
        self.message       = f"Toc do: {labels[idx]}"
        self.message_color = C.HUD_TEXT

    def try_move_player(self, dr: int, dc: int) -> bool:
        nr, nc = self.player_pos[0]+dr, self.player_pos[1]+dc
        if self.maze.is_walkable(nr, nc):
            self.player_pos = (nr, nc)
            if self.player_pos == self.maze.goal:
                self.message       = "Ban da den Goal!"
                self.message_color = C.GOAL_COLOR
            return True
        return False

    def _on_step_changed(self):
        if not self.result:
            return
        if self.current_step_idx >= len(self.result.steps):
            self.playback_state = PlaybackState.DONE
            if self.result.found:
                self.message = (f"[{self.current_algo}] Tim thay! "
                                f"Duong: {self.result.path_length} buoc | "
                                f"Visited: {self.result.total_visited} o | "
                                f"Time: {self.result.elapsed_ms:.1f}ms")
                self.message_color = C.START_COLOR
            else:
                self.message = (f"[{self.current_algo}] Khong tim thay duong! "
                                f"Visited: {self.result.total_visited} o")
                self.message_color = C.VIZ_BACKTRACK

    def update(self, dt: float):
        self._tick += dt
        self.maze.update(dt)

        if self.playback_state == PlaybackState.RUNNING and self.result:
            self._step_timer += dt

            if self._step_timer >= self.step_delay:
                self._step_timer = 0.0

                if self.current_step_idx < len(self.result.steps):
                    self.current_step_idx += 1

            # Race Mode: thuật toán B cũng chạy từng bước
            if self.race_mode and self.compare_result:
                self._compare_step_timer += dt

                if self._compare_step_timer >= self.step_delay:
                    self._compare_step_timer = 0.0

                    if self.compare_step_idx < len(self.compare_result.steps):
                        self.compare_step_idx += 1

            # kết thúc
            a_done = self.current_step_idx >= len(self.result.steps)

            if self.race_mode and self.compare_result:
                b_done = self.compare_step_idx >= len(self.compare_result.steps)
                if a_done and b_done:
                    self._on_step_changed()
            else:
                if a_done:
                    self._on_step_changed()

    @property
    def current_step(self) -> Optional[Step]:
        if not self.result or not self.result.steps:
            return None
        idx = min(self.current_step_idx, len(self.result.steps)-1)
        return self.result.steps[idx] if idx >= 0 else None

    @property
    def progress(self) -> float:
        if not self.result or not self.result.steps:
            return 0.0
        return min(1.0, self.current_step_idx / len(self.result.steps))

    @property
    def compare_current_step(self):
        if not self.compare_result or not self.compare_result.steps:
            return None

        idx = min(self.compare_step_idx, len(self.compare_result.steps) - 1)
        return self.compare_result.steps[idx] if idx >= 0 else None

    @property
    def compare_progress(self) -> float:
        if not self.compare_result or not self.compare_result.steps:
            return 0.0

        return min(1.0, self.compare_step_idx / len(self.compare_result.steps))
