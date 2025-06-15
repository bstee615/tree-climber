from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterator, List, Set


class DataflowDirection(Enum):
    """Direction of dataflow analysis"""

    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass
class DataflowFact:
    """Represents a fact in dataflow analysis"""

    variable: str
    definition_node: int  # CFG node ID where variable is defined
    use_nodes: Set[int] = field(
        default_factory=set
    )  # CFG node IDs where variable is used
    killed_by: Set[int] = field(
        default_factory=set
    )  # CFG node IDs that kill this definition

    def is_killed_by(self, node_id: int) -> bool:
        """Check if this fact is killed by a given node"""
        return node_id in self.killed_by

    def add_use(self, node_id: int) -> None:
        """Add a use of this variable at the given node"""
        self.use_nodes.add(node_id)

    def add_killer(self, node_id: int) -> None:
        """Add a node that kills this definition"""
        self.killed_by.add(node_id)


@dataclass
class DataflowState:
    """Current state of dataflow analysis at a CFG node"""

    node_id: int
    in_facts: Set[DataflowFact] = field(default_factory=set)
    out_facts: Set[DataflowFact] = field(default_factory=set)

    def add_fact(self, fact: DataflowFact, to_out: bool = False) -> bool:
        """Add a fact to in_facts or out_facts. Returns True if state changed."""
        target = self.out_facts if to_out else self.in_facts
        if fact not in target:
            target.add(fact)
            return True
        return False

    def remove_fact(self, fact: DataflowFact, from_out: bool = False) -> bool:
        """Remove a fact from in_facts or out_facts. Returns True if state changed."""
        target = self.out_facts if from_out else self.in_facts
        if fact in target:
            target.remove(fact)
            return True
        return False

    def get_facts_for_var(
        self, var: str, from_out: bool = False
    ) -> Iterator[DataflowFact]:
        """Get all facts for a given variable"""
        target = self.out_facts if from_out else self.in_facts
        return (fact for fact in target if fact.variable == var)

    def merge_facts(self, other_state: "DataflowState") -> bool:
        """Merge facts from another state into this one's in_facts. Returns True if changed."""
        changed = False
        for fact in other_state.out_facts:
            if fact not in self.in_facts:
                self.in_facts.add(fact)
                changed = True
        return changed


@dataclass
class DefUseChain:
    """Represents a def-use chain for a variable"""

    variable: str
    definition: int  # CFG node ID where variable is defined
    uses: Set[int] = field(
        default_factory=set
    )  # Set of CFG node IDs where variable is used

    def add_use(self, node_id: int) -> None:
        """Add a use of the variable"""
        self.uses.add(node_id)

    def get_uses(self) -> Set[int]:
        """Get all uses of the variable"""
        return self.uses.copy()

    def is_live(self) -> bool:
        """Check if this chain has any uses"""
        return len(self.uses) > 0


@dataclass
class DataflowResult:
    """Results of dataflow analysis"""

    def_use_chains: List[DefUseChain] = field(default_factory=list)
    state_map: Dict[int, DataflowState] = field(
        default_factory=dict
    )  # node_id -> DataflowState

    def add_chain(self, chain: DefUseChain) -> None:
        """Add a def-use chain to the results"""
        self.def_use_chains.append(chain)

    def get_chains_for_var(self, var: str) -> Iterator[DefUseChain]:
        """Get all chains for a given variable"""
        return (chain for chain in self.def_use_chains if chain.variable == var)

    def get_uses_for_def(self, def_node: int) -> Set[int]:
        """Get all uses reached by a definition"""
        uses = set()
        for chain in self.def_use_chains:
            if chain.definition == def_node:
                uses.update(chain.uses)
        return uses
