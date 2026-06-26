# core/maze.py — Cyber pixel maze rendering
"""
Maze: quản lý lưới 2D, vẽ tường/sàn, Start và Goal.
Nâng cấp UI:
  - Theme cyber neon
  - Overlay thuật toán có glow/pulse
  - Player là người pixel-art có animation bước đi
  - Goal là cờ pixel thay vì chấm tròn
"""

import math
import random
from typing import List, Tuple, Set
from core.monster import Monster
import pygame

import config as C
from algorithms.base import Step, PathResult


class Maze:
    def __init__(self, grid: List[List[int]], rows: int, cols: int,
                 start: Tuple[int, int], goal: Tuple[int, int]):
        self.grid = grid
        self.rows = rows
        self.cols = cols
        self.start = start
        self.goal = goal
        self._tick = 0.0
        self._tile_surf = self._build_tiles()
        self._font_marker = None
        self._ambient_particles = [
            [random.randrange(0, C.MAP_W), random.randrange(0, C.MAP_H), random.uniform(.12,.55), random.randint(35,120)]
            for _ in range(90)
        ]

    def _build_tiles(self):
        ts = C.TILE_SIZE

        def clamp(v):
            return max(0, min(255, int(v)))

        def shade(color, amount):
            return tuple(clamp(c + amount) for c in color)

        # WALL: nổi khối kiểu gạch cyber / dungeon pixel
        wall = pygame.Surface((ts, ts), pygame.SRCALPHA)
        wall.fill(C.WALL_COLOR)
        pygame.draw.rect(wall, shade(C.WALL_COLOR, 18), (0, 0, ts, ts), 1)
        pygame.draw.line(wall, C.WALL_LIGHT, (1, 1), (ts - 2, 1), 1)
        pygame.draw.line(wall, C.WALL_LIGHT, (1, 1), (1, ts - 2), 1)
        pygame.draw.line(wall, C.WALL_SHADOW, (1, ts - 2), (ts - 2, ts - 2), 1)
        pygame.draw.line(wall, C.WALL_SHADOW, (ts - 2, 1), (ts - 2, ts - 2), 1)

        if ts >= 12:
            mortar = C.WALL_MORTAR
            # các đường ron gạch lệch hàng, tạo cảm giác từng viên rõ hơn
            y1, y2 = ts // 3, 2 * ts // 3
            pygame.draw.line(wall, mortar, (2, y1), (ts - 3, y1), 1)
            pygame.draw.line(wall, mortar, (2, y2), (ts - 3, y2), 1)
            pygame.draw.line(wall, shade(mortar, 25), (ts // 2, 2), (ts // 2, y1 - 1), 1)
            pygame.draw.line(wall, shade(mortar, 18), (ts // 3, y1 + 1), (ts // 3, y2 - 1), 1)
            pygame.draw.line(wall, shade(mortar, 18), (2 * ts // 3, y2 + 1), (2 * ts // 3, ts - 3), 1)
            # chấm sáng nhỏ trên gạch giúp map không bị phẳng
            pygame.draw.rect(wall, shade(C.WALL_COLOR, 34), (max(2, ts // 6), max(2, ts // 6), max(2, ts // 5), 1))
            pygame.draw.rect(wall, shade(C.WALL_COLOR, 24), (ts - max(5, ts // 3), ts // 2, max(2, ts // 6), 1))
            # cracks / bevel pixels make each brick more hand-made and less flat
            pygame.draw.line(wall, shade(C.WALL_SHADOW, 6), (ts//4, ts//3+2), (ts//4+max(2,ts//8), ts//3+2), 1)
            pygame.draw.line(wall, shade(C.WALL_LIGHT, 12), (ts//2+1, 3), (ts//2+max(2,ts//6), 3), 1)

        # FLOOR: lát gạch tối có viền neon nhẹ
        floor = pygame.Surface((ts, ts), pygame.SRCALPHA)
        floor.fill(C.FLOOR_COLOR)
        pygame.draw.rect(floor, C.FLOOR_EDGE, (0, 0, ts, ts), 1)
        if ts >= 10:
            pygame.draw.line(floor, C.FLOOR_LIGHT, (1, 1), (ts - 2, 1), 1)
            pygame.draw.line(floor, C.FLOOR_LIGHT, (1, 1), (1, ts - 2), 1)
            pygame.draw.line(floor, shade(C.FLOOR_COLOR, -10), (1, ts - 2), (ts - 2, ts - 2), 1)
            pygame.draw.line(floor, shade(C.FLOOR_COLOR, -10), (ts - 2, 1), (ts - 2, ts - 2), 1)
        if ts >= 16:
            # pattern viên gạch sàn 2x2 + highlight từng góc
            half = ts // 2
            pygame.draw.line(floor, shade(C.FLOOR_EDGE, -8), (half, 2), (half, ts - 3), 1)
            pygame.draw.line(floor, shade(C.FLOOR_EDGE, -8), (2, half), (ts - 3, half), 1)
            pygame.draw.rect(floor, C.FLOOR_HILITE, (3, 3, half - 5, half - 5), 1)
            pygame.draw.rect(floor, shade(C.FLOOR_COLOR, -6), (half + 2, half + 2, half - 5, half - 5), 1)
        if ts >= 18:
            for dr in (ts // 4, 3 * ts // 4):
                for dc in (ts // 4, 3 * ts // 4):
                    pygame.draw.circle(floor, C.FLOOR_DOT, (dc, dr), 1)

        return {'wall': wall, 'floor': floor, '_size': ts}

    def _get_marker_font(self):
        if self._font_marker is None:
            try:
                self._font_marker = pygame.font.SysFont('Consolas', 11, bold=True)
            except Exception:
                self._font_marker = pygame.font.Font(None, 13)
        return self._font_marker

    def _ensure_tile_cache(self):
        """Rebuild tile surfaces if matrix size / TILE_SIZE changes."""
        ts = C.TILE_SIZE
        cached = self._tile_surf.get('_size') if isinstance(self._tile_surf, dict) else None
        if cached != ts:
            self._tile_surf = self._build_tiles()

    def is_walkable(self, r: int, c: int) -> bool:
        return (0 <= r < self.rows and 0 <= c < self.cols
                and self.grid[r][c] != 0)

    def update(self, dt: float):
        self._tick += dt

    def draw(self, surface: pygame.Surface,
             result: PathResult = None,
             current_step: int = 0,
             player_pos: Tuple[int, int] = None,
             player_trail: Set[Tuple[int, int]] = None,
             known_cells: Set[Tuple[int, int]] = None,
             show_start: bool = True):
        ts = C.TILE_SIZE
        self._ensure_tile_cache()
        self._draw_map_backdrop(surface)

        # 1. Tiles
        for r in range(self.rows):
            for c in range(self.cols):
                px, py = c * ts, r * ts
                if known_cells is not None and (r, c) not in known_cells:
                    pygame.draw.rect(surface, C.UNKNOWN_COLOR, (px, py, ts, ts))
                    pygame.draw.rect(surface, (12, 22, 40), (px, py, ts, ts), 1)
                else:
                    key = 'wall' if self.grid[r][c] == 0 else 'floor'
                    surface.blit(self._tile_surf[key], (px, py))

        # viền lưới mờ
        self._draw_soft_grid(surface, ts)
        self._draw_player_trail(surface, player_trail, known_cells)

        # 2. Algorithm visualization overlay
        if result and result.steps and current_step > 0:
            step_idx = min(current_step - 1, len(result.steps) - 1)
            if not C.SHOW_ALGO_TRACE:
                self._draw_algorithm_trail(
                    surface,
                    result.steps[step_idx],
                    result,
                    current_step,
                    known_cells,
                )
            if C.SHOW_ALGO_TRACE:
                self._draw_viz(surface, result.steps[step_idx], result, current_step, ts)
            elif C.SHOW_ROUTE_LINE:
                self._draw_route_line(surface, result.steps[step_idx], result, current_step)

        monster_pos = None
        monster_alert = False

        if result and result.steps and current_step > 0:
            step_idx = min(current_step - 1, len(result.steps) - 1)
            extra = result.steps[step_idx].extra
            monster_pos = extra.get("monster_pos", extra.get("ghost"))

        actor_pos = player_pos
        localized = False
        is_bfs_po = (result and result.algo_name == 'BFS-PO')
        
        if result and result.steps and current_step > 0:
            step_idx = min(current_step - 1, len(result.steps) - 1)
            if result.steps[step_idx].current:
                actor_pos = result.steps[step_idx].current
            localized = result.steps[step_idx].extra.get('localized', False)

        # 3. Start & treasure markers
        actual_show_start = show_start
        if is_bfs_po and not localized:
            actual_show_start = False

        self._draw_start_goal(surface, ts, treasure_open=(actor_pos == self.goal), show_start=actual_show_start)

        if monster_pos:
            monster_alert = actor_pos == monster_pos
            if not monster_alert:
                self._draw_monster(surface, monster_pos, ts, False)

        # Only draw player if not BFS-PO or if localized is True
        if actor_pos and (not is_bfs_po or localized):
            self._draw_player(surface, actor_pos, ts)
            self._draw_next_direction_arrow_for_step(
                surface,
                actor_pos,
                result,
                current_step,
                known_cells,
            )

        if actor_pos == self.goal:
            gr, gc = self.goal
            self._draw_pixel_trophy(surface, gc * ts, gr * ts, ts, opened=True)

        if monster_pos and monster_alert:
            self._draw_monster(surface, monster_pos, ts, True)

    def _draw_map_backdrop(self, surface: pygame.Surface):
        """Animated background: scanline + slow cyber dust / stars."""
        surface.fill(C.BG_COLOR)
        w, h = C.MAP_W, C.MAP_H
        phase = int(self._tick * 18) % 36
        grid_col = tuple(min(255, max(0, c + 4)) for c in C.FLOOR_EDGE)
        for y in range(-phase, h, 36):
            pygame.draw.line(surface, grid_col, (0, y), (w, y), 1)
        for x in range(0, w, 36):
            pygame.draw.line(surface, grid_col, (x, 0), (x, h), 1)

        # ambient particles nằm dưới tile, tạo cảm giác UI đang sống nhưng không rối mắt
        for p in self._ambient_particles:
            p[1] += p[2]
            p[0] += math.sin(self._tick * .7 + p[3]) * .08
            if p[1] > h: p[1] = -3; p[0] = random.randrange(0, w)
            a = int(35 + 55 * abs(math.sin(self._tick * .9 + p[3])))
            pygame.draw.rect(surface, (*C.HUD_TITLE, a), (int(p[0]), int(p[1]), 2, 2))

        # moving scanline
        scan = int((self._tick * 70) % h)
        pygame.draw.line(surface, (*C.HUD_TITLE, 80), (0, scan), (w, scan), 1)

        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 82), (0, 0, w, h), 18)
        pygame.draw.rect(vignette, (0, 0, 0, 0), (22, 22, w - 44, h - 44), 18)
        surface.blit(vignette, (0, 0))

    def _draw_soft_grid(self, surface: pygame.Surface, ts: int):
        if ts < 18:
            return
        line_col = (22, 36, 60)
        for x in range(0, C.MAP_W + 1, ts):
            pygame.draw.line(surface, line_col, (x, 0), (x, C.MAP_H), 1)
        for y in range(0, C.MAP_H + 1, ts):
            pygame.draw.line(surface, line_col, (0, y), (C.MAP_W, y), 1)

    # ── Visualization overlay ────────────────────────────────

    def _draw_cell_overlay(self, surface, r, c, color, alpha, inset=3, radius=4, glow=False):
        ts = C.TILE_SIZE
        x, y = c * ts, r * ts
        if glow:
            g = pygame.Surface((ts, ts), pygame.SRCALPHA)
            pygame.draw.rect(g, (*color, max(35, alpha // 3)), (1, 1, ts - 2, ts - 2), border_radius=radius)
            surface.blit(g, (x, y))
        s = pygame.Surface((ts, ts), pygame.SRCALPHA)
        rect = pygame.Rect(inset, inset, max(1, ts - inset * 2), max(1, ts - inset * 2))
        pygame.draw.rect(s, (*color, alpha), rect, border_radius=radius)
        surface.blit(s, (x, y))

    def _draw_player_trail(self, surface, player_trail, known_cells=None):
        if not player_trail:
            return

        ts = C.TILE_SIZE
        alpha = 170 if ts >= 18 else 200
        for r, c in player_trail:
            if (r, c) in (self.start, self.goal):
                continue
            if not self.is_walkable(r, c):
                continue
            if known_cells is not None and (r, c) not in known_cells:
                continue

            self._draw_cell_overlay(
                surface,
                r,
                c,
                C.PLAYER_TRAIL_COLOR,
                alpha,
                inset=max(1, ts // 12),
                radius=4,
                glow=True,
            )

            x, y = c * ts, r * ts
            mark = pygame.Rect(
                x + max(3, ts // 4),
                y + max(3, ts // 4),
                max(3, ts // 2),
                max(3, ts // 2),
            )
            pygame.draw.rect(surface, C.PLAYER_TRAIL_EDGE, mark, 1, border_radius=3)

    def _draw_algorithm_trail(self, surface, step: Step,
                              result: PathResult, current_step: int,
                              known_cells=None):
        if not step:
            return

        for pos in step.visited:
            if pos in (self.start, self.goal):
                continue
            if known_cells is not None and pos not in known_cells:
                continue
            r, c = pos
            self._draw_cell_overlay(
                surface,
                r,
                c,
                C.VIZ_VISITED,
                105,
                inset=max(2, C.TILE_SIZE // 8),
                radius=4,
                glow=False,
            )

        pruned_cells = step.extra.get("pruned_cells", set())
        for pos in pruned_cells:
            if pos in (self.start, self.goal):
                continue
            if known_cells is not None and pos not in known_cells:
                continue
            if not self.is_walkable(pos[0], pos[1]):
                continue
            r, c = pos
            self._draw_cell_overlay(
                surface,
                r,
                c,
                C.VIZ_BACKTRACK,
                120,
                inset=max(3, C.TILE_SIZE // 6),
                radius=4,
                glow=False,
            )
            if C.TILE_SIZE >= 16:
                x = c * C.TILE_SIZE
                y = r * C.TILE_SIZE
                pad = max(4, C.TILE_SIZE // 4)
                pygame.draw.line(
                    surface,
                    C.WHITE,
                    (x + pad, y + pad),
                    (x + C.TILE_SIZE - pad, y + C.TILE_SIZE - pad),
                    max(2, C.TILE_SIZE // 12),
                )
                pygame.draw.line(
                    surface,
                    C.WHITE,
                    (x + C.TILE_SIZE - pad, y + pad),
                    (x + pad, y + C.TILE_SIZE - pad),
                    max(2, C.TILE_SIZE // 12),
                )

        route = (
            result.path
            if current_step >= len(result.steps) and result.path
            else step.path_so_far
        )
        for pos in route:
            if pos in (self.start, self.goal):
                continue
            if known_cells is not None and pos not in known_cells:
                continue
            r, c = pos
            self._draw_cell_overlay(
                surface,
                r,
                c,
                C.PLAYER_TRAIL_COLOR,
                165,
                inset=max(1, C.TILE_SIZE // 10),
                radius=4,
                glow=True,
            )

        if getattr(C, 'SHOW_UPCOMING_PREVIEW', True):
            upcoming = self._next_preview_cells(step, result, current_step, known_cells)
            self._draw_upcoming_cells(surface, upcoming, origin=step.current)

    def _next_preview_cells(self, step: Step, result: PathResult,
                            current_step: int, known_cells=None):
        count = max(1, getattr(C, 'UPCOMING_PREVIEW_STEPS', 5))
        current = step.current

        if result.path and current in result.path:
            start_idx = result.path.index(current) + 1
            cells = result.path[start_idx:start_idx + count]
            if known_cells is None:
                return cells
            return [pos for pos in cells if pos in known_cells]

        cells = []
        seen = {current}
        for future_step in result.steps[current_step:current_step + count * 3]:
            pos = future_step.current
            if not pos or pos in seen:
                continue
            if not self.is_walkable(pos[0], pos[1]):
                continue
            if known_cells is not None and pos not in known_cells:
                continue
            cells.append(pos)
            seen.add(pos)
            if len(cells) >= count:
                break

        if cells:
            return cells

        for pos in step.frontier:
            if not pos or pos in seen:
                continue
            if known_cells is not None and pos not in known_cells:
                continue
            cells.append(pos)
            seen.add(pos)
            if len(cells) >= count:
                break
        return cells

    def _draw_upcoming_cells(self, surface, cells, origin=None):
        if not cells:
            return

        ts = C.TILE_SIZE
        font = self._get_marker_font()
        colors = getattr(C, 'VIZ_UPCOMING_COLORS', [C.VIZ_CURRENT])
        prev = origin
        for idx, pos in enumerate(cells):
            if pos in (self.start,):
                continue
            color = colors[idx % len(colors)]
            if prev and self._are_adjacent(prev, pos):
                x1, y1 = self._cell_center(prev)
                x2, y2 = self._cell_center(pos)
                pygame.draw.line(surface, (8, 10, 18), (x1, y1), (x2, y2),
                                 max(5, ts // 3))
                pygame.draw.line(surface, color, (x1, y1), (x2, y2),
                                 max(3, ts // 4))
                pygame.draw.line(surface, C.WHITE, (x1, y1), (x2, y2),
                                 max(1, ts // 11))
            prev = pos

        for idx, pos in enumerate(cells):
            if pos in (self.start,):
                continue
            r, c = pos
            color = colors[idx % len(colors)]
            self._draw_cell_overlay(
                surface,
                r,
                c,
                color,
                145,
                inset=max(2, ts // 8),
                radius=5,
                glow=True,
            )

            x, y = c * ts, r * ts
            badge = pygame.Rect(
                x + ts // 2 - max(5, ts // 6),
                y + ts // 2 - max(5, ts // 6),
                max(10, ts // 3),
                max(10, ts // 3),
            )
            pygame.draw.rect(surface, (8, 10, 18), badge.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surface, color, badge, border_radius=3)
            label = font.render(str(idx + 1), True, C.BLACK)
            surface.blit(
                label,
                (
                    badge.centerx - label.get_width() // 2,
                    badge.centery - label.get_height() // 2,
                ),
            )

    def _draw_next_direction_arrow_for_step(self, surface, actor_pos,
                                            result: PathResult,
                                            current_step: int,
                                            known_cells=None):
        if not getattr(C, 'SHOW_UPCOMING_PREVIEW', True):
            return
        if not result or not result.steps or current_step <= 0:
            return

        step_idx = min(current_step - 1, len(result.steps) - 1)
        step = result.steps[step_idx]
        upcoming = self._next_preview_cells(step, result, current_step, known_cells)
        next_pos = self._first_adjacent_next(actor_pos, upcoming)
        if next_pos:
            self._draw_next_direction_arrow(surface, actor_pos, next_pos)

    def _first_adjacent_next(self, current, cells):
        if not current or not cells:
            return None
        for pos in cells:
            if pos and self._are_adjacent(current, pos):
                return pos
        return None

    def _draw_next_direction_arrow(self, surface, current, next_pos):
        dr = next_pos[0] - current[0]
        dc = next_pos[1] - current[1]
        if abs(dr) + abs(dc) != 1:
            return

        ts = C.TILE_SIZE
        cx, cy = self._cell_center(current)
        dx, dy = dc, dr
        px, py = -dy, dx
        color = C.VIZ_UPCOMING_COLORS[0]

        tail_len = ts * 0.20
        tip_len = ts * 0.34
        base_len = ts * 0.08
        half_w = max(4, int(ts * 0.18))

        tail = (int(cx - dx * tail_len), int(cy - dy * tail_len))
        base = (int(cx + dx * base_len), int(cy + dy * base_len))
        tip = (int(cx + dx * tip_len), int(cy + dy * tip_len))

        outline_half = half_w + 3
        outline_tip = (int(cx + dx * (tip_len + 3)), int(cy + dy * (tip_len + 3)))
        outline_base = (int(cx + dx * (base_len - 1)), int(cy + dy * (base_len - 1)))
        outline = [
            outline_tip,
            (
                int(outline_base[0] + px * outline_half),
                int(outline_base[1] + py * outline_half),
            ),
            (
                int(outline_base[0] - px * outline_half),
                int(outline_base[1] - py * outline_half),
            ),
        ]
        arrow = [
            tip,
            (int(base[0] + px * half_w), int(base[1] + py * half_w)),
            (int(base[0] - px * half_w), int(base[1] - py * half_w)),
        ]

        backing = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(
            backing,
            (8, 10, 18, 145),
            (ts // 2, ts // 2),
            max(7, ts // 3),
        )
        surface.blit(backing, (cx - ts // 2, cy - ts // 2))

        pygame.draw.line(surface, (8, 10, 18), tail, base, max(5, ts // 4))
        pygame.draw.line(surface, color, tail, base, max(3, ts // 6))
        pygame.draw.polygon(surface, (8, 10, 18), outline)
        pygame.draw.polygon(surface, color, arrow)
        pygame.draw.line(surface, C.WHITE, tail, base, max(1, ts // 13))
        pygame.draw.polygon(surface, C.WHITE, [
            (
                int(tip[0] - dx * max(3, ts // 9)),
                int(tip[1] - dy * max(3, ts // 9)),
            ),
            (
                int(base[0] + px * max(1, half_w // 3)),
                int(base[1] + py * max(1, half_w // 3)),
            ),
            (
                int(base[0] - px * max(1, half_w // 3)),
                int(base[1] - py * max(1, half_w // 3)),
            ),
        ])

    def _are_adjacent(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _cell_center(self, pos):
        r, c = pos
        return (
            c * C.TILE_SIZE + C.TILE_SIZE // 2,
            r * C.TILE_SIZE + C.TILE_SIZE // 2,
        )

    def _draw_route_line(self, surface: pygame.Surface, step: Step,
                         result: PathResult, current_step: int):
        route = result.path if current_step >= len(result.steps) and result.path else step.path_so_far
        pts = [
            (c * C.TILE_SIZE + C.TILE_SIZE // 2, r * C.TILE_SIZE + C.TILE_SIZE // 2)
            for r, c in route
        ]
        if len(pts) >= 2:
            self._draw_pixel_route(surface, pts, C.VIZ_PATH, moving=current_step < len(result.steps))

    def _draw_viz(self, surface: pygame.Surface, step: Step,
                  result: PathResult, current_step: int, ts: int):
        is_done = current_step >= len(result.steps)
        pulse = int(45 + 35 * abs(math.sin(self._tick * 5)))

        is_bfs_po = (result.algo_name == 'BFS-PO')

        if is_bfs_po:
            # Đối với BFS-PO: Chỉ vẽ các chấm tròn cam (candidates) và đường đi của chúng đến đích
            candidate_paths = step.extra.get('candidate_paths', [])
            if candidate_paths:
                temp_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                for path in candidate_paths:
                    if len(path) >= 2:
                        pts = [(p[1]*ts + ts//2, p[0]*ts + ts//2) for p in path]
                        # Vẽ đường màu cam chỉ hướng đến đích
                        pygame.draw.lines(temp_surf, (255, 140, 0, 110), False, pts, 2)
                surface.blit(temp_surf, (0, 0))

            # Vẽ các chấm cam đại diện cho các trạng thái tin tưởng trong Belief State
            for pos in step.frontier:
                r, c = pos
                cx, cy = c*ts + ts//2, r*ts + ts//2
                glow = pygame.Surface((ts, ts), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 140, 0, 100), (ts//2, ts//2), ts//2 - 2)
                surface.blit(glow, (c*ts, r*ts))
                pygame.draw.circle(surface, (255, 165, 0), (cx, cy), ts//2 - 5)
                pygame.draw.circle(surface, C.WHITE, (cx, cy), ts//2 - 5, 1)
            return

        visited_list = list(step.visited)
        total_v = max(1, len(visited_list) - 1)
        for i, pos in enumerate(visited_list):
            if pos in (self.start, self.goal):
                continue
            r, c = pos
            # Heatmap: ô mới hơn ấm/sáng hơn, ô cũ lạnh hơn
            t = i / total_v
            col = (
                int(C.VIZ_VISITED[0] * (1-t) + C.VIZ_FRONTIER[0] * t),
                int(C.VIZ_VISITED[1] * (1-t) + C.VIZ_FRONTIER[1] * t),
                int(C.VIZ_VISITED[2] * (1-t) + C.VIZ_FRONTIER[2] * t),
            )
            self._draw_cell_overlay(surface, r, c, col, 62 + int(54*t), inset=4)
        pruned_cells = step.extra.get("pruned_cells", set())

        for pos in pruned_cells:
            if pos in (self.start, self.goal):
                continue

            # Không vẽ nếu ô đó nằm trên đường thật
            if pos in step.path_so_far:
                continue

            r, c = pos

            self._draw_cell_overlay(
                surface,
                r,
                c,
                (255, 60, 100),
                90,
                inset=6,
                glow=False
            )

            x = c * ts
            y = r * ts

            pygame.draw.line(
                surface,
                (255, 80, 120),
                (x + ts * 0.30, y + ts * 0.30),
                (x + ts * 0.70, y + ts * 0.70),
                max(2, ts // 10)
            )

            pygame.draw.line(
                surface,
                (255, 80, 120),
                (x + ts * 0.70, y + ts * 0.30),
                (x + ts * 0.30, y + ts * 0.70),
                max(2, ts // 10)
            )
        for pos in step.frontier:
            if pos in (self.start, self.goal):
                continue
            r, c = pos
            self._draw_cell_overlay(surface, r, c, C.VIZ_FRONTIER, 135, inset=3, glow=True)

        if step.path_so_far:
            color = C.VIZ_BACKTRACK if step.is_backtrack else C.VIZ_PATH
            alpha = 95 if step.is_backtrack else 135
            pts = []
            for pos in step.path_so_far:
                if pos in (self.start, self.goal):
                    continue
                r, c = pos
                self._draw_cell_overlay(surface, r, c, color, alpha, inset=5, glow=True)
                pts.append((c * ts + ts // 2, r * ts + ts // 2))
            if len(pts) >= 2 and ts >= 16:
                self._draw_pixel_route(surface, pts, color, moving=not is_done)

        cur = step.current
        if cur and cur not in (self.start, self.goal):
            r, c = cur
            cx = c * ts + ts // 2
            cy = r * ts + ts // 2

            pulse = abs(math.sin(self._tick * 6))
            radius = max(6, ts // 2 + int(pulse * 5))

            self._draw_cell_overlay(surface, r, c, C.VIZ_CURRENT, 100 + int(pulse * 80), inset=2, glow=True)

            pygame.draw.circle(surface, (*C.VIZ_CURRENT, 90), (cx, cy), radius)
            pygame.draw.circle(surface, C.WHITE, (cx, cy), max(4, ts // 5), 2)

            # 3 chấm “thinking”
            dot_y = cy - ts // 2 - 8
            for i in range(3):
                a = abs(math.sin(self._tick * 5 + i))
                pygame.draw.circle(
                    surface,
                    C.VIZ_CURRENT,
                    (cx - 10 + i * 10, dot_y - int(a * 4)),
                    max(2, ts // 10)
                )

        if is_done and result.path:
            pts = []
            for pos in result.path:
                if pos in (self.start, self.goal):
                    continue
                r, c = pos
                self._draw_cell_overlay(surface, r, c, C.VIZ_PATH, 210, inset=3, glow=True)
                pts.append((c * ts + ts // 2, r * ts + ts // 2))
            if len(pts) >= 2:
                self._draw_pixel_route(surface, pts, C.VIZ_PATH, moving=False, final=True)
    def draw_race_agent(self, surface, result, step_idx, color, label,
                        route_style="solid"):
        if not result or not result.steps or step_idx <= 0:
            return

        ts = C.TILE_SIZE
        idx = min(step_idx - 1, len(result.steps) - 1)
        step = result.steps[idx]

        # visited riêng của agent
        for pos in step.visited if C.SHOW_ALGO_TRACE else []:
            if pos in (self.start, self.goal):
                continue

            r, c = pos
            self._draw_cell_overlay(surface, r, c, color, 45, inset=6)

        # path riêng của agent
        pts = []
        for pos in step.path_so_far:
            if pos in (self.start, self.goal):
                continue

            r, c = pos
            if C.SHOW_ALGO_TRACE:
                self._draw_cell_overlay(surface, r, c, color, 95, inset=5, glow=True)
            pts.append((c * ts + ts // 2, r * ts + ts // 2))

        if len(pts) >= 2:
            if route_style == "dashed":
                self._draw_dashed_route(surface, pts, color, moving=True)
            else:
                self._draw_pixel_route(surface, pts, color, moving=True)

        # current node / agent
        if step.current:
            r, c = step.current
            cx = c * ts + ts // 2
            cy = r * ts + ts // 2

            pulse = abs(math.sin(self._tick * 7))
            radius = max(5, ts // 3 + int(pulse * 4))

            pygame.draw.circle(surface, (*color, 90), (cx, cy), radius)
            pygame.draw.circle(surface, color, (cx, cy), max(4, ts // 4))
            pygame.draw.circle(surface, C.WHITE, (cx, cy), max(2, ts // 9))

            if ts >= 18:
                font = self._get_marker_font()
                txt = font.render(label, True, C.BLACK)
                tag = pygame.Rect(cx - 14, cy - ts // 2, 28, 14)
                pygame.draw.rect(surface, color, tag, border_radius=4)
                surface.blit(
                    txt,
                    (
                        tag.centerx - txt.get_width() // 2,
                        tag.centery - txt.get_height() // 2,
                    ),
                )
    
    def _draw_dashed_route(self, surface, pts, color, moving=True):
        ts = C.TILE_SIZE
        if len(pts) < 2:
            return

        width_outer = max(5, ts // 4)
        width_mid = max(3, ts // 7)
        width_inner = max(1, ts // 12)
        dash_len = max(8, int(ts * 0.62))
        gap_len = max(5, int(ts * 0.38))
        segments = self._dashed_segments(pts, dash_len, gap_len)
        if not segments:
            return

        glow_s = pygame.Surface((C.MAP_W, C.MAP_H), pygame.SRCALPHA)
        for start, end in segments:
            pygame.draw.line(glow_s, (*color, 34), start, end, width_outer + 9)
            pygame.draw.line(glow_s, (*color, 70), start, end, width_outer + 3)
        surface.blit(glow_s, (0, 0))

        for start, end in segments:
            pygame.draw.line(surface, (8, 10, 18), start, end, width_outer)
            pygame.draw.line(surface, color, start, end, width_mid)
            pygame.draw.line(surface, C.WHITE, start, end, width_inner)

        for i, (x, y) in enumerate(pts):
            if i % 2 != 0:
                continue
            size = max(4, ts // 5)
            rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
            pygame.draw.rect(surface, (8, 10, 18), rect.inflate(4, 4), border_radius=3)
            pygame.draw.rect(surface, color, rect, border_radius=2)

        if moving and segments:
            idx = int(self._tick * 12) % len(segments)
            start, end = segments[idx]
            sx = (start[0] + end[0]) // 2
            sy = (start[1] + end[1]) // 2
            spark = max(5, ts // 3)
            pygame.draw.circle(surface, (*color, 130), (sx, sy), spark)
            pygame.draw.circle(surface, C.WHITE, (sx, sy), max(2, spark // 2))

    def _dashed_segments(self, pts, dash_len, gap_len):
        segments = []
        pattern = dash_len + gap_len
        if pattern <= 0:
            return segments

        phase = (self._tick * 18) % pattern
        carry = -phase
        for i in range(1, len(pts)):
            x1, y1 = pts[i - 1]
            x2, y2 = pts[i]
            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)
            if length <= 0:
                continue

            ux = dx / length
            uy = dy / length
            pos = carry
            while pos < length:
                dash_start = max(0, pos)
                dash_end = min(length, pos + dash_len)
                if dash_end > 0 and dash_start < length and dash_end > dash_start:
                    start = (
                        int(x1 + ux * dash_start),
                        int(y1 + uy * dash_start),
                    )
                    end = (
                        int(x1 + ux * dash_end),
                        int(y1 + uy * dash_end),
                    )
                    segments.append((start, end))
                pos += pattern

            carry = pos - length - pattern
        return segments

    def _draw_pixel_route(self, surface, pts, color, moving=True, final=False):
        """Vẽ route nổi bật dạng neon pixel cable + hạt sáng chạy trên đường."""
        ts = C.TILE_SIZE
        if len(pts) < 2:
            return
        width_outer = max(4, ts // 4 if final else ts // 6)
        width_mid = max(3, ts // 7)
        width_inner = max(2, ts // 11)

        # halo nhiều lớp giúp đường đi nổi lên trên nền gạch
        glow_s = pygame.Surface((C.MAP_W, C.MAP_H), pygame.SRCALPHA)
        pygame.draw.lines(glow_s, (*color, 38), False, pts, width_outer + 10)
        pygame.draw.lines(glow_s, (*color, 68 if final else 48), False, pts, width_outer + 4)
        surface.blit(glow_s, (0, 0))

        pygame.draw.lines(surface, C.VIZ_PATH_DARK, False, pts, width_outer)
        pygame.draw.lines(surface, color, False, pts, width_mid)
        pygame.draw.lines(surface, C.WHITE if final else C.ROUTE_CORE, False, pts, width_inner)

        # pixel node sáng tại các ngã / một số điểm trên đường
        jump = max(1, len(pts) // 28)
        phase = int(self._tick * 10) % max(1, jump)
        for i, (x, y) in enumerate(pts):
            if final:
                draw_it = i % max(1, len(pts) // 18) == 0
            else:
                draw_it = i % jump == phase
            if not draw_it:
                continue
            size = max(4, ts // 4)
            rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
            pygame.draw.rect(surface, C.ROUTE_NODE_DARK, rect.inflate(4, 4), border_radius=3)
            pygame.draw.rect(surface, color, rect, border_radius=2)
            pygame.draw.rect(surface, C.WHITE, rect.inflate(-max(2, size // 2), -max(2, size // 2)), border_radius=1)

        # “spark” chạy dọc đường để nhìn rõ animation đang tiến
        if moving and pts:
            idx = int(self._tick * 18) % len(pts)
            x, y = pts[idx]
            spark = max(5, ts // 3)
            pygame.draw.circle(surface, (*color, 120), (x, y), spark)
            pygame.draw.circle(surface, C.WHITE, (x, y), max(2, spark // 2))

        # mũi tên hướng đi, ít nhưng rõ
        step = max(4, len(pts) // 10)
        for i in range(step, len(pts), step):
            x1, y1 = pts[i - 1]
            x2, y2 = pts[i]
            dx, dy = x2 - x1, y2 - y1
            if dx == 0 and dy == 0:
                continue
            size = max(5, ts // 4)
            if abs(dx) > abs(dy):
                tri = [(x2 + (size if dx > 0 else -size), y2),
                       (x2 - (size // 2 if dx > 0 else -size // 2), y2 - size // 2),
                       (x2 - (size // 2 if dx > 0 else -size // 2), y2 + size // 2)]
            else:
                tri = [(x2, y2 + (size if dy > 0 else -size)),
                       (x2 - size // 2, y2 - (size // 2 if dy > 0 else -size // 2)),
                       (x2 + size // 2, y2 - (size // 2 if dy > 0 else -size // 2))]
            pygame.draw.polygon(surface, C.WHITE if final else C.ROUTE_CORE, tri)
            pygame.draw.polygon(surface, color, tri, 1)


    # ── Start / Goal ─────────────────────────────────────────

    def _draw_start_goal(self, surface: pygame.Surface, ts: int, treasure_open: bool = False, show_start: bool = True):
        """Start = animated portal, Goal = glowing trophy/star marker."""
        glow_a = int(120 + math.sin(self._tick * 3.2) * 50)
        font = self._get_marker_font()

        if show_start:
            sr, sc = self.start
            sx, sy = sc * ts + ts // 2, sr * ts + ts // 2
            self._draw_portal(surface, sx, sy, ts, C.START_COLOR, C.START_GLOW, label=None)

        gr, gc = self.goal
        gx, gy = gc * ts + ts // 2, gr * ts + ts // 2
        goal_s = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
        pygame.draw.circle(goal_s, (*C.GOAL_GLOW, min(230, glow_a)), (ts, ts), max(8, ts // 2 + 7))
        pygame.draw.circle(goal_s, (*C.GOAL_COLOR, 60), (ts, ts), max(5, ts // 2 - 1), 2)
        surface.blit(goal_s, (gx - ts, gy - ts))
        self._draw_pixel_trophy(surface, gc * ts, gr * ts, ts, opened=treasure_open)

    def _draw_portal(self, surface, cx: int, cy: int, ts: int, color, glow, label='S'):
        pulse = abs(math.sin(self._tick * 4.5))
        ring = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
        center = (ts, ts)
        for i in range(4):
            rad = max(4, ts // 3 + i * 3 + int(pulse * 2))
            pygame.draw.circle(ring, (*glow, 60 - i * 9), center, rad, max(1, ts // 12))
        # small orbiting pixels
        for k in range(8):
            ang = self._tick * 2.5 + k * math.pi / 4
            px = center[0] + int(math.cos(ang) * (ts * 0.45))
            py = center[1] + int(math.sin(ang) * (ts * 0.45))
            pygame.draw.rect(ring, (*glow, 190), (px-1, py-1, 3, 3), border_radius=1)
        surface.blit(ring, (cx - ts, cy - ts))
        base = pygame.Rect(cx - ts//3, cy - ts//3, 2*ts//3, 2*ts//3)
        pygame.draw.rect(surface, (6, 30, 24), base.inflate(5, 5), border_radius=7)
        pygame.draw.rect(surface, color, base, border_radius=6)
        pygame.draw.rect(surface, C.WHITE, base.inflate(-max(4, ts//3), -max(4, ts//3)), border_radius=3)
        if label:
            font = self._get_marker_font()
            lbl = font.render(label, True, C.BLACK)
            surface.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))
        else:
            self._draw_entrance_icon(surface, cx, cy, ts)

    def _draw_entrance_icon(self, surface, cx: int, cy: int, ts: int):
        radius = max(6, ts // 3)
        outline = (8, 18, 18)
        brass = (232, 190, 88)
        face = (230, 244, 216)
        needle = (220, 48, 42)

        pygame.draw.circle(surface, outline, (cx, cy), radius + 3)
        pygame.draw.circle(surface, brass, (cx, cy), radius + 1)
        pygame.draw.circle(surface, face, (cx, cy), radius - 2)
        pygame.draw.circle(surface, outline, (cx, cy), max(2, radius // 5))

        tip = max(5, radius - 2)
        pygame.draw.polygon(surface, needle,
                            [(cx, cy - tip), (cx - max(2, ts // 12), cy + 1),
                             (cx, cy + max(2, ts // 12)), (cx + max(2, ts // 12), cy + 1)])
        pygame.draw.polygon(surface, (40, 90, 95),
                            [(cx, cy + tip), (cx - max(2, ts // 12), cy - 1),
                             (cx, cy - max(2, ts // 12)), (cx + max(2, ts // 12), cy - 1)])

        tick = max(1, ts // 14)
        pygame.draw.line(surface, outline, (cx, cy - radius + 2), (cx, cy - radius + 2 + tick), 1)
        pygame.draw.line(surface, outline, (cx + radius - 2, cy), (cx + radius - 2 - tick, cy), 1)
        pygame.draw.line(surface, outline, (cx, cy + radius - 2), (cx, cy + radius - 2 - tick), 1)
        pygame.draw.line(surface, outline, (cx - radius + 2, cy), (cx - radius + 2 + tick, cy), 1)

    def _draw_pixel_trophy(self, surface, x: int, y: int, ts: int, opened: bool = False):
        unit = max(2, ts // 8 if opened else ts // 10)
        pad = 0 if opened else max(2, ts // 10)
        left = x - ts // 5 if opened else x + pad
        top = y + ts // 10 if opened else y + ts // 5
        w = ts + (2 * ts // 5) if opened else ts - pad * 2
        h = ts - (top - y) - pad
        lid_h = max(7, h // 2)
        body_h = h - lid_h + unit

        wood_dark = (74, 38, 16)
        wood_mid = (138, 78, 28)
        wood_light = (196, 124, 46)
        metal = (246, 190, 54)
        metal_light = (255, 238, 154)
        outline = (28, 18, 8)

        pygame.draw.ellipse(surface, (0, 0, 0, 115),
                            (left, y + ts - pad * 2, w, max(3, pad)))

        lid_y = top - (3 * unit if opened else 0)
        lid = pygame.Rect(left, lid_y, w, lid_h + unit)
        pygame.draw.rect(surface, outline, lid, border_radius=5)
        pygame.draw.rect(surface, wood_mid,
                         lid.inflate(-max(2, unit), -max(2, unit // 2)),
                         border_radius=4)
        pygame.draw.rect(surface, wood_light,
                         (left + 2 * unit, lid_y + unit, w - 4 * unit, max(2, unit)))
        pygame.draw.line(surface, outline, (left + unit, lid_y + lid_h),
                         (left + w - unit, lid_y + lid_h), 2)

        body = pygame.Rect(left, top + lid_h, w, body_h)
        pygame.draw.rect(surface, outline, body, border_radius=4)
        pygame.draw.rect(surface, wood_dark, body.inflate(-unit, -unit // 2), border_radius=3)
        if opened:
            pygame.draw.rect(surface, (18, 10, 4),
                             (left + unit, top + lid_h, w - 2 * unit, max(3, unit)),
                             border_radius=2)
        pygame.draw.rect(surface, wood_mid,
                         (left + unit, top + lid_h + body_h // 2, w - 2 * unit, body_h // 2 - 1))

        band_w = max(2, unit)
        pygame.draw.rect(surface, metal, (left + band_w, top + unit, band_w, h - unit))
        pygame.draw.rect(surface, metal, (left + w - 2 * band_w, top + unit, band_w, h - unit))
        pygame.draw.rect(surface, metal, (left, top + lid_h, w, band_w))
        pygame.draw.rect(surface, metal_light, (left + unit, top + lid_h, w - 2 * unit, 1))

        lock_w = max(6, 2 * unit)
        lock_h = max(6, 2 * unit)
        lock = pygame.Rect(x + ts // 2 - lock_w // 2, top + lid_h - unit // 2,
                           lock_w, lock_h)
        pygame.draw.rect(surface, metal_light, lock, border_radius=2)
        pygame.draw.rect(surface, outline, lock, 1, border_radius=2)
        pygame.draw.circle(surface, outline, (lock.centerx, lock.centery), max(1, unit // 3))
        pygame.draw.rect(surface, outline,
                         (lock.centerx - 1, lock.centery, 2, max(2, unit)),
                         border_radius=1)

        coin_y = top + lid_h - max(2, unit // 2)
        for i, col in enumerate((metal_light, C.GOAL_COLOR, (255, 210, 85))):
            pygame.draw.circle(surface, col,
                               (left + w // 3 + i * max(3, unit), coin_y),
                               max(2, unit // 2))

        if opened:
            pulse = abs(math.sin(self._tick * 7))
            shine = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
            pygame.draw.circle(shine, (*C.GOAL_GLOW, 85 + int(80 * pulse)),
                               (ts, ts), max(8, ts // 2 + int(5 * pulse)))
            surface.blit(shine, (x - ts // 2, y - ts // 2))

            for i in range(5):
                ang = self._tick * 3 + i * math.tau / 5
                sx = x + ts // 2 + int(math.cos(ang) * (ts * 0.34))
                sy = y + ts // 2 + int(math.sin(ang) * (ts * 0.28))
                pygame.draw.circle(surface, metal_light, (sx, sy), max(2, unit // 2))

            beam_w = max(2, unit)
            pygame.draw.polygon(surface, (*metal_light, 180),
                                [(x + ts // 2, top + lid_h - unit),
                                 (x + ts // 2 - beam_w, top),
                                 (x + ts // 2 + beam_w, top)])

    # ── Player sprite ────────────────────────────────────────

    def _draw_monster(self, surface: pygame.Surface, pos: Tuple[int, int],
                      ts: int, alert: bool = False):
        r, c = pos
        x, y = c * ts, r * ts
        pulse = abs(math.sin(self._tick * 6.5))
        color = C.MONSTER_GLOW if alert else C.MONSTER_COLOR

        glow = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
        center = (ts, ts)
        pygame.draw.circle(glow, (*color, 75 + int(60 * pulse)),
                           center, max(8, ts // 2 + int(5 * pulse)))
        pygame.draw.circle(glow, (*color, 45), center, max(10, ts // 2 + 7), 2)
        surface.blit(glow, (x - ts // 2, y - ts // 2))

        shadow_h = max(3, ts // 5)
        pygame.draw.ellipse(surface, (0, 0, 0, 125),
                            (x + ts // 6, y + ts - shadow_h - 1,
                             ts * 2 // 3, shadow_h))

        unit = max(2, ts // 10)
        sprite_w = unit * 9
        sprite_h = unit * 9
        ox = x + (ts - sprite_w) // 2
        oy = y + (ts - sprite_h) // 2 + int(math.sin(self._tick * 9) * max(1, unit // 2))
        frame = int(self._tick * 8) % 2

        dark = (35, 8, 22)
        body = color
        body_dark = (150, 28, 62)
        eye = (255, 245, 120) if not alert else C.WHITE
        tooth = (245, 250, 255)
        outline = (8, 4, 12)

        def px(col, row, w, h, draw_color):
            pygame.draw.rect(
                surface,
                draw_color,
                (ox + col * unit, oy + row * unit, w * unit, h * unit),
            )

        px(2, 0, 2, 1, outline)
        px(5, 0, 2, 1, outline)
        px(1, 1, 7, 1, outline)
        px(0, 2, 9, 5, outline)
        px(1, 7, 7, 1, outline)

        px(2, 0, 1, 1, C.MONSTER_GLOW)
        px(6, 0, 1, 1, C.MONSTER_GLOW)
        px(1, 1, 2, 1, C.MONSTER_GLOW)
        px(6, 1, 2, 1, C.MONSTER_GLOW)

        px(1, 2, 7, 4, body)
        px(2, 1, 5, 1, body)
        px(2, 6, 5, 1, body_dark)
        px(3, 7, 3, 1, dark)

        eye_shift = 1 if frame else 0
        px(2 + eye_shift, 3, 1, 1, eye)
        px(6 - eye_shift, 3, 1, 1, eye)
        px(3, 5, 3, 1, dark)
        px(3, 6, 1, 1, tooth)
        px(5, 6, 1, 1, tooth)

        if frame == 0:
            px(0, 4, 1, 2, body_dark)
            px(8, 4, 1, 2, body_dark)
            px(1, 8, 2, 1, dark)
            px(6, 8, 2, 1, dark)
        else:
            px(0, 3, 1, 2, body_dark)
            px(8, 5, 1, 2, body_dark)
            px(2, 8, 2, 1, dark)
            px(5, 8, 2, 1, dark)

        pygame.draw.rect(surface, C.MONSTER_GLOW,
                         (ox, oy, sprite_w, sprite_h), 1)

        if ts >= 18:
            font = self._get_marker_font()
            tag = font.render("MIN", True, C.BLACK)
            rect = pygame.Rect(x + ts // 2 - tag.get_width() - 7,
                               y + 2, tag.get_width() + 8, tag.get_height() + 3)
            pygame.draw.rect(surface, C.MONSTER_GLOW, rect, border_radius=4)
            surface.blit(tag, (rect.x + 4, rect.y + 1))

    def _draw_player(self, surface: pygame.Surface, pos: Tuple[int, int], ts: int):
        r, c = pos
        x, y = c * ts, r * ts
        glow = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C.PLAYER_COLOR, 70), (ts // 2, ts // 2), max(4, ts // 2 - 1))
        pygame.draw.circle(glow, (*C.PLAYER_COLOR, 40), (ts // 2, ts // 2), max(6, ts // 2 + 3), 2)
        surface.blit(glow, (x, y))
        pygame.draw.ellipse(surface, (0, 0, 0, 95), (x + ts // 5, y + ts - max(5, ts // 4), ts * 3 // 5, max(3, ts // 5)))

        # Người pixel 8x8, scale theo kích thước ô
        unit = max(2, ts // 10)
        sprite_w = unit * 8
        sprite_h = unit * 9
        ox = x + (ts - sprite_w) // 2
        oy = y + (ts - sprite_h) // 2 + int(math.sin(self._tick * 8) * max(1, unit // 2))
        frame = int(self._tick * 8) % 2

        skin = (232, 178, 125)
        hat = (155, 104, 44)
        hat_dark = (86, 58, 30)
        jacket = (116, 82, 42)
        jacket_dark = (72, 50, 30)
        scarf = (220, 56, 48)
        pants = (54, 72, 78)
        shoe = (28, 22, 16)
        lamp = (255, 232, 120)
        outline = (5, 10, 18)

        def px(col, row, w, h, color):
            pygame.draw.rect(surface, color, (ox + col * unit, oy + row * unit, w * unit, h * unit))

        # outline bóng nhỏ
        px(2, 0, 4, 1, outline)
        px(1, 1, 6, 3, outline)
        px(1, 4, 6, 3, outline)
        px(1, 7, 2, 2, outline)
        px(5, 7, 2, 2, outline)

        # hat + head
        px(1, 0, 6, 1, hat_dark)
        px(2, 0, 4, 1, hat)
        px(0, 1, 8, 1, hat)
        px(2, 1, 4, 3, skin)
        px(1, 2, 1, 1, hat_dark)
        px(5, 2, 1, 1, hat_dark)
        # eyes
        px(3, 2, 1, 1, outline)
        px(5, 2, 1, 1, outline)

        # body
        px(2, 4, 4, 3, jacket)
        px(3, 4, 2, 1, scarf)
        px(2, 6, 4, 1, jacket_dark)

        # arms swing
        if frame == 0:
            px(1, 4, 1, 3, skin)
            px(6, 4, 1, 2, jacket)
            px(7, 4, 1, 1, lamp)
            px(2, 7, 1, 2, pants)
            px(5, 7, 1, 2, pants)
            px(1, 9, 2, 1, shoe)
            px(5, 9, 2, 1, shoe)
        else:
            px(1, 4, 1, 2, skin)
            px(6, 4, 1, 3, jacket)
            px(7, 5, 1, 1, lamp)
            px(2, 7, 1, 2, pants)
            px(5, 7, 1, 2, pants)
            px(2, 9, 2, 1, shoe)
            px(4, 9, 2, 1, shoe)

        # flashlight beam
        beam = pygame.Surface((ts, ts), pygame.SRCALPHA)
        beam_alpha = 42 + int(abs(math.sin(self._tick * 6)) * 35)
        pygame.draw.polygon(beam, (*lamp, beam_alpha),
                            [(ts // 2 + unit, ts // 2),
                             (ts - 1, ts // 2 - 2 * unit),
                             (ts - 1, ts // 2 + 2 * unit)])
        surface.blit(beam, (x, y))

        # bong/hat bui pixel duoi chan tao cam giac dang chay
        dust_y = y + ts - max(3, unit)
        dust_phase = int(self._tick * 10) % 3
        for i in range(3):
            dx = (i * 3 + dust_phase) * unit // 2
            pygame.draw.rect(surface, (165, 138, 92),
                             (x + ts // 2 - dx, dust_y - i, max(2, unit), max(1, unit // 2)))

        # pixel outline sáng
        pygame.draw.rect(surface, C.PLAYER_OUT, (ox, oy, sprite_w, sprite_h + unit), 1)
