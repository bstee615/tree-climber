import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { useState, useRef, forwardRef, useImperativeHandle } from 'react';

cytoscape.use(dagre);

// API endpoint URL
const API_BASE_URL = 'http://localhost:8001';

// Type definitions
interface CFGNode {
  id: number;
  node_type: string;
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

interface GraphRef {
  updateGraph: (code: string, language: string) => Promise<void>;
}

// Constants for graph styling
const CYTOSCAPE_STYLE = [
  {
    selector: 'node',
    style: {
      'background-color': '#666',
      'label': 'data(label)',
      'text-wrap': 'wrap',
      'text-max-width': '120px',
      'width': '140px',
      'height': '80px',
      'color': '#fff',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': '10px',
      'font-family': 'monospace',
      'border-width': '2px',
      'border-color': '#333',
      'shape': 'round-rectangle',
      'padding': '5px'
    }
  },
  {
    selector: 'node[nodeType = "ENTRY"]',
    style: {
      'background-color': '#4CAF50',
      'border-color': '#2E7D32'
    }
  },
  {
    selector: 'node[nodeType = "EXIT"]',
    style: {
      'background-color': '#F44336',
      'border-color': '#C62828'
    }
  },
  {
    selector: 'node[nodeType = "CONDITION"]',
    style: {
      'background-color': '#FF9800',
      'border-color': '#E65100',
      'shape': 'diamond'
    }
  },
  {
    selector: 'node[nodeType = "LOOP_HEADER"]',
    style: {
      'background-color': '#9C27B0',
      'border-color': '#6A1B9A'
    }
  },
  {
    selector: 'node[nodeType = "RETURN"]',
    style: {
      'background-color': '#2196F3',
      'border-color': '#1565C0'
    }
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#999',
      'target-arrow-color': '#999',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-size': '8px',
      'color': '#333',
      'text-background-color': '#fff',
      'text-background-opacity': 0.8,
      'text-background-padding': '2px'
    }
  },
  {
    selector: ':selected',
    style: {
      'border-width': '3px',
      'border-color': '#FFD700',
      'background-color': '#FFF8DC'
    }
  }
];

const Graph = forwardRef<GraphRef>((_props, ref) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [elements, setElements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasGraph, setHasGraph] = useState(false);
  const cyRef = useRef<cytoscape.Core | null>(null);

  // Convert CFG data to Cytoscape elements
  const convertCFGToElements = (cfgData: CFGData) => {
    const nodes = Object.values(cfgData.nodes).map(node => {
      // Format the label with better text wrapping
      let sourceText = node.source_text || '';
      
      // Truncate very long source text
      if (sourceText.length > 50) {
        sourceText = sourceText.substring(0, 47) + '...';
      }
      
      // Clean up whitespace and newlines
      sourceText = sourceText.replace(/\s+/g, ' ').trim();
      
      // Format the label
      const label = sourceText 
        ? `${node.node_type}\n${sourceText}`
        : node.node_type;

      return {
        data: {
          id: node.id.toString(),
          label: label,
          nodeType: node.node_type,
          sourceText: node.source_text,
        }
      };
    });

    const edges: any[] = [];
    Object.values(cfgData.nodes).forEach(node => {
      node.successors.forEach(successorId => {
        const label = node.edge_labels[successorId] || '';
        edges.push({
          data: {
            id: `${node.id}-${successorId}`,
            source: node.id.toString(),
            target: successorId.toString(),
            label: label,
          }
        });
      });
    });

    return [...nodes, ...edges];
  };

  // API call to parse code and get CFG
  const parseCode = async (code: string, language: string): Promise<CFGData> => {
    const response = await fetch(`${API_BASE_URL}/parse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        source_code: code,
        language: language,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error || 'Failed to parse code');
    }

    return result.cfg;
  };

  // Update graph with new code
  const updateGraph = async (code: string, language: string = 'c') => {
    if (!code.trim()) {
      setElements([]);
      setHasGraph(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const cfgData = await parseCode(code, language);
      const newElements = convertCFGToElements(cfgData);
      setElements(newElements);
      setHasGraph(true);
      
      // Apply layout after elements are updated
      setTimeout(() => {
        if (cyRef.current) {
          cyRef.current.layout({ 
            name: 'dagre',
            rankSep: 100,
            nodeSep: 80,
            ranker: 'tight-tree'
          } as any).run();
        }
      }, 100);
    } catch (err) {
      console.error('Error parsing code:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setElements([]);
      setHasGraph(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    updateGraph,
  }));

  const handleNodeSelection = (event: cytoscape.EventObject) => {
    const nodeId = event.target.id();
    setSelectedNode(nodeId);
    console.log('Node selected:', nodeId);
  };

  const handleNodeUnselection = () => {
    setSelectedNode(null);
    console.log('Node unselected');
  };

  const selectNodeTwo = () => {
    if (cyRef.current) {
      // Unselect all nodes first
      cyRef.current.nodes().unselect();
      // Select node "two"
      cyRef.current.getElementById('two').select();
    }
  };

  return (
    <div className="container">
      <span style={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: '1em' }}>
        <h2>Graph Visualization</h2>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span>Selected Node: <strong>{selectedNode || 'none'}</strong></span>
          {isLoading && <span>Loading...</span>}
          {error && <span style={{ color: 'red' }}>Error: {error}</span>}
          <button onClick={selectNodeTwo} style={{ marginRight: '10px' }}>
            Select Node Two
          </button>
        </div>
      </span>
      <div className="cytoscape-container">
        {!hasGraph && !isLoading && !error ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '400px', 
            fontSize: '18px', 
            color: '#666' 
          }}>
            Enter code in the editor to see the control flow graph
          </div>
        ) : (
          <CytoscapeComponent
            elements={elements}
            stylesheet={CYTOSCAPE_STYLE}
            // https://stackoverflow.com/a/55872886
            style={{ width: "100%", height: "400px", textAlign: "initial" }}
            cy={(cy) => {
              cyRef.current = cy;

              // Add event listeners for node selection
              cy.on('select', 'node', handleNodeSelection);
              cy.on('unselect', 'node', handleNodeUnselection);

              // Apply layout with more spacing
              cy.layout({ 
                name: 'dagre',
                rankSep: 100,
                nodeSep: 80,
                ranker: 'tight-tree'
              } as any).run();
            }}
          />
        )}
      </div>
    </div>
  );
});

Graph.displayName = 'Graph';

export default Graph;
