import game


# =============================================================================
# SETUP — runs before every test to reset game state
# =============================================================================

def setup_function():
    """Reset all game state before each test so tests don't interfere."""
    game.reset_game()


# =============================================================================
# PLAYER MOVEMENT TESTS
# =============================================================================

def test_move_right():
    """Pressing 'd' moves the player one column to the right."""
    game.move_player("d")
    assert game.player_row == 0
    assert game.player_col == 1


def test_move_down():
    """Pressing 's' moves the player one row down."""
    game.move_player("s")
    assert game.player_row == 1
    assert game.player_col == 0


def test_move_left():
    """Pressing 'a' moves the player one column to the left."""
    game.player_col = 2
    game.move_player("a")
    assert game.player_col == 1


def test_move_up():
    """Pressing 'w' moves the player one row up."""
    game.player_row = 2
    game.move_player("w")
    assert game.player_row == 1


def test_move_left_blocked_at_edge():
    """Player at (0,0) tries to move left — should stay put."""
    game.move_player("a")
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_up_blocked_at_edge():
    """Player at (0,0) tries to move up — should stay put."""
    game.move_player("w")
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_right_blocked_at_edge():
    """Player at right edge cannot move further right."""
    game.player_col = game.GRID_SIZE - 1
    game.move_player("d")
    assert game.player_col == game.GRID_SIZE - 1


def test_move_down_blocked_at_edge():
    """Player at bottom edge cannot move further down."""
    game.player_row = game.GRID_SIZE - 1
    game.move_player("s")
    assert game.player_row == game.GRID_SIZE - 1


def test_move_to_center():
    """Move player to center of grid using multiple moves."""
    for _ in range(2):
        game.move_player("d")
    for _ in range(2):
        game.move_player("s")
    assert game.player_row == 2
    assert game.player_col == 2


def test_invalid_key_does_nothing():
    """An invalid key should not move the player."""
    game.move_player("x")
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_full_width():
    """Move player across the full width of the grid."""
    for _ in range(game.GRID_SIZE - 1):
        game.move_player("d")
    assert game.player_col == game.GRID_SIZE - 1


def test_move_full_height():
    """Move player across the full height of the grid."""
    for _ in range(game.GRID_SIZE - 1):
        game.move_player("s")
    assert game.player_row == game.GRID_SIZE - 1


# =============================================================================
# GAME RESET TESTS
# =============================================================================

def test_reset_player_position():
    """reset_game() moves the player back to (0, 0)."""
    game.player_row = 3
    game.player_col = 4
    game.reset_game()
    assert game.player_row == 0
    assert game.player_col == 0


def test_reset_score():
    """reset_game() sets the score back to 0."""
    game.score = 7
    game.reset_game()
    assert game.score == 0


def test_reset_lives():
    """reset_game() restores lives to STARTING_LIVES."""
    game.lives = 0
    game.reset_game()
    assert game.lives == game.STARTING_LIVES


def test_reset_collectible():
    """reset_game() resets collectible position to default."""
    game.collectible_row = 3
    game.collectible_col = 4
    game.reset_game()
    assert game.collectible_row == 0
    assert game.collectible_col == 0


def test_reset_hazards():
    """reset_game() clears the hazards list."""
    game.hazards = [(1, 1), (2, 2), (3, 3)]
    game.reset_game()
    assert game.hazards == []


# =============================================================================
# SPAWNING TESTS — collectible
# =============================================================================

def test_spawn_collectible_not_on_player():
    """The collectible should never spawn on the player's position."""
    game.player_row = 2
    game.player_col = 3
    game.spawn_collectible()
    assert (game.collectible_row, game.collectible_col) != (2, 3)


def test_spawn_collectible_within_grid():
    """The collectible should always be within grid boundaries."""
    for _ in range(50):
        game.spawn_collectible()
        assert 0 <= game.collectible_row < game.GRID_SIZE
        assert 0 <= game.collectible_col < game.GRID_SIZE


