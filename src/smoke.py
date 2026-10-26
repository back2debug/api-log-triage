import json
import os
import sys
import time

import openai
from openai import OpenAI

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()


def ms_since(t0):
    return round((time.perf_counter() - t0) * 1000, 1)


def ask(prompt, model=MODEL):
    t0 = time.perf_counter()
    try:
        resp = client.responses.create(model=model, input=prompt)
    except openai.APIError as exc:
        return {"ok": False, "model": model, "error": f"{type(exc).__name__}: {exc}",
                "elapsed_ms": ms_since(t0)}
    return {"ok": True, "model": model, "text": resp.output_text, "elapsed_ms": ms_since(t0)}


def ask_stream(prompt, model=MODEL):
    t0 = time.perf_counter()
    ttft_ms = None
    chunks = []
    try:
        stream = client.responses.create(model=model, input=prompt, stream=True)
        for event in stream:
            if event.type == "response.output_text.delta":
                if ttft_ms is None:
                    ttft_ms = ms_since(t0)
                chunks.append(event.delta)
                print(event.delta, end="", flush=True)
    except openai.APIError as exc:
        print()
        return {"ok": False, "model": model, "error": f"{type(exc).__name__}: {exc}",
                "ttft_ms": ttft_ms, "elapsed_ms": ms_since(t0)}
    print()
    return {"ok": True, "model": model, "ttft_ms": ttft_ms, "elapsed_ms": ms_since(t0),
            "chars": len("".join(chunks))}


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Say hello in five words."

    print("--- Standard call ---")
    print(json.dumps(ask(prompt), indent=2))

    print("\n--- Stream call ---")
    print(json.dumps(ask_stream(prompt), indent=2))