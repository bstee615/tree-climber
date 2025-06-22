import React from "react";
import Editor from "@monaco-editor/react";

const MonacoEditor = ({ language }: { language: string }) => {
  const [code, setCode] = React.useState<string>("");

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setCode(value);
      localStorage.setItem('tree_sprawler_code', value);
    }
  };

  React.useEffect(() => {
    const storedCode = localStorage.getItem('tree_sprawler_code');
    if (storedCode) {
      setCode(storedCode);
    }
  }, []);

  return (
    <div className="container">
      <h2>Code Editor</h2>
      <Editor
        height="300px"
        language={language}
        value={code}
        theme="vs-dark"
        onChange={handleEditorChange}
      />
    </div>
  );
};

export default MonacoEditor;
