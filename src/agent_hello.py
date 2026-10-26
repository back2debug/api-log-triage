import sys

from agents import Agent, Runner

agent = Agent(
    name="SupportHelper",
    instructions="You are a concise API support engineer. Answer in 3 bullets.",
    model="gpt-4o-mini",
)
question = sys.argv[1] if len(sys.argv) > 1 else "What does HTTP 429 mean?"
result = Runner.run_sync(agent, question)
print(result.final_output)