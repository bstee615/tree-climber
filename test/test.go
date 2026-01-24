// package main

// import (
// 	"fmt"
// )

// Sample functions to test Go language parsing

func main() {
	result := add(5, 3)
	fmt.Println("Result:", result)
	
	greet("World")
	
	person := Person{Name: "Alice", Age: 30}
	person.SayHello()
}

// Simple function with parameters and return value
// func add(a int, b int) int {
// 	return a + b
// }

// // Function with single parameter
// func greet(name string) {
// 	fmt.Printf("Hello, %s!\n", name)
// }

// // Struct definition
// type Person struct {
// 	Name string
// 	Age  int
// }

// // Method on struct
// func (p Person) SayHello() {
// 	fmt.Printf("Hi, I'm %s and I'm %d years old\n", p.Name, p.Age)
// }

// // Function with multiple return values
// func divide(a, b float64) (float64, error) {
// 	if b == 0 {
// 		return 0, fmt.Errorf("division by zero")
// 	}
// 	return a / b, nil
// }

// // Variadic function
// func sum(numbers ...int) int {
// 	total := 0
// 	for _, num := range numbers {
// 		total += num
// 	}
// 	return total
// }

// // Anonymous function
// var multiply = func(x, y int) int {
// 	return x * y
// }