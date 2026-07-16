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

GRID_SIZE = 16         # The grid is 16x16 cells
WIN_SCORE = 10         # Collect 10 items to win
TIME_LIMIT = 120       # 120 seconds to complete the game
STARTING_LIVES = 2     # Player begins with 2 lives
MIN_HAZARDS = 3        # Minimum number of hazards on the grid
MAX_HAZARDS = 5        # Maximum number of hazards on the grid
HAZARD_MOVE_EVERY_N_TICKS = 3  # Hazards move once every 3 ticks (~0.9s)
HAZARD_RESPAWN_DELAY = 2.0     # Seconds before a destroyed hazard respawns

# =============================================================================
# CUSTOM THEME
# =============================================================================

GAME_NAME = "Australian Jones"
STORY_INTRO = "Find and collect treasures and avoid traps"
PLAYER_EMOJI = "\U0001F3CD"       # 🏍️
COLLECTIBLE_EMOJI = "\U0001F4E6"  # 📦
HAZARD_EMOJI = "\U0001F30B"       # 🌋
BULLET_EMOJI = "\U0001F534"       # 🔴
WALL_EMOJI = "\U0001F9F1"         # 🧱
WIN_MESSAGE = "You won"
LOSE_MESSAGE = "Try again"

# =============================================================================
# WALL LAYOUT
# =============================================================================
# Each character = one cell.  # = wall, . = empty.
# The walls create rooms and corridors that slow hazards down.
# Player starts at (0,0) which is always clear.

WALL_MAP = [
    "................",  # row 0
    "................",  # row 1
    "..###.....###...",  # row 2
    "..#.#.....#.#...",  # row 3
    "....#.....#.....",  # row 4
    "..###.....###...",  # row 5
    "......#####.....",  # row 6
    "......#...#.....",  # row 7
    "......#...#.....",  # row 8
    "......#####.....",  # row 9
    "..#.#.....#.#...",  # row 10
    "..###.....###...",  # row 11
    "................",  # row 12
    "................",  # row 13
    "................",  # row 14
    "................",  # row 15
]

# Parse the map into a set of (row, col) tuples for fast lookups
WALLS: set[tuple[int, int]] = set()
for _row_idx, _row_str in enumerate(WALL_MAP):
    for _col_idx, _char in enumerate(_row_str):
        if _char == "#":
            WALLS.add((_row_idx, _col_idx))

# =============================================================================
# GAME STATE
# =============================================================================

player_row = 0         # Player's current row position
player_col = 0         # Player's current column position
score = 0              # How many items the player has collected
lives = STARTING_LIVES # How many lives the player has left

collectible_row = 0    # Row of the collectible item
collectible_col = 0    # Column of the collectible item

# Hazards are stored as a list of (row, col) tuples.
hazards: list[tuple[int, int]] = []

# Direction the player is facing (used for shooting).
# Starts as "right" — updated every time the player moves.
player_direction = "right"

# Tick counter for slowing down hazard movement
hazard_tick_counter = 0

# Timestamps when destroyed hazards should respawn (2-second delay)
pending_respawns: list[float] = []


# =============================================================================
# SINGLE KEYPRESS INPUT (with arrow key support)
# =============================================================================
# Arrow keys send escape sequences (3 bytes: ESC [ letter).
# We read the first byte and, if it's ESC, read the next 2 to identify
# which arrow was pressed.

# Arrow key escape sequences mapped to readable names
ARROW_KEYS = {
    "\x1b[A": "UP",
    "\x1b[B": "DOWN",
    "\x1b[C": "RIGHT",
    "\x1b[D": "LEFT",
}


def _read_key_from_fd(fd: int) -> str:
    """
    Read a single keypress from a raw file descriptor.
    Handles arrow key escape sequences (3-byte sequences starting with ESC).
    Returns a readable name like "UP", "DOWN", or the raw character.
    """
    char = sys.stdin.read(1)

    # If it's an escape character, read the rest of the sequence
    if char == "\x1b":
        # Read up to 2 more characters to complete the escape sequence
        seq = char + sys.stdin.read(2)
        # Check if it matches a known arrow key
        return ARROW_KEYS.get(seq, "")
    else:
        return char


