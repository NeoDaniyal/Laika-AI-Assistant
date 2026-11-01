# 🐾 Laika AI - Intelligent AI Assistant with RAG & Long-Term Memory

**Laika AI** is an intelligent conversational AI assistant designed to go beyond traditional chatbot functionality. Built with FastAPI, React, and MongoDB, Laika combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), long-term memory, and tool calling to deliver contextual and personalized conversations.

The project focuses on building an AI assistant capable of maintaining conversation history, retrieving information from uploaded documents, remembering relevant user preferences, and executing supported tools.

## 🚀 Features

### 1. AI-Powered Conversations
- Integration with Inception Labs Mercury-3.
- Streaming responses for real-time interaction.
- Context-aware conversation handling.
- Prompt engineering and context management.
- Markdown rendering and code syntax highlighting.

### 2. Retrieval-Augmented Generation (RAG)
- Document ingestion and processing.
- Support for TXT, PDF, DOCX/DOC, and CSV files.
- Text cleaning and chunking with overlapping sections.
- Semantic embeddings using Sentence Transformers.
- Vector similarity search using cosine similarity.
- Context retrieval to improve response relevance.

### 3. Long-Term Memory
- Automatic extraction of relevant user information.
- Persistent memory storage using MongoDB.
- Memory updating and deduplication.
- Contextual personalization across conversations.

### 4. Chat History Management
- Persistent conversation storage.
- Create, rename, and delete conversations.
- Retrieve previous conversations.
- Edit the latest prompt and regenerate responses.

### 5. Tool Calling
Laika includes a modular tool system with registered tools such as:
- Calculator
- Web Search
- Image Generation
- Image-to-Image Processing
- Video Generation
- Local Video Animation

### 6. Authentication and Security
- User registration and login.
- Authentication and protected API endpoints.
- User-specific conversation and memory management.

### 7. Observability and Evaluation
- Structured JSON logging.
- Request ID tracking.
- LLM generation latency monitoring.
- First-token latency tracking.
- RAG retrieval performance monitoring.
- LLM and RAG evaluation pipelines.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python, JavaScript |
| Frontend | React, Vite |
| Backend | FastAPI |
| Database | MongoDB |
| LLM | Inception Labs Mercury-3 |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Search | Cosine Similarity |
| AI Integration | OpenAI-compatible SDK |
| Frontend Rendering | React Markdown, Syntax Highlighting |
| Deployment | Vercel, Render |
| Production Database | MongoDB Atlas |

## 🏗️ System Architecture

```text
                    USER
                     |
                     v
             REACT + VITE FRONTEND
                  (Vercel)
                     |
                     | HTTP / SSE
                     v
               FASTAPI BACKEND
                  (Render)
                     |
          +----------+----------+
          |          |          |
          v          v          v
       MongoDB    LLM API    TOOL SYSTEM
       Atlas    Mercury-3   Calculator
          |                   Web Search
          |                   Image Tools
          |                   Video Tools
          |
    +-----+----------------+
    |                      |
    v                      v
 CHAT HISTORY          LONG-TERM MEMORY
    |
    v
 RAG PIPELINE
    |
    +--> Document Processing
    |
    +--> Text Chunking
    |
    +--> Embedding Generation
    |
    +--> Vector Similarity Search
    |
    +--> Context Retrieval
    |
    v
 CONTEXT-AWARE RESPONSE
```

## 🧠 How RAG Works in Laika

Laika uses Retrieval-Augmented Generation to provide answers based on information contained in uploaded documents.

The pipeline follows these steps:

1. **Document Upload:** The user uploads a supported document.
2. **Text Extraction:** Text is extracted from the document.
3. **Text Cleaning:** Unnecessary whitespace and formatting are normalized.
4. **Chunking:** Text is divided into smaller overlapping chunks.
5. **Embedding Generation:** Each chunk is converted into a numerical vector using `all-MiniLM-L6-v2`.
6. **Storage:** Document chunks and their embeddings are stored in MongoDB.
7. **Retrieval:** User queries are converted into embeddings and compared with stored vectors.
8. **Context Injection:** Relevant retrieved information is added to the LLM context.
9. **Response Generation:** Mercury-3 generates a response using the available context.

