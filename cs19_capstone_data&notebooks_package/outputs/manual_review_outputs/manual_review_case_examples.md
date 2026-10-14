# Manual Review Case Examples

## Example 1: Proposal 2 clearly helpful - case_001 / ghum / AAMI Website

The participant transcript included explicit difficulty navigating and interpreting homepage
content. The raw survey score was 100 and the pre-time model score was 90.1, while the Proposal 2
after-time score was 50. The manual label was moderate_friction with a ground-truth estimate
of 55, making Proposal 2 much closer for this case.

## Example 2: Proposal 2 neutral - case_003 / rae / PDFs and Understanding Terms

The participant found the PDF and reviewed it, but experienced clear friction from the 104-page
document, mobile zooming, and accidental scrolling. The manual label was moderate_friction
with a score of 55. All three candidate scores were similarly close, so this case supports the
presence of friction but does not uniquely support the time cap.

## Example 3: Time signal noisy - case_002 / ramazankawish / AAMI Website

The participant spent a long time evaluating the AAMI website, triggering strong time friction
and reducing the Proposal 2 score to 40. Manual review found that the participant repeatedly
described the website as accessible, useful, trustworthy, and easy to navigate. The manual label
was smooth_success with a score of 90, showing that high duration can reflect detailed
commentary rather than real usability failure.

## Example 4: Time alone insufficient - case_011 / gameoverdan / AAMI Website

The normalized time signal was normal, but transcript evidence showed severe accessibility
friction: small text, difficult navigation, visual complexity, and repeated zoom/scrolling.
The manual label was severe_friction_or_failure with a score of 25. This case shows that
time alone cannot detect accessibility barriers.