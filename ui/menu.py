# ui/menu.py — Man hinh chinh (AI Maze Solver)
"""Man hinh chinh voi hieu ung particle va thiet ke dep."""

import pygame
import math
import random
from typing import Optional
import config as C


class Particle:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.reset()

    def reset(self):
        self.x     = random.uniform(0, self.w)
        self.y     = random.uniform(0, self.h)
        self.vx    = random.uniform(-0.3, 0.3)
        self.vy    = random.uniform(-0.8, -0.2)
        self.size  = random.uniform(1, 2.5)
        self.alpha = random.uniform(60, 180)
        self.color = random.choice([
            C.START_COLOR, C.GOAL_COLOR, C.PLAYER_COLOR,
            C.VIZ_PATH, (150, 100, 255), (100, 200, 255)
        ])

    def update(self, dt):
        self.x     += self.vx
        self.y     += self.vy
        self.alpha -= dt * 45
        if self.alpha <= 0 or self.y < 0:
            self.y = self.h
            self.reset()

    def draw(self, surface):
        if self.alpha <= 0:
            return
        s = pygame.Surface((int(self.size*2+2), int(self.size*2+2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(self.alpha)),
                           (int(self.size)+1, int(self.size)+1), max(1, int(self.size)))
        surface.blit(s, (int(self.x), int(self.y)))


class MenuScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self._tick = 0.0
        self._particles = [Particle(self.w, self.h) for _ in range(60)]
        self.logo = self._load_logo()

        try:
            self.f_big      = pygame.font.SysFont('Segoe UI', 58, bold=True)
            self.f_mid      = pygame.font.SysFont('Segoe UI', 24, bold=True)
            self.f_sub      = pygame.font.SysFont('Segoe UI', 16, bold=True)
            self.f_small    = pygame.font.SysFont('Segoe UI', 14)
            self.f_btn      = pygame.font.SysFont('Segoe UI', 20, bold=True)
            self.f_tiny     = pygame.font.SysFont('Segoe UI', 12)
        except Exception:
            self.f_big      = pygame.font.Font(None, 64)
            self.f_mid      = pygame.font.Font(None, 28)
            self.f_sub      = pygame.font.Font(None, 20)
            self.f_small    = pygame.font.Font(None, 17)
            self.f_btn      = pygame.font.Font(None, 24)
            self.f_tiny     = pygame.font.Font(None, 14)

        bw, bh = 300, 56
        cx = self.w // 2 - bw // 2
        self._buttons = [
            {'rect': pygame.Rect(cx, 455, bw, bh), 'text': 'BAT DAU',
             'color': (35, 100, 55), 'hover': (55, 150, 85), 'border': (80, 210, 120)},
            {'rect': pygame.Rect(cx, 525, bw, bh), 'text': 'THOAT',
             'color': (90, 35, 35), 'hover': (140, 55, 55), 'border': (210, 80, 80)},
        ]

    def _load_logo(self) -> Optional[pygame.Surface]:
        try:
            return pygame.image.load(C.LOGO_PATH).convert_alpha()
        except (pygame.error, FileNotFoundError, AttributeError):
            return None

    def _draw_logo(self, x: int, y: int, size: int):
        rect = pygame.Rect(x, y, size, size)
        halo = pygame.Surface((size + 22, size + 22), pygame.SRCALPHA)
        pygame.draw.circle(halo, (70, 110, 230, 55), (size // 2 + 11, size // 2 + 11), size // 2 + 10)
        self.screen.blit(halo, (x - 11, y - 11))
        pygame.draw.circle(self.screen, (248, 250, 255), rect.center, size // 2)
        pygame.draw.circle(self.screen, (25, 42, 130), rect.center, size // 2, 3)
        if self.logo:
            logo = pygame.transform.smoothscale(self.logo, (size - 8, size - 8))
            self.screen.blit(logo, (x + 4, y + 4))
        else:
            pygame.draw.circle(self.screen, C.GOAL_COLOR, rect.center, size // 5)
            pygame.draw.circle(self.screen, C.HUD_TITLE, rect.center, size // 3, 3)

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return 'start'
            if event.key == pygame.K_ESCAPE:
                return 'quit'
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self._buttons:
                if btn['rect'].collidepoint(event.pos):
                    return btn['action'] if 'action' in btn else btn['text'].lower()
        return None

    def update(self, dt: float):
        self._tick += dt
        for p in self._particles:
            p.update(dt)

    def draw(self):
        self.screen.fill(C.BG_COLOR)
        self._draw_grid()
        for p in self._particles:
            p.draw(self.screen)
        self._draw_content()
        pygame.display.flip()

    def _draw_grid(self):
        """Luoi nen trang tri."""
        for x in range(0, self.w, 50):
            pygame.draw.line(self.screen, (14, 16, 28), (x, 0), (x, self.h))
        for y in range(0, self.h, 50):
            pygame.draw.line(self.screen, (14, 16, 28), (0, y), (self.w, y))

    def _draw_content(self):
        off = math.sin(self._tick * 1.4) * 6

        # ── Glow dang sau title ────────────────────────────────────────
        gw = 680
        glow = pygame.Surface((gw, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (50, 90, 200, 30), (0, 0, gw, 100))
        self.screen.blit(glow, (self.w//2 - gw//2, int(88+off)))

        # ── TITLE ──────────────────────────────────────────────────────
        self._draw_logo(self.w//2 - 34, int(18+off*0.3), 68)
        t1 = self.f_big.render("AI MAZE SOLVER", True, C.HUD_TITLE)
        # Shadow effect
        t1_shd = self.f_big.render("AI MAZE SOLVER", True, (20, 40, 100))
        self.screen.blit(t1_shd, (self.w//2 - t1.get_width()//2 + 2, int(100+off) + 2))
        self.screen.blit(t1,     (self.w//2 - t1.get_width()//2,     int(100+off)))

        # ── SUBTITLE ───────────────────────────────────────────────────
        t2 = self.f_mid.render("Me Cung AI  —  6 Thuat Toan Tim Duong", True, C.GOAL_COLOR)
        self.screen.blit(t2, (self.w//2 - t2.get_width()//2, int(168+off)))

        # ── DESCRIPTION ────────────────────────────────────────────────
        y_desc = int(215 + off)
        pygame.draw.line(self.screen, (35, 50, 90),
                         (self.w//2 - 280, y_desc), (self.w//2 + 280, y_desc))
        y_desc += 12

        desc_lines = [
            ("Moi thuat toan giai cung 1 bai toan:", C.HUD_TITLE, self.f_sub),
            ("Tim duong Start -> Goal trong me cung 15x15 den 40x40", C.HUD_TEXT, self.f_small),
            ("", None, None),
            ("Theo doi tung buoc thuc hien cua tung thuat toan:", C.HUD_TITLE, self.f_sub),
            ("Trang thai bat dau  ->  Cac buoc xu ly  ->  Ket qua", C.HUD_TEXT, self.f_small),
        ]
        for text, col, font in desc_lines:
            if not font:
                y_desc += 6
                continue
            s = font.render(text, True, col)
            self.screen.blit(s, (self.w//2 - s.get_width()//2, y_desc))
            y_desc += s.get_height() + 4

        # ── 5 NHOM THUAT TOAN (hien thi dep, khong co box tag nhu cu) ──
        y_groups = y_desc + 10
        pygame.draw.line(self.screen, (35, 50, 90),
                         (self.w//2 - 280, y_groups), (self.w//2 + 280, y_groups))
        y_groups += 10

        groups_label = self.f_sub.render("5 Nhom / 6 Thuat Toan:", True, C.HUD_TITLE)
        self.screen.blit(groups_label, (self.w//2 - groups_label.get_width()//2, y_groups))
        y_groups += groups_label.get_height() + 6

        group_items = [
            ("1. BFS",         "Uninformed Search",  C.ALGO_GROUPS['Uninformed Search']['color']),
            ("2. DFS",         "Uninformed Search",  C.ALGO_GROUPS['Uninformed Search']['color']),
            ("3. A*",          "Informed Search",    C.ALGO_GROUPS['Informed Search']['color']),
            ("4. Steepest HC", "Local Search",       C.ALGO_GROUPS['Local Search']['color']),
            ("5. BFS-PO",      "Complex Environment",C.ALGO_GROUPS['Complex Environment']['color']),
            ("6. Backtrack",   "CSP",                C.ALGO_GROUPS['CSP']['color']),
        ]

        # Hien thi 2 cot x 3 va 2
        col1 = [(g, n, c) for g, n, c in group_items[:3]]
        col2 = [(g, n, c) for g, n, c in group_items[3:]]

        x_left  = self.w//2 - 280
        x_right = self.w//2 + 20
        for i, (algo, group, color) in enumerate(col1):
            dot_x = x_left + 6
            pygame.draw.circle(self.screen, color, (dot_x, y_groups + i*20 + 7), 5)
            a_s = self.f_small.render(f"{algo}", True, C.WHITE)
            g_s = self.f_tiny.render(f" — {group}", True, (160, 175, 210))
            self.screen.blit(a_s, (dot_x + 12, y_groups + i*20))
            self.screen.blit(g_s, (dot_x + 12 + a_s.get_width(), y_groups + i*20 + 2))

        for i, (algo, group, color) in enumerate(col2):
            dot_x = x_right + 6
            pygame.draw.circle(self.screen, color, (dot_x, y_groups + i*20 + 7), 5)
            a_s = self.f_small.render(f"{algo}", True, C.WHITE)
            g_s = self.f_tiny.render(f" — {group}", True, (160, 175, 210))
            self.screen.blit(a_s, (dot_x + 12, y_groups + i*20))
            self.screen.blit(g_s, (dot_x + 12 + a_s.get_width(), y_groups + i*20 + 2))

        pygame.draw.line(self.screen, (35, 50, 90),
                         (self.w//2 - 280, y_groups + 60), (self.w//2 + 280, y_groups + 60))

        # ── BUTTONS ────────────────────────────────────────────────────
        mx, my = pygame.mouse.get_pos()
        actions = ['start', 'quit']
        for i, btn in enumerate(self._buttons):
            hover  = btn['rect'].collidepoint(mx, my)
            scale  = 1.04 if hover else 1.0
            bg     = btn['hover'] if hover else btn['color']
            border = btn['border']

            r = btn['rect']
            if hover:
                # Glow effect
                g_surf = pygame.Surface((r.w+12, r.h+12), pygame.SRCALPHA)
                pygame.draw.rect(g_surf, (*border, 50),
                                 (0, 0, r.w+12, r.h+12), border_radius=12)
                self.screen.blit(g_surf, (r.x-6, r.y-6))

            pygame.draw.rect(self.screen, bg, r, border_radius=10)
            pygame.draw.rect(self.screen, border, r, 2, border_radius=10)

            ts = self.f_btn.render(btn['text'], True, C.WHITE)
            self.screen.blit(ts, (r.centerx - ts.get_width()//2,
                                   r.centery - ts.get_height()//2))
            # Gan action cho nut
            btn['action'] = actions[i]

        # ── FOOTER ─────────────────────────────────────────────────────
        ft = self.f_tiny.render(
            "Nhan ENTER hoac click de bat dau  |  ESC de thoat",
            True, (55, 68, 100)
        )
        self.screen.blit(ft, (self.w//2 - ft.get_width()//2, self.h - 22))
