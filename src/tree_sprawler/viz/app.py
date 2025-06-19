from dataclasses import dataclass
from typing import List, Optional, Tuple

import networkx as nx
import plotly.graph_objects as go
import streamlit as st
from tree_sitter import Tree

from tree_sprawler.ast_utils import get_source_text
from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.cfg.visualization import make_node_style
from tree_sprawler.dataflow.analyses.def_use import DefUseResult, DefUseSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import ReachingDefinitionsProblem
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
) -> Tuple[List[dict], List[Tuple[str, str, Optional[str], Optional[str]]]]:
    """
    Compose graph data in a format suitable for plotly visualization.
    Returns:
        - List of node dictionaries with attributes
        - List of edge tuples (source, target, label, color)
    """
    nodes = []
    edges = []

    if options.show_ast:
        assert data.tree is not None, "AST tree must be provided when show_ast is True"
        # TODO implement AST visualization

    if options.show_cfg:
        assert data.cfg is not None, "CFG must be provided when show_cfg is True"
        for node_id, node in data.cfg.nodes.items():
            shape, color = make_node_style(node)
            display_label = (
                get_source_text(node.ast_node)
                if node.ast_node
                else f"{node.node_type.name} (no AST node)"
            )

            nodes.append(
                {
                    "id": str(node_id),
                    "label": display_label,
                    "color": color,
                    "shape": shape,
                }
            )

            for successor in node.successors:
                edges.append(
                    (
                        str(node_id),
                        str(successor),
                        node.get_edge_label(successor),
                        None,  # Default color for CFG edges
                    )
                )

    if options.show_dataflow:
        assert data.def_use is not None, (
            "Def-Use result must be provided when show_dataflow is True"
        )
        for variable_name, chains in data.def_use.chains.items():
            for chain in chains:
                for use in chain.uses:
                    edges.append(
                        (
                            str(chain.definition),
                            str(use),
                            "uses",
                            "blue",  # Color for dataflow edges
                        )
                    )

    return nodes, edges


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
    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(c_code)

    # Analyze reaching definitions
    problem = ReachingDefinitionsProblem()
    solver = RoundRobinSolver()
    result = solver.solve(cfg, problem)

    # Analyze def-use chains
    def_use_analyzer = DefUseSolver()
    def_use_result = def_use_analyzer.solve(cfg, result)

    analysis_data = GraphData(
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

nodes, edges = compose_graph(
    options=GraphOptions(
        show_ast="AST" in settings,
        show_cfg="CFG" in settings,
        show_dataflow="Def-Use" in settings,
    ),
    data=analysis_data,
)

# Create a networkx graph for layout
G = nx.DiGraph()

# Add nodes to the graph
for node in nodes:
    G.add_node(node["id"])

# Add edges to the graph
for source, target, label, color in edges:
    G.add_edge(source, target)

# Use networkx's layout algorithm
node_positions = nx.kamada_kawai_layout(G)

# Create separate edge traces for different colors
edge_by_color = {}

for source, target, label, color in edges:
    x0, y0 = node_positions[source]
    x1, y1 = node_positions[target]

    color = color or "gray"
    if color not in edge_by_color:
        edge_by_color[color] = {"x": [], "y": [], "labels": []}

    edge_by_color[color]["x"].extend([x0, x1, None])
    edge_by_color[color]["y"].extend([y0, y1, None])
    edge_by_color[color]["labels"].extend([label or "", None, None])

# Create edge traces for each color
edge_traces = []
for color, data in edge_by_color.items():
    edge_trace = go.Scatter(
        x=data["x"],
        y=data["y"],
        line=dict(width=1.5, color=color),
        hoverinfo="text",
        text=data["labels"],
        mode="lines",
        name=f"{color} edges",
    )
    edge_traces.append(edge_trace)

# Create node trace
node_x = []
node_y = []
node_labels = []
node_colors = []
node_shapes = []

# Map CFG shapes to plotly shapes
shape_map = {
    "ellipse": "circle",
    "box": "square",
    "diamond": "diamond",
}

for node in nodes:
    x, y = node_positions[node["id"]]
    node_x.append(x)
    node_y.append(y)
    node_labels.append(node["label"])
    node_colors.append(node["color"])
    node_shapes.append(shape_map.get(node["shape"], "circle"))

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    hoverinfo="text",
    text=node_labels,
    textposition="bottom center",
    marker=dict(
        color=node_colors,
        size=30,
        line=dict(width=2, color="white"),
        symbol=node_shapes,
    ),
)

# Create the figure with all traces
fig = go.Figure(
    data=[*edge_traces, node_trace],
    layout=go.Layout(
        title="Control Flow Graph",
        showlegend=True,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
        width=800,
        height=800,
    ),
)

# Display the graph in Streamlit
st.plotly_chart(fig, use_container_width=True)
