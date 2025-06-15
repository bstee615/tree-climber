# Example usage
from tree_sprawler.cfg.builder import CFGBuilder

if __name__ == "__main__":
    # Example C code
    c_code = """
    int foo() {
        return 42;
    }

    int test_cfg_constructs(int n) {
        int a = 0;
        int b = 1;
        int c = 3;
        int result = 1;
        
        /* Test conditional branching with
        true/false labels
        */
        if (n <= 1) {
            return 1;
        } else {
            c = 5;
        }

        if (a > 10) {
            foo();
        }
        
        c = 10;
        
        // Test for loop with true/false labels
        for (int i = 2; i <= n; i++) {
            result *= i;
        }
        
        // Test while loop
        while (n > 0) {
            n--;
        }
        
        // Test do-while loop
        do {
            result += 1;
            n -= 1;
        } while (n > 0);
        
        // Test switch statement
        switch (result % 3) {
            case 0:
                result *= 2;
                break;
            case 1:
                result += 10;
                // Fall through to case 2
            case 2:
                result -= 5;
                break;
            default:
                result = 0;
        }
        
        // Test labeled statements and goto
        if (result > 100) {
            goto too_large;
        }
        
        result += 1;
        
        too_large:
            result = 100;
        
        return result;
    }
    """

    print("Running example...")

    builder = CFGBuilder("c")
    builder.setup_parser()  # You must implement this to load tree-sitter-c

    cfg = builder.build_cfg(c_code)
    print(f"CFG built for function: {cfg.function_name}")
    print(f"Number of nodes: {len(cfg.nodes)}")
    image_path = builder.visualize_cfg(cfg)
