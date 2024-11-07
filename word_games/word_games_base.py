"""Abstract base classes, constants, and other common functionality for the word-games scripts."""

from __future__ import annotations

import abc
import dataclasses
import functools
import pathlib

THIS_FILE_FILEPATH = pathlib.Path(__file__).resolve()
WORD_GAMES_CODE_DIRPATH = THIS_FILE_FILEPATH.parent
WORD_GAMES_TOPLEVEL_DIRPATH = WORD_GAMES_CODE_DIRPATH.parent
DATA_FILES_DIRPATH = WORD_GAMES_TOPLEVEL_DIRPATH / "data_files"
TESTS_DIRPATH = WORD_GAMES_TOPLEVEL_DIRPATH / "tests"

ALL_WORDS_FILEPATH = DATA_FILES_DIRPATH / "words_alpha.txt"
FIVE_LETTER_WORDS_FILEPATH = DATA_FILES_DIRPATH / "five_letter_words.txt"

Letter = str

@dataclasses.dataclass(eq = True, frozen = True, repr = True)
class Word(abc.ABC):
    """An abstract base class representing a single valid English word."""

    full_word: str

    def __contains__(self, letter: Letter) -> bool:
        return letter in self.letters

    def __str__(self) -> str:
        return self.full_word

    @functools.cached_property
    def letters(self) -> set[Letter]:
        """The set of the Word's unique letters."""
        return set(self.full_word)
