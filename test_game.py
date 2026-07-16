import game


def setup_function():
    """Reset player position before each test."""
    game.player_row = 0
    game.player_col = 0


def test_move_right():
    game.move_player("d")
    assert game.player_row == 0
    assert game.player_col == 1


def test_move_down():
    game.move_player("s")
    assert game.player_row == 1
    assert game.player_col == 0


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
