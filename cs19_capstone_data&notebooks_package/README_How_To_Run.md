# CS19 Capstone — How to Run

## Project overview

This project implements automated accessibility and usability scoring for the AAMI website
user-testing dataset, using the **Katie Model C3 / Proposal 1** scoring framework and
**Proposal 2** participant-normalized time moderation.

### Three scoring outputs

| Output | Notebook | Description |
|---|---|---|
| Smart Accessibility Score | NB 01 | Model C L2 stream — AT friction, comprehension caps, cohort weights |
| Smart Usability Score | NB 01 + NB 02 | Model C L3 stream + Proposal 2 L3.8 time moderation |
| Tester Quality Rating | NB 04 | Independent third score — feedback quality, coverage, consistency |

### Key design constraints
- **Scores can only stay the same or go down** from the participant's stated survey score.
- **Proposal 2 only changes L3 usability time moderation.** Accessibility scores are unchanged.
- **Tester Quality is independent** and must not be multiplied into final ACC/USA scores.
- **Manual Review is a validation sample, not official ground truth.**
- **Do not overclaim that Proposal 2 is always better.** In the 18-case sample, Model C
  before-time has the lowest MAE (13.28). Proposal 2 was helpful for case_001 but noisy in others.

---

## Directory layout

```
cs19_capstone/
├── 01_run_model_c_proposal1.ipynb          # Proposal 1 / Model C scoring
├── 02_proposal2_time_integration.ipynb     # Proposal 2 L3.8 time moderation
├── 03_manual_review_validation.ipynb       # Manual review validation framework
├── 04_tester_quality_rating.ipynb          # Tester Quality independent rating
├── 05_presentation_assets.ipynb            # Optional: summary charts and PNGs
├── README_How_To_Run.md                    # This file
│
├── A_Test_Raw_Survey_Scores_AAMIInsuranceWebsite-Website.xls   # Raw survey (CSV format)
├── AAMIwebsite-IndividualInsights-2026-03-10(1).xlsx           # LLM friction insights
├── proposal2_time_signal_result.csv                            # Proposal 2 time signal
├── task_segmentation_combined.csv                              # Task time segmentation
├── aami-website-tasks(1).csv                                   # Task metadata
│
├── proposal2_segments/                     # Per-participant transcript segment CSVs (21 files)
│
├── outputs/                                # All generated outputs (created on run)
│   ├── proposal1_rows.csv
│   ├── proposal1_df_insights.csv
│   ├── model_c3_proposal1_results.xlsx
│   ├── proposal1_task_summary.csv
│   ├── proposal1_cohort_summary.csv
│   ├── proposal1_project_summary.txt
│   ├── l3_score_before_time.csv
│   ├── proposal2_integrated_l3_time_score.csv
│   ├── proposal2_time_audit_log.csv
│   ├── proposal2_integration_summary.csv
│   ├── proposal2_time_signal_result_recomputed_for_integration.csv
│   ├── proposal2_unmatched_participants.csv
│   ├── proposal2_unmatched_tasks.csv
│   ├── proposal2_human_readable_summary.txt
│   ├── manual_review_outputs/
│   │   ├── manual_review_cases_draft.csv
│   │   ├── manual_review_cases.csv
│   │   ├── manual_review_scoring_rubric.csv
│   │   ├── manual_review_validation_summary.csv
│   │   ├── manual_review_error_details.csv
│   │   ├── manual_review_findings.md
│   │   ├── manual_review_case_examples.md
│   │   └── manual_review_quality_check.md
│   ├── tester_quality_outputs/
│   │   ├── tester_quality_scores.csv
│   │   ├── tester_quality_features.csv
│   │   ├── tester_quality_summary.csv
│   │   ├── unmatched_tester_quality_participants.csv
│   │   ├── tester_quality_methodology.md
│   │   ├── tester_quality_case_examples.md
│   │   └── tester_quality_quality_check.md
│   └── presentation_assets/
│       ├── summary_validation_table.png
│       ├── audit_log_screenshot.png
│       ├── integrated_output_screenshot.png
│       ├── model_c_integration_pipeline.png
│       ├── implementation_pipeline_diagram.png
│       ├── previous_vs_current_progress.png
│       ├── tester_quality_band_chart.png
│       └── acc_usa_score_comparison.png
│
└── scripts/                                # Reference scripts (do not run directly)
    ├── run_manual_review_validation.py
    └── run_tester_quality_rating.py
```

