import os
import time

import openai
from openai import OpenAI
from agents import Agent, Runner

from pydantic import BaseModel

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def make_client(timeout=30.0, max_retries=2):
    return OpenAI(timeout=timeout, max_retries=max_retries)


def call_model(client, prompt, model=DEFAULT_MODEL, instructions=None):
    kwargs = {"model": model, "input": prompt}
    if instructions:
        kwargs["instructions"] = instructions
    t0 = time.perf_counter()
    try:
        resp = client.responses.create(**kwargs)
    except openai.APIError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1)}
    return {"ok": True, "text": resp.output_text,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1)}

class TriageSummary(BaseModel):
    symptoms: str
    likely_cause: str
    recommended_next_action: str


TRIAGE_INSTRUCTIONS = (
    "You are an OpenAI enterprise support engineer. Given aggregated request-log "
    "metrics as JSON, write a concise customer-facing triage: observed symptoms, "
    "likely cause, and one recommended next action. Use only numbers present in "
    "the input. If the data is insufficient, say so."
)


def run_triage_agent(metrics_json, model=DEFAULT_MODEL):
    agent = Agent(
        name="IncidentTriage",
        instructions=TRIAGE_INSTRUCTIONS,
        model=model,
        output_type=TriageSummary,
    )
    t0 = time.perf_counter()
    try:
        result = Runner.run_sync(agent, metrics_json, max_turns=3)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1)}
    return {"ok": True, "summary": result.final_output.model_dump(),
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1)}