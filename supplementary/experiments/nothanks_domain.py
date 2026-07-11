#!/usr/bin/env python3
"""
No Thanks! card game domain for the multi-domain topology sweep.

Ported from the TypeScript implementation at /home/lyra/projects/no-thanks/src/.

A 13-value continuous genome encodes an AI agent:
  - Values 0-11: feature weights (12 weights for the linear decision model)
  - Value 12: threshold (take card if dot product < threshold)
  - Each value is a float64 in [-1, 1]

Fitness is determined by tournament play within the population.
Each individual plays GAMES_PER_EVAL games against random opponents,
earning placement points (1st=3, 2nd=1, 3rd=0).

This is a COEVOLUTIONARY domain with continuous genomes:
  - Mutation: Gaussian (mean=0, sigma=0.1), NOT bit-flip
  - Crossover: uniform per-gene coin flip, NOT one-point
  - Diversity: Euclidean distance, NOT Hamming distance
  - Fitness: relative (tournament), NOT absolute

Game rules (No Thanks!):
  - Cards 3-35 (33 cards), 9 removed randomly at start (hidden)
  - 3 players, each starts with 11 chips
  - Each turn: take the card (+ accumulated chips) or pass (costs 1 chip)
  - Consecutive card runs score only the lowest card value
  - Score = sum of run minimums - remaining chips (lowest wins)
"""

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NOTHANKS_GENOME_LENGTH = 13  # 12 weights + 1 threshold
NUM_FEATURES = 12
GAMES_PER_EVAL = 50  # matches TypeScript training
NUM_PLAYERS = 3
INITIAL_CHIPS = 11
CARD_MIN = 3
CARD_MAX = 35
NUM_CARDS = CARD_MAX - CARD_MIN + 1  # 33
CARDS_REMOVED = 9
MAX_TURNS = 1000  # safety limit per game

# Mutation parameters for continuous genomes
MUTATION_SIGMA = 0.1
GENOME_CLIP = 1.0  # clip genome values to [-1, 1]


# ---------------------------------------------------------------------------
# Game engine (ported from TypeScript src/engine/)
# ---------------------------------------------------------------------------

def create_game(rng: np.random.Generator) -> dict:
    """Create a new No Thanks! game for 3 players.

    Returns a game state dict with:
      - players: list of {chips: int, cards: sorted list of ints}
      - current_player: int (0-2)
      - current_card: int or None
      - chips_on_card: int
      - deck: list of remaining cards
      - phase: 'playing' or 'finished'
    """
    # Generate and shuffle all cards 3-35
    all_cards = list(range(CARD_MIN, CARD_MAX + 1))
    rng.shuffle(all_cards)

    # Remove 9 cards (face down, unknown to all)
    remaining = all_cards[CARDS_REMOVED:]

    # Flip the first card
    current_card = remaining[0]
    deck = remaining[1:]

    # Create players
    players = [
        {'chips': INITIAL_CHIPS, 'cards': []}
        for _ in range(NUM_PLAYERS)
    ]

    return {
        'players': players,
        'current_player': 0,
        'current_card': current_card,
        'chips_on_card': 0,
        'deck': deck,
        'phase': 'playing',
    }


def get_valid_actions(state: dict) -> list:
    """Get valid actions for the current player.

    Returns list of strings: ['take'] or ['take', 'pass'].
    """
    if state['phase'] == 'finished' or state['current_card'] is None:
        return []
    player = state['players'][state['current_player']]
    actions = ['take']
    if player['chips'] > 0:
        actions.append('pass')
    return actions


