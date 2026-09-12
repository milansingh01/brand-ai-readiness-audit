import sys
import json
import importlib.util
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# SHARED
# ============================================================

from shared.http_client import fetch_page


# ============================================================
# LOAD SKILL MODULES
# ============================================================

SKILLS_ROOT = PROJECT_ROOT / "skills"


def load_module(module_name, file_path):
    """
    Load a Python module directly from its file path.

    This is necessary because our skill directories contain
    hyphens, for example:

        crawl-render-audit

    which cannot be used directly as a Python import name.
    """

    spec = importlib.util.spec_from_file_location(
        module_name,
        file_path
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Could not load skill module: {file_path}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


crawl_checks = load_module(
    "crawl_checks",
    SKILLS_ROOT
    / "crawl-render-audit"
    / "scripts"
    / "crawl_checks.py"
)


structured_checks = load_module(
    "structured_checks",
    SKILLS_ROOT
    / "structured-data-audit"
    / "scripts"
    / "structured_checks.py"
)


freshness_checks = load_module(
    "freshness_checks",
    SKILLS_ROOT
    / "freshness-corroboration"
    / "scripts"
    / "freshness_checks.py"
)


engagement_checks = load_module(
    "engagement_checks",
    SKILLS_ROOT
    / "engagement-audit"
    / "scripts"
    / "engagement_checks.py"
)


# ============================================================
# OBSERVATION CONVERSION
# ============================================================

def observation_to_dict(observation):
    """
    Convert an Observation object into a normal dictionary.
    """

    if hasattr(observation, "to_dict"):
        return observation.to_dict()

    if isinstance(observation, dict):
        return observation

    raise TypeError(
        f"Unsupported observation type: {type(observation)}"
    )


# ============================================================
# RUN CRAWL / RENDER AUDIT
# ============================================================

def run_crawl_audit(html, response):
    """
    Run the crawl-render audit using the existing
    crawl_checks.py implementation.
    """

    observations = crawl_checks.run_checks(
        html,
        response
    )

    return [
        observation_to_dict(observation)
        for observation in observations
    ]


# ============================================================
# RUN STRUCTURED DATA AUDIT
# ============================================================

def run_structured_data_audit(html):
    """
    Run the structured-data audit.
    """

    observations = structured_checks.run_checks(
        html
    )

    return [
        observation_to_dict(observation)
        for observation in observations
    ]


# ============================================================
# RUN FRESHNESS AUDIT
# ============================================================

def run_freshness_audit(html):
    """
    Run the freshness/corroboration audit.
    """

    observations = freshness_checks.run_checks(
        html
    )

    return [
        observation_to_dict(observation)
        for observation in observations
    ]


# ============================================================
# RUN ENGAGEMENT AUDIT
# ============================================================

def run_engagement_audit(html):
    """
    Run the engagement audit.
    """

    observations = engagement_checks.run_checks(
        html
    )

    return [
        observation_to_dict(observation)
        for observation in observations
    ]


# ============================================================
# COLLECT ALL OBSERVATIONS
# ============================================================

def collect_observations(url):
    """
    Execute all audit skills and collect their observations.

    Important:
    The skills detect objective facts.

    They do NOT decide:
        - severity
        - priority
        - final suggested action

    Those decisions belong to the agent/orchestration layer.
    """

    # --------------------------------------------------------
    # Fetch website once
    # --------------------------------------------------------

    response = fetch_page(url)

    html = response.text


    # --------------------------------------------------------
    # Results container
    # --------------------------------------------------------

    results = {
        "crawl-render-audit": [],
        "structured-data-audit": [],
        "freshness-corroboration": [],
        "engagement-audit": []
    }


    # --------------------------------------------------------
    # Crawl / Render
    # --------------------------------------------------------

    try:

        results["crawl-render-audit"] = run_crawl_audit(
            html,
            response
        )

    except Exception as e:

        results["crawl-render-audit"] = [
            {
                "check": "crawl_execution",
                "found": True,
                "evidence": str(e),
                "details": {
                    "url": url
                }
            }
        ]


    # --------------------------------------------------------
    # Structured Data
    # --------------------------------------------------------

    try:

        results["structured-data-audit"] = (
            run_structured_data_audit(html)
        )

    except Exception as e:

        results["structured-data-audit"] = [
            {
                "check": "structured_execution",
                "found": True,
                "evidence": str(e),
                "details": {
                    "url": url
                }
            }
        ]


    # --------------------------------------------------------
    # Freshness
    # --------------------------------------------------------

    try:

        results["freshness-corroboration"] = (
            run_freshness_audit(html)
        )

    except Exception as e:

        results["freshness-corroboration"] = [
            {
                "check": "freshness_execution",
                "found": True,
                "evidence": str(e),
                "details": {
                    "url": url
                }
            }
        ]


    # --------------------------------------------------------
    # Engagement
    # --------------------------------------------------------

    try:

        results["engagement-audit"] = (
            run_engagement_audit(html)
        )

    except Exception as e:

        results["engagement-audit"] = [
            {
                "check": "engagement_execution",
                "found": True,
                "evidence": str(e),
                "details": {
                    "url": url
                }
            }
        ]


    return results


# ============================================================
# TEMPORARY REPORT BUILDER
# ============================================================

def build_report(url, observations):
    """
    Build the marketplace report.

    At this stage observations are exposed so we can verify
    that all four skills actually executed.

    Severity/action interpretation will be added by the agent
    in the next stage.
    """

    all_observations = []


    for skill_name, skill_observations in observations.items():

        for observation in skill_observations:

            # Only expose observations where the detector
            # actually found something.
            if not observation.get("found", False):
                continue

            all_observations.append(
                {
                    "skill": skill_name,
                    **observation
                }
            )


    return {
        "site": url,

        "audited_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "summary": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },

        "findings": [],

        # Temporary developer field.
        # This lets us verify the complete pipeline.
        "observations": all_observations
    }


# ============================================================
# MARKETPLACE ENTRYPOINT
# ============================================================

def run_audit(url):
    """
    Main entrypoint called by main.py.
    """

    observations = collect_observations(url)

    report = build_report(
        url,
        observations
    )

    return report


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "python orchestrator.py https://example.com"
        )

        sys.exit(1)


    url = sys.argv[1]

    report = run_audit(url)

    print(
        json.dumps(
            report,
            indent=2
        )
    )