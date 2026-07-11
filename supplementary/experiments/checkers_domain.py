#!/usr/bin/env python3
"""
Checkers domain for the multi-domain topology sweep.

Standard 8x8 American Checkers (English Draughts) with greedy (0-ply) play.
A 64-bit genome encodes 8 evaluation weights (8 bits each):
  material, kings, center, advance, back_row, mobility, safety, threat.

Fitness is determined by round-robin tournament within each island population.
Each pair plays one game (first individual = red). Fitness = total_points / (n-1).

This creates a COEVOLUTIONARY landscape: fitness is relative to opponents,
making it inherently topology-sensitive as migration introduces new strategies.
"""

import os
from multiprocessing import Pool

import numpy as np

_NUM_WORKERS = min(8, os.cpu_count() or 4)
_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = Pool(_NUM_WORKERS)
    return _pool


def _play_game_pair(args):
    """Play one checkers game between two weight vectors. For Pool.map."""
    weights_i, weights_j, seed = args
    rng = np.random.default_rng(seed)
    return play_game(weights_i, weights_j, rng)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHECKERS_GENOME_LENGTH = 64  # 8 features x 8 bits each
NUM_FEATURES = 8
BITS_PER_FEATURE = 8
MAX_MOVES = 40  # half-move limit before draw (captures resolve most games)

# Board values
EMPTY = 0
RED = 1
RED_KING = 2
BLACK = -1
BLACK_KING = -2

# Diagonal move offsets for an 8x8 board: (row_delta, col_delta)
_FORWARD_RED = [(-1, -1), (-1, 1)]    # Red moves "up" (decreasing row)
_FORWARD_BLACK = [(1, -1), (1, 1)]    # Black moves "down" (increasing row)
_ALL_DIAGS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


# ---------------------------------------------------------------------------
# Board initialization
# ---------------------------------------------------------------------------

def init_board() -> np.ndarray:
    """Create starting 8x8 checkers board.

    Black pieces on rows 0-2 (dark squares), red on rows 5-7.
    Dark squares are those where (row + col) % 2 == 1.
    """
    board = np.zeros((8, 8), dtype=np.int8)
    for r in range(8):
        for c in range(8):
            if (r + c) % 2 == 1:  # dark square
                if r < 3:
                    board[r, c] = BLACK
                elif r > 4:
                    board[r, c] = RED
    return board


# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _get_jumps(board: np.ndarray, r: int, c: int, piece: int) -> list:
    """Get all jump sequences from position (r, c) for the given piece.

    Returns list of (moves_list, captures_list) where each is a multi-jump
    sequence. moves_list = [(r1,c1), (r2,c2), ...] landing squares.
    captures_list = [(cr1,cc1), ...] captured piece positions.
    """
    is_king = (piece == RED_KING or piece == BLACK_KING)
    if piece > 0:  # red
        dirs = _ALL_DIAGS if is_king else _FORWARD_RED
    else:  # black
        dirs = _ALL_DIAGS if is_king else _FORWARD_BLACK

    results = []
    _find_jumps(board, r, c, piece, dirs, is_king, [], [], set(), results)
    return results


def _find_jumps(board, r, c, piece, dirs, is_king, moves_so_far,
                captures_so_far, captured_set, results):
    """Recursive DFS for multi-jump sequences."""
    found_jump = False
    for dr, dc in dirs:
        mr, mc = r + dr, c + dc  # middle square (captured piece)
        lr, lc = r + 2 * dr, c + 2 * dc  # landing square
        if not (0 <= lr < 8 and 0 <= lc < 8):
            continue
        mid_pos = (mr, mc)
        if mid_pos in captured_set:
            continue
        mid_piece = board[mr, mc]
        # Must jump over an enemy piece onto an empty square
        if mid_piece == EMPTY or (mid_piece > 0) == (piece > 0):
            continue
        if board[lr, lc] != EMPTY and (lr, lc) != (r, c):
            # Landing square occupied (unless it's our start in a loop, which
            # shouldn't happen in standard checkers)
            continue

        found_jump = True
        new_moves = moves_so_far + [(lr, lc)]
        new_captures = captures_so_far + [mid_pos]
        new_captured = captured_set | {mid_pos}

        # Check for promotion mid-jump: in standard checkers, promotion
        # ends the turn (the piece stops on the king row)
        promoted = False
        if not is_king:
            if piece > 0 and lr == 0:  # red reaches row 0
                promoted = True
            elif piece < 0 and lr == 7:  # black reaches row 7
                promoted = True

        if promoted:
            # Promotion ends the multi-jump
            results.append((new_moves, new_captures))
        else:
            # Continue searching for more jumps
            _find_jumps(board, lr, lc, piece, dirs, is_king,
                        new_moves, new_captures, new_captured, results)

    if not found_jump and moves_so_far:
        # No more jumps available, record this sequence
        results.append((moves_so_far, captures_so_far))


