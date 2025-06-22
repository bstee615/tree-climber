import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';

cytoscape.use( dagre );

const elements = [
  { data: { id: "one", label: "Node 1" }, position: { x: 100, y: 100 } },
  { data: { id: "two", label: "Node 2" }, position: { x: 200, y: 200 } },
  { data: { source: "one", target: "two", label: "Edge from Node1 to Node2" } },
];

const Graph = () => {
  return (
    <div className="container">
      <h2>Graph Visualization</h2>
      <CytoscapeComponent
        elements={elements}
        style={{ width: "100%", height: "300px", textAlign: "initial" }}
      />
    </div>
  );
};

export default Graph;
