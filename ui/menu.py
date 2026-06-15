# ui/menu.py — Menu chính (phiên bản Maze Solver)
"""Menu chính đơn giản, elegant."""

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
        self.x = random.uniform(0, self.w)
        self.y = random.uniform(0, self.h)
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.6, -0.1)
        self.size = random.uniform(1, 3)
        self.alpha = random.uniform(80, 200)
        self.color = random.choice([
            C.START_COLOR, C.GOAL_COLOR, C.PLAYER_COLOR,
            C.VIZ_PATH, (180, 120, 255)
        ])

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= dt * 50
        if self.alpha <= 0 or self.y < 0:
            self.y = self.h
            self.reset()

    def draw(self, surface):
        if self.alpha <= 0:
            return
        s = pygame.Surface((int(self.size*2+1), int(self.size*2+1)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(self.alpha)),
                           (int(self.size), int(self.size)), max(1, int(self.size)))
        surface.blit(s, (int(self.x), int(self.y)))


class MenuScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self._tick = 0.0
        self._particles = [Particle(self.w, self.h) for _ in range(50)]

        try:
            self.f_big   = pygame.font.SysFont('Segoe UI', 52, bold=True)
            self.f_mid   = pygame.font.SysFont('Segoe UI', 22, bold=True)
            self.f_small = pygame.font.SysFont('Segoe UI', 15)
            self.f_tiny  = pygame.font.SysFont('Segoe UI', 13)
        except Exception:
            self.f_big   = pygame.font.Font(None, 58)
            self.f_mid   = pygame.font.Font(None, 26)
            self.f_small = pygame.font.Font(None, 18)
            self.f_tiny  = pygame.font.Font(None, 15)

        # Buttons
        bw, bh = 280, 52
        cx = self.w // 2 - bw // 2
        self._buttons = [
            {'rect': pygame.Rect(cx, 380, bw, bh), 'text': 'Bat Dau', 'action': 'start',
             'color': (40, 90, 60), 'hover': (60, 140, 90)},
            {'rect': pygame.Rect(cx, 445, bw, bh), 'text': 'Thoat', 'action': 'quit',
             'color': (80, 35, 35), 'hover': (130, 55, 55)},
        ]

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return 'start'
            if event.key == pygame.K_ESCAPE:
                return 'quit'
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self._buttons:
                if btn['rect'].collidepoint(event.pos):
                    return btn['action']
        return None

    def update(self, dt: float):
        self._tick += dt
        for p in self._particles:
            p.update(dt)

    def draw(self):
        self.screen.fill(C.BG_COLOR)

        # Grid pattern
        for x in range(0, self.w, 60):
            pygame.draw.line(self.screen, (15, 16, 28), (x, 0), (x, self.h))
        for y in range(0, self.h, 60):
            pygame.draw.line(self.screen, (15, 16, 28), (0, y), (self.w, y))

        # Particles
        for p in self._particles:
            p.draw(self.screen)

        # ── TITLE ─────────────────────────────────────────────
        off = math.sin(self._tick * 1.5) * 5

        # Glow
        gw = 700
        glow = pygame.Surface((gw, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (60, 100, 200, 25), (0, 0, gw, 80))
        self.screen.blit(glow, (self.w//2 - gw//2, int(100+off)-10))

        t1 = self.f_big.render("AI MAZE SOLVER", True, C.HUD_TITLE)
        self.screen.blit(t1, (self.w//2 - t1.get_width()//2, int(100+off)))

        t2 = self.f_mid.render("Me Cung AI  5 Thuat Toan Tim Duong", True, C.GOAL_COLOR)
        self.screen.blit(t2, (self.w//2 - t2.get_width()//2, int(160+off)))

        # ── ALGO TAGS ─────────────────────────────────────────
        algo_info = [
            ("1. DFS",        "Uninformed",    C.ALGO_GROUPS['Uninformed Search']['color']),
            ("2. A*",         "Informed",      C.ALGO_GROUPS['Informed Search']['color']),
            ("3. Steepest HC","Local Search",  C.ALGO_GROUPS['Local Search']['color']),
            ("4. BFS-PO",     "Complex Env",   C.ALGO_GROUPS['Complex Environment']['color']),
            ("5. Backtrack",  "CSP",           C.ALGO_GROUPS['CSP']['color']),
        ]
        tag_total_w = sum(140 for _ in algo_info)
        tx = self.w//2 - tag_total_w//2 + 10
        ty = 210
        for name, group, color in algo_info:
            tag_rect = pygame.Rect(tx-6, ty-4, 128, 38)
            pygame.draw.rect(self.screen, (*color[:3], 180), tag_rect, border_radius=8)
            pygame.draw.rect(self.screen, color, tag_rect, 1, border_radius=8)
            ns = self.f_small.render(name, True, C.WHITE)
            gs = self.f_tiny.render(group, True, (200, 200, 200))
            self.screen.blit(ns, (tx, ty))
            self.screen.blit(gs, (tx, ty + ns.get_height()))
            tx += 140

        # Separator
        pygame.draw.line(self.screen, C.HUD_BORDER,
                         (self.w//2-220, 270), (self.w//2+220, 270))

        # Description
        desc_lines = [
            "Moi thuat toan giai cung 1 bai toan: Tim duong S -> G trong me cung 30x30",
            "Theo doi tung buoc: Trang thai bat dau -> Cac buoc thuc hien -> Ket qua",
        ]
        for i, line in enumerate(desc_lines):
            s = self.f_small.render(line, True, (150, 160, 200))
            self.screen.blit(s, (self.w//2 - s.get_width()//2, 282 + i*18))

        # ── BUTTONS ───────────────────────────────────────────
        mx, my = pygame.mouse.get_pos()
        for btn in self._buttons:
            hover = btn['rect'].collidepoint(mx, my)
            color = btn['hover'] if hover else btn['color']
            border = C.WHITE if hover else C.HUD_BORDER
            pygame.draw.rect(self.screen, color, btn['rect'], border_radius=10)
            pygame.draw.rect(self.screen, border, btn['rect'], 2, border_radius=10)
            ts = self.f_mid.render(btn['text'], True, C.WHITE)
            self.screen.blit(ts, (
                btn['rect'].centerx - ts.get_width()//2,
                btn['rect'].centery - ts.get_height()//2
            ))

        # Footer
        ft = self.f_tiny.render(
            "Nhan ENTER hoac click de bat dau  |  ESC de thoat",
            True, (60, 70, 100)
        )
        self.screen.blit(ft, (self.w//2 - ft.get_width()//2, self.h - 25))