def get_all_moves(board: np.ndarray, side: int) -> list:
    """Get all legal moves for the given side (RED=1 or BLACK=-1).

    Returns list of (from_r, from_c, moves_list, captures_list) tuples.
    If any jumps exist, ONLY jumps are returned (forced capture rule).
    moves_list = list of landing squares for multi-jumps, or single landing.
    captures_list = list of captured positions (empty for simple moves).
    """
    jumps = []

    # First pass: find all jumps
    for r in range(8):
        for c in range(8):
            piece = board[r, c]
            if piece == EMPTY:
                continue
            if side > 0 and piece <= 0:
                continue
            if side < 0 and piece >= 0:
                continue

            piece_jumps = _get_jumps(board, r, c, piece)
            for move_seq, cap_seq in piece_jumps:
                jumps.append((r, c, move_seq, cap_seq))

    # Forced capture: if any jumps exist, must jump
    if jumps:
        return jumps

    # Second pass: simple moves only (no jumps found)
    simple_moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r, c]
            if piece == EMPTY:
                continue
            if side > 0 and piece <= 0:
                continue
            if side < 0 and piece >= 0:
                continue

            is_king = (piece == RED_KING or piece == BLACK_KING)
            if piece > 0:
                dirs = _ALL_DIAGS if is_king else _FORWARD_RED
            else:
                dirs = _ALL_DIAGS if is_king else _FORWARD_BLACK

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == EMPTY:
                    simple_moves.append((r, c, [(nr, nc)], []))

    return simple_moves


def apply_move(board: np.ndarray, from_r: int, from_c: int,
               moves_list: list, captures_list: list) -> np.ndarray:
    """Apply a move to the board. Returns a NEW board (copy).

    moves_list: list of (r, c) landing squares (multi-jump chain)
    captures_list: list of (r, c) captured piece positions
    """
    new_board = board.copy()
    piece = new_board[from_r, from_c]
    new_board[from_r, from_c] = EMPTY

    # Remove captured pieces
    for cr, cc in captures_list:
        new_board[cr, cc] = EMPTY

    # Place piece at final destination
    final_r, final_c = moves_list[-1]
    new_board[final_r, final_c] = piece

    # King promotion
    if piece == RED and final_r == 0:
        new_board[final_r, final_c] = RED_KING
    elif piece == BLACK and final_r == 7:
        new_board[final_r, final_c] = BLACK_KING

    return new_board


def _apply_move_inplace(board, from_r, from_c, moves_list, captures_list):
    """Apply move in-place. Returns (piece, final_piece, captured_values)
    for undo."""
    piece = board[from_r, from_c]
    board[from_r, from_c] = EMPTY

    # Save and remove captured pieces
    captured_values = []
    for cr, cc in captures_list:
        captured_values.append(board[cr, cc])
        board[cr, cc] = EMPTY

    final_r, final_c = moves_list[-1]

    # King promotion
    final_piece = piece
    if piece == RED and final_r == 0:
        final_piece = RED_KING
    elif piece == BLACK and final_r == 7:
        final_piece = BLACK_KING

    board[final_r, final_c] = final_piece
    return piece, final_piece, captured_values


def _undo_move_inplace(board, from_r, from_c, moves_list, captures_list,
                       piece, captured_values):
    """Undo an in-place move."""
    final_r, final_c = moves_list[-1]
    board[final_r, final_c] = EMPTY
    board[from_r, from_c] = piece

    # Restore captured pieces
    for i, (cr, cc) in enumerate(captures_list):
        board[cr, cc] = captured_values[i]


# ---------------------------------------------------------------------------
# Board evaluation features
# ---------------------------------------------------------------------------

