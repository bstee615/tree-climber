import React from "react";
import * as monaco from "monaco-editor";
import Editor from "@monaco-editor/react";
import { useGraph, selectGraphNodeById } from './GraphContext';
import type Graph from "graphology";

// Type definitions
interface Position {
  line: number;
  column: number;
  index: number;
}

interface Selection {
  start: Position;
  end: Position;
  text: string;
}

// Helper to get full position including index
function getPositionWithIndex(editor: monaco.editor.IStandaloneCodeEditor, position: monaco.Position): Position | undefined {
  const model = editor.getModel();
  if (!model) {
    console.error("Editor model not found");
    return;
  }
  const index = model.getOffsetAt(position);
  return {
    line: position.lineNumber,
    column: position.column,
    index: index,
  };
}

function positionEquals(start: Position, end: Position) {
  return start.line === end.line && start.column === end.column && start.index === end.index;
}

const MonacoEditor = ({ language, onTextChange }: { language: string, onTextChange: (code: string) => void }) => {
  // State to manage the code in the editor
  const [code, setCode] = React.useState<string>("");
  
  // Access the graph context
  const { graphologyGraph, getNodesInRange } = useGraph();
  
  // Use refs to store current graph state to avoid stale closures
  const graphRef = React.useRef(graphologyGraph);
  const getNodesInRangeRef = React.useRef(getNodesInRange);
  
  // Update refs when context values change
  React.useEffect(() => {
    graphRef.current = graphologyGraph;
    getNodesInRangeRef.current = getNodesInRange;
  }, [graphologyGraph, getNodesInRange]);
  
  // Load initial code from localStorage
  React.useEffect(() => {
    const storedCode = localStorage.getItem('tree_sprawler_code');
    if (storedCode) {
      setCode(storedCode);
      // Notify parent component of the initial code load
      onTextChange(storedCode);
    }
  }, [onTextChange]);
  // On change, update localStorage
  const handleEditorChange = (code: string | undefined) => {
    if (code !== undefined) {
      console.log("Updated code:", code.length, "characters");
      setCode(code);
      localStorage.setItem('tree_sprawler_code', code);
      onTextChange(code); // Notify parent component of code change
    }
  };

  const handleEditorMount = (editor: any) => {
    setCode(editor.getValue());
    // Log cursor position and analyze AST/CFG nodes
    editor.onDidChangeCursorPosition((e: monaco.editor.ICursorPositionChangedEvent) => {
      const pos = getPositionWithIndex(editor, e.position);
      console.log("Cursor Position:", pos);
      
      // Use the current graph reference to avoid stale closure
      const currentGraph = graphRef.current;
      if (currentGraph && pos) {
        const matchingNodes: string[] = getCursorPositionNodes(currentGraph, pos, editor);
        if (matchingNodes.length > 0) {
          // Select the first matching node in the graph
          selectGraphNodeById(matchingNodes[0]);
        } else {
          selectGraphNodeById();
        }
        console.log("CFG nodes at cursor position:", matchingNodes);
      } else {
        console.debug("Graph not yet available or position invalid");
      }
    });

    // Log selection changes
    editor.onDidChangeCursorSelection((e: monaco.editor.ICursorSelectionChangedEvent) => {
      const model = editor.getModel();
      const selection = e.selection;

      const start = getPositionWithIndex(editor, selection.getStartPosition());
      const end = getPositionWithIndex(editor, selection.getEndPosition());
      const text = model.getValueInRange(selection);

      if (!start || !end) {
        console.warn("Failed to get start or end position");
        return;
      }
      if (positionEquals(start, end)) {
        console.debug("Selection start and end are the same, no text selected.");
        return;
      }

      const selectionData: Selection = {
        start,
        end,
        text,
      };

      console.log("Selection:", selectionData);
      
      // Use the current graph reference to avoid stale closure
      const currentGraph = graphRef.current;
      const currentGetNodesInRange = getNodesInRangeRef.current;
      if (currentGraph) {
        const nodesInRange = currentGetNodesInRange(start.index, end.index);
        console.log("CFG nodes in selection range:", nodesInRange);
      } else {
        console.debug("Graph not yet available for selection analysis");
      }
    });

    // Deselect node when editor loses focus
    editor.onDidBlurEditorWidget(() => {
      selectGraphNodeById();
    });
  };

  return (
    <div className="container">
      <Editor
        height="500px"
        language={language}
        value={code}
        theme="vs-dark"
        onChange={handleEditorChange}
        onMount={handleEditorMount}
      />
    </div>
  );
};

export default MonacoEditor;

function getCursorPositionNodes(currentGraph: Graph, pos: Position, editor: any) {
  // Try to match the cursor position to CFG nodes
  // This implementation assumes that the CFG node metadata may contain source position info
  // If not, fallback to a best-effort match using source_text
  const matchingNodes: string[] = [];
  currentGraph.forEachNode((nodeId, attrs) => {
    // If node metadata has start/end index, use that
    const meta = attrs.metadata as any;
    if (meta && typeof meta.start_index === 'number' && typeof meta.end_index === 'number') {
      if (pos.index >= meta.start_index && pos.index <= meta.end_index) {
        matchingNodes.push(nodeId);
      }
    } else if (attrs.source_text) {
      // Fallback: try to find the source_text in the editor and see if the cursor is inside it
      const text = attrs.source_text;
      const codeValue = editor.getValue();
      const idx = codeValue.indexOf(text);
      if (idx !== -1 && pos.index >= idx && pos.index <= idx + text.length) {
        matchingNodes.push(nodeId);
      }
    }
  });
  return matchingNodes;
}

