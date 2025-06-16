# Example usage
import os

from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.visualization import visualize_cfg

if __name__ == "__main__":
    # Read example C code
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "test",
        "test.c",
    )
    print(f"Reading file: {test_file}")
    with open(test_file, "r") as f:
        c_code = f.read()
        print(f"Successfully read {len(c_code)} bytes")

    print("Running example...")

    builder = CFGBuilder("c")
    builder.setup_parser()  # You must implement this to load tree-sitter-c

    cfg = builder.build_cfg(c_code)
    print(f"CFG built for function: {cfg.function_name}")
    print(f"Number of nodes: {len(cfg.nodes)}")
    image_path = visualize_cfg(cfg, "c_cfg")
