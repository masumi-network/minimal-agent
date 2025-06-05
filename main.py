# main.py

import time
import uuid
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

# --- UPDATED: Import the new EchoAgentService ---
from echo_agent_service import EchoAgentService, AGENT_IDENTIFIER, SELLER_VKEY, INPUT_SCHEMA

# Load environment variables (harmless to keep, even if .env is empty)
load_dotenv()

# --- UPDATED: Initialize the new service ---
agent = EchoAgentService()

# --- UPDATED: Update app title and description ---
app = FastAPI(
    title="MIP-003 Compliant Echo Agent",
    description="An agent that receives text and returns it repeated 3 times.",
    version="1.0.0"
)

# --- Pydantic Models (unchanged) ---
class StartJobRequest(BaseModel):
    identifier_from_purchaser: str
    input_data: Dict[str, Any]

class Amount(BaseModel):
    amount: int
    unit: str

class StartJobResponse(BaseModel):
    status: str
    job_id: str
    blockchainIdentifier: str
    submitResultTime: int
    unlockTime: int
    externalDisputeUnlockTime: int
    agentIdentifier: str
    sellerVKey: str
    identifierFromPurchaser: str
    amounts: List[Amount]
    input_hash: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
    result: Optional[str] = None

# --- API Endpoints (almost unchanged) ---

@app.get("/availability", tags=["MIP-003 Required"])
def get_availability():
    return {
        "status": "available",
        "type": "masumi-agent",
        "message": "Echo Agent is ready to accept jobs."
    }

@app.get("/input_schema", tags=["MIP-003 Required"])
def get_input_schema():
    return INPUT_SCHEMA

@app.post("/start_job", response_model=StartJobResponse, status_code=201, tags=["MIP-003 Required"])
def start_job(request: StartJobRequest, background_tasks: BackgroundTasks):
    # UPDATED: Validate against the new schema key
    if "text_input" not in request.input_data:
        raise HTTPException(status_code=400, detail="Input data must contain a 'text_input' field.")

    job_info = agent.start_new_job(request.identifier_from_purchaser, request.input_data)
    background_tasks.add_task(agent._process_job, job_info['job_id'])
    current_time = int(time.time())

    return StartJobResponse(
        status="success",
        job_id=job_info['job_id'],
        blockchainIdentifier=f"block_{uuid.uuid4().hex[:12]}",
        submitResultTime=current_time + 3600,
        unlockTime=current_time + 3700,
        externalDisputeUnlockTime=current_time + 7200,
        agentIdentifier=AGENT_IDENTIFIER,
        sellerVKey=SELLER_VKEY,
        identifierFromPurchaser=request.identifier_from_purchaser,
        amounts=[{"amount": 100000, "unit": "lovelace"}], # Lower price!
        input_hash=job_info['input_hash']
    )

@app.get("/status", response_model=StatusResponse, tags=["MIP-003 Required"])
def get_status(job_id: str = Query(..., description="The ID of the job to check.")):
    job = agent.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with id '{job_id}' not found.")
    return StatusResponse(**job, job_id=job_id)

@app.post("/provide_input", status_code=501, tags=["MIP-003 Optional"])
def provide_input():
    return {"error": "Not Implemented. This agent does not require additional input."}