# CFG Test Expectation Generator

This utility generates DOT format expectations for Control Flow Graph (CFG) test files.

## Usage

### Generate expectations for all test files:
```bash
python test/parse_trees/generate_test_expectations.py
```

### Generate expectations for specific files:
```bash
python test/parse_trees/generate_test_expectations.py test/parse_trees/c/basic.test.toml
```

### Overwrite existing expectations:
```bash
python test/parse_trees/generate_test_expectations.py --overwrite
```

### Process files in a specific directory:
```bash
python test/parse_trees/generate_test_expectations.py --directory path/to/test/files
```

## File Format

The utility reads `.test.toml` files with the following structure:

```toml
code="""\
int factorial() {
    int a = 1;
    int b = 10;
    for (int i = 2; i <= b; i ++) {
        a *= i;
    }
    return a;
}
"""
```

And generates the `expect.graph` field with DOT format:

```toml
[expect]
graph="""\
digraph CFG {
    node_0 [type="ENTRY", label="factorial"]
    node_1 [type="EXIT", label="factorial"]
    node_2 [type="STATEMENT", label="int a = 1;"]
    # ... more nodes ...
    
    node_0 -> node_2
    node_2 -> node_3
    # ... more edges ...
}
"""
```

## Output

The utility generates a complete DOT format graph that includes:
- All CFG nodes with their types and labels
- All edges between nodes with optional labels (e.g., "true", "false")
- Proper DOT format syntax for visualization with Graphviz

## Workflow

1. Write your test code in a `.test.toml` file
2. Run the utility to generate expectations
3. Review the generated DOT graph (optionally visualize with Graphviz)
4. Run tests to validate CFG generation