def get_keypress() -> str:
    """
    Wait for a single keypress and return it.
    Handles arrow keys, spacebar, and regular characters.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        return _read_key_from_fd(fd)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_keypress_with_timeout(timeout: float) -> str | None:
    """
    Wait up to 'timeout' seconds for a keypress.
    Returns the key if pressed, or None if the timeout expires.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        ready, _, _ = select.select([fd], [], [], timeout)
        if ready:
            return _read_key_from_fd(fd)
        else:
            return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# =============================================================================
# SCREEN DRAWING
# =============================================================================
# We use ANSI escape codes instead of os.system("clear") to avoid flickering.
# \033[H   = move cursor to top-left (home position)
# \033[J   = clear everything from cursor to end of screen
# \033[?25l = hide the cursor   \033[?25h = show the cursor

def clear_screen() -> None:
    """Move cursor to top-left and clear everything below — no flicker."""
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()


def hide_cursor() -> None:
    """Hide the blinking terminal cursor during gameplay."""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor() -> None:
    """Show the terminal cursor again (used when the game ends)."""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def get_cell_content(row: int, col: int) -> str:
    """
    Decide what to display in a single grid cell.
    Priority: Player > Collectible > Hazard > Wall > Empty
    """
    if row == player_row and col == player_col:
        return f" {PLAYER_EMOJI} "
    elif row == collectible_row and col == collectible_col:
        return f" {COLLECTIBLE_EMOJI} "
    elif (row, col) in hazards:
        return f" {HAZARD_EMOJI} "
    elif (row, col) in WALLS:
        return f" {WALL_EMOJI} "
    else:
        return " . "


def draw_grid(time_remaining: float) -> None:
    """
    Draw the full game frame — ONE write, ZERO flicker, ZERO ghosting.
    Every frame: jump to top-left, write the whole grid, then clear
    any leftover lines below. All in a single sys.stdout.write() call,
    so the terminal renders the entire frame in one shot.
    """
    # --- Build the frame as a list of lines ---
    lines = []
    lines.append(f"=== {GAME_NAME} ===")
    lines.append(f"Score: {score}/{WIN_SCORE}  |  Lives: {lives}  |  Time left: {time_remaining:.1f}s")
    lines.append(f"{PLAYER_EMOJI} move | {BULLET_EMOJI} auto-shoot (space) | Q quit")
    lines.append("")  # blank line for spacing

    for row in range(GRID_SIZE):
        line = "".join(get_cell_content(row, col) for col in range(GRID_SIZE))
        lines.append(line)

    frame = "\n".join(lines)

    # \033[H  = cursor to top-left    \033[J = clear from cursor to end
    sys.stdout.write(f"\033[H{frame}\033[J")
    sys.stdout.flush()


# =============================================================================
# GAME STATE MANAGEMENT
# =============================================================================

def reset_game() -> None:
    """Reset all game state to default values for a fresh game."""
    global player_row, player_col, score, lives, player_direction
    global collectible_row, collectible_col, hazards, hazard_tick_counter
    global pending_respawns

    player_row = 0
    player_col = 0
    score = 0
    lives = STARTING_LIVES
    player_direction = "right"
    collectible_row = 0
    collectible_col = 0
    hazards = []
    hazard_tick_counter = 0
    pending_respawns = []


# =============================================================================
# PLAYER MOVEMENT
# =============================================================================

# Map arrow key names to row/col changes
DIRECTION_DELTAS = {
    "UP":    (-1,  0),
    "DOWN":  ( 1,  0),
    "LEFT":  ( 0, -1),
    "RIGHT": ( 0,  1),
}

# Map arrow key names to direction labels (for shooting)
DIRECTION_LABELS = {
    "UP":    "up",
    "DOWN":  "down",
    "LEFT":  "left",
    "RIGHT": "right",
}


def move_player(direction: str) -> bool:
    """
    Move the player in the given direction (UP/DOWN/LEFT/RIGHT arrow keys).
    Returns True if the player actually moved, False if blocked by boundary or wall.
    Updates player_direction so we know which way the player is facing.
    """
    global player_row, player_col, player_direction

    if direction not in DIRECTION_DELTAS:
        return False

    delta_row, delta_col = DIRECTION_DELTAS[direction]
    new_row = player_row + delta_row
    new_col = player_col + delta_col

    # Boundary check
    if new_row < 0 or new_row >= GRID_SIZE:
        return False
    if new_col < 0 or new_col >= GRID_SIZE:
        return False

    # Wall check — can't walk through walls
    if (new_row, new_col) in WALLS:
        return False

    player_row = new_row
    player_col = new_col
    # Remember which way the player is facing (for shooting)
    player_direction = DIRECTION_LABELS[direction]
    return True