## 🧩 Project Structure

```text
Laika/
│
├── backend/
│   ├── auth.py
│   ├── context.py
│   ├── database.py
│   ├── embeddings.py
│   ├── llm.py
│   ├── main.py
│   ├── memory.py
│   ├── observability.py
│   ├── prompts.py
│   ├── rag.py
│   ├── summarizer.py
│   ├── vector_search.py
│   │
│   ├── evaluation/
│   │   ├── dataset.json
│   │   ├── rag_dataset.json
│   │   ├── evaluate.py
│   │   ├── evaluate_rag.py
│   │   └── LAIKA_EVALUATION_REPORT.md
│   │
│   └── tools/
│       ├── base.py
│       ├── calculator.py
│       ├── image_generation.py
│       ├── image_to_image.py
│       ├── local_video_animation.py
│       ├── registry.py
│       ├── video_generation.py
│       └── web_search.py
│
├── frontend/
│   └── React + Vite application
│
└── README.md
```

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.11+
- Node.js and npm
- MongoDB
- Mercury-3 API access

### 1. Clone the Repository

```bash
git clone https://github.com/NeoDaniyal/Laika.git
cd Laika
```

### 2. Backend Setup

```bash
cd backend

python -m venv venv
```

Activate the virtual environment.

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file inside the backend directory.

```env
MONGODB_URI=your_mongodb_connection_string
DATABASE_NAME=laika
HF_TOKEN=your_mercury_api_key
```

Use the actual environment variable names configured in your backend. Never commit real API keys or database credentials.

### 4. Start the Backend

```bash
uvicorn main:app --reload
```

Backend development server:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will display its local URL in the terminal.

## 📊 Evaluation

Laika includes separate evaluation workflows for LLM responses and RAG retrieval.

### LLM Evaluation

An initial evaluation using four test cases produced:

| Metric | Result |
|---|---:|
| Correctness | 5/5 |
| Relevance | 5/5 |
| Completeness | 5/5 |
| Average Latency | 1.776 seconds |

These results represent a small initial evaluation, not a comprehensive benchmark.

### RAG Evaluation

An initial evaluation using 20 queries produced:

| Metric | Result |
|---|---:|
| Recall@1 | 0.425 |
| Recall@2 | 0.575 |
| Recall@5 | 0.750 |
| Recall@8 | 0.875 |
| MRR | 0.6392 |
| Average Retrieval Latency | 60.91 ms |

These measurements reflect the evaluation dataset and configuration used at the time of testing.

## 🌐 Deployment

Laika's deployment architecture:

| Component | Hosting |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | MongoDB Atlas |
| LLM | Inception Labs API |

**Deployment note:** The application is configured as a public demonstration project. Free hosting services may have resource, uptime, and storage limitations. Uploaded files and generated media require persistent cloud storage for reliable production use.

## 🔮 Future Improvements

- Improve RAG retrieval accuracy and ranking.
- Expand evaluation datasets and test coverage.
- Implement more advanced memory management.
- Improve document retrieval and summarization.
- Optimize model loading and inference performance.
- Add more intelligent tools and integrations.
- Improve deployment reliability and scalability.
- Enhance the user experience and responsive design.

## 👨‍💻 Author

**Syed Daniyal Syed Javed**

BCA (Science) | Computer Science

- GitHub: [@NeoDaniyal](https://github.com/NeoDaniyal)

Laika AI is a personal AI engineering project developed to explore and implement practical concepts in Large Language Models, Retrieval-Augmented Generation, vector search, AI agents, backend development, and full-stack application engineering.

---

⭐ If you find this project interesting, consider giving it a star on GitHub.

**Built with curiosity, Python, and a passion for AI.**