from colorama import Fore, Style
import base64
import os
import shutil

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


PLEX_MARK_ASCII = [
    "      >",
    "     >>",
    "    >>>",
    "     >>",
    "      >",
]


def print_plex_mark():
    # Use plain ASCII to be consistent across terminals/devices.
    for line in PLEX_MARK_ASCII:
        print(PLEX_YELLOW + line + Style.RESET_ALL)


def print_plex_wordmark(right_chevron: str = "❯"):
    """
    Text-only Plex-inspired wordmark.

    Terminals cannot render Plex's official font; this is a clean, consistent
    fallback that keeps the brand chevron visible using ANSI color + ASCII.
    """
    # "ple❯" with chevron in Plex yellow (chevron glyph is configurable)
    print(
        Fore.WHITE
        + Style.BRIGHT
        + "ple"
        + PLEX_YELLOW
        + right_chevron
        + Style.RESET_ALL
    )


def format_plex_wordmark_toolkit(
    right_chevron: str = "❯", left_chevron: str = "‹"
) -> str:
    """
    Return a styled "ple{right_chevron}{left_chevron} Toolkit" string for inline use.

    Notes:
    - `right_chevron` is the Plex chevron and is colored Plex yellow.
    - `left_chevron` is a visually smaller "less-than" (default: `‹`) and is dim.
    """
    return (
        Fore.WHITE
        + Style.BRIGHT
        + "ple"
        + PLEX_YELLOW
        + right_chevron
        + Fore.LIGHTBLACK_EX
        + left_chevron
        + Fore.LIGHTBLACK_EX
        + " Toolkit"
        + Style.RESET_ALL
    )


def print_divider(char: str = "─"):
    width = shutil.get_terminal_size(fallback=(80, 24)).columns
    line = char * max(10, min(width, 120))
    print(Fore.LIGHTBLACK_EX + line + Style.RESET_ALL)


def print_plex_branding(style: str = "auto"):
    """
    Print Plex branding in a terminal-friendly way.

    style:
      - "auto": choose based on terminal width
      - "full": big ASCII logo
      - "mark": small chevron mark only
    """
    if style not in ("auto", "full", "mark"):
        style = "auto"

    if style == "auto":
        # Prefer the modern compact header by default.
        style = "mark"

    if style == "full":
        print_plex_logo_ascii()
        return

    # Compact branding: wordmark + chevron mark
    right_chevron = os.getenv("PLEX_CHEVRON_RIGHT", "❯")
    print_plex_wordmark(right_chevron=right_chevron)
    print_plex_mark()


def _supports_iterm2_inline_images() -> bool:
    # iTerm2 sets TERM_PROGRAM=iTerm.app; VS Code/Terminal.app typically won't.
    return os.getenv("TERM_PROGRAM") == "iTerm.app"


def print_inline_image_iterm2(
    image_bytes: bytes,
    *,
    width: str = "240px",
    preserve_aspect_ratio: bool = True,
) -> bool:
    """
    Print an inline image in iTerm2 using OSC 1337.

    Returns True if printed, False if the terminal likely doesn't support it.
    """
    if not _supports_iterm2_inline_images():
        return False

    payload = base64.b64encode(image_bytes).decode("ascii")
    preserve = "1" if preserve_aspect_ratio else "0"
    # OSC 1337 inline image protocol:
    # ESC ] 1337 ; File=inline=1;width=...;preserveAspectRatio=1:BASE64 BEL
    seq = f"\033]1337;File=inline=1;width={width};preserveAspectRatio={preserve}:{payload}\a"
    print(seq)
    return True


def print_plex_logo_image(path: str) -> bool:
    """
    Attempt to print a real Plex logo image (PNG/JPG) inline.

    Controlled via environment:
      - PLEX_LOGO_IMAGE: path to image file
      - PLEX_LOGO_IMAGE_WIDTH: e.g. 180px, 240px, 30%
    """
    if not path:
        return False

    path = os.path.expanduser(path)
    if not os.path.exists(path) or not os.path.isfile(path):
        return False

    width = os.getenv("PLEX_LOGO_IMAGE_WIDTH", "240px")
    try:
        with open(path, "rb") as f:
            data = f.read()
        return print_inline_image_iterm2(data, width=width, preserve_aspect_ratio=True)
    except Exception:
        return False
