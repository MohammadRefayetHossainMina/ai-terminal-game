import game


# =============================================================================
# SETUP
# =============================================================================

def setup_function():
    """Reset all game state before each test."""
    game.reset_game()


# =============================================================================
# PLAYER MOVEMENT TESTS (Arrow Keys)
# =============================================================================

def test_move_right():
    """Pressing RIGHT arrow moves the player one column to the right."""
    game.move_player("RIGHT")
    assert game.player_row == 0
    assert game.player_col == 1


def test_move_down():
    """Pressing DOWN arrow moves the player one row down."""
    game.move_player("DOWN")
    assert game.player_row == 1
    assert game.player_col == 0


def test_move_left():
    """Pressing LEFT arrow moves the player one column to the left."""
    game.player_col = 2
    game.move_player("LEFT")
    assert game.player_col == 1


def test_move_up():
    """Pressing UP arrow moves the player one row up."""
    game.player_row = 2
    game.move_player("UP")
    assert game.player_row == 1


def test_move_left_blocked_at_edge():
    """Player at (0,0) tries to move left — should stay put."""
    game.move_player("LEFT")
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_up_blocked_at_edge():
    """Player at (0,0) tries to move up — should stay put."""
    game.move_player("UP")
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_right_blocked_at_edge():
    """Player at right edge cannot move further right."""
    game.player_col = game.GRID_SIZE - 1
    result = game.move_player("RIGHT")
    assert result is False
    assert game.player_col == game.GRID_SIZE - 1


def test_move_down_blocked_at_edge():
    """Player at bottom edge cannot move further down."""
    game.player_row = game.GRID_SIZE - 1
    result = game.move_player("DOWN")
    assert result is False
    assert game.player_row == game.GRID_SIZE - 1


def test_move_to_center():
    """Move player to center of grid using multiple moves."""
    for _ in range(2):
        game.move_player("RIGHT")
    for _ in range(2):
        game.move_player("DOWN")
    assert game.player_row == 2
    assert game.player_col == 2


def test_invalid_key_does_nothing():
    """An invalid key should not move the player."""
    result = game.move_player("X")
    assert result is False
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_full_width():
    """Move player across the full width of the grid."""
    for _ in range(game.GRID_SIZE - 1):
        game.move_player("RIGHT")
    assert game.player_col == game.GRID_SIZE - 1


def test_move_full_height():
    """Move player across the full height of the grid."""
    for _ in range(game.GRID_SIZE - 1):
        game.move_player("DOWN")
    assert game.player_row == game.GRID_SIZE - 1


def test_move_updates_direction():
    """Moving should update the player's facing direction."""
    game.move_player("RIGHT")
    assert game.player_direction == "right"
    game.move_player("DOWN")
    assert game.player_direction == "down"
    game.move_player("LEFT")
    assert game.player_direction == "left"
    game.move_player("UP")
    assert game.player_direction == "up"


def test_move_returns_true():
    """A valid move should return True."""
    assert game.move_player("RIGHT") is True


# =============================================================================
# SHOOTING TESTS
# =============================================================================

def test_shoot_right_hits_hazard():
    """Shooting right should destroy a hazard in that direction."""
    game.player_row = 0
    game.player_col = 0
    game.player_direction = "right"
    game.hazards = [(0, 2), (3, 3)]
    result = game.shoot()
    assert result is True
    assert (0, 2) not in game.hazards
    assert len(game.hazards) == 1


def test_shoot_down_hits_hazard():
    """Shooting down should destroy a hazard below."""
    game.player_row = 0
    game.player_col = 0
    game.player_direction = "down"
    game.hazards = [(2, 0)]
    result = game.shoot()
    assert result is True
    assert (2, 0) not in game.hazards


def test_shoot_up_hits_hazard():
    """Shooting up should destroy a hazard above."""
    game.player_row = 4
    game.player_col = 4
    game.player_direction = "up"
    game.hazards = [(1, 4)]
    result = game.shoot()
    assert result is True
    assert (1, 4) not in game.hazards


def test_shoot_left_hits_hazard():
    """Shooting left should destroy a hazard to the left."""
    game.player_row = 2
    game.player_col = 4
    game.player_direction = "left"
    game.hazards = [(2, 1)]
    result = game.shoot()
    assert result is True
    assert (2, 1) not in game.hazards


