# Goals

* [ ] Auto test with https://github.com/marketplace/actions/setup-python and publish with https://github.com/marketplace/actions/pypi-publish
* [ ] Parse `linux-5.18.4`. This requires robust CFG parsing which handles a lot more cases than it does currently.
* [ ] Handle multiple files and functions correctly. Currently, we have only verified correct procedure when the program is a single function.
* [x] PDG (def-use graph)

## C language features

https://en.cppreference.com/w/c

* [ ] preprocessor macros
* [ ] headers
* [ ] function parameters
* [ ] structs
* [ ] custom typedefs
* [ ] expressions inside statements, such as `if ((i = 0) == 0)`
* [ ] variadic functions
* [ ] global variables
* [x] goto and labels
