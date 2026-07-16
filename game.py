import os
import random
import time

# =============================================================================
# GAME CONFIGURATION
# =============================================================================

GRID_SIZE = 5          # The grid is 5x5 cells
WIN_SCORE = 10         # Collect 10 items to win
TIME_LIMIT = 60        # 60 seconds to complete the game
STARTING_LIVES = 2     # Player begins with 2 lives

# =============================================================================
# GAME STATE
# =============================================================================
# These variables track the current state of the game.
# They start at default values and get updated as the player plays.

player_row = 0         # Player's current row position (starts at top)
player_col = 0         # Player's current column position (starts at left)
score = 0              # How many items the player has collected
lives = STARTING_LIVES # How many lives the player has left

collectible_row = 0    # Row of the collectible item '*'
collectible_col = 0    # Column of the collectible item '*'

hazard_row = 0         # Row of the hazard tile 'X'
hazard_col = 0         # Column of the hazard tile 'X'


# =============================================================================
# SCREEN DRAWING
# =============================================================================

def clear_screen() -> None:
    """Clear the terminal so each frame replaces the previous one."""
    os.system("cls" if os.name == "nt" else "clear")


def draw_header(time_remaining: float) -> None:
    """Print the game title and current stats (score, lives, time)."""
    print("=== My Terminal Game ===")
    print(f"Score: {score}/{WIN_SCORE}  |  Lives: {lives}  |  Time left: {time_remaining:.1f}s\n")


def get_cell_content(row: int, col: int) -> str:
    """
    Decide what to display in a single grid cell.

    Priority order:
      1. 'P' — if the player is here
      2. '*' — if the collectible is here
      3. 'X' — if the hazard is here
      4. '.' — empty cell
    """
    if row == player_row and col == player_col:
        return " P "
    elif row == collectible_row and col == collectible_col:
        return " * "
    elif row == hazard_row and col == hazard_col:
        return " X "
    else:
        return " . "


def draw_grid(time_remaining: float) -> None:
    """Draw the full game grid with header, stats, and all cells."""
    clear_screen()
    draw_header(time_remaining)

    # Loop through each row and column to draw every cell
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # end="" keeps all cells in the same row on the same line
            print(get_cell_content(row, col), end="")
        # After finishing a row, move to the next line
        print()

    print()  # Extra blank line for readability


# =============================================================================
# PLAYER MOVEMENT
# =============================================================================

def move_player(direction: str) -> None:
    """
    Move the player in the given direction (w/a/s/d).
    Boundary checks prevent the player from leaving the grid.
    """
    global player_row, player_col

    if direction == "w" and player_row > 0:
        # Move up — only if not already at the top edge
        player_row -= 1
    elif direction == "s" and player_row < GRID_SIZE - 1:
        # Move down — only if not already at the bottom edge
        player_row += 1
    elif direction == "a" and player_col > 0:
        # Move left — only if not already at the left edge
        player_col -= 1
    elif direction == "d" and player_col < GRID_SIZE - 1:
        # Move right — only if not already at the right edge
        player_col += 1


# =============================================================================
# SPAWNING (placing items on the grid)
# =============================================================================

def is_position_occupied(row: int, col: int) -> bool:
    """Check if a position is taken by the player or the collectible."""
    if row == player_row and col == player_col:
        return True
    if row == collectible_row and col == collectible_col:
        return True
    return False


def spawn_collectible() -> None:
    """Place the collectible '*' at a random empty position on the grid."""
    global collectible_row, collectible_col

    while True:
        collectible_row = random.randint(0, GRID_SIZE - 1)
        collectible_col = random.randint(0, GRID_SIZE - 1)
        # The collectible only needs to avoid the player's position
        if collectible_row != player_row or collectible_col != player_col:
            break


def spawn_hazard() -> None:
    """Place the hazard 'X' at a random empty position on the grid."""
    global hazard_row, hazard_col

    while True:
        hazard_row = random.randint(0, GRID_SIZE - 1)
        hazard_col = random.randint(0, GRID_SIZE - 1)
        # The hazard can't overlap with the player OR the collectible
        if hazard_row == player_row and hazard_col == player_col:
            continue
        if hazard_row == collectible_row and hazard_col == collectible_col:
            continue
        break


