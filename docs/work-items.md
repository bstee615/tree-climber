1. [x] Parse linear statements into one single CFG node.
2. [x] Label true and false branches on conditional nodes.
3. [x] Label nodes like "for condition" with the text of the condition, etc for exit and init.
4. [x] Update type hints Any to tree_sitter.Node in visitors
5. [x] Remove comments from the CFG.
6. [ ] Add class/file nodes.
7. [ ] Handle forward declarations of function calls.
8. [ ] Raise warnings throughout the code and handle gracefully where nodes are missing.
9. [ ] Avoid hardcoded constants in language specific code, preferring predicates, such as "comment" vs. "line_comment/block_comment" -> is_comment.