def test_collectible_responds_to_new_position_after_collect():
    """After collecting, spawn_collectible should move collectible to a new spot."""
    game.player_row = 2
    game.player_col = 2
    game.collectible_row = 2
    game.collectible_col = 2
    old_pos = (game.collectible_row, game.collectible_col)
    game.spawn_collectible()
    new_pos = (game.collectible_row, game.collectible_col)
    assert new_pos != old_pos


def test_collectible_avoids_hazards():
    """The collectible should never spawn on top of a hazard."""
    game.hazards = [(1, 1), (2, 2), (3, 3), (4, 4)]
    for _ in range(50):
        game.spawn_collectible()
        assert (game.collectible_row, game.collectible_col) not in game.hazards


# =============================================================================
# SPAWNING TESTS — hazards (multiple)
# =============================================================================

def test_spawn_hazards_count_in_range():
    """spawn_hazards() should create between MIN_HAZARDS and MAX_HAZARDS hazards."""
    for _ in range(30):
        game.spawn_hazards()
        assert len(game.hazards) >= game.MIN_HAZARDS
        assert len(game.hazards) <= game.MAX_HAZARDS


def test_spawn_hazards_not_on_player():
    """No hazard should spawn on the player's position."""
    game.player_row = 2
    game.player_col = 3
    game.spawn_hazards()
    assert (game.player_row, game.player_col) not in game.hazards


def test_spawn_hazards_not_on_collectible():
    """No hazard should spawn on the collectible's position."""
    game.collectible_row = 1
    game.collectible_col = 4
    game.spawn_hazards()
    assert (game.collectible_row, game.collectible_col) not in game.hazards


def test_spawn_hazards_within_grid():
    """All hazards should always be within grid boundaries."""
    for _ in range(30):
        game.spawn_hazards()
        for row, col in game.hazards:
            assert 0 <= row < game.GRID_SIZE
            assert 0 <= col < game.GRID_SIZE


def test_spawn_hazards_no_duplicates():
    """No two hazards should be on the same position."""
    for _ in range(30):
        game.spawn_hazards()
        assert len(game.hazards) == len(set(game.hazards))


def test_spawn_hazards_avoids_collectible():
    """Hazards should never overlap with the collectible."""
    game.collectible_row = 2
    game.collectible_col = 2
    for _ in range(30):
        game.spawn_hazards()
        assert (game.collectible_row, game.collectible_col) not in game.hazards


# =============================================================================
# COLLISION TESTS — collectible
# =============================================================================

def test_collect_item_increases_score():
    """Moving onto the collectible increases score by 1."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 0
    game.collectible_col = 1
    game.move_player("d")
    result = game.check_collectible()
    assert result is True
    assert game.score == 1


def test_collect_does_not_trigger_when_miss():
    """Moving to a cell without the collectible should not change the score."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.move_player("d")
    result = game.check_collectible()
    assert result is False
    assert game.score == 0


def test_score_starts_at_zero():
    """Score should start at 0."""
    assert game.score == 0


# =============================================================================
# COLLISION TESTS — hazards (multiple)
# =============================================================================

def test_hit_hazard_reduces_lives():
    """Stepping on any hazard should reduce lives by 1."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 1)]
    game.move_player("d")
    result = game.check_hazard()
    assert result is True
    assert game.lives == 1


def test_hazard_respawns_after_hit():
    """After hitting a hazard, it should be removed and a new one spawned."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 1)]
    game.move_player("d")
    game.check_hazard()
    # The hazard at (0,1) should be gone, replaced by a new one
    assert (0, 1) not in game.hazards
    assert len(game.hazards) == 1


