from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from tree_sitter import Tree

from tree_sprawler.ast_utils import get_source_text
from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.cfg.visualization import make_node_style
from tree_sprawler.dataflow.analyses.def_use import DefUseResult, DefUseSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
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


def compose_network(options: GraphOptions, data: GraphData) -> Network:
    # Create a new network with base settings
    net = Network(
        height="750px",
        width="100%",
        directed=True,
    )

    # Configure network options
    net.set_options(
        """
    const options = {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08
            },
            "solver": "forceAtlas2Based"
        },
        "interaction": {
            "hover": true,
            "navigationButtons": true,
            "tooltipDelay": 100
        },
        "edges": {
            "smooth": {
                "type": "continuous",
                "forceDirection": "none"
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            }
        }
    }
    """
    )

    # Add nodes and edges based on the options
    if options.show_cfg:
        assert data.cfg is not None, "CFG must be provided when show_cfg is True"
        for node_id, node in data.cfg.nodes.items():
            label = node.source_text
            _, color = make_node_style(node)
            net.add_node(
                str(node_id),
                label=get_source_text(node.ast_node)
                if node.ast_node
                else f"{node.node_type.name} (no AST node)",
                title=label.strip(),
                color=color,
                shape="ellipse",
            )
        for node_id, node in data.cfg.nodes.items():
            for successor in node.successors:
                edge_label = node.get_edge_label(successor) or ""
                net.add_edge(str(node_id), str(successor), label=edge_label)

    if options.show_dataflow:
        assert data.def_use is not None, (
            "Def-Use result must be provided when show_dataflow is True"
        )
        for variable_name, chains in data.def_use.chains.items():
            for chain in chains:
                for use in chain.uses:
                    net.add_edge(
                        str(chain.definition),
                        str(use),
                        label="uses",
                        color="blue",
                        arrows="to",
                    )

    return net


# Handle session state and analysis data
analysis_data = st.session_state.get("analysis_data")
if not st.session_state.get("analysis_data"):
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
    st.session_state.graph = analysis_data

assert isinstance(analysis_data, GraphData), "analysis_data must be initialized"

# Create visualization options in sidebar
st.sidebar.header("Visualization Options")
show_cfg = st.sidebar.checkbox("Show CFG", value=True)
show_dataflow = st.sidebar.checkbox("Show Dataflow", value=False)

# Create the network
net = compose_network(
    options=GraphOptions(
        show_ast=False, show_cfg=show_cfg, show_dataflow=show_dataflow
    ),
    data=analysis_data,
)

# Save and display the network
html_path = Path("temp_network.html")
net.save_graph(str(html_path))
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Display the network in Streamlit
components.html(html_content, height=800)

# Clean up the temporary file
html_path.unlink()

# Display node information on selection
if "selected_node" in st.session_state:
    node_id = st.session_state.selected_node
    if node_id and analysis_data.cfg and node_id in analysis_data.cfg.nodes:
        node = analysis_data.cfg.nodes[node_id]
        st.sidebar.subheader("Node Information")
        st.sidebar.write("Source:", node.source_text)
        st.sidebar.write("Type:", node.node_type.name)
        if node.ast_node:
            st.sidebar.write("AST Node:", get_source_text(node.ast_node))
