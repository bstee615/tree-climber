import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from 'cytoscape';
import cytoscapePopper from 'cytoscape-popper';
import tippy from 'tippy.js';
import dagre from 'cytoscape-dagre';
import nodeHtmlLabel from 'cytoscape-node-html-label';
import { useState, useRef, forwardRef, useImperativeHandle } from 'react';
import { useGraph, setSelectGraphNodeCallback, notifyGraphNodeSelected } from './GraphContext';
import type { GraphData, CFGData, DFGEdge, DFGData } from './GraphContext';
import './Graph.css';
import 'tippy.js/dist/tippy.css';

// Register popper with tippy factory
function tippyFactory(ref: any, content: string) {
  const dummyDomEle = document.createElement('div');
  const tip = tippy(dummyDomEle, {
    getReferenceClientRect: ref.getBoundingClientRect,
    trigger: 'manual',
    content: content,
    allowHTML: true,
    arrow: true,
    placement: 'bottom',
    hideOnClick: false,
    // sticky: 'reference',
    interactive: true,
    appendTo: document.body
  });
  return tip;
}

cytoscape.use(dagre);
nodeHtmlLabel(cytoscape);
cytoscape.use(cytoscapePopper(tippyFactory));

// API endpoint URL
const API_BASE_URL = 'http://localhost:8000';

interface GraphRef {
  updateGraph: (code: string, language: string) => Promise<void>;
}