# =============================================================================
# COLLISION CHECKS (what happens when the player steps on something)
# =============================================================================

def check_collectible() -> bool:
    """
    Check if the player stepped on the collectible.
    Returns True if the player collected an item.
    """
    global score

    if player_row == collectible_row and player_col == collectible_col:
        score += 1
        return True
    return False


def check_hazard() -> bool:
    """
    Check if the player stepped on the hazard.
    Returns True if the player was hit (a life was lost).
    """
    global lives

    if player_row == hazard_row and player_col == hazard_col:
        lives -= 1
        return True
    return False


# =============================================================================
# WIN / LOSE CONDITIONS
# =============================================================================

def has_won() -> bool:
    """Return True if the player has collected enough items to win."""
    return score >= WIN_SCORE


def has_lost() -> bool:
    """Return True if the player has no lives left."""
    return lives <= 0


# =============================================================================
# GAME LOOP
# =============================================================================

def start_game() -> None:
    """Print the welcome message and instructions, then wait for the player."""
    print("Welcome! Use WASD to move. Collect '*' to score. Avoid 'X'!")
    print(f"You have {TIME_LIMIT} seconds and {lives} lives. Press 'q' to quit.\n")
    input("Press Enter to start...")


def calculate_time_remaining(start_time: float) -> float:
    """Calculate how many seconds are left in the game."""
    elapsed = time.time() - start_time
    return max(TIME_LIMIT - elapsed, 0.0)


def handle_time_up() -> None:
    """Show the time's up message and end the game."""
    draw_grid(0.0)
    print(f"Time's up! You only collected {score}/{WIN_SCORE} items.")
    print("Game over! Better luck next time.")


def handle_quit() -> bool:
    """Show the goodbye message. Returns True to signal the game should end."""
    print("Thanks for playing! Goodbye!")
    return True


def handle_hazard_hit(time_remaining: float) -> bool:
    """
    Handle what happens when the player steps on a hazard.
    Returns True if the game is over (no lives left).
    """
    if has_lost():
        draw_grid(time_remaining)
        print("Game Over! You ran out of lives.")
        return True
    else:
        # Player survived — move the hazard to a new spot
        spawn_hazard()
        return False


def handle_collectible_pickup(time_remaining: float, elapsed: float) -> bool:
    """
    Handle what happens when the player picks up a collectible.
    Returns True if the player has won.
    """
    if has_won():
        draw_grid(time_remaining)
        print(f"You win! Final score: {score} in {elapsed:.1f} seconds!")
        return True
    else:
        # Player collected an item — spawn a new one
        spawn_collectible()
        return False


def main() -> None:
    """
    The main game loop. Runs repeatedly until the game ends.
    Each turn: draw grid → get input → move player → check collisions → repeat.
    """
    global score, lives

    # Set up the initial game state
    spawn_collectible()
    spawn_hazard()
    start_game()

    start_time = time.time()

    while True:
        # --- Check if time has run out ---
        time_remaining = calculate_time_remaining(start_time)
        if time_remaining <= 0:
            handle_time_up()
            break

        # --- Draw the grid and get player input ---
        draw_grid(time_remaining)
        user_input = input("Your move: ").lower()

        # --- Handle quit ---
        if user_input == "q":
            if handle_quit():
                break

        # --- Move the player ---
        move_player(user_input)

        # --- Check if the player hit the hazard ---
        if check_hazard():
            if handle_hazard_hit(time_remaining):
                break

        # --- Check if the player collected an item ---
        if check_collectible():
            elapsed = time.time() - start_time
            if handle_collectible_pickup(time_remaining, elapsed):
                break


# =============================================================================
# ENTRY POINT
# =============================================================================
# This runs main() only when you execute this file directly.
# It does NOT run if another file imports this one as a module.

if __name__ == "__main__":
    main()
