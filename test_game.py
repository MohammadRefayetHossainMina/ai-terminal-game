import game
import time


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


def test_move_through_open_area():
    """Move player several steps in an open area of the grid."""
    # Move right 5 (col 5 is wall-free on rows 0-1)
    for _ in range(5):
        game.move_player("RIGHT")
    # Move down 3 (col 5 is clear at rows 1, 2, 3)
    for _ in range(3):
        game.move_player("DOWN")
    assert game.player_row == 3
    assert game.player_col == 5


def test_invalid_key_does_nothing():
    """An invalid key should not move the player."""
    result = game.move_player("X")
    assert result is False
    assert game.player_row == 0
    assert game.player_col == 0


def test_move_full_width():
    """Move player across the full width of the grid (row 0 is wall-free)."""
    for _ in range(game.GRID_SIZE - 1):
        game.move_player("RIGHT")
    assert game.player_col == game.GRID_SIZE - 1


def test_move_full_height():
    """Move player across the full height (col 0 is wall-free)."""
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
# WALL TESTS — player movement blocked by walls
# =============================================================================

def test_wall_blocks_player_right():
    """Player cannot move right into a wall at (2,2)."""
    game.player_row = 2
    game.player_col = 1
    result = game.move_player("RIGHT")
    assert result is False
    assert game.player_col == 1


def test_wall_blocks_player_down():
    """Player cannot move down into a wall at (2,2)."""
    game.player_row = 1
    game.player_col = 2
    result = game.move_player("DOWN")
    assert result is False
    assert game.player_row == 1


def test_wall_blocks_player_left():
    """Player cannot move left into a wall at (2,2)."""
    game.player_row = 2
    game.player_col = 3
    result = game.move_player("LEFT")
    assert result is False
    assert game.player_col == 3


def test_wall_blocks_player_up():
    """Player cannot move up into a wall at (2,2)."""
    game.player_row = 3
    game.player_col = 2
    result = game.move_player("UP")
    assert result is False
    assert game.player_row == 3


def test_player_can_move_through_doorway():
    """Player can move through a doorway between walls."""
    # (3,3) is inside the top-left room — reachable through the doorway at (3,3)
    game.player_row = 3
    game.player_col = 3
    # All adjacent cells: (2,3)=wall, (4,3)=empty, (3,2)=wall, (3,4)=wall (wait, is (3,4) a wall?)

    # Let me check: row 3 is "..#.#.....#.#..."
    # (3,0)=., (3,1)=., (3,2)=#, (3,3)=., (3,4)=#
    # So (3,3) is surrounded by walls on 3 sides and (2,3) is also a wall.
    # Only way out is (4,3).
    result = game.move_player("DOWN")
    assert result is True
    assert game.player_row == 4
    assert game.player_col == 3


def test_walls_constant_across_resets():
    """Walls should not change between game resets."""
    walls_before = game.WALLS.copy()
    game.reset_game()
    assert game.WALLS == walls_before


def test_player_start_not_on_wall():
    """The player's starting position should never be a wall."""
    assert (0, 0) not in game.WALLS


# =============================================================================
# SHOOTING TESTS (auto-target closest hazard)
# =============================================================================

def test_shoot_targets_closest_hazard():
    """Should destroy the closest hazard, not the farthest one."""
    game.player_row = 0
    game.player_col = 0
    # Hazard at distance 3 vs distance 10
    game.hazards = [(0, 3), (0, 10)]
    result = game.shoot()
    assert result is True
    assert (0, 3) not in game.hazards  # Closest destroyed
    assert (0, 10) in game.hazards      # Farthest survives


def test_shoot_hits_hazard_on_same_row():
    """Should shoot horizontally when the closest hazard is on the same row."""
    # Use row 0 (no walls in row 0)
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 8)]
    result = game.shoot()
    assert result is True
    assert (0, 8) not in game.hazards


def test_shoot_hits_hazard_on_same_column():
    """Should shoot vertically when the closest hazard is on the same column."""
    game.player_row = 0
    game.player_col = 5
    game.hazards = [(8, 5)]
    result = game.shoot()
    assert result is True
    assert (8, 5) not in game.hazards


def test_shoot_diagonal_prefers_vertical():
    """When closest hazard is diagonal and row distance <= col distance, shoot vertically.
    The bullet travels vertically — it hits anything in that column, not the diagonal target."""
    game.player_row = 0
    game.player_col = 0
    # Hazard at (3, 5): row_diff=3, col_diff=5 → prefer vertical
    # Place a decoy hazard in the vertical path to prove the bullet goes down
    game.hazards = [(3, 5), (4, 0)]
    result = game.shoot()
    assert result is True
    assert (4, 0) not in game.hazards   # Hit the one in the vertical path
    assert (3, 5) in game.hazards        # Diagonal target survives


