// --- FUNCTION STRUCTURE ---
 // Function Definition with parameters and return value
int calculateSum(int a, int b) {
// --- OPERATORS (Arithmetic) ---
    return a + b;
}

void printResult(double value) {
   printf("Result: %f\n", value);
}
int main() {
    // --- DATA TYPES ---
    int myInt = 10;
    long myLong = 100000L;
    float myFloat = 5.5f;
    double myDouble = 99.99;
    char myChar = ’X’;
    char myString[] = "Hello AST"; // String and char array
    // Function Invocation (Call)
    int result = calculateSum(myInt, 5);
    // --- OPERATORS (Logic & Comparison) ---
    int condition = (result > 10) && (myFloat < 10.0);
    // --- CONTROL FLOW ---
    // If-Else Statement
    if (condition) {
    printResult(myDouble); // Function call
    } else {
    printResult(0.0);
    }
    // For Loop
    for (int i = 0; i < 5; i++) {
    myInt = myInt + 1;
    }
    // While Loop
    while (myLong > 99990) {
    myLong = myLong - 1;
    }
    return 0;
}