/*
 * C DFG Stress Test - Comprehensive scenarios for dataflow analysis
 * This file contains complex C constructs to thoroughly test DFG analysis.
 */

// Basic function with multiple parameters
int add(int a, int b) {
    int result = a + b;
    return result;
}

// Function with parameter modification
int increment(int x) {
    x = x + 1;
    int doubled = x * 2;
    return doubled;
}

// Recursive function
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

// Function with complex control flow
int complex_flow(int input) {
    int result = 0;
    
    if (input > 0) {
        result = input * 2;
        if (result > 10) {
            result = result - 5;
        }
    } else {
        result = input * -1;
        while (result < 10) {
            result = result + 1;
        }
    }
    
    return result;
}

// Function with loops and function calls
int sum_processed(int count) {
    int total = 0;
    for (int i = 0; i < count; i++) {
        total = total + increment(i);
    }
    return total;
}

// Function with multiple local variables
int multi_vars(int a, int b, int c) {
    int x = a + b;
    int y = b + c;
    int z = x + y;
    
    // Redefine some variables
    x = z - a;
    y = x + c;
    
    return x + y + z;
}

// Function with nested function calls
int nested_calls(int val) {
    int processed = increment(val);
    int doubled = add(processed, processed);
    return complex_flow(doubled);
}

// Main function with comprehensive testing
int main() {
    // Basic assignments
    int x = 5;
    int y = 3;
    
    // Function calls with argument aliasing
    int sum = add(x, y);
    int inc_x = increment(x);
    
    // Complex expressions
    int complex_result = nested_calls(x + y);
    
    // Variable reuse
    x = complex_result;
    y = sum_processed(x);
    
    // Conditional with function calls
    int final_result;
    if (x > y) {
        final_result = factorial(5);
    } else {
        final_result = multi_vars(x, y, sum);
    }
    
    // Loop with function calls
    for (int i = 0; i < 3; i++) {
        final_result = final_result + add(i, final_result);
        if (final_result > 100) {
            break;
        }
    }
    
    return final_result;
}

// Additional test functions
void test_pointers_and_arrays() {
    int arr[5] = {1, 2, 3, 4, 5};
    int *ptr = arr;
    
    for (int i = 0; i < 5; i++) {
        arr[i] = increment(arr[i]);
        *ptr = add(*ptr, i);
        ptr++;
    }
}

void test_switch_statement(int value) {
    int result = 0;
    
    switch (value) {
        case 1:
            result = increment(value);
            break;
        case 2:
            result = add(value, 10);
            // Fallthrough
        case 3:
            result = result + complex_flow(value);
            break;
        default:
            result = factorial(value % 5);
    }
}

// Test function with multiple returns
int multiple_returns(int condition) {
    int x = increment(condition);
    
    if (x < 0) {
        return add(x, -1);
    }
    
    if (x > 100) {
        return complex_flow(x);
    }
    
    return factorial(x % 10);
}

// Test deeply nested calls
int deeply_nested(int depth) {
    if (depth <= 0) {
        return 1;
    }
    
    int a = increment(depth);
    int b = add(a, depth);
    int c = complex_flow(b);
    
    return deeply_nested(depth - 1) + c;
}