"""
MenuBuilder class for creating consistent, styled menus throughout the application.
"""

import sys
import contextlib
from colorama import Fore
from typing import Optional, Set

from toolkit.input_handler import InputHandler


class MenuBuilder:
    """Builds and displays consistent menus with styling, emojis, and colors."""

    def __init__(
        self,
        title: Optional[str] = None,
        title_emoji: Optional[str] = None,
        title_color: str = Fore.YELLOW,
        footer: Optional[str] = None,
        footer_color: str = Fore.LIGHTBLACK_EX,
    ):
        """
        Initialize a MenuBuilder.

        Args:
            title: Menu title text
            title_emoji: Emoji to display before the title
            title_color: Colorama color for the title
            footer: Footer text to display after options
            footer_color: Colorama color for the footer
        """
        self.title = title
        self.title_emoji = title_emoji
        self.title_color = title_color
        self.footer = footer
        self.footer_color = footer_color
        self.options = []

    def add_option(
        self,
        number: str,
        text: str,
        emoji: Optional[str] = None,
        color: str = Fore.GREEN,
        enabled: bool = True,
    ):
        """
        Add an option to the menu.

        Args:
            number: Option number/key (e.g., "1", "2", "a", "b")
            text: Option description text
            emoji: Optional emoji to display before the text
            color: Colorama color for the option number
            enabled: Whether this option is enabled (disabled options shown in gray)
        """
        self.options.append(
            {
                "number": number,
                "text": text,
                "emoji": emoji,
                "color": color,
                "enabled": enabled,
            }
        )
        return self  # Allow method chaining

    def display(self):
        """Display the menu with all options."""
        # Display title
        if self.title:
            title_text = ""
            if self.title_emoji:
                title_text += f"{self.title_emoji} "
            title_text += f"{self.title}"
            print(self.title_color + title_text + "\n")

        # Display options
        for option in self.options:
            number_color = option["color"] if option["enabled"] else Fore.LIGHTBLACK_EX
            text_color = Fore.RESET if option["enabled"] else Fore.LIGHTBLACK_EX

            emoji_part = f"{option['emoji']} " if option["emoji"] else ""
            print(
                number_color
                + f"{option['number']}."
                + text_color
                + f" {emoji_part}{option['text']}\n"
            )

        # Display footer
        if self.footer:
            print(self.footer_color + self.footer + "\n")

    def get_valid_choices(self) -> Set[str]:
        """Return a set of valid choice keys (only enabled options)."""
        return {opt["number"] for opt in self.options if opt["enabled"]}

    def get_all_choices(self) -> Set[str]:
        """Return a set of all choice keys (including disabled options)."""
        return {opt["number"] for opt in self.options}

    def display_interactive(self) -> str:
        """
        Display menu with arrow key navigation support.
        Returns the selected option number, or "ESC" if cancelled.

        Features:
        - Up/Down arrows to navigate
        - Enter to select highlighted option
        - Number/letter to jump directly to option
        - Esc to cancel
        """
        # Filter to only enabled options for navigation
        enabled_options = [opt for opt in self.options if opt["enabled"]]
        if not enabled_options:
            return "ESC"

        selected_index = 0

        def _render_menu():
            """Render the menu with current selection highlighted."""
            # Display title
            if self.title:
                title_text = ""
                if self.title_emoji:
                    title_text += f"{self.title_emoji} "
                title_text += f"{self.title}"
                print(self.title_color + title_text + "\n")

            # Save cursor position at start of menu options (for redraws)
            sys.stdout.write("\033[s")  # Save cursor position
            sys.stdout.flush()

            # Display options with highlighting
            enabled_idx = 0
            for option in self.options:
                if not option["enabled"]:
                    # Disabled option - show in gray
                    number_color = Fore.LIGHTBLACK_EX
                    text_color = Fore.LIGHTBLACK_EX
                    prefix = "  "
                elif enabled_idx == selected_index:
                    # Selected option - highlight with arrow
                    number_color = Fore.CYAN + "\033[1m"  # Bright cyan
                    text_color = Fore.CYAN + "\033[1m"
                    prefix = "▶ "
                else:
                    # Normal enabled option
                    number_color = option["color"]
                    text_color = Fore.RESET
                    prefix = "  "

                emoji_part = f"{option['emoji']} " if option["emoji"] else ""
                print(
                    prefix + number_color + f"{option['number']}."
                    + text_color + f" {emoji_part}{option['text']}"
                    + "\033[0m\n"  # Reset colors
                )

                if option["enabled"]:
                    enabled_idx += 1

            # Display footer
            if self.footer:
                print(self.footer_color + self.footer + "\n")

            # Show current selection indicator with full styling
            selected_option = enabled_options[selected_index]
            selected_emoji = selected_option.get('emoji', '')
            emoji_part = f"{selected_emoji} " if selected_emoji else ""
            print(f"{Fore.CYAN}\033[1m▶ Selected: {selected_option['number']}. {emoji_part}{selected_option['text']}\033[0m{Fore.RESET}")
            print()  # Extra blank line for spacing

            sys.stdout.flush()

        # Initial render
        _render_menu()

        # Interactive selection loop
        with InputHandler._terminal_mode():
            while True:
                key = InputHandler._read_char_raw()

                # Handle Ctrl+C
                if key == "\x03":
                    sys.stdout.write("\n")
                    return "ESC"

                # Handle arrow keys (must check before standalone ESC)
                if key.startswith("\x1b["):
                    seq = key[2:]
                    if seq == "A":  # Up arrow
                        selected_index = (selected_index - 1) % len(enabled_options)
                        # Restore cursor to menu start, clear to end, redraw
                        sys.stdout.write("\033[u\033[J")  # Restore cursor, clear to end
                        sys.stdout.flush()
                        # Redraw options, footer, and indicator
                        enabled_idx = 0
                        for option in self.options:
                            if not option["enabled"]:
                                prefix = "  "
                                number_color = Fore.LIGHTBLACK_EX
                                text_color = Fore.LIGHTBLACK_EX
                            elif enabled_idx == selected_index:
                                prefix = "▶ "
                                number_color = Fore.CYAN + "\033[1m"
                                text_color = Fore.CYAN + "\033[1m"
                            else:
                                prefix = "  "
                                number_color = option["color"]
                                text_color = Fore.RESET

                            emoji_part = f"{option['emoji']} " if option["emoji"] else ""
                            print(prefix + number_color + f"{option['number']}." + text_color + f" {emoji_part}{option['text']}\033[0m\n")
                            if option["enabled"]:
                                enabled_idx += 1

                        if self.footer:
                            print(self.footer_color + self.footer + "\n")

                        selected_option = enabled_options[selected_index]
                        selected_emoji = selected_option.get('emoji', '')
                        emoji_part = f"{selected_emoji} " if selected_emoji else ""
                        print(f"{Fore.CYAN}\033[1m▶ Selected: {selected_option['number']}. {emoji_part}{selected_option['text']}\033[0m{Fore.RESET}\n")
                        sys.stdout.flush()
                    elif seq == "B":  # Down arrow
                        selected_index = (selected_index + 1) % len(enabled_options)
                        # Restore cursor to menu start, clear to end, redraw
                        sys.stdout.write("\033[u\033[J")  # Restore cursor, clear to end
                        sys.stdout.flush()
                        # Redraw options, footer, and indicator
                        enabled_idx = 0
                        for option in self.options:
                            if not option["enabled"]:
                                prefix = "  "
                                number_color = Fore.LIGHTBLACK_EX
                                text_color = Fore.LIGHTBLACK_EX
                            elif enabled_idx == selected_index:
                                prefix = "▶ "
                                number_color = Fore.CYAN + "\033[1m"
                                text_color = Fore.CYAN + "\033[1m"
                            else:
                                prefix = "  "
                                number_color = option["color"]
                                text_color = Fore.RESET

                            emoji_part = f"{option['emoji']} " if option["emoji"] else ""
                            print(prefix + number_color + f"{option['number']}." + text_color + f" {emoji_part}{option['text']}\033[0m\n")
                            if option["enabled"]:
                                enabled_idx += 1

                        if self.footer:
                            print(self.footer_color + self.footer + "\n")

                        selected_option = enabled_options[selected_index]
                        selected_emoji = selected_option.get('emoji', '')
                        emoji_part = f"{selected_emoji} " if selected_emoji else ""
                        print(f"{Fore.CYAN}\033[1m▶ Selected: {selected_option['number']}. {emoji_part}{selected_option['text']}\033[0m{Fore.RESET}\n")
                        sys.stdout.flush()
                    # Ignore left/right arrows (C/D)
                    continue

                # Handle standalone ESC (after checking for escape sequences)
                if key == "\x1b":
                    sys.stdout.write("\n")
                    return "ESC"

                # Handle Enter
                if key in ("\r", "\n"):
                    selected_option = enabled_options[selected_index]
                    sys.stdout.write("\n")
                    return selected_option["number"]

                # Handle direct number/letter selection
                valid_choices = self.get_valid_choices()
                if key in valid_choices:
                    sys.stdout.write(key + "\n")
                    return key
