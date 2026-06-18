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
            pygame.draw.line(wall, (8, 13, 28), (ts//4, ts//3+2), (ts//4+max(2,ts//8), ts//3+2), 1)
            pygame.draw.line(wall, (118, 170, 240), (ts//2+1, 3), (ts//2+max(2,ts//6), 3), 1)

        # FLOOR: lát gạch tối có viền neon nhẹ
        floor = pygame.Surface((ts, ts), pygame.SRCALPHA)
        floor.fill(C.FLOOR_COLOR)
        pygame.draw.rect(floor, C.FLOOR_EDGE, (0, 0, ts, ts), 1)
        if ts >= 10:
            pygame.draw.line(floor, C.FLOOR_LIGHT, (1, 1), (ts - 2, 1), 1)
            pygame.draw.line(floor, C.FLOOR_LIGHT, (1, 1), (1, ts - 2), 1)
            pygame.draw.line(floor, (7, 12, 22), (1, ts - 2), (ts - 2, ts - 2), 1)
            pygame.draw.line(floor, (7, 12, 22), (ts - 2, 1), (ts - 2, ts - 2), 1)
        if ts >= 16:
            # pattern viên gạch sàn 2x2 + highlight từng góc
            half = ts // 2
            pygame.draw.line(floor, (12, 26, 47), (half, 2), (half, ts - 3), 1)
            pygame.draw.line(floor, (12, 26, 47), (2, half), (ts - 3, half), 1)
            pygame.draw.rect(floor, C.FLOOR_HILITE, (3, 3, half - 5, half - 5), 1)
            pygame.draw.rect(floor, (8, 17, 31), (half + 2, half + 2, half - 5, half - 5), 1)
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
             known_cells: Set[Tuple[int, int]] = None):
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

        # 2. Algorithm visualization overlay
        if result and result.steps and current_step > 0:
            step_idx = min(current_step - 1, len(result.steps) - 1)
            self._draw_viz(surface, result.steps[step_idx], result, current_step, ts)

        # 3. Start & Goal markers
        self._draw_start_goal(surface, ts)

        # 4. Player sprite: khi thuat toan dang chay, nhan vat di theo node hien tai
        actor_pos = player_pos
        if result and result.steps and current_step > 0:
            step_idx = min(current_step - 1, len(result.steps) - 1)
            if result.steps[step_idx].current:
                actor_pos = result.steps[step_idx].current
        if actor_pos:
            self._draw_player(surface, actor_pos, ts)

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

    def _draw_viz(self, surface: pygame.Surface, step: Step,
                  result: PathResult, current_step: int, ts: int):
        is_done = current_step >= len(result.steps)
        pulse = int(45 + 35 * abs(math.sin(self._tick * 5)))

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
            rect = pygame.Rect(c * ts + 2, r * ts + 2, ts - 4, ts - 4)
            self._draw_cell_overlay(surface, r, c, C.VIZ_CURRENT, 70 + pulse, inset=2, glow=True)
            pygame.draw.rect(surface, C.WHITE, rect, 2, border_radius=5)
            pygame.draw.rect(surface, C.VIZ_PATH, rect.inflate(-6, -6), 2, border_radius=4)

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

    def _draw_start_goal(self, surface: pygame.Surface, ts: int):
        """Start = animated portal, Goal = glowing trophy/star marker."""
        glow_a = int(120 + math.sin(self._tick * 3.2) * 50)
        font = self._get_marker_font()

        sr, sc = self.start
        sx, sy = sc * ts + ts // 2, sr * ts + ts // 2
        self._draw_portal(surface, sx, sy, ts, C.START_COLOR, C.START_GLOW, label='S')

        gr, gc = self.goal
        gx, gy = gc * ts + ts // 2, gr * ts + ts // 2
        goal_s = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
        pygame.draw.circle(goal_s, (*C.GOAL_GLOW, min(230, glow_a)), (ts, ts), max(8, ts // 2 + 7))
        pygame.draw.circle(goal_s, (*C.GOAL_COLOR, 60), (ts, ts), max(5, ts // 2 - 1), 2)
        surface.blit(goal_s, (gx - ts, gy - ts))
        self._draw_pixel_trophy(surface, gc * ts, gr * ts, ts)
        if ts >= 22:
            lbl_g = font.render('GOAL', True, C.BLACK)
            tag = pygame.Rect(gx - lbl_g.get_width() // 2 - 4, gy + ts // 5, lbl_g.get_width() + 8, lbl_g.get_height() + 3)
            pygame.draw.rect(surface, C.GOAL_GLOW, tag, border_radius=4)
            pygame.draw.rect(surface, C.BLACK, tag, 1, border_radius=4)
            surface.blit(lbl_g, (tag.x + 4, tag.y + 1))

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
        font = self._get_marker_font()
        lbl = font.render(label, True, C.BLACK)
        surface.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))

    def _draw_pixel_trophy(self, surface, x: int, y: int, ts: int):
        unit = max(1, ts // 8)
        cx = x + ts // 2
        top = y + unit
        # dark backing
        pygame.draw.rect(surface, (30, 20, 6), (cx - 3*unit, top + unit, 6*unit, 4*unit), border_radius=3)
        # cup body
        pygame.draw.rect(surface, C.GOAL_COLOR, (cx - 2*unit, top + unit, 4*unit, 3*unit))
        pygame.draw.rect(surface, (255, 245, 160), (cx - unit, top + unit, unit, unit))
        # handles
        pygame.draw.rect(surface, C.GOAL_COLOR, (cx - 3*unit, top + 2*unit, unit, 2*unit))
        pygame.draw.rect(surface, C.GOAL_COLOR, (cx + 2*unit, top + 2*unit, unit, 2*unit))
        pygame.draw.rect(surface, (80, 50, 10), (cx - 3*unit, top + 3*unit, unit, unit))
        pygame.draw.rect(surface, (80, 50, 10), (cx + 2*unit, top + 3*unit, unit, unit))
        # stem/base
        pygame.draw.rect(surface, C.GOAL_GLOW, (cx - unit, top + 4*unit, 2*unit, unit))
        pygame.draw.rect(surface, C.GOAL_COLOR, (cx - 2*unit, top + 5*unit, 4*unit, unit))
        # star sparkle above
        sp_y = y + max(2, unit // 2)
        pygame.draw.polygon(surface, C.WHITE, [(cx, sp_y), (cx+unit//2+1, sp_y+unit), (cx+unit+1, sp_y+unit), (cx+unit//2+1, sp_y+unit+1), (cx, sp_y+2*unit), (cx-unit//2-1, sp_y+unit+1), (cx-unit-1, sp_y+unit), (cx-unit//2-1, sp_y+unit)])
        pygame.draw.rect(surface, (35, 25, 8), (cx - 2*unit, top + unit, 4*unit, 5*unit), 1)

    # ── Player sprite ────────────────────────────────────────

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

        skin = (255, 214, 172)
        hair = (42, 28, 18)
        shirt = (55, 175, 255)
        shirt_dark = (20, 95, 175)
        pants = (52, 62, 84)
        shoe = (18, 22, 32)
        outline = (5, 10, 18)

        def px(col, row, w, h, color):
            pygame.draw.rect(surface, color, (ox + col * unit, oy + row * unit, w * unit, h * unit))

        # outline bóng nhỏ
        px(2, 0, 4, 1, outline)
        px(1, 1, 6, 3, outline)
        px(1, 4, 6, 3, outline)
        px(1, 7, 2, 2, outline)
        px(5, 7, 2, 2, outline)

        # head + hair
        px(2, 1, 4, 3, skin)
        px(2, 0, 4, 1, hair)
        px(1, 1, 1, 2, hair)
        px(5, 1, 1, 1, hair)
        # eyes
        px(3, 2, 1, 1, outline)
        px(5, 2, 1, 1, outline)

        # body
        px(2, 4, 4, 3, shirt)
        px(3, 4, 2, 1, (120, 225, 255))
        px(2, 6, 4, 1, shirt_dark)

        # arms swing
        if frame == 0:
            px(1, 4, 1, 3, skin)
            px(6, 4, 1, 2, skin)
            px(2, 7, 1, 2, pants)
            px(5, 7, 1, 2, pants)
            px(1, 9, 2, 1, shoe)
            px(5, 9, 2, 1, shoe)
        else:
            px(1, 4, 1, 2, skin)
            px(6, 4, 1, 3, skin)
            px(2, 7, 1, 2, pants)
            px(5, 7, 1, 2, pants)
            px(2, 9, 2, 1, shoe)
            px(4, 9, 2, 1, shoe)

        # bong/hat bui pixel duoi chan tao cam giac dang chay
        dust_y = y + ts - max(3, unit)
        dust_phase = int(self._tick * 10) % 3
        for i in range(3):
            dx = (i * 3 + dust_phase) * unit // 2
            pygame.draw.rect(surface, (115, 225, 255),
                             (x + ts // 2 - dx, dust_y - i, max(2, unit), max(1, unit // 2)))

        # pixel outline sáng
        pygame.draw.rect(surface, C.PLAYER_OUT, (ox, oy, sprite_w, sprite_h + unit), 1)