# =============================================================================
# SHOOTING
# =============================================================================

def shoot() -> bool:
    """
    Auto-target the closest hazard and fire a bullet toward it.
    The bullet travels horizontally or vertically (not diagonally).
    The player does NOT choose the direction — the game picks automatically.

    Returns True if a hazard was destroyed, False otherwise.
    """
    global hazards

    # No hazards on the grid — nothing to shoot
    if not hazards:
        return False

    # --- Step 1: Find the closest hazard by Manhattan distance ---
    best_hazard = None
    best_distance = float("inf")

    for h_row, h_col in hazards:
        distance = abs(h_row - player_row) + abs(h_col - player_col)
        if distance < best_distance:
            best_distance = distance
            best_hazard = (h_row, h_col)

    if best_hazard is None:
        return False

    h_row, h_col = best_hazard
    row_diff = h_row - player_row
    col_diff = h_col - player_col

    # Hazard is on the player's position — can't shoot (shouldn't happen)
    if row_diff == 0 and col_diff == 0:
        return False

    # --- Step 2: Pick a direction (horizontal or vertical) ---
    if row_diff == 0:
        # Same row — shoot horizontally
        delta_row, delta_col = 0, (1 if col_diff > 0 else -1)
    elif col_diff == 0:
        # Same column — shoot vertically
        delta_row, delta_col = (1 if row_diff > 0 else -1), 0
    elif abs(row_diff) <= abs(col_diff):
        # Diagonal — prefer vertical (closer axis)
        delta_row, delta_col = (1 if row_diff > 0 else -1), 0
    else:
        # Diagonal — prefer horizontal (closer axis)
        delta_row, delta_col = 0, (1 if col_diff > 0 else -1)

    # --- Step 3: Travel in a straight line until we hit something ---
    row = player_row + delta_row
    col = player_col + delta_col

    while 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        # Bullet stops at walls
        if (row, col) in WALLS:
            return False
        # Check if there's a hazard at this position
        if (row, col) in hazards:
            destroy_hazard((row, col))
            return True
        # Move further along the line
        row += delta_row
        col += delta_col

    # No hazard found — bullet went off the edge
    return False


# =============================================================================
# HAZARD AI — hazards chase the player, respecting walls
# =============================================================================

def move_hazards_toward_player() -> None:
    """
    Move each hazard one step closer to the player.
    Uses greedy pathfinding with wall avoidance:
    - Try to move along the axis with the largest distance.
    - If that direction is blocked by a wall, try the other axis.
    - If both are blocked, stay put.
    """
    global hazards

    new_hazards = []

    for hazard_row, hazard_col in hazards:
        # Already adjacent to the player — stay put
        if abs(hazard_row - player_row) <= 1 and abs(hazard_col - player_col) <= 1:
            new_hazards.append((hazard_row, hazard_col))
            continue

        # Calculate distance on each axis
        row_diff = player_row - hazard_row
        col_diff = player_col - hazard_col

        # Build a list of candidate moves, preferred axis first
        if abs(row_diff) >= abs(col_diff):
            # Prefer vertical, fall back to horizontal
            candidates = [
                (hazard_row + (1 if row_diff > 0 else -1), hazard_col),
                (hazard_row, hazard_col + (1 if col_diff > 0 else -1)),
            ]
        else:
            # Prefer horizontal, fall back to vertical
            candidates = [
                (hazard_row, hazard_col + (1 if col_diff > 0 else -1)),
                (hazard_row + (1 if row_diff > 0 else -1), hazard_col),
            ]

        moved = False
        for new_row, new_col in candidates:
            # Skip if out of bounds
            if not (0 <= new_row < GRID_SIZE and 0 <= new_col < GRID_SIZE):
                continue
            # Skip if blocked by a wall
            if (new_row, new_col) in WALLS:
                continue
            # Don't move onto the player (collision handled separately)
            if (new_row, new_col) == (player_row, player_col):
                continue
            # Don't move onto another hazard
            if (new_row, new_col) in new_hazards:
                continue
            # Valid move!
            new_hazards.append((new_row, new_col))
            moved = True
            break

        # If both directions were blocked, stay put
        if not moved:
            new_hazards.append((hazard_row, hazard_col))

    hazards = new_hazards


