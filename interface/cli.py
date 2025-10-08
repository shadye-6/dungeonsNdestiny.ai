# interface/cli.py

def get_player_input() -> str:
    """
    Prompt the player for input.
    """
    return input("\n> Player: ")

def display_output(text: str):
    """
    Display the DM's response.
    """
    print(f"\nDM: {text}\n")
