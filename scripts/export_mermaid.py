"""Export the compiled LangGraph topology as Mermaid text.

This script only builds the graph; it does not invoke LLM-backed nodes, so no LLM API key
is required just to render the topology. LangGraph itself must be installed.
"""

from pathlib import Path

from langgraph_agent_lab.graph import build_graph


def main() -> None:
    graph = build_graph()
    mermaid = graph.get_graph().draw_mermaid()

    output = Path("outputs/graph.mmd")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(mermaid, encoding="utf-8")
    print(f"Wrote Mermaid graph to {output}")
    print(mermaid)


if __name__ == "__main__":
    main()
