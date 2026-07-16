import os
import random
import select
import sys
import time
import tty
import termios

# =============================================================================
# GAME CONFIGURATION
# =============================================================================

GRID_SIZE = 5          # The grid is 5x5 cells
WIN_SCORE = 10         # Collect 10 items to win
TIME_LIMIT = 60        # 60 seconds to complete the game
STARTING_LIVES = 2     # Player begins with 2 lives
MIN_HAZARDS = 2        # Minimum number of hazards on the grid
MAX_HAZARDS = 4        # Maximum number of hazards on the grid
HAZARD_MOVE_MIN = 2    # Minimum seconds between hazard moves
HAZARD_MOVE_MAX = 5    # Maximum seconds between hazard moves

# =============================================================================
# CUSTOM THEME
# =============================================================================

GAME_NAME = "Australian Jones"
STORY_INTRO = "Find and collect treasures and avoid traps"
PLAYER_EMOJI = "\U0001F3A9"       # 🎩
COLLECTIBLE_EMOJI = "\U0001F4E6"  # 📦
HAZARD_EMOJI = "\U0001F30B"       # 🌋
WIN_MESSAGE = "You won"
LOSE_MESSAGE = "Try again"

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

# Hazards are stored as a list of (row, col) tuples.
# There will be 2 to 4 hazards on the grid at any time.
hazards: list[tuple[int, int]] = []


# =============================================================================
# SINGLE KEYPRESS INPUT
# =============================================================================
# Instead of waiting for the player to press Enter, we read one character
# at a time directly from the terminal. This makes movement feel instant.
# We use the 'tty' and 'termios' modules which work on Linux/Mac.

def get_keypress() -> str:
    """
    Wait for the player to press a single key and return it immediately.
    No Enter needed! The terminal is temporarily switched to 'raw' mode
    so each keypress is captured right away.

    Returns:
        The character the player pressed (e.g., 'w', 'a', 's', 'd', 'q').
    """
    # Save the current terminal settings so we can restore them later
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        # Switch terminal to raw mode — captures keys without waiting for Enter
        tty.setraw(fd)
        # Read one character from standard input
        key = sys.stdin.read(1)
    finally:
        # Always restore the terminal settings, even if something goes wrong
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return key


def get_keypress_with_timeout(timeout: float) -> str | None:
    """
    Wait up to 'timeout' seconds for a keypress.
    Returns the key if pressed, or None if the timeout expires.

    This lets us do other things (like move hazards) when the player
    hasn't pressed a key yet.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        # select() waits for input OR until timeout — whichever comes first
        # The first arg is a list of file descriptors to check for reading
        ready, _, _ = select.select([fd], [], [], timeout)
        if ready:
            # A key was pressed — read it
            key = sys.stdin.read(1)
            return key
        else:
            # Timeout expired — no key was pressed
            return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# =============================================================================
# SCREEN DRAWING
# =============================================================================

def clear_screen() -> None:
    """Clear the terminal so each frame replaces the previous one."""
    os.system("cls" if os.name == "nt" else "clear")


def draw_header(time_remaining: float) -> None:
    """Print the game title and current stats (score, lives, time)."""
    print(f"=== {GAME_NAME} ===")
    print(f"Score: {score}/{WIN_SCORE}  |  Lives: {lives}  |  Time left: {time_remaining:.1f}s")
    print("WASD to move | Q to quit\n")


def get_cell_content(row: int, col: int) -> str:
    """
    Decide what to display in a single grid cell.

    Priority order:
      1. Player emoji — if the player is here
      2. Collectible emoji — if the collectible is here
      3. Hazard emoji — if any hazard is here
      4. '.' — empty cell
    """
    if row == player_row and col == player_col:
        return f" {PLAYER_EMOJI} "
    elif row == collectible_row and col == collectible_col:
        return f" {COLLECTIBLE_EMOJI} "
    elif (row, col) in hazards:
        return f" {HAZARD_EMOJI} "
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
# GAME STATE MANAGEMENT
# =============================================================================

def reset_game() -> None:
    """Reset all game state to default values for a fresh game."""
    global player_row, player_col, score, lives
    global collectible_row, collectible_col, hazards

    player_row = 0
    player_col = 0
    score = 0
    lives = STARTING_LIVES
    collectible_row = 0
    collectible_col = 0
    hazards = []


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
    """Check if a position is taken by the player, collectible, or any hazard."""
    if row == player_row and col == player_col:
        return True
    if row == collectible_row and col == collectible_col:
        return True
    if (row, col) in hazards:
        return True
    return False


def spawn_collectible() -> None:
    """Place the collectible '*' at a random empty position on the grid."""
    global collectible_row, collectible_col

    while True:
        collectible_row = random.randint(0, GRID_SIZE - 1)
        collectible_col = random.randint(0, GRID_SIZE - 1)
        # Avoid the player and all hazards (but NOT itself — it hasn't been placed yet)
        if (collectible_row, collectible_col) == (player_row, player_col):
            continue
        if (collectible_row, collectible_col) in hazards:
            continue
        break


def _spawn_one_hazard() -> tuple[int, int]:
    """
    Pick a single random position that isn't occupied by anything.
    Returns the (row, col) position.
    """
    while True:
        row = random.randint(0, GRID_SIZE - 1)
        col = random.randint(0, GRID_SIZE - 1)
        if not is_position_occupied(row, col):
            return (row, col)


def spawn_hazards() -> None:
    """
    Place between MIN_HAZARDS and MAX_HAZARDS hazards on the grid.
    Each hazard is placed at a random empty position.
    """
    global hazards

    hazards = []
    # Pick a random number of hazards between MIN and MAX
    num_hazards = random.randint(MIN_HAZARDS, MAX_HAZARDS)

    for _ in range(num_hazards):
        pos = _spawn_one_hazard()
        hazards.append(pos)


def move_hazards() -> None:
    """
    Move all hazards to new random positions on the grid.
    This makes the game more dynamic — hazards shift every 2-5 seconds!
    No two hazards will end up on the same position.
    """
    global hazards

    num_hazards = len(hazards)
    # Temporarily clear hazards so new positions don't avoid old ones
    hazards = []

    for _ in range(num_hazards):
        pos = _spawn_one_hazard()
        hazards.append(pos)


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
    Check if the player stepped on any hazard.
    Returns True if the player was hit (a life was lost).
    If hit, the specific hazard is respawned to a new position.
    """
    global lives, hazards

    player_pos = (player_row, player_col)
    if player_pos in hazards:
        lives -= 1
        # Remove the hazard the player stepped on and respawn a new one
        hazards.remove(player_pos)
        new_pos = _spawn_one_hazard()
        hazards.append(new_pos)
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
# GAME LOOP HELPERS
# =============================================================================

