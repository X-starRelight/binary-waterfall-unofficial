from collections.abc import Iterable
import os
from itertools import zip_longest


def make_file_path(filename: str):
    file_path, file_title = os.path.split(filename) # pyright: ignore[reportUnusedVariable]
    os.makedirs(file_path, exist_ok=True)


def grouper(iterable: Iterable[int], n: int, fillvalue: int | None=None) -> Iterable[tuple[int, ...]]:
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue) # pyright: ignore[reportReturnType]
