# Frontend Integration with FastAPI CFG Server

**Created:** 2025-06-22  
**Author:** AI Assistant  
**Status:** Completed  

## Overview

This document describes the integration between the React frontend and the FastAPI CFG server. The frontend provides a real-time code editor with CFG visualization that updates automatically as the user types code.

## Architecture

```
┌─────────────────┐    HTTP POST    ┌──────────────────┐
│   React App     │  /parse         │   FastAPI        │
│                 │ ────────────────>│   Server         │
│ ┌─────────────┐ │                 │                  │
│ │   Editor    │ │  JSON Response  │ ┌──────────────┐ │
│ │  (Monaco)   │ │ <───────────────│ │  CFG Builder │ │
│ └─────────────┘ │                 │ │  (tree-sitter│ │
│                 │                 │ │   parsing)   │ │
│ ┌─────────────┐ │                 │ └──────────────┘ │
│ │   Graph     │ │                 └──────────────────┘
│ │ (Cytoscape) │ │
│ └─────────────┘ │
└─────────────────┘
```

## Components

### App.tsx

The main application component that orchestrates the integration between the editor and graph visualization.

**Key Features:**
- Manages language selection state
- Handles code changes from the editor
- Calls the FastAPI `/parse` endpoint
- Updates the graph visualization with CFG data

**Code Structure:**
```tsx
interface GraphRef {
  updateGraph: (code: string, language: string) => Promise<void>;
}

function App() {
  const [language, setLanguage] = useState('c');
  const graphRef = useRef<GraphRef>(null);

  const handleCodeChange = async (code: string) => {
    if (graphRef.current) {
      await graphRef.current.updateGraph(code, language);
    }
  };

  // ... render components
}
```

### Graph.tsx

The graph visualization component that communicates with the FastAPI server and renders CFG data.

**Key Features:**
- Uses `forwardRef` to expose `updateGraph` method to parent
- Converts CFG JSON data to Cytoscape elements
- Handles API communication with error handling
- Applies automatic layout using Dagre
- Provides loading states and error messages

**API Integration:**
```tsx
const parseCode = async (code: string, language: string): Promise<CFGData> => {
  const response = await fetch(`${API_BASE_URL}/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_code: code,
      language: language,
    }),
  });

  const result = await response.json();
  if (!result.success) {
    throw new Error(result.error || 'Failed to parse code');
  }
  return result.cfg;
};
```

**CFG to Cytoscape Conversion:**
```tsx
const convertCFGToElements = (cfgData: CFGData) => {
  const nodes = Object.values(cfgData.nodes).map(node => ({
    data: {
      id: node.id.toString(),
      label: `${node.node_type}\n${node.source_text || ''}`,
      nodeType: node.node_type,
      sourceText: node.source_text,
    }
  }));

  const edges = [];
  Object.values(cfgData.nodes).forEach(node => {
    node.successors.forEach(successorId => {
      const label = node.edge_labels[successorId] || '';
      edges.push({
        data: {
          id: `${node.id}-${successorId}`,
          source: node.id.toString(),
          target: successorId.toString(),
          label: label,
        }
      });
    });
  });

  return [...nodes, ...edges];
};
```

### Editor.tsx

The Monaco-based code editor component that triggers parsing on code changes.

**Integration Points:**
- `onTextChange` prop receives code changes
- Supports multiple languages (C, Java)
- Provides syntax highlighting and code completion

## Data Flow

1. **User Input**: User types code in the Monaco editor
2. **Code Change Event**: Editor triggers `onTextChange` callback
3. **API Call**: App component calls Graph's `updateGraph` method
4. **HTTP Request**: Graph component sends POST request to `/parse` endpoint
5. **CFG Generation**: FastAPI server parses code and generates CFG
6. **JSON Response**: Server returns CFG data in JSON format
7. **Data Conversion**: Graph component converts CFG to Cytoscape elements
8. **Visualization Update**: Cytoscape renders the updated graph
9. **Layout Application**: Dagre layout arranges nodes automatically

## Error Handling

The frontend implements comprehensive error handling:

### Network Errors
```tsx
try {
  const cfgData = await parseCode(code, language);
  // Success path
} catch (err) {
  console.error('Error parsing code:', err);
  setError(err instanceof Error ? err.message : 'Unknown error');
  setElements(defaultElements); // Fallback to default graph
}
```

### Empty Code Handling
```tsx
const updateGraph = async (code: string, language: string = 'c') => {
  if (!code.trim()) {
    setElements(defaultElements);
    return;
  }
  // Continue with parsing
};
```

### Loading States
```tsx
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// In render:
{isLoading && <span>Loading...</span>}
{error && <span style={{ color: 'red' }}>Error: {error}</span>}
```

## Configuration

### API Base URL
```tsx
const API_BASE_URL = 'http://localhost:8001';
```

### Supported Languages
The frontend supports the same languages as the backend:
- C (`"c"`)
- Java (`"java"`)

### Graph Layout
Uses Dagre layout algorithm for automatic node positioning:
```tsx
cy.layout({ name: 'dagre' } as any).run();
```

## Type Definitions

The frontend includes comprehensive TypeScript types for the CFG data:

```tsx
interface CFGNode {
  id: number;
  node_type: string;
  source_text: string;
  successors: number[];
  predecessors: number[];
  edge_labels: { [key: number]: string };
  metadata: {
    function_calls: string[];
    variable_definitions: string[];
    variable_uses: string[];
  };
}

