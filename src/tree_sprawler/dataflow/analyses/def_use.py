from dataclasses import dataclass
from typing import Dict, List

from tree_sprawler.ast_utils import get_uses
from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.dataflow.analyses.reaching_definitions import ReachingDefinition
from tree_sprawler.dataflow.dataflow_types import DataflowResult


@dataclass
class UseDefChain:
    variable_name: str
    use: int  # Node ID where the variable is used
    definitions: List[int]  # List of node IDs where the variable is defined


class UseDefResult:
    chains: Dict[str, List[UseDefChain]]  # Maps variable names to their def-use chains


@dataclass
class DefUseChain:
    variable_name: str
    definition: int  # Node ID where the variable is defined
    uses: List[int]  # List of node IDs where the variable is used


class DefUseResult:
    chains: Dict[str, List[DefUseChain]]  # Maps variable names to their def-use chains


class UseDefSolver:
    def solve(self, cfg: CFG, dataflow_result: DataflowResult) -> UseDefResult:
        """
        Solve the Use-Def problem for the given Control Flow Graph (CFG).
        Groups uses by node to avoid duplicates.
        """
        result = UseDefResult()
        result.chains = chains = {}

        # First pass: collect all uses per node
        uses_by_node = {}  # Maps node_id -> set of variable names used
        for node_id, node in cfg.nodes.items():
            if not node.ast_node:
                continue  # Skip nodes without AST nodes
            uses_by_node[node_id] = set(get_uses(node.ast_node))

        # Second pass: create chains for each unique use
        for node_id, var_names in uses_by_node.items():
            # Get reaching definitions at this node
            in_at_point = dataflow_result.in_facts[node_id]

            # Create chains for each variable used in this node
            for variable_name in var_names:
                if variable_name not in chains:
                    chains[variable_name] = []

                definitions = [
                    fact.node_id
                    for fact in in_at_point
                    if isinstance(fact, ReachingDefinition)
                    and fact.variable_name == variable_name
                ]

                # Only create a chain if we haven't already for this use
                if not any(chain.use == node_id for chain in chains[variable_name]):
                    chains[variable_name].append(
                        UseDefChain(
                            variable_name=variable_name,
                            use=node_id,
                            definitions=definitions,
                        )
                    )

        return result


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
            for variable_name in get_uses(node.ast_node):
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
                    uses=sorted(list(uses)),  # Convert set to sorted list for consistency
                )
            )

        return result
