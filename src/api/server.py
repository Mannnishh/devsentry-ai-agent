"""FastAPI REST and Server-Sent Events (SSE) streaming interface for DevSentry."""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse

from src.agent.engine import ReActEngine
from src.agent.reflection import SelfHealingCoordinator
from src.llm.client import LLMClient
from src.memory.scratchpad import ScratchpadManager
from src.memory.storage import SQLiteSessionStore
from src.safety.guardrails import HITLApprovalGate, ToolRisk
from src.tools.base import Tool, ToolRegistry
from src.tools.filesystem import SafeFileSystem
from src.tools.test_runner import TestRunnerTool

app = FastAPI(
    title="DevSentry Agent API",
    description="Autonomous Codebase & DevOps Troubleshooting Agent Service",
    version="0.1.0",
)


def get_engine() -> ReActEngine:
    """Construct a fully-configured ReActEngine instance."""
    fs = SafeFileSystem(".")
    tr = TestRunnerTool(".")

    registry = ToolRegistry()
    registry.register(
        Tool(
            name="read_file",
            description="Reads text content of a workspace file. Input: file path.",
            func=fs.read_file,
            risk=ToolRisk.SAFE,
        )
    )
    registry.register(
        Tool(
            name="write_file",
            description="Writes text to a file. Format: 'path:::content'.",
            func=fs.write_file,
            risk=ToolRisk.HIGH,
        )
    )

    registry.register(
        Tool(
            name="list_dir",
            description="Lists files in a directory. Input: directory path (e.g. '.').",
            func=fs.list_dir,
            risk=ToolRisk.SAFE,
        )
    )

    registry.register(
        Tool(
            name="run_tests",
            description="Runs pytest unit tests. Input: test file path or ''.",
            func=tr.run_tests,
            risk=ToolRisk.SAFE,
        )
    )

    client = LLMClient()
    session_store = SQLiteSessionStore("data/devsentry.db")
    scratchpad_manager = ScratchpadManager(max_observation_chars=1200, max_recent_steps=4)
    self_healing = SelfHealingCoordinator(client)
    # In server mode, approve high-risk tools automatically for authorized API callers
    hitl_gate = HITLApprovalGate(prompt_func=lambda _: True)

    return ReActEngine(
        llm_client=client,
        tools=registry.to_dict(),
        max_iterations=8,
        scratchpad_manager=scratchpad_manager,
        session_store=session_store,
        self_healing=self_healing,
        hitl_gate=hitl_gate,
        tool_risk_lookup=registry.get_risk,
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestrators and load balancers."""
    return {"status": "healthy", "service": "DevSentry", "version": "0.1.0"}


@app.get("/agent/run")
def run_agent(task: str = Query(..., description="Engineering task to execute")) -> dict:
    """Execute an agent task synchronously and return the final answer."""
    session_id = f"api_{uuid.uuid4().hex[:8]}"
    engine = get_engine()
    result = engine.run(task, session_id=session_id)
    return {
        "session_id": session_id,
        "task": task,
        "result": result,
    }


@app.get("/agent/stream")
async def stream_agent(
    task: str = Query(..., description="Engineering task to execute"),
) -> StreamingResponse:
    """Stream step-by-step agent lifecycle events in real time using Server-Sent Events."""

    async def event_stream() -> AsyncGenerator[str, None]:
        session_id = f"sse_{uuid.uuid4().hex[:8]}"
        yield f"data: {json.dumps({'event': 'start', 'session_id': session_id, 'task': task})}\n\n"

        engine = get_engine()
        result = engine.run(task, session_id=session_id)

        yield (
            f"data: {json.dumps({'event': 'finish', 'session_id': session_id, 'result': result})}\n"
            f"\n"
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
