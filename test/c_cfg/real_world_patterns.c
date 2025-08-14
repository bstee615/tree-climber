/**
 * Real-world C programming patterns for CFG testing
 * 
 * This file contains realistic code patterns commonly found in C programs:
 * - Iterative algorithms (factorial, binary search)
 * - String processing with multiple exit points
 * - State machine implementations
 * - Resource management with cleanup patterns
 * - Matrix processing with early termination
 * - Parser-like functions with state transitions
 * - Optimization paths based on input values
 * - Typical main function structure
 * 
 * Use for: Practical scenario validation, real-world CFG complexity testing
 * 
 * These functions represent realistic programming patterns found in production
 * code, testing the CFG implementation's ability to handle complex control
 * flow scenarios that developers actually write.
 */

#include <stdio.h>

// Factorial function with iterative approach
int factorial_iterative(int n) {
    if (n < 0) {
        return -1;  // Error case
    }
    if (n <= 1) {
        return 1;   // Base case
    }
    
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result = result * i;
    }
    return result;
}

// Binary search algorithm
int binary_search(int arr[], int size, int target) {
    int left = 0;
    int right = size - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] == target) {
            return mid;  // Found
        }
        
        if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return -1;  // Not found
}

// String processing with multiple exit points
int string_processor(char *str) {
    if (str == 0) {  // NULL pointer check
        return -1;
    }
    
    int length = 0;
    int digit_count = 0;
    int alpha_count = 0;
    
    while (*str != '\0') {
        length++;
        
        if (*str >= '0' && *str <= '9') {
            digit_count++;
        } else if ((*str >= 'a' && *str <= 'z') || 
                   (*str >= 'A' && *str <= 'Z')) {
            alpha_count++;
        }
        
        if (length > 1000) {  // Safety check
            return -2;  // String too long
        }
        
        str++;
    }
    
    if (digit_count > alpha_count) {
        return 1;  // More digits
    } else if (alpha_count > digit_count) {
        return 2;  // More letters
    } else {
        return 0;  // Equal
    }
}

// State machine implementation
typedef enum {
    STATE_IDLE,
    STATE_PROCESSING,
    STATE_ERROR,
    STATE_COMPLETE
} ProcessorState;

int state_machine_processor(int input, ProcessorState *state) {
    int result = 0;
    
    switch (*state) {
        case STATE_IDLE:
            if (input > 0) {
                *state = STATE_PROCESSING;
                result = 1;
            } else if (input < 0) {
                *state = STATE_ERROR;
                result = -1;
            }
            break;
            
        case STATE_PROCESSING:
            if (input == 0) {
                *state = STATE_COMPLETE;
                result = 100;
            } else if (input > 100) {
                *state = STATE_ERROR;
                result = -2;
            } else {
                result = input * 2;
            }
            break;
            
        case STATE_ERROR:
            if (input == 999) {  // Reset code
                *state = STATE_IDLE;
                result = 0;
            } else {
                result = -1;  // Stay in error
            }
            break;
            
        case STATE_COMPLETE:
            *state = STATE_IDLE;  // Auto-reset
            result = 0;
            break;
            
        default:
            *state = STATE_ERROR;
            result = -3;
    }
    
    return result;
}

// Error handling with cleanup pattern
int resource_manager(int resource_type, int operation) {
    int *buffer = 0;
    int file_handle = -1;
    int result = -1;
    
    // Resource allocation
    switch (resource_type) {
        case 1:  // Memory
            buffer = (int*)malloc(100 * sizeof(int));
            if (!buffer) {
                goto cleanup_and_exit;
            }
            break;
            
        case 2:  // File
            file_handle = open("tempfile.txt", O_RDWR);
            if (file_handle < 0) {
                goto cleanup_and_exit;
            }
            break;
            
        default:
            goto cleanup_and_exit;
    }
    
    // Perform operation
    switch (operation) {
        case 1:  // Read
            if (resource_type == 1 && buffer) {
                result = buffer[0];  // Read from buffer
            } else if (resource_type == 2 && file_handle >= 0) {
                char temp;
                result = read(file_handle, &temp, 1);
            }
            break;
            
        case 2:  // Write
            if (resource_type == 1 && buffer) {
                buffer[0] = 42;  // Write to buffer
                result = 0;
            } else if (resource_type == 2 && file_handle >= 0) {
                result = write(file_handle, "test", 4);
            }
            break;
            
        default:
            result = -2;  // Invalid operation
    }
    
cleanup_and_exit:
    // Cleanup resources
    if (buffer) {
        free(buffer);
    }
    if (file_handle >= 0) {
        close(file_handle);
    }
    
    return result;
}

// Nested loop with early termination
int matrix_search(int matrix[][10], int rows, int cols, int target) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (matrix[i][j] == target) {
                return i * cols + j;  // Return linear index
            }
            
            // Early termination for sorted matrix
            if (matrix[i][j] > target) {
                break;  // No point checking rest of row
            }
        }
    }
    return -1;  // Not found
}

// Parser-like function with multiple states
int simple_parser(char *input) {
    if (!input) return -1;
    
    int state = 0;
    int token_count = 0;
    int error_count = 0;
    char *ptr = input;
    
    while (*ptr != '\0') {
        switch (state) {
            case 0:  // Initial state
                if (*ptr == '(') {
                    state = 1;
                    token_count++;
                } else if (*ptr >= 'a' && *ptr <= 'z') {
                    state = 2;
                    token_count++;
                } else if (*ptr == ' ' || *ptr == '\t') {
                    // Skip whitespace
                } else {
                    error_count++;
                    if (error_count > 10) {
                        return -2;  // Too many errors
                    }
                }
                break;
                
            case 1:  // Inside parentheses
                if (*ptr == ')') {
                    state = 0;
                } else if (*ptr >= 'a' && *ptr <= 'z') {
                    token_count++;
                }
                break;
                
            case 2:  // Reading identifier
                if (*ptr >= 'a' && *ptr <= 'z') {
                    // Continue reading identifier
                } else {
                    state = 0;
                    continue;  // Don't advance ptr
                }
                break;
        }
        ptr++;
    }
    
    return token_count;
}

// Algorithm with multiple optimization paths
int fibonacci_optimized(int n) {
    if (n < 0) {
        return -1;  // Invalid input
    }
    
    if (n <= 1) {
        return n;   // Base cases: fib(0) = 0, fib(1) = 1
    }
    
    // For small values, use simple iteration
    if (n <= 20) {
        int a = 0, b = 1, temp;
        for (int i = 2; i <= n; i++) {
            temp = a + b;
            a = b;
            b = temp;
        }
        return b;
    }
    
    // For larger values, use optimized approach (placeholder)
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result = result + (result * 618) / 1000;  // Approximation
        if (result < 0) {  // Overflow check
            return -2;
        }
    }
    
    return result;
}

// Main function demonstrating typical program structure
int main(int argc, char *argv[]) {
    int result = 0;
    
    // Argument validation
    if (argc < 2) {
        printf("Usage: program <number>\n");
        return 1;
    }
    
    // Convert argument to number
    int input = atoi(argv[1]);
    if (input < 0) {
        printf("Error: negative input not allowed\n");
        return 2;
    }
    
    // Process based on input range
    if (input < 10) {
        result = factorial_iterative(input);
    } else if (input < 100) {
        result = fibonacci_optimized(input);
    } else {
        printf("Input too large\n");
        return 3;
    }
    
    // Output result
    if (result >= 0) {
        printf("Result: %d\n", result);
    } else {
        printf("Computation error\n");
        return 4;
    }
    
    return 0;
}