def evaluate_board(board: np.ndarray, side: int, weights: np.ndarray,
                   my_moves_count: int = -1) -> float:
    """Evaluate a board position from the perspective of `side`.

    weights: array of 8 floats (decoded genome).
    my_moves_count: number of legal moves for `side` (pass if already known).

    Uses a single Python loop over 64 cells — faster than numpy for small boards
    because it avoids function-call overhead.
    """
    # Single pass over board to collect all features
    my_pieces = 0
    my_kings = 0
    opp_pieces = 0
    opp_kings = 0
    my_center = 0
    my_advance_sum = 0
    my_back_row = 0
    my_edge = 0
    threat_count = 0

    # Access board data directly (flat view for speed)
    bd = board  # 8x8 int8 array

    is_red = (side > 0)

    for r in range(8):
        row = bd[r]
        for c in range(8):
            p = row[c]
            if p == 0:
                continue

            if is_red:
                mine = (p > 0)
            else:
                mine = (p < 0)

            if mine:
                my_pieces += 1
                ap = p if p > 0 else -p
                if ap == 2:
                    my_kings += 1
                if 2 <= r <= 5 and 2 <= c <= 5:
                    my_center += 1
                if is_red:
                    my_advance_sum += (7 - r)
                else:
                    my_advance_sum += r
                if is_red and r == 7:
                    my_back_row += 1
                elif not is_red and r == 0:
                    my_back_row += 1
                if r == 0 or r == 7 or c == 0 or c == 7:
                    my_edge += 1
                # Threat: can we jump an opponent from here?
                if ap == 2:
                    dirs = _ALL_DIAGS
                elif p > 0:
                    dirs = _FORWARD_RED
                else:
                    dirs = _FORWARD_BLACK
                for dr, dc in dirs:
                    mr = r + dr
                    mc = c + dc
                    lr = r + 2 * dr
                    lc = c + 2 * dc
                    if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
                        mp = bd[mr, mc]
                        if mp != 0:
                            if is_red:
                                is_opp = (mp < 0)
                            else:
                                is_opp = (mp > 0)
                            if is_opp and bd[lr, lc] == 0:
                                threat_count += 1
            else:
                opp_pieces += 1
                if p == 2 or p == -2:
                    opp_kings += 1

    if my_pieces == 0:
        return -1000.0

    inv_my = 1.0 / my_pieces
    # Feature 0: material advantage
    f0 = (my_pieces - opp_pieces) * 0.08333333333333333  # /12
    # Feature 1: king advantage
    f1 = (my_kings - opp_kings) * 0.08333333333333333
    # Feature 2: center control
    f2 = my_center * inv_my
    # Feature 3: advancement
    f3 = my_advance_sum * inv_my * 0.14285714285714285  # /7
    # Feature 4: back row
    f4 = my_back_row * inv_my
    # Feature 5: mobility
    f5 = min(1.0, my_moves_count * 0.05) if my_moves_count >= 0 else 0.5
    # Feature 6: edge safety (approximation)
    f6 = my_edge * inv_my if my_edge <= my_pieces else 1.0
    # Feature 7: threat
    f7 = threat_count / max(1, opp_pieces) if threat_count <= opp_pieces else 1.0

    return (weights[0] * f0 + weights[1] * f1 + weights[2] * f2 +
            weights[3] * f3 + weights[4] * f4 + weights[5] * f5 +
            weights[6] * f6 + weights[7] * f7)


# ---------------------------------------------------------------------------
# Genome decoding
# ---------------------------------------------------------------------------

def decode_genome(genome: np.ndarray) -> np.ndarray:
    """Decode 64-bit genome into 8 float weights (0-255 each)."""
    weights = np.zeros(NUM_FEATURES, dtype=np.float64)
    for i in range(NUM_FEATURES):
        bits = genome[i * BITS_PER_FEATURE:(i + 1) * BITS_PER_FEATURE]
        # Convert 8 bits to integer (MSB first)
        val = 0
        for b in bits:
            val = (val << 1) | int(b)
        weights[i] = float(val)
    return weights


# ---------------------------------------------------------------------------
# Game play
# ---------------------------------------------------------------------------