def test_shoot_diagonal_prefers_horizontal():
    """When closest hazard is diagonal and col distance < row distance, shoot horizontally.
    The bullet travels horizontally — it hits anything in that row, not the diagonal target."""
    game.player_row = 0
    game.player_col = 0
    # Hazard at (5, 3): row_diff=5, col_diff=3 → prefer horizontal
    # Place a decoy hazard in the horizontal path to prove the bullet goes right
    game.hazards = [(5, 3), (0, 4)]
    result = game.shoot()
    assert result is True
    assert (0, 4) not in game.hazards   # Hit the one in the horizontal path
    assert (5, 3) in game.hazards        # Diagonal target survives


def test_shoot_misses_when_no_hazards():
    """Shooting with no hazards should return False."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = []
    result = game.shoot()
    assert result is False


def test_shoot_stops_at_wall():
    """Bullet should stop at a wall and not reach a hazard behind it."""
    game.player_row = 2
    game.player_col = 0
    # Wall at (2,2), hazard at (2,5) — bullet blocked by wall
    game.hazards = [(2, 5)]
    result = game.shoot()
    assert result is False
    assert (2, 5) in game.hazards  # Hazard still alive


def test_shoot_does_not_hit_player():
    """Bullet should never hit the player's own position."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 3), (0, 8)]
    result = game.shoot()
    assert result is True
    # Only the first hazard in line should be hit
    assert (0, 3) not in game.hazards
    assert (0, 8) in game.hazards


def test_shoot_stops_at_collectible():
    """Bullet should pass through the collectible and only hit hazards."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 0
    game.collectible_col = 1
    game.hazards = [(0, 5)]
    result = game.shoot()
    assert result is True
    assert (0, 5) not in game.hazards
    assert game.score == 0  # collectible not affected


def test_shoot_multiple_closest_picks_right_one():
    """When two hazards are equidistant, the bullet should hit the one in its path."""
    game.player_row = 0
    game.player_col = 0
    # Both at distance 5, but (0,5) is on the same row (horizontal path)
    # and (5,0) is on the same column (vertical path)
    # Manhattan distance: both = 5. Closest is whichever is found first.
    # (0,5): row_diff=0, col_diff=5 → same row → shoot horizontal
    game.hazards = [(0, 5), (5, 0)]
    result = game.shoot()
    assert result is True
    # One of them should be destroyed
    remaining = len(game.hazards)
    assert remaining == 1


def test_shoot_left_when_hazard_to_the_left():
    """Should shoot left when the closest hazard is to the left."""
    # Use row 0 (no walls)
    game.player_row = 0
    game.player_col = 10
    game.hazards = [(0, 3)]
    result = game.shoot()
    assert result is True
    assert (0, 3) not in game.hazards


def test_shoot_up_when_hazard_above():
    """Should shoot up when the closest hazard is above."""
    game.player_row = 10
    game.player_col = 5
    game.hazards = [(3, 5)]
    result = game.shoot()
    assert result is True
    assert (3, 5) not in game.hazards


def test_shoot_down_when_hazard_below():
    """Should shoot down when the closest hazard is below."""
    game.player_row = 3
    game.player_col = 5
    game.hazards = [(10, 5)]
    result = game.shoot()
    assert result is True
    assert (10, 5) not in game.hazards


# =============================================================================
# HAZARD AI TESTS (Chase the player, respecting walls)
# =============================================================================

def test_hazard_moves_toward_player():
    """A hazard should move one step closer to the player."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(8, 8)]
    game.move_hazards_toward_player()
    # Should move closer
    assert game.hazards[0] != (8, 8)
    h_row, h_col = game.hazards[0]
    assert h_row < 8 or h_col < 8  # at least one axis got closer


def test_hazard_moves_vertically_when_closer():
    """Hazard should move vertically when row distance > col distance."""
    game.player_row = 0
    game.player_col = 3
    game.hazards = [(8, 3)]  # Same column, 8 rows away
    game.move_hazards_toward_player()
    assert game.hazards[0] == (7, 3)  # Should move up by 1


def test_hazard_moves_horizontally_when_closer():
    """Hazard should move horizontally when col distance > row distance."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(0, 8)]  # Same row, 8 cols away
    game.move_hazards_toward_player()
    assert game.hazards[0] == (0, 7)  # Should move left by 1


def test_hazard_stays_put_when_adjacent():
    """Hazard should not move if already adjacent to the player."""
    game.player_row = 5
    game.player_col = 5
    game.hazards = [(5, 6)]  # Right next to the player
    game.move_hazards_toward_player()
    assert game.hazards[0] == (5, 6)  # Should stay put


def test_hazard_avoids_other_hazards():
    """Hazard should not move onto another hazard's position."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(5, 0), (4, 0)]  # Both in same column
    game.move_hazards_toward_player()
    positions = game.hazards
    # No two hazards should share a position
    assert len(positions) == len(set(positions))