def test_shoot_misses():
    """Shooting when no hazard is in the line should return False."""
    game.player_row = 0
    game.player_col = 0
    game.player_direction = "right"
    game.hazards = [(3, 3)]
    result = game.shoot()
    assert result is False
    assert len(game.hazards) == 1


def test_shoot_stops_at_collectible():
    """Bullet should pass through the collectible and only hit hazards."""
    game.player_row = 0
    game.player_col = 0
    game.player_direction = "right"
    game.collectible_row = 0
    game.collectible_col = 1
    game.hazards = [(0, 3)]
    result = game.shoot()
    assert result is True
    assert (0, 3) not in game.hazards
    assert game.score == 0  # collectible not affected


def test_shoot_does_not_hit_player():
    """Bullet should not hit the player's own position."""
    game.player_row = 2
    game.player_col = 2
    game.player_direction = "right"
    game.hazards = [(2, 3), (2, 4)]
    result = game.shoot()
    assert result is True
    # Only the first hazard in line should be hit
    assert (2, 3) not in game.hazards
    assert (2, 4) in game.hazards


# =============================================================================
# HAZARD AI TESTS (Chase the player)
# =============================================================================

def test_hazard_moves_toward_player():
    """A hazard should move one step closer to the player."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(4, 4)]
    game.move_hazards_toward_player()
    # Should move closer (row 3 or col 3)
    assert game.hazards[0] != (4, 4)
    h_row, h_col = game.hazards[0]
    assert h_row < 4 or h_col < 4  # at least one axis got closer


def test_hazard_moves_vertically_when_closer():
    """Hazard should move vertically when row distance > col distance."""
    game.player_row = 0
    game.player_col = 3
    game.hazards = [(4, 3)]  # Same column, 4 rows away
    game.move_hazards_toward_player()
    assert game.hazards[0] == (3, 3)  # Should move up by 1


def test_hazard_moves_horizontally_when_closer():
    """Hazard should move horizontally when col distance > row distance."""
    game.player_row = 2
    game.player_col = 0
    game.hazards = [(2, 4)]  # Same row, 4 cols away
    game.move_hazards_toward_player()
    assert game.hazards[0] == (2, 3)  # Should move left by 1


def test_hazard_stays_put_when_adjacent():
    """Hazard should not move if already adjacent to the player."""
    game.player_row = 2
    game.player_col = 2
    game.hazards = [(2, 3)]  # Right next to the player
    game.move_hazards_toward_player()
    assert game.hazards[0] == (2, 3)  # Should stay put


def test_hazard_avoids_other_hazards():
    """Hazard should not move onto another hazard's position."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(3, 0), (2, 0)]  # Both in same column
    game.move_hazards_toward_player()
    positions = game.hazards
    # No two hazards should share a position
    assert len(positions) == len(set(positions))


def test_hazard_avoids_player_position():
    """Hazard should not move onto the player's position."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(2, 0)]
    game.move_hazards_toward_player()
    assert (0, 0) not in game.hazards


def test_multiple_hazards_all_chase():
    """All hazards should move toward the player."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(4, 4), (4, 0), (0, 4)]
    old_positions = game.hazards[:]
    game.move_hazards_toward_player()
    # At least some should have moved
    moved_count = sum(1 for i in range(len(game.hazards)) if game.hazards[i] != old_positions[i])
    assert moved_count >= 1


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


def test_reset_direction():
    """reset_game() resets the player direction to 'right'."""
    game.player_direction = "left"
    game.reset_game()
    assert game.player_direction == "right"


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


def test_collectible_avoids_hazards():
    """The collectible should never spawn on top of a hazard."""
    game.hazards = [(1, 1), (2, 2), (3, 3), (4, 4)]
    for _ in range(50):
        game.spawn_collectible()
        assert (game.collectible_row, game.collectible_col) not in game.hazards


# =============================================================================
# SPAWNING TESTS — hazards
# =============================================================================

def test_spawn_hazards_count_in_range():
    """spawn_hazards() should create between MIN and MAX hazards."""
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


# =============================================================================
# COLLISION TESTS
# =============================================================================

