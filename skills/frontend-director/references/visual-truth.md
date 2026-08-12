# Signature Visual Truth

Use this reference whenever a task creates or changes visible UI. Its purpose is to stop a polished-looking placeholder from being accepted as the product's defining visual.

## 1. Name the signature visuals before implementation

A signature visual is any image, rendered object, map, chart, hero scene, product view, artifact, or detail state that carries the page's identity or factual claim. Record each one in the acceptance contract and UI plan. A page normally has one to five; do not classify decorative dividers or minor icons as signature visuals.

For every signature visual record:

- its user-facing claim and whether that claim is factual;
- one truth mode: `sourced`, `procedural-validated`, `generated-illustration`, or `intentional-abstraction`;
- asset or algorithm provenance, license, implementation files, and target desktop/mobile/detail views;
- a task that owns acquisition or generation, implementation, comparison, and repair.

## 2. Truth-mode rules

- `sourced`: use a traceable asset from an authoritative or appropriate source and record its URL/path and license.
- `procedural-validated`: render from a documented model or dataset; cite the model/data and verify scale, domain, units, bounds, and camera coverage.
- `generated-illustration`: AI-generated or artist-created imagery is allowed only when the UI presents it as illustration, not documentary fact.
- `intentional-abstraction`: a deliberately non-realistic representation is allowed only when it is honest, visually coherent, and does not imply factual detail it does not contain.

A factual scientific, medical, geographic, financial, historical, museum, or product-identification visual MUST use `sourced` or `procedural-validated`. A generated image or decorative approximation cannot be labelled or implied to be factual.

## 3. Automatic rejection patterns

Reject the UI and return to the earliest responsible task when a signature visual uses any of these shortcuts:

- a generic CSS gradient circle, flat textureless sphere, emoji, stock placeholder, wireframe, or arbitrary contour line in place of the claimed object;
- one gradient, silhouette, texture, or decorative recipe reused for distinct entities that should be visually distinguishable;
- fake maps, invented data, decorative charts, impossible scale/camera bounds, or labels that claim more truth than the rendering contains;
- a tiny thumbnail that looks acceptable only because defects are hidden, while the modal/detail view has no additional craft;
- a broken or missing asset silently replaced by unrelated decoration;
- “looks premium,” a detector score, Lighthouse, or successful build used as evidence of visual fidelity.

If trustworthy assets or tooling are unavailable, choose and label an honest abstraction or change the visual direction. Never fake realism to preserve the original concept.

## 4. Implementation loop for each signature visual

1. Save a reference/provenance note before coding.
2. Capture or define a failure-first comparison that exposes the placeholder, false claim, repeated identity, incorrect scale, or missing detail.
3. Implement the smallest truthful complete visual, including loading, missing-asset, and narrow-screen behavior.
4. Render the actual page at desktop and mobile sizes and open the largest available detail state.
5. Compare the result with its source/model. Repair until every binary check below passes.
6. Record all evidence in `.agent/evidence/visual-evidence.json` and validate it with:

   ```text
   workflowctl validate-visual-evidence --manifest .agent/evidence/visual-evidence.json
   ```

## 5. Blind review protocol

When the host can delegate or request a human review, give the reviewer only the brief, source/reference material, and actual screenshots—not the implementation report or author's self-assessment. Ask the reviewer to judge each signature visual with these binary checks:

- recognizable without its text label;
- visually distinct from other entities;
- not a placeholder or generic decoration;
- truthful to the claim made by the interface;
- materially matches its cited reference/model;
- remains crafted in the full-size detail view.

Any `false` result fails `visual-fidelity`. Fix the implementation and repeat the review. If independent review is unavailable, use `degraded-self-review`, disclose that limitation in the manifest and final report, and perform a separate adversarial pass after clearing prior implementation commentary from the immediate context.

## 6. Required evidence manifest

Use `schemas/visual-evidence.schema.json`. The manifest must list at least one signature visual when UI work occurred, reference existing implementation files, store every desktop/mobile/detail screenshot as `{ "path": "...", "sha256": "..." }`, contain provenance for every factual visual, have an empty `issues` array, and use `verdict: "pass"`. Screenshots must be real PNG, JPEG, or WebP files; the controller verifies their hashes so an image cannot be replaced after review. The controller also applies the factual truth-mode rule.

Minimal shape:

```json
{
  "schemaVersion": 1,
  "surface": "product home and detail",
  "reviewer": { "mode": "independent-agent", "id": "reviewer-1", "blind": true },
  "signatureVisuals": [
    {
      "id": "hero-object",
      "role": "hero",
      "claim": "The documented object shown in the hero",
      "factual": true,
      "truthMode": "sourced",
      "sources": [
        { "uri": "https://authoritative.example/object", "license": "CC BY 4.0", "note": "identity and appearance reference" }
      ],
      "implementationFiles": ["src/components/Hero.tsx"],
      "screenshots": {
        "desktop": { "path": "reports/hero-desktop.png", "sha256": "<64 lowercase hex characters>" },
        "mobile": { "path": "reports/hero-mobile.png", "sha256": "<64 lowercase hex characters>" },
        "detail": { "path": "reports/hero-detail.png", "sha256": "<64 lowercase hex characters>" }
      },
      "checks": {
        "recognizableWithoutLabel": true,
        "entityDistinct": true,
        "notPlaceholder": true,
        "truthfulToClaim": true,
        "referenceMatch": true,
        "fullSizeCraft": true
      },
      "notes": "Compared against the cited reference at all required sizes."
    }
  ],
  "verdict": "pass",
  "issues": []
}
```

The integration gate records the manifest itself as the `visual-fidelity` evidence. A passed UI phase cannot mark this check manual or not applicable.
