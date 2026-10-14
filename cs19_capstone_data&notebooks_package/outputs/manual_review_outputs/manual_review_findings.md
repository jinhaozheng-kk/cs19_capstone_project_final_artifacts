# Manual Expert Review / Ground Truth Validation Findings

**Author:** CS19 Capstone Project
**Date:** 2026-05-16
**Scope:** CS19 capstone validation sample for Proposal 2 participant-normalized time moderation.

## 1. Purpose

This manual review provides a reviewer-estimated ground truth validation sample for comparing
three candidate scoring outputs: the raw survey/self-reported score, Model C before Proposal 2
time moderation, and Proposal 2 after-time moderation. The purpose is to supplement the
validation framework, not to replace the model, redefine Proposal 1 or Proposal 2, or convert
retry behaviour into an automatic scoring rule.

## 2. Method

The sample contains 18 participant-task cases, of which 14 cases have a
manual ground-truth estimate and 4 cases are marked as insufficient evidence.

| manual_label               |   n_cases |
|:---------------------------|----------:|
| minor_friction             |         6 |
| smooth_success             |         4 |
| insufficient_evidence      |         4 |
| moderate_friction          |         2 |
| severe_friction_or_failure |         2 |

## 3. Validation Summary

| metric                            |   mean_absolute_error |   median_absolute_error |   n_cases |   closest_count_including_ties |   closest_percentage_including_ties |   unique_closest_count |   unique_closest_percentage | notes                                                                                             |
|:----------------------------------|----------------------:|------------------------:|----------:|-------------------------------:|------------------------------------:|-----------------------:|----------------------------:|:--------------------------------------------------------------------------------------------------|
| raw_survey_score                  |                 13.57 |                      10 |        14 |                             11 |                                78.6 |                      1 |                         7.1 | Closest counts are tie-aware; percentages can sum above 100 when several scores tie.              |
| model_c_before_time               |                 13.28 |                      10 |        14 |                             12 |                                85.7 |                      1 |                         7.1 | Closest counts are tie-aware; percentages can sum above 100 when several scores tie.              |
| proposal2_after_time              |                 19.49 |                      10 |        14 |                             10 |                                71.4 |                      1 |                         7.1 | Closest counts are tie-aware; percentages can sum above 100 when several scores tie.              |
| tie_cases_multiple_scores_closest |                nan    |                     nan |        14 |                             11 |                                78.6 |                    nan |                       nan   | Number of valid cases where two or three candidate scores were equally close to the manual score. |

The validation sample does NOT support a broad conclusion that Proposal 2 after-time scores
are closer to manual review than the raw survey score or Model C before time.
Model C before time has the lowest mean absolute error in this sample.
Proposal 2 after time has a higher MAE, primarily because several long-duration tasks were
successful but verbose, segmented across adjacent tasks, or driven by multi-route evaluation
rather than actual failure.

## 4. Key Findings

Proposal 2 was clearly helpful in case_001 / ghum / AAMI Website, where the transcript showed
real navigation/readability friction and the after-time score was much closer to the manual score.

However, several cases show that the time signal remains noisy:
case_002 / ramazankawish / AAMI Website, case_004 / sharelinsonny / Emergency Response, case_005 / sharelinsonny / Finding Answers, case_007 / fjone7 / AAMI Website, case_008 / reneerussell99 / AAMI Website.

## 5. Limitations

This manual review has a small sample size and should not be treated as definitive statistical
proof. Transcript text may mix participant speech, screen-reader output, page audio, and system
audio. Segment boundaries are approximate. The manual score is a reviewer estimate for validation
comparison, not official ground truth.

## 6. Recommendation

Use this manual review as a validation sample and audit artifact rather than as a replacement
scoring mechanism. Proposal 2 should remain a moderation signal, but future iterations should
avoid treating high normalized time as conclusive evidence without supporting transcript,
clickstream, or focus evidence.