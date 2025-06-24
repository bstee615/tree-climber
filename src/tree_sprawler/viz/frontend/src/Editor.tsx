import React from "react";
import * as monaco from "monaco-editor";
import Editor from "@monaco-editor/react";
import { useGraph, selectGraphNodeById, setOnGraphNodeSelectCallback } from './GraphContext';
import type Graph from "graphology";
import './highlighted-cfg-node.css'

const DEFAULT_CODE = `// Example code
int main() {
    int a;
    if (a > 10) {
        for (int i = 0; i < 10; i ++) {
            a ++;
        }
    }
    return a;
}
`

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

/**
 * Given a node's attributes and the editor instance, return the [startIdx, endIdx] for highlighting.
 * Returns null if no valid range is found.
 */
function getNodeHighlightRange(nodeAttrs: any, editor: any): [number, number] | null {
  // Try to use metadata if available
  const meta = nodeAttrs.metadata as any;
  if (meta && typeof meta.start_index === 'number' && typeof meta.end_index === 'number') {
    return [meta.start_index, meta.end_index];
  } else if (nodeAttrs.source_text) {
    // Fallback: highlight only the first occurrence of source_text in code
    const codeValue = editor.getValue();
    const text = nodeAttrs.source_text;
    const idx = codeValue.indexOf(text);
    if (idx !== -1) {
      return [idx, idx + text.length];
    }
  }
  return null;
}

const MonacoEditor = ({ language, onTextChange }: { language: string, onTextChange: (code: string) => void }) => {
  // State to manage the code in the editor
  const [code, setCode] = React.useState<string>("");
  
  // Access the graph context
  const { graphologyGraph, getNodesInRange } = useGraph();
  
  // Use refs to store current graph state to avoid stale closures
  const graphRef = React.useRef(graphologyGraph);
  const getNodesInRangeRef = React.useRef(getNodesInRange);
  const editorRef = React.useRef<any>(null);
  const decorationsCollectionRef = React.useRef<any>(null);

  // Register callback to highlight code when a graph node is selected
  React.useEffect(() => {
    setOnGraphNodeSelectCallback((nodeId?: string) => {
      const editor = editorRef.current;
      if (!editor) return;
      // Remove previous decorations
      if (decorationsCollectionRef.current) {
        decorationsCollectionRef.current.clear();
      }
      if (!nodeId) return;
      const currentGraph = graphRef.current;
      if (!currentGraph) return;
      const nodeAttrs = currentGraph.getNodeAttributes(nodeId);
      const range = getNodeHighlightRange(nodeAttrs, editor);
      highlightRange(range, editor, decorationsCollectionRef);
    });
  }, []);
  
  // Update refs when context values change
  React.useEffect(() => {
    graphRef.current = graphologyGraph;
    getNodesInRangeRef.current = getNodesInRange;
  }, [graphologyGraph, getNodesInRange]);
  
  // Load initial code from localStorage
  React.useEffect(() => {
    let storedCode = localStorage.getItem('tree_sprawler_code');
    if (!storedCode) {
      storedCode = DEFAULT_CODE;
    }
    setCode(storedCode);
    // Notify parent component of the initial code load
    onTextChange(storedCode);
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
    editorRef.current = editor;
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

function highlightRange(range: [number, number] | null, editor: any, decorationsCollectionRef: React.RefObject<any>) {
  if (range) {
    const [startIdx, endIdx] = range;
    const model = editor.getModel();
    if (model) {
      const startPos = model.getPositionAt(startIdx);
      const endPos = model.getPositionAt(endIdx);
      if (startPos && endPos) {
        // Only one decoration for the full range
        const decoration = {
          range: new monaco.Range(startPos.lineNumber, startPos.column, endPos.lineNumber, endPos.column),
          options: {
            className: 'highlighted-cfg-node',
            isWholeLine: false,
            stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
          }
        };
        decorationsCollectionRef.current = editor.createDecorationsCollection([decoration]);
      }
    }
  }
}

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

