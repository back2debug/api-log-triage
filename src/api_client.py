import time
from openai import OpenAI
from agents import Agent, Runner

def call_model(client, model, prompt, timeout=30.0, retries=2):
    last_exc = None
    for attempt in range(retries + 1):
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
            )
            return {
                "ok": True,
                "text": resp.choices[0].message.content,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                "attempt": attempt + 1,
            }
        except Exception as exc:
            last_exc = exc
            time.sleep(min(2 ** attempt, 8))
    return {
        "ok": False,
        "error": f"{type(last_exc).__name__}: {last_exc}",
        "elapsed_ms": None,
    }

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