def test_hazard_miss_does_not_reduce_lives():
    """Moving to a cell without any hazard should not change lives."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(2, 2), (3, 3)]
    game.move_player("d")
    result = game.check_hazard()
    assert result is False
    assert game.lives == 2


def test_lives_starts_at_two():
    """Lives should start at STARTING_LIVES (2)."""
    assert game.lives == game.STARTING_LIVES


def test_two_hazard_hits_game_over():
    """Hitting hazards twice should bring lives to 0."""
    game.lives = 2
    game.hazards = [(0, 1)]
    game.player_row = 0
    game.player_col = 0
    # First hit
    game.move_player("d")
    game.check_hazard()
    assert game.lives == 1
    # Simulate second hit on the respawned hazard
    game.hazards = [(game.player_row, game.player_col)]
    game.check_hazard()
    assert game.lives == 0


# =============================================================================
# WIN / LOSE CONDITION TESTS
# =============================================================================

def test_has_won_false_below_threshold():
    """Player has not won if score is below WIN_SCORE."""
    game.score = game.WIN_SCORE - 1
    assert game.has_won() is False


def test_has_won_true_at_threshold():
    """Player has won if score reaches WIN_SCORE."""
    game.score = game.WIN_SCORE
    assert game.has_won() is True


def test_has_lost_false_with_lives():
    """Player has not lost if they have lives remaining."""
    game.lives = 1
    assert game.has_lost() is False


def test_has_lost_true_at_zero():
    """Player has lost if lives reach 0."""
    game.lives = 0
    assert game.has_lost() is True


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

def test_is_position_occupied_by_player():
    """Returns True if the position matches the player's position."""
    game.player_row = 2
    game.player_col = 3
    assert game.is_position_occupied(2, 3) is True


def test_is_position_occupied_by_collectible():
    """Returns True if the position matches the collectible's position."""
    game.collectible_row = 1
    game.collectible_col = 4
    assert game.is_position_occupied(1, 4) is True


def test_is_position_occupied_by_hazard():
    """Returns True if the position matches any hazard's position."""
    game.hazards = [(3, 3)]
    assert game.is_position_occupied(3, 3) is True


def test_is_position_occupied_empty():
    """Returns False if the position is empty."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.hazards = [(3, 3)]
    assert game.is_position_occupied(4, 4) is False


def test_get_cell_content_player():
    """Shows 'P' where the player is."""
    game.player_row = 1
    game.player_col = 1
    game.collectible_row = 3
    game.collectible_col = 3
    game.hazards = [(4, 4)]
    assert game.get_cell_content(1, 1) == " P "


def test_get_cell_content_collectible():
    """Shows '*' where the collectible is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 3
    game.hazards = [(4, 4)]
    assert game.get_cell_content(2, 3) == " * "


def test_get_cell_content_hazard():
    """Shows 'X' where any hazard is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.hazards = [(3, 4), (1, 1)]
    assert game.get_cell_content(3, 4) == " X "
    assert game.get_cell_content(1, 1) == " X "


def test_get_cell_content_empty():
    """Shows '.' for an empty cell."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.hazards = [(3, 3)]
    assert game.get_cell_content(4, 4) == " . "


# =============================================================================
# TIME CALCULATION TEST
# =============================================================================

def test_calculate_time_remaining():
    """Time remaining should decrease as time passes."""
    import time
    start = time.time()
    # Simulate some time passing
    time.sleep(0.1)
    remaining = game.calculate_time_remaining(start)
    assert remaining < game.TIME_LIMIT
    assert remaining > game.TIME_LIMIT - 1


# =============================================================================
# MULTIPLE HAZARDS ON GRID TEST
# =============================================================================

def test_multiple_hazards_all_shown():
    """All hazards in the list should appear as 'X' on the grid."""
    game.hazards = [(0, 4), (2, 2), (4, 0)]
    for row, col in game.hazards:
        assert game.get_cell_content(row, col) == " X "


def test_hazard_list_is_modifiable():
    """The hazards list should support append and remove."""
    game.hazards = [(1, 1), (2, 2)]
    game.hazards.remove((1, 1))
    game.hazards.append((3, 3))
    assert (1, 1) not in game.hazards
    assert (3, 3) in game.hazards
    assert len(game.hazards) == 2
