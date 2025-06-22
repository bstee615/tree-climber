import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { useState, useRef } from 'react';

cytoscape.use(dagre);

const elements = [
  { data: { id: "one", label: "Node 1" }, position: { x: 100, y: 100 } },
  { data: { id: "two", label: "Node 2" }, position: { x: 200, y: 200 } },
  { data: { source: "one", target: "two", label: "Edge from Node1 to Node2" } },
];

const Graph = () => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

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
      <h2>Graph Visualization</h2>
      <div style={{ marginBottom: '10px' }}>
        <button onClick={selectNodeTwo} style={{ marginRight: '10px' }}>
          Select Node Two
        </button>
        {selectedNode && (
          <span>Selected Node: <strong>{selectedNode}</strong></span>
        )}
      </div>
      <div className="cytoscape-container">
        <CytoscapeComponent
          elements={elements}
          // https://stackoverflow.com/a/55872886
          style={{ width: "100%", height: "300px", textAlign: "initial" }}
          cy={(cy) => {
            cyRef.current = cy;

            // Add event listeners for node selection
            cy.on('select', 'node', handleNodeSelection);
            cy.on('unselect', 'node', handleNodeUnselection);
          }}
        />
      </div>
    </div>
  );
};

export default Graph;
