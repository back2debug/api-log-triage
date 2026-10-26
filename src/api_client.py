import os
import time

import openai
from openai import OpenAI
from agents import Agent, Runner

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

def run_triage_agent(metrics_json: str, instructions: str, model: str = "gpt-4o-mini") -> dict:
    """Run the IncidentTriage agent and return a uniform dict."""
    client = OpenAI()
    agent = Agent(
        name="IncidentTriage",
        instructions=instructions,
        model=model,
    )
    try:
        result = Runner.run_sync(agent, input=metrics_json)
        return {
            "ok": True,
            "text": result.final_output,
            "elapsed_ms": None,  # Agents SDK doesn't expose elapsed time here
            "attempt": 1,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": None,
            "attempt": 0,
        }