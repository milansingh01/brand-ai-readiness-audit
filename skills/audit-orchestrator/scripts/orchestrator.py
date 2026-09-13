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

    Skill directories contain hyphens, so they cannot be imported
    directly as normal Python package names.
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
    Convert an Observation object or dictionary into a normal
    dictionary and normalize observations to the tri-state model:

        pass
        issue
        unverified

    Older implementations may still return `found`.
    That value is converted for compatibility.
    """

    if hasattr(observation, "to_dict"):
        observation = observation.to_dict()

    if not isinstance(observation, dict):
        raise TypeError(
            f"Unsupported observation type: {type(observation)}"
        )

    result = dict(observation)

    # --------------------------------------------------------
    # Normalize old `found` representation
    # --------------------------------------------------------

    if "status" not in result:
        if "found" in result:
            result["status"] = (
                "issue" if result["found"] else "pass"
            )
        else:
            result["status"] = "unverified"

    # `status` is authoritative.
    result["status"] = str(
        result["status"]
    ).lower()

    if result["status"] not in {
        "pass",
        "issue",
        "unverified"
    }:
        result["status"] = "unverified"

    # Preserve `found` for compatibility with older scripts.
    if "found" not in result:
        result["found"] = (
            result["status"] == "issue"
        )

    return result


def unverified_observation(check, error, url):
    """
    Create an observation for a check that could not be
    reliably evaluated.

    An execution failure is NOT treated as evidence of a
    website problem.
    """

    return {
        "check": check,
        "status": "unverified",
        "found": False,
        "evidence": (
            "The check could not be reliably evaluated."
        ),
        "details": {
            "url": url
        },
        "error": str(error)
    }


# ============================================================
# RUN CRAWL / RENDER AUDIT
# ============================================================

def run_crawl_audit(html, response):
    """
    Run the crawl-render audit using the crawl implementation.
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
    Run the freshness/corroboration evidence collection.

    Cross-source corroboration and contextual interpretation
    remain agent-level reasoning tasks.
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
    Run the engagement evidence collection.
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
    Execute all applicable audit skills independently.

    Important:

    - Skills collect evidence.
    - Skills do not assign final severity.
    - Skills do not assign final priority.
    - Skills do not invent suggested actions.
    - Failed checks become `unverified`.
    - One failed skill must not stop other applicable skills.
    """

    results = {
        "crawl-render-audit": [],
        "structured-data-audit": [],
        "freshness-corroboration": [],
        "engagement-audit": []
    }

    # --------------------------------------------------------
    # Fetch website once
    # --------------------------------------------------------

    try:
        response = fetch_page(url)
        html = response.text
    except Exception as error:
        # No reliable page content is available.
        #
        # This is an access limitation, not automatically a
        # finding about the website.
        access_error = unverified_observation(
            "website_access",
            error,
            url
        )

        results["crawl-render-audit"] = [
            access_error
        ]

        for skill_name, check_name in [
            (
                "structured-data-audit",
                "structured_execution"
            ),
            (
                "freshness-corroboration",
                "freshness_execution"
            ),
            (
                "engagement-audit",
                "engagement_execution"
            )
        ]:
            results[skill_name] = [
                unverified_observation(
                    check_name,
                    "Page content was unavailable, so this skill could not be reliably evaluated.",
                    url
                )
            ]

        return results

    # --------------------------------------------------------
    # Crawl / Render
    # --------------------------------------------------------

    try:
        results["crawl-render-audit"] = run_crawl_audit(
            html,
            response
        )
    except Exception as error:
        results["crawl-render-audit"] = [
            unverified_observation(
                "crawl_execution",
                error,
                url
            )
        ]

    # --------------------------------------------------------
    # Structured Data
    # --------------------------------------------------------

    try:
        results["structured-data-audit"] = (
            run_structured_data_audit(html)
        )
    except Exception as error:
        results["structured-data-audit"] = [
            unverified_observation(
                "structured_execution",
                error,
                url
            )
        ]

    # --------------------------------------------------------
    # Freshness
    # --------------------------------------------------------

    try:
        results["freshness-corroboration"] = (
            run_freshness_audit(html)
        )
    except Exception as error:
        results["freshness-corroboration"] = [
            unverified_observation(
                "freshness_execution",
                error,
                url
            )
        ]

    # --------------------------------------------------------
    # Engagement
    # --------------------------------------------------------

    try:
        results["engagement-audit"] = (
            run_engagement_audit(html)
        )
    except Exception as error:
        results["engagement-audit"] = [
            unverified_observation(
                "engagement_execution",
                error,
                url
            )
        ]

    return results


# ============================================================
# OBSERVATION SUMMARY
# ============================================================

def flatten_observations(observations):
    """
    Flatten skill observations while preserving their source.

    This is useful for inspection and for the agent-level
    interpretation stage.
    """

    flattened = []

    for skill_name, skill_observations in observations.items():
        for observation in skill_observations:
            flattened.append(
                {
                    "skill": skill_name,
                    **observation
                }
            )

    return flattened


# ============================================================
# REPORT BUILDER
# ============================================================

def build_report(url, findings=None):
    """
    Build the final report structure required by the marketplace.

    The deterministic scripts do not decide findings, severity,
    priority, or suggested actions. Those are interpretation
    decisions made by the agent/orchestrator.

    Therefore this function accepts interpreted findings rather
    than creating findings directly from raw observations.
    """

    findings = findings or []

    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for finding in findings:
        severity = str(
            finding.get("severity", "")
        ).lower()

        if severity in counts:
            counts[severity] += 1

    return {
        "site": url,
        "audited_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "summary": {
            "total_findings": len(findings),
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"]
        },
        "findings": findings
    }


# ============================================================
# MARKETPLACE ENTRYPOINT / TEST HARNESS
# ============================================================

def run_audit(url):
    """
    Run the deterministic evidence-collection pipeline.

    The returned object contains:
        - observations for agent interpretation
        - a schema-compatible empty report

    In the actual Agent Skills workflow, the agent uses the
    observations to interpret issues, deduplicate them, assign
    severity/priority, and produce the final report.
    """

    observations = collect_observations(url)

    report = build_report(
        url,
        findings=[]
    )

    return {
        "report": report,
        "observations": flatten_observations(
            observations
        )
    }


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python orchestrator.py https://example.com"
        )
        sys.exit(1)

    url = sys.argv[1]

    result = run_audit(url)

    print(
        json.dumps(
            result,
            indent=2
        )
    )