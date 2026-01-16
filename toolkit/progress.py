"""
Simple progress bar utility for displaying progress of long-running operations.
"""

import sys
from typing import Optional


class ProgressBar:
    """A simple progress bar that updates in place."""

    def __init__(
        self,
        total: int,
        prefix: str = "Progress",
        suffix: str = "Complete",
        length: int = 50,
        show_percentage: bool = True,
        show_count: bool = True,
    ):
        """
        Initialize a progress bar.

        Args:
            total: Total number of items to process
            prefix: Text to display before the progress bar
            suffix: Text to display after the progress bar
            length: Length of the progress bar in characters
            show_percentage: Whether to show percentage
            show_count: Whether to show current/total count
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.show_percentage = show_percentage
        self.show_count = show_count
        self.current = 0
        self._printed = False

    def update(self, n: int = 1, custom_message: Optional[str] = None):
        """
        Update the progress bar by n items.

        Args:
            n: Number of items to increment by (default: 1)
            custom_message: Optional custom message to display instead of suffix
        """
        self.current = min(self.current + n, self.total)
        self._display(custom_message)

    def set(self, value: int, custom_message: Optional[str] = None):
        """
        Set the progress bar to a specific value.

        Args:
            value: Current progress value
            custom_message: Optional custom message to display instead of suffix
        """
        self.current = min(max(value, 0), self.total)
        self._display(custom_message)

    def _display(self, custom_message: Optional[str] = None):
        """Display the progress bar."""
        if self.total == 0:
            return

        percent = 100 * (self.current / float(self.total))
        filled_length = int(self.length * self.current // self.total)
        bar = "█" * filled_length + "░" * (self.length - filled_length)

        # Build the display string
        parts = [self.prefix]
        if self.show_count:
            parts.append(f"[{self.current}/{self.total}]")
        parts.append(f"|{bar}|")
        if self.show_percentage:
            parts.append(f"{percent:.1f}%")
        parts.append(custom_message if custom_message else self.suffix)

        # Use carriage return to overwrite the line
        sys.stdout.write("\r" + " ".join(parts))
        sys.stdout.flush()
        self._printed = True

    def finish(self, message: Optional[str] = None):
        """
        Finish the progress bar and move to a new line.

        Args:
            message: Optional final message to display
        """
        if self._printed:
            # Clear the line and move to next
            sys.stdout.write("\r" + " " * (self.length + 50) + "\r")
            if message:
                print(message)
            else:
                print(f"{self.prefix} {self.suffix}: {self.current}/{self.total}")
            sys.stdout.flush()
        self._printed = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures progress bar is finished."""
        self.finish()


def create_progress_bar(
    total: int,
    prefix: str = "Progress",
    suffix: str = "Complete",
    length: int = 50,
) -> ProgressBar:
    """
    Convenience function to create a progress bar.

    Args:
        total: Total number of items to process
        prefix: Text to display before the progress bar
        suffix: Text to display after the progress bar
        length: Length of the progress bar in characters

    Returns:
        ProgressBar instance
    """
    return ProgressBar(total, prefix, suffix, length)
