import sys
import select
import os

try:
    import tty
    import termios
except ImportError:
    tty = None
    termios = None


class InputHandler:
    @staticmethod
    def _get_char():
        """Reads a single character or escape sequence from stdin."""
        if not tty:
            # Windows fallback
            if os.name == "nt":
                import msvcrt

                ch = msvcrt.getch()
                # Handle special keys (0x00 or 0xe0 followed by code)
                if ch in (b"\x00", b"\xe0"):
                    ch = ch + msvcrt.getch()
                return ch.decode("utf-8", errors="ignore")
            return sys.stdin.read(1)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # Use os.read to bypass Python's buffering, which causes select() to fail
            # when data is already buffered in Python but not in the OS pipe.
            b = os.read(fd, 1)
            if not b:
                return ""

            if b == b"\x1b":
                # Check for escape sequence (Arrow keys, etc.)
                if select.select([fd], [], [], 0.05)[0]:
                    b += os.read(fd, 1)
                    if select.select([fd], [], [], 0.05)[0]:
                        b += os.read(fd, 1)
                return b.decode("utf-8", errors="ignore")

            # Handle UTF-8 multi-byte characters
            first = ord(b)
            to_read = 0
            if (first & 0xE0) == 0xC0:
                to_read = 1
            elif (first & 0xF0) == 0xE0:
                to_read = 2
            elif (first & 0xF8) == 0xF0:
                to_read = 3

            while to_read > 0:
                if select.select([fd], [], [], 0.05)[0]:
                    b += os.read(fd, 1)
                    to_read -= 1
                else:
                    break

            return b.decode("utf-8", errors="ignore")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    @staticmethod
    def read_line(prompt=""):
        """
        Reads a line of input, supporting:
        - Typing text
        - Left/Right Arrow keys for navigation
        - Backspace
        - Esc to cancel (returns None)
        - Enter to confirm
        """
        sys.stdout.write(prompt)
        sys.stdout.flush()

        buffer = []
        cursor_pos = 0

        while True:
            key = InputHandler._get_char()

            # Handle ESC (Standalone)
            if key == "\x1b":
                sys.stdout.write("\n")
                return None

            # Handle Enter
            if key in ("\r", "\n"):
                sys.stdout.write("\n")
                return "".join(buffer)

            # Handle Backspace (127 is DEL on Mac/Linux, 8 is BS)
            if key in ("\x7f", "\x08"):
                if cursor_pos > 0:
                    buffer.pop(cursor_pos - 1)
                    cursor_pos -= 1
                    # Move back, clear to end of line, print rest
                    sys.stdout.write("\b\033[K" + "".join(buffer[cursor_pos:]))
                    # Move cursor back to correct position if needed
                    if len(buffer) > cursor_pos:
                        sys.stdout.write(f"\033[{len(buffer) - cursor_pos}D")
                    sys.stdout.flush()
                continue

            # Handle Arrow Keys (Escape Sequences)
            if key.startswith("\x1b["):
                seq = key[2:]
                if seq == "D":  # Left Arrow
                    if cursor_pos > 0:
                        cursor_pos -= 1
                        sys.stdout.write("\033[D")
                        sys.stdout.flush()
                elif seq == "C":  # Right Arrow
                    if cursor_pos < len(buffer):
                        cursor_pos += 1
                        sys.stdout.write("\033[C")
                        sys.stdout.flush()
                # Ignore Up/Down (A/B)
                continue

            # Handle Regular Printable Characters
            if len(key) == 1 and key.isprintable():
                buffer.insert(cursor_pos, key)
                cursor_pos += 1
                sys.stdout.write(key + "".join(buffer[cursor_pos:]))
                # Move cursor back if we inserted in middle
                if len(buffer) > cursor_pos:
                    sys.stdout.write(f"\033[{len(buffer) - cursor_pos}D")
                sys.stdout.flush()

    @staticmethod
    def read_menu_choice(prompt, valid_choices):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        while True:
            key = InputHandler._get_char()
            if key == "\x1b":
                sys.stdout.write("\n")
                return "ESC"
            if key in valid_choices:
                sys.stdout.write(key + "\n")
                return key
