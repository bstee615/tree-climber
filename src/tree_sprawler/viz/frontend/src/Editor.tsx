import React from "react";
import * as monaco from "monaco-editor";
import Editor from "@monaco-editor/react";

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
    // Log cursor position
    editor.onDidChangeCursorPosition((e: monaco.editor.ICursorPositionChangedEvent) => {
      const pos = getPositionWithIndex(editor, e.position);
      console.log("Cursor Position:", pos);
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