---

## How to run

### Prerequisites

```bash
pip install pandas numpy openpyxl sentence-transformers nbconvert jupyter ipykernel
python -m ipykernel install --user --name python3 --display-name "Python 3"
```

### Run all notebooks in order

```bash
cd cs19_capstone

# Notebook 01 — Model C / Proposal 1 (takes ~5 min due to sentence-transformers)
jupyter nbconvert --to notebook --execute --inplace 01_run_model_c_proposal1.ipynb

# Notebook 02 — Proposal 2 time moderation
jupyter nbconvert --to notebook --execute --inplace 02_proposal2_time_integration.ipynb

# Notebook 03 — Manual review validation
jupyter nbconvert --to notebook --execute --inplace 03_manual_review_validation.ipynb

# Notebook 04 — Tester Quality rating
jupyter nbconvert --to notebook --execute --inplace 04_tester_quality_rating.ipynb

# Notebook 05 — Presentation assets (optional)
jupyter nbconvert --to notebook --execute --inplace 05_presentation_assets.ipynb
```

Or open each notebook in JupyterLab / Jupyter Notebook and use **Run All Cells**.

### Path configuration

All notebooks use relative paths only:

```python
BASE_DIR   = Path(".").resolve()
INPUT_DIR  = BASE_DIR
OUTPUT_DIR = BASE_DIR / "outputs"
SEGMENT_DIR = BASE_DIR / "proposal2_segments"
SCRIPT_DIR  = BASE_DIR / "scripts"
```

**Do not hard-code `/home/ubuntu` or `G:/5703_data`.**
Run notebooks from the `cs19_capstone/` directory.

---

## Notebook dependency chain

```
NB 01 (Model C / Proposal 1)
  └── produces: proposal1_rows.csv, proposal1_df_insights.csv
        └── NB 02 (Proposal 2 time moderation)
              └── produces: proposal2_integrated_l3_time_score.csv, proposal2_time_audit_log.csv
                    └── NB 03 (Manual review validation)
                          └── produces: manual_review_cases.csv, manual_review_validation_summary.csv
                                └── NB 04 (Tester Quality)
                                      └── produces: tester_quality_scores.csv, etc.
                                            └── NB 05 (Presentation assets)
```

---

## Verified execution results (2026-05-17)

| Notebook | Key outputs | Status |
|---|---|---|
| NB 01 | 136 rows × 18 cols; project ACC 50.72, USA 60.10 | PASS |
| NB 02 | 12 scores changed, 14 cap-triggered, 0 violations | PASS |
| NB 03 | 18 cases, MAE: raw 13.57 / model_c 13.28 / p2 19.49; QC PASS | PASS |
| NB 04 | 21 testers scored; 13/13 QC checks PASS | PASS |
| NB 05 | 8 PNG assets generated | PASS |

---

## Important notes

1. **Proposal 2 only changes L3 usability time moderation.** Accessibility scores (L2) are
   produced in Notebook 01 and are not modified by Notebook 02.

2. **Accessibility Score changes come from Proposal 1 / Model C logic**, not Proposal 2.

3. **Tester Quality is an independent third score.** It must not be multiplied into final
   accessibility or usability scores. It is for quality monitoring and review prioritisation only.

4. **Manual Review is a validation sample, not official ground truth.** The manual score is a
   reviewer-estimated anchor. The sample size (18 cases, 14 valid) is too small for definitive
   statistical conclusions.

5. **Do not overclaim that Proposal 2 is always better.** The manual review showed that time is
   useful but noisy. Several long-duration cases were successful or verbose, causing over-penalization.

6. **Retry is not direct scoring.** Retry/confusion language in transcripts is supporting evidence
   only, never a direct scoring rule.
