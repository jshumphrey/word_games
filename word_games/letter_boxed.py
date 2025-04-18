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

    def can_follow(self, chain: WordChain) -> bool:
        """Whether or not the LetterBoxedWord can be appended to the provided WordChain."""
        return chain.words == [] or self.first_letter == chain.last_letter


class LetterBoxedWordList(word_games.WordList[LetterBoxedWord]):
    """A WordList specifically tailored to LetterBoxedWords."""

    @functools.cached_property
    def words_by_first_letter(self) -> dict[Letter, LetterBoxedWordList]:
        """A dict that organizes the words in the WordList by their first letter.

        Caching this dict allows us to avoid sweeping the entire WordList each time we want to find the list
        of words that begin with a particular letter.
        """
        output_dict: dict[Letter, LetterBoxedWordList] = collections.defaultdict(LetterBoxedWordList)
        for word in self:
            output_dict[word.first_letter].append(word)

        return output_dict

    @property
    def word_factory(self) -> Callable[[str], LetterBoxedWord]:
        """Implement word_factory for LetterBoxedWordList."""
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



class WordChain(LetterBoxedWordList):
    """A LetterBoxedWordList whose words form a Letter Boxed solution, where each successive word in
    the WordChain must begin with the same letter as the last letter of the preceding word."""

    letter_box: LetterBox

    def __init__(self, words, letter_box: LetterBox):
        super().__init__(words)
        self.letter_box = letter_box

    def __add__(self, other: object) -> Self:
        if isinstance(other, LetterBoxedWord):
            return type(self)(self.words + [other], self.letter_box)
        return NotImplemented

    def __str__(self) -> str:
        return " - ".join(map(str, self))

    @functools.cached_property
    def first_letter(self) -> Letter:
        """The first letter of the overall WordChain."""
        return self.words[0].first_letter

    @functools.cached_property
    def last_letter(self) -> Letter:
        """The last letter of the overall WordChain."""
        return self.words[-1].last_letter

    @functools.cached_property
    def remaining_letters(self) -> frozenset[Letter]:
        """The set of letters that are still needed to solve the WordChain's LetterBox."""
        return self.letter_box.letters - self.used_letters

    @functools.cached_property
    def used_letters(self) -> set[Letter]:
        """The total set of all letters used across all of the WordChain's words."""
        return functools.reduce(lambda a, b: a | b, [w.letters for w in self.words])

    def get_best_next_words(self, all_words: LetterBoxedWordList) -> LetterBoxedWordList:
        """Given a LetterBoxedWordList of all words, return the list of words that could possibly be
        appended to the WordChain, sorted by how many remaining letters there would be afterwards."""
        return all_words.filter(lambda w: w.can_follow(self)).sort(self.num_remaining_letters_after_word)

    def num_remaining_letters_after_word(self, word: LetterBoxedWord) -> int:
        """Given a LetterBoxedWord, return the number of remaining letters IF the word was added."""
        return len(self.remaining_letters - word.letters)


def parse_arguments() -> argparse.Namespace:
    """Parse the arguments provided to the script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("letter_box")
    return parser.parse_args()


def main():
    """Execute top-level functionality."""
    args = parse_arguments()
    letter_box = LetterBox.from_str(args.letter_box)
    print(letter_box.solve())


if __name__ == "__main__":
    main()
