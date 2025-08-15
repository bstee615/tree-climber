For release 0.1.0
- [x] Comprehensive tests and example programs for C and Java
  - [x] C (37/37 tests passed - 100% success)
  - [x] Java (29/29 tests passed - 100% success)
- [x] CLI parity with 0.0.0
- [x] Full list of language features that are supported and not supported (limitations)

Parsing Bugs
- [x] Both languages CFG, Function calls should have an edge from exit going back to the call
- [x] Both languages DFG, Function parameters should alias def uses
- [x] Java def use, a++ should point to itself
- [x] C def use, a++ should point to itself and should point to uses of a

Java CFG Enhancement Opportunities (Low Priority)
- [ ] Method call chain decomposition: Separate chained method calls into individual CFG nodes for better granularity
  - Current: `obj.method1().method2()` creates single STATEMENT node
  - Enhancement: Create separate METHOD_CALL nodes for each call in chain
  - Benefits: More granular CFG representation, better dataflow analysis
- [ ] Lambda expression CFG contexts: Create separate CFG contexts for lambda body statements
  - Current: Lambda bodies processed within containing method CFG
  - Enhancement: Generate isolated CFG contexts for lambda expressions
  - Benefits: Better representation of functional programming constructs
- [ ] Modern Java switch expression support: Full support for Java 14+ switch expressions with yield
  - Current: Switch expressions create minimal CFG nodes
  - Enhancement: Complete switch expression parsing with yield statements and multiple case values
  - Benefits: Complete Java 14+ language feature support
- [ ] Exception handling flow completeness: More explicit exception flow paths between try/catch/finally blocks
  - Current: Exception handling creates correct but dense statement structure
  - Enhancement: Clearer exception flow representation and propagation paths
  - Benefits: Better analysis of exception control flow patterns
- [ ] Method call context enhancement: Complete TODO at line 63 in java.py for full method call qualification
  - Current: Returns only method name (identifiers[-1])
  - Enhancement: Capture full context (obj.method vs Class.staticMethod)
  - Benefits: Better distinction between instance and static method calls

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