def play_game(weights_red: np.ndarray, weights_black: np.ndarray,
              rng: np.random.Generator) -> float:
    """Play one game of checkers. Red moves first.

    Uses greedy (0-ply) strategy: evaluate all legal moves, pick the best.

    Returns: score for red player (1.0 = win, 0.5 = draw, 0.0 = loss).
    """
    board = init_board()
    current_side = RED  # red moves first

    for half_move in range(MAX_MOVES):
        if current_side == RED:
            weights = weights_red
        else:
            weights = weights_black

        moves = get_all_moves(board, current_side)

        if not moves:
            # No legal moves = loss for current side
            if current_side == RED:
                return 0.0  # red loses
            else:
                return 1.0  # red wins

        # If only one move, skip evaluation
        if len(moves) == 1:
            from_r, from_c, move_seq, cap_seq = moves[0]
            piece, final_piece, cap_vals = _apply_move_inplace(
                board, from_r, from_c, move_seq, cap_seq)
        else:
            # Greedy: evaluate each resulting board using in-place apply/undo
            best_score = -float('inf')
            best_indices = []
            n_moves = len(moves)

            for mi, (from_r, from_c, move_seq, cap_seq) in enumerate(moves):
                piece, final_piece, cap_vals = _apply_move_inplace(
                    board, from_r, from_c, move_seq, cap_seq)
                score = evaluate_board(board, current_side, weights,
                                       my_moves_count=n_moves)
                _undo_move_inplace(board, from_r, from_c, move_seq, cap_seq,
                                   piece, cap_vals)
                if score > best_score:
                    best_score = score
                    best_indices = [mi]
                elif score == best_score:
                    best_indices.append(mi)

            # Break ties randomly
            chosen = best_indices[rng.integers(0, len(best_indices))]
            from_r, from_c, move_seq, cap_seq = moves[chosen]
            piece, final_piece, cap_vals = _apply_move_inplace(
                board, from_r, from_c, move_seq, cap_seq)

        # Check if opponent has any pieces left
        opp_side = -current_side
        opp_has_pieces = False
        for r in range(8):
            for c in range(8):
                p = board[r, c]
                if p != EMPTY and ((opp_side > 0 and p > 0) or (opp_side < 0 and p < 0)):
                    opp_has_pieces = True
                    break
            if opp_has_pieces:
                break

        if not opp_has_pieces:
            # Current side captured all opponent pieces = win
            if current_side == RED:
                return 1.0
            else:
                return 0.0

        current_side = opp_side

    # Exceeded move limit = draw
    return 0.5


# ---------------------------------------------------------------------------
# Population-level functions
# ---------------------------------------------------------------------------

_SWISS_ROUNDS = 5  # max opponents per individual in Swiss-style tournament
_eval_cache = {}  # LRU-style cache for recent evaluations
_CACHE_SIZE = 20  # keep last N evaluations


def evaluate_checkers(pop: np.ndarray) -> np.ndarray:
    """Tournament evaluation for checkers.

    For small populations (n <= 20): full round-robin, each pair plays one game.
    For large populations (n > 20): Swiss-style, each individual plays up to
    SWISS_ROUNDS random opponents. This keeps evaluation cost bounded.

    Fitness = total_points / games_played, normalized to [0, 1].

    Args:
        pop: (pop_size, 64) int8 binary array.

    Returns: (pop_size,) float64 array of fitnesses in [0, 1].
    """
    global _eval_cache
    n = len(pop)
    if n == 0:
        return np.array([], dtype=np.float64)
    if n == 1:
        return np.array([0.5], dtype=np.float64)

    # Check cache (avoids redundant evaluation for metrics calls)
    cache_key = hash(pop.tobytes())
    if cache_key in _eval_cache:
        cached = _eval_cache[cache_key]
        if len(cached) == n:
            return cached.copy()

    # Pre-decode all genomes
    all_weights = np.array([decode_genome(pop[i]) for i in range(n)])

    # Use a fixed rng for tie-breaking within a single evaluation call
    rng = np.random.default_rng(cache_key % (2**31))

    points = np.zeros(n, dtype=np.float64)
    games_played = np.zeros(n, dtype=np.float64)

    if n <= 20:
        # Full round-robin — parallelized across worker pool
        tasks = []
        pair_indices = []
        for i in range(n):
            for j in range(i + 1, n):
                seed = int((cache_key + i * n + j) % (2**31))
                tasks.append((all_weights[i], all_weights[j], seed))
                pair_indices.append((i, j))

        results = _get_pool().map(_play_game_pair, tasks)

        for (i, j), result in zip(pair_indices, results):
            points[i] += result
            points[j] += (1.0 - result)
            games_played[i] += 1
            games_played[j] += 1
    else:
        # Swiss-style — parallelized across worker pool
        tasks = []
        pair_list = []
        for i in range(n):
            opponents = rng.choice(n - 1, size=min(_SWISS_ROUNDS, n - 1),
                                   replace=False)
            for opp_idx in opponents:
                j = int(opp_idx if opp_idx < i else opp_idx + 1)
                seed = int(rng.integers(0, 2**31))
                tasks.append((all_weights[i], all_weights[j], seed))
                pair_list.append((i, j))

        results = _get_pool().map(_play_game_pair, tasks)

        for (i, j), result in zip(pair_list, results):
            points[i] += result
            points[j] += (1.0 - result)
            games_played[i] += 1
            games_played[j] += 1

    # Normalize to [0, 1]
    fitnesses = points / np.maximum(1, games_played)

    # Cache result (keep cache bounded)
    _eval_cache[cache_key] = fitnesses.copy()
    if len(_eval_cache) > _CACHE_SIZE:
        # Remove oldest entry
        oldest_key = next(iter(_eval_cache))
        del _eval_cache[oldest_key]

    return fitnesses


