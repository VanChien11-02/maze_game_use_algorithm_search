# core/maze.py — Lưới mê cung 30×30 và rendering
"""
Maze: quản lý lưới 2D, vẽ tường/sàn, Start và Goal.
Hỗ trợ:
  - Algorithm visualization overlay (visited / frontier / path)
  - Fog-of-war cho BFS Partially Observable (known_cells)
  - Player sprite
"""

import pygame
import math
from typing import List, Tuple, Set
import config as C
from algorithms.base import Step, PathResult


class Maze:
    def __init__(self, grid: List[List[int]], rows: int, cols: int,
                 start: Tuple[int,int], goal: Tuple[int,int]):
        self.grid  = grid
        self.rows  = rows
        self.cols  = cols
        self.start = start
        self.goal  = goal
        self._tick = 0.0
        self._tile_surf = self._build_tiles()
        self._font_marker = None   # lazy init

    def _build_tiles(self):
        ts   = C.TILE_SIZE
        wall = pygame.Surface((ts, ts))
        wall.fill(C.WALL_COLOR)
        pygame.draw.rect(wall, C.WALL_EDGE, (0, 0, ts, ts), 1)
        pygame.draw.line(wall, (40, 48, 72), (1, ts-2), (ts-2, ts-2))
        pygame.draw.line(wall, (40, 48, 72), (ts-2, 1), (ts-2, ts-2))

        floor = pygame.Surface((ts, ts))
        floor.fill(C.FLOOR_COLOR)
        for dr in [ts//4, 3*ts//4]:
            for dc in [ts//4, 3*ts//4]:
                pygame.draw.circle(floor, C.FLOOR_DOT, (dc, dr), 1)

        return {'wall': wall, 'floor': floor}

    def _get_marker_font(self):
        if self._font_marker is None:
            try:
                self._font_marker = pygame.font.SysFont('Arial', 11, bold=True)
            except Exception:
                self._font_marker = pygame.font.Font(None, 13)
        return self._font_marker

    def is_walkable(self, r: int, c: int) -> bool:
        return (0 <= r < self.rows and 0 <= c < self.cols
                and self.grid[r][c] != 0)

    def update(self, dt: float):
        self._tick += dt

    def draw(self, surface: pygame.Surface,
             result: PathResult = None,
             current_step: int = 0,
             player_pos: Tuple[int,int] = None,
             known_cells: Set[Tuple[int,int]] = None):
        """Vẽ mê cung + visualization overlay."""
        ts = C.TILE_SIZE

        # 1. Tiles (fog-of-war nếu có known_cells)
        for r in range(self.rows):
            for c in range(self.cols):
                px, py = c*ts, r*ts
                if known_cells is not None and (r, c) not in known_cells:
                    pygame.draw.rect(surface, C.UNKNOWN_COLOR, (px, py, ts, ts))
                else:
                    key = 'wall' if self.grid[r][c] == 0 else 'floor'
                    surface.blit(self._tile_surf[key], (px, py))

        # 2. Algorithm visualization overlay
        if result and result.steps and current_step > 0:
            step_idx = min(current_step - 1, len(result.steps) - 1)
            self._draw_viz(surface, result.steps[step_idx], result, current_step, ts)

        # 3. Start & Goal markers
        self._draw_start_goal(surface, ts)

        # 4. Player sprite
        if player_pos:
            self._draw_player(surface, player_pos, ts)

    # ── Visualization overlay ────────────────────────────────

    def _draw_viz(self, surface: pygame.Surface, step: Step,
                  result: PathResult, current_step: int, ts: int):
        is_done = (current_step >= len(result.steps))

        # Visited — xanh navy
        for pos in step.visited:
            if pos in (self.start, self.goal): continue
            r, c = pos
            s = pygame.Surface((ts, ts), pygame.SRCALPHA)
            s.fill((*C.VIZ_VISITED, 150))
            surface.blit(s, (c*ts, r*ts))

        # Frontier — cam
        for pos in step.frontier:
            if pos in (self.start, self.goal): continue
            r, c = pos
            s = pygame.Surface((ts, ts), pygame.SRCALPHA)
            s.fill((*C.VIZ_FRONTIER, 170))
            surface.blit(s, (c*ts, r*ts))

        # Path so far
        if step.path_so_far:
            color = C.VIZ_BACKTRACK if step.is_backtrack else C.VIZ_PATH
            alpha = 80 if step.is_backtrack else 130
            for pos in step.path_so_far:
                if pos in (self.start, self.goal): continue
                r, c = pos
                s = pygame.Surface((ts, ts), pygame.SRCALPHA)
                s.fill((*color, alpha))
                surface.blit(s, (c*ts, r*ts))

        # Current cell — vàng sáng
        cur = step.current
        if cur and cur not in (self.start, self.goal):
            r, c = cur
            s = pygame.Surface((ts, ts), pygame.SRCALPHA)
            s.fill((*C.VIZ_CURRENT, 220))
            surface.blit(s, (c*ts, r*ts))
            pygame.draw.rect(surface, C.WHITE, (c*ts, r*ts, ts, ts), 2)

        # Final path (hoàn tất)
        if is_done and result.path:
            for pos in result.path:
                if pos in (self.start, self.goal): continue
                r, c = pos
                s = pygame.Surface((ts, ts), pygame.SRCALPHA)
                s.fill((*C.VIZ_PATH, 210))
                surface.blit(s, (c*ts, r*ts))
            pts = [(p[1]*ts + ts//2, p[0]*ts + ts//2) for p in result.path]
            if len(pts) >= 2:
                pygame.draw.lines(surface, C.VIZ_PATH, False, pts, 2)

    # ── Start / Goal ─────────────────────────────────────────

    def _draw_start_goal(self, surface: pygame.Surface, ts: int):
        glow_a = int(150 + math.sin(self._tick * 3) * 50)
        font   = self._get_marker_font()

        # START
        sr, sc = self.start
        sx, sy = sc*ts + ts//2, sr*ts + ts//2
        gs = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*C.START_GLOW, min(255, glow_a)), (ts//2, ts//2), ts//2-1)
        surface.blit(gs, (sc*ts, sr*ts))
        pygame.draw.circle(surface, C.START_COLOR, (sx, sy), ts//2-4)
        pygame.draw.circle(surface, C.WHITE, (sx, sy), ts//2-4, 2)
        lbl = font.render('S', True, C.WHITE)
        surface.blit(lbl, (sx - lbl.get_width()//2, sy - lbl.get_height()//2))

        # GOAL
        gr, gc = self.goal
        gx, gy = gc*ts + ts//2, gr*ts + ts//2
        gg = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(gg, (*C.GOAL_GLOW, min(255, glow_a)), (ts//2, ts//2), ts//2-1)
        surface.blit(gg, (gc*ts, gr*ts))
        pygame.draw.circle(surface, C.GOAL_COLOR, (gx, gy), ts//2-4)
        pygame.draw.circle(surface, C.WHITE, (gx, gy), ts//2-4, 2)
        lbl_g = font.render('G', True, C.BLACK)
        surface.blit(lbl_g, (gx - lbl_g.get_width()//2, gy - lbl_g.get_height()//2))

    # ── Player sprite ────────────────────────────────────────

    def _draw_player(self, surface: pygame.Surface,
                     pos: Tuple[int,int], ts: int):
        r, c  = pos
        cx, cy = c*ts + ts//2, r*ts + ts//2
        rad   = ts//2 - 5
        glow  = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C.PLAYER_COLOR, 80), (ts//2, ts//2), rad+4)
        surface.blit(glow, (c*ts, r*ts))
        pygame.draw.circle(surface, C.PLAYER_COLOR, (cx, cy), rad)
        pygame.draw.circle(surface, C.PLAYER_OUT,   (cx, cy), rad, 2)
        # Eyes
        pygame.draw.circle(surface, C.WHITE, (cx-3, cy-2), 3)
        pygame.draw.circle(surface, C.WHITE, (cx+3, cy-2), 3)
        pygame.draw.circle(surface, C.BLACK, (cx-3, cy-2), 1)
        pygame.draw.circle(surface, C.BLACK, (cx+3, cy-2), 1)
