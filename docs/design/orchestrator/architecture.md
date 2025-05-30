# Mesh Orchestrator Architecture

## Overview

The **Mesh Orchestrator** is a modular middleware layer that connects chat interfaces with reasoning engines and toolchains, while maintaining OpenAI compatibility. It acts as the control center that:

- Parses and validates requests,
- Routes them through a reasoning engine,
- Dynamically invokes tools based on project configuration,
- And returns structured responses to the user.

## Components

### Orchestrator

- **OpenAI-Compatible API**  
  Listens at `/v1/chat/completions` and `/v1/models`. Accepts the same schema as the OpenAI API.

- **ChatEndpoint**  
  Parses and validates the request, logs unknown fields, and formats the final response.

- **Reasoning Engine**  
  Performs the logic required to decide which tools to invoke and handles message context.

- **MCP Host / Tool Server**  
  Acts as a bridge between the orchestrator and agentic tools in the mesh.

## Diagrams

### Sequence Flow Diagram  

Shows the runtime message path from user input to tool response and back.

👉 [View sequence.mmd](./sequence.mmd)

### Slim Architecture Diagram  

Illustrates the system layers: UI → Orchestrator → Mesh.

👉 [View structure.mmd](./structure.mmd)
