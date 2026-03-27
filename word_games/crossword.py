"""Classes and functions pertaining to crossword-style games, such as Scrabble, UpWords, and Crossplay."""

import collections
from collections.abc import Iterable, Generator
import dataclasses
import functools
import random
import tomllib
from typing import Self

from collections_extended import frozenbag

import word_games
from word_games import Letter


@dataclasses.dataclass(frozen = True)
class TileFrequencies:
    """The frequency of the pool of tiles in a particular crossword game."""
    frequencies: collections.Counter[Letter]

    def __getitem__(self, key: Letter) -> int:
        return self.frequencies[key]

    def __iter__(self) -> Generator[Letter]:
        yield from self.frequencies

    def __len__(self) -> int:
        return len(self.frequencies)

    def __sub__(self, other: TileFrequencies | Iterable[Letter]) -> TileFrequencies:
        output_freqs = collections.Counter(self.frequencies)  # Create a new one so we don't mutate ours
        if isinstance(other, TileFrequencies):
            output_freqs.subtract(other.frequencies)
        else:
            output_freqs.subtract(other)
        return TileFrequencies(output_freqs)

    @classmethod
    def from_data_file(cls: type[Self], game_name: word_games.CrosswordGame) -> Self:
        """Read the tile frequencies from the data file of frequencies, for the provided game."""
        with open(word_games.TILE_DATA_FILEPATH, "rb") as infile:
            game_data = tomllib.load(infile)[game_name]
            return cls(collections.Counter({letter: data["count"] for letter, data in game_data.items()}))

    @functools.cached_property
    def tile_pool(self) -> list[Letter]:
        """The list of all tiles in the pool of tiles with the specified tile frequences.
        Letters appear more than once in the list if their frequency is greater than 1."""
        return list(self.frequencies.elements())

    def draw(self, num_tiles: int) -> frozenbag:
        """Draw ``num_tiles`` from the pool, WITHOUT replacement. The pool is NOT changed."""
        return frozenbag(random.sample(self.tile_pool, num_tiles))
