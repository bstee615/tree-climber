import { useState, useRef } from "react";
import ReactDOM from "react-dom/client";
import MonacoEditor from "@monaco-editor/react";
import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import debounce from 'lodash.debounce';

cytoscape.use(dagre);

const initialCode = `function greet() {
  console.log("Hello from Monaco + Cytoscape!");
}`;

const elements = [
  { data: { id: "a", label: "Node A" } },
  { data: { id: "b", label: "Node B" } },
  { data: { id: "c", label: "Node C" } },
  { data: { source: "a", target: "b" } },
  { data: { source: "b", target: "c" } }
];

const DEBOUNCE_DELAY = 300; // Adjust as needed

class Position {
  constructor(public lineNumber: number, public column: number, public index: number) { }

  public static from_monaco(model: any, position: any): Position {
    return new Position(
      position.lineNumber,
      position.column,
      model.getOffsetAt(position)
    );
  }
}

class Selection {
  constructor(public start: Position, public end: Position, public text: string) { }

  public static from_monaco(model: any, selection: any): Selection {
    const start = Position.from_monaco(model, selection.getStartPosition());
    const end = Position.from_monaco(model, selection.getEndPosition());
    const text = model.getValueInRange(selection);
    return new Selection(start, end, text);
  }
}

const App = () => {
  const [code, setCode] = useState(initialCode);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const handleEditorChange = (value: string | undefined) => {
    console.log("Editor changed:", value);
    setCode(value || "");
  };

  const selectNodeB = () => {
    if (cyRef.current) {
      cyRef.current.$(":selected").unselect(); // Unselect any previously selected nodes
      // Select node with id "b"
      const nodeB = cyRef.current.$('node[id = "b"]');
      if (nodeB) {
        nodeB.select();
      }
    }
  };

  // Debounce event handlers for better performance
  const debouncedCursorPosition = useRef(
    debounce((position: Position) => {
      console.log("Cursor moved:", position);
    }, DEBOUNCE_DELAY)
  ).current;

  const debouncedSelectionChange = useRef(
    debounce((selected: Selection) => {
      console.log("Selected text:", selected);
    }, DEBOUNCE_DELAY)
  ).current;

  const handleCursorChange = (monaco: any, editor: any) => {
    editor.onDidChangeCursorPosition(e => {
      debouncedCursorPosition(Position.from_monaco(editor.getModel(), e.position));
    });
    editor.onDidChangeCursorSelection(e => {
      const model = editor.getModel();
      if (!model) return;
      // Get the selected text and its range
      if (e.selection.isEmpty()) return; // Ignore empty selections
      const selected = model.getValueInRange(e.selection);
      debouncedSelectionChange(Selection.from_monaco(model, e.selection));
    });
  };

  const handleNodeSelect = (event: cytoscape.EventObject) => {
    const node = event.target;
    console.log("Node selected:", node.data());
  };

  return (
    <div className="app">
      <div className="editor">
        <MonacoEditor
          height="100%"
          defaultLanguage="javascript"
          value={code}
          onChange={handleEditorChange}
          onMount={(editor, monaco) => handleCursorChange(monaco, editor)}
        />
      </div>
      <div className="graph">
        <button onClick={selectNodeB}>Select Node B</button>
        <CytoscapeComponent
          elements={elements}
          style={{ width: "100%", height: "100%" }}
          layout={{ name: "dagre" }}
          cy={cy => {
            cyRef.current = cy;
            cy.on("select", "node", handleNodeSelect);
          }}
        />
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
