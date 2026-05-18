COLOR_PLAYER = "\033[96m"
COLOR_DM = "\033[92m"
COLOR_RESET = "\033[0m"


def get_player_input(prompt_text: str = "> Player: ") -> str:
    return input(f"{COLOR_PLAYER}{prompt_text}{COLOR_RESET}")


def display_output(text: str):
    print(f"{COLOR_DM}{text}{COLOR_RESET}")
