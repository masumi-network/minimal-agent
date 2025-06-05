# echo_agent_service.py

import threading
import time
import uuid
import hashlib
import json
from typing import Dict, Any

# --- 1. Agent Configuration and State ---

AGENT_IDENTIFIER = "echo-agent-v1"
SELLER_VKEY = "addr1qxlkjl23k4jlksdjfl234jlksdf"
INPUT_SCHEMA = {
  "input_data": [
    {
      "id": "text_input",
      "type": "string",
      "name": "Text to Echo",
      "data": {"description": "The text that will be repeated three times."},
      "validations": [{"validation": "required", "value": "true"}]
    }
  ]
}

# --- 2. The Agent Service Class ---

class EchoAgentService:
    """
    Manages the state and core logic for the Echo agent.
    This version has no external API calls.
    """
    def __init__(self):
        """Initializes the service with an in-memory job store."""
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def _process_job(self, job_id: str):
        """
        The private worker method that runs in the background.
        It repeats the input text three times.
        """
        print(f"Background task started for job_id: {job_id}")

        with self.lock:
            job = self.jobs[job_id]
            job["status"] = "running"
            # We get the input based on the new ID in our INPUT_SCHEMA
            text_to_repeat = job["input_data"]["text_input"]

        try:
            # Simulate a bit of work
            time.sleep(2)

            # The new core logic: repeat the text
            result_text = f"{text_to_repeat} {text_to_repeat} {text_to_repeat}"

            # Update the job with the result
            with self.lock:
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["result"] = result_text
            print(f"Job {job_id} completed successfully.")

        except Exception as e:
            error_message = f"Job {job_id} failed unexpectedly: {e}"
            with self.lock:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["message"] = error_message
            print(error_message)

    def start_new_job(self, identifier_from_purchaser: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new job, stores it, and returns details for the API response."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        input_string = json.dumps(input_data, sort_keys=True)
        input_hash = hashlib.md5(input_string.encode('utf-8')).hexdigest()

        with self.lock:
            self.jobs[job_id] = {
                "status": "pending",
                "input_data": input_data,
                "identifier_from_purchaser": identifier_from_purchaser,
                "result": None,
                "message": None
            }
        return {"job_id": job_id, "input_hash": input_hash}

    def get_job_status(self, job_id: str) -> Dict[str, Any] | None:
        """Retrieves a job's status."""
        with self.lock:
            return self.jobs.get(job_id)