import sys
import json
from pathlib import Path

args = sys.argv[1:]
sandbox_dir = Path(__file__).parent.parent
stages_path = sandbox_dir / "test-project" / ".harness" / "STAGES.md"

result = {
    "summary": "Pruebas simuladas exitosas.",
    "status": "ok",
    "args": args
}

if stages_path.exists():
    current_content = stages_path.read_text(encoding="utf-8")
    if "Sub-paso activo:" not in current_content:
        lines = current_content.split("\n")
        lines.insert(1, "Sub-paso activo: 1.0")
        stages_path.write_text("\n".join(lines), encoding="utf-8")
        result["summary"] = "STAGES.md actualizado con Sub-paso activo: 1.0"

print(json.dumps(result))
sys.exit(0)
