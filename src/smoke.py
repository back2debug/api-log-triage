import os, sys, json, time
from openai import OpenAI

client = OpenAI()

def ask(prompt, model=None):
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "ok": True,
            "model": model,
            "text": resp.choices[0].message.content,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
    except Exception as exc:
        return {"ok": False, "model": model, "error": f"{type(exc).__name__}: {exc}"}

def ask_stream(prompt, model="gpt-4o-mini"):
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    chunks = []
    for event in stream:
        delta = event.choices[0].delta.content or ""
        chunks.append(delta)
        print(delta, end="", flush=True)
    print()
    return "".join(chunks)

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Say hello in five words."
    
    # Standard call
    print("--- Standard call ---")
    print(json.dumps(ask(prompt), indent=2))
    
    # Streaming call
    print("\n--- Stream call ---")
    ask_stream("Say hello in five words.")