# Deployment Guide

This document explains how to deploy the current Hybrid RAG API to EC2 or EKS.

It keeps deployment guidance separate from the main README.

## Runtime Pieces

The service depends on these runtime components:

1. FastAPI application
2. Qdrant vector store
3. Ollama model server
4. frontend static app, if you want a real browser UI
5. LangSmith tracing, if enabled

For real production, add these before public exposure:

1. persistent chat memory such as Redis or Postgres
2. auth and authorization
3. secret management
4. monitoring and logs
5. backups for Qdrant data

## Recommended Path

1. Start with EC2
2. Externalize session memory
3. Add auth and rate limiting
4. Move to EKS only if scaling or team operations justify it

## EC2 Deployment

### When EC2 is the right fit

Choose EC2 when:

- you want the simplest first deployment
- you want direct control over Ollama runtime and model placement
- one host or a small number of hosts is enough

### EC2 layout

Simple first layout:

1. FastAPI and Ollama on one EC2 machine
2. Qdrant on the same host or a second host
3. LangSmith external

### EC2 deployment steps

1. Provision the instance
2. Install Python, Docker, and Ollama
3. Pull the models referenced in `.env`
4. Start Qdrant
5. Install Python dependencies from `requirements.txt`
6. Create `.env`
7. Start FastAPI under `systemd` or another process manager
8. Put a load balancer or reverse proxy in front if exposing externally

### Example EC2 service shape

Run these as separate managed processes:

1. `ollama serve`
2. Qdrant
3. FastAPI via `uvicorn` or `gunicorn` with Uvicorn workers

### EC2 checklist

1. confirm `OLLAMA_BASE_URL` points to the correct Ollama host
2. confirm `QDRANT_URL` points to the correct Qdrant host
3. confirm LangSmith env vars are present if tracing is required
4. keep Qdrant data on persistent storage
5. restrict ingest access

## EKS Deployment

### When EKS is the right fit

Choose EKS when:

- you need separate scaling for API and storage layers
- you already operate Kubernetes
- you need clearer workload separation and cluster-level ops

### EKS layout

Recommended workloads:

1. FastAPI deployment
2. Qdrant stateful workload with persistent volume
3. Ollama deployment or dedicated model-serving node pool
4. Redis or Postgres for persistent session memory
5. ingress controller or API gateway
6. secret and config management

### EKS cautions

1. do not keep session memory in-process across multiple replicas
2. do not rely on pod-local disk for Qdrant persistence
3. do not scale Ollama without planning node capacity and warm-up time
4. keep backups and restore paths explicit

### EKS migration work from this repo

1. replace `app/memory.py` with Redis or database-backed history
2. move secrets into Kubernetes secrets
3. add readiness and liveness probes
4. add auth before public exposure
5. separate Qdrant persistence from stateless API pods

## UI Concept For Real Deployment

This repo intentionally does not include a frontend, but the natural user-facing product on top of this API would have:

1. login and workspace selection
2. document upload and ingest screen
3. chat screen with citations and retrieved source panel
4. conversation history list
5. admin view for traces and ingestion status

The current `/ingest` and `/chat` APIs are the backend contract for that UI.

The current repo now includes a lightweight static frontend in `frontend/`. In real deployment, serve those static assets from a small web server, CDN, or ingress-backed frontend service.

## Current Production Gaps

Not production-ready yet:

1. in-memory chat memory
2. no auth
3. no infra manifests or scripts in repo
4. no background ingest queue
5. no backup strategy documented for Qdrant data

## Best Next Steps

1. replace in-memory memory with Redis
2. add auth around ingest and chat
3. deploy on EC2 first
4. add a small web UI
5. move to EKS once scaling needs are proven