# =============================================================================
# SPAWNING (placing items on the grid)
# =============================================================================

def is_position_occupied(row: int, col: int) -> bool:
    """Check if a position is taken by the player, collectible, a hazard, or a wall."""
    if (row, col) in WALLS:
        return True
    if row == player_row and col == player_col:
        return True
    if row == collectible_row and col == collectible_col:
        return True
    if (row, col) in hazards:
        return True
    return False


def spawn_collectible() -> None:
    """Place the collectible at a random empty position on the grid (not on a wall)."""
    global collectible_row, collectible_col

    while True:
        collectible_row = random.randint(0, GRID_SIZE - 1)
        collectible_col = random.randint(0, GRID_SIZE - 1)
        if (collectible_row, collectible_col) == (player_row, player_col):
            continue
        if (collectible_row, collectible_col) in hazards:
            continue
        if (collectible_row, collectible_col) in WALLS:
            continue
        break


def _spawn_one_hazard() -> tuple[int, int]:
    """Pick a single random position that isn't occupied (including walls)."""
    while True:
        row = random.randint(0, GRID_SIZE - 1)
        col = random.randint(0, GRID_SIZE - 1)
        if not is_position_occupied(row, col):
            return (row, col)


def spawn_hazards() -> None:
    """Place between MIN_HAZARDS and MAX_HAZARDS hazards on the grid."""
    global hazards

    hazards = []
    num_hazards = random.randint(MIN_HAZARDS, MAX_HAZARDS)

    for _ in range(num_hazards):
        pos = _spawn_one_hazard()
        hazards.append(pos)


# =============================================================================
# COLLISION CHECKS
# =============================================================================

def destroy_hazard(position: tuple[int, int]) -> None:
    """
    Remove a hazard from the grid and schedule it to respawn
    after HAZARD_RESPAWN_DELAY seconds.
    """
    global hazards, pending_respawns

    if position in hazards:
        hazards.remove(position)
        pending_respawns.append(time.time() + HAZARD_RESPAWN_DELAY)


def respawn_pending_hazards() -> None:
    """Check if any destroyed hazards are due to respawn, and spawn them."""
    global pending_respawns

    now = time.time()
    # Find which respawns are ready
    ready = [t for t in pending_respawns if t <= now]
    # Keep only the ones still waiting
    pending_respawns = [t for t in pending_respawns if t > now]

    for _ in ready:
        pos = _spawn_one_hazard()
        hazards.append(pos)


def check_collectible() -> bool:
    """Check if the player stepped on the collectible."""
    global score

    if player_row == collectible_row and player_col == collectible_col:
        score += 1
        return True
    return False


def check_hazard() -> bool:
    """Check if the player stepped on any hazard."""
    global lives

    player_pos = (player_row, player_col)
    if player_pos in hazards:
        lives -= 1
        destroy_hazard(player_pos)
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
    """Ask the player if they want to play again."""
    print("\nPlay again? (y/n): ")
    while True:
        key = get_keypress().lower()
        if key == "y":
            return True
        elif key == "n":
            return False


def end_game(message: str) -> bool:
    """
    Show the end screen with a message, then ask to play again.
    Returns True if the player wants another round, False to quit.
    """
    show_cursor()  # Bring back the cursor for the prompt
    # Build the entire screen as one string to avoid flicker
    frame = f"\033[H\033[J=== {GAME_NAME} ===\n\n{message}"
    sys.stdout.write(frame)
    sys.stdout.flush()
    return play_again_prompt()


# =============================================================================
# SETUP AND WELCOME
# =============================================================================

def setup_game() -> None:
    """Reset all state and place items on the grid for a fresh game."""
    reset_game()
    spawn_collectible()
    spawn_hazards()


def show_welcome_screen() -> None:
    """Display the intro screen with instructions, then wait for a keypress."""
    # Enter the alternate screen buffer — a clean canvas with no ghosting.
    # This is what vim, htop, less etc. use to avoid leftover content.
    sys.stdout.write("\033[?1049h")
    hide_cursor()  # Hide blinking cursor during gameplay
    # Build the entire screen as one string to avoid flicker
    frame = "\n".join([
        f"\033[H\033[J=== {GAME_NAME} ===",
        "",
        f"{STORY_INTRO}!",
        "",
        f"Collect {COLLECTIBLE_EMOJI} to score. Avoid {HAZARD_EMOJI} traps!",
        f"Press SPACE to auto-shoot the nearest {HAZARD_EMOJI} with {BULLET_EMOJI}!",
        f"{WALL_EMOJI} walls block your path — and the hazards'!",
        f"You have {TIME_LIMIT} seconds and {STARTING_LIVES} lives.",
        "Arrow keys to move. Q to quit.",
        "",
        "Press any key to start...",
    ])
    sys.stdout.write(frame)
    sys.stdout.flush()
    get_keypress()


