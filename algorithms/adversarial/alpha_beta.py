# algorithms/adversarial/alpha_beta.py

from collections import deque
import math
import time
from typing import List, Tuple, Dict, Set

from algorithms.base import PathResult, Step


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
SEARCH_DEPTH = 5
WIN_SCORE = 10000
LOSE_SCORE = -10000


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(grid, rows, cols, pos):
    r, c = pos
    result = []

    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 0:
            result.append((nr, nc))

    return result


def distance_map(grid, rows, cols, source):
    dist = {source: 0}
    q = deque([source])

    while q:
        cur = q.popleft()

        for nxt in neighbors(grid, rows, cols, cur):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)

    return dist


def choose_monster_start(grid, rows, cols, start, goal):
    dist_start = distance_map(grid, rows, cols, start)
    dist_goal = distance_map(grid, rows, cols, goal)

    candidates = []

    for pos in dist_start:
        if pos != start and pos != goal:
            if dist_start[pos] >= max(4, rows // 3):
                candidates.append(pos)

    if not candidates:
        candidates = [pos for pos in dist_start if pos != start and pos != goal]

    if not candidates:
        return goal

    return max(
        candidates,
        key=lambda p: (
            dist_start.get(p, 0),
            -dist_goal.get(p, rows + cols)
        )
    )


def run_alpha_beta(grid: List[List[int]],
                   start: Tuple[int, int],
                   goal: Tuple[int, int],
                   rows: int,
                   cols: int) -> PathResult:

    t0 = time.time()

    dist_goal = distance_map(grid, rows, cols, goal)
    dist_cache = {goal: dist_goal}

    player = start
    monster = choose_monster_start(grid, rows, cols, start, goal)
    monster_prev = None

    player_path = [player]
    visited: Set[Tuple[int, int]] = {player}

    steps: List[Step] = []

    nodes_total = 0
    prunes_total = 0

    def maze_distance(a, b):
        if a not in dist_cache:
            dist_cache[a] = distance_map(grid, rows, cols, a)
        return dist_cache[a].get(b, rows + cols)

    def evaluate(player_pos, monster_pos, trail_len, monster_prev_pos=None):
        if player_pos == goal:
            return WIN_SCORE - trail_len

        if player_pos == monster_pos:
            return LOSE_SCORE + dist_goal.get(player_pos, rows + cols)

        d_goal = dist_goal.get(player_pos, rows + cols)
        d_monster = maze_distance(player_pos, monster_pos)
        mobility = len(neighbors(grid, rows, cols, player_pos))
        reverse_penalty = 18 if monster_prev_pos and monster_pos == monster_prev_pos else 0

        danger = 0
        if d_monster <= 1:
            danger = 80
        elif d_monster == 2:
            danger = 30

        return (
            -d_goal * 20
            + d_monster * 12
            + mobility * 3
            - danger
            + reverse_penalty
            - trail_len * 0.5
        )

    def order_player_moves(player_pos, monster_pos):
        moves = neighbors(grid, rows, cols, player_pos)

        moves.sort(
            key=lambda p: (
                dist_goal.get(p, rows + cols),
                -maze_distance(p, monster_pos)
            )
        )

        return moves

    def order_monster_moves(monster_pos, player_pos, monster_prev_pos=None):
        moves = neighbors(grid, rows, cols, monster_pos)

        moves.sort(
            key=lambda p: (
                p == monster_prev_pos,
                maze_distance(p, player_pos)
            )
        )

        return moves if moves else [monster_pos]

    def _new_stats():
        return {
            "nodes": 0,
            "prunes": 0,
            "searched_cells": set(),
            "pruned_cells": set()
        }

    def alpha_beta(player_pos, monster_pos, trail, depth, maximizing, alpha, beta, stats,
                   monster_prev_pos=None):
        stats["nodes"] += 1
        stats["searched_cells"].add(player_pos)

        if depth == 0 or player_pos == goal or player_pos == monster_pos:
            return evaluate(player_pos, monster_pos, len(trail), monster_prev_pos), None

        if maximizing:
            best_score = -math.inf
            best_move = None

            moves = order_player_moves(player_pos, monster_pos)
            if not moves:
                return evaluate(player_pos, monster_pos, len(trail), monster_prev_pos), None

            for idx, move in enumerate(moves):
                score, _ = alpha_beta(
                    move,
                    monster_pos,
                    trail + (move,),
                    depth - 1,
                    False,
                    alpha,
                    beta,
                    stats,
                    monster_prev_pos
                )

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, best_score)

                if beta <= alpha:
                    skipped = moves[idx + 1:]
                    if skipped:
                        stats["prunes"] += 1
                        stats["pruned_cells"].update(skipped)
                    break

            return best_score, best_move

        else:
            best_score = math.inf
            best_move = None

            moves = order_monster_moves(monster_pos, player_pos, monster_prev_pos)
            if not moves:
                return evaluate(player_pos, monster_pos, len(trail), monster_prev_pos), None

            for idx, move in enumerate(moves):
                score, _ = alpha_beta(
                    player_pos,
                    move,
                    trail,
                    depth - 1,
                    True,
                    alpha,
                    beta,
                    stats,
                    monster_pos
                )

                if score < best_score:
                    best_score = score
                    best_move = move

                beta = min(beta, best_score)

                if beta <= alpha:
                    skipped = moves[idx + 1:]
                    if skipped:
                        stats["prunes"] += 1
                        stats["pruned_cells"].update(skipped)
                    break

            return best_score, best_move

    steps.append(Step(
        step_num=0,
        current=player,
        frontier=neighbors(grid, rows, cols, player),
        visited={player},
        path_so_far=[player],
        description=f"START | Player={player} | Monster={monster} | Alpha-Beta depth={SEARCH_DEPTH}",
        extra={
            "turn": "START",
            "monster_pos": monster,
            "score": 0,
            "depth": SEARCH_DEPTH,
            "nodes": 0,
            "prunes": 0,
            "pruned_cells": set(),
            "searched_cells": set(),
            "caught": False
        }
    ))

    found = False
    caught = False

    max_turns = min(rows * cols * 2, 600)

    for turn in range(1, max_turns + 1):
        if player == goal:
            found = True
            break

        if player == monster:
            caught = True
            break

        stats = _new_stats()

        score, player_move = alpha_beta(
            player,
            monster,
            tuple(player_path),
            SEARCH_DEPTH,
            True,
            -math.inf,
            math.inf,
            stats,
            monster_prev
        )

        if player_move is None:
            break

        candidates = order_player_moves(player, monster)

        player = player_move
        player_path.append(player)
        visited.update(stats["searched_cells"])
        visited.add(player)

        current_turn = "MAX"

        if player == goal:
            found = True
        elif player == monster:
            caught = True
        else:
            monster_stats = _new_stats()
            monster_score, next_monster = alpha_beta(
                player,
                monster,
                tuple(player_path),
                SEARCH_DEPTH,
                False,
                -math.inf,
                math.inf,
                monster_stats,
                monster_prev
            )
            monster_prev, monster = monster, next_monster

            score = min(score, monster_score)

            stats["nodes"] += monster_stats["nodes"]
            stats["prunes"] += monster_stats["prunes"]
            stats["searched_cells"].update(monster_stats["searched_cells"])
            stats["pruned_cells"].update(monster_stats["pruned_cells"])

            visited.update(monster_stats["searched_cells"])

            current_turn = "MIN"

            if player == monster:
                caught = True

        nodes_total += stats["nodes"]
        prunes_total += stats["prunes"]

        if found:
            status = "GOAL"
        elif caught:
            status = "CAUGHT"
        else:
            status = "CHASE"

        steps.append(Step(
            step_num=turn,
            current=player,
            frontier=candidates,
            visited=set(visited),
            path_so_far=list(player_path),
            description=(
                f"Turn {turn} | {current_turn} | {status} | "
                f"Player={player} | Monster={monster} | "
                f"score={score:.1f} | nodes={stats['nodes']} | prunes={stats['prunes']}"
            ),
            is_backtrack=caught,
            extra={
                "turn": current_turn,
                "monster_pos": monster,
                "score": score,
                "depth": SEARCH_DEPTH,
                "nodes": stats["nodes"],
                "prunes": stats["prunes"],
                "nodes_total": nodes_total,
                "prunes_total": prunes_total,
                "searched_cells": stats["searched_cells"],
                "pruned_cells": stats["pruned_cells"],
                "caught": caught,
                "status": status
            }
        ))

        if found or caught:
            break

    elapsed = (time.time() - t0) * 1000

    return PathResult(
        algo_name="Alpha-Beta",
        start=start,
        goal=goal,
        steps=steps,
        path=list(player_path) if found else [],
        total_visited=len(visited),
        found=found,
        elapsed_ms=elapsed
    )
