/**
 * Edge cases and boundary conditions for CFG testing
 * 
 * This file contains edge cases, boundary conditions, and potential error scenarios:
 * - Empty functions and blocks
 * - Single statement blocks (no braces)
 * - Switch statements without default cases
 * - Multiple consecutive jump statements
 * - Unreachable code scenarios
 * - Complex conditional expressions
 * - Very long switch statements
 * - Functions with many parameters
 * 
 * Use for: Robustness testing, error condition handling
 * 
 * These functions test the CFG implementation's ability to handle unusual
 * or extreme cases gracefully, including boundary conditions that might
 * cause parsing errors or generate unexpected CFG structures.
 */

// Empty function
void empty_function() {
}

// Function with only return
int only_return() {
    return 42;
}

// Empty blocks
int empty_blocks(int x) {
    if (x > 0) {
        // Empty if block
    }
    
    while (x > 10) {
        // Empty while block
    }
    
    for (int i = 0; i < x; i++) {
        // Empty for block
    }
    
    switch (x) {
        case 1:
            // Empty case
            break;
        default:
            // Empty default
            break;
    }
    
    return x;
}

// Single statement blocks
int single_statement_blocks(int x) {
    if (x > 0)
        x = x + 1;  // No braces
    
    while (x < 100)
        x = x * 2;  // No braces
    
    for (int i = 0; i < 5; i++)
        x = x + i;  // No braces
    
    return x;
}

// Switch without default
int switch_no_default(int x) {
    int result = x;
    switch (x) {
        case 1:
            result = 10;
            break;
        case 2:
            result = 20;
            break;
    }  // No default case
    return result;
}

// Switch with only default
int switch_only_default(int x) {
    int result = x;
    switch (x) {
        default:
            result = -1;
    }
    return result;
}

// All cases fall through
int switch_all_fallthrough(int x) {
    int result = 0;
    switch (x) {
        case 1:
            result = result + 1;
        case 2:
            result = result + 2;
        case 3:
            result = result + 3;
        default:
            result = result + 10;
    }
    return result;
}

// Multiple consecutive breaks/continues
int multiple_breaks_continues(int limit) {
    int sum = 0;
    for (int i = 0; i < limit; i++) {
        if (i == 5) {
            continue;
            continue;  // Unreachable
        }
        
        if (i == 10) {
            break;
            break;  // Unreachable
        }
        
        sum = sum + i;
    }
    return sum;
}

// Multiple consecutive returns
int multiple_consecutive_returns(int x) {
    if (x > 0) {
        return x;
        return -x;  // Unreachable
    }
    return 0;
}

// Goto jumping over declarations
int goto_over_declarations(int x) {
    if (x < 0) {
        goto skip_declarations;
    }
    
    int a = 5;
    int b = 10;
    x = a + b;
    
skip_declarations:
    return x;
}

// Backward goto creating loop
int backward_goto_loop(int n) {
    int sum = 0;
    
loop_start:
    if (n <= 0) {
        return sum;
    }
    
    sum = sum + n;
    n = n - 1;
    goto loop_start;
}

// Multiple labels
int multiple_labels(int x) {
label1:
label2:
label3:
    x = x + 1;
    
    if (x == 1) {
        goto label1;
    }
    if (x == 2) {
        goto label2;
    }
    if (x == 3) {
        goto label3;
    }
    
    return x;
}

// Complex expressions in conditions
int complex_expressions(int x, int y, int z) {
    // Complex if condition
    if ((x > 0 && y < 10) || (z == 5 && x != y)) {
        x = x + y + z;
    }
    
    // Complex while condition  
    while ((x > 0 && x < 100) && (y > 0 || z < 0)) {
        if (x % 2 == 0 && y % 3 == 0 && z % 5 == 0) {
            break;
        }
        x = x - 1;
        y = y + 1;
        z = z * 2;
    }
    
    // Complex for condition
    for (int i = 0; (i < x && i < y) || i < z; i++) {
        if (i * i > x + y + z) {
            continue;
        }
        x = x + i;
    }
    
    return x + y + z;
}

// Nested ternary operators (not control flow, but complex)
int ternary_expressions(int x, int y, int z) {
    int result = (x > y) ? (y > z ? x : z) : (x > z ? y : x);
    return result;
}

// Very long switch statement
int long_switch(int x) {
    int result = 0;
    switch (x) {
        case 1: result = 1; break;
        case 2: result = 4; break;
        case 3: result = 9; break;
        case 4: result = 16; break;
        case 5: result = 25; break;
        case 6: result = 36; break;
        case 7: result = 49; break;
        case 8: result = 64; break;
        case 9: result = 81; break;
        case 10: result = 100; break;
        case 11: result = 121; break;
        case 12: result = 144; break;
        case 13: result = 169; break;
        case 14: result = 196; break;
        case 15: result = 225; break;
        default: result = x * x; break;
    }
    return result;
}

// Function with many parameters (tests entry node)
int many_parameters(int a, int b, int c, int d, int e, 
                   int f, int g, int h, int i, int j) {
    return a + b + c + d + e + f + g + h + i + j;
}

// Minimal valid C program
int minimal() {
    return 0;
}