# =============================================================================
# TICK PROCESSING — what happens each frame
# =============================================================================

def move_hazards_on_idle() -> bool:
    """
    Called when no key was pressed (idle tick).
    Moves hazards toward the player on their slow schedule.
    Returns True if a hazard reached the player and killed them.
    """
    global hazard_tick_counter

    hazard_tick_counter += 1

    # Only move hazards every N ticks (slower movement)
    if hazard_tick_counter % HAZARD_MOVE_EVERY_N_TICKS != 0:
        return False

    # Move all hazards one step closer to the player
    move_hazards_toward_player()

    # Did any hazard reach the player?
    if check_hazard() and has_lost():
        return True

    return False


def process_keypress(key: str) -> str:
    """
    Handle a single keypress from the player.
    Returns:
        'quit'  — player pressed Q
        'acted' — player shot or moved
        'ignore' — unknown key, do nothing
    """
    if key == "q":
        return "quit"

    if key == " ":
        shoot()  # Auto-target and fire at the nearest hazard
        return "acted"

    if key in DIRECTION_LABELS:
        move_player(key)
        return "acted"

    return "ignore"


def check_player_status() -> str:
    """
    After the player moved or shot, check what happened.
    Returns:
        'dead'      — player hit a hazard and lost all lives
        'won'       — player collected enough items to win
        'collected' — player picked up an item (game continues)
        'ok'        — nothing special happened
    """
    if check_hazard() and has_lost():
        return "dead"

    if check_collectible():
        if has_won():
            return "won"
        return "collected"

    return "ok"


# =============================================================================
# MAIN GAME LOOP
# =============================================================================

def run_game() -> bool:
    """
    Run a single game from start to finish.
    Returns True if the player wants to play again, False to quit.
    """
    # --- Set up the board ---
    setup_game()
    show_welcome_screen()
    start_time = time.time()

    # --- Main loop: one iteration per "tick" ---
    while True:

        # 1. Has time run out?
        time_remaining = calculate_time_remaining(start_time)
        if time_remaining <= 0:
            msg = f"Time's up! You collected {score}/{WIN_SCORE} treasures.\n{LOSE_MESSAGE}!"
            return end_game(msg)

        # 1b. Respawn any destroyed hazards that are due
        respawn_pending_hazards()

        # 2. Draw the grid
        draw_grid(time_remaining)

        # 3. Wait for player input (with timeout so hazards can move)
        key = get_keypress_with_timeout(0.3)

        # 4. No key pressed → hazards move on their own schedule
        if key is None:
            if move_hazards_on_idle():
                msg = f"{LOSE_MESSAGE}! You collected {score}/{WIN_SCORE} treasures but the traps got you."
                return end_game(msg)
            continue  # Redraw grid with updated hazard positions

        # 5. Player pressed a key → process it
        action = process_keypress(key)

        if action == "quit":
            return end_game("Thanks for playing! See ya, mate!")

        # 6. Check what happened after the player acted
        status = check_player_status()

        if status == "dead":
            msg = f"{LOSE_MESSAGE}! You collected {score}/{WIN_SCORE} treasures but ran out of lives."
            return end_game(msg)

        if status == "won":
            elapsed = time.time() - start_time
            msg = f"{WIN_MESSAGE}! Collected {score} treasures in {elapsed:.1f} seconds!"
            return end_game(msg)

        if status == "collected":
            spawn_collectible()  # Place a new treasure on the grid


def main() -> None:
    """Top-level game loop. Handles the play-again cycle."""
    while True:
        play_again = run_game()
        if not play_again:
            break

    show_cursor()  # Always restore cursor on exit
    # Exit the alternate screen buffer — restores the original terminal content
    sys.stdout.write("\033[?1049l")
    sys.stdout.write("Thanks for playing! See ya, mate!\n")
    sys.stdout.flush()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
