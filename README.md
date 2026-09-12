# Brand AI-Readiness Audit Marketplace

An Agent Skill Marketplace for auditing website AI discoverability and on-site engagement.

## What This Does

Given any website URL, the marketplace:
1. **Discovers** problems that hurt AI discoverability (getting found and cited)
2. **Identifies** issues that hurt on-site engagement (keeping visitors)
3. **Reports** findings with evidence, severity, and prioritized fixes
4. **Recommends** proactive improvements beyond just fixing defects

## How It Works

The marketplace uses a **5-stage AI crawl pipeline** framework:

- **Stage 1: DISCOVERY** → Can AI find the URL?
- **Stage 2: FETCHING** → Can AI retrieve the page?
- **Stage 3: PARSING** → Can AI read the HTML?
- **Stage 4: EXTRACTION** → Can AI extract facts?
- **Stage 5: RETRIEVAL** → Can AI find it when needed?

**Failure at ANY stage = invisible to AI.**

## Skills in This Marketplace

### 1. audit-orchestrator (ENTRYPOINT)
Orchestrates all audit skills and produces the final audit report.

### 2. crawl-render-audit
Audits crawlability, rendering, and accessibility for AI crawlers.

### 3. structured-data-audit
Audits structured data, meta tags, and machine-readable content.

### 4. freshness-corroboration
Audits content freshness, entity disambiguation, and web corroboration.

### 5. engagement-audit
Audits on-site engagement signals and content accessibility.

## Design Principles

1. **Recommend-only:** No skill modifies live websites. All actions are read-only.
2. **Safe:** Respects robots.txt, no destructive actions, no authenticated access.
3. **Fast:** Completes audit in <5 minutes on standard machine.
4. **Generic:** Works on any website, seen or unseen. Derived from first principles.
5. **Mechanism-sound:** Every finding explains WHY it matters and HOW to fix it.

## Severity Levels

- **CRITICAL:** Makes site completely invisible (NOINDEX, robots.txt blocks)
- **HIGH:** Major visibility reduction (empty HTML, no noscript)
- **MEDIUM:** Reduced discovery (no sitemap, no structured data)
- **LOW:** Optimization opportunity (no meta description)

## License

MIT
