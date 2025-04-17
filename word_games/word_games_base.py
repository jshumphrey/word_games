"""Abstract base classes, constants, and other common functionality for the word-games scripts."""
# pylint: disable = W2604

from __future__ import annotations

import abc
from collections.abc import Callable, Iterable, Generator, Sequence
import dataclasses
import functools
import pathlib
import typing
from typing import Any, Self

THIS_FILE_FILEPATH = pathlib.Path(__file__).resolve()
WORD_GAMES_CODE_DIRPATH = THIS_FILE_FILEPATH.parent
WORD_GAMES_TOPLEVEL_DIRPATH = WORD_GAMES_CODE_DIRPATH.parent
DATA_FILES_DIRPATH = WORD_GAMES_TOPLEVEL_DIRPATH / "data_files"
TESTS_DIRPATH = WORD_GAMES_TOPLEVEL_DIRPATH / "tests"

ALL_WORDS_FILEPATH = DATA_FILES_DIRPATH / "words_alpha.txt"
FIVE_LETTER_WORDS_FILEPATH = DATA_FILES_DIRPATH / "five_letter_words.txt"

Letter = str
AnyWordList = typing.TypeVar("AnyWordList", bound = "WordList")

def read_words_from_file(filepath: str | pathlib.Path) -> Generator[str, None, None]:
    """Open the provided file of words and yield each line from it."""
    with open(filepath, "r", encoding = "utf-8") as infile:
        yield from (line.strip() for line in infile.readlines() if line)


@functools.total_ordering
@dataclasses.dataclass(eq = True, frozen = True, repr = True)
class Word(abc.ABC):
    """A single valid English word."""

    full_word: str

    def __contains__(self, letter: Letter) -> bool:
        return letter in self.letters

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and other.full_word == self.full_word

    def __len__(self) -> int:
        return len(self.full_word)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            raise TypeError
        return self.full_word < other.full_word

    def __str__(self) -> str:
        return self.full_word

    @functools.cached_property
    def letters(self) -> set[Letter]:
        """The set of the Word's unique letters."""
        return set(self.full_word)


class WordList[W: Word](abc.ABC):
    """A list of Word objects.

    Note that WordLists are named WordLISTS for a reason (as opposed to WordSets): they are ordered
    collections, and x in WordList is O(n)."""

    words: list[W]

    def __init__(self, words: Iterable[W | str]):
        self.words = [self.word_factory(w) if isinstance(w, str) else w for w in words]

    def __add__(self, other: WordList | W) -> Self:
        return (
            type(self)(self.words + [other]) if isinstance(other, Word)
            else type(self)(list(dict.fromkeys(self.words + other.words)))  # dict.fromkeys preserves order
        )

    def __radd__(self, other: AnyWordList) -> AnyWordList:
        return other.__add__(self)

    def __bool__(self) -> bool:
        return self.words != []

    def __contains__(self, word: Word) -> bool:
        return word in self.words

    def __eq__(self, other: object) -> bool:
        return (
            (isinstance(other, type(self)) and self.words == other.words)
            or (isinstance(other, Sequence) and self.words == other)
        )

    @typing.overload
    def __getitem__(self, key: slice) -> Self: ...

    @typing.overload
    def __getitem__(self, key: int) -> W: ...

    def __getitem__(self, key: int | slice):
        if isinstance(key, slice):
            return type(self)(self.words[key])

        if isinstance(key, int):
            return self.words[key]

        raise TypeError(
            f"{type(self).__name__}.__getitem__ expects keys that are integers or slices, "
            f"but got {type(key)} instead!"
        )

    def __iter__(self) -> Generator[W, None, None]:
        yield from self.words

    def __len__(self) -> int:
        return len(self.words)

    def __repr__(self) -> str:
        return object.__repr__(self)

    def __str__(self) -> str:
        return f"A {type(self).__name__} containing {len(self)} words"

    @property
    @abc.abstractmethod
    def word_factory(self) -> Callable[[str], W]:
        """The Callable used to create the appropriate subtype of Word objects from input strings."""
        raise NotImplementedError()

    @classmethod
    def from_file(cls: type[Self], filepath: str | pathlib.Path) -> Self:
        """Set up a WordList by reading Words from a text file."""
        return cls(read_words_from_file(filepath))

    def copy(self) -> Self:
        """Returns a deep copy of this WordList."""
        return type(self)(self.words[:])

    def filter(self, lambda_function: Callable[[W], bool]) -> Self:
        """Return a new WordList of the Words that return True when passed to the provided function."""
        return type(self)(filter(lambda_function, self.words))

    def sort(self, sort_function: Callable[[W], Any], reverse: bool = False) -> Self:
        """Sort self._words according to the provided callable."""
        self.words.sort(key = sort_function, reverse = reverse)
        return self
