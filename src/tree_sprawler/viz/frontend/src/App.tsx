import { useState, useRef, useEffect } from 'react'
import Editor from './Editor'
import Graph from './Graph'
import LanguageSelector from './LanguageSelector'
import './App.css'

// Define the interface for Graph component ref
interface GraphRef {
  updateGraph: (code: string, language: string) => Promise<void>;
}

function App() {
  const [language, setLanguage] = useState('c');
  const [isInitialized, setIsInitialized] = useState(false);
  const graphRef = useRef<GraphRef>(null);

  const handleCodeChange = async (code: string) => {
    // Call backend /parse and update the graph
    if (graphRef.current) {
      try {
        await graphRef.current.updateGraph(code, language);
        if (!isInitialized) {
          setIsInitialized(true);
        }
      } catch (error) {
        console.error('Error updating graph:', error);
      }
    }
  };

  // Handle language changes - update graph with current code
  useEffect(() => {
    if (isInitialized && graphRef.current) {
      // Get current code from localStorage and update graph with new language
      const storedCode = localStorage.getItem('tree_sprawler_code');
      if (storedCode) {
        handleCodeChange(storedCode);
      }
    }
  }, [language, isInitialized]);

  return (
    <>
      {/* <h1>Tree Sprawler Visualization</h1> */}
      <LanguageSelector language={language} onLanguageChange={setLanguage} />
      <div className="app-container">
        <Editor language={language} onTextChange={handleCodeChange} />
        <Graph ref={graphRef} />
      </div>
    </>
  )
}

export default App
