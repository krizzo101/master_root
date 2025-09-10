# IDE Context Bridge Protocol Specification

## Overview

The IDE Context Bridge Protocol defines a standardized interface for bidirectional communication between IDEs/editors and the unified context system. This protocol enables intelligent code assistance by capturing IDE state and providing contextual suggestions based on the populated context_items database.

## Architecture

```
┌─────────────────┐    WebSocket/HTTP    ┌──────────────────┐    Redis PubSub    ┌─────────────────┐
│   IDE Client    │◄─────────────────────►│  Bridge Service  │◄──────────────────►│  Context System │
│  (VSCode, Vim,  │                       │                  │                    │  (PostgreSQL +  │
│   Emacs, etc.)  │                       │                  │                    │   pgvector)     │
└─────────────────┘                       └──────────────────┘                    └─────────────────┘
        │                                          │
        ▼                                          ▼
┌─────────────────┐                       ┌──────────────────┐
│  IDE Extension  │                       │  Embedding API   │
│   /Plugin       │                       │   Integration    │
└─────────────────┘                       └──────────────────┘
```

## Core Components

### 1. Context Capture Protocol

#### IDE State Message Format
```typescript
interface IDEContextMessage {
  type: 'context_update' | 'query_request' | 'suggestion_request';
  timestamp: string; // ISO 8601
  session_id: string;
  editor_id: string; // unique identifier for editor instance

  // Context Data
  active_file?: {
    path: string;
    language: string;
    content?: string; // Optional for large files
    modified: boolean;
    line_count: number;
  };

  cursor_position?: {
    line: number;
    column: number;
    offset: number;
  };

  selection?: {
    start: { line: number; column: number; };
    end: { line: number; column: number; };
    text: string;
  };

  // Environment Context
  workspace?: {
    root_path: string;
    folders: string[];
    active_project?: string;
  };

  open_files?: Array<{
    path: string;
    language: string;
    modified: boolean;
  }>;

  // Git Context
  git_info?: {
    branch: string;
    repository: string;
    uncommitted_changes: number;
  };

  // Diagnostics & Errors
  diagnostics?: Array<{
    file_path: string;
    severity: 'error' | 'warning' | 'info' | 'hint';
    line: number;
    column: number;
    message: string;
    source: string;
  }>;

  // Query Context (for search requests)
  query?: {
    text: string;
    type: 'semantic' | 'code' | 'hybrid' | 'chat_history';
    filters?: {
      source_types?: string[];
      entity_types?: string[];
      file_patterns?: string[];
      languages?: string[];
    };
  };
}
```

### 2. Response Protocol

#### Bridge Service Response Format
```typescript
interface BridgeResponse {
  type: 'context_ack' | 'suggestions' | 'search_results' | 'error';
  timestamp: string;
  request_id?: string;
  session_id: string;

  // Success response
  data?: {
    // Code Suggestions
    suggestions?: Array<{
      type: 'completion' | 'refactor' | 'fix' | 'documentation';
      priority: number; // 1-10
      confidence: number; // 0-1
      title: string;
      description: string;
      code_snippet?: string;
      file_path?: string;
      line_range?: [number, number];
      source_context_id?: string; // Reference to context_items
    }>;

    // Search Results
    search_results?: Array<{
      id: string;
      source_type: string;
      entity_type: string;
      title: string;
      content: string;
      file_path?: string;
      similarity: number;
      relevance_score: number;
      metadata: Record<string, any>;
    }>;

    // Chat History Context
    chat_context?: Array<{
      id: string;
      session_id: string;
      message_type: 'user' | 'assistant';
      content: string;
      timestamp: string;
      relevance: number;
      file_references?: string[];
    }>;

    // Performance metrics
    metrics?: {
      response_time_ms: number;
      search_time_ms: number;
      embedding_time_ms: number;
      cache_hit: boolean;
    };
  };

  // Error response
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
```

## Communication Protocols

### 1. WebSocket Protocol (Real-time)

**Connection Endpoint**: `ws://localhost:8080/ide-bridge`

**Connection Flow**:
1. Client establishes WebSocket connection
2. Client sends authentication/registration message
3. Server acknowledges and assigns session_id
4. Bidirectional messaging for context updates and responses

**Message Types**:
- `context_update`: IDE sends current state
- `query_request`: IDE requests semantic search
- `suggestion_request`: IDE requests code suggestions
- `subscription`: IDE subscribes to specific event types

### 2. HTTP REST API (Request-Response)

**Base URL**: `http://localhost:8080/api/v1/ide-bridge`

**Endpoints**:

```http
POST /context
Content-Type: application/json
{
  "session_id": "uuid",
  "context": IDEContextMessage
}
```

```http
GET /suggestions?session_id={id}&file_path={path}&line={num}&column={num}
Response: BridgeResponse
```

```http
POST /search
Content-Type: application/json
{
  "query": "search term",
  "type": "semantic|code|hybrid",
  "filters": {...}
}
```

### 3. Redis PubSub Integration

**Channels**:
- `context:updates:{session_id}`: IDE context changes
- `suggestions:{session_id}`: Real-time suggestions
- `search:results:{request_id}`: Async search results

