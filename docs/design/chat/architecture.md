# LAT-Mesh Chat Service Architecture

## Overview

The **LAT-Mesh Chat Service** is a configurable, modular framework designed to enable technical and non-technical users to interact with LLMs through structured, pluggable components. The system orchestrates prompts, memory, and model invocation using a clean adapter-based architecture.

It acts as the orchestration layer that:

- Interfaces with the user or API caller,
- Retrieves context via pluggable memory backends,
- Constructs formatted messages using system prompts and history,
- Calls selected LLMs (OpenAI, Anthropic, LLaMA),
- And returns structured, explainable responses.

## Components

### Chat Service Interface

- **Entry Point**  
  Exposes simple `chat` API for user interaction.
  
- **Platform Layer**  
  Lives in `platform.chat`, orchestrating config-based execution of flows.

### Chat Manager

- **Central Coordinator**  
  Created from a flow config to link prompt renderer, memory, message manager, and model proxy.
  
- **Dynamic Flow Loading**  
  Reads YAML or dict-based config to choose implementations per request or project.

### Prompt Renderer

- **Flexible Prompting Strategy**  
  Supports templated or persona-based system prompts.

- **Methods**
  - `render`
  - `load`
  - `save`

### Memory Manager

- **Session and Context Store**  
  Retrieves and persists previous chat messages from in-memory, LangChain, or LangGraph backends.

- **Methods**
  - `get_messages`
  - `save_message`
  - `clear`

### Message Manager

- **Message Composer**  
  Converts LAT-Mesh ChatMessage objects into a model-compatible list of messages.

- **Responsibilities**
  - Composes message list from prompt + memory + user input
  - Adds messages to memory after receiving model responses
  - Handles optional session management
  - Supports stateless mode (no memory) or stateful mode (with memory)
  - Accepts one or more user messages (multiple only when memory is disabled)
  - Handles message formatting via framework-specific adapters\

- **Methods**
  - `create_message`
  - `add_messages`
  - `get_formatted_messages`

### Model Proxy

- **LLM Invocation Gateway**  
  Handles synchronous, asynchronous, and streaming calls to OpenAI-compatible or local models.

- **Methods**
  - `invoke`
  - `stream`

## Diagrams

### Sequence Flow Diagram

Shows the runtime flow from ChatService input to final LLM response.

👉 [View sequence.mmd](./sequence.mmd)

### Architecture Structure Diagram

Outlines how components interact: ChatService → ChatManager → lib.chat stack.

👉 [View structure.mmd](./structure.mmd)
