# Project Structure

## Directory Organization

```
src/ai_companion/
├── core/              # Core utilities and shared components
│   ├── exceptions.py  # Custom exception classes
│   ├── prompts.py     # System prompts and character cards
│   └── schedules.py   # Activity scheduling logic
├── graph/             # LangGraph workflow definition
│   ├── graph.py       # Main workflow graph construction
│   ├── state.py       # State schema (AICompanionState)
│   ├── nodes.py       # Workflow node implementations
│   ├── edges.py       # Conditional edge logic
│   └── utils/         # Graph-related utilities
├── interfaces/        # User-facing interfaces
│   ├── chainlit/      # Web chat interface
│   └── whatsapp/      # WhatsApp webhook integration
├── modules/           # Feature modules
│   ├── image/         # Image generation
│   ├── memory/        # Memory management (short/long-term)
│   ├── schedules/     # Schedule management
│   └── speech/        # Speech-to-text and text-to-speech
└── settings.py        # Application configuration
```

## Key Conventions

### State Management
- All workflow state extends `AICompanionState` (inherits from `MessagesState`)
- State includes: messages, workflow type, audio buffer, image path, memory context, current activity

### Graph Architecture
- **Nodes**: Discrete processing steps (memory extraction, routing, response generation)
- **Edges**: Flow control between nodes (conditional routing based on workflow type)
- **Workflow Types**: "conversation", "image", "audio"

### Memory System
- **Long-term**: Qdrant vector database (`long_term_memory/` volume)
- **Short-term**: SQLite/DuckDB checkpointer (`short_term_memory/` volume)
- Automatic summarization triggers after configurable message count

### Configuration Pattern
- Settings loaded from `.env` via `pydantic-settings`
- Centralized in `settings.py` with type hints
- Model names, memory parameters, and API keys all configurable

### Module Organization
- Each module is self-contained with its own logic
- Modules expose functions used by graph nodes
- Clear separation between interface, graph orchestration, and business logic

## Docker Volumes
- `long_term_memory/`: Qdrant vector storage (gitignored)
- `short_term_memory/`: Conversation checkpoints (gitignored)
- `generated_images/`: Image generation output (gitignored)

## Testing & Notebooks
- `notebooks/`: Jupyter notebooks for experimentation
- No formal test suite currently in project
