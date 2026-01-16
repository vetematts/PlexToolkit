"""
MenuBuilder class for creating consistent, styled menus throughout the application.
"""

from colorama import Fore
from typing import Optional, Set


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
