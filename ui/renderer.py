# ui/renderer.py — Renderer chinh (HUD + Combobox + Play)
"""
Thu tu ve (z-order) de tranh che dropdown:
  1. Maze area
  2. HUD background panel
  3. Nut Play
  4. cb_algo.draw()  <- ve truoc (z-duoi)
  5. cb_group.draw() <- ve SAU (dropdown cb1 de len cb2)

FIX combobox bug:
  - CB1 dropdown cat bet nam tren CB2 header
  - Giai phap: khi CB1 mo, KHONG chuyen event cho CB2
  - Khi CB2 mo, KHONG chuyen event cho CB1
  - Them: tang khoang cach Y giua CB1 va CB2
"""

import pygame
import math
from typing import Optional
import config as C
from core.game import Game, PlaybackState
from ui.combobox import Combobox


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._init_fonts()
        self._init_widgets()

    # ── Font ──────────────────────────────────────────────────────────────

    def _init_fonts(self):
        pygame.font.init()
        try:
            self.f_title   = pygame.font.SysFont('Segoe UI', 18, bold=True)
            self.f_section = pygame.font.SysFont('Segoe UI', 13, bold=True)
            self.f_label   = pygame.font.SysFont('Segoe UI', 12, bold=True)
            self.f_value   = pygame.font.SysFont('Segoe UI', 12)
            self.f_tiny    = pygame.font.SysFont('Segoe UI', 11)
            self.f_cb      = pygame.font.SysFont('Segoe UI', 12)
            self.f_play    = pygame.font.SysFont('Segoe UI', 15, bold=True)
        except Exception:
            self.f_title   = pygame.font.Font(None, 22)
            self.f_section = pygame.font.Font(None, 16)
            self.f_label   = pygame.font.Font(None, 15)
            self.f_value   = pygame.font.Font(None, 14)
            self.f_tiny    = pygame.font.Font(None, 13)
            self.f_cb      = pygame.font.Font(None, 14)
            self.f_play    = pygame.font.Font(None, 18)

    # ── Widget init ───────────────────────────────────────────────────────

    def _init_widgets(self):
        pad  = 10
        hx   = C.MAP_W + pad
        cb_w = C.HUD_W - pad * 2

        # Layout - CB1 va CB2 phai cach nhau du xa de dropdown khong che
        self.CB_H      = 28
        self.Y_LABEL1  = 38
        self.Y_CB1     = 52    # CB1 header: y=52..80
        # CB1 dropdown (max 5 items): y=80..220 -> CB2 phai o duoi 220!
        self.Y_LABEL2  = 228
        self.Y_CB2     = 242   # CB2 header: y=242..270
        self.Y_PLAY    = 282   # Play button
        self.PLAY_H    = 36

        # Combobox 1: Nhom thuat toan
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

        # Combobox 2: Ten thuat toan
        first_group  = C.GROUP_NAMES[0]
        algo_options = self._algo_options(first_group)
        self.cb_algo = Combobox(
            abs_x=hx, abs_y=self.Y_CB2,
            w=cb_w, h=self.CB_H,
            options=algo_options,
            font=self.f_cb,
            selected_idx=0,
            max_visible=5,
        )

        # Play button
        self.play_btn = pygame.Rect(hx, self.Y_PLAY, cb_w, self.PLAY_H)
        self._group_idx = 0

    def _algo_options(self, group_name: str):
        info  = C.ALGO_GROUPS.get(group_name, {})
        algos = info.get('algorithms', {})
        return [f"{k} — {v}" for k, v in algos.items()]

    def _algo_key(self) -> str:
        group = C.GROUP_NAMES[self._group_idx]
        keys  = list(C.ALGO_GROUPS[group]['algorithms'].keys())
        idx   = self.cb_algo.selected
        return keys[idx] if 0 <= idx < len(keys) else (keys[0] if keys else '')

    def _on_group_changed(self, idx: int):
        self._group_idx = idx
        new_opts = self._algo_options(C.GROUP_NAMES[idx])
        self.cb_algo.set_options(new_opts, selected_idx=0)
        self.cb_algo.close()

    def get_selected_algo(self) -> str:
        return self._algo_key()

    # ── Event ─────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event, game: Game) -> bool:
        """
        Fix bug: chi chuyen event cho mot combobox tai mot thoi diem.
        - Neu CB1 mo va click trong dropdown CB1 -> chi xu ly CB1.
        - Neu CB2 mo va click trong dropdown CB2 -> chi xu ly CB2.
        - Neu click vao CB1 header -> dong CB2, mo CB1.
        - Neu click vao CB2 header -> dong CB1, mo CB2.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            hdr1  = pygame.Rect(self.cb_group.abs_x, self.cb_group.abs_y,
                                self.cb_group.w, self.cb_group.h)
            drop1 = self.cb_group.get_dropdown_rect()

            hdr2  = pygame.Rect(self.cb_algo.abs_x, self.cb_algo.abs_y,
                                self.cb_algo.w, self.cb_algo.h)
            drop2 = self.cb_algo.get_dropdown_rect()

            in_cb1 = hdr1.collidepoint(mx, my) or (drop1 and drop1.collidepoint(mx, my))
            in_cb2 = hdr2.collidepoint(mx, my) or (drop2 and drop2.collidepoint(mx, my))

            if in_cb1:
                # Chi xu ly CB1, dong CB2 truoc
                self.cb_algo.close()
                self.cb_group.handle_event(event)
                if self.play_btn.collidepoint(mx, my): return True
                return False
            elif in_cb2:
                # Chi xu ly CB2, dong CB1 truoc
                self.cb_group.close()
                self.cb_algo.handle_event(event)
                if self.play_btn.collidepoint(mx, my): return True
                return False
            else:
                # Click ngoai -> dong ca hai
                self.cb_group.close()
                self.cb_algo.close()
                if self.play_btn.collidepoint(mx, my): return True
                return False

        # Cac event khac (MOUSEMOTION, MOUSEWHEEL...) -> chuyen cho ca hai
        self.cb_group.handle_event(event)
        self.cb_algo.handle_event(event)

        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.play_btn.collidepoint(event.pos)):
            return True
        return False

    # ── Main render ───────────────────────────────────────────────────────

    def render(self, game: Game, dt: float):
        self.screen.fill(C.BG_COLOR)
        self._draw_maze_area(game)
        self._draw_hud(game)
        self._draw_play_button(game)
        # Z-order: cb_algo truoc, cb_group sau (dropdown group de len algo)
        self.cb_algo.draw(self.screen)
        self.cb_group.draw(self.screen)
        pygame.display.flip()

    # ── Maze area ─────────────────────────────────────────────────────────

    def _draw_maze_area(self, game: Game):
        map_surf = self.screen.subsurface((0, 0, C.MAP_W, C.MAP_H))
        known_cells = None
        if (game.current_algo == 'BFS-PO'
                and game.result and game.current_step):
            known_cells = game.current_step.extra.get('known_cells')
        game.maze.draw(
            map_surf,
            result=game.result,
            current_step=game.current_step_idx,
            player_pos=game.player_pos,
            known_cells=known_cells,
        )
        pygame.draw.rect(self.screen, C.HUD_BORDER, (0, 0, C.MAP_W, C.MAP_H), 2)

    # ── HUD panel ─────────────────────────────────────────────────────────

    def _draw_hud(self, game: Game):
        pad   = 10
        panel = pygame.Surface((C.HUD_W, C.SCREEN_H))
        panel.fill(C.HUD_BG)
        pygame.draw.line(panel, C.HUD_BORDER, (0, 0), (0, C.SCREEN_H), 2)

        y = 6

        # ── TITLE ──────────────────────────────────────────────────────
        title = self.f_title.render("AI MAZE SOLVER", True, C.HUD_TITLE)
        panel.blit(title, (C.HUD_W//2 - title.get_width()//2, y))
        y += title.get_height() + 1
        sub = self.f_tiny.render("Me Cung AI  30x30  5 Thuat Toan", True, (70, 90, 140))
        panel.blit(sub, (C.HUD_W//2 - sub.get_width()//2, y))
        y += sub.get_height() + 3
        pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
        y += 4

        # ── LABEL COMBOBOX 1 ───────────────────────────────────────────
        # Vung widget: CB1, CB2, Play duoc ve truc tiep len screen sau
        # Panel chi ve label va nen
        _draw_label(panel, self.f_label, "Nhom thuat toan:", pad, self.Y_LABEL1 - 2, C.HUD_TITLE)
        pygame.draw.rect(panel, (22, 25, 45), (pad-2, self.Y_CB1-2, C.HUD_W-pad+2, self.CB_H+4))

        _draw_label(panel, self.f_label, "Thuat toan:", pad, self.Y_LABEL2 - 2, C.HUD_TITLE)
        pygame.draw.rect(panel, (22, 25, 45), (pad-2, self.Y_CB2-2, C.HUD_W-pad+2, self.CB_H+4))

        # Nen nut Play
        pygame.draw.rect(panel, (22, 25, 45), (pad-2, self.Y_PLAY-2, C.HUD_W-pad+2, self.PLAY_H+4))

        sep_y = self.Y_PLAY + self.PLAY_H + 8
        pygame.draw.line(panel, C.HUD_BORDER, (pad, sep_y), (C.HUD_W-pad, sep_y))
        y = sep_y + 6

        # ── MAZE INFO ──────────────────────────────────────────────────
        _draw_section(panel, self.f_section, "Thong tin me cung", pad, y)
        y += self.f_section.get_height() + 4

        for label, val, col in [
            ("Start (S):", str(game.maze.start), C.START_COLOR),
            ("Goal  (G):", str(game.maze.goal),  C.GOAL_COLOR),
            ("Kich thuoc:", f"{C.COLS} x {C.ROWS}", C.HUD_TEXT),
        ]:
            _draw_kv(panel, self.f_label, self.f_value, label, val, col, pad, C.HUD_W, y)
            y += self.f_label.get_height() + 3
        y += 3

        pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
        y += 6

        # ── TRANG THAI THUAT TOAN ──────────────────────────────────────
        _draw_section(panel, self.f_section, "Trang thai thuc hien", pad, y)
        y += self.f_section.get_height() + 4

        result = game.result
        step   = game.current_step

        if result is None:
            rows = [
                ("Trang thai:", "Chua chay",          (70, 80, 110)),
                ("Bat dau:",    str(game.maze.start),  C.START_COLOR),
                ("Ket thuc:",   str(game.maze.goal),   C.GOAL_COLOR),
                ("Nhom:",       "—",                   (70, 80, 110)),
                ("Algorithm:",  "—",                   (70, 80, 110)),
            ]
        else:
            st_map = {
                PlaybackState.RUNNING: ("DANG CHAY",  (80, 220, 120)),
                PlaybackState.PAUSED:  ("TAM DUNG",   C.GOAL_COLOR),
                PlaybackState.DONE:    ("HOAN THANH", C.START_COLOR),
                PlaybackState.IDLE:    ("Chua chay",  (70, 80, 110)),
            }
            st_str, st_col = st_map.get(game.playback_state, ("?", C.HUD_TEXT))
            v_cnt = len(step.visited)  if step else result.total_visited
            f_cnt = len(step.frontier) if step else 0
            p_len = result.path_length if result.found else 0
            rows = [
                ("Trang thai:", st_str,                              st_col),
                ("Bat dau:",    str(result.start),                   C.START_COLOR),
                ("Ket thuc:",   str(result.goal),                    C.GOAL_COLOR),
                ("Nhom:",       C.get_algo_group(game.current_algo), (140, 160, 220)),
                ("Algorithm:",  game.current_algo,                   C.GOLD_COLOR),
                ("__SEP__",     "",                                  C.HUD_BORDER),
                ("Buoc:",       f"{game.current_step_idx}/{result.total_steps}", C.HUD_TEXT),
                ("Da duyet:",   f"{v_cnt} o",                        C.VIZ_VISITED),
                ("Frontier:",   f"{f_cnt} o",                        C.VIZ_FRONTIER),
                ("Duong di:",   f"{p_len} buoc" if result.found else "Chua co",
                                C.VIZ_PATH if result.found else C.VIZ_BACKTRACK),
                ("Thoi gian:",  f"{result.elapsed_ms:.1f} ms",       C.GOLD_COLOR),
            ]

        for label, val, col in rows:
            if label == "__SEP__":
                pygame.draw.line(panel, (40, 48, 72), (pad, y+3), (C.HUD_W-pad, y+3))
                y += 9
                continue
            _draw_kv(panel, self.f_label, self.f_value, label, val, col, pad, C.HUD_W, y)
            y += self.f_label.get_height() + 3

        y += 3
        pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
        y += 5

        # ── MO TA BUOC ─────────────────────────────────────────────────
        if step:
            _draw_section(panel, self.f_section, "Mo ta buoc", pad, y)
            y += self.f_section.get_height() + 3

            y = _draw_wrapped(panel, self.f_tiny, step.description,
                              pad, C.HUD_W - pad*2, y, C.HUD_TEXT)
            y += 2

            if step.is_backtrack:
                mode    = step.extra.get('mode', '')
                bt_col  = C.VIZ_STUCK if mode == 'stuck' else C.VIZ_BACKTRACK
                bt_txt  = "Bi ket - Local Optimum" if mode == 'stuck' else "BACKTRACK"
                bt_s    = self.f_label.render(bt_txt, True, bt_col)
                panel.blit(bt_s, (pad, y))
                y += bt_s.get_height() + 2

            skip = {'known_cells', 'neighbors_h', 'mode'}
            for k, v in list(step.extra.items())[:5]:
                if k in skip: continue
                v_str = (f"[{len(v)}]" if isinstance(v, (set, list))
                         else f"{v:.1f}" if isinstance(v, float)
                         else str(v))
                es = self.f_tiny.render(f"  {k}: {v_str}", True, (150, 168, 215))
                panel.blit(es, (pad, y))
                y += es.get_height() + 1

        # ── PROGRESS BAR ───────────────────────────────────────────────
        if result:
            y = max(y + 4, C.SCREEN_H - 100)
            pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
            y += 4
            pb_w = C.HUD_W - pad * 2
            pb_h = 7
            pygame.draw.rect(panel, (22, 28, 48), (pad, y, pb_w, pb_h), border_radius=3)
            fill = int(pb_w * game.progress)
            if fill > 0:
                pygame.draw.rect(panel, C.get_algo_color(game.current_algo),
                                 (pad, y, fill, pb_h), border_radius=3)
            pygame.draw.rect(panel, C.HUD_BORDER, (pad, y, pb_w, pb_h), 1, border_radius=3)
            # Percent label
            pct = self.f_tiny.render(f"{int(game.progress*100)}%", True, C.HUD_TEXT)
            panel.blit(pct, (pad + pb_w//2 - pct.get_width()//2, y - 1))
            y += pb_h + 5

        # ── DIEU KHIEN ─────────────────────────────────────────────────
        ctrl_y = C.SCREEN_H - 82
        pygame.draw.line(panel, C.HUD_BORDER, (pad, ctrl_y-2), (C.HUD_W-pad, ctrl_y-2))
        _draw_section(panel, self.f_section, "Dieu Khien", pad, ctrl_y)
        ctrl_y += self.f_section.get_height() + 2

        ctrls = [
            ("[PLAY]",  "Chay / Pause"),
            ("[Space]", "Pause / Resume"),
            ("[-> <-]", "Tien / lui buoc"),
            ("[Enter]", "Chay lai"),
            ("[R]",     "Me cung moi"),
            ("[T]",     "Doi toc do"),
            ("[Esc]",   "Ve menu"),
        ]
        for key, desc in ctrls:
            ks = self.f_tiny.render(key,  True, (180, 205, 255))
            ds = self.f_tiny.render(desc, True, (150, 165, 200))
            panel.blit(ks, (pad, ctrl_y))
            panel.blit(ds, (pad + 52, ctrl_y))
            ctrl_y += ks.get_height() + 1

        # ── MESSAGE BAR ────────────────────────────────────────────────
        msg_y = C.SCREEN_H - 18
        pygame.draw.rect(panel, (12, 14, 26), (0, msg_y-1, C.HUD_W, 19))
        pygame.draw.line(panel, C.HUD_BORDER, (0, msg_y-1), (C.HUD_W, msg_y-1))
        ms = self.f_tiny.render(game.message, True, game.message_color)
        panel.blit(ms, (pad, msg_y + 3))

        self.screen.blit(panel, (C.MAP_W, 0))

    # ── Play button ───────────────────────────────────────────────────────

    def _draw_play_button(self, game: Game):
        mx, my  = pygame.mouse.get_pos()
        hover   = self.play_btn.collidepoint(mx, my)
        running = (game.playback_state == PlaybackState.RUNNING)

        bg = C.PLAY_HOVER if hover else C.PLAY_BG
        pygame.draw.rect(self.screen, bg, self.play_btn, border_radius=8)
        pygame.draw.rect(self.screen, C.PLAY_BORDER, self.play_btn, 2, border_radius=8)

        # Hieu ung glow khi hover
        if hover:
            glow = pygame.Surface((self.play_btn.w + 8, self.play_btn.h + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*C.PLAY_BORDER, 60),
                             (0, 0, self.play_btn.w+8, self.play_btn.h+8), border_radius=10)
            self.screen.blit(glow, (self.play_btn.x-4, self.play_btn.y-4))
            pygame.draw.rect(self.screen, bg, self.play_btn, border_radius=8)
            pygame.draw.rect(self.screen, C.PLAY_BORDER, self.play_btn, 2, border_radius=8)

        label = "PAUSE" if running else "PLAY"
        ts = self.f_play.render(label, True, C.WHITE)
        self.screen.blit(ts, (
            self.play_btn.centerx - ts.get_width()//2,
            self.play_btn.centery - ts.get_height()//2,
        ))


# ── Helper functions ───────────────────────────────────────────────────────

def _draw_label(surface, font, text, x, y, color):
    s = font.render(text, True, color)
    surface.blit(s, (x, y))

def _draw_section(surface, font, text, x, y):
    """Section header voi duong gach chan noi bat."""
    s = font.render(text, True, C.HUD_TITLE)
    surface.blit(s, (x, y))
    uy = y + s.get_height() + 1
    pygame.draw.line(surface, C.HUD_TITLE,
                     (x, uy), (x + s.get_width(), uy), 1)

def _draw_kv(surface, f_label, f_value, label, val, val_col, pad, hud_w, y):
    """Ve cap key-value: label ben trai, value ben phai."""
    ls = f_label.render(label, True, C.HUD_TEXT)
    vs = f_value.render(str(val), True, val_col)
    surface.blit(ls, (pad, y))
    surface.blit(vs, (hud_w - vs.get_width() - pad, y))

def _draw_wrapped(surface, font, text, x, max_w, y, color) -> int:
    """Ve text xuat dong khi qua dai, tra ve y moi."""
    cur = ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if font.render(test, True, color).get_width() > max_w and cur:
            surface.blit(font.render(cur, True, color), (x, y))
            y += font.get_height() + 1
            cur = word
        else:
            cur = test
    if cur:
        surface.blit(font.render(cur, True, color), (x, y))
        y += font.get_height() + 2
    return y