def random_checkers_population(rng, pop_size,
                               genome_length=CHECKERS_GENOME_LENGTH):
    """Generate random checkers population (uniform binary).

    Args:
        rng: numpy random Generator.
        pop_size: number of individuals.
        genome_length: must be CHECKERS_GENOME_LENGTH (64).

    Returns: (pop_size, 64) int8 array.
    """
    return rng.integers(0, 2, size=(pop_size, genome_length), dtype=np.int8)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_checkers_domain():
    """Self-tests for the checkers domain."""
    print("=== Checkers Domain Self-Test ===\n")

    # Test 1: Board initialization
    board = init_board()
    black_count = np.sum((board == BLACK) | (board == BLACK_KING))
    red_count = np.sum((board == RED) | (board == RED_KING))
    assert black_count == 12, f"Expected 12 black pieces, got {black_count}"
    assert red_count == 12, f"Expected 12 red pieces, got {red_count}"
    # Verify pieces are on dark squares only
    for r in range(8):
        for c in range(8):
            if board[r, c] != EMPTY:
                assert (r + c) % 2 == 1, (
                    f"Piece at ({r},{c}) is not on a dark square"
                )
    print(f"[PASS] Test 1: Board init correct — 12 black, 12 red, all on dark squares")

    # Test 2: Legal move generation — opening position
    red_moves = get_all_moves(board, RED)
    black_moves = get_all_moves(board, BLACK)
    # In starting position, each side has 7 simple moves (no jumps)
    assert len(red_moves) == 7, (
        f"Red should have 7 opening moves, got {len(red_moves)}"
    )
    assert len(black_moves) == 7, (
        f"Black should have 7 opening moves, got {len(black_moves)}"
    )
    # Verify all are simple moves (no captures)
    for _, _, _, caps in red_moves:
        assert len(caps) == 0, "No captures should exist in opening position"
    print(f"[PASS] Test 2: Opening moves — red={len(red_moves)}, black={len(black_moves)}")

    # Test 3: Forced captures
    # Set up a position where red MUST jump
    test_board = np.zeros((8, 8), dtype=np.int8)
    test_board[4, 3] = RED       # red piece at (4,3)
    test_board[3, 2] = BLACK     # black piece at (3,2) — can be jumped
    test_board[3, 4] = BLACK     # black piece at (3,4) — can be jumped
    moves = get_all_moves(test_board, RED)
    # Should only return jump moves (forced capture)
    assert all(len(caps) > 0 for _, _, _, caps in moves), (
        "When captures are available, only capture moves should be returned"
    )
    assert len(moves) >= 1, "Should have at least one jump"
    print(f"[PASS] Test 3: Forced captures — {len(moves)} jump(s) when captures available")

    # Test 4: Multi-jumps
    test_board2 = np.zeros((8, 8), dtype=np.int8)
    test_board2[6, 1] = RED
    test_board2[5, 2] = BLACK     # first jump
    test_board2[3, 4] = BLACK     # second jump (after landing on 4,3)
    moves2 = get_all_moves(test_board2, RED)
    # Should find the multi-jump sequence
    max_caps = max(len(caps) for _, _, _, caps in moves2)
    assert max_caps == 2, (
        f"Should find double-jump, max captures = {max_caps}"
    )
    print(f"[PASS] Test 4: Multi-jump — found {max_caps}-capture sequence")

    # Test 5: King promotion
    test_board3 = np.zeros((8, 8), dtype=np.int8)
    test_board3[1, 2] = RED  # one step from promotion
    moves3 = get_all_moves(test_board3, RED)
    assert len(moves3) == 2, f"Red at (1,2) should have 2 moves, got {len(moves3)}"
    # Apply move to row 0 — should promote
    for from_r, from_c, move_seq, cap_seq in moves3:
        new_board = apply_move(test_board3, from_r, from_c, move_seq, cap_seq)
        final_r, final_c = move_seq[-1]
        if final_r == 0:
            assert new_board[final_r, final_c] == RED_KING, (
                f"Red piece should promote to king at row 0, "
                f"got {new_board[final_r, final_c]}"
            )
    print(f"[PASS] Test 5: King promotion — red promoted at row 0")

    # Test 6: King moves (backward movement)
    test_board4 = np.zeros((8, 8), dtype=np.int8)
    test_board4[3, 4] = RED_KING  # king in middle of board
    moves4 = get_all_moves(test_board4, RED)
    # King should be able to move in all 4 diagonal directions
    destinations = set()
    for _, _, move_seq, _ in moves4:
        destinations.add(move_seq[-1])
    expected = {(2, 3), (2, 5), (4, 3), (4, 5)}
    assert destinations == expected, (
        f"King at (3,4) should reach {expected}, got {destinations}"
    )
    print(f"[PASS] Test 6: King moves — all 4 diagonals accessible")

    # Test 7: Genome decoding
    genome = np.zeros(CHECKERS_GENOME_LENGTH, dtype=np.int8)
    weights = decode_genome(genome)
    assert weights.shape == (NUM_FEATURES,), f"Wrong shape: {weights.shape}"
    assert np.all(weights == 0.0), "All-zero genome should give zero weights"

    genome_max = np.ones(CHECKERS_GENOME_LENGTH, dtype=np.int8)
    weights_max = decode_genome(genome_max)
    assert np.all(weights_max == 255.0), (
        f"All-ones genome should give 255 weights, got {weights_max}"
    )
    print(f"[PASS] Test 7: Genome decoding — zeros→0, ones→255")

    # Test 8: Evaluation function shape and range
    rng = np.random.default_rng(42)
    pop = random_checkers_population(rng, 8)
    fitnesses = evaluate_checkers(pop)
    assert fitnesses.dtype == np.float64, f"Expected float64, got {fitnesses.dtype}"
    assert len(fitnesses) == 8, f"Expected 8 fitnesses, got {len(fitnesses)}"
    assert np.all(fitnesses >= 0.0), f"Found negative fitness: {fitnesses.min()}"
    assert np.all(fitnesses <= 1.0), f"Found fitness > 1: {fitnesses.max()}"
    print(f"[PASS] Test 8: evaluate_checkers — 8 individuals, "
          f"fitnesses in [{fitnesses.min():.3f}, {fitnesses.max():.3f}]")

    # Test 9: A complete game terminates
    rng2 = np.random.default_rng(99)
    w_red = decode_genome(random_checkers_population(rng2, 1)[0])
    w_black = decode_genome(random_checkers_population(rng2, 1)[0])
    result = play_game(w_red, w_black, rng2)
    assert result in (0.0, 0.5, 1.0), f"Game result should be 0, 0.5, or 1; got {result}"
    print(f"[PASS] Test 9: Complete game terminates — result={result}")

    # Test 10: Tournament produces valid distribution
    total_points = np.sum(fitnesses) * (len(fitnesses) - 1)
    expected_total = len(fitnesses) * (len(fitnesses) - 1) / 2  # n*(n-1)/2 games
    assert abs(total_points - expected_total) < 1e-6, (
        f"Total points ({total_points}) should equal number of games ({expected_total})"
    )
    print(f"[PASS] Test 10: Tournament points sum correctly "
          f"({total_points:.1f} = {expected_total:.1f} games)")

    print("\nAll checkers domain tests passed!")
    return True


if __name__ == '__main__':
    test_checkers_domain()
