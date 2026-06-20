# main.py — Entry point AI Maze Solver
"""
AI Maze Solver — Mê Cung AI 30×30
5 nhóm thuật toán, chọn qua Combobox, chạy bằng nút PLAY.

Điều khiển:
  Combobox 1  : Chọn nhóm thuật toán
  Combobox 2  : Chọn tên thuật toán
  [PLAY btn]  : Chạy / Pause thuật toán
  [Space]     : Pause / Resume
  [→]         : Tiến 1 bước
  [←]         : Lùi 1 bước
  [Enter]     : Chạy lại thuật toán hiện tại
  [R]         : Sinh mê cung mới
  [Delete]    : Xóa kết quả
  [T]         : Đổi tốc độ (nhanh/bình thường/chậm)
  [H]         : Đổi theme
  [M]         : Bật/tắt Race Mode khi có thuật toán so sánh
  [↑↓]        : Di chuyển player lên/xuống
  [A/D]       : Di chuyển player trái/phải
  [ESC]       : Về menu
"""

import sys
import signal
import pygame
import config as C
from core.game import Game, PlaybackState
from ui.renderer import Renderer
from ui.menu import MenuScreen


def run_game(screen: pygame.Surface) -> str:
    """Chạy màn chơi. Trả về 'menu' | 'quit'."""
    clock    = pygame.time.Clock()
    game     = Game()
    renderer = Renderer(screen)

    while True:
        dt = min(clock.tick(C.FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'

            # ── Combobox và Play button ─────────────────────
            should_play = renderer.handle_event(event, game)
            if should_play:
                # Play button click: chạy hoặc pause
                if game.playback_state == PlaybackState.RUNNING:
                    game.toggle_pause()
                else:
                    algo = renderer.get_selected_algo()
                    if algo:
                        game.run_comparison(algo, renderer.get_compare_algo())
                    else:
                        game.message = "⚠ Vui lòng chọn thuật toán!"
                        game.message_color = C.VIZ_STUCK

            # ── Keyboard ────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                key = event.key

                if key == pygame.K_ESCAPE:
                    return 'menu'
                elif key == pygame.K_SPACE:
                    if game.playback_state in (PlaybackState.RUNNING,
                                               PlaybackState.PAUSED):
                        game.toggle_pause()
                    else:
                        # Nếu chưa chạy → chạy algo đang chọn
                        algo = renderer.get_selected_algo()
                        if algo:
                            game.run_comparison(algo, renderer.get_compare_algo())
                elif key == pygame.K_RIGHT:
                    game.step_forward()
                elif key == pygame.K_LEFT:
                    game.step_backward()
                elif key == pygame.K_RETURN:
                    game.replay_algo()
                elif key == pygame.K_r:
                    game.new_maze()
                elif key == pygame.K_DELETE:
                    game.reset_algo()
                elif key == pygame.K_t:
                    game.toggle_speed()
                elif key == pygame.K_h:
                    game.toggle_theme()
                elif key == pygame.K_m:
                    game.toggle_race_mode()
                # Di chuyển player
                elif key == pygame.K_UP    or key == pygame.K_w:
                    game.try_move_player(-1, 0)
                elif key == pygame.K_DOWN  or key == pygame.K_s:
                    game.try_move_player(1, 0)
                elif key == pygame.K_a:
                    game.try_move_player(0, -1)
                elif key == pygame.K_d:
                    game.try_move_player(0, 1)


        game.update(dt)
        renderer.render(game, dt)


def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    pygame.init()
    pygame.display.set_caption("AI Maze Solver - Me Cung AI")

    try:
        icon = pygame.image.load(C.LOGO_PATH)
        icon = pygame.transform.smoothscale(icon, (32, 32))
    except (pygame.error, FileNotFoundError, AttributeError):
        icon = pygame.Surface((32, 32))
        icon.fill((10, 10, 25))
        pygame.draw.circle(icon, C.START_COLOR, (8, 16), 5)
        pygame.draw.circle(icon, C.GOAL_COLOR, (24, 16), 5)
        pygame.draw.line(icon, C.VIZ_PATH, (13, 16), (19, 16), 2)
    pygame.display.set_icon(icon)

    screen  = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
    clock   = pygame.time.Clock()
    menu    = MenuScreen(screen)
    in_menu = True

    while True:
        dt = min(clock.tick(C.FPS) / 1000.0, 0.05)

        if in_menu:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                result = menu.handle_event(event)
                if result == 'start':
                    in_menu = False
                elif result == 'quit':
                    pygame.quit()
                    sys.exit()
            menu.update(dt)
            menu.draw()
            pygame.display.flip()
        else:
            result = run_game(screen)
            if result == 'quit':
                pygame.quit()
                sys.exit()
            else:
                in_menu = True
                menu = MenuScreen(screen)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
 