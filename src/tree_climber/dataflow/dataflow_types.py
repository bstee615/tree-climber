import abc
from dataclasses import dataclass
from typing import Iterable, Set

from tree_climber.cfg.cfg_types import CFGNode


class DataflowFact:
    """
    Base class for dataflow facts.
    Each fact should implement __hash__ and __eq__ methods.
    """

    def __hash__(self) -> int:
        return hash(tuple(sorted(vars(self).items(), key=lambda p: p[0])))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and all(
            getattr(self, attr) == getattr(other, attr) for attr in vars(self)
        )

    @abc.abstractmethod
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{k}={v}' for k, v in vars(self).items())})"


class MeetOperation:
    """
    Compute the meet operation for a CFG node.
    """

    def __call__(self, facts: Iterable[frozenset[DataflowFact]]) -> Set[DataflowFact]:
        """
        Combine multiple dataflow facts using a meet operation.
        This is typically a set union or intersection, depending on the problem.
        """
        raise NotImplementedError("Meet operation must be implemented.")


class TransferFunction:
    """
    Compute the transfer function for a CFG node.
    """

    def __call__(self, node: CFGNode, in_facts: Set[DataflowFact]) -> Set[DataflowFact]:
        """
        Apply the transfer function to a node with the given input facts.
        This function should return the output facts for the node.
        """
        raise NotImplementedError("Transfer function must be implemented.")


class DataflowInitializer:
    """
    Initialize the dataflow facts for a node.
    Should return the initial facts for the node.
    """

    def __call__(self, node: CFGNode) -> Set[DataflowFact]:
        """
        Initialize the dataflow facts for a node.
        This function should return the initial facts for the node.
        """
        raise NotImplementedError("Dataflow initializer must be implemented.")


@dataclass
class DataflowProblem:
    """Dataflow problem definition."""

    meet: MeetOperation
    transfer: TransferFunction
    in_init: DataflowInitializer
    out_init: DataflowInitializer


@dataclass
class DataflowResult:
    """Results of solving a dataflow problem."""

    in_facts: dict[int, Set[DataflowFact]]
    out_facts: dict[int, Set[DataflowFact]]