def apply_action(state: dict, action: str) -> dict:
    """Apply an action to the game state. Returns a NEW state (immutable).

    Actions: 'take' or 'pass'.
    """
    if state['phase'] == 'finished' or state['current_card'] is None:
        return state

    # Deep copy players
    players = [
        {'chips': p['chips'], 'cards': list(p['cards'])}
        for p in state['players']
    ]
    cp = state['current_player']
    current_player = players[cp]

    if action == 'take':
        # Player takes the card and all chips on it
        current_player['cards'].append(state['current_card'])
        current_player['cards'].sort()
        current_player['chips'] += state['chips_on_card']

        # Flip next card or end game
        if len(state['deck']) == 0:
            return {
                'players': players,
                'current_player': cp,
                'current_card': None,
                'chips_on_card': 0,
                'deck': [],
                'phase': 'finished',
            }

        deck = list(state['deck'])
        next_card = deck.pop(0)
        return {
            'players': players,
            'current_player': cp,  # same player goes again after taking
            'current_card': next_card,
            'chips_on_card': 0,
            'deck': deck,
            'phase': 'playing',
        }
    else:
        # Pass: lose 1 chip, chip goes on the card
        current_player['chips'] -= 1
        next_player = (cp + 1) % NUM_PLAYERS
        return {
            'players': players,
            'current_player': next_player,
            'current_card': state['current_card'],
            'chips_on_card': state['chips_on_card'] + 1,
            'deck': list(state['deck']),
            'phase': 'playing',
        }


def is_game_over(state: dict) -> bool:
    """Check if the game is over."""
    return state['phase'] == 'finished'


# ---------------------------------------------------------------------------
# Scoring (ported from TypeScript src/engine/scoring.ts)
# ---------------------------------------------------------------------------

def detect_runs(cards: list) -> list:
    """Detect consecutive runs in a sorted list of cards.

    e.g., [3,4,5,8,9,15] -> [[3,4,5],[8,9],[15]]
    """
    if not cards:
        return []
    sorted_cards = sorted(cards)
    runs = [[sorted_cards[0]]]
    for i in range(1, len(sorted_cards)):
        if sorted_cards[i] == sorted_cards[i - 1] + 1:
            runs[-1].append(sorted_cards[i])
        else:
            runs.append([sorted_cards[i]])
    return runs


def calculate_score(player: dict) -> int:
    """Calculate a player's score.

    In No Thanks!:
    - Each run of consecutive cards scores only the lowest card value
    - Remaining chips subtract from the score
    - Lowest score wins
    """
    runs = detect_runs(player['cards'])
    card_score = sum(run[0] for run in runs)
    return card_score - player['chips']


def run_score(cards: list) -> int:
    """Calculate just the card-run component of scoring (no chip offset)."""
    if not cards:
        return 0
    sorted_cards = sorted(cards)
    score = sorted_cards[0]
    for i in range(1, len(sorted_cards)):
        if sorted_cards[i] != sorted_cards[i - 1] + 1:
            score += sorted_cards[i]
    return score


# ---------------------------------------------------------------------------
# Feature extraction (ported from TypeScript src/ai/features.ts)
# ---------------------------------------------------------------------------

def compute_run_savings(cards: list, new_card: int) -> float:
    """Compute how much score is saved by extending an existing run.

    If holding [10,11,12] and card is 13, taking it adds 0 to score.
    A standalone 13 would cost 13 points. So savings = 13.
    """
    with_card = sorted(cards + [new_card])
    score_with = run_score(with_card)
    score_without = run_score(cards)
    actual_cost = score_with - score_without
    savings = new_card - actual_cost
    return max(0.0, float(savings))


