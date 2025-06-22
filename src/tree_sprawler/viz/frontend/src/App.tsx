import { useState } from 'react'
import Editor from './Editor'
import Graph from './Graph'
import LanguageSelector from './LanguageSelector'
import './App.css'

function App() {
  const [language, setLanguage] = useState('c');

  return (
    <>
      <h1>Tree Sprawler Visualization</h1>
      <LanguageSelector language={language} onLanguageChange={setLanguage} />
      <div className="app-container">
        <Editor language={language} />
        <Graph />
      </div>
    </>
  )
}

export default App
