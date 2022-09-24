# Goals

* [ ] Parse `linux-5.18.4`. This requires robust CFG parsing which handles a lot more cases than it does currently.
* [ ] Handle multiple files and functions correctly. Currently, we have only verified correct procedure when the program is a single function.
* [x] PDG (def-use graph)

## C language features

https://en.cppreference.com/w/c

* [x] goto and labels
* [ ] preprocessor macros
* [ ] headers
* [ ] function parameters
* [ ] structs
* [ ] custom typedefs
* [ ] expressions inside statements, such as `if ((i = 0) == 0)`
* [ ] variadic functions
* [ ] global variables
