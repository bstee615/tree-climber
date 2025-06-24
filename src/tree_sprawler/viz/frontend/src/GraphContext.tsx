import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { DirectedGraph } from 'graphology';
import type { Attributes } from 'graphology-types';

// Type definitions for our graph data
interface CFGNode {
  id: number;
  node_type: string;
  start_index: number | null;
  end_index: number | null;
  source_text: string;
  successors: number[];
  predecessors: number[];
  edge_labels: { [key: number]: string };
  metadata: {
    function_calls: string[];
    variable_definitions: string[];
    variable_uses: string[];
  };
}

interface CFGData {
  function_name: string | null;
  entry_node_ids: number[];
  exit_node_ids: number[];
  nodes: { [key: number]: CFGNode };
}

// Node attributes for Graphology
interface NodeAttributes extends Attributes {
  node_type: string;
  start_index: number | null;
  end_index: number | null;
  source_text: string;
  metadata: {
    function_calls: string[];
    variable_definitions: string[];
    variable_uses: string[];
  };
}

// Edge attributes for Graphology
interface EdgeAttributes extends Attributes {
  label: string;
}

// Context state type
interface GraphContextState {
  graphologyGraph: DirectedGraph<NodeAttributes, EdgeAttributes> | null;
  cfgData: CFGData | null;
  currentLanguage: string;
  setGraphData: (cfgData: CFGData, language: string) => void;
  getNodeById: (nodeId: number) => CFGNode | null;
  getNodesInRange: (startIndex: number, endIndex: number) => CFGNode[];
  // Utility functions for graph operations
  getNodeNeighbors: (nodeId: string) => string[];
  getNodeAttribute: (nodeId: string, attribute: keyof NodeAttributes) => any;
  getAllNodes: () => string[];
  getAllEdges: () => Array<{ source: string; target: string; attributes: EdgeAttributes }>;
}

// Create the context
const GraphContext = createContext<GraphContextState | undefined>(undefined);

// Provider component
export const GraphProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [graphologyGraph, setGraphologyGraph] = useState<DirectedGraph<NodeAttributes, EdgeAttributes> | null>(null);
  const [cfgData, setCfgData] = useState<CFGData | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState<string>('c');

  const setGraphData = (newCfgData: CFGData, language: string) => {
    setCfgData(newCfgData);
    setCurrentLanguage(language);
    
    // Create new Graphology graph
    const graph = new DirectedGraph<NodeAttributes, EdgeAttributes>();
    
    // Add nodes to the graph
    Object.values(newCfgData.nodes).forEach(node => {
      graph.addNode(node.id.toString(), {
        node_type: node.node_type,
        start_index: node.start_index,
        end_index: node.end_index,
        source_text: node.source_text,
        metadata: node.metadata,
      });
    });
    
    // Add edges to the graph
    Object.values(newCfgData.nodes).forEach(node => {
      node.successors.forEach(successorId => {
        const edgeLabel = node.edge_labels[successorId] || '';
        graph.addEdge(node.id.toString(), successorId.toString(), {
          label: edgeLabel,
        });
      });
    });
    
    setGraphologyGraph(graph);
  };

  const getNodeById = (nodeId: number): CFGNode | null => {
    if (!cfgData) return null;
    return cfgData.nodes[nodeId] || null;
  };

  const getNodesInRange = (startIndex: number, endIndex: number): CFGNode[] => {
    if (!cfgData) return [];
    
    // TODO: This is a simplified implementation - in a real scenario, you'd need
    // to map source code positions to CFG nodes more precisely based on the
    // CFG builder's source position metadata
    
    // For now, return all nodes that have source text within the range
    // This will need to be enhanced with proper source mapping
    return Object.values(cfgData.nodes).filter(node => {
      // Placeholder implementation - would need actual source position mapping
      // Parameters startIndex and endIndex would be used for proper range checking
      const hasSourceText = node.source_text && node.source_text.length > 0;
      const isInRange = startIndex <= endIndex; // Basic range validation
      return hasSourceText && isInRange;
    });
  };

  const getNodeNeighbors = (nodeId: string): string[] => {
    if (!graphologyGraph) return [];
    try {
      return graphologyGraph.neighbors(nodeId);
    } catch {
      return [];
    }
  };

  const getNodeAttribute = (nodeId: string, attribute: keyof NodeAttributes): any => {
    if (!graphologyGraph) return null;
    try {
      return graphologyGraph.getNodeAttribute(nodeId, attribute);
    } catch {
      return null;
    }
  };

  const getAllNodes = (): string[] => {
    if (!graphologyGraph) return [];
    return graphologyGraph.nodes();
  };

  const getAllEdges = (): Array<{ source: string; target: string; attributes: EdgeAttributes }> => {
    if (!graphologyGraph) return [];
    return graphologyGraph.mapEdges((_edge, attributes, source, target) => ({
      source,
      target,
      attributes,
    }));
  };

  const contextValue: GraphContextState = {
    graphologyGraph,
    cfgData,
    currentLanguage,
    setGraphData,
    getNodeById,
    getNodesInRange,
    getNodeNeighbors,
    getNodeAttribute,
    getAllNodes,
    getAllEdges,
  };

  return (
    <GraphContext.Provider value={contextValue}>
      {children}
    </GraphContext.Provider>
  );
};

// Hook to use the graph context
export const useGraph = (): GraphContextState => {
  const context = useContext(GraphContext);
  if (context === undefined) {
    throw new Error('useGraph must be used within a GraphProvider');
  }
  return context;
};

// Export types for use in other components
export type { CFGNode, CFGData, NodeAttributes, EdgeAttributes };

// Add a callback ref for selecting nodes in Cytoscape
let selectGraphNode: ((nodeId?: string) => void) | null = null;

function setSelectGraphNodeCallback(cb: (nodeId?: string) => void) {
  selectGraphNode = cb;
}

function selectGraphNodeById(nodeId?: string) {
  if (selectGraphNode) selectGraphNode(nodeId);
}

export { setSelectGraphNodeCallback, selectGraphNodeById };

// Allow Editor to register a callback for node selection
let onGraphNodeSelect: ((nodeId?: string) => void) | null = null;

function setOnGraphNodeSelectCallback(cb: (nodeId?: string) => void) {
  onGraphNodeSelect = cb;
}

function notifyGraphNodeSelected(nodeId?: string) {
  if (onGraphNodeSelect) onGraphNodeSelect(nodeId);
}

export { setOnGraphNodeSelectCallback, notifyGraphNodeSelected };
