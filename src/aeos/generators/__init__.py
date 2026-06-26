from collections.abc import Callable
from pathlib import Path

from aeos.generators.basic import generate as generate_basic

GeneratorFn = Callable[[Path, str], list[str]]

GENERATORS: dict[str, GeneratorFn] = {
    "basic": generate_basic,
}
