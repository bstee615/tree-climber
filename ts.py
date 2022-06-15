from tree_sitter import Language, Parser
import networkx as nx
import matplotlib.pyplot as plt

Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',

  # Include one or more languages
  [
    'tree-sitter-c',
  ]
)

C_LANGUAGE = Language('build/my-languages.so', 'c')
parser = Parser()
parser.set_language(C_LANGUAGE)
tree = parser.parse(bytes("""int main()
{
    int x = 0;
    x = x + 1;
    if (x > 1) {
        x += 5;
    }
    x = x + 2;
    for (int i = 0; i < 10; i ++) {
        x --;
    }
    x = x + 3;
    while (x < 0) {
        x ++;
        x = x + 1;
    }
    x = x + 4;
    return x;
}
""", "utf8"))


"""
How Joern does it:
https://github.com/joernio/joern/blob/6df0bbe6afad7f9b04bf0d1877e9797a7cdddcc4/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/controlflow/cfgcreation/CfgCreator.scala
/** Translation of abstract syntax trees into control flow graphs
  *
  * The problem of translating an abstract syntax tree into a corresponding control flow graph can be formulated as a
  * recursive problem in which sub trees of the syntax tree are translated and their corresponding control flow graphs
  * are connected according to the control flow semantics of the root node. For example, consider the abstract syntax
  * tree for an if-statement:
  * {{{
  *               (  if )
  *              /       \
  *          (x < 10)  (x += 1)
  *            / \       / \
  *           x  10     x   1
  * }}}
  * This tree can be translated into a control flow graph, by translating the sub tree rooted in `x < 10` and that of `x
  * += 1` and connecting their control flow graphs according to the semantics of `if`:
  * {{{
  *            [x < 10]----
  *               |t     f|
  *            [x +=1 ]   |
  *               |
  * }}}
  *
  * The semantics of if dictate that the first sub tree to the left is a condition, which is connected to the CFG of the
  * second sub tree - the body of the if statement - via a control flow edge with the `true` label (indicated in the
  * illustration by `t`), and to the CFG of any follow-up code via a `false` edge (indicated by `f`).
  *
  * A problem that becomes immediately apparent in the illustration is that the result of translating a sub tree may
  * leave us with edges for which a source node is known but the destination node depends on parents or siblings that
  * were not considered in the translation. For example, we know that an outgoing edge from [x<10] must exist, but we do
  * not yet know where it should lead. We refer to the set of nodes of the control flow graph with outgoing edges for
  * which the destination node is yet to be determined as the "fringe" of the control flow graph.
  */
"""

class BaseVisitor:   
    """
    Extensible AST visitor.
    Traverses and prints all nodes recursively by default.
    """

    def visit(self, n, indentation_level=0, **kwargs):
        getattr(self, f"visit_{n.type}", self.visit_default)(n=n, indentation_level=indentation_level, **kwargs)
    
    def visit_children(self, n, indentation_level, **kwargs):
        for c in n.children:
            self.visit(c, indentation_level+1, parent=n, siblings=n.children)

    def visit_default(self, n, indentation_level, **kwargs):
        print("\t" * indentation_level, "enter", n)
        self.visit_children(n, indentation_level)
        print("\t" * indentation_level, "exit", n)

def test_base_visitor():
    v = BaseVisitor()
    v.visit(tree.root_node)

class CFGCreator(BaseVisitor):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self):
        super(CFGCreator).__init__()
        self.cfg = nx.DiGraph()
        self.node_id = 0
        self.fringe = []
    
    def add_cfg_node(self, ast_node, label):
        node_id = self.node_id
        self.cfg.add_node(node_id, n=ast_node, label=label)
        self.node_id += 1
        return node_id
    
    def add_edge_from_fringe_to(self, node_id):
        # TODO: assign edge type
        self.cfg.add_edges_from(zip(self.fringe, [node_id] * len(self.fringe)))
        self.fringe = []
    
    """
    VISITOR RULES
    """

    def visit_function_definition(self, n, **kwargs):
        entry_id = self.add_cfg_node(n, "FUNC_ENTRY")
        self.fringe.append(entry_id)
        self.visit_children(n, **kwargs)
        exit_id = self.add_cfg_node(n, "FUNC_EXIT")
        self.add_edge_from_fringe_to(exit_id)

    def visit_default(self, n, indentation_level, **kwargs):
        self.visit_children(n, indentation_level)

    """STRAIGHT LINE STATEMENTS"""

    def enter_statement(self, n):
        node_id = self.add_cfg_node(n, f"{n.type}\n`{n.text.decode()}`")
        self.add_edge_from_fringe_to(node_id)
        self.fringe.append(node_id)

    def visit_expression_statement(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    def visit_init_declarator(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    """STRUCTURED CONTROL FLOW"""

    def visit_if_statement(self, n, **kwargs):
        condition = n.children[1].children[1]
        assert condition.type in ("binary_expression",), condition.type
        condition_id = self.add_cfg_node(condition, f"{condition.type}\n`{condition.text.decode()}`")
        self.add_edge_from_fringe_to(condition_id)
        self.fringe.append(condition_id)

        compound_statement = n.children[2]
        assert compound_statement.type == "compound_statement", compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.fringe.append(condition_id)

    def visit_for_statement(self, n, **kwargs):
        init = n.children[2]
        cond = n.children[3]
        incr = n.children[5]
        
        assert init.type in ("declaration",), cond.type
        assert cond.type in ("binary_expression",), cond.type
        assert incr.type in ("update_expression",), cond.type

        init_id = self.add_cfg_node(init, f"{init.type}\n`{init.text.decode()}`")
        cond_id = self.add_cfg_node(cond, f"{cond.type}\n`{cond.text.decode()}`")
        incr_id = self.add_cfg_node(incr, f"{incr.type}\n`{incr.text.decode()}`")

        self.add_edge_from_fringe_to(init_id)
        self.cfg.add_edge(init_id, cond_id)
        self.fringe.append(cond_id)

        compound_statement = n.children[7]
        assert compound_statement.type == "compound_statement", compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.add_edge_from_fringe_to(incr_id)
        self.cfg.add_edge(incr_id, cond_id)
        self.fringe.append(cond_id)

    def visit_while_statement(self, n, **kwargs):
        cond = n.children[1].children[1]
        
        assert cond.type in ("binary_expression",), cond.type

        cond_id = self.add_cfg_node(cond, f"{cond.type}\n`{cond.text.decode()}`")

        self.cfg.add_edges_from(zip(self.fringe, [cond_id] * len(self.fringe)))
        self.fringe = []
        self.fringe.append(cond_id)

        compound_statement = n.children[2]
        assert compound_statement.type == "compound_statement", compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

def test_cfg():
    v = CFGCreator()
    v.visit(tree.root_node)
    print(v.cfg)
    pos = nx.spring_layout(v.cfg, seed=0)
    nx.draw(v.cfg, pos=pos)
    nx.draw_networkx_labels(v.cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in v.cfg.nodes(data=True)})
    plt.show()
