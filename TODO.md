For release 0.1.0
- [ ] Comprehensive tests and example programs for C and Java
- [ ] CLI parity with 0.0.0
- [x] Full list of language features that are supported and not supported (limitations)

Parsing Bugs
- [ ] Java def use, a++ should point to itself
- [ ] C def use, a++ should point to itself and should point to uses of a
- [ ] Function calls should have an edge from exit going back to the call
- [ ] Function parameters should alias def uses

UI Bugs
- [ ] Code editor, when typing, the highlight doesn't update so points to the wrong tokens

Old list
- [ ] Add class/file nodes.
- [ ] Handle forward declarations of function calls.
- [ ] Raise warnings throughout the code and handle gracefully where nodes are missing.
- [ ] Avoid hardcoded constants in language specific code, preferring predicates, such as "comment" vs. "line_comment/block_comment" -> is_comment.
- [ ] Detect potentially undefined variables
- [x] 💪 Need to implement main.py in parity with tree-climber
- [x] 💪 Allow toggling Def use edges
- [x] Java enhanced for loop, next() and hasNext() point to the same ast node.
  - In general, all CFG nodes should point to a distinct AST node.
- [x] When editor is blurred, don't deselect if the focus moves to the graph
  - Too complex -- when the user clicks the graph in a blank area, do we deselect? Left as is.
- [x] Remove python from GUI
- [x] Save language in local storage
- [x] Switch case labels in GUI are "case" instead of the value
- [x] break in do/while in java test program goes to the next statement but should go out of the loop
  - Fix: Incorrect name for initializer -- should be "init"
