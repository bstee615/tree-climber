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


def analyze_source_code(source: str, language: str) -> CPG:

    ast_root = _parse_source_string(source, language=language)

    cfg = None
    cfg = _build_cfg(ast_root, language=language)
    def_use_result = None
   
    if cfg is None:
        raise ValueError("CFG is required for dataflow analysis")
        
    def_use_result = _analyze_dataflow(cfg)
    
    cpg = CPG()
    cpg.build_from_analysis(cfg=cfg, def_use_result=def_use_result)
    
    return cpg



def _parse_source_string(source_code: str, language: str) -> Tree:
    """Parse source code string to AST."""
    return parse_source_to_ast(source_code, language)


def _build_cfg(ast_root: Tree, language: str) -> CFG:
    """Build Control Flow Graph from AST."""
    builder = CFGBuilder(language)
    builder.setup_parser()
    return builder.build_cfg(tree=ast_root)


def _analyze_dataflow(cfg: CFG) -> DefUseResult:
    """Perform reaching definitions dataflow analysis."""
    problem = ReachingDefinitionsProblem()
    dataflow_solver = RoundRobinSolver()
    def_use_solver = DefUseSolver()
    return def_use_solver.solve(cfg, dataflow_solver.solve(cfg, problem))
