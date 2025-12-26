


import os
from colorama import Fore, Style

def print_plex_logo_ascii():
    file_path = os.path.join(os.path.dirname(__file__), "plex_ascii.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Split the line by "1" to identify the sections
            parts = line.rstrip("\n").split("1")

            # If we have 5 parts (P, L, E, Arrow, Rest), color the 4th part (index 3)
            if len(parts) == 5:
                print(Fore.WHITE + parts[0] + parts[1] + parts[2] + Fore.YELLOW + parts[3] + Fore.WHITE + parts[4] + Style.RESET_ALL)
            # If we have 3 parts (Start, Arrow, End), color the middle part
            elif len(parts) == 3:
                print(Fore.WHITE + parts[0] + Fore.YELLOW + parts[1] + Fore.WHITE + parts[2] + Style.RESET_ALL)
            else:
                print(Fore.WHITE + "".join(parts) + Style.RESET_ALL)