def test_collect_item_increases_score():
    """Moving onto the collectible increases score by 1."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 0
    game.collectible_col = 1
    game.move_player("RIGHT")
    result = game.check_collectible()
    assert result is True
    assert game.score == 1


def test_collect_does_not_trigger_when_miss():
    """Moving to a cell without the collectible should not change the score."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.move_player("RIGHT")
    result = game.check_collectible()
    assert result is False
    assert game.score == 0


def test_hit_hazard_reduces_lives():
    """Stepping on any hazard should reduce lives by 1."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 1)]
    game.move_player("RIGHT")
    result = game.check_hazard()
    assert result is True
    assert game.lives == 1


def test_hazard_respawns_after_hit():
    """After hitting a hazard, it should be removed and a new one spawned."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 1)]
    game.move_player("RIGHT")
    game.check_hazard()
    assert (0, 1) not in game.hazards
    assert len(game.hazards) == 1


def test_hazard_miss_does_not_reduce_lives():
    """Moving to a cell without any hazard should not change lives."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(2, 2), (3, 3)]
    game.move_player("RIGHT")
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
    """Shows the player emoji where the player is."""
    game.player_row = 1
    game.player_col = 1
    game.collectible_row = 3
    game.collectible_col = 3
    game.hazards = [(4, 4)]
    assert game.get_cell_content(1, 1) == f" {game.PLAYER_EMOJI} "


def test_get_cell_content_collectible():
    """Shows the collectible emoji where the collectible is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 3
    game.hazards = [(4, 4)]
    assert game.get_cell_content(2, 3) == f" {game.COLLECTIBLE_EMOJI} "


def test_get_cell_content_hazard():
    """Shows the hazard emoji where any hazard is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 2
    game.collectible_col = 2
    game.hazards = [(3, 4), (1, 1)]
    assert game.get_cell_content(3, 4) == f" {game.HAZARD_EMOJI} "
    assert game.get_cell_content(1, 1) == f" {game.HAZARD_EMOJI} "


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
    time.sleep(0.1)
    remaining = game.calculate_time_remaining(start)
    assert remaining < game.TIME_LIMIT
    assert remaining > game.TIME_LIMIT - 1


# =============================================================================
# THEME TESTS
# =============================================================================

def test_game_name():
    """Game name should be set to Australian Jones."""
    assert game.GAME_NAME == "Australian Jones"


def test_story_intro():
    """Story intro should match the theme."""
    assert game.STORY_INTRO == "Find and collect treasures and avoid traps"


def test_player_emoji():
    """Player emoji should be the fedora hat."""
    assert game.PLAYER_EMOJI == "\U0001F3A9"


def test_collectible_emoji():
    """Collectible emoji should be the package."""
    assert game.COLLECTIBLE_EMOJI == "\U0001F4E6"


def test_hazard_emoji():
    """Hazard emoji should be the volcano."""
    assert game.HAZARD_EMOJI == "\U0001F30B"


def test_win_message():
    """Win message should match the theme."""
    assert game.WIN_MESSAGE == "You won"


def test_lose_message():
    """Lose message should match the theme."""
    assert game.LOSE_MESSAGE == "Try again"


def test_cell_content_uses_correct_emojis():
    """Each cell type should return the correct themed emoji."""
    game.player_row = 2
    game.player_col = 2
    game.collectible_row = 0
    game.collectible_col = 0
    game.hazards = [(4, 4)]

    assert game.PLAYER_EMOJI in game.get_cell_content(2, 2)
    assert game.COLLECTIBLE_EMOJI in game.get_cell_content(0, 0)
    assert game.HAZARD_EMOJI in game.get_cell_content(4, 4)
    assert game.get_cell_content(1, 3) == " . "


# =============================================================================
# DIRECTION DELTAS TESTS
# =============================================================================

def test_direction_deltas_are_correct():
    """Each arrow key should map to the correct row/col change."""
    assert game.DIRECTION_DELTAS["UP"] == (-1, 0)
    assert game.DIRECTION_DELTAS["DOWN"] == (1, 0)
    assert game.DIRECTION_DELTAS["LEFT"] == (0, -1)
    assert game.DIRECTION_DELTAS["RIGHT"] == (0, 1)
