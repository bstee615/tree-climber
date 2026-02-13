import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from tree_sitter import Node

from tree_climber.cfg.cfg_types import CFGNode
from tree_climber.cfg.visitor import CFG
from tree_climber.dataflow.analyses.def_use import DefUseResult

import re

go_to_cpp = {
    # --- Functions & Blocks ---
    "function_declaration": "function_definition",
    "method_declaration": "function_definition",
    "parameter_list": "parameter_list",
    "block": "compound_statement",
    "return_statement": "return_statement",

    # --- Declarations ---
    "short_var_declaration": "declaration",
    "var_declaration": "declaration",
    "const_declaration": "declaration",
    "type_identifier": "type_identifier",
    "field_declaration": "field_declaration",
    
    # --- NEW: Type Definitions (Crucial for Memory Safety Analysis) ---
    "pointer_type": "pointer_declarator",       # *T
    "array_type": "array_declarator",           # [N]T
    "slice_type": "template_type",              # []T (Mapped to vector<T> semantics ideally)
    "interface_type": "class_specifier",        # interface{}

    # --- Control Flow ---
    "if_statement": "if_statement",
    "for_statement": "for_statement",
    "break_statement": "break_statement",
    "continue_statement": "continue_statement",
    "switch_statement": "switch_statement",
    "case_clause": "case_statement",
    "default_clause": "default_statement",
    
    # --- NEW: Go Special Flow (Map to Call for Data Flow Analysis) ---
    "defer_statement": "call_expression",       # Treat defer as a function call
    "go_statement": "call_expression",          # Treat go routine as a function call

    # --- Expressions ---
    "binary_expression": "binary_expression",
    "unary_expression": "unary_expression",
    "inc_statement": "update_expression",
    "dec_statement": "update_expression",
    "assignment_statement": "assignment_expression",
    "call_expression": "call_expression",
    "argument_list": "argument_list",
    "type_conversion_expression": "cast_expression", # T(x) -> (T)x

    # --- Access & Data Structure ---
    "selector_expression": "field_expression",
    "index_expression": "subscript_expression",
    "parenthesized_expression": "parenthesized_expression",

    # --- Literals ---
    "interpreted_string_literal": "string_literal",
    "raw_string_literal": "string_literal",
    "int_literal": "number_literal",
    "float_literal": "number_literal",
    
    # --- NEW: Special Literals & Structures ---
    "nil": "null",                              # nil -> null/nullptr
    "true": "boolean_literal",                  # true -> true
    "false": "boolean_literal",                 # false -> false
    "composite_literal": "initializer_list",    # T{...} -> {...}
    "literal_value": "initializer_list",        # Content inside {}
    "keyed_element": "field_initializer",       # key: value -> .key = value
    "literal_element": "assignment_expression",
    
    # --- Structural ---
    "package_clause": "namespace_definition",
    "import_declaration": "using_declaration",  # Approximate mapping
    "comment": "comment",                       # Always good to keep
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

java_to_cpp = {
    "program": "translation_unit",
    "class_declaration": "class_specifier",
    "method_declaration": "function_definition",
    "formal_parameters": "parameter_list",
    "block": "compound_statement",
    "local_variable_declaration": "declaration",
    "integral_type": "primitive_type",
    "variable_declarator": "init_declarator",
    "try_statement": "try_statement",
    "catch_clause": "catch_clause",
    "catch_formal_parameter": "parameter_declaration",
    "catch_type": "type_qualifier",
    "field_access": "field_expression",
    "for_statement": "for_statement",
    "binary_expression": "binary_expression",
    "update_expression": "update_expression",
    "if_statement": "if_statement",
    "parenthesized_expression": "parenthesized_expression",
    "continue_statement": "continue_statement",
    "else": "else_clause",
    "expression_statement": "expression_statement",
    "assignment_expression": "assignment_expression",
    "method_invocation": "call_expression",
    "string_literal": "string_literal",
    "argument_list": "argument_list",
    "constructor_declaration": "function_definition", # C++ coi constructor như hàm          # Root node

    # --- Câu lệnh (Statements) ---
    "return_statement": "return_statement",
    "while_statement": "while_statement",
    "do_statement": "do_statement",
    "switch_statement": "switch_statement",
    "break_statement": "break_statement",
    "case_label": "case_statement",          # Java: case L:, C++: case L:

    # --- Biểu thức (Expressions) ---
    "object_creation_expression": "new_expression", # new Object()
    "array_access": "subscript_expression",         # arr[i]
    "unary_expression": "unary_expression",         # -a, !b
    "cast_expression": "cast_expression",           # (int)a
    "this": "this",                                 # keyword this

    # --- Kiểu dữ liệu (Types) ---
    "floating_point_type": "primitive_type", # float, double
    "boolean_type": "primitive_type",        # boolean
    "void_type": "primitive_type",           # void
    "array_type": "array_declarator",        # int[] -> int[] (Lưu ý: cấu trúc cây khác nhau nhiều)

    # --- Literals ---
    "decimal_integer_literal": "number_literal",
    "true": "true",                          # Node type là boolean_literal hoặc true
    "false": "false",
    "null_literal": "null",                  # hoặc nullptr trong C++ hiện đại
    "character_literal": "char_literal",     # 'c'
}

def replace_java_to_cpp(code: str) -> str:
    """
    Replace Java-specific syntax elements with C++ equivalents in the source code.
    """
    for java_node, cpp_node in java_to_cpp.items():
        # Regex: match Java node names and replace with C++ equivalents
        pattern = rf'({java_node})'
        code = re.sub(pattern, f'{cpp_node}', code)
    return code

@dataclass
class ASTNodeData:
    
    node_id: str  
    node_type: str  
    text: str  
    start_byte: int
    end_byte: int
    parent_id: Optional[str] = None  
    children_ids: List[str] = field(default_factory=list)  
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "text": self.text,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
        }


