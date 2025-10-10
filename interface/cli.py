COLOR_PLAYER = "\033[96m"   # Cyan
COLOR_DM = "\033[92m"       # Bright Green
COLOR_RESET = "\033[0m" 

def get_player_input() -> str:
    """
    Prompt the player for input.
    """
    return input(f"{COLOR_PLAYER}> Player: {COLOR_RESET}")

def display_output(text: str):
    """
    Display the DM's response.
    """
    print(f"{COLOR_DM}{text}{COLOR_RESET}")
