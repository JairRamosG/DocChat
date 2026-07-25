"""Generate Mermaid diagram from the agent workflow graph."""

from agents.workflow import AgentWorkflow
from pathlib import Path


def main():
    workflow = AgentWorkflow()
    graph = workflow.compiled_workflow.get_graph()

    # Generate Mermaid text
    mermaid_text = graph.draw_mermaid()

    # Save to file
    output_dir = Path("diagrama")
    output_dir.mkdir(exist_ok=True)

    mermaid_path = output_dir / "workflow.mmd"
    mermaid_path.write_text(mermaid_text)
    print(f"Mermaid saved to: {mermaid_path}")

    # Also save as PNG if graphviz is installed
    try:
        png_path = output_dir / "workflow.png"
        graph.draw_mermaid_png(str(png_path))
        print(f"PNG saved to: {png_path}")
    except Exception as e:
        print(f"PNG generation skipped (install graphviz for PNG): {e}")

    print("\nMermaid content:")
    print(mermaid_text)


if __name__ == "__main__":
    main()
