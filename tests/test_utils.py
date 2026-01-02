import sys
import os

# Add parent directory to path so we can import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolkit.utils import extract_title_and_year, normalize_title, is_escape


def test_extract_title_and_year():
    assert extract_title_and_year("The Matrix (1999)") == ("The Matrix", 1999)
    assert extract_title_and_year("Avatar") == ("Avatar", None)
    assert extract_title_and_year("Title (With Parentheses) (2023)") == (
        "Title (With Parentheses)",
        2023,
    )
    assert extract_title_and_year("   Spaced Out (2001)   ") == ("Spaced Out", 2001)


def test_normalize_title():
    assert normalize_title("The Matrix!") == "the matrix"
    assert normalize_title("Spider-Man: No Way Home") == "spiderman no way home"
    assert normalize_title("  Messy   Title  ") == "messy title"


def test_is_escape():
    assert is_escape("ESC") is True
    assert is_escape("esc") is True
    assert is_escape("ESCAPE") is True
    assert is_escape("\x1b") is True
    assert is_escape("no") is False
    assert is_escape("") is False
