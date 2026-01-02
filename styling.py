from colorama import Fore, Style

# Custom Plex Yellow Colour (Hex: #EBAF01 -> RGB: 235, 175, 1)
PLEX_YELLOW = "\033[38;2;235;175;1m"

PLEX_LOGO_ASCII = r"""
                      .lOOOl.
                      .kMMMO.
   ....   .',,,.      .kMMMO.       .',;,'.    ......      ......
  .dKKKkokXWWWWX0d,   .kMMMO.   .:oxKNWWWWXOo,.'ldddo,   .oKKKKx'
  .kMMMMMWX0OKNMMMNd. .kMMMO.  ;0WMMWKkxk0NMMNd'.okkkxc..oWMMWx'
  .kMMMWk;.  .'oXMMWd..OMMMO. :XMMMXl.   .,OWMWk..:xkkko''xNXl.
  .kMMMk.       cNMMK,.OMMMO..kMMMMXkxxxxxx0WMMNc  ,dkkkd;.;,
  .kMMMd        :NMMX;.OMMMO..OMMMMXOOOOOOOOOOOk;  .okkkkc...
  .kMMMXl.     ;0MMMO..OMMMX: oWMMM0,     .''''.  ,dkkkd;.cKO,
  .kMMMMWKxoodONMMW0, .xMMMMO'.oNMMMXxlclxKNNXx'.:xkkko..lNMMXl.
  .kMMMNKXWMMMMMNOl.   'OWMMWd. ,dOKWMMMMMWXkc..lkkkxc.  ,kNMMWx.
  .kMMMK;.;clll:'.      .,ll;.     .,:lllc;.   .'..'.      ,clc'
  .kMMM0'
  .xNXk;
   ...
"""

# Coordinates (start_col, end_col) for the yellow chevron on each line
YELLOW_ZONES = {
    2: (47, 53),
    3: (48, 55),
    4: (49, 56),
    5: (51, 57),
    6: (51, 57),
    7: (51, 58),
    8: (50, 57),
    9: (49, 56),
    10: (48, 55),
    11: (47, 53),
}


def print_plex_logo_ascii():
    lines = PLEX_LOGO_ASCII.strip("\n").splitlines()
    for i, line in enumerate(lines):
        if i in YELLOW_ZONES:
            start, end = YELLOW_ZONES[i]
            if len(line) >= end:
                print(
                    Fore.WHITE
                    + line[:start]
                    + PLEX_YELLOW
                    + line[start:end]
                    + Fore.WHITE
                    + line[end:]
                    + Style.RESET_ALL
                )
            else:
                print(Fore.WHITE + line + Style.RESET_ALL)
        else:
            print(Fore.WHITE + line + Style.RESET_ALL)
