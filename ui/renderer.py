# ui/renderer.py - Renderer chinh (maze + HUD + controls)

from typing import Optional
import math

import pygame

import config as C
from core.game import Game, PlaybackState
from ui.combobox import Combobox


COMPARE_NONE_LABEL = "Không so sánh"


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.logo = None
        self._init_fonts()
        self._load_logo()
        self._init_widgets()
        self._tick = 0.0

    def _init_fonts(self):
        pygame.font.init()
        try:
            self.f_title = pygame.font.SysFont('Segoe UI', 22, bold=True)
            self.f_section = pygame.font.SysFont('Segoe UI', 14, bold=True)
            self.f_label = pygame.font.SysFont('Segoe UI', 12, bold=True)
            self.f_value = pygame.font.SysFont('Consolas', 13, bold=True)
            self.f_tiny = pygame.font.SysFont('Segoe UI', 11)
            self.f_log = pygame.font.SysFont('Consolas', 12, bold=True)
            self.f_cb = pygame.font.SysFont('Segoe UI', 12, bold=True)
            self.f_play = pygame.font.SysFont('Segoe UI', 17, bold=True)
        except Exception:
            self.f_title = pygame.font.Font(None, 24)
            self.f_section = pygame.font.Font(None, 16)
            self.f_label = pygame.font.Font(None, 14)
            self.f_value = pygame.font.Font(None, 15)
            self.f_tiny = pygame.font.Font(None, 13)
            self.f_log = pygame.font.Font(None, 14)
            self.f_cb = pygame.font.Font(None, 14)
            self.f_play = pygame.font.Font(None, 18)

    def _load_logo(self):
        try:
            self.logo = pygame.image.load(C.LOGO_PATH).convert_alpha()
        except (pygame.error, FileNotFoundError, AttributeError):
            self.logo = None

    def _init_widgets(self):
        pad = 12
        hx = C.MAP_W + pad
        cb_w = C.HUD_W - pad * 2

        self.CB_H = 30
        self.Y_LABEL1 = 60
        self.Y_CB1 = 76
        self.Y_LABEL2 = 116
        self.Y_CB2 = 132
        self.Y_LABEL3 = 116
        self.Y_CB3 = 132
        self.Y_PLAY = 176
        self.PLAY_H = 40
        self.Y_SIZE = 268
        self.Y_DIFFICULTY = 290

        group_options = [
            f"{g} ({info['vi_name']})"
            for g, info in C.ALGO_GROUPS.items()
        ]
        self.cb_group = Combobox(
            abs_x=hx, abs_y=self.Y_CB1,
            w=cb_w, h=self.CB_H,
            options=group_options,
            font=self.f_cb,
            selected_idx=0,
            on_change=self._on_group_changed,
            max_visible=5,
        )

        first_group = C.GROUP_NAMES[0]
        self.cb_algo = Combobox(
            abs_x=hx, abs_y=self.Y_CB2,
            w=(cb_w - 10) // 2, h=self.CB_H,
            options=self._algo_options(first_group),
            font=self.f_cb,
            selected_idx=0,
            max_visible=5,
        )
        self.cb_compare = Combobox(
            abs_x=hx + (cb_w + 10) // 2, abs_y=self.Y_CB3,
            w=(cb_w - 10) // 2, h=self.CB_H,
            options=self._compare_options(first_group),
            font=self.f_cb,
            selected_idx=0,
            max_visible=5,
        )
        size_options = [f"{n} x {n}" for n in C.GRID_OPTIONS]
        size_idx = C.GRID_OPTIONS.index(C.GRID_SIZE)
        self.cb_size = Combobox(
            abs_x=hx + cb_w - 116, abs_y=self.Y_SIZE,
            w=116, h=28,
            options=size_options,
            font=self.f_cb,
            selected_idx=size_idx,
            max_visible=4,
        )
        difficulty_idx = C.DIFFICULTY_NAMES.index(C.current_difficulty_name())
        self.cb_difficulty = Combobox(
            abs_x=hx + cb_w - 116, abs_y=self.Y_DIFFICULTY,
            w=116, h=20,
            options=C.DIFFICULTY_NAMES,
            font=self.f_cb,
            selected_idx=difficulty_idx,
            max_visible=3,
        )

        self.play_btn = pygame.Rect(hx, self.Y_PLAY, cb_w, self.PLAY_H)
        self.depth_btn = pygame.Rect(C.MAP_W + C.HUD_W - pad - 190, 17, 76, 24)
        self._group_idx = 0

    def _algo_options(self, group_name: str):
        info = C.ALGO_GROUPS.get(group_name, {})
        algos = info.get('algorithms', {})
        return [f"{k} - {v}" for k, v in algos.items()]

    def _compare_options(self, group_name: str):
        return [COMPARE_NONE_LABEL] + self._algo_options(group_name)

    def _algo_key(self) -> str:
        group = C.GROUP_NAMES[self._group_idx]
        keys = list(C.ALGO_GROUPS[group]['algorithms'].keys())
        idx = self.cb_algo.selected
        return keys[idx] if 0 <= idx < len(keys) else (keys[0] if keys else '')

    def _on_group_changed(self, idx: int):
        self._group_idx = idx
        group_name = C.GROUP_NAMES[idx]
        self.cb_algo.set_options(self._algo_options(group_name), selected_idx=0)
        self.cb_compare.set_options(self._compare_options(group_name), selected_idx=0)
        self.cb_algo.close()
        self.cb_compare.close()

    def get_selected_algo(self) -> str:
        return self._algo_key()

    def get_compare_algo(self) -> str:
        group = C.GROUP_NAMES[self._group_idx]
        keys = list(C.ALGO_GROUPS[group]['algorithms'].keys())
        idx = self.cb_compare.selected - 1
        return keys[idx] if 0 <= idx < len(keys) else ''

    def _selected_matrix_size(self) -> int:
        idx = max(0, min(self.cb_size.selected, len(C.GRID_OPTIONS) - 1))
        return C.GRID_OPTIONS[idx]

    def _selected_difficulty(self) -> str:
        idx = max(0, min(self.cb_difficulty.selected,
                         len(C.DIFFICULTY_NAMES) - 1))
        return C.DIFFICULTY_NAMES[idx]

    def handle_event(self, event: pygame.event.Event, game: Game) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            hdr1 = pygame.Rect(self.cb_group.abs_x, self.cb_group.abs_y,
                               self.cb_group.w, self.cb_group.h)
            drop1 = self.cb_group.get_dropdown_rect()
            hdr2 = pygame.Rect(self.cb_algo.abs_x, self.cb_algo.abs_y,
                               self.cb_algo.w, self.cb_algo.h)
            drop2 = self.cb_algo.get_dropdown_rect()
            hdr3 = pygame.Rect(self.cb_compare.abs_x, self.cb_compare.abs_y,
                               self.cb_compare.w, self.cb_compare.h)
            drop3 = self.cb_compare.get_dropdown_rect()
            hdr_size = pygame.Rect(self.cb_size.abs_x, self.cb_size.abs_y,
                                   self.cb_size.w, self.cb_size.h)
            drop_size = self.cb_size.get_dropdown_rect()
            hdr_diff = pygame.Rect(self.cb_difficulty.abs_x, self.cb_difficulty.abs_y,
                                   self.cb_difficulty.w, self.cb_difficulty.h)
            drop_diff = self.cb_difficulty.get_dropdown_rect()

            in_cb1 = hdr1.collidepoint(mx, my) or (drop1 and drop1.collidepoint(mx, my))
            in_cb2 = hdr2.collidepoint(mx, my) or (drop2 and drop2.collidepoint(mx, my))
            in_cb3 = hdr3.collidepoint(mx, my) or (drop3 and drop3.collidepoint(mx, my))
            in_size = (hdr_size.collidepoint(mx, my)
                       or (drop_size and drop_size.collidepoint(mx, my)))
            in_diff = (hdr_diff.collidepoint(mx, my)
                       or (drop_diff and drop_diff.collidepoint(mx, my)))

            if self.depth_btn.collidepoint(mx, my):
                self.cb_group.close()
                self.cb_algo.close()
                self.cb_compare.close()
                self.cb_size.close()
                self.cb_difficulty.close()
                game.cycle_alpha_beta_depth()
                return False

            if in_cb1:
                self.cb_algo.close()
                self.cb_compare.close()
                self.cb_size.close()
                self.cb_difficulty.close()
                self.cb_group.handle_event(event)
                return False
            if in_cb2:
                self.cb_group.close()
                self.cb_compare.close()
                self.cb_size.close()
                self.cb_difficulty.close()
                self.cb_algo.handle_event(event)
                return False
            if in_cb3:
                self.cb_group.close()
                self.cb_algo.close()
                self.cb_size.close()
                self.cb_difficulty.close()
                self.cb_compare.handle_event(event)
                return False
            if in_size:
                self.cb_group.close()
                self.cb_algo.close()
                self.cb_compare.close()
                self.cb_difficulty.close()
                changed = self.cb_size.handle_event(event)
                if changed:
                    game.resize_matrix(self._selected_matrix_size())
                return False
            if in_diff:
                self.cb_group.close()
                self.cb_algo.close()
                self.cb_compare.close()
                self.cb_size.close()
                changed = self.cb_difficulty.handle_event(event)
                if changed:
                    game.set_difficulty(self._selected_difficulty())
                return False

            self.cb_group.close()
            self.cb_algo.close()
            self.cb_compare.close()
            self.cb_size.close()
            self.cb_difficulty.close()
            if self.play_btn.collidepoint(mx, my):
                return True
            return False

        self.cb_group.handle_event(event)
        self.cb_algo.handle_event(event)
        self.cb_compare.handle_event(event)
        self.cb_size.handle_event(event)
        self.cb_difficulty.handle_event(event)
        return False

    def render(self, game: Game, dt: float):
        self._tick += dt
        self.screen.fill(C.BG_COLOR)
        self._draw_maze_area(game)
        self._draw_hud(game)
        self._draw_play_button(game)
        self.cb_difficulty.draw(self.screen)
        self.cb_size.draw(self.screen)
        self.cb_compare.draw(self.screen)
        self.cb_algo.draw(self.screen)
        self.cb_group.draw(self.screen)
        self._draw_victory_overlay(game)
        pygame.display.flip()

    def _draw_maze_area(self, game: Game):
        map_surf = self.screen.subsurface((0, 0, C.MAP_W, C.MAP_H))
        known_cells = None
        if game.current_algo == 'BFS-PO' and game.result and game.current_step:
            known_cells = game.current_step.extra.get('known_cells')
        game.maze.draw(
            map_surf,
            result=game.result,
            current_step=game.current_step_idx,
            player_pos=game.player_pos,
            player_trail=game.player_trail,
            known_cells=known_cells,
        )
        if game.race_mode and game.compare_result:
            game.maze.draw_race_agent(
                map_surf,
                game.result,
                game.current_step_idx,
                C.START_COLOR,
                "A",
                route_style="solid",
            )

            game.maze.draw_race_agent(
                map_surf,
                game.compare_result,
                game.compare_step_idx,
                C.PLAYER_COLOR,
                "B",
                route_style="dashed",
            )
        pygame.draw.rect(self.screen, C.HUD_BORDER, (0, 0, C.MAP_W, C.MAP_H), 2)

    def _draw_hud(self, game: Game):
        pad = 12
        panel = pygame.Surface((C.HUD_W, C.SCREEN_H))
        panel.fill(C.HUD_BG)
        pygame.draw.line(panel, C.HUD_BORDER, (0, 0), (0, C.SCREEN_H), 2)

        self._draw_header(panel, pad)
        self._draw_selector_card(panel, pad)
        self._draw_maze_card(panel, game, pad)
        self._draw_minimap_card(panel, game, pad)
        self._draw_status_card(panel, game, pad)
        self._draw_log_card(panel, game, pad)
        self._draw_progress_card(panel, game, pad)
        self._draw_controls_card(panel, pad)
        self._draw_message_bar(panel, game, pad)

        self.screen.blit(panel, (C.MAP_W, 0))

    def _draw_header(self, panel: pygame.Surface, pad: int):
        self._draw_logo(panel, pad, 12, 34)
        title = self.f_title.render("AI MAZE SOLVER", True, C.HUD_TITLE)
        panel.blit(title, (pad + 44, 13))
        algo_count = sum(len(info['algorithms']) for info in C.ALGO_GROUPS.values())
        subtitle = self.f_tiny.render(f"{C.current_theme_name()} theme | Treasure Maze AI {C.GRID_SIZE}x{C.GRID_SIZE} | {algo_count} thuat toan",
                                      True, C.HUD_MUTED)
        panel.blit(subtitle, (pad + 44, 37))
        _draw_chip(panel, self.f_tiny, f"AB d{C.ALPHA_BETA_DEPTH}", C.HUD_W - pad - 190, 17, C.MONSTER_GLOW)
        _draw_chip(panel, self.f_tiny, f"H: {C.current_theme_name()}", C.HUD_W - pad - 108, 17, C.HUD_TITLE)

    def _draw_logo(self, surface: pygame.Surface, x: int, y: int, size: int):
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.circle(surface, (248, 250, 255), rect.center, size // 2)
        pygame.draw.circle(surface, (30, 45, 130), rect.center, size // 2, 2)
        if self.logo:
            logo = pygame.transform.smoothscale(self.logo, (size - 4, size - 4))
            surface.blit(logo, (x + 2, y + 2))
        else:
            pygame.draw.circle(surface, C.GOAL_COLOR, rect.center, size // 5)
            pygame.draw.circle(surface, C.HUD_TITLE, rect.center, size // 3, 2)

    def _draw_selector_card(self, panel: pygame.Surface, pad: int):
        rect = pygame.Rect(pad - 2, 54, C.HUD_W - pad * 2 + 4, 174)
        _draw_card(panel, rect)
        _draw_label(panel, self.f_label, "Nhom thuat toan", pad, self.Y_LABEL1, C.HUD_TITLE)
        half = (C.HUD_W - pad * 2 - 10) // 2
        _draw_label(panel, self.f_label, "Thuat toan A (hien thi)", pad, self.Y_LABEL2, C.HUD_TITLE)
        _draw_label(panel, self.f_label, "Thuat toan B (tuy chon)", pad + half + 10, self.Y_LABEL3, C.HUD_TITLE)

        hint = self.f_tiny.render("Chon thuat toan roi nhan PLAY", True, C.HUD_MUTED)
        panel.blit(hint, (pad, self.Y_PLAY + self.PLAY_H + 1))

    def _draw_maze_card(self, panel: pygame.Surface, game: Game, pad: int):
        rect = pygame.Rect(pad - 2, 238, C.HUD_W - pad * 2 + 4, 72)
        _draw_card(panel, rect)
        _draw_section(panel, self.f_section, "Me cung", pad, 248)
        _draw_chip(panel, self.f_tiny, "Compass", pad + 95, 245, C.START_COLOR)
        _draw_chip(panel, self.f_tiny, "Treasure", pad + 190, 245, C.GOAL_COLOR)
        _draw_label(panel, self.f_label, "Matrix", pad + 380, 249, C.HUD_TITLE)
        _draw_label(panel, self.f_label, "Difficulty", pad + 380, 279, C.HUD_TITLE)
        tile_s = self.f_tiny.render(f"Tile {C.TILE_SIZE}px", True, C.HUD_MUTED)
        panel.blit(tile_s, (pad + 258, 297))
        # mini legend pixels
        lx, ly = pad, 282
        next_color = C.VIZ_UPCOMING_COLORS[0]
        for label, color in [("Wall", C.WALL_LIGHT), ("Trail", C.PLAYER_TRAIL_COLOR), ("Next", next_color), ("Visited", C.VIZ_VISITED), ("Path", C.VIZ_PATH), ("Player", C.PLAYER_COLOR)]:
            pygame.draw.rect(panel, color, (lx, ly+2, 10, 10), border_radius=2)
            txt = self.f_tiny.render(label, True, C.HUD_MUTED)
            panel.blit(txt, (lx+14, ly))
            lx += txt.get_width() + 42

    def _draw_minimap_card(self, panel: pygame.Surface, game: Game, pad: int):
        """Tiny overview map placed inside the maze info zone."""
        # use available blank region in Maze card, right side but below chips
        size = 54
        x = pad + 254
        y = 251
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(panel, (8, 13, 25), rect, border_radius=8)
        pygame.draw.rect(panel, (65, 100, 160), rect, 1, border_radius=8)
        pygame.draw.circle(panel, (*C.HUD_TITLE, 45), rect.center, size//2 - 4, 1)
        ang = self._tick * 2.8
        end = (rect.centerx + int(math.cos(ang) * (size//2-6)), rect.centery + int(math.sin(ang) * (size//2-6)))
        pygame.draw.line(panel, C.HUD_TITLE, rect.center, end, 1)
        rows, cols = game.maze.rows, game.maze.cols
        if rows <= 0 or cols <= 0:
            return
        cell_w = max(1, (size - 8) / cols)
        cell_h = max(1, (size - 8) / rows)
        ox, oy = x + 4, y + 4
        for r in range(rows):
            for c in range(cols):
                if game.maze.grid[r][c] == 0:
                    col = (36, 54, 92)
                else:
                    col = (13, 22, 38)
                rx = int(ox + c * cell_w); ry = int(oy + r * cell_h)
                rw = max(1, int(cell_w + 0.8)); rh = max(1, int(cell_h + 0.8))
                pygame.draw.rect(panel, col, (rx, ry, rw, rh))
        for rr, cc in game.player_trail:
            if not (0 <= rr < rows and 0 <= cc < cols):
                continue
            rx = int(ox + cc * cell_w)
            ry = int(oy + rr * cell_h)
            rw = max(1, int(cell_w + 0.8))
            rh = max(1, int(cell_h + 0.8))
            pygame.draw.rect(panel, C.PLAYER_TRAIL_COLOR, (rx, ry, rw, rh))
        def map_point(pos):
            rr, cc = pos
            px = int(ox + cc * cell_w + cell_w / 2)
            py = int(oy + rr * cell_h + cell_h / 2)
            return px, py

        def dot(pos, color, radius=3):
            px, py = map_point(pos)
            pulse = int(abs(math.sin(self._tick * 5)) * 2)
            pygame.draw.circle(panel, color, (px, py), radius + pulse)
            pygame.draw.circle(panel, C.WHITE, (px, py), max(1, radius-2))

        def compass_icon(pos):
            px, py = map_point(pos)
            pulse = int(abs(math.sin(self._tick * 5)) * 1)
            pygame.draw.circle(panel, (26, 44, 40), (px, py), 6 + pulse)
            pygame.draw.circle(panel, (232, 190, 88), (px, py), 5)
            pygame.draw.circle(panel, (230, 244, 216), (px, py), 3)
            pygame.draw.polygon(panel, (220, 48, 42), [(px, py - 5), (px - 2, py), (px, py + 1), (px + 2, py)])

        def chest_icon(pos):
            px, py = map_point(pos)
            pulse = int(abs(math.sin(self._tick * 5)) * 1)
            pygame.draw.circle(panel, (*C.GOAL_GLOW, 80), (px, py), 7 + pulse)
            pygame.draw.rect(panel, (32, 20, 8), (px - 6, py - 4, 12, 9), border_radius=2)
            pygame.draw.rect(panel, (138, 78, 28), (px - 5, py - 3, 10, 7), border_radius=1)
            pygame.draw.rect(panel, C.GOAL_COLOR, (px - 6, py, 12, 2))
            pygame.draw.rect(panel, (255, 238, 154), (px - 2, py - 1, 4, 4), border_radius=1)

        compass_icon(game.maze.start)
        chest_icon(game.maze.goal)
        dot(game.player_pos, C.PLAYER_COLOR, 2)

    def _draw_status_card(self, panel: pygame.Surface, game: Game, pad: int):
        rect = pygame.Rect(pad - 2, 320, C.HUD_W - pad * 2 + 4, 220)
        _draw_card(panel, rect)

        result = game.result
        compare = game.compare_result
        status_text, status_color = self._status_info(game)

        _draw_section(panel, self.f_section, "So sanh trong cung nhom", pad, 330)
        _draw_pill(panel, self.f_tiny, status_text, C.HUD_W - pad - 92, 328, 92, status_color)

        algo_a = game.current_algo or "--"
        algo_b = game.compare_algo or "--"
        group = C.get_algo_group(algo_a) if game.current_algo else C.GROUP_NAMES[self._group_idx]
        group_s = self.f_tiny.render(group, True, C.HUD_MUTED)
        panel.blit(group_s, (pad, 352))

        table = pygame.Rect(pad, 374, C.HUD_W - pad * 2, 154)
        _draw_compare_table(panel, self.f_label, self.f_value, self.f_tiny,
                            table, algo_a, result, algo_b, compare, game)
        self._draw_race_bars(panel, game, pad, 531)

    def _draw_log_card(self, panel: pygame.Surface, game: Game, pad: int):
        rect = pygame.Rect(pad - 2, 548, C.HUD_W - pad * 2 + 4, 82)
        _draw_card(panel, rect)
        _draw_section(panel, self.f_section, "Log duong di truc quan", pad, 558)

        result = game.result
        step = game.current_step
        if result and step:
            path_log = result.path if result.found and game.playback_state == PlaybackState.DONE else step.path_so_far
            status = "FINAL PATH" if game.playback_state == PlaybackState.DONE and result.found else "LIVE TRACE"
            _draw_pill(panel, self.f_tiny, status, C.HUD_W - pad - 108, 556, 108, C.VIZ_PATH)
            y = _draw_path_log(panel, self.f_log, path_log, pad, 580, C.HUD_W - pad * 2, 614)
            desc = step.description or ""

            if game.current_algo == "Alpha-Beta":
                extra = step.extra
                turn = extra.get("turn", "--")
                status = extra.get("status", "--")
                score = extra.get("score", 0)
                nodes = extra.get("nodes", 0)
                prunes = extra.get("prunes", 0)
                cache_hits = extra.get("cache_hits", 0)
                loop = " | LOOP" if extra.get("loop_detected") else ""

                desc = (
                    f"{turn}/{status}{loop} | d={extra.get('depth', '--')} | "
                    f"score={score:.1f} | nodes={nodes} | "
                    f"prunes={prunes} | cache={cache_hits} | "
                    f"Monster={extra.get('monster_pos')}"
                )
            elif game.current_algo == "Forward Checking":
                extra = step.extra
                removed = extra.get("removed_values", extra.get("restored_values", set()))
                future = extra.get("future_domain", [])
                var = extra.get("var", "--")
                value = extra.get("value", extra.get("removed_assignment", "--"))
                h = extra.get("h", "--")
                desc = (
                    f"{extra.get('mode', '--')} | {var}={value} | "
                    f"removed={len(removed)} | next_domain={len(future)} | "
                    f"h={h} | {extra.get('reason', '')}"
                )

            _draw_wrapped_limited(
                panel,
                self.f_tiny,
                desc,
                pad,
                C.HUD_W - pad * 2,
                y + 3,
                C.HUD_MUTED,
                max_lines=1
            )
        else:
            text = self.f_tiny.render("Chua co log. Hay chon thuat toan va nhan PLAY.", True, C.HUD_MUTED)
            panel.blit(text, (pad, 582))

    def _draw_progress_card(self, panel: pygame.Surface, game: Game, pad: int):
        rect = pygame.Rect(pad - 2, 634, C.HUD_W - pad * 2 + 4, 36)
        _draw_card(panel, rect)
        label = self.f_label.render("Tien do", True, C.HUD_TITLE)
        panel.blit(label, (pad, 642))
        pct = int(game.progress * 100)
        pct_s = self.f_label.render(f"{pct}%", True, C.HUD_TEXT)
        panel.blit(pct_s, (C.HUD_W - pad - pct_s.get_width(), 642))

        bar = pygame.Rect(pad, 656, C.HUD_W - pad * 2, 9)
        pygame.draw.rect(panel, (21, 25, 43), bar, border_radius=4)
        fill = int(bar.w * game.progress)
        if fill > 0:
            color = C.get_algo_color(game.current_algo) if game.current_algo else C.HUD_TITLE
            pygame.draw.rect(panel, color, (bar.x, bar.y, fill, bar.h), border_radius=4)
        pygame.draw.rect(panel, C.HUD_BORDER, bar, 1, border_radius=4)

    def _draw_race_bars(self, panel: pygame.Surface, game: Game, pad: int, y: int):
        if not game.result or not game.compare_result:
            return

        w = (C.HUD_W - pad * 2 - 20) // 2

        a_pct = game.progress
        b_pct = game.compare_progress if game.race_mode else (1.0 if game.compare_result else 0.0)

        items = [
            ("A " + (game.current_algo or "--"), a_pct, C.START_COLOR),
            ("B " + (game.compare_algo or "--"), b_pct, C.PLAYER_COLOR),
        ]

        for idx, (name, pct, col) in enumerate(items):
            x = pad + idx * (w + 20)

            rb = pygame.Rect(x, y, w, 7)
            pygame.draw.rect(panel, (20, 24, 42), rb, border_radius=4)

            fill = int(rb.w * max(0, min(1, pct)))

            if fill > 0:
                pygame.draw.rect(panel, col, (rb.x, rb.y, fill, rb.h), border_radius=4)

                runner_x = rb.x + fill
                pygame.draw.circle(panel, col, (runner_x, rb.centery), 5)
                pygame.draw.circle(panel, C.WHITE, (runner_x, rb.centery), 2)

            pygame.draw.rect(panel, C.HUD_BORDER, rb, 1, border_radius=4)

    def _draw_controls_card(self, panel: pygame.Surface, pad: int):
        rect = pygame.Rect(pad - 2, 674, C.HUD_W - pad * 2 + 4, 24)
        _draw_card(panel, rect)

        controls = [
            ("Space", "Pause"),
            ("<- / ->", "Step"),
            ("R", "Maze moi"),
            ("T", "Toc do"),
            ("H", "Theme"),
            ("M", "Race"),
            ("P", "Preview"),
            ("Y", f"AB d{C.ALPHA_BETA_DEPTH}"),
            ("Esc", "Menu"),
        ]
        x = pad
        y = 677
        for key, desc in controls:
            chip_w = max(42, self.f_tiny.render(key, True, C.HUD_TEXT).get_width() + 14)
            _draw_small_key(panel, self.f_tiny, key, x, y, chip_w)
            ds = self.f_tiny.render(desc, True, C.HUD_MUTED)
            panel.blit(ds, (x + chip_w + 4, y + 3))
            x += chip_w + ds.get_width() + 16
            if x > C.HUD_W - 78:
                break

    def _draw_message_bar(self, panel: pygame.Surface, game: Game, pad: int):
        msg_y = C.SCREEN_H - 20
        pygame.draw.rect(panel, (10, 12, 22), (0, msg_y, C.HUD_W, 20))
        pygame.draw.line(panel, C.HUD_BORDER, (0, msg_y), (C.HUD_W, msg_y))
        msg = _clip_surface(self.f_tiny, game.message, game.message_color, C.HUD_W - pad * 2)
        panel.blit(msg, (pad, msg_y + 4))

    def _status_info(self, game: Game):
        mapping = {
            PlaybackState.RUNNING: ("DANG CHAY", (55, 210, 115)),
            PlaybackState.PAUSED: ("TAM DUNG", C.GOAL_COLOR),
            PlaybackState.DONE: ("HOAN THANH", C.START_COLOR),
            PlaybackState.IDLE: ("CHUA CHAY", (115, 130, 165)),
        }
        return mapping.get(game.playback_state, ("--", C.HUD_TEXT))

    def _draw_play_button(self, game: Game):
        mx, my = pygame.mouse.get_pos()
        hover = self.play_btn.collidepoint(mx, my)
        running = game.playback_state == PlaybackState.RUNNING

        bg = C.PLAY_HOVER if hover else C.PLAY_BG
        border = C.PLAY_BORDER if not running else C.HUD_TITLE
        pygame.draw.rect(self.screen, bg, self.play_btn, border_radius=7)
        pygame.draw.rect(self.screen, border, self.play_btn, 2, border_radius=7)

        icon_x = self.play_btn.x + 86
        icon_y = self.play_btn.centery
        if running:
            pygame.draw.rect(self.screen, C.WHITE, (icon_x - 5, icon_y - 8, 4, 16), border_radius=1)
            pygame.draw.rect(self.screen, C.WHITE, (icon_x + 3, icon_y - 8, 4, 16), border_radius=1)
            label = "PAUSE"
        else:
            pygame.draw.polygon(self.screen, C.WHITE,
                                [(icon_x - 4, icon_y - 8), (icon_x - 4, icon_y + 8), (icon_x + 9, icon_y)])
            label = "PLAY"

        ts = self.f_play.render(label, True, C.WHITE)
        self.screen.blit(ts, (self.play_btn.centerx - ts.get_width() // 2 + 12,
                              self.play_btn.centery - ts.get_height() // 2))


    def _draw_victory_overlay(self, game: Game):
        if game.playback_state != PlaybackState.DONE or not game.result:
            return
        # Cinematic translucent overlay only when algorithm finished
        overlay = pygame.Surface((C.MAP_W, C.MAP_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        self.screen.blit(overlay, (0, 0))

        w, h = 390, 210
        x = (C.MAP_W - w) // 2
        y = (C.MAP_H - h) // 2
        rect = pygame.Rect(x, y, w, h)
        # glow backplate
        glow = pygame.Surface((w + 60, h + 60), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*C.VIZ_PATH, 48), (0, 0, w + 60, h + 60), border_radius=30)
        self.screen.blit(glow, (x - 30, y - 30))
        _draw_card(self.screen, rect)
        pygame.draw.rect(self.screen, C.VIZ_PATH if game.result.found else C.VIZ_BACKTRACK, rect, 2, border_radius=14)

        caught = (
            game.current_algo == 'Alpha-Beta'
            and game.result.steps
            and game.result.steps[-1].extra.get('caught')
        )
        title = "TREASURE FOUND" if game.result.found else "CAUGHT" if caught else "NO PATH FOUND"
        color = C.GOAL_COLOR if game.result.found else C.VIZ_BACKTRACK
        title_s = self.f_title.render(title, True, color)
        self.screen.blit(title_s, (rect.centerx - title_s.get_width() // 2, y + 22))

        # confetti / sparks
        for i in range(28):
            ang = self._tick * 2 + i * 0.73
            px = rect.centerx + int(math.cos(ang) * (70 + (i % 5) * 18))
            py = y + 60 + int(math.sin(ang * 1.3) * (22 + (i % 4) * 8))
            col = [C.GOAL_COLOR, C.VIZ_PATH, C.PLAYER_COLOR, C.START_COLOR][i % 4]
            pygame.draw.rect(self.screen, col, (px, py, 4, 4), border_radius=1)

        result = game.result
        lines = [
            ("Algorithm", game.current_algo or "--", C.HUD_TITLE),
            ("Path", f"{result.path_length} bước" if result.found else "N/A", C.VIZ_PATH),
            ("Visited", f"{result.total_visited} ô", C.START_COLOR),
            ("Time", f"{result.elapsed_ms:.2f} ms", C.GOAL_COLOR),
            ("Memory", f"{result.memory_kb:.1f} KB", C.PLAYER_COLOR),
        ]
        yy = y + 72
        for label, value, col in lines:
            ls = self.f_label.render(label, True, C.HUD_MUTED)
            vs = self.f_value.render(value, True, col)
            self.screen.blit(ls, (x + 54, yy))
            self.screen.blit(vs, (x + w - 54 - vs.get_width(), yy))
            yy += 22

        hint = self.f_tiny.render("Nhấn R để tạo mê cung mới • Space để chạy lại/tạm dừng", True, C.HUD_MUTED)
        self.screen.blit(hint, (rect.centerx - hint.get_width() // 2, y + h - 30))


def _draw_card(surface, rect: pygame.Rect):
    # Glassmorphism + hover glow. Với HUD subsurface, mouse x cần trừ MAP_W.
    mx, my = pygame.mouse.get_pos()
    local = (mx - C.MAP_W, my) if mx >= C.MAP_W else (mx, my)
    hover = rect.collidepoint(local)
    shadow = rect.move(0, 4 if hover else 3)
    pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=13)
    base = (16, 24, 44) if hover else (12, 18, 34)
    inner = (22, 38, 68) if hover else (18, 30, 54)
    pygame.draw.rect(surface, base, rect, border_radius=12)
    pygame.draw.rect(surface, inner, rect.inflate(-4, -4), border_radius=10)
    border = C.HUD_TITLE if hover else (52, 82, 140)
    pygame.draw.rect(surface, border, rect, 2 if hover else 1, border_radius=12)
    pygame.draw.line(surface, (120, 190, 250) if hover else (95, 155, 220), (rect.x + 10, rect.y + 1), (rect.right - 10, rect.y + 1), 1)
    pygame.draw.line(surface, (20, 30, 52), (rect.x + 10, rect.bottom - 2), (rect.right - 10, rect.bottom - 2), 1)


def _draw_label(surface, font, text, x, y, color):
    surface.blit(font.render(text, True, color), (x, y))


def _draw_section(surface, font, text, x, y):
    s = font.render(text, True, C.HUD_TITLE)
    surface.blit(s, (x, y))


def _draw_kv(surface, f_label, f_value, label, val, val_col, pad, hud_w, y):
    ls = f_label.render(label, True, C.HUD_TEXT)
    vs = _clip_surface(f_value, str(val), val_col, hud_w - pad * 2 - 88)
    surface.blit(ls, (pad, y))
    surface.blit(vs, (hud_w - vs.get_width() - pad, y))


def _draw_chip(surface, font, text, x, y, color):
    text_s = font.render(text, True, color)
    rect = pygame.Rect(x, y, text_s.get_width() + 16, 24)
    pygame.draw.rect(surface, (20, 24, 43), rect, border_radius=6)
    pygame.draw.rect(surface, color, rect, 1, border_radius=6)
    surface.blit(text_s, (x + 8, y + 6))


def _draw_pill(surface, font, text, x, y, w, color):
    rect = pygame.Rect(x, y, w, 21)
    pygame.draw.rect(surface, (18, 28, 34), rect, border_radius=10)
    pygame.draw.rect(surface, color, rect, 1, border_radius=10)
    s = _clip_surface(font, text, color, w - 10)
    surface.blit(s, (rect.centerx - s.get_width() // 2, rect.centery - s.get_height() // 2))


def _draw_metric(surface, f_label, f_value, label, value, color, x, y, w):
    rect = pygame.Rect(x, y, w, 28)
    pygame.draw.rect(surface, (18, 21, 38), rect, border_radius=6)
    pygame.draw.line(surface, color, (x + 6, y + 5), (x + 6, y + 23), 2)
    ls = f_label.render(label, True, C.HUD_MUTED)
    vs = _clip_surface(f_value, str(value), color, w - 52)
    surface.blit(ls, (x + 12, y + 4))
    surface.blit(vs, (x + w - vs.get_width() - 8, y + 12))


def _draw_compare_table(surface, f_label, f_value, f_tiny, rect,
                        algo_a, result_a, algo_b, result_b, game):
    col_metric = rect.x
    col_a = rect.x + 118
    col_b = rect.x + 332
    col_w = 204
    row_h = 20

    pygame.draw.rect(surface, (17, 20, 36), rect, border_radius=6)
    pygame.draw.rect(surface, (39, 50, 85), rect, 1, border_radius=6)

    headers = [
        ("Chi so", col_metric, 110, C.HUD_TITLE),
        (f"A live: {algo_a}", col_a, col_w, C.START_COLOR),
        (f"B {'live' if game.race_mode and result_b else 'final'}: {algo_b}", col_b, col_w, C.PLAYER_COLOR),
    ]
    for text, x, w, color in headers:
        s = _clip_surface(f_label, text, color, w - 8)
        surface.blit(s, (x + 6, rect.y + 8))

    pygame.draw.line(surface, (44, 56, 92), (rect.x + 6, rect.y + 30),
                     (rect.right - 6, rect.y + 30))
    pygame.draw.line(surface, (35, 45, 78), (col_a - 8, rect.y + 5),
                     (col_a - 8, rect.bottom - 6))
    pygame.draw.line(surface, (35, 45, 78), (col_b - 8, rect.y + 5),
                     (col_b - 8, rect.bottom - 6))

    rows = [
        ("Cost", _metric_cost, True),
        ("Time", _metric_time, True),
        ("Memory", _metric_memory, True),
        ("Steps", _metric_steps, True),
        ("Visited", _metric_visited, True),
        ("Found", _metric_found, False),
    ]

    y = rect.y + 38
    a_is_final = game.playback_state == PlaybackState.DONE or game.progress >= 1.0
    b_is_live = bool(game.race_mode and result_b)
    b_is_final = (
        game.playback_state == PlaybackState.DONE
        or (b_is_live and game.compare_progress >= 1.0)
        or (result_b and not b_is_live)
    )
    for idx, (label, getter, lower_is_better) in enumerate(rows):
        if idx % 2 == 1:
            pygame.draw.rect(surface, (14, 17, 31),
                             (rect.x + 4, y - 2, rect.w - 8, row_h), border_radius=4)

        label_s = f_label.render(label, True, C.HUD_TEXT)
        surface.blit(label_s, (col_metric + 8, y))

        raw_a, text_a = _metric_live(
            label, getter, result_a, game.current_step,
            game.progress, game.current_step_idx
        )
        if b_is_live:
            raw_b, text_b = _metric_live(
                label, getter, result_b, game.compare_current_step,
                game.compare_progress, game.compare_step_idx
            )
        else:
            raw_b, text_b = getter(result_b)

        if a_is_final and b_is_final:
            col_a_color, col_b_color = _compare_colors(raw_a, raw_b, lower_is_better)
        else:
            col_a_color = C.START_COLOR
            col_b_color = C.PLAYER_COLOR if b_is_live else C.HUD_TEXT

        a_s = _clip_surface(f_value, text_a, col_a_color, col_w - 12)
        b_s = _clip_surface(f_value, text_b, col_b_color, col_w - 12)
        surface.blit(a_s, (col_a + 6, y))
        surface.blit(b_s, (col_b + 6, y))
        y += row_h


def _compare_colors(a, b, lower_is_better):
    neutral = C.HUD_TEXT
    best = C.START_COLOR
    if a is None or b is None or a == b:
        return neutral, neutral
    if isinstance(a, bool) or isinstance(b, bool):
        return (best if a else neutral), (best if b else neutral)
    a_better = a < b if lower_is_better else a > b
    return (best if a_better else neutral), (best if not a_better else neutral)


def _metric_live(label, final_getter, result, step, progress, step_idx):
    if not result:
        return None, "--"

    progress = max(0.0, min(1.0, progress))
    done = progress >= 1.0
    if done:
        return final_getter(result)

    if label == "Cost":
        if not step or not step.path_so_far:
            return None, "--"
        cost = max(0, len(step.path_so_far) - 1)
        return cost, str(cost)
    if label == "Time":
        live_ms = result.elapsed_ms * progress
        return live_ms, f"{live_ms:.2f} ms"
    if label == "Memory":
        if not step:
            return None, "--"
        live_ratio = 0.0
        denom = max(1, result.total_visited + len(result.steps))
        live_ratio = min(1.0, (len(step.visited) + step_idx) / denom)
        live_kb = result.memory_kb * live_ratio
        return live_kb, f"{live_kb:.1f} KB"
    if label == "Steps":
        return step_idx, f"{step_idx}/{result.total_steps}"
    if label == "Visited":
        visited = len(step.visited) if step else 0
        return visited, str(visited)
    if label == "Found":
        found = step.current == result.goal if step else False
        return found, "YES" if found else "RUN"

    return final_getter(result)


def _metric_cost(result):
    if not result:
        return None, "--"
    return result.path_cost if result.found else None, str(result.path_cost) if result.found else "N/A"


def _metric_time(result):
    if not result:
        return None, "--"
    return result.elapsed_ms, f"{result.elapsed_ms:.2f} ms"


def _metric_memory(result):
    if not result:
        return None, "--"
    return result.memory_kb, f"{result.memory_kb:.1f} KB"


def _metric_steps(result):
    if not result:
        return None, "--"
    return result.total_steps, str(result.total_steps)


def _metric_visited(result):
    if not result:
        return None, "--"
    return result.total_visited, str(result.total_visited)


def _metric_found(result):
    if not result:
        return None, "--"
    return result.found, "YES" if result.found else "NO"


def _draw_small_key(surface, font, text, x, y, w):
    rect = pygame.Rect(x, y, w, 18)
    pygame.draw.rect(surface, (21, 26, 46), rect, border_radius=5)
    pygame.draw.rect(surface, (55, 70, 115), rect, 1, border_radius=5)
    s = font.render(text, True, C.HUD_TEXT)
    surface.blit(s, (rect.centerx - s.get_width() // 2, rect.centery - s.get_height() // 2))


def _clip_surface(font, text, color, max_w):
    s = font.render(text, True, color)
    if s.get_width() <= max_w:
        return s
    clipped = text
    while clipped and font.render(clipped + "...", True, color).get_width() > max_w:
        clipped = clipped[:-1]
    return font.render((clipped or "") + "...", True, color)


def _draw_wrapped_limited(surface, font, text, x, max_w, y, color, max_lines=2) -> int:
    lines = []
    cur = ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if font.render(test, True, color).get_width() > max_w and cur:
            lines.append(cur)
            cur = word
            if len(lines) >= max_lines:
                break
        else:
            cur = test
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and len(" ".join(text.split())) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".") + "..."
    for line in lines:
        surface.blit(font.render(line, True, color), (x, y))
        y += font.get_height() + 1
    return y


def _draw_path_log(surface, font, path, x, y, max_w, max_y) -> int:
    """Log toa do dang chip: S -> step gan nhat -> Current, de nhin hon chuoi dai."""
    if not path:
        s = font.render("Chua co toa do duong di.", True, C.HUD_MUTED)
        surface.blit(s, (x, y))
        return y + s.get_height() + 1

    # chi hien thi cac moc quan trong: Start, vai buoc cuoi, Current
    visible_tail = 6
    tail_start = max(0, len(path) - visible_tail)
    items = []
    if tail_start > 0:
        items.append(("S", path[0], C.START_COLOR))
        items.append(("...", None, C.HUD_DIM))
    for idx in range(tail_start, len(path)):
        label = "NOW" if idx == len(path) - 1 else f"{idx:02d}"
        color = C.VIZ_CURRENT if idx == len(path) - 1 else C.VIZ_PATH
        items.append((label, path[idx], color))

    cx = x
    cy = y
    line_h = font.get_height() + 8
    for label, pos, color in items:
        text = label if pos is None else f"{label} ({pos[0]},{pos[1]})"
        tw = font.render(text, True, color).get_width()
        w = min(tw + 16, max_w)
        if cx + w > x + max_w:
            cx = x
            cy += line_h
            if cy + line_h > max_y:
                break
        rect = pygame.Rect(cx, cy, w, line_h - 3)
        pygame.draw.rect(surface, (16, 25, 43), rect, border_radius=6)
        pygame.draw.rect(surface, color, rect, 1, border_radius=6)
        txt = _clip_surface(font, text, color, w - 10)
        surface.blit(txt, (rect.x + 8, rect.y + 4))
        cx += w + 7

        if label != "NOW" and pos is not None and cx + 18 < x + max_w:
            arrow = font.render("→", True, C.HUD_MUTED)
            surface.blit(arrow, (cx, cy + 4))
            cx += arrow.get_width() + 7

    # dong tong ket nho
    summary = f"Tong node tren trace: {len(path)} | Current: {path[-1]}"
    sy = min(max_y, cy + line_h)
    if sy + font.get_height() <= max_y + 10:
        surface.blit(_clip_surface(font, summary, C.GOLD_COLOR, max_w), (x, sy))
        return sy + font.get_height()
    return cy + line_h