def test_hazard_avoids_player_position():
    """Hazard should not move onto the player's position."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(3, 0)]
    game.move_hazards_toward_player()
    assert (0, 0) not in game.hazards


def test_multiple_hazards_all_chase():
    """All hazards should move toward the player."""
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(8, 8), (8, 0), (0, 8)]
    old_positions = game.hazards[:]
    game.move_hazards_toward_player()
    # At least some should have moved
    moved_count = sum(
        1 for i in range(len(game.hazards))
        if game.hazards[i] != old_positions[i]
    )
    assert moved_count >= 1


def test_hazard_avoids_wall_goes_around():
    """Hazard should try to go around a wall instead of getting stuck."""
    # Place a wall between hazard and player in a tight spot
    # Hazard at (7,7) (inside center room), player at (0,0)
    # Greedy would go to (6,7) which is a wall at (6,7)
    # Should try (7,6) instead — which is also a wall at (7,6)!
    # So it should stay put since all moves are blocked
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(7, 8)]  # Inside center room, (7,6) and (7,10) are walls
    game.move_hazards_toward_player()
    # From (7,8), preferred move is up to (6,8) which is a wall.
    # Fallback is left to (7,7) which is NOT a wall. So it should move there.
    assert game.hazards[0] == (7, 7)


def test_hazard_stuck_in_room():
    """Hazard fully enclosed by walls should not move."""
    # (3,3) is inside the top-left room — surrounded by walls on 3 sides
    # Row 2 col 3 = wall, Row 3 col 2 = wall, Row 3 col 4 = wall
    # Player at (0,0) far away
    game.player_row = 0
    game.player_col = 0
    game.hazards = [(3, 3)]
    game.move_hazards_toward_player()
    # From (3,3): preferred up to (2,3) = wall. Fallback left to (3,2) = wall.
    # Both blocked — stays put.
    assert game.hazards[0] == (3, 3)


# =============================================================================
# GAME RESET TESTS
# =============================================================================

def test_reset_player_position():
    """reset_game() moves the player back to (0, 0)."""
    game.player_row = 10
    game.player_col = 12
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


def test_reset_tick_counter():
    """reset_game() resets the hazard tick counter."""
    game.hazard_tick_counter = 99
    game.reset_game()
    assert game.hazard_tick_counter == 0


# =============================================================================
# SPAWNING TESTS — collectible
# =============================================================================

def test_spawn_collectible_not_on_player():
    """The collectible should never spawn on the player's position."""
    game.player_row = 0
    game.player_col = 0
    game.spawn_collectible()
    assert (game.collectible_row, game.collectible_col) != (0, 0)


def test_spawn_collectible_within_grid():
    """The collectible should always be within grid boundaries."""
    for _ in range(50):
        game.spawn_collectible()
        assert 0 <= game.collectible_row < game.GRID_SIZE
        assert 0 <= game.collectible_col < game.GRID_SIZE


def test_collectible_avoids_hazards():
    """The collectible should never spawn on top of a hazard."""
    game.hazards = [(10, 0), (12, 5), (14, 8), (8, 12)]
    for _ in range(50):
        game.spawn_collectible()
        assert (game.collectible_row, game.collectible_col) not in game.hazards


def test_collectible_avoids_walls():
    """The collectible should never spawn on a wall."""
    for _ in range(100):
        game.spawn_collectible()
        assert (game.collectible_row, game.collectible_col) not in game.WALLS


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
    game.player_row = 10
    game.player_col = 10
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


def test_spawn_hazards_avoids_walls():
    """No hazard should spawn on a wall."""
    for _ in range(30):
        game.spawn_hazards()
        for pos in game.hazards:
            assert pos not in game.WALLS


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
    game.collectible_row = 10
    game.collectible_col = 10
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
    game.hazards = [(10, 10), (12, 12)]
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
    game.player_row = 5
    game.player_col = 5
    assert game.is_position_occupied(5, 5) is True


def test_is_position_occupied_by_collectible():
    """Returns True if the position matches the collectible's position."""
    game.collectible_row = 7
    game.collectible_col = 10
    assert game.is_position_occupied(7, 10) is True


def test_is_position_occupied_by_hazard():
    """Returns True if the position matches any hazard's position."""
    game.hazards = [(10, 10)]
    assert game.is_position_occupied(10, 10) is True


def test_is_position_occupied_by_wall():
    """Returns True if the position is a wall."""
    # (2,2) is a wall in the layout
    assert game.is_position_occupied(2, 2) is True