def extract_features(state: dict, player_index: int) -> np.ndarray:
    """Extract 12 normalized features from the game state for a given player.

    Returns a numpy array of 12 float64 values.
    """
    player = state['players'][player_index]
    card = state['current_card']

    # Feature 0: Card value normalized (0-1)
    card_value = (card - CARD_MIN) / (CARD_MAX - CARD_MIN)

    # Feature 1: Chips on card normalized (0-1)
    chips_on_card = state['chips_on_card'] / NUM_CARDS

    # Feature 2: Net cost -- how expensive is this card after chips offset (-1 to 1)
    net_cost = (card - state['chips_on_card']) / CARD_MAX

    # Feature 3: My remaining chips (0-1)
    my_chips = player['chips'] / INITIAL_CHIPS

    # Feature 4: Does this card extend an existing run? (0 or 1)
    extends_run = 1.0 if any(abs(c - card) == 1 for c in player['cards']) else 0.0

    # Feature 5: Does this card fill a gap between two held cards? (0 or 1)
    fills_gap = 1.0 if (
        (card - 1) in player['cards'] and (card + 1) in player['cards']
    ) else 0.0

    # Feature 6: Distance to nearest held card (0-1), 1.0 if no cards
    if not player['cards']:
        distance_to_nearest = 1.0
    else:
        min_dist = min(abs(c - card) for c in player['cards'])
        distance_to_nearest = min_dist / (CARD_MAX - CARD_MIN)

    # Feature 7: Cards remaining in deck (0-1)
    cards_remaining = len(state['deck']) / (NUM_CARDS - CARDS_REMOVED)

    # Feature 8: Score delta -- positive means I'm behind (worse)
    my_score = calculate_score(player)
    opponent_scores = [
        calculate_score(state['players'][i])
        for i in range(NUM_PLAYERS) if i != player_index
    ]
    best_opponent_score = min(opponent_scores)
    raw_delta = (my_score - best_opponent_score) / CARD_MAX
    score_delta = max(-1.0, min(1.0, raw_delta))

    # Feature 9: ACTUAL score change from taking this card
    hypothetical_cards = sorted(player['cards'] + [card])
    hypothetical_player = {
        'chips': player['chips'] + state['chips_on_card'],
        'cards': hypothetical_cards,
    }
    score_if_take = calculate_score(hypothetical_player)
    score_now = calculate_score(player)
    score_change = max(-1.0, min(1.0, (score_if_take - score_now) / CARD_MAX))

    # Feature 10: Chip urgency -- non-linear pressure as chips run low
    chip_urgency = 1.0 - (player['chips'] / INITIAL_CHIPS) ** 0.5

    # Feature 11: Run savings -- how much score an adjacent run saves
    if extends_run > 0:
        run_savings_val = compute_run_savings(player['cards'], card) / (CARD_MAX - CARD_MIN)
    else:
        run_savings_val = 0.0

    return np.array([
        card_value,
        chips_on_card,
        net_cost,
        my_chips,
        extends_run,
        fills_gap,
        distance_to_nearest,
        cards_remaining,
        score_delta,
        score_change,
        chip_urgency,
        run_savings_val,
    ], dtype=np.float64)


# ---------------------------------------------------------------------------
# AI agent (ported from TypeScript src/ai/agent.ts)
# ---------------------------------------------------------------------------

def decide(state: dict, player_index: int, genome: np.ndarray) -> str:
    """AI decision function.

    Computes dot product of features x weights. Takes the card if the
    result is below the threshold (lower score = more desirable to take).

    genome: array of 13 float64 values (12 weights + 1 threshold).
    Returns: 'take' or 'pass'.
    """
    valid_actions = get_valid_actions(state)

    # If only one valid action, must do it
    if len(valid_actions) == 1:
        return valid_actions[0]

    features = extract_features(state, player_index)

    # Dot product of features and weights
    weights = genome[:NUM_FEATURES]
    threshold = genome[NUM_FEATURES]  # genome[12]
    score = float(np.dot(features, weights))

    # Below threshold -> take the card (lower score = more desirable)
    # Above threshold -> pass (save chips, wait for better opportunity)
    return 'take' if score < threshold else 'pass'


# ---------------------------------------------------------------------------
# Game play
# ---------------------------------------------------------------------------

