from dataclasses import dataclass
from typing import Any, Dict, List

from tree_climber.cfg.visitor import CFG
from tree_climber.dataflow.analyses.reaching_definitions import ReachingDefinition, ParameterAlias
from tree_climber.dataflow.dataflow_types import DataflowResult


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
            uses_by_node[node_id] = set(node.metadata.variable_uses)

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
                
                # Also check for inter-procedural parameter aliases
                alias_definitions = self._find_parameter_aliases(cfg, node_id, variable_name)
                definitions.extend(alias_definitions)

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

    def _find_parameter_aliases(self, cfg: CFG, use_node_id: int, variable_name: str) -> List[int]:
        """Find argument definitions that alias to this parameter use."""
        alias_definitions = []
        
        # Check if this variable use is for a function parameter
        use_node = cfg.nodes[use_node_id]
        if variable_name not in use_node.metadata.variable_uses:
            return alias_definitions
            
        # Find the function entry node that defines this parameter
        parameter_def_node = None
        for node_id, node in cfg.nodes.items():
            if (node.node_type.name == "ENTRY" and 
                variable_name in node.metadata.variable_definitions):
                parameter_def_node = node
                break
        
        if not parameter_def_node:
            return alias_definitions
            
        # Find call sites that call this function
        function_name = parameter_def_node.source_text.strip()
        for node_id, node in cfg.nodes.items():
            if (node.metadata.function_calls and 
                function_name in node.metadata.function_calls and
                node.ast_node):
                
                # Extract arguments from the function call
                from tree_climber.dataflow.analyses.reaching_definitions import extract_function_call_arguments
                call_arguments = extract_function_call_arguments(node.ast_node)
                
                # Map arguments to parameters
                param_index = parameter_def_node.metadata.variable_definitions.index(variable_name)
                if param_index < len(call_arguments):
                    arg_name = call_arguments[param_index]
                    
                    # Find definitions of the argument at the call site
                    for pred_node_id, pred_node in cfg.nodes.items():
                        if (arg_name in pred_node.metadata.variable_definitions and
                            self._reaches_call_site(cfg, pred_node_id, node_id, arg_name)):
                            alias_definitions.append(pred_node_id)
        
        return alias_definitions
    
    def _reaches_call_site(self, cfg: CFG, def_node_id: int, call_node_id: int, variable_name: str) -> bool:
        """Check if a definition reaches a call site without being killed."""
        # Simplified reachability check - in a full implementation, 
        # this would use proper dataflow analysis
        # For now, we'll do a simple check based on node ordering and CFG structure
        
        if def_node_id == call_node_id:
            return False
            
        # Check if there's a path from def_node to call_node
        visited = set()
        stack = [def_node_id]
        
        while stack:
            current = stack.pop()
            if current == call_node_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            
            current_node = cfg.nodes.get(current)
            if current_node:
                # Check if this node redefines the variable (kills the definition)
                if (current != def_node_id and 
                    variable_name in current_node.metadata.variable_definitions):
                    continue  # This path is killed
                    
                # Add successors to explore
                for succ_id in current_node.successors:
                    if succ_id not in visited:
                        stack.append(succ_id)
        
        return False


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
                
                # Also check for inter-procedural parameter aliases
                alias_definitions = self._find_parameter_aliases(cfg, node_id, variable_name)
                definitions.extend(alias_definitions)

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

    def _find_parameter_aliases(self, cfg: CFG, use_node_id: int, variable_name: str) -> List[int]:
        """Find argument definitions that alias to this parameter use."""
        alias_definitions = []
        
        # Check if this variable use is for a function parameter
        use_node = cfg.nodes[use_node_id]
        if variable_name not in use_node.metadata.variable_uses:
            return alias_definitions
            
        # Find the function entry node that defines this parameter
        parameter_def_node = None
        for node_id, node in cfg.nodes.items():
            if (node.node_type.name == "ENTRY" and 
                variable_name in node.metadata.variable_definitions):
                parameter_def_node = node
                break
        
        if not parameter_def_node:
            return alias_definitions
            
        # Find call sites that call this function
        function_name = parameter_def_node.source_text.strip()
        for node_id, node in cfg.nodes.items():
            if (node.metadata.function_calls and 
                function_name in node.metadata.function_calls and
                node.ast_node):
                
                # Extract arguments from the function call
                from tree_climber.dataflow.analyses.reaching_definitions import extract_function_call_arguments
                call_arguments = extract_function_call_arguments(node.ast_node)
                
                # Map arguments to parameters
                param_index = parameter_def_node.metadata.variable_definitions.index(variable_name)
                if param_index < len(call_arguments):
                    arg_name = call_arguments[param_index]
                    
                    # Find definitions of the argument at the call site
                    for pred_node_id, pred_node in cfg.nodes.items():
                        if (arg_name in pred_node.metadata.variable_definitions and
                            self._reaches_call_site(cfg, pred_node_id, node_id, arg_name)):
                            alias_definitions.append(pred_node_id)
        
        return alias_definitions
    
    def _reaches_call_site(self, cfg: CFG, def_node_id: int, call_node_id: int, variable_name: str) -> bool:
        """Check if a definition reaches a call site without being killed."""
        # Simplified reachability check - for now, we'll use a basic heuristic
        if def_node_id == call_node_id:
            return False
            
        # Check if there's a path from def_node to call_node
        visited = set()
        stack = [def_node_id]
        
        while stack:
            current = stack.pop()
            if current == call_node_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            
            current_node = cfg.nodes.get(current)
            if current_node:
                # Check if this node redefines the variable (kills the definition)
                if (current != def_node_id and 
                    variable_name in current_node.metadata.variable_definitions):
                    continue  # This path is killed
                    
                # Add successors to explore
                for succ_id in current_node.successors:
                    if succ_id not in visited:
                        stack.append(succ_id)
        
        return False
