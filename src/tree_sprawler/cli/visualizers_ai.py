"""
Visualization classes for AST, CFG, DUC, and CPG graphs.

This module provides visualization capabilities for different program analysis
graph types using matplotlib and graphviz.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx

from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.dataflow.analyses.def_use import DefUseResult

from .constants import (
    AST_EDGE_COLOR,
    CFG_EDGE_COLOR,
    CONDITION_NODE_COLOR,
    DEFAULT_DPI,
    DEFAULT_FIGURE_SIZE,
    DUC_EDGE_COLOR,
    ENTRY_NODE_COLOR,
    EXIT_NODE_COLOR,
    MAX_LABEL_LENGTH,
    REGULAR_NODE_COLOR,
    TRUNCATION_SUFFIX,
    LayoutAlgorithm,
    OutputFormat,
)


class BaseVisualizer(ABC):
    """Base class for all visualizers."""

    def __init__(
        self,
        layout: LayoutAlgorithm = LayoutAlgorithm.DOT,
        output_format: OutputFormat = OutputFormat.PNG,
    ):
        self.layout = layout
        self.output_format = output_format

    @abstractmethod
    def show(self, *args, title: str = "", **kwargs):
        """Display the visualization interactively."""
        pass

    @abstractmethod
    def save(self, *args, output_path: Path, title: str = "", **kwargs):
        """Save the visualization to a file."""
        pass

    def _truncate_label(self, text: str) -> str:
        """Truncate text labels to reasonable length."""
        if len(text) <= MAX_LABEL_LENGTH:
            return text
        return text[: MAX_LABEL_LENGTH - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX

    def _get_layout_pos(self, graph: nx.Graph):
        """Get node positions using the specified layout algorithm.

        Preference order:
        1) graphviz via pydot (dot/neato/etc.) for hierarchical layouts
        2) hierarchical-ish fallback using shell layout
        3) spring/circular layouts as last resort
        """
        prog = {
            LayoutAlgorithm.DOT: "dot",
            LayoutAlgorithm.NEATO: "neato",
            LayoutAlgorithm.FDP: "fdp",
            LayoutAlgorithm.SFDP: "sfdp",
            LayoutAlgorithm.CIRCO: "circo",
            LayoutAlgorithm.TWOPI: "twopi",
        }.get(self.layout, "dot")

        # Provide spacing hints for graphviz
        try:
            graph.graph.setdefault("graph", {})
            # Wider ranks and node separation for less density
            graph.graph["graph"].update(
                {
                    "ranksep": "1.2",
                    "nodesep": "0.6",
                    "overlap": "false",
                    "splines": "spline",
                }
            )
        except Exception:
            pass

        # Try graphviz via pydot first (works with pydot installed)
        try:
            from networkx.drawing.nx_pydot import graphviz_layout  # type: ignore

            return graphviz_layout(graph, prog=prog)
        except Exception:
            pass

        # Fallback: try pygraphviz if available
        try:
            from networkx.drawing.nx_agraph import graphviz_layout  # type: ignore

            return graphviz_layout(graph, prog=prog)
        except Exception:
            pass

        # Hierarchical-ish fallback for directed graphs (like CFG/CPG)
        try:
            if isinstance(graph, (nx.DiGraph, nx.MultiDiGraph)):
                shells = self._create_hierarchical_shells(graph)
                if shells:
                    return dict(nx.shell_layout(graph, nlist=shells))
        except Exception:
            pass

        # Generic fallbacks
        if self.layout == LayoutAlgorithm.CIRCO:
            return dict(nx.circular_layout(graph))
        # Spring with stable seed for consistent results
        return dict(nx.spring_layout(graph, k=3, iterations=150, seed=42))

    def _create_hierarchical_shells(self, graph):
        """Create hierarchical shells for shell layout based on graph structure."""
        if not hasattr(graph, "nodes") or len(graph.nodes) == 0:
            return []

        # Handle directed graphs for CFGs
        if isinstance(graph, nx.DiGraph):
            # Find entry nodes (nodes with no predecessors in directed graph)
            entry_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            if not entry_nodes:
                # If no clear entry, use the first node
                entry_nodes = [list(graph.nodes())[0]]

            visited = set()
            shells = []
            current_level = entry_nodes

            while current_level:
                # Filter out already visited nodes
                current_level = [n for n in current_level if n not in visited]
                if not current_level:
                    break

                shells.append(current_level)
                visited.update(current_level)

                # Get next level (successors of current level)
                next_level = []
                for node in current_level:
                    next_level.extend(
                        [n for n in graph.successors(node) if n not in visited]
                    )

                # Remove duplicates while preserving order
                current_level = list(dict.fromkeys(next_level))
        else:
            # For undirected graphs, use simple level-based grouping
            if not graph.nodes():
                return []

            start_node = list(graph.nodes())[0]
            visited = set()
            shells = []
            current_level = [start_node]

            while current_level:
                current_level = [n for n in current_level if n not in visited]
                if not current_level:
                    break

                shells.append(current_level)
                visited.update(current_level)

                # Get neighbors of current level
                next_level = []
                for node in current_level:
                    next_level.extend(
                        [n for n in graph.neighbors(node) if n not in visited]
                    )

                current_level = list(dict.fromkeys(next_level))

        # Add any remaining nodes to the last shell
        remaining = [n for n in graph.nodes() if n not in visited]
        if remaining:
            shells.append(remaining)

        return [shell for shell in shells if shell]  # Remove empty shells

    def _setup_matplotlib_figure(self, title: str = ""):
        """Set up a matplotlib figure with standard settings."""
        """Set up a matplotlib figure with standard settings."""
        fig, ax = plt.subplots(figsize=DEFAULT_FIGURE_SIZE, dpi=DEFAULT_DPI)
        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.axis("off")
        return fig, ax


class ASTVisualizer(BaseVisualizer):
    """Visualizer for Abstract Syntax Trees."""

    def show(self, ast_root, title: str = ""):
        """Display AST visualization interactively."""
        graph = self._ast_to_networkx(ast_root)
        self._render_graph(graph, title, show=True)

    def save(self, ast_root, output_path: Path, title: str = ""):
        """Save AST visualization to file."""
        if self.output_format == OutputFormat.JSON:
            self._save_ast_json(ast_root, output_path)
        else:
            graph = self._ast_to_networkx(ast_root)
            self._render_graph(graph, title, output_path=output_path)

    def _ast_to_networkx(self, ast_root) -> nx.DiGraph:
        """Convert AST to NetworkX graph."""
        graph = nx.DiGraph()

        def add_node_recursive(node, node_id=0):
            """Recursively add AST nodes to the graph."""
            # Handle both Tree and ASTNode objects
            if hasattr(node, "root_node"):
                # This is a Tree object
                return add_node_recursive(node.root_node, node_id)

            # This is a Node object (tree-sitter node)
            label = node.type if hasattr(node, "type") else str(node)
            graph.add_node(
                node_id,
                label=label,
                node_type=node.type if hasattr(node, "type") else "unknown",
            )

            child_id = node_id * 1000 + 1  # Simple ID generation
            for child in node.children if hasattr(node, "children") else []:
                child_node_id = child_id
                add_node_recursive(child, child_node_id)
                graph.add_edge(node_id, child_node_id)
                child_id += 1

            return node_id

        add_node_recursive(ast_root)
        return graph

    def _save_ast_json(self, ast_root, output_path: Path):
        """Save AST as JSON."""
        # Convert AST to dictionary format
        ast_dict = {
            "type": "ast",
            "root": "placeholder",
        }  # Implement based on AST structure

        with open(output_path, "w") as f:
            json.dump(ast_dict, f, indent=2)

    def _render_graph(
        self,
        graph: nx.DiGraph,
        title: str = "",
        output_path: Optional[Path] = None,
        show: bool = False,
    ):
        """Render the graph using matplotlib."""
        fig, ax = self._setup_matplotlib_figure(title)

        pos = self._get_layout_pos(graph)

        # Draw nodes
        nx.draw_networkx_nodes(
            graph, pos, node_color=REGULAR_NODE_COLOR, node_size=1000, ax=ax
        )

        # Draw edges
        nx.draw_networkx_edges(
            graph, pos, edge_color=AST_EDGE_COLOR, arrows=True, ax=ax
        )

        # Draw labels
        labels = {
            node: self._truncate_label(str(data.get("label", node)))
            for node, data in graph.nodes(data=True)
        }
        nx.draw_networkx_labels(graph, pos, labels, font_size=8, ax=ax)

        if output_path:
            plt.savefig(output_path, dpi=DEFAULT_DPI, bbox_inches="tight")

        if show:
            plt.show()

        if not show:
            plt.close(fig)


class CFGVisualizer(BaseVisualizer):
    """Visualizer for Control Flow Graphs."""

    def show(self, cfg: CFG, title: str = ""):
        """Display CFG visualization interactively."""
        graph = self._cfg_to_networkx(cfg)
        self._render_graph(graph, title, show=True)

    def save(self, cfg: CFG, output_path: Path, title: str = ""):
        """Save CFG visualization to file."""
        if self.output_format == OutputFormat.JSON:
            self._save_cfg_json(cfg, output_path)
        else:
            graph = self._cfg_to_networkx(cfg)
            self._render_graph(graph, title, output_path=output_path)

    def _cfg_to_networkx(self, cfg: CFG) -> nx.DiGraph:
        """Convert CFG to NetworkX graph."""
        graph = nx.DiGraph()

        # Add nodes
        for node_id, node in cfg.nodes.items():
            label = self._get_node_label(node)
            node_type = self._get_node_type(node)
            graph.add_node(node_id, label=label, node_type=node_type)

        # Add edges
        for node_id, node in cfg.nodes.items():
            for successor_id in node.successors:
                edge_label = node.edge_labels.get(successor_id, "")
                graph.add_edge(node_id, successor_id, label=edge_label)

        return graph

    def _get_node_label(self, node) -> str:
        """Get display label for a CFG node."""
        if hasattr(node, "source_text") and node.source_text:
            return self._truncate_label(node.source_text.strip())
        elif hasattr(node, "node_type"):
            return (
                node.node_type.name
                if hasattr(node.node_type, "name")
                else str(node.node_type)
            )
        return f"Node {node.id}"

    def _get_node_type(self, node) -> str:
        """Get the type of a CFG node for coloring."""
        if hasattr(node, "node_type"):
            node_type = (
                node.node_type.name
                if hasattr(node.node_type, "name")
                else str(node.node_type)
            )
            if "ENTRY" in node_type:
                return "entry"
            elif "EXIT" in node_type:
                return "exit"
            elif "CONDITION" in node_type or "IF" in node_type:
                return "condition"
        return "regular"

    def _save_cfg_json(self, cfg: CFG, output_path: Path):
        """Save CFG as JSON."""
        cfg_dict = cfg.to_dict()

        with open(output_path, "w") as f:
            json.dump(cfg_dict, f, indent=2)

    def _render_graph(
        self,
        graph: nx.DiGraph,
        title: str = "",
        output_path: Optional[Path] = None,
        show: bool = False,
    ):
        """Render the CFG graph."""
        fig, ax = self._setup_matplotlib_figure(title)

        pos = self._get_layout_pos(graph)

        # Draw nodes grouped by type to keep typing happy and colors distinct
        entry_nodes = [
            n for n, d in graph.nodes(data=True) if d.get("node_type") == "entry"
        ]
        exit_nodes = [
            n for n, d in graph.nodes(data=True) if d.get("node_type") == "exit"
        ]
        cond_nodes = [
            n for n, d in graph.nodes(data=True) if d.get("node_type") == "condition"
        ]
        regular_nodes = [
            n
            for n, d in graph.nodes(data=True)
            if d.get("node_type") not in {"entry", "exit", "condition"}
        ]

        if regular_nodes:
            nx.draw_networkx_nodes(
                graph,
                pos,
                nodelist=regular_nodes,
                node_color=REGULAR_NODE_COLOR,
                node_size=1500,
                ax=ax,
            )
        if entry_nodes:
            nx.draw_networkx_nodes(
                graph,
                pos,
                nodelist=entry_nodes,
                node_color=ENTRY_NODE_COLOR,
                node_size=1500,
                ax=ax,
            )
        if exit_nodes:
            nx.draw_networkx_nodes(
                graph,
                pos,
                nodelist=exit_nodes,
                node_color=EXIT_NODE_COLOR,
                node_size=1500,
                ax=ax,
            )
        if cond_nodes:
            nx.draw_networkx_nodes(
                graph,
                pos,
                nodelist=cond_nodes,
                node_color=CONDITION_NODE_COLOR,
                node_size=1500,
                ax=ax,
            )

        # Draw edges
        nx.draw_networkx_edges(
            graph, pos, edge_color=CFG_EDGE_COLOR, arrows=True, arrowsize=20, ax=ax
        )

        # Draw node labels
        node_labels = {
            node: data.get("label", str(node)) for node, data in graph.nodes(data=True)
        }
        nx.draw_networkx_labels(graph, pos, node_labels, font_size=8, ax=ax)

        # Draw edge labels
        edge_labels = {
            (u, v): data.get("label", "")
            for u, v, data in graph.edges(data=True)
            if data.get("label")
        }
        if edge_labels:
            nx.draw_networkx_edge_labels(graph, pos, edge_labels, font_size=6, ax=ax)

        if output_path:
            plt.savefig(output_path, dpi=DEFAULT_DPI, bbox_inches="tight")

        if show:
            plt.show()

        if not show:
            plt.close(fig)


class DUCVisualizer(BaseVisualizer):
    """Visualizer for Def-Use Chains."""

    def show(self, cfg: CFG, duc_result: DefUseResult, title: str = ""):
        """Display DUC visualization interactively."""
        graph = self._duc_to_networkx(cfg, duc_result)
        self._render_graph(graph, title, show=True)

    def save(
        self, cfg: CFG, duc_result: DefUseResult, output_path: Path, title: str = ""
    ):
        """Save DUC visualization to file."""
        if self.output_format == OutputFormat.JSON:
            self._save_duc_json(duc_result, output_path)
        else:
            graph = self._duc_to_networkx(cfg, duc_result)
            self._render_graph(graph, title, output_path=output_path)

    def _duc_to_networkx(self, cfg: CFG, duc_result: DefUseResult) -> nx.MultiDiGraph:
        """Convert CFG with DUC edges to NetworkX graph."""
        graph = nx.MultiDiGraph()

        # Add CFG nodes
        for node_id, node in cfg.nodes.items():
            label = self._get_node_label(node)
            graph.add_node(node_id, label=label, graph_type="cfg")

        # Add CFG edges
        for node_id, node in cfg.nodes.items():
            for successor_id in node.successors:
                edge_label = node.edge_labels.get(successor_id, "")
                graph.add_edge(
                    node_id,
                    successor_id,
                    label=edge_label,
                    graph_type="cfg",
                    color=CFG_EDGE_COLOR,
                )

        # Add DUC edges
        duc_dict = duc_result.to_dict()
        for edge in duc_dict["edges"]:
            graph.add_edge(
                edge["source"],
                edge["target"],
                label=edge["label"],
                graph_type="duc",
                color=DUC_EDGE_COLOR,
            )

        return graph

    def _get_node_label(self, node) -> str:
        """Get display label for a node."""
        if hasattr(node, "source_text") and node.source_text:
            return self._truncate_label(node.source_text.strip())
        return f"Node {node.id}"

    def _save_duc_json(self, duc_result: DefUseResult, output_path: Path):
        """Save DUC as JSON."""
        duc_dict = duc_result.to_dict()
        # Add metadata to the dict
        result_dict = {"type": "duc", "edges": duc_dict["edges"]}

        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2)

    def _render_graph(
        self,
        graph: nx.MultiDiGraph,
        title: str = "",
        output_path: Optional[Path] = None,
        show: bool = False,
    ):
        """Render the DUC graph."""
        fig, ax = self._setup_matplotlib_figure(title)

        pos = self._get_layout_pos(graph)

        # Draw nodes
        nx.draw_networkx_nodes(
            graph, pos, node_color=REGULAR_NODE_COLOR, node_size=1500, ax=ax
        )

        # Draw CFG edges
        cfg_edges = [
            (u, v) for u, v, d in graph.edges(data=True) if d.get("graph_type") == "cfg"
        ]
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=cfg_edges,
            edge_color=CFG_EDGE_COLOR,
            arrows=True,
            ax=ax,
        )

        # Draw DUC edges
        duc_edges = [
            (u, v) for u, v, d in graph.edges(data=True) if d.get("graph_type") == "duc"
        ]
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=duc_edges,
            edge_color=DUC_EDGE_COLOR,
            arrows=True,
            style="dashed",
            ax=ax,
        )

        # Draw labels
        node_labels = {
            node: data.get("label", str(node)) for node, data in graph.nodes(data=True)
        }
        nx.draw_networkx_labels(graph, pos, node_labels, font_size=8, ax=ax)

        # Add legend
        try:
            from matplotlib.lines import Line2D

            legend_elements = [
                Line2D([0], [0], color=CFG_EDGE_COLOR, label="Control Flow"),
                Line2D(
                    [0],
                    [0],
                    color=DUC_EDGE_COLOR,
                    linestyle="--",
                    label="Def-Use Chain",
                ),
            ]
            ax.legend(handles=legend_elements, loc="upper right")
        except ImportError:
            # matplotlib.lines not available, skip legend
            pass

        if output_path:
            plt.savefig(output_path, dpi=DEFAULT_DPI, bbox_inches="tight")

        if show:
            plt.show()

        if not show:
            plt.close(fig)


class CPGVisualizer(BaseVisualizer):
    """Visualizer for Code Property Graphs (AST + CFG + DUC)."""

    def show(self, ast_root, cfg: CFG, duc_result: DefUseResult, title: str = ""):
        """Display CPG visualization interactively."""
        graph = self._cpg_to_networkx(ast_root, cfg, duc_result)
        self._render_graph(graph, title, show=True)

    def save(
        self,
        ast_root,
        cfg: CFG,
        duc_result: DefUseResult,
        output_path: Path,
        title: str = "",
    ):
        """Save CPG visualization to file."""
        if self.output_format == OutputFormat.JSON:
            self._save_cpg_json(cfg, duc_result, output_path)
        else:
            graph = self._cpg_to_networkx(ast_root, cfg, duc_result)
            self._render_graph(graph, title, output_path=output_path)

    def _cpg_to_networkx(
        self, ast_root, cfg: CFG, duc_result: DefUseResult
    ) -> nx.MultiDiGraph:
        """Convert AST + CFG + DUC to NetworkX graph.

        - Base: full AST tree (nodes/edges)
        - Overlay: CFG nodes (distinct colors) + CFG edges
        - Overlay: DUC edges (dashed)
        Nodes are namespaced to avoid collisions: 'ast:<id>' and 'cfg:<id>'
        """
        graph = nx.MultiDiGraph()

        # 1) Add AST nodes and edges (as a tree) and build map from TS id -> AST key
        ast_id_map: dict[int, str] = {}

        def add_ast_recursive(ts_node) -> str:
            # Tree-sitter Node has a stable numeric id
            node_key = f"ast_{getattr(ts_node, 'id', id(ts_node))}"
            node_label = getattr(ts_node, "type", str(ts_node))
            node_label = ts_node.text.decode().splitlines()[0][:25]
            graph.add_node(
                node_key,
                label=node_label,
                node_kind="ast",
                is_cfg=False,
            )
            try:
                ast_id_map[int(getattr(ts_node, "id"))] = node_key
            except Exception:
                pass
            # Children edges
            for child in getattr(ts_node, "children", []) or []:
                child_key = add_ast_recursive(child)
                graph.add_edge(
                    node_key, child_key, graph_type="ast", color=AST_EDGE_COLOR
                )
            return node_key

        # ast_root may be a Tree or a Node
        if hasattr(ast_root, "root_node"):
            add_ast_recursive(ast_root.root_node)
        else:
            add_ast_recursive(ast_root)

        # 2) Overlay CFG nodes by marking corresponding AST nodes when possible.
        #    If a CFG node doesn't map to an AST node, create a synthetic cfg node.
        def _cfg_node_key_for(cfg_node_id: int, cfg_node) -> str:
            ast_node = getattr(cfg_node, "ast_node", None)
            if ast_node is not None:
                key = ast_id_map.get(int(getattr(ast_node, "id", -1)))
                if key:
                    # mark AST node as CFG overlay
                    graph.nodes[key]["is_cfg"] = True
                    graph.nodes[key]["node_type"] = self._get_cfg_node_type(cfg_node)
                    graph.nodes[key]["cfg_label"] = self._get_node_label(cfg_node)
                    return key
            # fallback synthetic node
            synth_key = f"cfg_{cfg_node_id}"
            graph.add_node(
                synth_key,
                label=self._get_node_label(cfg_node),
                node_kind="cfg",
                node_type=self._get_cfg_node_type(cfg_node),
                is_cfg=True,
            )
            return synth_key

        # Precompute keys for all CFG nodes
        cfg_node_keys: dict[int, str] = {
            nid: _cfg_node_key_for(nid, n) for nid, n in cfg.nodes.items()
        }

        # 3) Add CFG edges
        for node_id, node in cfg.nodes.items():
            for successor_id in node.successors:
                edge_label = node.edge_labels.get(successor_id, "")
                src = cfg_node_keys[node_id]
                dst = cfg_node_keys.get(successor_id)
                if dst is None:
                    # Shouldn't happen, but guard anyway
                    dst = _cfg_node_key_for(successor_id, cfg.nodes[successor_id])
                    cfg_node_keys[successor_id] = dst
                graph.add_edge(
                    src,
                    dst,
                    label=edge_label,
                    graph_type="cfg",
                    color=CFG_EDGE_COLOR,
                )

        # 4) Add DUC edges (between CFG nodes)
        duc_dict = duc_result.to_dict()
        for edge in duc_dict.get("edges", []):
            src = cfg_node_keys.get(edge["source"])
            if src is None:
                src = _cfg_node_key_for(edge["source"], cfg.nodes[edge["source"]])
                cfg_node_keys[edge["source"]] = src
            dst = cfg_node_keys.get(edge["target"])
            if dst is None:
                dst = _cfg_node_key_for(edge["target"], cfg.nodes[edge["target"]])
                cfg_node_keys[edge["target"]] = dst
            graph.add_edge(
                src,
                dst,
                label=edge.get("label", ""),
                graph_type="duc",
                color=DUC_EDGE_COLOR,
            )

        return graph

    def _get_cfg_node_type(self, node) -> str:
        """Mirror CFGVisualizer node-type classification for coloring."""
        if hasattr(node, "node_type"):
            nt = (
                node.node_type.name
                if hasattr(node.node_type, "name")
                else str(node.node_type)
            )
            if "ENTRY" in nt:
                return "entry"
            if "EXIT" in nt:
                return "exit"
            if "CONDITION" in nt or "IF" in nt:
                return "condition"
        return "regular"

    def _get_node_label(self, node) -> str:
        """Get display label for a node."""
        if hasattr(node, "source_text") and node.source_text:
            return self._truncate_label(node.source_text.strip())
        return f"Node {node.id}"

    def _save_cpg_json(self, cfg: CFG, duc_result: DefUseResult, output_path: Path):
        """Save CPG as JSON."""
        # Combine CFG and DUC data
        cfg_nodes = {
            str(node_id): {
                "id": node_id,
                "label": self._get_node_label(node),
            }
            for node_id, node in cfg.nodes.items()
        }

        cfg_edges = [
            {
                "source": node_id,
                "target": successor_id,
                "label": node.edge_labels.get(successor_id, ""),
                "type": "cfg",
            }
            for node_id, node in cfg.nodes.items()
            for successor_id in node.successors
        ]

        duc_dict = duc_result.to_dict()
        duc_edges = [{**edge, "type": "duc"} for edge in duc_dict["edges"]]

        cpg_dict = {"type": "cpg", "nodes": cfg_nodes, "edges": cfg_edges + duc_edges}

        with open(output_path, "w") as f:
            json.dump(cpg_dict, f, indent=2)

    def _render_graph(
        self,
        graph: nx.MultiDiGraph,
        title: str = "",
        output_path: Optional[Path] = None,
        show: bool = False,
    ):
        """Render the CPG graph with AST base, CFG overlay, and DUC edges."""
        fig, ax = self._setup_matplotlib_figure(title)

        pos = self._get_layout_pos(graph)

        # Separate nodes by kind
        ast_only_nodes = [
            n
            for n, d in graph.nodes(data=True)
            if d.get("node_kind") == "ast" and not d.get("is_cfg")
        ]
        ast_cfg_nodes = [
            n
            for n, d in graph.nodes(data=True)
            if d.get("node_kind") == "ast" and d.get("is_cfg")
        ]
        synthetic_cfg_nodes = [
            n for n, d in graph.nodes(data=True) if d.get("node_kind") == "cfg"
        ]
        cfg_nodes = ast_cfg_nodes + synthetic_cfg_nodes

        # Draw AST nodes (smaller)
        if ast_only_nodes:
            nx.draw_networkx_nodes(
                graph,
                pos,
                nodelist=ast_only_nodes,
                node_color=REGULAR_NODE_COLOR,
                node_size=250,
                ax=ax,
            )

        # Draw CFG nodes (larger, colored by type) in groups
        if cfg_nodes:
            cfg_entry = [
                n for n in cfg_nodes if graph.nodes[n].get("node_type") == "entry"
            ]
            cfg_exit = [
                n for n in cfg_nodes if graph.nodes[n].get("node_type") == "exit"
            ]
            cfg_cond = [
                n for n in cfg_nodes if graph.nodes[n].get("node_type") == "condition"
            ]
            cfg_reg = [
                n
                for n in cfg_nodes
                if graph.nodes[n].get("node_type") not in {"entry", "exit", "condition"}
            ]

            if cfg_reg:
                nx.draw_networkx_nodes(
                    graph,
                    pos,
                    nodelist=cfg_reg,
                    node_color=REGULAR_NODE_COLOR,
                    node_size=1200,
                    ax=ax,
                )
            if cfg_entry:
                nx.draw_networkx_nodes(
                    graph,
                    pos,
                    nodelist=cfg_entry,
                    node_color=ENTRY_NODE_COLOR,
                    node_size=1200,
                    ax=ax,
                )
            if cfg_exit:
                nx.draw_networkx_nodes(
                    graph,
                    pos,
                    nodelist=cfg_exit,
                    node_color=EXIT_NODE_COLOR,
                    node_size=1200,
                    ax=ax,
                )
            if cfg_cond:
                nx.draw_networkx_nodes(
                    graph,
                    pos,
                    nodelist=cfg_cond,
                    node_color=CONDITION_NODE_COLOR,
                    node_size=1200,
                    ax=ax,
                )

        # Draw edges by type
        ast_edges = [
            (u, v) for u, v, d in graph.edges(data=True) if d.get("graph_type") == "ast"
        ]
        cfg_edges = [
            (u, v) for u, v, d in graph.edges(data=True) if d.get("graph_type") == "cfg"
        ]
        duc_edges = [
            (u, v) for u, v, d in graph.edges(data=True) if d.get("graph_type") == "duc"
        ]

        if ast_edges:
            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=ast_edges,
                edge_color=AST_EDGE_COLOR,
                width=0.6,
                alpha=0.3,
                arrows=False,
                ax=ax,
            )

        if cfg_edges:
            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=cfg_edges,
                edge_color=CFG_EDGE_COLOR,
                width=1.5,
                arrows=True,
                ax=ax,
            )

        if duc_edges:
            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=duc_edges,
                edge_color=DUC_EDGE_COLOR,
                width=1.2,
                arrows=True,
                style="dashed",
                ax=ax,
            )

        # Draw labels: small labels for AST-only nodes; readable labels for CFG nodes
        # AST-only labels
        ast_labels = {n: graph.nodes[n].get("label", str(n)) for n in ast_only_nodes}
        if ast_labels:
            nx.draw_networkx_labels(graph, pos, ast_labels, font_size=6, ax=ax)

        # CFG labels
        cfg_labels = {}
        for n in cfg_nodes:
            nd = graph.nodes[n]
            lbl = nd.get("cfg_label") or nd.get("label") or str(n)
            cfg_labels[n] = lbl
        if cfg_labels:
            nx.draw_networkx_labels(graph, pos, cfg_labels, font_size=8, ax=ax)

        # Add legend
        try:
            from matplotlib.lines import Line2D

            legend_elements = [
                Line2D([0], [0], color=AST_EDGE_COLOR, label="AST"),
                Line2D([0], [0], color=CFG_EDGE_COLOR, label="Control Flow"),
                Line2D(
                    [0],
                    [0],
                    color=DUC_EDGE_COLOR,
                    linestyle="--",
                    label="Def-Use Chain",
                ),
            ]
            ax.legend(handles=legend_elements, loc="upper right")
        except ImportError:
            pass

        if output_path:
            plt.savefig(output_path, dpi=DEFAULT_DPI, bbox_inches="tight")
        if show:
            plt.show()
        if not show:
            plt.close(fig)