def play_game(agents: list, rng: np.random.Generator) -> list:
    """Play a single game with 3 AI agents.

    agents: list of 3 genome arrays (each 13 float64 values).
    Returns placement points: [p0, p1, p2] where 1st=3, 2nd=1, 3rd=0.
    """
    state = create_game(rng)
    turns = 0

    while not is_game_over(state) and turns < MAX_TURNS:
        player_idx = state['current_player']
        action = decide(state, player_idx, agents[player_idx])
        state = apply_action(state, action)
        turns += 1

    # Score and rank
    scores = [
        (i, calculate_score(state['players'][i]))
        for i in range(NUM_PLAYERS)
    ]
    scores.sort(key=lambda x: x[1])  # lowest score wins

    points = [0, 0, 0]
    points[scores[0][0]] = 3  # 1st place
    points[scores[1][0]] = 1  # 2nd place
    # 3rd place gets 0
    return points


# ---------------------------------------------------------------------------
# Population-level functions
# ---------------------------------------------------------------------------

def evaluate_nothanks(pop: np.ndarray) -> np.ndarray:
    """Tournament evaluation for No Thanks!

    Each individual plays GAMES_PER_EVAL games against random opponents
    from the population. Fitness = total_points / max_possible_points,
    normalized to [0, 1].

    Args:
        pop: (pop_size, 13) float64 array.

    Returns: (pop_size,) float64 array of fitnesses in [0, 1].
    """
    n = len(pop)
    if n == 0:
        return np.array([], dtype=np.float64)
    if n == 1:
        return np.array([0.5], dtype=np.float64)

    # Use a deterministic rng seeded from population content for reproducibility
    cache_key = hash(pop.tobytes()) % (2**31)
    rng = np.random.default_rng(cache_key)

    total_points = np.zeros(n, dtype=np.float64)

    for i in range(n):
        for _ in range(GAMES_PER_EVAL):
            # Pick 2 random opponents
            opponents_idx = rng.integers(0, n, size=2)
            # Random seat position
            seat = rng.integers(0, NUM_PLAYERS)
            agents = [None, None, None]
            opp_idx = 0
            for s in range(NUM_PLAYERS):
                if s == seat:
                    agents[s] = pop[i]
                else:
                    agents[s] = pop[opponents_idx[opp_idx]]
                    opp_idx += 1

            points = play_game(agents, rng)
            total_points[i] += points[seat]

    # Normalize: max possible = GAMES_PER_EVAL * 3 (all 1st place)
    max_points = GAMES_PER_EVAL * 3.0
    fitnesses = total_points / max_points

    return fitnesses


def evaluate_nothanks_fast(pop: np.ndarray) -> np.ndarray:
    """Faster tournament evaluation: reduced games for sweep use.

    Uses 10 games per individual instead of 50 to keep sweep runtime
    reasonable. Each individual plays 10 games against random opponents.

    Args:
        pop: (pop_size, 13) float64 array.

    Returns: (pop_size,) float64 array of fitnesses in [0, 1].
    """
    n = len(pop)
    if n == 0:
        return np.array([], dtype=np.float64)
    if n == 1:
        return np.array([0.5], dtype=np.float64)

    games_per = 10  # reduced for sweep speed

    cache_key = hash(pop.tobytes()) % (2**31)
    rng = np.random.default_rng(cache_key)

    total_points = np.zeros(n, dtype=np.float64)

    for i in range(n):
        for _ in range(games_per):
            opponents_idx = rng.integers(0, n, size=2)
            seat = rng.integers(0, NUM_PLAYERS)
            agents = [None, None, None]
            opp_idx = 0
            for s in range(NUM_PLAYERS):
                if s == seat:
                    agents[s] = pop[i]
                else:
                    agents[s] = pop[opponents_idx[opp_idx]]
                    opp_idx += 1

            points = play_game(agents, rng)
            total_points[i] += points[seat]

    max_points = games_per * 3.0
    fitnesses = total_points / max_points

    return fitnesses


def random_nothanks_population(rng, pop_size,
                                genome_length=NOTHANKS_GENOME_LENGTH):
    """Generate random No Thanks! population.

    Each individual is 13 float64 values uniformly sampled from [-1, 1].

    Args:
        rng: numpy random Generator.
        pop_size: number of individuals.
        genome_length: must be NOTHANKS_GENOME_LENGTH (13).

    Returns: (pop_size, 13) float64 array.
    """
    return rng.uniform(-1.0, 1.0, size=(pop_size, genome_length))


