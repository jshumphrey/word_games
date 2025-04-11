"""A script to help find optional solutions to the New York Times' "Letter Boxed" game."""
# pylint: disable = method-cache-max-size-none

from __future__ import annotations

import argparse
import collections
from collections.abc import Callable
import dataclasses
import functools
import itertools
import re
from typing import Self

import word_games
from word_games import Letter


MINIMUM_WORD_LENGTH = 3  # Letter Boxed enforces that all words must be at least 3 letters long


class LetterBoxedWord(word_games.Word):
    """A word_games.Word, with custom functionality for use in Letter Boxed."""

    @functools.cached_property
    def first_letter(self) -> Letter:
        """The first letter of the LetterBoxedWord."""
        return self.full_word[0]

    @functools.cached_property
    def last_letter(self) -> Letter:
        """The last letter of the LetterBoxedWord."""
        return self.full_word[-1]


class LetterBoxedWordList(word_games.WordList[LetterBoxedWord]):
    """A WordList specifically tailored to LetterBoxedWords."""

    @functools.cached_property
    def words_by_first_letter(self) -> dict[Letter, list[LetterBoxedWord]]:
        """A dict that organizes the words in the WordList by their first letter.

        Caching this dict allows us to avoid sweeping the entire WordList each time we want to find the list
        of words that begin with a particular letter.
        """
        output_dict = collections.defaultdict(list)
        for word in self:
            output_dict[word.first_letter].append(word)

        return output_dict

    @property
    def word_factory(self) -> Callable[[str], LetterBoxedWord]:
        """Implement word_factory for LetterBoxedWord."""
        return LetterBoxedWord


@dataclasses.dataclass(frozen = True)
class LetterBox:
    """The "letter box" that defines a Letter Boxed puzzle."""

    sides: frozenset[frozenset[Letter]]

    def __contains__(self, letter: Letter) -> bool:
        return letter in self.letters

    def __str__(self) -> str:
        return f"LetterBox with sides of {', '.join(''.join(side) for side in self.sides)}"

    @functools.cached_property
    def letters(self) -> frozenset[Letter]:
        """The set of all letters across all sides of the LetterBox."""
        return functools.reduce(lambda a, b: a | b, self.sides)

    @classmethod
    def from_str(cls: type[Self], input_str: str) -> Self:
        """Parse the provided input_str and return a LetterBox with the given sides."""

        letters_only = re.sub(r"[^a-z]", "", input_str.casefold())  # Delete everything except a-z

        if len(letters_only) != 12:
            raise ValueError(
                "LetterBoxed puzzles must use exactly twelve letters, but extracting the letters from "
                f"{input_str} yields {letters_only}, which has {len(letters_only)} letters!"
            )

        if dupes := {l for l in letters_only if letters_only.count(l) > 1}:
            raise ValueError(
                f"LetterBoxed puzzles cannot reuse letters, but these letters appear more than once: {dupes}!"
            )

        return cls(frozenset(frozenset(side) for side in itertools.batched(letters_only, 3)))

    @functools.cache
    def get_side_with_letter(self, letter: Letter) -> frozenset[Letter]:
        """Return the side of the LetterBox that contains the provided letter."""
        for side in self.sides:
            if letter in side:
                return side

        raise ValueError(f"Could not find '{letter}' on any of the LetterBox's sides ({self.sides})!")

    def is_word_accepted(self, word: LetterBoxedWord | str) -> bool:
        """Examine an input word and determine whether it is valid for use in the LetterBox."""

        word = word if isinstance(word, LetterBoxedWord) else LetterBoxedWord(word)

        if not word.letters <= self.letters:
            return False  # If the word contains letters that aren't in the LetterBox, it can't be valid

        for current_letter, next_letter in itertools.pairwise(word.full_word):
            if current_letter == next_letter:
                return False  # Shortcut in case the word has double letters; such words are NEVER valid
            if next_letter in self.get_side_with_letter(current_letter):
                return False  # If the next letter is on the same side, it's not valid

        return True


def parse_arguments() -> argparse.Namespace:
    """Parse the arguments provided to the script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("letter_box")
    return parser.parse_args()


def main():
    """Execute top-level functionality."""
    args = parse_arguments()
    letter_box = LetterBox.from_str(args.letter_box)
    word_list = (
        LetterBoxedWordList.from_file(word_games.ALL_WORDS_FILEPATH)
        .filter(letter_box.is_word_accepted)
        .filter(lambda w: len(w) >= MINIMUM_WORD_LENGTH)
    )
    breakpoint()  # pylint: disable = forgotten-debug-statement


if __name__ == "__main__":
    main()
