from pathlib import Path

this_file = Path(__file__)
source_dir = this_file.parent
root_dir = source_dir.parent
data_dir = root_dir / "tests/data"

example_c = data_dir / "example.c"
assert example_c.exists(), example_c
