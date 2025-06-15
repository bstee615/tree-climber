# Define a simple dataflow problem (e.g., reaching definitions)
from typing import Iterable, Set

from tree_sprawler.cfg.cfg_types import CFGNode
from tree_sprawler.dataflow.dataflow_types import (
    DataflowFact,
    DataflowInitializer,
    DataflowProblem,
    MeetOperation,
    TransferFunction,
)


class ReachingDefinition(DataflowFact):
    def __init__(self, variable: str, node_id: int):
        self.variable_name = variable
        self.node_id = node_id

    def __repr__(self) -> str:
        return (
            f"ReachingDefinition(variable={self.variable_name}, node_id={self.node_id})"
        )


class Union(MeetOperation):
    def __call__(self, facts: Iterable[frozenset[DataflowFact]]) -> Set[DataflowFact]:
        return set().union(*[set(fact_set) for fact_set in facts])


class ReachingDefinitionsGenKill(TransferFunction):
    def __call__(self, node: CFGNode, in_facts: Set[DataflowFact]) -> Set[DataflowFact]:
        node_id = node.id
        defined_variables = node.variable_definitions if node.ast_node else []
        gen_facts = {
            ReachingDefinition(variable=var, node_id=node_id)
            for var in defined_variables
        }
        kill_facts = {
            fact
            for fact in in_facts
            if isinstance(fact, ReachingDefinition)
            and fact.variable_name in defined_variables
        }

        out_facts = (in_facts - kill_facts) | gen_facts
        # print(
        #     f"Node {node_id}: DEFS = {defined_variables}, GEN = {gen_facts}, KILL = {kill_facts}, OUT = {out_facts}"
        # )
        return out_facts


class Empty(DataflowInitializer):
    def __call__(self, _node: CFGNode) -> Set[DataflowFact]:
        # Initialize with an empty set of facts
        return set()


def ReachingDefinitionsProblem() -> DataflowProblem:
    """Factory function to create a reaching definitions analysis."""
    return DataflowProblem(
        meet=Union(),
        transfer=ReachingDefinitionsGenKill(),
        in_init=Empty(),
        out_init=Empty(),
    )
