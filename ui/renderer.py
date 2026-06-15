# ui/renderer.py — Renderer chính (HUD + Combobox + Play)
"""
Thứ tự vẽ (z-order) để tránh che dropdown:
  1. Maze area
  2. HUD background panel (không bao gồm vùng widget)
  3. Nút Play
  4. Combobox 2 (algo) — vẽ trước
  5. Combobox 1 (group) — vẽ SAU (dropdown của cb1 đè lên cb2)

Không dùng emoji — tránh lỗi font trên một số hệ thống Windows.
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

    # ── Font ─────────────────────────────────────────────────

    def _init_fonts(self):
        pygame.font.init()
        try:
            self.f_title  = pygame.font.SysFont('Segoe UI', 17, bold=True)
            self.f_large  = pygame.font.SysFont('Segoe UI', 14, bold=True)
            self.f_small  = pygame.font.SysFont('Segoe UI', 12)
            self.f_tiny   = pygame.font.SysFont('Segoe UI', 10)
            self.f_cb     = pygame.font.SysFont('Segoe UI', 12)
        except Exception:
            self.f_title  = pygame.font.Font(None, 20)
            self.f_large  = pygame.font.Font(None, 17)
            self.f_small  = pygame.font.Font(None, 14)
            self.f_tiny   = pygame.font.Font(None, 12)
            self.f_cb     = pygame.font.Font(None, 14)

    # ── Widget init ──────────────────────────────────────────

    def _init_widgets(self):
        """Khởi tạo 2 combobox và nút Play trên HUD."""
        pad  = 10
        hx   = C.MAP_W + pad        # x bắt đầu trong HUD (tọa độ screen)
        cb_w = C.HUD_W - pad * 2    # chiều rộng combobox

        # Layout cố định (tọa độ y tuyệt đối trên screen)
        self.Y_LABEL1  = 40    # label "Nhom thuat toan:"
        self.Y_CB1     = 54    # combobox 1
        self.CB_H      = 26    # chiều cao mỗi combobox
        self.Y_LABEL2  = 88    # label "Thuat toan:"
        self.Y_CB2     = 102   # combobox 2
        self.Y_PLAY    = 138   # nút Play
        self.PLAY_H    = 32    # chiều cao nút Play

        # Combobox 1 — Nhóm thuật toán
        group_options = [
            f"{g} — {info['vi_name']}"
            for g, info in C.ALGO_GROUPS.items()
        ]
        self.cb_group = Combobox(
            abs_x=hx, abs_y=self.Y_CB1,
            w=cb_w, h=self.CB_H,
            options=group_options,
            font=self.f_cb,
            selected_idx=0,
            on_change=self._on_group_changed,
            max_visible=6,
        )

        # Combobox 2 — Tên thuật toán
        first_group  = C.GROUP_NAMES[0]
        algo_options = self._algo_options(first_group)
        self.cb_algo = Combobox(
            abs_x=hx, abs_y=self.Y_CB2,
            w=cb_w, h=self.CB_H,
            options=algo_options,
            font=self.f_cb,
            selected_idx=0,
            max_visible=6,
        )

        # Nút Play
        self.play_btn = pygame.Rect(hx, self.Y_PLAY, cb_w, self.PLAY_H)

        self._group_idx = 0   # index nhóm hiện tại

    def _algo_options(self, group_name: str):
        info  = C.ALGO_GROUPS.get(group_name, {})
        algos = info.get('algorithms', {})
        return [f"{k} — {v}" for k, v in algos.items()]

    def _algo_key(self) -> str:
        """Lấy key thuật toán từ lựa chọn combobox 2."""
        group = C.GROUP_NAMES[self._group_idx]
        keys  = list(C.ALGO_GROUPS[group]['algorithms'].keys())
        idx   = self.cb_algo.selected
        return keys[idx] if 0 <= idx < len(keys) else (keys[0] if keys else '')

    def _on_group_changed(self, idx: int):
        self._group_idx = idx
        self.cb_algo.set_options(
            self._algo_options(C.GROUP_NAMES[idx]), selected_idx=0)
        # Đóng combobox 2 nếu đang mở
        self.cb_algo.close()

    def get_selected_algo(self) -> str:
        return self._algo_key()

    # ── Event ────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event, game: Game) -> bool:
        """
        Xử lý event cho toàn bộ HUD widget.
        Trả về True nếu nên trigger run_algorithm (nút Play được click).
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Nếu click vào cb1, đóng cb2
            in_cb1_header = pygame.Rect(
                self.cb_group.abs_x, self.cb_group.abs_y,
                self.cb_group.w, self.cb_group.h
            ).collidepoint(mx, my)
            drop1 = self.cb_group.get_dropdown_rect()
            in_cb1_drop = drop1.collidepoint(mx, my) if drop1 else False

            in_cb2_header = pygame.Rect(
                self.cb_algo.abs_x, self.cb_algo.abs_y,
                self.cb_algo.w, self.cb_algo.h
            ).collidepoint(mx, my)
            drop2 = self.cb_algo.get_dropdown_rect()
            in_cb2_drop = drop2.collidepoint(mx, my) if drop2 else False

            if in_cb1_header or in_cb1_drop:
                self.cb_algo.close()
            if in_cb2_header or in_cb2_drop:
                self.cb_group.close()
            if not in_cb1_header and not in_cb1_drop:
                self.cb_group.close()
            if not in_cb2_header and not in_cb2_drop:
                self.cb_algo.close()

        # Chuyển event cho từng combobox
        self.cb_group.handle_event(event)
        self.cb_algo.handle_event(event)

        # Nút Play
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.play_btn.collidepoint(event.pos)):
            return True
        return False

    # ── Main render ──────────────────────────────────────────

    def render(self, game: Game, dt: float):
        self.screen.fill(C.BG_COLOR)

        # 1. Maze
        self._draw_maze_area(game)

        # 2. HUD background + text (trừ vùng widget)
        self._draw_hud(game)

        # 3. Nút Play (trên panel, dưới combobox)
        self._draw_play_button(game)

        # 4. Vẽ combobox theo z-order:
        #    cb_algo trước (z-dưới), cb_group sau (z-trên)
        #    → dropdown của cb_group đè lên cb_algo
        self.cb_algo.draw(self.screen)
        self.cb_group.draw(self.screen)

        pygame.display.flip()

    # ── Maze area ────────────────────────────────────────────

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

    # ── HUD panel ────────────────────────────────────────────

    def _draw_hud(self, game: Game):
        """Vẽ toàn bộ HUD background và text, trừ vùng widget (combobox/play)."""
        pad   = 10
        panel = pygame.Surface((C.HUD_W, C.SCREEN_H))
        panel.fill(C.HUD_BG)
        pygame.draw.line(panel, C.HUD_BORDER, (0, 0), (0, C.SCREEN_H), 2)

        y = 8

        # ── Tiêu đề ───────────────────────────────────────────
        t = self.f_title.render("AI MAZE SOLVER", True, C.HUD_TITLE)
        panel.blit(t, (C.HUD_W//2 - t.get_width()//2, y))
        y += t.get_height() + 2
        sub = self.f_tiny.render("Me Cung AI  30x30  5 Thuat Toan Tim Duong", True, C.HUD_BORDER)
        panel.blit(sub, (C.HUD_W//2 - sub.get_width()//2, y))
        y += sub.get_height() + 4
        pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
        y += 4

        # ── Labels cho combobox (vẽ trên panel, combobox sẽ vẽ trực tiếp lên screen) ──
        l1 = self.f_small.render("Nhom thuat toan:", True, C.HUD_TITLE)
        panel.blit(l1, (pad, self.Y_LABEL1 - 4))

        l2 = self.f_small.render("Thuat toan:", True, C.HUD_TITLE)
        panel.blit(l2, (pad, self.Y_LABEL2 - 4))

        # Vùng trắng làm nền cho widget (đảm bảo nền sạch)
        widget_bg = pygame.Rect(pad-2, self.Y_CB1-2, C.HUD_W - pad, self.Y_PLAY + self.PLAY_H + 4 - self.Y_CB1)
        pygame.draw.rect(panel, C.HUD_BG, widget_bg)

        # Separator sau widget
        sep_y = self.Y_PLAY + self.PLAY_H + 8
        pygame.draw.line(panel, C.HUD_BORDER, (pad, sep_y), (C.HUD_W-pad, sep_y))
        y = sep_y + 6

        # ── Thong tin me cung ─────────────────────────────────
        mz = self.f_small.render("Thong tin me cung:", True, C.HUD_TITLE)
        panel.blit(mz, (pad, y))
        y += mz.get_height() + 3

        for label, val, col in [
            ("Start (S)", str(game.maze.start), C.START_COLOR),
            ("Goal  (G)", str(game.maze.goal),  C.GOAL_COLOR),
            ("Kich thuoc", f"{C.COLS} x {C.ROWS}", C.HUD_TEXT),
        ]:
            ls = self.f_small.render(label, True, C.HUD_TEXT)
            vs = self.f_small.render(val,   True, col)
            panel.blit(ls, (pad, y))
            panel.blit(vs, (C.HUD_W - vs.get_width() - pad, y))
            y += ls.get_height() + 2
        y += 4

        pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
        y += 6

        # ── Trang thai thuat toan ─────────────────────────────
        result = game.result
        step   = game.current_step

        st_lbl = self.f_small.render("Trang thai thuc hien:", True, C.HUD_TITLE)
        panel.blit(st_lbl, (pad, y))
        y += st_lbl.get_height() + 3

        if result is None:
            info_rows = [
                ("Trang thai",   "Chua chay",          C.HUD_BORDER),
                ("Bat dau (S)",  str(game.maze.start),  C.START_COLOR),
                ("Ket thuc (G)", str(game.maze.goal),   C.GOAL_COLOR),
                ("Nhom",         "—",                   C.HUD_BORDER),
                ("Thuat toan",   "—",                   C.HUD_BORDER),
            ]
        else:
            st_map = {
                PlaybackState.RUNNING: ("DANG CHAY",     (80,  220, 120)),
                PlaybackState.PAUSED:  ("TAM DUNG",      C.GOAL_COLOR),
                PlaybackState.DONE:    ("HOAN THANH",    C.START_COLOR),
                PlaybackState.IDLE:    ("Chua chay",     C.HUD_BORDER),
            }
            st_str, st_col = st_map.get(game.playback_state, ("?", C.HUD_TEXT))
            v_cnt = len(step.visited)  if step else result.total_visited
            f_cnt = len(step.frontier) if step else 0
            p_len = result.path_length if result.found else 0

            info_rows = [
                ("Trang thai",   st_str,                        st_col),
                ("Bat dau (S)",  str(result.start),             C.START_COLOR),
                ("Ket thuc (G)", str(result.goal),              C.GOAL_COLOR),
                ("Nhom",         C.get_algo_group(game.current_algo), C.HUD_BORDER),
                ("Thuat toan",   game.current_algo,             C.GOLD_COLOR),
                ("__SEP__",      "",                            C.HUD_BORDER),
                ("Buoc hien tai",f"{game.current_step_idx}/{result.total_steps}", C.HUD_TEXT),
                ("Da duyet",     f"{v_cnt} o",                  C.VIZ_VISITED),
                ("Frontier",     f"{f_cnt} o",                  C.VIZ_FRONTIER),
                ("Duong di",     f"{p_len} buoc" if result.found else "Chua co",
                                 C.VIZ_PATH if result.found else C.VIZ_BACKTRACK),
                ("Thoi gian",    f"{result.elapsed_ms:.1f} ms", C.GOLD_COLOR),
            ]

        for label, val, col in info_rows:
            if label == "__SEP__":
                pygame.draw.line(panel, (40,45,70), (pad, y+3), (C.HUD_W-pad, y+3))
                y += 8
                continue
            ls = self.f_small.render(label, True, C.HUD_TEXT)
            vs = self.f_small.render(str(val), True, col)
            panel.blit(ls, (pad, y))
            panel.blit(vs, (C.HUD_W - vs.get_width() - pad, y))
            y += ls.get_height() + 2

        y += 4
        pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
        y += 6

        # ── Mo ta buoc ────────────────────────────────────────
        if step:
            dt_lbl = self.f_small.render("Mo ta buoc:", True, C.HUD_TITLE)
            panel.blit(dt_lbl, (pad, y))
            y += dt_lbl.get_height() + 3

            desc   = step.description
            max_w  = C.HUD_W - pad * 2
            cur_line = ""
            for word in desc.split():
                test = (cur_line + " " + word).strip()
                if self.f_tiny.render(test, True, C.HUD_TEXT).get_width() > max_w and cur_line:
                    s = self.f_tiny.render(cur_line, True, C.HUD_TEXT)
                    panel.blit(s, (pad, y))
                    y += s.get_height() + 1
                    cur_line = word
                else:
                    cur_line = test
            if cur_line:
                s = self.f_tiny.render(cur_line, True, C.HUD_TEXT)
                panel.blit(s, (pad, y))
                y += s.get_height() + 3

            # Backtrack / stuck indicator
            mode = step.extra.get('mode', '')
            if step.is_backtrack:
                bt_col = C.VIZ_STUCK if mode == 'stuck' else C.VIZ_BACKTRACK
                bt_txt = "Bi ket - Local Optimum" if mode == 'stuck' else "BACKTRACK"
                bt_s   = self.f_small.render(bt_txt, True, bt_col)
                panel.blit(bt_s, (pad, y))
                y += bt_s.get_height() + 2

            # Extra key-value
            skip = {'known_cells', 'neighbors_h', 'mode'}
            for k, v in list(step.extra.items())[:5]:
                if k in skip: continue
                v_str = (f"[{len(v)} item]" if isinstance(v, (set, list))
                         else f"{v:.1f}" if isinstance(v, float)
                         else str(v))
                es = self.f_tiny.render(f"  {k}: {v_str}", True, (150, 160, 200))
                panel.blit(es, (pad, y))
                y += es.get_height() + 1

        # ── Progress bar ──────────────────────────────────────
        if result:
            y = max(y + 4, C.SCREEN_H - 120)
            pygame.draw.line(panel, C.HUD_BORDER, (pad, y), (C.HUD_W-pad, y))
            y += 4
            pb_w = C.HUD_W - pad * 2
            pb_h = 6
            pygame.draw.rect(panel, (25, 30, 50), (pad, y, pb_w, pb_h), border_radius=3)
            fill = int(pb_w * game.progress)
            if fill > 0:
                pygame.draw.rect(panel, C.get_algo_color(game.current_algo),
                                 (pad, y, fill, pb_h), border_radius=3)
            pygame.draw.rect(panel, C.HUD_BORDER, (pad, y, pb_w, pb_h), 1, border_radius=3)
            y += pb_h + 6

        # ── Dieu khien ────────────────────────────────────────
        ctrl_y = C.SCREEN_H - 88
        pygame.draw.line(panel, C.HUD_BORDER, (pad, ctrl_y-2), (C.HUD_W-pad, ctrl_y-2))
        ct = self.f_small.render("Dieu Khien:", True, C.HUD_TITLE)
        panel.blit(ct, (pad, ctrl_y))
        ctrl_y += ct.get_height() + 2

        ctrls = [
            ("[Play]",  "Chay / Pause thuat toan"),
            ("[Space]", "Pause / Resume"),
            ("[-> <-]", "Tien / lui 1 buoc"),
            ("[Enter]", "Chay lai"),
            ("[R]",     "Me cung moi"),
            ("[T]",     "Doi toc do"),
            ("[Esc]",   "Ve menu"),
        ]
        for key, desc in ctrls:
            ks = self.f_tiny.render(key,  True, (180, 200, 255))
            ds = self.f_tiny.render(desc, True, (140, 150, 180))
            panel.blit(ks, (pad, ctrl_y))
            panel.blit(ds, (pad + 50, ctrl_y))
            ctrl_y += ks.get_height() + 1

        # ── Message bar ───────────────────────────────────────
        msg_y = C.SCREEN_H - 18
        pygame.draw.rect(panel, (15, 15, 28), (0, msg_y-1, C.HUD_W, 19))
        pygame.draw.line(panel, C.HUD_BORDER, (0, msg_y-1), (C.HUD_W, msg_y-1))
        ms = self.f_tiny.render(game.message, True, game.message_color)
        panel.blit(ms, (pad, msg_y + 2))

        # Blit panel lên screen
        self.screen.blit(panel, (C.MAP_W, 0))

    # ── Play button ──────────────────────────────────────────

    def _draw_play_button(self, game: Game):
        """Vẽ nút PLAY trực tiếp lên screen (trước combobox)."""
        mx, my  = pygame.mouse.get_pos()
        hover   = self.play_btn.collidepoint(mx, my)
        running = (game.playback_state == PlaybackState.RUNNING)

        bg  = C.PLAY_HOVER if hover else C.PLAY_BG
        pygame.draw.rect(self.screen, bg, self.play_btn, border_radius=7)
        pygame.draw.rect(self.screen, C.PLAY_BORDER, self.play_btn, 2, border_radius=7)

        label = "PAUSE" if running else "PLAY"
        ts = self.f_large.render(label, True, C.WHITE)
        self.screen.blit(ts, (
            self.play_btn.centerx - ts.get_width()//2,
            self.play_btn.centery - ts.get_height()//2,
        ))
