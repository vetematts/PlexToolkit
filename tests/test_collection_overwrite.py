from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from toolkit import ops


@pytest.fixture
def overwrite_flow(monkeypatch):
    collection = Mock(title="Example", smart=False)
    library = Mock()
    library.search.return_value = [collection]
    manager = Mock()
    manager.get_movie_library.return_value = library
    monkeypatch.setattr(ops, "get_plex_manager", Mock(return_value=manager))
    choice = Mock(return_value="o")
    confirmation = Mock(return_value="y")
    monkeypatch.setattr(ops, "read_menu_choice", choice)
    monkeypatch.setattr(ops, "read_line", confirmation)
    movies = [SimpleNamespace(title="The Matrix", year=1999, ratingKey="42")]
    pause = Mock()

    def run():
        ops.process_and_create_collection(
            "Example",
            movies,
            {"PLEX_TOKEN": "test-token", "PLEX_URL": "http://example.invalid"},
            pause,
            is_pre_matched=True,
        )

    return SimpleNamespace(
        collection=collection,
        library=library,
        choice=choice,
        confirmation=confirmation,
        movies=movies,
        run=run,
    )


@pytest.mark.parametrize("answer", [None, "", "n", "N", "   ", "no"])
def test_declining_overwrite_leaves_collection_untouched(overwrite_flow, answer):
    overwrite_flow.confirmation.return_value = answer

    overwrite_flow.run()

    overwrite_flow.confirmation.assert_called_once()
    overwrite_flow.collection.delete.assert_not_called()
    overwrite_flow.library.createCollection.assert_not_called()


@pytest.mark.parametrize("answer", ["y", " Y "])
def test_confirmed_overwrite_replaces_collection_once(overwrite_flow, answer):
    overwrite_flow.confirmation.return_value = answer

    overwrite_flow.run()

    overwrite_flow.confirmation.assert_called_once()
    overwrite_flow.collection.delete.assert_called_once_with()
    overwrite_flow.library.createCollection.assert_called_once_with(
        "Example", items=overwrite_flow.movies
    )


def test_overwrite_confirms_before_deletion_and_creation(overwrite_flow):
    events = []

    def confirm(prompt):
        overwrite_flow.collection.delete.assert_not_called()
        overwrite_flow.library.createCollection.assert_not_called()
        assert "Example" in prompt
        events.append("confirm")
        return "y"

    overwrite_flow.confirmation.side_effect = confirm
    overwrite_flow.collection.delete.side_effect = lambda: events.append("delete")
    overwrite_flow.library.createCollection.side_effect = (
        lambda *args, **kwargs: events.append("create")
    )

    overwrite_flow.run()

    assert events == ["confirm", "delete", "create"]


def test_deletion_failure_stops_replacement(overwrite_flow, capsys):
    overwrite_flow.collection.delete.side_effect = ConnectionError("Server unavailable")

    overwrite_flow.run()

    overwrite_flow.library.createCollection.assert_not_called()
    output = capsys.readouterr().out
    assert "Failed to delete collection" in output
    assert "Server unavailable" in output


@pytest.mark.parametrize("choice", ["c", "C", "ESC"])
def test_cancelling_collection_menu_does_not_prompt_or_write(overwrite_flow, choice):
    overwrite_flow.choice.return_value = choice

    overwrite_flow.run()

    overwrite_flow.confirmation.assert_not_called()
    overwrite_flow.collection.delete.assert_not_called()
    overwrite_flow.library.createCollection.assert_not_called()


@pytest.mark.parametrize("answer", ["n", "y"])
def test_new_collection_keeps_its_confirmation(overwrite_flow, answer):
    overwrite_flow.library.search.return_value = []
    overwrite_flow.confirmation.return_value = answer

    overwrite_flow.run()

    overwrite_flow.choice.assert_not_called()
    overwrite_flow.confirmation.assert_called_once()
    overwrite_flow.collection.delete.assert_not_called()
    if answer == "y":
        overwrite_flow.library.createCollection.assert_called_once_with(
            "Example", items=overwrite_flow.movies
        )
    else:
        overwrite_flow.library.createCollection.assert_not_called()


def test_append_adds_items_without_deleting_or_recreating(overwrite_flow):
    overwrite_flow.choice.return_value = "a"
    overwrite_flow.collection.items.return_value = []

    overwrite_flow.run()

    overwrite_flow.collection.addItems.assert_called_once_with(overwrite_flow.movies)
    overwrite_flow.confirmation.assert_not_called()
    overwrite_flow.collection.delete.assert_not_called()
    overwrite_flow.library.createCollection.assert_not_called()
