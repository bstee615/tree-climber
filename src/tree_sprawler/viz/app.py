import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import streamlit as st
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

sys.path.append(str(Path(__file__).parent.joinpath("streamlit-monaco").resolve()))
from streamlit_monaco.render import render_component as st_monaco


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

    return nodes, edges


# Example C code snippet for testing
code = """int example_function(int n) {
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
# code = """
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

analysis_data = st.session_state.get("analysis_data")
if not st.session_state.get("analysis_data"):
    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(code)

    # Analyze reaching definitions
    problem = ReachingDefinitionsProblem()

    solver = RoundRobinSolver()
    result = solver.solve(cfg, problem)

    # Analyze def-use chains
    def_use_analyzer = DefUseSolver()
    def_use_result = def_use_analyzer.solve(cfg, result)
    analysis_data = GraphData(
        # tree=builder.tree,
        tree=None,
        cfg=cfg,
        def_use=def_use_result,
    )
    st.session_state.graph = analysis_data
assert isinstance(analysis_data, GraphData), "analysis_data must be initialized"

st.title("Tree-Sprawler Graph")

with st.sidebar:
    st.title("Graph Visualization Options")
    settings = st.pills(
        "Layers", ["AST", "CFG", "Def-Use"], default=["CFG"], selection_mode="multi"
    )

st.set_page_config(layout="wide", page_title="Tree-Sprawler Graph Visualization")

nodes, edges = compose_graph(
    options=GraphOptions(
        show_ast="AST" in settings,
        show_cfg="CFG" in settings,
        show_dataflow="Def-Use" in settings,
    ),
    data=analysis_data,
)

if st.button("🔍 Highlight node 6"):
    selected_button = "6"
else:
    selected_button = None

col1, col2 = st.columns(2)

with col1:
    container = st.container(border=True)
    with container:
        content = st_monaco(
            height="200px",
            value=code,
            language="python",
            lineNumbers=True,
            minimap=True,
            theme="vs-light",
        )
        st.write("## Selection")
        st.write(content)
        # TODO:
        # On cursor change, highlight the corresponding node in the graph
        # On selection, highlight the corresponding nodes in the graph
        # Do this by parsing to AST, matching to CFG nodes, and updating the graph styling

if selected_button:
    st.write(f"🔵 Highlighting node **{selected_button}**")

    # Update node colors
    for n in nodes:
        if n.id == selected_button:
            n.color = "#FF4500"
            # TODO: Set highlight styling correctly

with col2:
    with st.container(border=True):
        config = Config(
            width=500,
            directed=True,
            physics=True,
            hierarchical=True,
            interaction=dict(
                dragNodes=False,
                dragView=False,
                zoomView=False,
            ),
        )
        # TODO: Store zoom coordinates in session state
        selected_node = agraph(nodes=nodes, edges=edges, config=config)
        st.write("## Selected node:")
        st.write(selected_node)