def calculate_time_remaining(start_time: float) -> float:
    """Calculate how many seconds are left in the game."""
    elapsed = time.time() - start_time
    return max(TIME_LIMIT - elapsed, 0.0)


def play_again_prompt() -> bool:
    """
    Ask the player if they want to play again.
    Returns True if they type 'y', False for anything else.
    """
    print("\nPlay again? (y/n): ")
    while True:
        key = get_keypress().lower()
        if key == "y":
            return True
        elif key == "n":
            return False
        # Ignore any other key — just wait for y or n


def show_end_screen(message: str) -> None:
    """Display a final message (win, lose, or time's up)."""
    clear_screen()
    print(f"=== {GAME_NAME} ===\n")
    print(message)


# =============================================================================
# MAIN GAME LOOP
# =============================================================================

def run_game() -> bool:
    """
    Run a single game from start to finish.

    Returns:
        True if the player wants to play again, False to quit.
    """
    # Set up the initial game state
    reset_game()
    spawn_collectible()
    spawn_hazards()

    # Show the welcome screen and wait for the player to start
    clear_screen()
    print(f"=== {GAME_NAME} ===\n")
    print(f"{STORY_INTRO}!\n")
    print(f"Collect {COLLECTIBLE_EMOJI} to score. Avoid {HAZARD_EMOJI} traps!")
    print(f"You have {TIME_LIMIT} seconds, {STARTING_LIVES} lives,")
    print(f"and {len(hazards)} traps to dodge.")
    print(f"Traps move every {HAZARD_MOVE_MIN}-{HAZARD_MOVE_MAX} seconds!")
    print("WASD to move. Q to quit.\n")
    print("Press any key to start...")
    get_keypress()

    start_time = time.time()
    # Pick when the hazards will first move
    next_hazard_move = time.time() + random.uniform(HAZARD_MOVE_MIN, HAZARD_MOVE_MAX)

    while True:
        # --- Check if time has run out ---
        time_remaining = calculate_time_remaining(start_time)
        if time_remaining <= 0:
            show_end_screen(
                f"Time's up! You collected {score}/{WIN_SCORE} treasures.\n"
                f"{LOSE_MESSAGE}!"
            )
            return play_again_prompt()

        # --- Draw the grid ---
        draw_grid(time_remaining)

        # --- Wait for a keypress, but only for a short time ---
        # This lets hazards move even if the player doesn't press anything
        time_until_hazard = max(next_hazard_move - time.time(), 0.1)
        key = get_keypress_with_timeout(time_until_hazard)

        # --- If no key was pressed, it's time to move the hazards ---
        if key is None:
            move_hazards()
            # Pick the next random time for hazards to move
            next_hazard_move = time.time() + random.uniform(HAZARD_MOVE_MIN, HAZARD_MOVE_MAX)
            continue  # Redraw the grid with new hazard positions

        key = key.lower()

        # --- Handle quit ---
        if key == "q":
            show_end_screen("Thanks for playing! See ya, mate!")
            return False

        # --- Move the player ---
        move_player(key)

        # --- Check if the player hit a hazard ---
        if check_hazard():
            if has_lost():
                show_end_screen(
                    f"{LOSE_MESSAGE}! You collected {score}/{WIN_SCORE} treasures "
                    "but ran out of lives."
                )
                return play_again_prompt()

        # --- Check if the player collected an item ---
        if check_collectible():
            if has_won():
                elapsed = time.time() - start_time
                show_end_screen(
                    f"{WIN_MESSAGE}! Collected {score} treasures in {elapsed:.1f} seconds!"
                )
                return play_again_prompt()
            else:
                # Player collected an item — spawn a new one
                spawn_collectible()


def main() -> None:
    """
    Top-level game loop. Handles the play-again cycle.
    Keeps running until the player chooses not to play again.
    """
    while True:
        play_again = run_game()
        if not play_again:
            break

    clear_screen()
    print("Thanks for playing! See ya, mate!")


# =============================================================================
# ENTRY POINT
# =============================================================================
# This runs main() only when you execute this file directly.
# It does NOT run if another file imports this one as a module.

if __name__ == "__main__":
    main()
