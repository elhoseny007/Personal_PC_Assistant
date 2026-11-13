# Personal_PC_Assistant
An AI-powered personal desktop assistant that combines LLMs, RAG, web search, file management, and Windows PC automation in one intelligent application.
SonnaAI 🤖

It combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), intelligent tool routing, and PC automation into one application.

🚀 Key Features

🧠 AI Assistant

Intelligent chat powered by Groq LLMs.

Simple and complex query routing.

Automatic model selection based on task complexity.

Context-aware conversations.

📚 Retrieval-Augmented Generation (RAG)

Upload and index local documents.

Persistent FAISS vector storage.

Hybrid retrieval using dense vector search and BM25.

Reranking for more relevant results.

Semantic caching with TTL-based expiration.

Supported document formats: PDF, DOCX, TXT, and Markdown.

🔎 Web Research

Web search powered by Tavily.

Retrieve relevant online information.

Search-based question answering.

💻 Windows PC Automation

Search for files and folders.

Create files, folders, Word documents, and Excel spreadsheets.

Open applications and folders.

Count images.

Retrieve system status.

Permission-based execution and action auditing.

☁️ Google Drive Integration

Upload local files to an authenticated Google Drive account.

Integrate cloud storage with desktop workflows.

🏗️ Architecture

SonnaAI follows a modular agent-based architecture:

User Interface: Desktop interaction through the application interface.

API Layer: FastAPI handles application requests.

Orchestration Layer: Routes requests to the appropriate execution workflow.

LLM Layer: Groq models handle language understanding and generation.

RAG Layer: Retrieves relevant information from indexed documents.

Tools Layer: Executes PC automation, web search, and cloud operations.

Security Layer: Applies permission checks and maintains action logs.

🛠️ Tech Stack

Category

Technologies

Programming Language

Python

LLM Provider

Groq

Backend

FastAPI

Desktop Integration

PyWebView

Web Search

Tavily

RAG

FAISS, BM25

Document Processing

PDF, DOCX, TXT, Markdown

Environment Management

Python dotenv

Cloud Storage

Google Drive API
🔐 Security

SonnaAI incorporates:

Permission-based tool execution.

Risk-level handling for PC operations.

Action auditing.

Environment-based API key management.

🎯 Project Goal

The goal of SonnaAI is to build a practical personal AI assistant that goes beyond text generation by combining reasoning, information retrieval, external tools, and real-world desktop automation.

👨‍💻 Developer

Elhoseny Hassan

GitHub: [elhoseny007](https://github.com/elhoseny007)

LinkedIn: https://www.linkedin.com/in/elhoseny-hassan-65561b191/

Built with Python, LLMs, RAG, and AI-powered automation.
Version Control

Git & GitHub