def test_is_position_occupied_empty():
    """Returns False if the position is empty."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 10
    game.collectible_col = 10
    game.hazards = [(12, 12)]
    assert game.is_position_occupied(14, 14) is False


def test_get_cell_content_player():
    """Shows the player emoji where the player is."""
    game.player_row = 1
    game.player_col = 1
    game.collectible_row = 10
    game.collectible_col = 10
    game.hazards = [(12, 12)]
    assert game.get_cell_content(1, 1) == f" {game.PLAYER_EMOJI} "


def test_get_cell_content_collectible():
    """Shows the collectible emoji where the collectible is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 10
    game.collectible_col = 10
    game.hazards = [(12, 12)]
    assert game.get_cell_content(10, 10) == f" {game.COLLECTIBLE_EMOJI} "


def test_get_cell_content_hazard():
    """Shows the hazard emoji where any hazard is."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 10
    game.collectible_col = 10
    game.hazards = [(12, 12), (14, 5)]
    assert game.get_cell_content(12, 12) == f" {game.HAZARD_EMOJI} "
    assert game.get_cell_content(14, 5) == f" {game.HAZARD_EMOJI} "


def test_get_cell_content_wall():
    """Shows the wall emoji for wall cells."""
    # (2,2) is a wall
    assert game.get_cell_content(2, 2) == f" {game.WALL_EMOJI} "
    # (6,7) is a wall (center room)
    assert game.get_cell_content(6, 7) == f" {game.WALL_EMOJI} "


def test_get_cell_content_empty():
    """Shows '.' for an empty cell."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 10
    game.collectible_col = 10
    game.hazards = [(12, 12)]
    assert game.get_cell_content(14, 14) == " . "


# =============================================================================
# TIME CALCULATION TEST
# =============================================================================

def test_calculate_time_remaining():
    """Time remaining should decrease as time passes."""
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


def test_bullet_emoji():
    """Bullet emoji should be the red circle."""
    assert game.BULLET_EMOJI == "\U0001F534"


def test_wall_emoji():
    """Wall emoji should be the brick wall."""
    assert game.WALL_EMOJI == "\U0001F9F1"


def test_win_message():
    """Win message should match the theme."""
    assert game.WIN_MESSAGE == "You won"


def test_lose_message():
    """Lose message should match the theme."""
    assert game.LOSE_MESSAGE == "Try again"


def test_cell_content_uses_correct_emojis():
    """Each cell type should return the correct themed emoji."""
    game.player_row = 0
    game.player_col = 0
    game.collectible_row = 10
    game.collectible_col = 10
    game.hazards = [(12, 12)]

    assert game.PLAYER_EMOJI in game.get_cell_content(0, 0)
    assert game.COLLECTIBLE_EMOJI in game.get_cell_content(10, 10)
    assert game.HAZARD_EMOJI in game.get_cell_content(12, 12)
    assert game.WALL_EMOJI in game.get_cell_content(2, 2)
    assert game.get_cell_content(14, 14) == " . "


# =============================================================================
# DIRECTION DELTAS TESTS
# =============================================================================

def test_direction_deltas_are_correct():
    """Each arrow key should map to the correct row/col change."""
    assert game.DIRECTION_DELTAS["UP"] == (-1, 0)
    assert game.DIRECTION_DELTAS["DOWN"] == (1, 0)
    assert game.DIRECTION_DELTAS["LEFT"] == (0, -1)
    assert game.DIRECTION_DELTAS["RIGHT"] == (0, 1)


# =============================================================================
# GRID AND WALL LAYOUT TESTS
# =============================================================================

def test_grid_size_is_16():
    """Grid should be 16x16."""
    assert game.GRID_SIZE == 16


def test_wall_map_has_16_rows():
    """Wall map should have exactly 16 rows."""
    assert len(game.WALL_MAP) == 16


def test_wall_map_rows_are_16_chars():
    """Each row in the wall map should be exactly 16 characters."""
    for idx, row in enumerate(game.WALL_MAP):
        assert len(row) == 16, f"Row {idx} has length {len(row)}"


def test_walls_are_set_of_tuples():
    """Walls should be a set of (row, col) tuples."""
    assert isinstance(game.WALLS, set)
    for pos in game.WALLS:
        assert isinstance(pos, tuple)
        assert len(pos) == 2


def test_wall_count_reasonable():
    """Should have a reasonable number of walls (30-60) for a 16x16 grid."""
    assert 30 <= len(game.WALLS) <= 60


# =============================================================================
# HAZARD TICK COUNTER TESTS
# =============================================================================

def test_hazard_tick_counter_exists():
    """The tick counter should exist and start at 0 after reset."""
    game.hazard_tick_counter = 10
    game.reset_game()
    assert game.hazard_tick_counter == 0


def test_hazard_move_interval_config():
    """HAZARD_MOVE_EVERY_N_TICKS should be at least 2 (slower than every tick)."""
    assert game.HAZARD_MOVE_EVERY_N_TICKS >= 2
