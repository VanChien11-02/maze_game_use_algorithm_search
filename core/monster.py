# core/monster.py

from typing import Tuple, List


class Monster:
    def __init__(self, pos: Tuple[int, int]):
        self.pos = pos
        self.path: List[Tuple[int, int]] = [pos]
        self.caught = False

    def move_to(self, new_pos: Tuple[int, int]):
        self.pos = new_pos
        self.path.append(new_pos)

    def reset(self, pos: Tuple[int, int]):
        self.pos = pos
        self.path = [pos]
        self.caught = False