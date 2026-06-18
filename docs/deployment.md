# Deployment and User Operations Guide

This document describes how to deploy the platform stack in production-like environments and outlines a operational guide for support agents and administrator roles.

---

## Production Deployment Checklist

### 1. Database Scaling (PostgreSQL)
For production, avoid sqlite file paths. Update the database URL target in `.env` to point to a high-availability PostgreSQL cluster:
`DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>`

### 2. High-Performance Model Serving (vLLM / Triton)
Instead of local CPU sentence-transformers or LangGraph mocks:
1. Spin up an instance of **vLLM** or **TensorFlow Serving** hosting Qwen-3 or Llama-3.
2. In the `.env` configuration, update the LLM provider environment variables:
   ```env
   LLM_PROVIDER=openai  # vLLM is OpenAI API-compatible
   LLM_API_KEY=your-vllm-token
   LLM_MODEL_NAME=Qwen/Qwen1.5-7B-Chat
   ```

---

## Telemetry & Logging Setup

The docker-compose setup spins up Prometheus and Grafana automatically.

### 1. Prometheus Telemetry
Prometheus scrapes the API metrics endpoint `/api/metrics` every 15 seconds.
- Access the web UI at `http://localhost:9090`.
- Verify the API target status by navigating to **Status -> Targets**. The `customer_support_backend` endpoint should show **UP**.

### 2. Grafana Dashboards
- Access Grafana at `http://localhost:3000`.
- Credentials: `admin` / `admin`.
- Click **Data Sources** and add a Prometheus data source pointing to `http://prometheus:9090`.
- Build custom telemetry panels graphing request rates, database queries, and response latencies.

---

## User Operations Guide

### A. Customer Portals
1. Navigate to the landing domain `http://localhost:5173`.
2. Interact with the chat bot using Bangla or English keywords.
3. Use the **Mic** button to test speech-to-text inputs.
4. If the conversation requires custom support or displays negative sentiment, notice the **Ticket Escalated** card appears instantly on the left menu.
5. Provide helpfulness rating feedback at the end of the conversation.

### B. Support Agent Dashboard
1. Click the **Agent Portal** option in the top navigation bar.
2. Log in using `agent@example.com` / `agentpassword123`.
3. View the customer queue on the **Open Tickets** tab.
4. Click **Start Working** to assign a ticket to yourself, changing its status to `In Progress`.
5. Once resolved, click the green check mark to finalize the issue and remove it from the active queue.

### C. Administrator Configurations
1. Log in using `admin@example.com` / `adminpassword123`.
2. Inspect the **Insights & Analytics** tab to verify conversation volume and sentiment distribution trends.
3. Open the **Seed Knowledge Base** tab. Drag-and-drop a corporate PDF guide or FAQ CSV and click **Ingest File** to dynamically load semantic embeddings into the ChromaDB vector store.