# ---------------------------------------------------------------------------
# Continuous-genome GA operators
# ---------------------------------------------------------------------------

def gaussian_mutate(rng: np.random.Generator, pop: np.ndarray,
                    mutation_rate: float) -> np.ndarray:
    """Per-gene Gaussian mutation for continuous genomes.

    Each gene has `mutation_rate` probability of being mutated.
    Mutation adds Gaussian noise with mean=0, sigma=MUTATION_SIGMA.
    Values are clipped to [-GENOME_CLIP, GENOME_CLIP].
    """
    result = pop.copy()
    mask = rng.random(size=pop.shape) < mutation_rate
    noise = rng.normal(0.0, MUTATION_SIGMA, size=pop.shape)
    result[mask] += noise[mask]
    result = np.clip(result, -GENOME_CLIP, GENOME_CLIP)
    return result


def uniform_crossover(rng: np.random.Generator, pop: np.ndarray,
                      crossover_rate: float) -> np.ndarray:
    """Uniform crossover for continuous genomes.

    Pairs are formed sequentially. If crossover occurs (probability
    crossover_rate), each gene is independently taken from either parent
    with equal probability.
    """
    result = pop.copy()
    n = len(pop)
    i = 0
    while i + 1 < n:
        r = rng.random()
        if r < crossover_rate:
            # Per-gene coin flip
            mask = rng.random(size=pop.shape[1]) < 0.5
            result[i, mask], result[i + 1, mask] = (
                pop[i + 1, mask].copy(), pop[i, mask].copy()
            )
        i += 2
    return result


def euclidean_diversity(pop: np.ndarray) -> float:
    """Mean pairwise Euclidean distance, normalized to [0, 1].

    For continuous genomes in [-1, 1]^d, max pairwise distance is 2*sqrt(d).
    """
    n = len(pop)
    if n < 2:
        return 0.0
    d = pop.shape[1]
    max_dist = 2.0 * np.sqrt(d)  # max Euclidean distance in [-1,1]^d

    # Efficient computation using broadcasting
    # For small populations (island size ~16-20), this is fast
    total_dist = 0.0
    count = 0
    for i in range(n):
        diffs = pop[i + 1:] - pop[i]
        dists = np.sqrt(np.sum(diffs ** 2, axis=1))
        total_dist += np.sum(dists)
        count += len(dists)

    if count == 0:
        return 0.0
    mean_dist = total_dist / count
    return float(mean_dist / max_dist)


