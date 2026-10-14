# ── Findings markdown ──────────────────────────────────────────────────────
from datetime import datetime
n_cases  = len(cases)
n_valid  = len(valid)
n_insuff = int(cases['manual_label'].eq('insufficient_evidence').sum())
noisy_cases = [
    'case_002 / ramazankawish / AAMI Website',
    'case_004 / sharelinsonny / Emergency Response',
    'case_005 / sharelinsonny / Finding Answers',
    'case_007 / fjone7 / AAMI Website',
    'case_008 / reneerussell99 / AAMI Website',
]
summary_md = summary.to_markdown(index=False)
label_counts_md = (
    cases['manual_label']
    .value_counts(dropna=False)
    .rename_axis('manual_label')
    .reset_index(name='n_cases')
    .to_markdown(index=False)
)

lines = [
    "# Manual Expert Review / Ground Truth Validation Findings",
    "",
    f"**Author:** CS19 Capstone Project",
    f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
    "**Scope:** CS19 capstone validation sample for Proposal 2 participant-normalized time moderation.",
    "",
    "## 1. Purpose",
    "",
    "This manual review provides a reviewer-estimated ground truth validation sample for comparing",
    "three candidate scoring outputs: the raw survey/self-reported score, Model C before Proposal 2",
    "time moderation, and Proposal 2 after-time moderation. The purpose is to supplement the",
    "validation framework, not to replace the model, redefine Proposal 1 or Proposal 2, or convert",
    "retry behaviour into an automatic scoring rule.",
    "",
    "## 2. Method",
    "",
    f"The sample contains {n_cases} participant-task cases, of which {n_valid} cases have a",
    f"manual ground-truth estimate and {n_insuff} cases are marked as insufficient evidence.",
    "",
    label_counts_md,
    "",
    "## 3. Validation Summary",
    "",
    summary_md,
    "",
    "The validation sample does NOT support a broad conclusion that Proposal 2 after-time scores",
    "are closer to manual review than the raw survey score or Model C before time.",
    "Model C before time has the lowest mean absolute error in this sample.",
    "Proposal 2 after time has a higher MAE, primarily because several long-duration tasks were",
    "successful but verbose, segmented across adjacent tasks, or driven by multi-route evaluation",
    "rather than actual failure.",
    "",
    "## 4. Key Findings",
    "",
    "Proposal 2 was clearly helpful in case_001 / ghum / AAMI Website, where the transcript showed",
    "real navigation/readability friction and the after-time score was much closer to the manual score.",
    "",
    "However, several cases show that the time signal remains noisy:",
    ", ".join(noisy_cases) + ".",
    "",
    "## 5. Limitations",
    "",
    "This manual review has a small sample size and should not be treated as definitive statistical",
    "proof. Transcript text may mix participant speech, screen-reader output, page audio, and system",
    "audio. Segment boundaries are approximate. The manual score is a reviewer estimate for validation",
    "comparison, not official ground truth.",
    "",
    "## 6. Recommendation",
    "",
    "Use this manual review as a validation sample and audit artifact rather than as a replacement",
    "scoring mechanism. Proposal 2 should remain a moderation signal, but future iterations should",
    "avoid treating high normalized time as conclusive evidence without supporting transcript,",
    "clickstream, or focus evidence.",
]
findings = "\n".join(lines)
(MAN_OUT / 'manual_review_findings.md').write_text(findings, encoding='utf-8')
print("manual_review_findings.md written.")