// Constants for graph styling
const CYTOSCAPE_STYLE = [
  {
    selector: 'node',
    style: {
      'background-color': '#666',
      // Remove 'label': 'data(label)', so Cytoscape doesn't render a text label
      'text-wrap': 'wrap',
      'text-max-width': '120px',
      'width': '140px',
      'height': '40px',
      'color': '#fff',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': '10px',
      'font-family': 'inherit',
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
    selector: 'edge[edgeType = "DATA_DEPENDENCY"]',
    style: {
      'line-style': 'dashed',
      'width': 1,
      'line-color': '#FF6B35',
      'target-arrow-color': '#FF6B35',
      'curve-style': 'unbundled-bezier', // Make DFG edges slightly curved
      'control-point-distance': 30,      // Slight curve
      'control-point-weight': 0.5        // Centered
    }
  },
  {
    selector: 'edge[edgeType = "FUNCTION_CALL"]',
    style: {
      'line-style': 'dashed',
      'width': 2,
      'line-color': '#7ecbff', // light blue
      'target-arrow-color': '#7ecbff',
    }
  },
  {
    selector: ':selected',
    style: {
      'color': '#FF6B35',
      'background-color': 'rgba(255,235,59,0.1)',
      'border-color': '#FF6B35',
      'border-width': '2px',
      'border-style': 'solid',
      'border-radius': '6px',
    }
  }
];

// Convert CFG data to Cytoscape elements
const convertCFGToElements = (cfgData: CFGData) => {
  const nodes = Object.values(cfgData.nodes).map(node => {
    const definitions = (node.metadata?.variable_definitions || []).join(', ');
    const uses = (node.metadata?.variable_uses || []).join(', ');
    const functionCalls = (node.metadata?.function_calls || []).join(', ');
    let sourceText = node.source_text || '';
    return {
      data: {
        id: node.id.toString(),
        label: node.node_type + (sourceText ? `\n${sourceText}` : ''), // fallback for plain text
        nodeType: node.node_type,
        sourceText: node.source_text,
        definitions,
        uses,
        functionCalls,
        hasDefUse: definitions || uses || functionCalls ? true : false,
      }
    };
  });

  const edges: any[] = [];
  Object.values(cfgData.nodes).forEach(node => {
    node.successors.forEach(successorId => {
      const label = node.edge_labels[successorId] || '';
      // Detect function call edges by label (adjust if you have a better way)
      const isFunctionCall = label && label.toLowerCase() === 'function_call';
      edges.push({
        data: {
          id: `${node.id}-${successorId}`,
          source: node.id.toString(),
          target: successorId.toString(),
          label: label.replace('function_call', 'call'),
          edgeType: isFunctionCall ? "FUNCTION_CALL" : null,
        }
      });
    });
  });

  return [...nodes, ...edges];
};

const convertDFGToElements = (dfgData: DFGData) => {
  const edges: any[] = [];
  Object.values(dfgData.edges).forEach((edge: DFGEdge) => {
    edges.push({
      data: {
        source: edge.source.toString(),
        target: edge.target.toString(),
        label: edge.label,
        edgeType: "DATA_DEPENDENCY",
      }
    });
  });
  return [...edges];
}

// API call to parse code and get CFG
const parseCode = async (code: string, language: string): Promise<GraphData> => {
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

  return {
    ast: result.ast,
    cfg: result.cfg,
    dfg: result.dfg,
  };
};

const Graph = forwardRef<GraphRef>((_props, ref) => {
  const [elements, setElements] = useState<any[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showDefUseEdges, setShowDefUseEdges] = useState<boolean>(true); // Toggle for DFG edges
  const selectedNode = useRef<string | null>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const nodeSelection = useRef<string>('');
  
  // Use the graph context
  const { setGraphData } = useGraph();

  // Store last loaded graphs for toggling DFG edges
  const lastGraphs = useRef<GraphData | null>(null);

  // Update graph with new code
  const updateGraph = async (code: string, language: string = 'c') => {
    if (!code.trim()) {
      setElements([]);
      lastGraphs.current = null;
      return;
    }

    try {
      const graphs = await parseCode(code, language);
      
      // Store the graph data in the context (creates Graphology graph)
      setGraphData(graphs.cfg, language);
      lastGraphs.current = graphs;
      
      // Create Cytoscape elements for visualization
      const cfgElements = convertCFGToElements(graphs.cfg);
      const dfgElements = convertDFGToElements(graphs.dfg);
      setElements([...cfgElements, ...(showDefUseEdges ? dfgElements : [])]);
      setErrorMessage(null);
      
    } catch (err) {
      if (err instanceof Error) {
        setErrorMessage(err.toString());
        setElements([]);
        lastGraphs.current = null;
      } else {
        console.error('Unhandled error:', err);
      }
    }
  };

  // Toggle DFG edges
  const handleToggleDefUseEdges = () => {
    setShowDefUseEdges((prev) => {
      const newValue = !prev;
      // If we have loaded graphs, update elements accordingly
      if (lastGraphs.current) {
        const cfgElements = convertCFGToElements(lastGraphs.current.cfg);
        const dfgElements = convertDFGToElements(lastGraphs.current.dfg);
        setElements([...cfgElements, ...(newValue ? dfgElements : [])]);
      }
      return newValue;
    });
  };

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    updateGraph,
  }));

  const handleNodeSelection = (event: cytoscape.EventObject) => {
    const nodeId = event.target.id();
    selectedNode.current = nodeId;
    notifyGraphNodeSelected(nodeId);
    console.log('Node selected:', nodeId);
  };

  const handleNodeUnselection = () => {
    selectedNode.current = null;
    notifyGraphNodeSelected();
    console.log('Node unselected');
  };

  const handleZoomOrPan = (cy: cytoscape.Core) => {
    return (_event: cytoscape.EventObject) => {
      console.log('Saving zoom and pan info');
      saveZoomInfo(cy);
    }
  }

  const selectNode = () => {
    if (!cyRef.current || !nodeSelection.current) {
      console.warn('Cytoscape instance not available or no node selected');
      return;
    }
    console.log('Selecting node:', nodeSelection.current);
    // Unselect all nodes first
    cyRef.current.nodes().unselect();
    // Select the specified node
    cyRef.current.getElementById(nodeSelection.current).select();
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

  // Register the selectNode callback for programmatic selection
  setSelectGraphNodeCallback((nodeId?: string) => {
    if (!cyRef.current) return;
    cyRef.current.nodes().unselect();
    if (nodeId) {
        const node = cyRef.current.getElementById(nodeId);
        if (node) node.select();
    }
  });

  // Tooltip handler for defs/uses/calls using tippy.js and cytoscape-popper
  const handleNodeHover = (cy: cytoscape.Core) => {
    cy.on('mouseover', 'node', (event) => {
      const node = event.target;
      const defs = node.data('definitions');
      const uses = node.data('uses');
      const calls = node.data('functionCalls');
      let tooltip = '';
      if (defs && defs.trim()) tooltip += `<div class='cy-tooltip cy-tooltip-defs'><span class='cy-tooltip-label'>Defs: <code class='cy-tooltip-identifiers'>${defs}</code></span></div>`;
      if (uses && uses.trim()) tooltip += `<div class='cy-tooltip cy-tooltip-uses'><span class='cy-tooltip-label'>Uses: <code class='cy-tooltip-identifiers'>${uses}</code></span></div>`;
      if (calls && calls.trim()) tooltip += `<div class='cy-tooltip cy-tooltip-calls'><span class='cy-tooltip-label'>Calls: <code class='cy-tooltip-identifiers'>${calls}</code></span></div>`;
      if (tooltip) {
        // Remove any previous tippy
        if (node.data('tippyInstance')) {
          node.data('tippyInstance').destroy();
          node.removeData('tippyInstance');
        }
        const tip = node.popper({
          content: () => {
            const div = document.createElement('div');
            div.innerHTML = tooltip;
            return div;
          }
        });
        tip.show();
        node.data('tippyInstance', tip);
      }
    });
    cy.on('mouseout', 'node', (event) => {
      const node = event.target;
      const tip = node.data('tippyInstance');
      if (tip) {
        tip.destroy();
        node.removeData('tippyInstance');
      }
    });
  };

  return (
    <div className="container">
      <span style={{ display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: '1em' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span>Select a node: <strong>{selectedNode ? selectedNode.current : 'none'}</strong></span>
          <input
            type="text"
            defaultValue={nodeSelection.current}
            onChange={(e) => nodeSelection.current = e.target.value}
            placeholder="Enter node ID to select"
          />
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button onClick={selectNode} style={{ padding: '5px 10px', marginBottom: '10px' }}>
              Select Node
            </button>
            <button onClick={resetZoom} style={{ padding: '5px 10px', marginBottom: '10px' }}>
              Reset Zoom
            </button>
            <button onClick={relayoutGraph} style={{ padding: '5px 10px', marginBottom: '10px' }}>
              Relayout
            </button>
            <button onClick={handleToggleDefUseEdges} style={{ padding: '5px 10px', marginBottom: '10px' }}>
              {showDefUseEdges ? 'Hide' : 'Show'} Def-Use Edges
            </button>
          </div>
        </div>
      </span>
      <div className="cytoscape-container">
        {errorMessage ? (
          <div className="error-message">
            <div><strong>Could not generate graph.</strong></div>
            <div>{errorMessage}</div>
          </div>
        ) : <CytoscapeComponent
          elements={elements}
          stylesheet={CYTOSCAPE_STYLE}
          // https://stackoverflow.com/a/55872886
          style={{ width: "100%", height: "400px", textAlign: "initial" }}
          cy={(cy) => {
            // Add event listeners for node selection
            cy.on('select', 'node', handleNodeSelection);
            cy.on('unselect', 'node', handleNodeUnselection);
            cy.one('layoutstop', () => {
              cy.on('viewport', handleZoomOrPan(cy));
            });

            // Setup nodeHtmlLabel for styled node labels
            cy.nodeHtmlLabel([
              {
                query: 'node',
                halign: 'center',
                valign: 'center',
                halignBox: 'center',
                valignBox: 'center',
                cssClass: 'htmlNodeLabel',
                tpl: function(data) {
                  // Node type (default font), source text (monospace)
                  return data.sourceText
                    ? `<div class='cy-html-label'><span class='cy-node-type'>${data.nodeType}</span><span class='cy-source-text'>${data.sourceText}</span></div>`
                    : `<span class='cy-node-type'>${data.nodeType}</span>`;
                }
              }
            ]);

            // Store the cytoscape instance in the ref
            if (cyRef.current) {
              if (cyRef.current === cy) {
                // Remove previous event listeners to avoid memory leaks
                cyRef.current.removeListener('viewport');
              }
            }
            cyRef.current = cy;
            layoutGraph(cyRef.current);
            handleNodeHover(cy);
          }}
        />}
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

// When laying out the graph, only use CFG nodes/edges, then add DFG edges after
function layoutGraph(cy: cytoscape.Core, callback?: () => void) {
  // Get only CFG nodes and edges (exclude DFG edges)
  const cfgNodes = cy.nodes().filter((n) => !n.isEdge() && n.data('nodeType'));
  const cfgEdges = cy.edges().filter((e) => e.data('edgeType') !== 'DATA_DEPENDENCY');
  // Hide DFG edges during layout
  cy.edges().filter((e) => e.data('edgeType') === 'DATA_DEPENDENCY').style({ display: 'none' });

  // Layout only CFG nodes and edges
  const layoutElements = cy.collection(cfgNodes).union(cfgEdges);
  const layout = layoutElements.layout({
    name: 'dagre',
    rankSep: 50,
    nodeSep: 80,
    ranker: 'tight-tree'
  } as any);

  layout.on('layoutstop', () => {
    // Show DFG edges after layout
    cy.edges().filter((e) => e.data('edgeType') === 'DATA_DEPENDENCY').style({ display: 'element' });
    // Load zoom and pan info from localStorage
    loadZoomAndPanInfo(cy);
    if (callback) {
      callback();
    }
  });

  layout.run();
}

