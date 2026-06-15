# ui/combobox.py — Combobox widget thuần Pygame
"""
Combobox: click header để mở/đóng dropdown.
Tất cả tọa độ là TUYỆT ĐỐI trên màn hình (không phải trên Surface con).
Dropdown vẽ TRỰC TIẾP lên surface được truyền vào draw() — đảm bảo
nó luôn nằm trên cùng khi được vẽ sau cùng.

Thứ tự vẽ (quan trọng):
  renderer vẽ cb_algo.draw() trước, cb_group.draw() sau
  → dropdown của cb_group đè lên mọi thứ bên dưới.
"""

import pygame
from typing import List, Optional, Callable
import config as C


class Combobox:
    """
    Args:
        abs_x, abs_y : Tọa độ góc trên-trái (tuyệt đối trên screen)
        w, h         : Kích thước phần header
        options      : Danh sách chuỗi hiển thị
        font         : pygame.font.Font
        selected_idx : Index mặc định
        on_change    : Callback(int) khi selection thay đổi
        max_visible  : Số item tối đa hiển thị trong dropdown
    """

    def __init__(self, abs_x: int, abs_y: int, w: int, h: int,
                 options: List[str], font: pygame.font.Font,
                 selected_idx: int = 0,
                 on_change: Optional[Callable[[int], None]] = None,
                 max_visible: int = 8):
        self.abs_x       = abs_x
        self.abs_y       = abs_y
        self.w           = w
        self.h           = h
        self.options     = list(options)
        self.font        = font
        self.selected    = selected_idx
        self.on_change   = on_change
        self.max_visible = max_visible
        self.is_open     = False
        self._hover_idx  = -1
        self._scroll     = 0

    # ── Properties ───────────────────────────────────────────

    @property
    def selected_text(self) -> str:
        if 0 <= self.selected < len(self.options):
            return self.options[self.selected]
        return ''

    def set_options(self, options: List[str], selected_idx: int = 0):
        self.options  = list(options)
        self.selected = max(0, min(selected_idx, len(options)-1)) if options else 0
        self.is_open  = False
        self._scroll  = 0
        self._hover_idx = -1

    def set_selected(self, idx: int):
        self.selected = idx
        self.is_open  = False

    def close(self):
        self.is_open  = False
        self._hover_idx = -1

    def get_dropdown_rect(self) -> Optional[pygame.Rect]:
        """Rect của dropdown (None nếu đóng)."""
        if not self.is_open or not self.options:
            return None
        n = min(self.max_visible, len(self.options))
        return pygame.Rect(self.abs_x, self.abs_y + self.h, self.w, self.h * n)

    # ── Vẽ ───────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        """Vẽ combobox trực tiếp lên screen với tọa độ tuyệt đối."""
        self._draw_header(screen)
        if self.is_open and self.options:
            self._draw_dropdown(screen)

    def _clip_text(self, text: str, max_w: int) -> pygame.Surface:
        """Render text, cắt bớt nếu quá dài (thêm '...')."""
        s = self.font.render(text, True, C.CB_TEXT)
        if s.get_width() <= max_w:
            return s
        for i in range(len(text)-1, 0, -1):
            s2 = self.font.render(text[:i] + '...', True, C.CB_TEXT)
            if s2.get_width() <= max_w:
                return s2
        return self.font.render('...', True, C.CB_TEXT)

    def _draw_header(self, screen: pygame.Surface):
        x, y, w, h = self.abs_x, self.abs_y, self.w, self.h

        # Nền header
        bg = C.CB_SELECT if self.is_open else C.CB_BG
        pygame.draw.rect(screen, bg, (x, y, w, h), border_radius=5)
        pygame.draw.rect(screen, C.CB_BORDER, (x, y, w, h), 1, border_radius=5)

        # Text (tối đa w-30px để dành chỗ mũi tên)
        ts = self._clip_text(self.selected_text or '---', w - 30)
        screen.blit(ts, (x + 8, y + h//2 - ts.get_height()//2))

        # Mũi tên tam giác
        ax = x + w - 14
        ay = y + h//2
        if self.is_open:
            pts = [(ax-5, ay+3), (ax+5, ay+3), (ax, ay-3)]
        else:
            pts = [(ax-5, ay-3), (ax+5, ay-3), (ax, ay+3)]
        pygame.draw.polygon(screen, C.CB_ARROW, pts)

    def _draw_dropdown(self, screen: pygame.Surface):
        x       = self.abs_x
        drop_y  = self.abs_y + self.h
        w, h    = self.w, self.h
        n_show  = min(self.max_visible, len(self.options))
        drop_h  = h * n_show

        # Shadow / outline
        shadow_rect = pygame.Rect(x+2, drop_y+2, w, drop_h)
        pygame.draw.rect(screen, (5, 5, 12), shadow_rect, border_radius=5)

        # Nền dropdown
        pygame.draw.rect(screen, C.CB_BG, (x, drop_y, w, drop_h), border_radius=5)
        pygame.draw.rect(screen, C.CB_BORDER, (x, drop_y, w, drop_h), 1, border_radius=5)

        for i in range(n_show):
            idx = i + self._scroll
            if idx >= len(self.options):
                break

            iy        = drop_y + i * h
            item_rect = pygame.Rect(x, iy, w, h)

            # Highlight: selected = xanh đậm, hover = xanh nhạt
            if idx == self.selected:
                pygame.draw.rect(screen, C.CB_SELECT, item_rect)
            elif idx == self._hover_idx:
                pygame.draw.rect(screen, C.CB_HOVER, item_rect)

            # Divider (trừ item đầu)
            if i > 0:
                pygame.draw.line(screen, (30, 35, 60),
                                 (x+4, iy), (x+w-4, iy))

            # Text — màu trắng nếu selected
            text_col = C.WHITE if idx == self.selected else C.CB_TEXT
            ts = self._clip_text(self.options[idx], w - 16)
            # Recolor nếu cần
            if idx == self.selected and ts.get_colorkey() is None:
                ts = self.font.render(
                    self.options[idx][:self._max_chars(self.options[idx], w-16)],
                    True, C.WHITE)
            screen.blit(ts, (x + 8, iy + h//2 - ts.get_height()//2))

    def _max_chars(self, text: str, max_w: int) -> int:
        for i in range(len(text), 0, -1):
            if self.font.render(text[:i], True, C.WHITE).get_width() <= max_w:
                return i
        return 0

    # ── Event ────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Xử lý event. Trả về True nếu selection vừa thay đổi.
        """
        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(mx, my)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hdr = pygame.Rect(self.abs_x, self.abs_y, self.w, self.h)

            if hdr.collidepoint(mx, my):
                # Toggle dropdown
                self.is_open = not self.is_open
                return False

            if self.is_open:
                # Click trong dropdown?
                n_show = min(self.max_visible, len(self.options))
                for i in range(n_show):
                    idx = i + self._scroll
                    iy  = self.abs_y + self.h + i * self.h
                    item_rect = pygame.Rect(self.abs_x, iy, self.w, self.h)
                    if item_rect.collidepoint(mx, my) and idx < len(self.options):
                        old = self.selected
                        self.selected = idx
                        self.is_open  = False
                        self._hover_idx = -1
                        if self.on_change and old != idx:
                            self.on_change(idx)
                        return old != idx
                # Click ngoài → đóng
                self.is_open = False

        if event.type == pygame.MOUSEWHEEL and self.is_open:
            max_scroll = max(0, len(self.options) - self.max_visible)
            self._scroll = max(0, min(max_scroll, self._scroll - event.y))

        return False

    def _update_hover(self, mx: int, my: int):
        if not self.is_open:
            self._hover_idx = -1
            return
        n_show = min(self.max_visible, len(self.options))
        for i in range(n_show):
            idx = i + self._scroll
            iy  = self.abs_y + self.h + i * self.h
            if (self.abs_x <= mx < self.abs_x + self.w
                    and iy <= my < iy + self.h):
                self._hover_idx = idx
                return
        self._hover_idx = -1
