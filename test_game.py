import game


# =============================================================================
# SETUP — runs before every test to reset game state
# =============================================================================

def setup_function():
    """Reset all game state before each test so tests don't interfere."""
    game.player_row = 0
    game.player_col = 0
    game.score = 0
    game.lives = game.STARTING_LIVES
    game.collectible_row = 0
    game.collectible_col = 0
    game.hazard_row = 0
    game.hazard_col = 0


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


# =============================================================================
# SPAWNING TESTS — hazard
# =============================================================================

def test_spawn_hazard_not_on_player():
    """The hazard should never spawn on the player's position."""
    game.player_row = 2
    game.player_col = 3
    game.spawn_hazard()
    assert (game.hazard_row, game.hazard_col) != (2, 3)


def test_spawn_hazard_not_on_collectible():
    """The hazard should never spawn on the collectible's position."""
    game.collectible_row = 1
    game.collectible_col = 4
    game.spawn_hazard()
    assert (game.hazard_row, game.hazard_col) != (1, 4)


def test_spawn_hazard_within_grid():
    """The hazard should always be within grid boundaries."""
    for _ in range(50):
        game.spawn_hazard()
        assert 0 <= game.hazard_row < game.GRID_SIZE
        assert 0 <= game.hazard_col < game.GRID_SIZE


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
# COLLISION TESTS — hazard
# =============================================================================

def test_hit_hazard_reduces_lives():
    """Stepping on the hazard should reduce lives by 1."""
    game.player_row = 0
    game.player_col = 0
    game.hazard_row = 0
    game.hazard_col = 1
    game.move_player("d")
    result = game.check_hazard()
    assert result is True
    assert game.lives == 1


def test_hazard_miss_does_not_reduce_lives():
    """Moving to a cell without the hazard should not change lives."""
    game.player_row = 0
    game.player_col = 0
    game.hazard_row = 2
    game.hazard_col = 2
    game.move_player("d")
    result = game.check_hazard()
    assert result is False
    assert game.lives == 2


def test_lives_starts_at_two():
    """Lives should start at STARTING_LIVES (2)."""
    assert game.lives == game.STARTING_LIVES


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


def test_is_position_occupied_empty():
    """Returns False if the position is empty."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    assert game.is_position_occupied(4, 4) is False


def test_get_cell_content_player():
    """Shows 'P' where the player is."""
    game.player_row = 1
    game.player_col = 1
    game.collectible_row = 3
    game.collectible_col = 3
    game.hazard_row = 4
    game.hazard_col = 4
    assert game.get_cell_content(1, 1) == " P "


def test_get_cell_content_collectible():
    """Shows '*' where the collectible is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 3
    game.hazard_row = 4
    game.hazard_col = 4
    assert game.get_cell_content(2, 3) == " * "


def test_get_cell_content_hazard():
    """Shows 'X' where the hazard is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.hazard_row = 3
    game.hazard_col = 4
    assert game.get_cell_content(3, 4) == " X "


def test_get_cell_content_empty():
    """Shows '.' for an empty cell."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.hazard_row = 3
    game.hazard_col = 3
    assert game.get_cell_content(4, 4) == " . "
