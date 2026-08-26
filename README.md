# Aster & Row Support Agent

A RAG-based AI customer support assistant for Aster & Row ecommerce company built using Python, Google Gemini, and Streamlit.

The agent helps customers with:
- Return policies
- Shipping information
- Warranty queries
- Product questions
- Membership information
- Order tracking


## Features

### RAG Knowledge Retrieval

- Semantic search over knowledge base documents
- Metadata-based document ranking
- Prioritizes active official policies
- Filters internal and outdated documents
- Provides source citations


### Order Lookup Tool

Supports customer order queries:

Example:
Where is ORD-1007?

Features:
- Order ID validation
- Secure order retrieval
- Customer-safe responses
- Sensitive data filtering


### Privacy Protection

The system prevents exposure of:

- Customer names
- Emails
- Addresses
- Internal notes
- Risk scores
- Warehouse information


### Multi-turn Conversation

The assistant maintains conversation context.

Example:

User:
Do you ship internationally?

User:
What about Canada?

Assistant:
Uses previous conversation context to answer correctly.


### Conflict Detection

The system detects conflicting official documents.

Example:

Document 1:
Hand wash stainless steel body

Document 2:
All components are dishwasher safe

The assistant identifies the conflict and avoids making unsupported decisions.


### Debug Mode

Enable:

DEBUG=true

Debug output includes:
- Retrieved documents
- Metadata
- Similarity scores
- Ranking information



# Architecture


User
|
Streamlit UI / CLI
|
Gemini AI Agent
|
+----------------+
|                |                
RAG Retrieval   Order Lookup
|
Knowledge Base


# Technology Stack
Language:
Python 3.12

LLM:
Google Gemini

Frontend:
Streamlit

Retrieval:
Custom RAG pipeline

Testing:
Pytest

Environment:
Python dotenv



# Project Structure


AI-Agent/

app/
    agent.py
    rag
        ingest.py
        retriever.py
        conflicts.py
    tools/
        orders.py

knowledge-base/
    Policy and product documents


data/
    orders.json


evaluation/
    visible-cases.json
    custom-cases.json
    run_evaluation.py


tests/
    pytest test files


streamlit_app.py

requirements.txt

README.md



# Installation


Clone repository:

git clone https://github.com/Blessina03/AI-Agentproject.git

cd AI-Agentproject


Create virtual environment:

python -m venv .venv


Activate environment:

Windows:

.venv\Scripts\activate


Install dependencies:

pip install -r requirements.txt



# Environment Setup


Create a .env file:

GEMINI_API_KEY=your_api_key_here

DEBUG=false



# Running the Application


Streamlit:

streamlit run streamlit_app.py


CLI:

python app/agent.py



# Testing


Run unit tests:

pytest tests -v


Run evaluation:

python -m evaluation.run_evaluation


Evaluation covers:

- RAG retrieval
- Order lookup
- Privacy protection
- Prompt security
- Multi-turn conversations
- Conflict handling



# Bug Fixes


## Bug 1: Privacy Data Exposure

Problem:
Order lookup returned sensitive customer information.

Root Cause:
No field filtering.

Fix:
Implemented customer-safe field whitelist.

Result:
Only approved fields are returned.



## Bug 2: Cancelled Order Showing Old ETA

Problem:
Cancelled orders displayed previous delivery dates.

Root Cause:
Old tracking information remained available.

Fix:
Removed ETA and tracking details for cancelled orders.

Result:
No incorrect delivery information is shown.



## Bug 3: Missing Delivery Estimate

Problem:
Agent generated estimated delivery dates when unavailable.

Root Cause:
Missing ETA handling.

Fix:
Added explicit delivery estimate unavailable status.

Result:
Agent clearly informs users when ETA is unavailable.



# Author

Blessina

GitHub:
https://github.com/Blessina03