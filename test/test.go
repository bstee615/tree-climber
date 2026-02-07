// package main

// import "fmt"

// --- FUNCTION STRUCTURE ---
// Function Definition with parameters and return value
func calculateSum(a int, b int) int {
	// --- OPERATORS (Arithmetic) ---
	return a + b
}

func printResult(value float64) {
	fmt.Printf("Result: %f\n", value)
}

func main() {
	// --- DATA TYPES ---
	var myInt int = 10
	var myLong int64 = 100000
	var myFloat float32 = 5.5
	var myDouble float64 = 99.99
	var myChar rune = 'X'
	var myString string = "Hello AST" // String

	// Function Invocation (Call)
	result := calculateSum(myInt, 5)

	// --- OPERATORS (Logic & Comparison) ---
	condition := (result > 10) && (myFloat < 10.0)

	// --- CONTROL FLOW ---
	// If-Else Statement
	if condition {
		printResult(myDouble) // Function call
	} else {
		printResult(0.0)
	}

	// For Loop
	for i := 0; i < 5; i++ {
		myInt = myInt + 1
	}

	// While Loop (Go doesn't have while, use for loop)
	for myLong > 99990 {
		myLong = myLong - 1
	}

}
