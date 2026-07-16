import os

# --- Game State ---
# The grid is 5x5. Player starts at the top-left corner (row 0, col 0).
GRID_SIZE = 5
player_row = 0
player_col = 0


def draw_grid() -> None:
    """
    Draws the current game grid to the terminal.
    The player is shown as 'P' and empty cells as '.'.
    """
    # Clear the terminal so each frame looks fresh
    os.system("cls" if os.name == "nt" else "clear")

    print("=== My Terminal Game ===\n")

    # Loop through each row
    for row in range(GRID_SIZE):
        # Loop through each column in the current row
        for col in range(GRID_SIZE):
            # If this cell is where the player is, show 'P', otherwise '.'
            if row == player_row and col == player_col:
                print(" P ", end="")
            else:
                print(" . ", end="")
        # After printing all columns in a row, move to the next line
        print()

    print()


def move_player(direction: str) -> None:
    """
    Moves the player based on WASD input.
    Checks grid boundaries before updating position.
    """
    global player_row, player_col

    if direction == "w":
        # Move up — only if not already at the top row
        if player_row > 0:
            player_row -= 1
    elif direction == "s":
        # Move down — only if not already at the bottom row
        if player_row < GRID_SIZE - 1:
            player_row += 1
    elif direction == "a":
        # Move left — only if not already at the leftmost column
        if player_col > 0:
            player_col -= 1
    elif direction == "d":
        # Move right — only if not already at the rightmost column
        if player_col < GRID_SIZE - 1:
            player_col += 1


def main() -> None:
    """
    The main game loop. Repeatedly draws the grid and waits for input.
    Press 'q' to quit.
    """
    print("Welcome! Use WASD to move. Press 'q' to quit.\n")
    input("Press Enter to start...")

    while True:
        # 1. Draw the grid
        draw_grid()

        # 2. Wait for the player to type something and press Enter
        user_input = input("Your move: ").lower()

        # 3. If the player typed 'q', break out of the loop and end the game
        if user_input == "q":
            print("Thanks for playing! Goodbye!")
            break

        # 4. Move the player based on WASD input
        move_player(user_input)


# This runs main() only if you run this file directly (not if you import it)
if __name__ == "__main__":
    main()
