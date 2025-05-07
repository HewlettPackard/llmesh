# LLM Agentic Tool Mesh

Welcome to LLM Agentic Tool Mesh, a pioneering initiative by HPE Athonet aimed at democratizing Generative Artificial Intelligence (Gen AI). Our vision is to make Gen AI accessible and beneficial to a broader audience, enabling users from various backgrounds to leverage cutting-edge Gen AI technology effortlessly.

## Understanding the Challenges

Gen AI has the potential to revolutionize businesses, but adopting it comes with challenges:

- **Technical Complexity**: Gen AI tools are powerful but often require both coding and machine learning expertise. This makes it difficult for companies to use these tools effectively without specialized skills.
- **Organizational Challenges**: Simply adding a Gen AI team isn’t enough. The real value comes from using the knowledge of your existing teams, especially those who may not be tech experts. However, if not done right, Gen AI can impact team dynamics. It’s important to find ways to use Gen AI that enhance collaboration and make the most of everyone’s expertise.

## Our Approach

LLM Agentic Tool Mesh empowers users to create tools and web applications using Gen AI with Low or No Coding. This approach addresses the technical challenges by simplifying the integration process. By leveraging the Pareto principle, LLM Agentic Tool Mesh focuses on the 20% of features that cover 80% of user needs. This is achieved by abstracting complex, low-level libraries into easy-to-understand services that are accessible even to non-developers, effectively hiding the underlying complexity.

This simplicity not only helps technical teams but also enables non-technical teams to develop tools related to their domain expertise. The platform then allows for the creation of a "Mesh" of these Gen AI tools, providing orchestration capabilities through an agentic Reasoning Engine based on Large Language Models (LLMs). This orchestration ensures that all tools work together seamlessly, enhancing overall functionality and efficiency across the organization.

## Quick Start

We have created a series of tools and examples to demonstrate what you can do with LLM Agentic Tool Mesh. To get started, follow these steps to set up your environment, understand the project structure, and run the tools and web applications provided.

### Folder Structure

The project is organized into the following directories:

- **src**: Sourve code
  - **lib**: Contains **`athon`** the agentic-python library with all self-serve platform services for creating tools and web applications. These services are grouped into:
    - **Chat Services**
    - **RAG (Retrieval-Augmented Generation) Services**
    - **Agent Services**
    - **System Platform Services**
  - **platform**: Includes the **`agentic tool mesh`** with examples of Gen AI applications that demonstrate various capabilities:
    - **Tool Examples**: Demonstrates how to call an API, improve text, generate code, retrieve information from documents using RAG, and use a multi-agent system to solve complex tasks.
    - **Web Applications**:
      - A chatbot that orchestrates all these tools.
      - An agentic memory for sharing chat messages among different users.
      - A back panel that allows configuring a tool via a user interface.
  - **notebooks**: Contains interactive Jupyter notebooks to explore LLM Agentic Tool Mesh functionalities:
    - **Platform Seervices**: Notebooks to try Chat, RAG, and Agent services.
    - **Meta-Prompting**: Notebooks for creating an eCustomer Support Service agent using meta-prompting.
- **policies**: Contains a set of governance policies and standards to ensure consistency, ethical adherence, and quality across all tools.

### Prerequisites

Before setting up the LLM Agentic Tool Mesh platform, please ensure the following prerequisites are met:

#### General Requirements

- **API Key**: Set your ChatGPT API key by assigning it to the `OPENAI_API_KEY` environment variable.
- **Python 3.11**: Ensure Python 3.11 is installed on your machine.

  - It's recommended to install **`uv`**, a drop-in replacement for `pip`, `venv`, and other Python tooling.
  - You can install `uv` either via script or with `pip`:

  **Option 1: Install via script (macOS/Linux)**

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source $HOME/.local/bin/env
  ```

  **Option 2: Install via pip**

  ```bash
  pip install uv
  ```

  - Optional: Enable shell completions

  ```bash
  echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
  echo 'eval "$(uvx --generate-shell-completion bash)"' >> ~/.bashrc
  ```

  > Note: "Drop-in" means you can use `uv` in place of the original tools (e.g., `pip`, `venv`) without changing your workflow.

### Installation Options

#### Option 1: Install LLM Agentic Tool Mesh Services Only

If you only need the core LLM Agentic Tool Mesh services without the example applications, you can install them directly via `uv pip`:

  ```bash
  uv pip install -e '.[all]'
  ```

After installation, refer to the [Usage Guide](https://github.com/HewlettPackard/llmesh/wiki/Usage#using-library-services) for instructions on using platform services.

#### Option 2: Full Example Setup

To use the complete setup, including examples and demo applications, follow these steps:

1. **Clone the Repository**: Download the LLM Agentic Tool Mesh repository to your local machine.

   ```bash
   git clone https://github.com/HewlettPackard/llmesh.git
   cd llmesh
   ```

2. **Install Dependencies**: All dependencies required by the platform are specified in the `pyproject.toml` file. Use the following commands to install them:

  ```bash
  # Install with all extras
  uv pip install -e ".[all]"

  # Install with specific extras
  uv pip install -e ".[chat,agents,rag]"

  # Install with development/testing dependencies
  uv pip install -e ".[all,test]"
  ```

3. **Setup for Specific Tools**: Some tools, including **tool_rag**, **tool_agents**, and **tool_analyzer**, require additional setup (e.g., copying specific data files and initializing configurations). For detailed setup instructions, refer to the [Installation Guide](https://github.com/HewlettPackard/llmesh/wiki/Installation).

### Running the UIs

You can run the tools and web applications individually or use the provided script `src/infra/scripts/start_examples.sh` to run them all together. Once everything is started, you can access the chatbot app at [https://127.0.0.1:5001/](https://127.0.0.1:5001/) and the back panel at [https://127.0.0.1:5011/](https://127.0.0.1:5011/).

### Running the Games

You can run the game web application individually or use the provided script `run_games.sh` to run them all together. Once everything is started, you can access the chatbot app at [https://127.0.0.1:5001/](https://127.0.0.1:5001/). Have fun :) !!!

## References

For more details about installation, usage, and advanced configurations, please visit the [LLM Agentic Tool Mesh project Wiki](https://github.com/HewlettPackard/llmesh/wiki).

## Contact

If you have any questions or need further assistance, feel free to contact me at <antonio.fin@hpe.com>.
