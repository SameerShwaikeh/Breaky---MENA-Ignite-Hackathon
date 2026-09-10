# BREAKY — Tooling Guide

# This document lists the tools and frameworks the agent layer (Phase 2) will use, selected from the hackathon's official Resource \& Tooling Guide (GSMA MENA). Everything below has a free tier and requires no credit card.

# Stack Summary

# Layer

# Choice

# Why

# &#x20;

# LLM provider

# Groq (Llama 3.3 70B) — fallback: Google AI Studio (Gemini 2.5 Flash)

# Free tier, high rate limits, native function/tool calling, very fast inference (important for a live demo)

# Agent approach

# Direct tool-calling loop using the LLM provider's native function-calling API — no heavy multi-agent framework

# Our pipeline is a single linear decision flow (identity → location → network → model → stock → alert), not a multi-agent negotiation. TOOLS is already defined in agent/run\_agent.py in JSON-schema form, ready to hand to the LLM directly. Frameworks like CrewAI/LangGraph add setup overhead we don't have time for in a 3-day hackathon.

# LLM memory / Vector DB

# None

# The LLM itself is stateless — each report is decided independently, with no conversational memory or document retrieval (RAG) needed. Note: this is separate from outbreak-pattern memory over time, which is not an LLM/vector-DB concern — see below.

# Demo / UI

# Streamlit Community Cloud

# Already in requirements.txt; free, one-click deploy, fastest way to get a live dashboard for the recorded demo.

# Data source

# CAMARA APIs via Nokia Network-as-Code

# Already wired in camara/client.py (mock/live switch).

# 

# 

# Rationale

# The hackathon guide (Section 11, "Tips for Participants") explicitly recommends picking one focused, polished agent over a complex multi-agent system — this favors our simple tool-calling approach.

# Groq and Gemini both support structured function calling matching the shape of our existing TOOLS schema, so Phase 2 is mostly "pass TOOLS to the LLM API and loop," not a rewrite.

# No framework lock-in: if Groq rate limits are hit during the demo, we can swap to Gemini with minimal code change since both use a similar tool-calling interface.

# 

# How outbreak history is actually remembered (important distinction)

# Detecting an outbreak requires comparing today's case count against the pattern over the past days/weeks — that IS a form of memory, but it's handled by the existing SQL database (backend/db.py, table Record), not by an LLM memory layer:

# Every incoming report is persisted permanently via /ingest into the Record table.

# When run\_anomaly\_detection(city, syndrome) runs, it calls /aggregate, which queries all past records for that city/syndrome and returns daily counts.

# anomaly.py computes a rolling z-score over a 14-day window on those counts — so a report arriving 5 hours after another, or 2 days after, is automatically compared against that history.

# This is why no vector DB is needed: the "memory" required here is structured time-series data (case counts per day), which a relational database handles natively and more reliably than a vector/embedding store — vector DBs are for semantic search over unstructured text, which isn't what outbreak detection needs.

# 

# Explicitly Not Used (and why)

# CrewAI / LangGraph / AutoGen — designed for multi-agent collaboration; unnecessary complexity for a single linear pipeline.

# Vector DBs (Chroma, Pinecone, Qdrant, etc.) — outbreak history is structured time-series data already served by the SQL database's /aggregate endpoint; no semantic/document retrieval is needed.

# Voice tools (ElevenLabs, Deepgram, etc.) — out of scope for this prototype.

# 

# Fallback Plan

# If live API calls are rate-limited during the demo, the agent falls back to cached/mock responses (already supported via CAMARA\_MODE=mock in camara/client.py) so the pipeline never blocks the demo.