def euclidean_divergence(pop1: np.ndarray, pop2: np.ndarray) -> float:
    """Distance between two populations using mean vectors.

    Compares the mean genome value at each locus. Returns a value in [0, 1]
    where 0 = identical mean distributions, 1 = maximally different.

    Analogous to population_divergence but for continuous genomes.
    """
    if len(pop1) == 0 or len(pop2) == 0:
        return 1.0
    mean1 = pop1.mean(axis=0)
    mean2 = pop2.mean(axis=0)
    # L1 distance normalized by genome length, scaled to [-1,1] range
    # Max L1 difference per gene = 2 (from -1 to +1), so divide by 2
    return float(np.mean(np.abs(mean1 - mean2)) / 2.0)


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def test_nothanks_domain():
    """Self-tests for the No Thanks! domain."""
    print("=== No Thanks! Domain Self-Test ===\n")

    rng = np.random.default_rng(42)

    # Test 1: Game creation
    state = create_game(rng)
    assert state['phase'] == 'playing'
    assert state['current_card'] is not None
    assert CARD_MIN <= state['current_card'] <= CARD_MAX
    assert state['chips_on_card'] == 0
    assert len(state['players']) == NUM_PLAYERS
    for p in state['players']:
        assert p['chips'] == INITIAL_CHIPS
        assert p['cards'] == []
    # Total cards = current + deck + removed = 33
    total_cards = 1 + len(state['deck']) + CARDS_REMOVED
    assert total_cards == NUM_CARDS, f"Expected {NUM_CARDS} total cards, got {total_cards}"
    print(f"[PASS] Test 1: Game creation -- card={state['current_card']}, "
          f"deck={len(state['deck'])}, 3 players with 11 chips each")

    # Test 2: Apply take action
    state2 = create_game(np.random.default_rng(42))
    taken_card = state2['current_card']
    state_after_take = apply_action(state2, 'take')
    assert taken_card in state_after_take['players'][0]['cards']
    assert state_after_take['players'][0]['chips'] == INITIAL_CHIPS  # 0 chips on card
    assert state_after_take['current_player'] == 0  # same player goes again
    assert state_after_take['chips_on_card'] == 0
    print(f"[PASS] Test 2: Take action -- player 0 took card {taken_card}")

    # Test 3: Apply pass action
    state3 = create_game(np.random.default_rng(42))
    state_after_pass = apply_action(state3, 'pass')
    assert state_after_pass['players'][0]['chips'] == INITIAL_CHIPS - 1
    assert state_after_pass['current_player'] == 1  # next player
    assert state_after_pass['chips_on_card'] == 1
    assert state_after_pass['current_card'] == state3['current_card']  # same card
    print(f"[PASS] Test 3: Pass action -- player 0 lost 1 chip, 1 chip on card")

    # Test 4: Scoring
    player_a = {'chips': 5, 'cards': [3, 4, 5, 8, 9, 15]}
    score_a = calculate_score(player_a)
    # Runs: [3,4,5] -> 3, [8,9] -> 8, [15] -> 15 = 26, minus 5 chips = 21
    assert score_a == 21, f"Expected score 21, got {score_a}"
    print(f"[PASS] Test 4: Scoring -- [3,4,5,8,9,15] with 5 chips = {score_a}")

    # Test 5: Run detection
    runs = detect_runs([3, 4, 5, 8, 9, 15])
    assert runs == [[3, 4, 5], [8, 9], [15]], f"Unexpected runs: {runs}"
    assert detect_runs([]) == []
    assert detect_runs([10]) == [[10]]
    assert detect_runs([3, 5, 7]) == [[3], [5], [7]]
    print(f"[PASS] Test 5: Run detection -- correct for all cases")

    # Test 6: Feature extraction
    state6 = create_game(np.random.default_rng(42))
    features = extract_features(state6, 0)
    assert features.shape == (NUM_FEATURES,), f"Expected {NUM_FEATURES} features, got {features.shape}"
    assert features.dtype == np.float64
    # All features should be in reasonable range
    assert np.all(np.isfinite(features)), f"Non-finite features: {features}"
    print(f"[PASS] Test 6: Feature extraction -- {NUM_FEATURES} features, "
          f"range [{features.min():.3f}, {features.max():.3f}]")

    # Test 7: Agent decision
    genome = np.zeros(NOTHANKS_GENOME_LENGTH, dtype=np.float64)
    state7 = create_game(np.random.default_rng(42))
    action = decide(state7, 0, genome)
    assert action in ('take', 'pass'), f"Invalid action: {action}"
    # With zero weights and zero threshold, dot product = 0 < 0 is False, so 'pass'
    assert action == 'pass', f"Zero genome: dot=0, threshold=0, 0 < 0 is False -> pass"
    print(f"[PASS] Test 7: Agent decision -- zero genome correctly returns '{action}'")

    # Test 8: Complete game terminates
    rng8 = np.random.default_rng(99)
    agents = [
        rng8.uniform(-1, 1, size=NOTHANKS_GENOME_LENGTH),
        rng8.uniform(-1, 1, size=NOTHANKS_GENOME_LENGTH),
        rng8.uniform(-1, 1, size=NOTHANKS_GENOME_LENGTH),
    ]
    points = play_game(agents, rng8)
    assert len(points) == 3
    assert sum(points) == 4, f"Total points should be 4 (3+1+0), got {sum(points)}"
    assert sorted(points, reverse=True) == [3, 1, 0], (
        f"Points should be [3,1,0] in some order, got {sorted(points, reverse=True)}"
    )
    print(f"[PASS] Test 8: Complete game terminates -- points={points}")

    # Test 9: Population creation
    rng9 = np.random.default_rng(42)
    pop = random_nothanks_population(rng9, 20)
    assert pop.shape == (20, NOTHANKS_GENOME_LENGTH)
    assert pop.dtype == np.float64
    assert np.all(pop >= -1.0)
    assert np.all(pop <= 1.0)
    print(f"[PASS] Test 9: Population creation -- shape={pop.shape}, "
          f"range [{pop.min():.3f}, {pop.max():.3f}]")

    # Test 10: Evaluation function
    rng10 = np.random.default_rng(42)
    pop10 = random_nothanks_population(rng10, 8)
    print("  Running evaluation (8 individuals x 10 games each)...", end=" ", flush=True)
    fitnesses = evaluate_nothanks_fast(pop10)
    assert fitnesses.dtype == np.float64
    assert len(fitnesses) == 8
    assert np.all(fitnesses >= 0.0), f"Found negative fitness: {fitnesses.min()}"
    assert np.all(fitnesses <= 1.0), f"Found fitness > 1: {fitnesses.max()}"
    print(f"done")
    print(f"[PASS] Test 10: Evaluation -- 8 individuals, "
          f"fitnesses in [{fitnesses.min():.3f}, {fitnesses.max():.3f}]")

    # Test 11: Gaussian mutation
    rng11 = np.random.default_rng(42)
    pop11 = random_nothanks_population(rng11, 10)
    mutated = gaussian_mutate(rng11, pop11, 0.3)
    assert mutated.shape == pop11.shape
    # Some genes should have changed
    changed = np.sum(mutated != pop11)
    assert changed > 0, "Mutation should change some genes"
    assert np.all(mutated >= -GENOME_CLIP)
    assert np.all(mutated <= GENOME_CLIP)
    pct_changed = changed / pop11.size * 100
    print(f"[PASS] Test 11: Gaussian mutation -- {changed}/{pop11.size} genes changed "
          f"({pct_changed:.1f}%)")

    # Test 12: Uniform crossover
    rng12 = np.random.default_rng(42)
    pop12 = random_nothanks_population(rng12, 10)
    crossed = uniform_crossover(rng12, pop12, 0.8)
    assert crossed.shape == pop12.shape
    print(f"[PASS] Test 12: Uniform crossover -- shape preserved")

    # Test 13: Euclidean diversity
    rng13 = np.random.default_rng(42)
    pop_uniform = random_nothanks_population(rng13, 20)
    div_uniform = euclidean_diversity(pop_uniform)
    assert 0.0 <= div_uniform <= 1.0
    # Identical population should have zero diversity
    pop_identical = np.ones((10, NOTHANKS_GENOME_LENGTH))
    div_identical = euclidean_diversity(pop_identical)
    assert div_identical == 0.0, f"Identical population diversity should be 0, got {div_identical}"
    print(f"[PASS] Test 13: Euclidean diversity -- uniform={div_uniform:.4f}, "
          f"identical={div_identical:.4f}")

    # Test 14: Euclidean divergence
    rng14 = np.random.default_rng(42)
    pop_a = random_nothanks_population(rng14, 20)
    pop_b = random_nothanks_population(rng14, 20)
    div_ab = euclidean_divergence(pop_a, pop_b)
    div_aa = euclidean_divergence(pop_a, pop_a)
    assert 0.0 <= div_ab <= 1.0
    assert div_aa == 0.0, f"Self-divergence should be 0, got {div_aa}"
    print(f"[PASS] Test 14: Euclidean divergence -- cross={div_ab:.4f}, self={div_aa:.4f}")

    print("\nAll No Thanks! domain tests passed!")
    return True


if __name__ == '__main__':
    test_nothanks_domain()