@dataclass
class CFGNodeData:
    """Represents a CFG node with attached AST subtree in the CPG structure"""
    
    cfg_node_id: int  # ID from the original CFG
    node_type: str  # Type of CFG node (ENTRY, EXIT, STATEMENT, etc.)
    source_text: str  # Source code text
    successors: List[int] = field(default_factory=list)  # CFG successor node IDs
    predecessors: List[int] = field(default_factory=list)  # CFG predecessor node IDs
    edge_labels: Dict[int, str] = field(default_factory=dict)  # Labels on CFG edges
    ast_root_id: Optional[str] = None  # ID of the root AST node in this cluster
    metadata: Dict[str, Any] = field(default_factory=dict)  # Variable defs/uses/calls
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cfg_node_id": self.cfg_node_id,
            "node_type": self.node_type,
            "source_text": self.source_text,
            "successors": self.successors,
            "predecessors": self.predecessors,
            "edge_labels": self.edge_labels,
            "ast_root_id": self.ast_root_id,
            "metadata": self.metadata,
        }


@dataclass
class DFGEdgeData:
    
    source_id: int  # CFG node ID where variable is defined
    target_id: int  # CFG node ID where variable is used
    variables: Set[str] = field(default_factory=set)  # Variables flowing on this edge
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "variables": sorted(list(self.variables)),
        }