## IDE-Specific Integration Patterns

### VSCode Extension

```typescript
// Extension activation
export function activate(context: vscode.ExtensionContext) {
  const bridge = new IDEContextBridge('ws://localhost:8080/ide-bridge');

  // Context tracking
  vscode.window.onDidChangeActiveTextEditor((editor) => {
    bridge.sendContextUpdate({
      type: 'context_update',
      active_file: {
        path: editor.document.fileName,
        language: editor.document.languageId,
        // ...
      }
    });
  });

  // Suggestion provider
  vscode.languages.registerCompletionItemProvider('*', {
    provideCompletionItems: async (document, position) => {
      const suggestions = await bridge.requestSuggestions(document, position);
      return suggestions.map(s => new vscode.CompletionItem(s.title));
    }
  });
}
```

### Vim Plugin (Vimscript/Lua)

```lua
-- Neovim Lua plugin
local M = {}
local bridge_client = require('ide-bridge.client')

function M.setup(opts)
  local bridge = bridge_client.new(opts.bridge_url or 'ws://localhost:8080/ide-bridge')

  -- Context tracking autocmds
  vim.api.nvim_create_autocmd({'BufEnter', 'CursorMoved'}, {
    callback = function()
      bridge:send_context({
        type = 'context_update',
        active_file = {
          path = vim.fn.expand('%:p'),
          language = vim.bo.filetype,
        },
        cursor_position = {
          line = vim.fn.line('.'),
          column = vim.fn.col('.')
        }
      })
    end
  })

  -- Completion function
  vim.keymap.set('i', '<C-x><C-o>', function()
    local suggestions = bridge:request_suggestions()
    -- Process suggestions...
  end)
end
```

### Emacs Integration

```elisp
;; Emacs Lisp integration
(require 'websocket)

(defvar ide-bridge-connection nil)
(defvar ide-bridge-session-id nil)

(defun ide-bridge-connect ()
  "Connect to IDE Context Bridge"
  (setq ide-bridge-connection
        (websocket-open "ws://localhost:8080/ide-bridge"
                        :on-message #'ide-bridge-handle-message
                        :on-open (lambda (ws) (ide-bridge-register)))))

(defun ide-bridge-send-context ()
  "Send current context to bridge"
  (when ide-bridge-connection
    (websocket-send-text
     ide-bridge-connection
     (json-encode
      `((type . "context_update")
        (active_file . ((path . ,(buffer-file-name))
                       (language . ,(symbol-name major-mode)))))))))

;; Hooks for context tracking
(add-hook 'post-command-hook #'ide-bridge-send-context)
```

## Security & Authentication

### Authentication Flow
1. Client connects with API key or token
2. Server validates credentials against configured auth provider
3. Session established with permissions scope
4. All subsequent messages include session_id

### Security Measures
- TLS/WSS encryption for all communications
- Rate limiting per session/IP
- Input validation and sanitization
- Configurable data retention policies
- Audit logging for all context captures

## Performance Optimization

### Caching Strategy
- **L1 Cache**: In-memory context state (Redis)
- **L2 Cache**: Frequently accessed suggestions
- **L3 Cache**: Precomputed embeddings and search results

### Batching & Debouncing
- Context updates debounced (500ms default)
- Batch processing for embedding generation
- Async processing for non-critical operations

### Resource Management
- Connection pooling for database
- WebSocket connection limits
- Memory usage monitoring
- Graceful degradation under load

## Configuration

### Bridge Service Configuration
```yaml
# bridge-config.yaml
server:
  host: "0.0.0.0"
  port: 8080
  websocket_path: "/ide-bridge"

database:
  postgres_url: "postgresql://opsvi:password@localhost:5432/unified_context"
  redis_url: "redis://localhost:6379/0"

embedding:
  service_url: "http://localhost:8001"
  model: "sentence-transformers"
  batch_size: 100

search:
  default_similarity_threshold: 0.7
  max_results: 10
  cache_ttl: 300

security:
  require_auth: true
  api_key_header: "X-API-Key"
  rate_limit: "100/minute"
```

## Error Handling

### Error Codes
- `BRIDGE_001`: Connection failed
- `BRIDGE_002`: Authentication failed
- `BRIDGE_003`: Invalid message format
- `BRIDGE_004`: Database connection error
- `BRIDGE_005`: Embedding service unavailable
- `BRIDGE_006`: Rate limit exceeded
- `BRIDGE_007`: Internal server error

### Retry Logic
- Exponential backoff for connection failures
- Circuit breaker pattern for external services
- Graceful degradation when services unavailable

## Monitoring & Metrics

### Key Metrics
- Connection count and duration
- Message throughput and latency
- Search query performance
- Cache hit rates
- Error rates by type

### Health Checks
- `/health`: Service health
- `/metrics`: Prometheus metrics
- `/status`: Detailed system status

## Future Extensions

### Planned Features
1. Multi-language support for embeddings
2. Code action suggestions
3. Refactoring recommendations
4. Test generation assistance
5. Documentation auto-generation
6. Code review integration
7. AI pair programming mode

### Plugin Architecture
- Extensible plugin system
- Custom suggestion providers
- External tool integrations
- Customizable context filters
