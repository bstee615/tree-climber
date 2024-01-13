from tree_sitter_languages import get_parser
from pyvis.network import Network
import networkx as nx
from .util import concretize_graph, concretize_node


class CfgNode:
    """Represents a node in the CFG."""
    def __init__(self, ast_node, node_type=None):
        self.node_type = node_type
        self.ast_node = ast_node
    
    def __repr__(self):
        return str(self)
    
    def __hash__(self):
        return self.id
    
    def __str__(self):
        if isinstance(self.ast_node, str):
            return f"{type(self).__name__} ({self.ast_node})"
        else:
            return f"{type(self).__name__} ({self.ast_node.type}) {repr(self.ast_node.text.decode())}"

    def asdict(self):
        return {
            "node_type": self.node_type,
            "ast_node": concretize_node(self.ast_node),
        }

    @property
    def id(self):
        return id(self)


def is_cfg_statement(ast_node):
    """Return true if this node is a CFG statement."""
    return (ast_node.type.endswith("_statement") and not ast_node.type == "compound_statement") \
        or ast_node.type in ["declaration", "parameter_declaration"]


class CfgVisitor:
    """Walks the AST to create a CFG."""
    
    def __init__(self):
        self.return_statements = []
        self.break_statements = []
        self.continue_statements = []
        self.goto_statements = []
        self.labeled_statements = []
        self.passes = []

        self.graph = nx.DiGraph()

    def fork(self):
        """Fork this visitor to walk a subgraph of the CFG"""
        visitor = CfgVisitor()
        visitor.return_statements = self.return_statements
        visitor.break_statements = self.break_statements
        visitor.continue_statements = self.continue_statements
        visitor.goto_statements = self.goto_statements
        visitor.labeled_statements = self.labeled_statements
        visitor.passes = self.passes
        visitor.graph = self.graph
        return visitor

    def add_child(self, parent, child, **kwargs):
        self.graph.add_edge(parent, child, **kwargs)
    
    def parents(self, node):
        return self.graph.predecessors(node)
    
    def remove_children(self, node):
        self.graph.remove_edges_from(list(self.graph.out_edges(node)))
    
    def children(self, node):
        return self.graph.successors(node)
    
    def visit(self, node):
        """
        Convert a single node as the root to a subgraph in the CFG.
        Return two nodes, one root and one "tail", lowest point in the CFG.
        For subgraphs which terminate in multiple nodes, point all to a "pass-through" node which will be post-processed out.

        Compound statements:
        a -> b -> c ; return (a, c)

        If statements:
        cond -T-> a -> pass ; return (cond, pass)
             -F-> b -/
        
        Loops:
        init -> c....o....n....d -F-> pass ; return (init, pass)
                -T-> update -/
        """

        if node.type == "if_statement":
            condition = node.child_by_field_name("condition")
            condition_cfg = CfgNode(condition, node_type="branch")

            true_branch = node.child_by_field_name("consequence")
            true_cfg_entry, true_cfg_exit = self.visit(true_branch)

            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)
            self.add_child(condition_cfg, true_cfg_entry, label="TRUE")

            false_branch = node.child_by_field_name("alternative")
            if false_branch:
                false_branch_entry, false_branch_exit = self.visit(false_branch)
                self.add_child(condition_cfg, false_branch_entry, label="FALSE")
                self.add_child(false_branch_exit, pass_cfg)
            else:
                self.add_child(condition_cfg, pass_cfg, label="FALSE")
            self.add_child(true_cfg_exit, pass_cfg)

            return condition_cfg, pass_cfg
        if node.type == "switch_statement":
            condition = node.child_by_field_name("condition")
            condition_cfg = CfgNode(condition, node_type="branch")

            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)

            fork = self.fork()
            fork.break_statements = []
            fork.continue_statements = []

            body = node.child_by_field_name("body")
            children = [c for c in body.children if c.is_named and not c.type == "comment"]
            for case_stmt in children:
                case_cond = case_stmt.child_by_field_name("value")
                case_cond_text = case_cond.text.decode()
                case_body = next(c for c in case_stmt.children if c.id != case_cond.id and c.is_named and not c.type == "comment")
                case_entry, case_exit = fork.visit(case_body)
                self.add_child(condition_cfg, case_entry, label=case_cond_text)
                self.add_child(case_exit, pass_cfg)

            return condition_cfg, pass_cfg
        elif node.type == "for_statement":
            initializer = node.child_by_field_name("initializer")
            condition = node.child_by_field_name("condition")
            update = node.child_by_field_name("update")
            stmt = next(child for child in reversed(node.children) if child.is_named and child.type != "comment")

            init_cfg = CfgNode(initializer, node_type="loop")
            cond_cfg = CfgNode(condition, node_type="loop")
            fork = self.fork()
            fork.break_statements = []
            fork.continue_statements = []
            stmt_entry, stmt_exit = fork.visit(stmt)
            update_cfg = CfgNode(update, node_type="loop")
            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)

            for break_cfg in fork.break_statements:
                self.remove_children(break_cfg)
                self.add_child(break_cfg, pass_cfg)
            for continue_cfg in fork.continue_statements:
                self.remove_children(continue_cfg)
                self.add_child(continue_cfg, update_cfg)

            self.add_child(init_cfg, cond_cfg)
            self.add_child(cond_cfg, stmt_entry, label="TRUE")
            self.add_child(stmt_exit, update_cfg)
            self.add_child(update_cfg, cond_cfg)
            self.add_child(cond_cfg, pass_cfg, label="FALSE")

            return init_cfg, pass_cfg
        elif node.type == "while_statement":
            condition = node.child_by_field_name("condition")
            body = node.child_by_field_name("body")

            cond_cfg = CfgNode(condition, node_type="loop")
            fork = self.fork()
            fork.break_statements = []
            fork.continue_statements = []
            body_entry, body_exit = fork.visit(body)
            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)

            for break_cfg in fork.break_statements:
                self.remove_children(break_cfg)
                self.add_child(break_cfg, pass_cfg)
            for continue_cfg in fork.continue_statements:
                self.remove_children(continue_cfg)
                self.add_child(continue_cfg, update_cfg)

            self.add_child(cond_cfg, body_entry, label="TRUE")
            self.add_child(body_exit, cond_cfg)
            self.add_child(cond_cfg, pass_cfg, label="FALSE")

            return cond_cfg, pass_cfg
        elif node.type == "do_statement":
            condition = node.child_by_field_name("condition")
            body = node.child_by_field_name("body")

            cond_cfg = CfgNode(condition, node_type="loop")
            fork = self.fork()
            fork.break_statements = []
            fork.continue_statements = []
            body_entry, body_exit = fork.visit(body)
            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)

            for break_cfg in fork.break_statements:
                self.remove_children(break_cfg)
                self.add_child(break_cfg, pass_cfg)
            for continue_cfg in fork.continue_statements:
                self.remove_children(continue_cfg)
                self.add_child(continue_cfg, update_cfg)

            self.add_child(body_exit, cond_cfg)
            self.add_child(cond_cfg, body_entry, label="TRUE")
            self.add_child(cond_cfg, pass_cfg, label="FALSE")

            return body_entry, pass_cfg
        elif node.type == "function_definition":
            entry_cfg = CfgNode("entry", node_type="auxiliary")
            parent_cfg = entry_cfg
            for param in [c for c in node.child_by_field_name("declarator").child_by_field_name("parameters").children if c.is_named and c.type != "comment"]:
                param_cfg = CfgNode(param)
                self.add_child(parent_cfg, param_cfg)
                parent_cfg = param_cfg
            body = node.child_by_field_name("body")
            fork = self.fork()
            fork.return_statements = []
            body_entry, body_exit = fork.visit(body)
            exit_cfg = CfgNode("exit", node_type="auxiliary")

            for return_cfg in fork.return_statements:
                self.remove_children(return_cfg)
                self.add_child(return_cfg, exit_cfg)

            self.add_child(parent_cfg, body_entry)
            self.add_child(body_exit, exit_cfg)
            return entry_cfg, exit_cfg
        elif node.type == "labeled_statement":
            label = node.child_by_field_name("label")
            label_text = label.text.decode()

            children = [child for child in node.children if child.id != label.id and child.is_named and not child.type == "comment"]
            cfg_begin = None
            cfg_end = None
            last_cfg_exit = None
            for child in children:
                cfg_entry, cfg_exit = self.visit(child)
                if last_cfg_exit is not None:
                    self.add_child(last_cfg_exit, cfg_entry)
                if cfg_begin is None:
                    cfg_begin = cfg_entry
                cfg_end = last_cfg_exit = cfg_exit
            
            self.labeled_statements.append((cfg_begin, label_text))
                
            return cfg_begin, cfg_end
        elif node.type in ("translation_unit", "compound_statement"):
            children = [child for child in node.children if child.is_named and not child.type == "comment"]
            cfg_begin = None
            cfg_end = None
            last_cfg_exit = None
            for child in children:
                cfg_entry, cfg_exit = self.visit(child)
                if last_cfg_exit is not None:
                    self.add_child(last_cfg_exit, cfg_entry)
                if cfg_begin is None:
                    cfg_begin = cfg_entry
                cfg_end = last_cfg_exit = cfg_exit
                
            return cfg_begin, cfg_end
        elif is_cfg_statement(node):
            cfg_node = CfgNode(node)
            self.graph.add_node(cfg_node)
            if node.type == "break_statement":
                self.break_statements.append(cfg_node)
                cfg_node.node_type = "jump"
            elif node.type == "continue_statement":
                self.continue_statements.append(cfg_node)
                cfg_node.node_type = "jump"
            elif node.type == "return_statement":
                self.return_statements.append(cfg_node)
                cfg_node.node_type = "jump"
            elif node.type == "goto_statement":
                label = node.child_by_field_name("label").text.decode()
                self.goto_statements.append((cfg_node, label))
                cfg_node.node_type = "jump"
            return cfg_node, cfg_node
        else:
            raise NotImplementedError(f"({node.type}) {node.text.decode()}")

    def postprocess(self):
        """Postprocess a CFG created using this visitor"""
        for goto_cfg, label in self.goto_statements:
            # TODO handle duplicate labels
            label_cfg = next(stmt for stmt, l in self.labeled_statements if l == label)
            self.remove_children(goto_cfg)
            self.add_child(goto_cfg, label_cfg)

        for n in self.passes:
            parents = list(self.parents(n))
            children = list(self.children(n))
            
            in_edges = list(self.graph.in_edges(n, data=True))
            in_edge_data = in_edges[0][2]
            mismatched_nodes = [(u, v, d) for u, v, d in in_edges if in_edge_data != d]
            if any(mismatched_nodes):
                print("WARNING: Mismatched in data", mismatched_nodes, in_edges[0])
            
            out_edges = list(self.graph.out_edges(n, data=True))
            out_edge_data = out_edges[0][2]
            mismatched_nodes = [(u, v, d) for u, v, d in out_edges if out_edge_data != d]
            if any(mismatched_nodes):
                print("WARNING: Mismatched out data", mismatched_nodes, out_edges[0])
            
            data = {**in_edge_data, **out_edge_data}

            self.graph.remove_edges_from(in_edges + out_edges)
            for p in parents:
                for c in children:
                    self.add_child(p, c, **data)
            self.graph.remove_node(n)

def visualize_cfg(cfg, fpath):
    net = Network(directed=True)
    net.from_nx(concretize_graph(cfg))
    net.show(fpath, notebook=False)


if __name__ == "__main__":
    parser = get_parser("c")
    tree = parser.parse(b"""int main(int argc, char **argv) {
    x = 0;
    if ((i = 0) == 0) {
        x += 15;
    }
    else
        for (int i = 0; i < 10; i ++) {
            x += i;
            if (x)
                continue;
            x -= i;
        }
    
    while (x) {
        x --;
        if (y) {
            goto end;
        }
    }
    do {
        x --;
    } while (x);
                        
    switch (x) {
        case 0:
            x += 10;
            break;
        case 10:
            x -= 10;
            break;
    }
                        
end:
    return x + 10
}""")

    visitor = CfgVisitor()
    cfg_entry, cfg_exit = visitor.visit(tree.root_node)
    visitor.postprocess()
    cfg = visitor.graph
    visualize_cfg(cfg, "test_cfg.html")
