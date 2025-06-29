# LAT-Mesh RAG Service Architecture

## Overview

The **LAT-Mesh RAG Service** is a modular, pluggable system designed to enrich user queries with relevant document context using retrieval-augmented generation techniques. It orchestrates document ingestion, vector store creation, query augmentation, retrieval, reranking, and summarization—providing accurate, explainable, and grounded LLM responses.

This architecture enables:

* Efficient ingestion and transformation of technical documents,
* Fast semantic retrieval of relevant chunks,
* Query refinement using custom augmentation prompts,
* Optional reranking with cross-encoders,
* Contextual answer summarization using LLMs.

## Components

### RAG Service Interface

* **Entry Point**
  Accessible via the `retrieve()` method in `platform.rag.main`. Acts as the primary user-facing interface for question answering.

* **Orchestration Flow**
  Follows a linear RAG pipeline:
  `query → [optional augmentation] → retrieve → rerank → summarize → return answer`

### Document Loader

* **Responsible for ingestion and transformation**

  * Loads documents from file system using YAML-configured paths.
  * Extracts text using pluggable extractors.
  * Transforms extracted elements via configured NLP actions (e.g., chunking, cleaning).
  * Persists data into a vector store collection.

### Retriever

* **Semantic Search Layer**

  * Uses vector similarity to find chunks relevant to a query.
  * Configurable retriever strategy (e.g., Chroma, Milvus, Qdrant).

### Query Augmentor

* **Optional Query Expansion**

  * Supports “HyDE” (Hypothetical Document Embeddings) and general expansion.
  * Uses system prompts to guide augmentation via LLM.

### Reranker

* **Optional Post-Retrieval Filtering**

  * Uses a cross-encoder model (e.g., BERT-based) to rerank chunks based on true relevance to the original query.
  * Produces a refined list of top-k results.

### Summarizer

* **Final Answer Generator**

  * Summarizes the top retrieved document chunks into a coherent response.
  * Uses templated prompts (YAML-configured) for consistent tone and structure.

### Chunk Presenter

* **Supplementary JSON Output**

  * Formats the top retrieved chunks (with source, header, score) into a readable code block.
  * Appended after the main summary to improve transparency.

## Diagrams

### Sequence Flow Diagram

Illustrates the end-to-end runtime of the RAG process.

👉 [View sequence\_rag.mmd](./sequence_rag.mmd)

### Component Interaction Diagram

Shows how loader, retriever, reranker, and summarizer connect under `retrieve()`.

👉 [View structure\_rag.mmd](./structure_rag.mmd)
