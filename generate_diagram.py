"""Generate workflow diagram as PNG from Mermaid."""

import subprocess
from pathlib import Path


def main():
    mermaid_path = Path("diagrama/workflow.mmd")
    output_dir = Path("diagrama")

    if not mermaid_path.exists():
        print("Run 'python generate_diagram.py' first to create the .mmd file")
        return

    # Use mmdc (Mermaid CLI) to generate PNG
    png_path = output_dir / "workflow.png"
    try:
        subprocess.run(
            ["mmdc", "-i", str(mermaid_path), "-o", str(png_path), "-b", "white"],
            check=True,
            capture_output=True,
        )
        print(f"PNG saved to: {png_path}")
    except FileNotFoundError:
        print("mmdc not found. Install it with:")
        print("  npm install -g @mermaid-js/mermaid-cli")
    except subprocess.CalledProcessError as e:
        print(f"Error generating PNG: {e.stderr.decode()}")


if __name__ == "__main__":
    main()
