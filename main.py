import json
import sys
import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

ORCHESTRATOR_PATH = (
    PROJECT_ROOT
    / "skills"
    / "audit-orchestrator"
    / "scripts"
    / "orchestrator.py"
)


def load_orchestrator():
    spec = importlib.util.spec_from_file_location(
        "audit_orchestrator",
        ORCHESTRATOR_PATH
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load audit orchestrator.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python main.py https://example.com")
        return

    url = sys.argv[1]

    print("=" * 60)
    print("BRAND AI READINESS AUDIT")
    print("=" * 60)
    print(f"Website: {url}")
    print("=" * 60)

    try:
        orchestrator = load_orchestrator()

        report = orchestrator.run_audit(url)

        print("\nFINAL AUDIT REPORT")
        print("=" * 60)
        print(json.dumps(report, indent=2))

    except Exception as e:
        print("\nAUDIT FAILED")
        print("=" * 60)
        print(str(e))


if __name__ == "__main__":
    main()