class CPG:
    def __init__(self, show_only_named: bool = True):
        self.cfg_nodes: Dict[int, CFGNodeData] = {}
        self.ast_nodes: Dict[str, ASTNodeData] = {}
        self.dfg_edges: List[DFGEdgeData] = []
        self.entry_node_ids: List[int] = []
        self.exit_node_ids: List[int] = []
        self.function_name: Optional[str] = None
        self.show_only_named = show_only_named
        self.has_errors: bool = False
        self.error_nodes: List = []
    
    def build_from_analysis(
        self, 
        cfg: CFG, 
        def_use_result: Optional[DefUseResult] = None
    ) -> 'CPG':
       
        self.function_name = cfg.function_name
        self.entry_node_ids = cfg.entry_node_ids.copy()
        self.exit_node_ids = cfg.exit_node_ids.copy()
        
        # Build CFG nodes with AST subtrees
        for node_id, cfg_node in cfg.nodes.items():
            cfg_node_data = self._build_cfg_node(cfg_node)
            self.cfg_nodes[node_id] = cfg_node_data
            
            # Build AST subtree if AST node exists
            if cfg_node.ast_node is not None:
                ast_root_id = self._build_ast_subtree(
                    cfg_node.ast_node, 
                    cfg_node_id=node_id
                )
                cfg_node_data.ast_root_id = ast_root_id
        
        # Build DFG edges from def-use chains
        if def_use_result is not None:
            self._build_dfg_edges(def_use_result)
        
        return self
    
    def _build_cfg_node(self, cfg_node: CFGNode) -> CFGNodeData:
        """Convert a CFGNode to CFGNodeData"""
        return CFGNodeData(
            cfg_node_id=cfg_node.id,
            node_type=cfg_node.node_type.name,
            source_text=cfg_node.source_text,
            successors=list(cfg_node.successors),
            predecessors=list(cfg_node.predecessors),
            edge_labels=cfg_node.edge_labels.copy(),
            metadata={
                "function_calls": cfg_node.metadata.function_calls,
                "variable_definitions": cfg_node.metadata.variable_definitions,
                "variable_uses": cfg_node.metadata.variable_uses,
            }
        )
    
    def _build_ast_subtree(
        self, 
        ts_node: Node, 
        cfg_node_id: int,
        parent_ast_id: Optional[str] = None
    ) -> str:
        """
            ts_node: Tree-sitter AST node
            cfg_node_id: ID of the CFG node this AST belongs to
            parent_ast_id: ID of the parent AST node in our structure
            Returns: The unique ID assigned to this AST node
        """
        # Create unique ID for this AST node
        ast_node_id = f"{cfg_node_id}__ast_{ts_node.id}"
        
        # Extract node information
        node_type = ts_node.type if hasattr(ts_node, "type") else str(ts_node)
        text = getattr(ts_node, "text", b"") or b""
        try:
            text_str = text.decode("utf-8").strip().replace("\n", " ")
        except Exception:
            text_str = ""
        
        # Create AST node data
        mapped_node_type = replace_java_to_cpp(node_type)
        # with open("/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/cli/debug_dict.txt", "a") as f:
        #     f.write(f"{node_type} : {mapped_node_type} \n")
        ast_node_data = ASTNodeData(
            node_id=ast_node_id,
            node_type=mapped_node_type,
            text=text_str,
            start_byte=ts_node.start_byte,
            end_byte=ts_node.end_byte,
            parent_id=parent_ast_id,
        )
        
        # Process children
        child_nodes = [
            c for c in getattr(ts_node, "children", [])
            if not self.show_only_named or getattr(c, "is_named", False)
        ]
        
        for child in child_nodes:
            child_id = self._build_ast_subtree(child, cfg_node_id, ast_node_id)
            ast_node_data.children_ids.append(child_id)
        
        self.ast_nodes[ast_node_id] = ast_node_data
        return ast_node_id
    
    def _build_dfg_edges(self, def_use_result: DefUseResult) -> None:
        # Group edges by (source, target) pair
        edge_map: Dict[tuple[int, int], Set[str]] = {}
        
        for var_name, chains in def_use_result.chains.items():
            for chain in chains:
                for use in chain.uses:
                    key = (chain.definition, use)
                    if key not in edge_map:
                        edge_map[key] = set()
                    edge_map[key].add(var_name)
        
        # Convert to DFGEdgeData objects
        for (source_id, target_id), variables in edge_map.items():
            self.dfg_edges.append(
                DFGEdgeData(
                    source_id=source_id,
                    target_id=target_id,
                    variables=variables
                )
            )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_name": self.function_name,
            "entry_node_ids": self.entry_node_ids,
            "exit_node_ids": self.exit_node_ids,
            "cfg_nodes": {
                node_id: node_data.to_dict() 
                for node_id, node_data in self.cfg_nodes.items()
            },
            "ast_nodes": {
                node_id: node_data.to_dict() 
                for node_id, node_data in self.ast_nodes.items()
            },
            "dfg_edges": [edge.to_dict() for edge in self.dfg_edges],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CPG':
        cpg = cls()
        cpg.function_name = data.get("function_name")
        cpg.entry_node_ids = data.get("entry_node_ids", [])
        cpg.exit_node_ids = data.get("exit_node_ids", [])
        
        # Reconstruct CFG nodes
        for node_id_str, node_dict in data.get("cfg_nodes", {}).items():
            node_id = int(node_id_str)
            cpg.cfg_nodes[node_id] = CFGNodeData(
                cfg_node_id=node_dict["cfg_node_id"],
                node_type=node_dict["node_type"],
                source_text=node_dict["source_text"],
                successors=node_dict.get("successors", []),
                predecessors=node_dict.get("predecessors", []),
                edge_labels=node_dict.get("edge_labels", {}),
                ast_root_id=node_dict.get("ast_root_id"),
                metadata=node_dict.get("metadata", {}),
            )
        
        # Reconstruct AST nodes
        for node_id, node_dict in data.get("ast_nodes", {}).items():
            cpg.ast_nodes[node_id] = ASTNodeData(
                node_id=node_dict["node_id"],
                node_type=node_dict["node_type"],
                text=node_dict["text"],
                start_byte=node_dict["start_byte"],
                end_byte=node_dict["end_byte"],
                parent_id=node_dict.get("parent_id"),
                children_ids=node_dict.get("children_ids", []),
            )
        
        # Reconstruct DFG edges
        for edge_dict in data.get("dfg_edges", []):
            cpg.dfg_edges.append(DFGEdgeData(
                source_id=edge_dict["source_id"],
                target_id=edge_dict["target_id"],
                variables=set(edge_dict.get("variables", [])),
            ))
        
        return cpg
    
    def save_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def load_json(cls, json_string: str) -> 'CPG':
        data = json.loads(json_string)
        return cls.from_dict(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        total_cfg_edges = sum(len(node.successors) for node in self.cfg_nodes.values())
        
        return {
            "function_name": self.function_name,
            "num_cfg_nodes": len(self.cfg_nodes),
            "num_cfg_edges": total_cfg_edges,
            "num_ast_nodes": len(self.ast_nodes),
            "num_dfg_edges": len(self.dfg_edges),
            "entry_nodes": self.entry_node_ids,
            "exit_nodes": self.exit_node_ids,
        }
    
    def get_cfg_node(self, node_id: int) -> Optional[CFGNodeData]:
        """Get CFG node by ID"""
        return self.cfg_nodes.get(node_id)
    
    def get_ast_subtree_root(self, cfg_node_id: int) -> Optional[ASTNodeData]:
        """Get the root AST node for a given CFG node"""
        cfg_node = self.cfg_nodes.get(cfg_node_id)
        if cfg_node and cfg_node.ast_root_id:
            return self.ast_nodes.get(cfg_node.ast_root_id)
        return None
    
    def get_ast_children(self, ast_node_id: str) -> List[ASTNodeData]:
        """Get all children of an AST node"""
        ast_node = self.ast_nodes.get(ast_node_id)
        if ast_node:
            return [
                self.ast_nodes[child_id] 
                for child_id in ast_node.children_ids 
                if child_id in self.ast_nodes
            ]
        return []
    
    def get_dfg_edges_for_node(self, cfg_node_id: int) -> List[DFGEdgeData]:
        """Get all DFG edges involving a specific CFG node"""
        return [
            edge for edge in self.dfg_edges
            if edge.source_id == cfg_node_id or edge.target_id == cfg_node_id
        ]