interface CFGData {
  function_name: string | null;
  entry_node_ids: number[];
  exit_node_ids: number[];
  nodes: { [key: number]: CFGNode };
}
```

## Performance Considerations

### Debouncing
Currently, the API is called on every code change. For better performance, consider implementing debouncing:

```tsx
const debouncedUpdateGraph = useCallback(
  debounce((code: string) => {
    if (graphRef.current) {
      graphRef.current.updateGraph(code, language);
    }
  }, 300),
  [language]
);
```

### Caching
Consider implementing client-side caching for identical code inputs:

```tsx
const [cacheMap, setCacheMap] = useState<Map<string, CFGData>>(new Map());

const parseCode = async (code: string, language: string): Promise<CFGData> => {
  const cacheKey = `${language}:${code}`;
  if (cacheMap.has(cacheKey)) {
    return cacheMap.get(cacheKey)!;
  }
  // Make API call and cache result
};
```

## Testing

### Unit Tests
Test the individual components:

```tsx
// Test Graph component API integration
test('updateGraph makes API call with correct parameters', async () => {
  const mockFetch = jest.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ success: true, cfg: mockCFG })
  });
  global.fetch = mockFetch;
  
  const graphRef = { current: { updateGraph: jest.fn() } };
  await graphRef.current.updateGraph('int main() {}', 'c');
  
  expect(mockFetch).toHaveBeenCalledWith(
    'http://localhost:8001/parse',
    expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_code: 'int main() {}',
        language: 'c'
      })
    })
  );
});
```

### Integration Tests
Test the complete flow from editor to graph:

```tsx
test('code change updates graph visualization', async () => {
  render(<App />);
  
  const editor = screen.getByRole('textbox');
  fireEvent.change(editor, { target: { value: 'int foo() { return 42; }' } });
  
  await waitFor(() => {
    expect(screen.getByText(/ENTRY/)).toBeInTheDocument();
    expect(screen.getByText(/RETURN/)).toBeInTheDocument();
  });
});
```

## Development Setup

### Prerequisites
- Node.js and npm/bun installed
- FastAPI server running on port 8001
- Frontend dependencies installed

### Running the Frontend
```bash
cd src/tree_climber/viz/frontend
npm run dev
# or
bun dev
```

### Building for Production
```bash
npm run build
# or
bun run build
```

## Deployment Considerations

### CORS Configuration
For production deployment, configure CORS in the FastAPI server:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables
Use environment variables for configuration:

```tsx
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
```

### Error Monitoring
Consider adding error monitoring service integration:

```tsx
import * as Sentry from '@sentry/react';

// In error handling:
Sentry.captureException(error);
```

## Future Enhancements

1. **Real-time Collaboration**: WebSocket support for multi-user editing
2. **Code Formatting**: Integration with prettier/formatters
3. **Syntax Validation**: Real-time syntax error highlighting
4. **Graph Interactions**: Click-to-edit nodes, drag-and-drop layout
5. **Export Features**: Save graphs as images or export CFG data
6. **Performance Metrics**: Display parsing time and graph complexity
7. **Themes**: Dark/light mode support
8. **Language Extensions**: Plugin system for adding new languages
