

from __future__ import annotations

import argparse
import csv
import typing

from collections_extended import frozenbag
from tqdm import tqdm

import word_games
from word_games import crossword

DEFAULT_NUM_TRIALS = 10000


def parse_arguments():
    """Parse the arguments to the script and return the corresponding Namespace."""
    class CustomArgparseNamespace(argparse.Namespace):
        game: word_games.CrosswordGame
        lexicon: word_games.Lexicon
        word_length: int
        num_trials: int
        write_results: bool

    parser = argparse.ArgumentParser()
    parser.add_argument("game", choices = typing.get_args(word_games.CrosswordGame), type = str.capitalize)
    parser.add_argument("lexicon", choices = typing.get_args(word_games.Lexicon), type = str.upper)
    parser.add_argument("word_length", type = int)
    parser.add_argument("-n", "--num-trials", type = int, default = DEFAULT_NUM_TRIALS)
    parser.add_argument("-w", "--write-results", action = "store_true")

    return parser.parse_args(namespace = CustomArgparseNamespace())


def odds_of_word_given_letter(
    letter: word_games.Letter,
    tile_pool: crossword.TileFrequencies,
    valid_anagrams: dict[frozenbag, frozenset],
    num_trials: int
) -> float:
    """Return the odds of drawing a valid word, given the provided starting letter, by simulating many draws.

    Args:
        letter: The single given letter that each draw begins with.
        tile_pool: A TileFrequencies describing the number of tiles in the pool.
        valid_anagrams: A set of frozenbags of anagrams of valid words.
        num_trials: The number of draws to simulate.

    Returns:
        A float between 0 and 1 representing the percentage of the time a random draw yielded a valid word.
    """
    word_length = len(next(iter(valid_anagrams)))  # Every word has the same length, so this is safe
    pool_minus_letter = tile_pool - letter  # We took a letter out of the pool, so we need to reflect that

    successes: int = 0
    for _ in tqdm(range(num_trials), desc = f"Calculating odds for {letter}", leave = False):
        rack = pool_minus_letter.draw(word_length - 1) + letter

        if rack in valid_anagrams:
            successes += 1

        elif "?" in rack:
            nonblank_rack = frozenbag(letter for letter in rack if letter != "?")
            nonblank_letters = set(nonblank_rack)
            if any(
                nonblank_letters.issubset(letters)
                and nonblank_rack.issubset(anagram)
                for anagram, letters in valid_anagrams.items()
            ):
                successes += 1

        # We don't need an `else`; we just... don't increment successes, in that case.

    return successes / num_trials


def main():
    """Execute top-level functionality."""
    args = parse_arguments()

    tile_frequencies = crossword.TileFrequencies.from_data_file(args.game)
    word_list = word_games.GenericWordList.from_file(word_games.LEXICON_FILEPATHS[args.lexicon])
    word_list = word_list.filter(lambda word: len(word) == args.word_length)

    # "Index" the word list by its anagram - which is to say, which tiles are in each word, and how many.
    # We can then check whether a rack of letters forms a valid word simply by a O(1) set lookup, to see if
    # the rack's anagram is within the set of valid anagrams. There's separate logic for handling blanks;
    # to help speed that up, also precompile and cache the (basic) set for each word.
    valid_anagrams = {frozenbag(word): frozenset(word) for word in word_list}

    probabilities: dict[word_games.Letter, float] = {
        letter: odds_of_word_given_letter(letter, tile_frequencies, valid_anagrams, args.num_trials)
        for letter in tqdm(tile_frequencies)
    }

    print(
        f"Odds of drawing a length-{args.word_length} word, "
        f"given one starting letter and drawing {args.word_length - 1} from the full pool."
    )
    for letter, probability in probabilities.items():
        print(f"Given one '{letter}': {probability:.2%}")

    if args.write_results is True:
        output_filename = f"{args.game}_{args.lexicon}_{args.word_length}_odds.csv"
        with open(output_filename, "w", encoding = "utf-8") as outfile:
            (writer := csv.writer(outfile)).writerow(["Starting Letter", "% Valid Word"])
            writer.writerows(probabilities.items())

if __name__ == "__main__":
    main()
