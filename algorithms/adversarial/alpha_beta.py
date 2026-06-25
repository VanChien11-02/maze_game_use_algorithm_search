# algorithms/adversarial/alpha_beta.py

from collections import deque
import math
import time
from typing import List, Tuple, Dict, Set

import config as C
from algorithms.base import PathResult, Step


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
SEARCH_DEPTH = 5
WIN_SCORE = 10000
LOSE_SCORE = -10000
REVISIT_PENALTY = 75
LOOP_PENALTY = 260
LOOP_REPEATS = 3
LOOP_MAX_PERIOD = 5


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


def repeated_pattern(path, min_repeats=LOOP_REPEATS, max_period=LOOP_MAX_PERIOD):
    if len(path) < min_repeats * 2:
        return ()

    max_period = min(max_period, len(path) // min_repeats)
    for period in range(2, max_period + 1):
        pattern = tuple(path[-period:])
        ok = True
        for repeat in range(2, min_repeats + 1):
            start = -period * repeat
            end = -period * (repeat - 1)
            if tuple(path[start:end]) != pattern:
                ok = False
                break
        if ok:
            return pattern

    return ()


def run_alpha_beta(grid: List[List[int]],
                   start: Tuple[int, int],
                   goal: Tuple[int, int],
                   rows: int,
                   cols: int) -> PathResult:

    t0 = time.time()
    search_depth = getattr(C, "ALPHA_BETA_DEPTH", SEARCH_DEPTH)

    dist_goal = distance_map(grid, rows, cols, goal)
    dist_cache = {goal: dist_goal}
    transposition: Dict[tuple, tuple] = {}

    player = start
    monster = choose_monster_start(grid, rows, cols, start, goal)
    monster_prev = None

    player_path = [player]
    visited: Set[Tuple[int, int]] = {player}

    steps: List[Step] = []

    nodes_total = 0
    prunes_total = 0
    cache_hits_total = 0
    step_counter = 0

    def maze_distance(a, b):
        if a not in dist_cache:
            dist_cache[a] = distance_map(grid, rows, cols, a)
        return dist_cache[a].get(b, rows + cols)

    def evaluate(player_pos, monster_pos, trail, monster_prev_pos=None):
        trail_len = len(trail)
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

        repeat_count = max(0, trail_len - len(set(trail)))
        current_revisit_count = max(0, trail[:-1].count(player_pos))
        loop_pattern = repeated_pattern(trail)
        revisit_penalty = (
            repeat_count * REVISIT_PENALTY
            + current_revisit_count * REVISIT_PENALTY
            + (LOOP_PENALTY if loop_pattern else 0)
        )

        return (
            -d_goal * 20
            + d_monster * 12
            + mobility * 3
            - danger
            + reverse_penalty
            - trail_len * 0.5
            - revisit_penalty
        )

    def order_player_moves(player_pos, monster_pos, trail=()):
        moves = neighbors(grid, rows, cols, player_pos)
        recent = set(trail[-LOOP_MAX_PERIOD:])

        moves.sort(
            key=lambda p: (
                p in recent,
                p in trail,
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
            "cache_hits": 0,
            "searched_cells": set(),
            "pruned_cells": set(),
            "loop_detected": False,
            "loop_pattern": ()
        }

    def alpha_beta(player_pos, monster_pos, trail, depth, maximizing, alpha, beta, stats,
                   monster_prev_pos=None):
        stats["nodes"] += 1
        stats["searched_cells"].add(player_pos)

        repeat_count = len(trail) - len(set(trail))
        cache_key = (
            player_pos,
            monster_pos,
            depth,
            maximizing,
            monster_prev_pos,
            len(trail),
            repeat_count,
            trail.count(player_pos),
            tuple(trail[-8:]),
        )
        cached = transposition.get(cache_key)
        if cached is not None:
            stats["cache_hits"] += 1
            return cached

        if depth == 0 or player_pos == goal or player_pos == monster_pos:
            result = (evaluate(player_pos, monster_pos, trail, monster_prev_pos), None)
            transposition[cache_key] = result
            return result

        if maximizing:
            best_score = -math.inf
            best_move = None

            moves = order_player_moves(player_pos, monster_pos, trail)
            if not moves:
                result = (evaluate(player_pos, monster_pos, trail, monster_prev_pos), None)
                transposition[cache_key] = result
                return result

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

            result = (best_score, best_move)
            transposition[cache_key] = result
            return result

        else:
            best_score = math.inf
            best_move = None

            moves = order_monster_moves(monster_pos, player_pos, monster_prev_pos)
            if not moves:
                result = (evaluate(player_pos, monster_pos, trail, monster_prev_pos), None)
                transposition[cache_key] = result
                return result

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

            result = (best_score, best_move)
            transposition[cache_key] = result
            return result

    def choose_player_move(player_pos, monster_pos, trail, monster_prev_pos=None):
        stats = _new_stats()
        stats["nodes"] += 1
        stats["searched_cells"].add(player_pos)

        moves = order_player_moves(player_pos, monster_pos, trail)
        pattern = repeated_pattern(trail)
        if pattern:
            stats["loop_detected"] = True
            stats["loop_pattern"] = pattern
            loop_cells = set(pattern)
            non_loop_moves = [move for move in moves if move not in loop_cells]
            if non_loop_moves:
                moves = non_loop_moves
            else:
                return None, None, stats, moves

        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf

        for idx, move in enumerate(moves):
            score, _ = alpha_beta(
                move,
                monster_pos,
                trail + (move,),
                search_depth - 1,
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

        return best_score, best_move, stats, moves

    steps.append(Step(
        step_num=0,
        current=player,
        frontier=neighbors(grid, rows, cols, player),
        visited={player},
        path_so_far=[player],
        description=f"START | Player={player} | Monster={monster} | Alpha-Beta depth={search_depth}",
        extra={
            "turn": "START",
            "monster_pos": monster,
            "score": 0,
            "depth": search_depth,
            "nodes": 0,
            "prunes": 0,
            "cache_hits": 0,
            "pruned_cells": set(),
            "searched_cells": set(),
            "caught": False
        }
    ))

    found = False
    caught = False
    looped = False

    max_turns = min(rows * cols * 2, 600)

    for turn in range(1, max_turns + 1):
        if player == goal:
            found = True
            break

        if player == monster:
            caught = True
            break

        score, player_move, stats, candidates = choose_player_move(
            player,
            monster,
            tuple(player_path),
            monster_prev
        )

        if player_move is None:
            looped = bool(stats.get("loop_detected"))
            nodes_total += stats["nodes"]
            prunes_total += stats["prunes"]
            cache_hits_total += stats["cache_hits"]
            step_counter += 1
            status = "LOOP" if looped else "NO_MOVE"
            steps.append(Step(
                step_num=step_counter,
                current=player,
                frontier=candidates,
                visited=set(visited),
                path_so_far=list(player_path),
                description=(
                    f"Turn {turn} | MAX | {status} | "
                    f"Player={player} | Monster={monster} | "
                    f"nodes={stats['nodes']} | prunes={stats['prunes']}"
                ),
                is_backtrack=True,
                extra={
                    "turn": "MAX",
                    "monster_pos": monster,
                    "score": score or 0,
                    "depth": search_depth,
                    "nodes": stats["nodes"],
                    "prunes": stats["prunes"],
                    "cache_hits": stats["cache_hits"],
                    "nodes_total": nodes_total,
                    "prunes_total": prunes_total,
                    "cache_hits_total": cache_hits_total,
                    "searched_cells": stats["searched_cells"],
                    "pruned_cells": stats["pruned_cells"],
                    "loop_detected": stats["loop_detected"],
                    "loop_pattern": stats["loop_pattern"],
                    "caught": False,
                    "status": status
                }
            ))
            break

        player = player_move
        player_path.append(player)
        visited.update(stats["searched_cells"])
        visited.add(player)

        if player == goal:
            found = True
        elif player == monster:
            caught = True

        nodes_total += stats["nodes"]
        prunes_total += stats["prunes"]
        cache_hits_total += stats["cache_hits"]

        if found:
            status = "GOAL"
        elif caught:
            status = "CAUGHT"
        else:
            status = "CHASE"

        step_counter += 1
        steps.append(Step(
            step_num=step_counter,
            current=player,
            frontier=candidates,
            visited=set(visited),
            path_so_far=list(player_path),
            description=(
                f"Turn {turn} | MAX | {status} | "
                f"Player={player} | Monster={monster} | "
                f"score={score:.1f} | nodes={stats['nodes']} | prunes={stats['prunes']}"
            ),
            is_backtrack=caught,
            extra={
                "turn": "MAX",
                "monster_pos": monster,
                "score": score,
                "depth": search_depth,
                "nodes": stats["nodes"],
                "prunes": stats["prunes"],
                "cache_hits": stats["cache_hits"],
                "nodes_total": nodes_total,
                "prunes_total": prunes_total,
                "cache_hits_total": cache_hits_total,
                "searched_cells": stats["searched_cells"],
                "pruned_cells": stats["pruned_cells"],
                "loop_detected": stats["loop_detected"],
                "loop_pattern": stats["loop_pattern"],
                "caught": caught,
                "status": status
            }
        ))

        if found or caught:
            break

        monster_from = monster
        monster_before_from = monster_prev
        monster_stats = _new_stats()
        monster_score, next_monster = alpha_beta(
            player,
            monster,
            tuple(player_path),
            search_depth,
            False,
            -math.inf,
            math.inf,
            monster_stats,
            monster_prev
        )
        if next_monster is None:
            next_monster = monster
        monster_prev, monster = monster, next_monster

        score = min(score, monster_score)
        visited.update(monster_stats["searched_cells"])

        if player == monster:
            caught = True

        nodes_total += monster_stats["nodes"]
        prunes_total += monster_stats["prunes"]
        cache_hits_total += monster_stats["cache_hits"]

        status = "CAUGHT" if caught else "CHASE"

        step_counter += 1
        steps.append(Step(
            step_num=step_counter,
            current=player,
            frontier=order_monster_moves(monster_from, player, monster_before_from),
            visited=set(visited),
            path_so_far=list(player_path),
            description=(
                f"Turn {turn} | MIN | {status} | "
                f"Player={player} | Monster={monster} | "
                f"score={score:.1f} | nodes={monster_stats['nodes']} | "
                f"prunes={monster_stats['prunes']}"
            ),
            is_backtrack=caught,
            extra={
                "turn": "MIN",
                "monster_pos": monster,
                "score": score,
                "depth": search_depth,
                "nodes": monster_stats["nodes"],
                "prunes": monster_stats["prunes"],
                "cache_hits": monster_stats["cache_hits"],
                "nodes_total": nodes_total,
                "prunes_total": prunes_total,
                "cache_hits_total": cache_hits_total,
                "searched_cells": monster_stats["searched_cells"],
                "pruned_cells": monster_stats["pruned_cells"],
                "loop_detected": False,
                "loop_pattern": (),
                "caught": caught,
                "status": status
            }
        ))

        if caught:
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
