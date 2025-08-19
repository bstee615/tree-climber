from dataclasses import dataclass
from typing import Any, Dict, List

from tree_climber.cfg.visitor import CFG
from tree_climber.dataflow.analyses.reaching_definitions import ReachingDefinition
from tree_climber.dataflow.dataflow_types import DataflowResult


@dataclass
class DefUseChain:
    variable_name: str
    definition: int  # Node ID where the variable is defined
    uses: List[int]  # List of node IDs where the variable is used


class DefUseResult:
    chains: Dict[str, List[DefUseChain]]  # Maps variable names to their def-use chains

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert the DefUseResult to a dictionary format suitable for JSON serialization.
        """

        edges = []
        for name, chains in self.chains.items():
            for chain in chains:
                for use in chain.uses:
                    edges.append(
                        {
                            "source": chain.definition,
                            "target": use,
                            "label": name,
                        }
                    )

        return dict(
            edges=edges,
        )


class DefUseSolver:
    def solve(self, cfg: CFG, dataflow_result: DataflowResult) -> DefUseResult:
        """
        Solve the Def-Use problem for the given Control Flow Graph (CFG).
        Ensures that there is one chain per definition by merging uses.
        """
        result = DefUseResult()
        result.chains = chains = {}

        # First pass: collect all uses per node and their reaching definitions
        uses_by_def = {}  # Maps (var_name, def_node_id) -> set of use node_ids

        # For each node that has uses
        for node_id, node in cfg.nodes.items():
            if not node.ast_node:
                continue  # Skip nodes without AST nodes

            # For each variable used in this node
            for variable_name in node.metadata.variable_uses:
                # Find all reaching definitions for this use
                in_at_point = dataflow_result.in_facts[node_id]
                definitions = [
                    fact.node_id
                    for fact in in_at_point
                    if isinstance(fact, ReachingDefinition)
                    and fact.variable_name == variable_name
                ]

                # Add this use to each definition's list of uses
                for def_node_id in definitions:
                    key = (variable_name, def_node_id)
                    if key not in uses_by_def:
                        uses_by_def[key] = set()
                    uses_by_def[key].add(node_id)

        # Second pass: create chains from the collected uses
        for (variable_name, def_node_id), uses in uses_by_def.items():
            if variable_name not in chains:
                chains[variable_name] = []

            chains[variable_name].append(
                DefUseChain(
                    variable_name=variable_name,
                    definition=def_node_id,
                    uses=sorted(
                        list(uses)
                    ),  # Convert set to sorted list for consistency
                )
            )

        return result
