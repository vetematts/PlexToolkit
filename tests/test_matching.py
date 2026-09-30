from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from toolkit import ops


def movie(title, year=None):
    return SimpleNamespace(title=title, year=year)


@pytest.fixture
def choose_match(monkeypatch):
    chooser = Mock(return_value=1)
    monkeypatch.setattr(ops, "read_index_or_skip", chooser)
    return chooser


@pytest.mark.parametrize(
    ("query", "candidates", "expected_index"),
    [
        ("The Matrix (1999)", [movie("The Matrix", 1999)], 0),
        ("Avatar", [movie("Avatar", 2009)], 0),
        ("The Matrix! (1999)", [movie("The Matrix", 1999)], 0),
        ("The Matrix (1999)", [movie("The Matrix", 2000)], 0),
        ("Alien", [movie("Alien 3", 1992), movie("Alien", 1979)], 1),
        ("The Thing (1982)", [movie("The Thing", 2011), movie("The Thing", 1982)], 1),
        ("Example (2000)", [movie("Example", 1999), movie("Example", 2000)], 1),
    ],
)
def test_unique_exact_match_is_automatic(query, candidates, expected_index, choose_match):
    assert ops.pick_plex_match(query, candidates) is candidates[expected_index]
    choose_match.assert_not_called()


@pytest.mark.parametrize(
    ("query", "candidates"),
    [
        ("Alien", [movie("Alien 3", 1992)]),
        ("The Thing", [movie("The Thing", 2011), movie("The Thing", 1982)]),
        ("The Matrix (1999)", [movie("The Matrx", 1999)]),
        ("The Matrix (1999)", [movie("The Matrix")]),
        ("The Matrix (1999)", [movie("The Matrix", 1999), movie("The Matrix", 1999)]),
    ],
)
def test_uncertain_matches_require_selection(query, candidates, choose_match):
    assert ops.pick_plex_match(query, candidates) is candidates[0]
    choose_match.assert_called_once()
    assert choose_match.call_args.args[0] == len(candidates)


def test_user_can_select_a_remake(choose_match):
    candidates = [movie("The Thing", 2011), movie("The Thing", 1982)]
    choose_match.return_value = 2

    assert ops.pick_plex_match("The Thing", candidates) is candidates[1]


def test_user_can_skip_a_sequel(choose_match):
    choose_match.return_value = None

    assert ops.pick_plex_match("Alien", [movie("Alien 3", 1992)]) is None
    choose_match.assert_called_once()


@pytest.mark.parametrize(
    ("query", "candidates"),
    [
        ("The Thing (1982)", [movie("The Thing", 2011)]),
        ("Alien", [movie("Avatar", 2009)]),
        ("Alien", []),
        ("!!!", [movie("!!!", 2000)]),
    ],
)
def test_incompatible_or_empty_matches_are_rejected(query, candidates, choose_match):
    assert ops.pick_plex_match(query, candidates) is None
    choose_match.assert_not_called()
