from dataclasses import dataclass
from typing import Optional

import streamlit
from streamlit_agraph import Config, Edge, Node, agraph
from tree_sitter import Tree

from tree_sprawler.ast_utils import get_source_text
from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.cfg.visualization import make_node_label, make_node_style
from tree_sprawler.dataflow.analyses.def_use import DefUseResult, DefUseSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_sprawler.dataflow.dataflow_types import DataflowResult
from tree_sprawler.dataflow.solver import RoundRobinSolver


@dataclass
class GraphOptions:
    """Options for graph visualization."""

    show_ast: bool
    show_cfg: bool
    show_dataflow: bool


@dataclass
class GraphData:
    """Data required to compose the graph."""

    tree: Optional[Tree] = None
    cfg: Optional[CFG] = None
    def_use: Optional[DefUseResult] = None


def compose_graph(
    options: GraphOptions, data: GraphData
) -> tuple[list[Node], list[Edge]]:
    nodes = []
    edges = []
    # Add AST nodes and edges
    if options.show_ast:
        assert data.tree is not None, "AST tree must be provided when show_ast is True"
        # TODO implement
    if options.show_cfg:
        assert data.cfg is not None, "CFG must be provided when show_cfg is True"
        for node_id, node in data.cfg.nodes.items():
            # label = make_node_label(node)
            label = node.source_text
            shape, color = make_node_style(node)
            shape = "ellipse"
            nodes.append(
                Node(
                    id=str(node_id),
                    title=label.strip(),
                    shape=shape,
                    color=color,
                    label=get_source_text(node.ast_node)
                    if node.ast_node
                    else f"{node.node_type.name} (no AST node)",
                )
            )
            for successor in node.successors:
                edges.append(
                    Edge(
                        source=str(node_id),
                        target=str(successor),
                        label=node.get_edge_label(successor) or None,
                    )
                )
    if options.show_dataflow:
        assert data.def_use is not None, (
            "Def-Use result must be provided when show_dataflow is True"
        )
        for variable_name, chains in data.def_use.chains.items():
            for chain in chains:
                # Link CFG nodes with dataflow facts in a different color
                for use in chain.uses:
                    edges.append(
                        Edge(
                            source=str(chain.definition),
                            target=str(use),
                            label="uses",
                            color="blue",
                        )
                    )

    # Example:
    # nodes.append(
    #     Node(
    #         id="Spiderman",
    #         label="Peter Parker",
    #         size=25,
    #         shape="circularImage",
    #         image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_spiderman.png",
    #     )
    # )  # includes **kwargs
    # nodes.append(
    #     Node(
    #         id="Captain_Marvel",
    #         size=25,
    #         shape="circularImage",
    #         image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_captainmarvel.png",
    #     )
    # )
    # edges.append(
    #     Edge(
    #         source="Captain_Marvel",
    #         label="friend_of",
    #         target="Spiderman",
    #         # **kwargs
    #     )
    # )
    return nodes, edges


analysis_data = streamlit.session_state.get("analysis_data")
if not streamlit.session_state.get("analysis_data"):
    # Example C code snippet for testing
    c_code = """
    int example_function(int n) {
        int result = 0;
        
        // Test if-else statement
        if (n > 0) {
            result = result * 2;
        } else if (n < 0) {
            result = -result;
            print(result);
        }

        if (n == 0) {
            print(result);
        }
    }
    """
    # java_code = """
    # public class Example {
    #     public static int exampleFunction(int n) {
    #         int result = 0;

    #         // Test if-else statement
    #         if (n > 0) {
    #             result = result * 2;
    #         } else if (n < 0) {
    #             result = -result;
    #             System.out.println(result, foo);
    #         }

    #         if (n == 0) {
    #             System.out.println(result);
    #         }
    #         return result;
    #     }
    # }
    # """
    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(c_code)
    # builder = CFGBuilder("java")
    # builder.setup_parser()
    # cfg = builder.build_cfg(java_code)

    # Visualize the CFG
    # visualize_cfg(cfg)

    # Analyze reaching definitions
    problem = ReachingDefinitionsProblem()

    solver = RoundRobinSolver()
    result = solver.solve(cfg, problem)
    # print("Reaching definitions:")
    # print("In facts:")
    # for node_id, facts in result.in_facts.items():
    #     print(f"Node {node_id}:")
    #     for fact in facts:
    #         print(f"\t* {fact}")
    # for node_id, facts in result.out_facts.items():
    #     print(f"Node {node_id}:")
    #     for fact in facts:
    #         print(f"\t* {fact}")

    # Analyze def-use chains
    def_use_analyzer = DefUseSolver()
    def_use_result = def_use_analyzer.solve(cfg, result)
    analysis_data = GraphData(
        # tree=builder.tree,
        tree=None,
        cfg=cfg,
        def_use=def_use_result,
    )
    streamlit.session_state.graph = analysis_data
assert isinstance(analysis_data, GraphData), "analysis_data must be initialized"


nodes, edges = compose_graph(
    options=GraphOptions(show_ast=False, show_cfg=True, show_dataflow=False),
    data=analysis_data,
)

config = Config(
    width=750,
    height=950,
    directed=True,
    physics=True,
    hierarchical=True,
)

return_value = agraph(nodes=nodes, edges=edges, config=config)
