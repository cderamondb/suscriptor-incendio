"""Script temporal para probar modelos disponibles."""
import sys
sys.path.insert(0, "/app")
import anthropic

modelos = [
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-sonnet-4-6-20261015",
    "claude-haiku-3-5-20241022",
]

c = anthropic.Anthropic()
for m in modelos:
    try:
        r = c.messages.create(model=m, max_tokens=5, messages=[{"role": "user", "content": "hi"}])
        print(f"OK: {m} -> {r.content[0].text}")
    except Exception as e:
        print(f"FAIL: {m} -> {type(e).__name__}: {e}")
