# LL-Mesh

Welcome to LL-Mesh, a pioneering initiative by HPE Athonet aimed at democratizing Generative Artificial Intelligence (Gen AI). Our vision is to make Gen AI accessible and beneficial to a broader audience, enabling users from various backgrounds to leverage cutting-edge Gen AI technology effortlessly.

## Understanding the Challenges

Gen AI has the potential to revolutionize businesses, but adopting it comes with challenges:

- **Technical Complexity**: Gen AI tools are powerful but often require both coding and machine learning expertise. This makes it difficult for companies to use these tools effectively without specialized skills.
- **Organizational Challenges**: Simply adding a Gen AI team isn’t enough. The real value comes from using the knowledge of your existing teams, especially those who may not be tech experts. However, if not done right, Gen AI can impact team dynamics. It’s important to find ways to use Gen AI that enhance collaboration and make the most of everyone’s expertise.

## Our Approach

LL-Mesh empowers users to create tools and web applications using Gen AI with Low or No Coding. This approach addresses the technical challenges by simplifying the integration process. By leveraging the Pareto principle, LL-Mesh focuses on the 20% of features that cover 80% of user needs. This is achieved by abstracting complex, low-level libraries into easy-to-understand services that are accessible even to non-developers, effectively hiding the underlying complexity.

This simplicity not only helps technical teams but also enables non-technical teams to develop tools related to their domain expertise. The platform then allows for the creation of a "Mesh" of these Gen AI tools, providing orchestration capabilities through an agentic Reasoning Engine based on Large Language Models (LLMs). This orchestration ensures that all tools work together seamlessly, enhancing overall functionality and efficiency across the organization.

## Quick Start

We have created a series of tools and examples to demonstrate what you can do with LL-Mesh. To get started, follow these steps to set up your environment, understand the project structure, and run the tools and web applications provided.

### Folder Structure

The project is organized into the following directories:

- **self_serve_platform**: Contains all self-serve platform services for creating tools and web applications. These services are grouped into:
  - **Chat Services**
  - **RAG (Retrieval-Augmented Generation) Services**
  - **Agent Services**
  - **System Platform Services**
- **examples**: Includes four Gen AI tools based on LLMs that demonstrate various capabilities:
  - **Tool Examples**: Demonstrates how to call an API, improve text, generate code, retrieve information from documents using RAG, and use a multi-agent system to solve complex tasks.
  - **Web Applications**:
    - A chatbot that orchestrates all these tools.
    - An agentic memory for sharing chat messages among different users.
    - A back panel that allows configuring a tool via a user interface.
- **federated_governance**: Contains a set of governance policies and standards to ensure consistency, ethical adherence, and quality across all tools.

### Prerequisites

Before setting up the LL-Mesh platform, please ensure the following prerequisites are met:

#### General Requirements

- **Python 3.11**: Ensure Python 3.11 is installed on your machine.
- **API Key**: Set your ChatGPT API key by assigning it to the `OPENAI_API_KEY` environment variable.

### Installation Options

#### Option 1: Install LL-Mesh Services Only

If you only need the core LL-Mesh services without the example applications, you can install them directly via `pip`:

  ```bash
  pip install llmesh[all]
  ```

After installation, refer to the [Usage Guide](https://github.com/HewlettPackard/llmesh/wiki/Usage) for instructions on using platform services.

#### Option 2: Full Example Setup

To use the complete setup, including examples and demo applications, follow these steps:

1. **Clone the Repository**: Download the LL-Mesh repository to your local machine.

   ```bash
   git clone https://github.com/HewlettPackard/llmesh.git
   cd llmesh
   ```

2. **Install Dependencies**: All dependencies required by the platform are specified in the `pyproject.toml` file. Use the following commands to install them:

   ```bash
   pip install poetry
   poetry install --all-extras
   ```

3. **Setup for Specific Tools**: Some tools, including **tool_rag**, **tool_agents**, and **tool_analyzer**, require additional setup (e.g., copying specific data files and initializing configurations). For detailed setup instructions, refer to the [Installation Guide](https://github.com/HewlettPackard/llmesh/wiki/Installation).

### Running the UIs

You can run the tools and web applications individually or use the provided script `run_examples.sh` to run them all together. Once everything is started, you can access the chatbot app at [https://127.0.0.1:5001/](https://127.0.0.1:5001/) and the back panel at [https://127.0.0.1:5011/](https://127.0.0.1:5011/). Have fun :) !!!

## References

For more details about installation, usage, and advanced configurations, please visit the [Athon project Wiki](https://github.com/HewlettPackard/llmesh/wiki).

## Contact

If you have any questions or need further assistance, feel free to contact me at <antonio.fin@hpe.com>.