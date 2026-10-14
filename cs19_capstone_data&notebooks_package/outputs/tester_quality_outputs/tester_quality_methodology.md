# Tester Quality Rating Mini Prototype Methodology

## Purpose

The Tester Quality Rating is a third, independent score for the CS19 capstone scoring system. It does not evaluate whether the AAMI website is good or bad, and it does not judge a participant's ability. Instead, it evaluates whether each tester's feedback appears reliable, specific, useful, and sufficiently evidenced.

Tester Quality Rating should not penalize disability, assistive technology use, slower reading, or ESL status. It only evaluates feedback quality, evidence completeness, and reliability.

## Data Sources

The prototype used the raw AAMI survey export, Proposal 2 integrated scoring outputs, participant-normalized time signals, LLM-generated individual insight evidence, local transcript segment files, and the earlier manual review sample.

## Why Tester Quality Rating Is Needed

Accessibility and usability scores describe product experience, but client interpretation also depends on the quality of the evidence behind those scores. This MVP keeps the rating separate from Proposal 1 and Proposal 2. It is intended for quality monitoring, review prioritisation, and future confidence weighting, not for changing final accessibility/usability outputs.

## Sub-score Definitions

| Sub-score | Weight | Definition | Main features used |
|---|---|---|---|
| Feedback Depth Score | 35% | Measures whether open-ended feedback is detailed, specific, and actionable. | total open-text word count, non-empty open answers, specific issue terms, actionable feedback answers, vague answer count. |
| Task Coverage Score | 25% | Measures whether the tester has enough task/component evidence for interpretation. | attempted/evidenced tasks, survey task score responses, transcript-evidenced tasks, LLM insight task coverage, expected non-excluded tasks. |
| Evidence Consistency Score | 25% | Measures whether survey ratings are broadly consistent with model, insight, time, and manual-review evidence. | raw survey average, Proposal 2 L3 average, score gap, high/severe friction count, friction mentions in survey text, manual-review gap when available. |
| Engagement / Effort Score | 15% | Measures whether there is enough evidence of meaningful participation without rewarding or punishing slowness. | survey completion, open-answer completion, attempted tasks, transcript/session duration, extremely short session plus low feedback flag. |

## Formula and Weights

tester_quality_score = 0.35 * feedback_depth_score + 0.25 * task_coverage_score + 0.25 * evidence_consistency_score + 0.15 * engagement_effort_score

When one or more dimensions were missing, the score was calculated from available dimensions only and the remaining weights were re-normalised. Missing dimensions were recorded in missing_dimensions.

## Fairness Safeguards

The prototype explicitly avoids direct penalties for disability cohort, screen-reader use, VoiceOver/NVDA/JAWS use, magnification, Deaf/Blind/Low Vision status, ESL status, negative feedback, blockers, or slower completion. Slow task duration is not interpreted as low quality. The engagement score only penalises the combination of an extremely short session plus sparse written feedback, because that pattern suggests low evidence rather than disability-related access needs.

## Relationship to Proposal 1 and Proposal 2

Tester Quality Rating is independent of Proposal 1 (Model C scoring) and Proposal 2 (time moderation). It does not change accessibility or usability scores. It is intended for quality monitoring, review prioritisation, and future confidence weighting only.

## Limitations

This is a mini prototype, not a final psychometric model. The raw survey export provided strong open-text data, but survey-response header timing fields were unusable. Proposal 2 maps only a subset of Model C tasks, so model score gaps are incomplete for some components.

## Future Improvements

Future versions should integrate direct platform response IDs, use explicit task-completion events, add rubric-calibrated manual labels for more participants, separate task-level tester reliability from participant-level quality, and include a confidence interval for each score.
