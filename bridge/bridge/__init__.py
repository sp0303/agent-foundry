"""agent-foundry bridge server.

A small always-on server that owns the task loop as a state machine, spawns
vendor workers headlessly, listens to GitHub webhooks, and calls LLM agents only
at judgement points. See docs/bridge-design.md and docs/decisions/0001-*.
"""

__version__ = "0.0.1"
