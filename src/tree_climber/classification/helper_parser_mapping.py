from tree_sitter import Tree

from tree_climber.ast_utils import parse_source_to_ast
from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.visitor import CFG
from tree_climber.cli.cpg import CPG
from tree_climber.dataflow.analyses.def_use import DefUseResult, DefUseSolver
from tree_climber.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_climber.dataflow.solver import RoundRobinSolver
import re

go_to_cpp = {
    # --- Functions & Blocks ---
    "function_declaration": "function_definition",
    "method_declaration": "function_definition", # Add: Go methods
    "parameter_list": "parameter_list",
    "block": "compound_statement",
    "return_statement": "return_statement",

    # --- Declarations ---
    "short_var_declaration": "declaration", # x := 1 -> auto x = 1;
    "var_declaration": "declaration",       # var x int -> int x;
    "const_declaration": "declaration",
    "type_identifier": "type_identifier",
    "field_declaration": "field_declaration",

    # --- Control Flow ---
    "if_statement": "if_statement",
    "for_statement": "for_statement",       # Lưu ý: Go 'for' bao gồm cả 'while' của C++
    "break_statement": "break_statement",
    "continue_statement": "continue_statement",
    "switch_statement": "switch_statement", # Add
    "case_clause": "case_statement",        # Add
    "default_clause": "default_statement",  # Add

    # --- Expressions ---
    "binary_expression": "binary_expression",
    "unary_expression": "unary_expression",       # Add: !, *, &, -, +
    "inc_statement": "update_expression",
    "dec_statement": "update_expression",
    "assignment_statement": "assignment_expression",
    "call_expression": "call_expression",
    "argument_list": "argument_list",

    # --- Access & Data Structure ---
    "selector_expression": "field_expression",    # Fix: a.b -> a.b / a->b
    "index_expression": "subscript_expression",   # Add: a[i]
    "parenthesized_expression": "parenthesized_expression", # Fix: (exp)

    # --- Literals ---
    "interpreted_string_literal": "string_literal",
    "raw_string_literal": "string_literal",
    "int_literal": "number_literal",              # Add
    "float_literal": "number_literal",            # Add
    "composite_literal": "initializer_list",      # Add: struct/array init
}

def replace_go_to_cpp(code: str) -> str:
    """
    Replace Go-specific syntax elements with C++ equivalents in the source code.
    """
    for go_node, cpp_node in go_to_cpp.items():
        # Regex: match Go node names and replace with C++ equivalents
        pattern = rf'({go_node})'
        code = re.sub(pattern, f'{cpp_node}', code)
    return code



class CppMappedNode:
    """
    Wrapper class để giả lập node Go thành node C++ 
    bằng cách override thuộc tính .type
    """
    def __init__(self, node):
        self._node = node

    @property
    def type(self):
        # Trả về tên C++ nếu có trong map, nếu không giữ nguyên tên Go
        return go_to_cpp.get(self._node.type, self._node.type)

    @property
    def children(self):
        # Quan trọng: Khi duyệt con, cũng phải wrap các con lại
        return [CppMappedNode(child) for child in self._node.children]

    @property
    def named_children(self):
        return [CppMappedNode(child) for child in self._node.named_children]

    def child_by_field_name(self, name):
        child = self._node.child_by_field_name(name)
        return CppMappedNode(child) if child else None
    
    # Delegate các thuộc tính khác (start_point, text, etc.) cho node gốc
    def __getattr__(self, name):
        return getattr(self._node, name)

    def __repr__(self):
        return f"<Node type={self.type} (mapped), text={self._node.text[:10]}...>"

class ProxyTree:
    """
    Wrapper cho object Tree để trả về root_node đã được map
    """
    def __init__(self, tree):
        self._tree = tree
    
    @property
    def root_node(self):
        return CppMappedNode(self._tree.root_node)
    
    def __getattr__(self, name):
        return getattr(self._tree, name)

def analyze_source_code(source: str, language: str) -> CPG:
    # 1. Parse ra cây AST gốc của Go (chưa chỉnh sửa gì cả)
    raw_tree = parse_source_to_ast(source, language)
    
    # 2. Bọc cây đó lại để "fake" thành C++ node types
    # Lúc này, các tool phía sau (CFGBuilder) sẽ nhìn thấy type kiểu C++
    mapped_tree = ProxyTree(raw_tree)

    cfg = None
    # Truyền cây đã map vào builder
    # Lưu ý: Builder cần phải chấp nhận object dạng Tree (có thuộc tính root_node)
    cfg = _build_cfg(mapped_tree, language=language) 
    
    if cfg is None:
        raise ValueError("CFG is required for dataflow analysis")
        
    def_use_result = _analyze_dataflow(cfg)
    
    cpg = CPG()
    cpg.build_from_analysis(cfg=cfg, def_use_result=def_use_result)
    
    return cpg

# Các hàm dưới giữ nguyên logic, chỉ bỏ việc xử lý string
def _parse_source_string(source_code: str, language: str) -> Tree:
    return parse_source_to_ast(source_code, language)

def _build_cfg(tree, language: str) -> CFG: # tree ở đây là ProxyTree
    builder = CFGBuilder(language) # Có thể bạn cần trick language="cpp" ở đây nếu builder check string language
    builder.setup_parser()
    return builder.build_cfg(tree=tree)


def _analyze_dataflow(cfg: CFG) -> DefUseResult:
    """Perform reaching definitions dataflow analysis."""
    problem = ReachingDefinitionsProblem()
    dataflow_solver = RoundRobinSolver()
    def_use_solver = DefUseSolver()
    return def_use_solver.solve(cfg, dataflow_solver.solve(cfg, problem))
