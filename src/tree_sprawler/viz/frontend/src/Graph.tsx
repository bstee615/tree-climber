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
      'height': '40px',
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
      'border-color': '#FF6B35',
      'border-style': 'dashed'
    }
  }
];

// Convert CFG data to Cytoscape elements
const convertCFGToElements = (cfgData: CFGData) => {
  const nodes = Object.values(cfgData.nodes).map(node => {
    // Format the label with better text wrapping
    let sourceText = node.source_text || '';

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

const Graph = forwardRef<GraphRef>((_props, ref) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [elements, setElements] = useState<any[]>([]);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [nodeSelection, setNodeSelection] = useState<string>('');

  // Update graph with new code
  const updateGraph = async (code: string, language: string = 'c') => {
    if (!code.trim()) {
      setElements([]);
      return;
    }

    try {
      const cfgData = await parseCode(code, language);
      const cfgElements = convertCFGToElements(cfgData);
      setElements(cfgElements);
    } catch (err) {
      console.error('Error parsing code:', err);
      setElements([]);
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

  const handleZoomOrPan = (cy: cytoscape.Core) => {
    return (_event: cytoscape.EventObject) => {
      console.log('Saving zoom and pan info');
      saveZoomInfo(cy);
    }
  }

  const selectNode = () => {
    if (!cyRef.current || !nodeSelection) {
      console.warn('Cytoscape instance not available or no node selected');
      return;
    }
    console.log('Selecting node:', nodeSelection);
    // Unselect all nodes first
    cyRef.current.nodes().unselect();
    // Select the specified node
    cyRef.current.getElementById(nodeSelection).select();
  };

  const resetZoom = () => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 30);
    }
  };

  const relayoutGraph = () => {
    if (cyRef.current) {
      cyRef.current.off('viewport');
      layoutGraph(cyRef.current, () => {
        if (cyRef.current) {
          cyRef.current.on('viewport', handleZoomOrPan(cyRef.current));
        }
      });
    }
  };

  return (
    <div className="container">
      <span style={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: '1em' }}>
        <h2>Graph Visualization</h2>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span>Selected Node: <strong>{selectedNode || 'none'}</strong></span>
          <input
            type="text"
            value={nodeSelection}
            onChange={(e) => setNodeSelection(e.target.value)}
            placeholder="Enter node ID to select"
          />
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button onClick={selectNode} style={{ padding: '5px 10px' }}>
              Select Node
            </button>
            <button onClick={resetZoom} style={{ padding: '5px 10px' }}>
              Reset Zoom
            </button>
            <button onClick={relayoutGraph} style={{ padding: '5px 10px' }}>
              Relayout
            </button>
          </div>
        </div>
      </span>
      <div className="cytoscape-container">
        <CytoscapeComponent
          elements={elements}
          stylesheet={CYTOSCAPE_STYLE}
          // https://stackoverflow.com/a/55872886
          style={{ width: "100%", height: "500px", textAlign: "initial" }}
          cy={(cy) => {
            // Add event listeners for node selection
            cy.on('select', 'node', handleNodeSelection);
            cy.on('unselect', 'node', handleNodeUnselection);
            cy.one('layoutstop', () => {
              cy.on('viewport', handleZoomOrPan(cy));
            });

            // Store the cytoscape instance in the ref
            if (cyRef.current) {
              if (cyRef.current === cy) {
                // Remove previous event listeners to avoid memory leaks
                cyRef.current.removeListener('viewport');
              }
            }
            cyRef.current = cy;

            layoutGraph(cyRef.current);
          }}
        />
      </div>
    </div>
  );
});

Graph.displayName = 'Graph';

export default Graph;

const saveZoomInfo = (cy: cytoscape.Core) => {
  const zoomInfo = {
    zoom: cy.zoom(),
    pan: cy.pan(),
  };
  localStorage.setItem('tree_sprawler_zoom', JSON.stringify(zoomInfo));
}

function loadZoomAndPanInfo(cy: cytoscape.Core) {
  const zoomInfo = localStorage.getItem('tree_sprawler_zoom');
  if (zoomInfo) {
    const { zoom, pan } = JSON.parse(zoomInfo);
    cy.zoom(zoom);
    cy.pan(pan);
  }
}

function layoutGraph(cy: cytoscape.Core, callback?: () => void) {
  const layout = cy.layout({
    name: 'dagre',
    rankSep: 50,
    nodeSep: 80,
    ranker: 'tight-tree'
  } as any)

  layout.on('layoutstop', () => {
    // Load zoom and pan info from localStorage
    loadZoomAndPanInfo(cy);
    if (callback) {
      callback();
    }
  });

  layout.run();
}

