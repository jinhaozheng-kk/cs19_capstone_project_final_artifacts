from pathlib import Path
import pandas as pd
import numpy as np
import re, json, math
from collections import defaultdict

ROOT = Path('/home/ubuntu')
OUT = ROOT / 'tester_quality_outputs'
OUT.mkdir(exist_ok=True)

RAW_SURVEY_PATH = ROOT/'upload/A_Test_Raw_Survey_Scores_AAMIInsuranceWebsite-Website.xls'
PROPOSAL2_INTEGRATED_PATH = ROOT/'proposal2_outputs/proposal2_integrated_l3_time_score.csv'
PROPOSAL2_TIME_PATH = ROOT/'proposal2_outputs/proposal2_time_signal_result_recomputed_for_integration.csv'
INSIGHTS_PATH = ROOT/'proposal2_integration_work/proposal1_df_insights.csv'
MANUAL_REVIEW_PATH = ROOT/'manual_review_outputs/manual_review_cases.csv'
TASKS_PATH = ROOT/'upload/aami-website-tasks(1).csv'
SEG_DIR = ROOT/'upload'

# -----------------------
# Helpers
# -----------------------
def norm_email(x):
    if pd.isna(x):
        return ''
    return str(x).strip().lower()

def keyify(x):
    if pd.isna(x): return ''
    return re.sub(r'[^a-z0-9]+', '', str(x).strip().lower())

def email_local(email):
    e = norm_email(email)
    return e.split('@')[0] if '@' in e else e

# Known identity aliases needed because the raw survey export and the insight/time exports use a few different emails.
EMAIL_TO_PARTICIPANT = {
    'reneerussell99@hotmail.com':'reneerussell99',
    'reececraigie@outlook.com':'reececraigie',
    'giuliaclemente26@gmail.com':'giuliaclemente26',
    'mgblackwell2001@gmail.com':'mgblackwell2001',
    'carlpatrickrobinson@gmail.com':'carlpatrickrobinson',
    'ghum@me.com':'ghum',
    'fjone7@gmail.com':'fjone7',
    'gracieha22@gmail.com':'gracieha22',
    'tdcn66@gmail.com':'marychaunguyen',
    'marychaunguyen@hotmail.com':'marychaunguyen',
    'terryaflint17@gmail.com':'terryaflint17',
    'sharelinsonny@gmail.com':'sharelinsonny',
    'asmaosyan9@gmail.com':'asma',
    'asma@civikpeople.com.au':'asma',
    'mattymc2@gmail.com':'info',
    'info@smproductions.com.au':'info',
    'gameoverdan@gmail.com':'gameoverdan',
    'oliviamitchell22@gmail.com':'oliviamitchell22',
    'thanoptions@icloud.com':'thanoptions',
    'ramazankawish@gmail.com':'ramazankawish',
    'laurenrosemetzler@gmail.com':'laurenrosemetzler',
    'kris.rae@live.com.au':'rae',
    'margieflint@iprimus.com.au':'margieflint',
    'troyparnell@hotmail.com':'troyparnell',
}

def participant_from_email(email):
    e = norm_email(email)
    if e in EMAIL_TO_PARTICIPANT:
        return EMAIL_TO_PARTICIPANT[e]
    return keyify(email_local(e))

def participant_from_any(row, email_col='email', participant_col='participant'):
    e = norm_email(row.get(email_col, '')) if isinstance(row, dict) else ''
    if e:
        return participant_from_email(e)
    p = row.get(participant_col, '') if isinstance(row, dict) else ''
    return keyify(p)

VAGUE_PATTERNS = [
    r'^\s*$', r'^(no|none|nothing|n/a|na|nil|not sure|unsure)\.?$',
    r'^(good|fine|ok|okay|great|easy|nice|clear|yes)\.?$',
    r'^(all good|not much|no issues|nothing really)\.?$'
]
SPECIFIC_TERMS = [
    'search', 'search box', 'voiceover', 'screen reader', 'nvda', 'jaws', 'pdf', 'pds',
    'product disclosure', 'quote', 'home page', 'homepage', 'navigation', 'menu', 'heading',
    'link', 'button', 'label', 'form', 'chat', 'live chat', 'emergency', 'natural disaster',
    'financial hardship', 'faq', 'disclosure', 'document', 'glossary', 'keyboard', 'mobile',
    'browser', 'safari', 'chrome', 'inaccessible', 'difficult', 'confusing', 'could not',
    "couldn't", 'unable', 'locate', 'find', 'read', 'understand', 'plain english', 'contrast',
    'magnification', 'subtitles', 'auslan', 'error', 'login', 'account', 'payment'
]
ACTION_TERMS = [
    'should', 'could', 'would', 'need', 'needs', 'make', 'add', 'improve', 'redesign',
    'include', 'provide', 'clearer', 'visible', 'easier', 'plain english', 'larger', 'better',
    'simplify', 'label', 'heading', 'link directly', 'search box', 'filter', 'guide', 'tool'
]
FRICTION_TERMS = [
    'difficult', 'confusing', 'frustrating', 'could not', "couldn't", 'unable', 'hard',
    'blocked', 'inaccessible', 'not accessible', 'issue', 'problem', 'barrier', 'struggle',
    'difficult to locate', 'not locate', 'not find', 'unclear', 'overwhelming', 'slow',
    'did not understand', 'didn’t understand', "didn't understand"
]

EXCLUDE_OPEN_COL_TERMS = [
    'timestamp', 'email address', 'type of tester', 'assistive technolog', 'adaption',
    'age range', 'gender', 'device', 'browser', 'state where', 'location', 'postcode',
    'previously explored', 'considered aami', 'select all', 'select the option',
    'how digitally proficient', 'most important', 'how did you begin', 'how do you usually prefer',
    'when you need to', 'generally speaking', 'now considering', 'personal information',
    'passwords', 'account?'
]
INCLUDE_OPEN_COL_TERMS = [
    'explain', 'describe', 'what would make', 'what information', 'did you find anything',
    'before you began', 'previously experienced', 'best thing', 'most difficult',
    'three issues', 'redesign', 'best insurance website', 'compare with other services',
    'product disclosure pdf', 'feedback trying', 'terminology and services',
    'met your expectations', 'blocked from completing', 'independently answer questions',
    'ease of navigating online services'
]

SCORE_COLS = [
    'Overall, how accessible did you find the AAMI website?',
    'Generally speaking, how user friendly, inuitive, helpful was the AAMI website to use?',
    'How user-friendly was the AAMI Homepage?',
    'How easy was it to find and read a product disclosure statement?',
    'How easy and clear was the information on Natural disasters?',
    'How user-friendly was the search function?',
    'How user friendly was the live chat?',
    'How easy was it to navigate around the website?'
]
TASK_SURVEY_SCORE_COLS = SCORE_COLS[2:]

def count_words(text):
    if pd.isna(text): return 0
    return len(re.findall(r"\b[\w'’.-]+\b", str(text)))

def is_vague(text):
    if pd.isna(text): return False
    s = str(text).strip().lower()
    if not s: return True
    # Multi-select lists are not considered vague if they contain semicolon-delimited details.
    if ';' in s and count_words(s) > 3:
        return False
    if count_words(s) <= 2:
        return True
    return any(re.match(p, s) for p in VAGUE_PATTERNS)

def count_terms(text, terms):
    if pd.isna(text): return 0
    s = str(text).lower()
    return sum(len(re.findall(re.escape(t.lower()), s)) for t in terms)

def clamp(x, lo=0, hi=100):
    if pd.isna(x): return np.nan
    return max(lo, min(hi, float(x)))

def score_to_band(score):
    if pd.isna(score): return 'insufficient_data'
    if score >= 85: return 'high_quality'
    if score >= 70: return 'good_quality'
    if score >= 50: return 'medium_quality'
    return 'low_quality_review_needed'

# -----------------------
# Load data
# -----------------------
raw = pd.read_csv(RAW_SURVEY_PATH, engine='python')
raw['email'] = raw['Please enter your email address'].map(norm_email)
raw['participant'] = raw['email'].map(participant_from_email)
raw['primary_cohort'] = raw['What type of tester are you? (Select all that apply)'].astype(str).str.replace(';', ',', regex=False)

p2 = pd.read_csv(PROPOSAL2_INTEGRATED_PATH)
p2['email_norm'] = p2['email'].map(norm_email)
p2['participant_unified'] = p2.apply(lambda r: participant_from_email(r['email_norm']) if pd.notna(r.get('email_norm')) and r.get('email_norm') else keyify(r.get('participant', '')), axis=1)

time = pd.read_csv(PROPOSAL2_TIME_PATH)
time['email_norm'] = time['email'].map(norm_email)
time['participant_unified'] = time.apply(lambda r: participant_from_email(r['email_norm']) if pd.notna(r.get('email_norm')) and r.get('email_norm') else keyify(r.get('participant', '')), axis=1)

ins = pd.read_csv(INSIGHTS_PATH)
ins['email_norm'] = ins['tester_email'].map(norm_email)
ins['participant_unified'] = ins.apply(lambda r: participant_from_email(r['email_norm']) if r['email_norm'] else keyify(r.get('tester_name','')), axis=1)

try:
    manual = pd.read_csv(MANUAL_REVIEW_PATH)
    manual['email_norm'] = manual['email'].map(norm_email)
    manual['participant_unified'] = manual.apply(lambda r: participant_from_email(r['email_norm']) if r['email_norm'] else keyify(r.get('participant','')), axis=1)
except Exception:
    manual = pd.DataFrame()

tasks = pd.read_csv(TASKS_PATH)
expected_tasks = int((tasks['ExcludeFromCollation'].astype(str).str.lower() != 'true').sum()) if 'ExcludeFromCollation' in tasks.columns else 10
if expected_tasks <= 0: expected_tasks = 10

# Segment evidence aggregation from local segment CSVs.
segment_stats = {}
for seg_path in sorted(SEG_DIR.glob('*_segments.csv')):
    p = keyify(seg_path.name.replace('_segments.csv', ''))
    # Sharelinsonny should normalize to sharelinsonny; others already match aliases.
    try:
        sdf = pd.read_csv(seg_path)
        if len(sdf):
            end_max = pd.to_numeric(sdf['end_time'], errors='coerce').max() if 'end_time' in sdf.columns else np.nan
            text_words = sdf['text'].fillna('').map(count_words).sum() if 'text' in sdf.columns else 0
            segment_stats[p] = {'segment_file': seg_path.name, 'segment_count': len(sdf), 'segment_duration_minutes': float(end_max)/60 if pd.notna(end_max) else np.nan, 'transcript_word_count': int(text_words)}
    except Exception:
        pass

# Determine open-ended response columns from raw survey export.
open_cols = []
for c in raw.columns:
    lc = c.lower().strip()
    if c in ['Timestamp', 'Please enter your email address']:
        continue
    if c in SCORE_COLS:
        continue
    if any(term in lc for term in INCLUDE_OPEN_COL_TERMS):
        open_cols.append(c)
    elif any(term in lc for term in EXCLUDE_OPEN_COL_TERMS):
        continue
# Ensure no duplicates while preserving order.
open_cols = list(dict.fromkeys(open_cols))
number_of_open_answers = len(open_cols)

# Aggregates from p2/model scores.
p2_part = p2.groupby('participant_unified').agg(
    average_l3_after_proposal2_time=('l3_score_after_proposal2_time','mean'),
    average_l3_before_time=('l3_score_before_time','mean'),
    number_of_model_rows=('model_c_task','count'),
    matched_model_tasks=('model_c_task_key', lambda x: x.dropna().nunique()),
    p2_changed_rows=('proposal2_changed_score', lambda x: int((x.astype(str).str.lower()=='true').sum())),
    p2_strong_time_rows=('time_signal', lambda x: int((x.astype(str)=='strong_time_friction').sum())),
).reset_index()

# Time/task coverage aggregates.
time_part = time.groupby('participant_unified').agg(
    number_of_tasks_with_transcript_evidence=('task_id', lambda x: x.dropna().astype(str).nunique()),
    total_session_duration_minutes=('end_seconds', lambda x: pd.to_numeric(x, errors='coerce').max()/60),
    strong_time_friction_count=('time_signal', lambda x: int((x.astype(str)=='strong_time_friction').sum())),
    medium_time_friction_count=('time_signal', lambda x: int((x.astype(str)=='medium_time_friction').sum())),
    task_rows_with_time=('task_id','count')
).reset_index()

# Insights evidence aggregates.
def weighted_severity(series):
    weights = {'low':1, 'medium':2, 'high':3, 'severe':4, 'blocker':5}
    return sum(weights.get(str(s).strip().lower(), 0) for s in series.dropna())

ins_part = ins.groupby('participant_unified').agg(
    insight_count=('category','count'),
    friction_insight_count=('category', lambda x: int((x.astype(str).str.lower().isin(['friction','blocker'])).sum())),
    high_severe_blocker_insight_count=('severity', lambda x: int(x.astype(str).str.lower().isin(['high','severe','blocker']).sum())),
    blocker_insight_count=('severity', lambda x: int(x.astype(str).str.lower().isin(['blocker','severe']).sum())),
    insight_task_coverage=('task_title', lambda x: x.dropna().astype(str).nunique()),
    insight_severity_weight=('severity', weighted_severity),
).reset_index()

if not manual.empty:
    manual_valid = manual[manual['manual_ground_truth_score'].notna()].copy()
    manual_valid['manual_abs_gap_after'] = (pd.to_numeric(manual_valid['l3_score_after_proposal2_time'], errors='coerce') - pd.to_numeric(manual_valid['manual_ground_truth_score'], errors='coerce')).abs()
    man_part = manual_valid.groupby('participant_unified').agg(
        manual_review_case_count=('case_id','count'),
        manual_avg_abs_gap_after=('manual_abs_gap_after','mean'),
        manual_insufficient_count=('manual_label', lambda x: int((x.astype(str)=='insufficient_evidence').sum()))
    ).reset_index()
else:
    man_part = pd.DataFrame(columns=['participant_unified','manual_review_case_count','manual_avg_abs_gap_after','manual_insufficient_count'])

# -----------------------
# Per-participant features and scores
# -----------------------
feature_rows = []
score_rows = []
unmatched_rows = []

for _, row in raw.iterrows():
    email = row['email']
    participant = row['participant']
    primary_cohort = row['primary_cohort'] if pd.notna(row['primary_cohort']) else ''

    # Survey open text features.
    answer_texts = []
    for c in open_cols:
        v = row.get(c, np.nan)
        if pd.notna(v):
            answer_texts.append(str(v))
        else:
            answer_texts.append('')
    non_empty_answers = [a for a in answer_texts if a.strip()]
    word_counts = [count_words(a) for a in answer_texts]
    total_open_words = int(sum(word_counts))
    avg_open_words = float(np.mean([w for w,a in zip(word_counts, answer_texts) if a.strip()])) if non_empty_answers else 0.0
    vague_count = int(sum(is_vague(a) for a in answer_texts if a.strip()))
    full_open_text = '\n'.join(non_empty_answers)
    specific_terms_count = int(count_terms(full_open_text, SPECIFIC_TERMS))
    actionable_count = int(sum(1 for a in non_empty_answers if count_terms(a, ACTION_TERMS) > 0))
    survey_mentions_friction_count = int(count_terms(full_open_text, FRICTION_TERMS))
    open_completion_ratio = len(non_empty_answers)/number_of_open_answers if number_of_open_answers else np.nan

    # Survey score features.
    raw_scores = []
    for c in SCORE_COLS:
        val = pd.to_numeric(row.get(c, np.nan), errors='coerce')
        if pd.notna(val): raw_scores.append(float(val) * 20.0)
    avg_raw_score = float(np.mean(raw_scores)) if raw_scores else np.nan
    task_survey_count = int(sum(pd.notna(pd.to_numeric(row.get(c, np.nan), errors='coerce')) for c in TASK_SURVEY_SCORE_COLS))

    # External evidence features.
    p2r = p2_part[p2_part['participant_unified'] == participant]
    tr = time_part[time_part['participant_unified'] == participant]
    ir = ins_part[ins_part['participant_unified'] == participant]
    mr = man_part[man_part['participant_unified'] == participant]
    p2dict = p2r.iloc[0].to_dict() if len(p2r) else {}
    tdict = tr.iloc[0].to_dict() if len(tr) else {}
    idict = ir.iloc[0].to_dict() if len(ir) else {}
    mdict = mr.iloc[0].to_dict() if len(mr) else {}
    sdict = segment_stats.get(participant, {})

    n_transcript_tasks = tdict.get('number_of_tasks_with_transcript_evidence', np.nan)
    if pd.isna(n_transcript_tasks) and sdict:
        # Segment file without task segmentation still counts as transcript evidence, but task count unknown.
        n_transcript_tasks = np.nan
    total_session_duration = tdict.get('total_session_duration_minutes', np.nan)
    if pd.isna(total_session_duration):
        total_session_duration = sdict.get('segment_duration_minutes', np.nan)

    number_of_tasks_attempted = np.nanmax([x for x in [n_transcript_tasks, task_survey_count, p2dict.get('matched_model_tasks', np.nan), idict.get('insight_task_coverage', np.nan)] if not pd.isna(x)]) if any([not pd.isna(x) for x in [n_transcript_tasks, task_survey_count, p2dict.get('matched_model_tasks', np.nan), idict.get('insight_task_coverage', np.nan)]]) else np.nan
    task_coverage_ratio = float(min(number_of_tasks_attempted/expected_tasks, 1.0)) if pd.notna(number_of_tasks_attempted) else np.nan
    avg_l3_after = p2dict.get('average_l3_after_proposal2_time', np.nan)
    avg_gap = float(avg_raw_score - avg_l3_after) if pd.notna(avg_raw_score) and pd.notna(avg_l3_after) else np.nan
    high_sev = int(idict.get('high_severe_blocker_insight_count', 0) or 0)
    friction_count = int(idict.get('friction_insight_count', 0) or 0)
    blocker_count = int(idict.get('blocker_insight_count', 0) or 0)
    high_score_with_high_friction_count = int(high_sev if pd.notna(avg_raw_score) and avg_raw_score >= 80 else 0)

    survey_completion_ratio = float(row.dropna().shape[0] / len(raw.columns))
    extremely_short_session_flag = bool(pd.notna(total_session_duration) and total_session_duration < 10)
    extremely_short_plus_no_feedback_flag = bool(extremely_short_session_flag and total_open_words < 80 and open_completion_ratio < 0.6)

    # Feedback depth score.
    depth = 20
    depth += min(total_open_words / 12.0, 35)       # 420+ words approaches full volume credit.
    depth += min(len(non_empty_answers) / max(number_of_open_answers,1) * 20, 20)
    depth += min(specific_terms_count * 1.2, 18)
    depth += min(actionable_count * 2.5, 17)
    depth -= min(vague_count * 4.0, 20)
    feedback_depth_score = clamp(depth)
    if total_open_words >= 650 and specific_terms_count >= 20 and actionable_count >= 6:
        fd_reason = f'Open-ended feedback is very detailed ({total_open_words} words), with {specific_terms_count} concrete issue/task terms and {actionable_count} actionable answers.'
    elif total_open_words >= 300 and specific_terms_count >= 8:
        fd_reason = f'Open-ended feedback is usable and reasonably specific ({total_open_words} words, {specific_terms_count} concrete terms), though not uniformly detailed across every answer.'
    elif total_open_words >= 120:
        fd_reason = f'Open-ended feedback has some usable detail ({total_open_words} words), but specificity/actionability is limited relative to stronger testers.'
    else:
        fd_reason = f'Open-ended feedback is short or sparse ({total_open_words} words), so depth is limited even if some answers are complete.'

    # Task coverage score.
    if pd.isna(task_coverage_ratio):
        task_coverage_score = np.nan
        tc_reason = 'No reliable task coverage evidence was available from task segmentation, transcript segments, Proposal 2, or survey task responses.'
    else:
        tc_base = 35 + 65 * task_coverage_ratio
        # If only survey task responses but no transcript/time/insight coverage, cap score at medium-high.
        has_external_task_evidence = (pd.notna(n_transcript_tasks) and n_transcript_tasks > 0) or idict.get('insight_task_coverage', 0) > 0
        if not has_external_task_evidence:
            tc_base = min(tc_base, 72)
        # Do not penalize blocker if the participant gave detailed explanations.
        if task_coverage_ratio < 0.5 and total_open_words >= 500:
            tc_base += 10
        task_coverage_score = clamp(tc_base)
        tc_reason = f'Coverage estimate uses {number_of_tasks_attempted:.0f} attempted/evidenced tasks against {expected_tasks} expected non-excluded tasks; survey task score responses={task_survey_count}, transcript-evidenced tasks={n_transcript_tasks if pd.notna(n_transcript_tasks) else "NA"}, insight task coverage={idict.get("insight_task_coverage", 0)}.'

    # Evidence consistency score.
    evidence_missing = len(p2r)==0 and len(ir)==0 and len(mr)==0
    if evidence_missing:
        evidence_consistency_score = np.nan
        ec_reason = 'No Proposal 2/model rows, LLM insight rows, or manual-review cases were available, so consistency was not scored.'
    else:
        ec = 88
        # High survey score can coexist with friction if survey text documents it; only unexplained contradictions are penalized.
        if pd.notna(avg_gap):
            if avg_gap > 35:
                ec -= 24
            elif avg_gap > 25:
                ec -= 16
            elif avg_gap > 15:
                ec -= 8
            elif avg_gap < -25:
                ec -= 6  # participant rated worse than model; cautious minor mismatch only.
        if high_score_with_high_friction_count >= 5:
            ec -= 22
        elif high_score_with_high_friction_count >= 3:
            ec -= 14
        elif high_score_with_high_friction_count >= 1:
            ec -= 6
        # Survey explanations mitigate conflict.
        if survey_mentions_friction_count >= 8:
            ec += 16
        elif survey_mentions_friction_count >= 4:
            ec += 10
        elif survey_mentions_friction_count >= 2:
            ec += 5
        if total_open_words < 150 and high_sev >= 2 and pd.notna(avg_raw_score) and avg_raw_score >= 80:
            ec -= 18
        if blocker_count > 0 and survey_mentions_friction_count == 0 and pd.notna(avg_raw_score) and avg_raw_score >= 80:
            ec -= 18
        # Manual review disagreement suggests caution but small sample should not dominate.
        if mdict.get('manual_avg_abs_gap_after', np.nan) is not np.nan and pd.notna(mdict.get('manual_avg_abs_gap_after', np.nan)):
            if mdict['manual_avg_abs_gap_after'] > 30:
                ec -= 8
            elif mdict['manual_avg_abs_gap_after'] <= 15:
                ec += 3
        evidence_consistency_score = clamp(ec)
        conflict_note = 'no large unexplained conflict' if evidence_consistency_score >= 75 else 'some survey/evidence tension requiring review'
        avg_l3_txt = 'NA' if pd.isna(avg_l3_after) else f'{avg_l3_after:.1f}'
        avg_gap_txt = 'NA' if pd.isna(avg_gap) else f'{avg_gap:.1f}'
        avg_raw_txt = 'NA' if pd.isna(avg_raw_score) else f'{avg_raw_score:.1f}'
        ec_reason = f'Average raw survey score={avg_raw_txt} and average Proposal 2 L3 score={avg_l3_txt}; score gap={avg_gap_txt}. LLM insight high/severe/blocker count={high_sev}, survey friction mentions={survey_mentions_friction_count}; {conflict_note}.'

    # Engagement / effort score.
    engagement_missing = pd.isna(total_session_duration) and pd.isna(number_of_tasks_attempted)
    if engagement_missing:
        engagement_effort_score = np.nan
        ee_reason = 'No session duration or task-attempt evidence was available, so engagement/effort was not scored.'
    else:
        ee = 45
        ee += min((number_of_tasks_attempted if pd.notna(number_of_tasks_attempted) else 0) / expected_tasks * 30, 30)
        ee += min(open_completion_ratio * 15 if pd.notna(open_completion_ratio) else 0, 15)
        ee += 10 if survey_completion_ratio >= 0.9 else 5 if survey_completion_ratio >= 0.75 else 0
        if pd.notna(total_session_duration):
            if total_session_duration >= 45:
                ee += 5
            elif total_session_duration < 10:
                ee -= 18
            elif total_session_duration < 20:
                ee -= 6
        if extremely_short_plus_no_feedback_flag:
            ee -= 22
        if total_open_words >= 350 and (number_of_tasks_attempted if pd.notna(number_of_tasks_attempted) else 0) >= 5:
            ee += 5
        engagement_effort_score = clamp(ee)
        ee_reason = f'Engagement uses survey completion ratio={survey_completion_ratio:.2f}, open-answer completion={open_completion_ratio:.2f}, attempted/evidenced tasks={number_of_tasks_attempted if pd.notna(number_of_tasks_attempted) else "NA"}, and session duration={total_session_duration:.1f} minutes if available. Slow completion was not penalized; only very short sessions with little feedback are flagged.' if pd.notna(total_session_duration) else f'Engagement uses survey completion ratio={survey_completion_ratio:.2f}, open-answer completion={open_completion_ratio:.2f}, and attempted/evidenced tasks={number_of_tasks_attempted if pd.notna(number_of_tasks_attempted) else "NA"}; no reliable duration was available.'

    dims = {
        'feedback_depth_score': feedback_depth_score,
        'task_coverage_score': task_coverage_score,
        'evidence_consistency_score': evidence_consistency_score,
        'engagement_effort_score': engagement_effort_score,
    }
    weights = {
        'feedback_depth_score': 0.35,
        'task_coverage_score': 0.25,
        'evidence_consistency_score': 0.25,
        'engagement_effort_score': 0.15,
    }
    avail = [k for k,v in dims.items() if pd.notna(v)]
    missing = [k for k,v in dims.items() if pd.isna(v)]
    if avail:
        denom = sum(weights[k] for k in avail)
        total_score = sum(dims[k]*weights[k] for k in avail)/denom
        total_score = round(clamp(total_score), 2)
    else:
        total_score = np.nan
    band = score_to_band(total_score)

    flags = []
    if pd.isna(total_score) or len(missing) >= 2 or 'evidence_consistency_score' in missing:
        flags.append('insufficient_data')
    if pd.notna(feedback_depth_score) and feedback_depth_score < 50:
        flags.append('low_feedback_depth')
    if pd.notna(task_coverage_score) and task_coverage_score < 60:
        flags.append('low_task_coverage')
    if pd.notna(evidence_consistency_score) and evidence_consistency_score < 65:
        flags.append('high_survey_model_conflict')
    if pd.notna(engagement_effort_score) and engagement_effort_score < 60:
        flags.append('possible_low_engagement')
    if not flags:
        flags.append('no_review_needed')
    review_flag = ';'.join(flags)
    overall_quality_reason = f'Overall score combines available dimensions ({", ".join(avail)}) using the required weights with renormalisation for missing dimensions. Main drivers: feedback_depth={feedback_depth_score:.1f}, task_coverage={task_coverage_score if pd.notna(task_coverage_score) else "NA"}, evidence_consistency={evidence_consistency_score if pd.notna(evidence_consistency_score) else "NA"}, engagement_effort={engagement_effort_score if pd.notna(engagement_effort_score) else "NA"}. Review flag: {review_flag}.'

    feature_rows.append({
        'participant': participant,
        'email': email,
        'total_open_text_word_count': total_open_words,
        'average_open_answer_word_count': round(avg_open_words, 2),
        'number_of_open_answers': number_of_open_answers,
        'number_of_non_empty_open_answers': len(non_empty_answers),
        'open_answer_completion_ratio': round(open_completion_ratio, 4),
        'vague_answer_count': vague_count,
        'specific_issue_terms_count': specific_terms_count,
        'actionable_feedback_count': actionable_count,
        'number_of_tasks_attempted': np.nan if pd.isna(number_of_tasks_attempted) else int(number_of_tasks_attempted),
        'number_of_tasks_with_survey_response': task_survey_count,
        'number_of_tasks_with_transcript_evidence': np.nan if pd.isna(n_transcript_tasks) else int(n_transcript_tasks),
        'task_coverage_ratio': np.nan if pd.isna(task_coverage_ratio) else round(task_coverage_ratio, 4),
        'average_raw_survey_score': np.nan if pd.isna(avg_raw_score) else round(avg_raw_score, 2),
        'average_l3_after_proposal2_time': np.nan if pd.isna(avg_l3_after) else round(float(avg_l3_after), 2),
        'average_score_gap': np.nan if pd.isna(avg_gap) else round(avg_gap, 2),
        'high_score_with_high_friction_count': high_score_with_high_friction_count,
        'total_session_duration_minutes': np.nan if pd.isna(total_session_duration) else round(float(total_session_duration), 2),
        'extremely_short_session_flag': extremely_short_session_flag,
        'extremely_short_plus_no_feedback_flag': extremely_short_plus_no_feedback_flag,
        # Additional audit columns for explainability.
        'survey_mentions_friction_count': survey_mentions_friction_count,
        'llm_friction_insight_count': friction_count,
        'llm_high_severe_blocker_insight_count': high_sev,
        'llm_blocker_insight_count': blocker_count,
        'proposal2_changed_rows': int(p2dict.get('p2_changed_rows', 0) or 0),
        'segment_file': sdict.get('segment_file', ''),
        'transcript_word_count': sdict.get('transcript_word_count', np.nan),
    })
    score_rows.append({
        'participant': participant,
        'email': email,
        'primary_cohort': primary_cohort,
        'tester_quality_score': total_score,
        'tester_quality_band': band,
        'feedback_depth_score': round(feedback_depth_score, 2) if pd.notna(feedback_depth_score) else np.nan,
        'task_coverage_score': round(task_coverage_score, 2) if pd.notna(task_coverage_score) else np.nan,
        'evidence_consistency_score': round(evidence_consistency_score, 2) if pd.notna(evidence_consistency_score) else np.nan,
        'engagement_effort_score': round(engagement_effort_score, 2) if pd.notna(engagement_effort_score) else np.nan,
        'available_dimensions': ';'.join(avail),
        'missing_dimensions': ';'.join(missing),
        'feedback_depth_reason': fd_reason,
        'task_coverage_reason': tc_reason,
        'evidence_consistency_reason': ec_reason,
        'engagement_effort_reason': ee_reason,
        'overall_quality_reason': overall_quality_reason,
        'review_flag': review_flag,
    })

    if evidence_missing:
        unmatched_rows.append({
            'participant': participant,
            'email': email,
            'missing_area': 'external_evidence_mapping',
            'reason': 'Raw survey participant could not be matched to Proposal 2/model rows, LLM insights, or manual-review evidence. Survey and local transcript may still exist, so this is not treated as low quality by itself.'
        })

features = pd.DataFrame(feature_rows).sort_values(['tester_quality_score' if 'tester_quality_score' in feature_rows else 'participant'] if False else ['participant'])
scores = pd.DataFrame(score_rows).sort_values('tester_quality_score', ascending=False, na_position='last')
unmatched = pd.DataFrame(unmatched_rows, columns=['participant','email','missing_area','reason'])

# Summary metrics.
summary_items = []
def add_metric(metric, value):
    summary_items.append({'metric': metric, 'value': value})

add_metric('number_of_testers', len(scores))
add_metric('average_tester_quality_score', round(scores['tester_quality_score'].dropna().mean(), 2))
add_metric('number_high_quality', int((scores['tester_quality_band']=='high_quality').sum()))
add_metric('number_good_quality', int((scores['tester_quality_band']=='good_quality').sum()))
add_metric('number_medium_quality', int((scores['tester_quality_band']=='medium_quality').sum()))
add_metric('number_low_quality_review_needed', int((scores['tester_quality_band']=='low_quality_review_needed').sum()))
add_metric('number_insufficient_data', int((scores['tester_quality_band']=='insufficient_data').sum() + scores['review_flag'].str.contains('insufficient_data').sum()))
add_metric('number_with_missing_dimensions', int(scores['missing_dimensions'].fillna('').astype(str).str.len().gt(0).sum()))
add_metric('average_feedback_depth_score', round(scores['feedback_depth_score'].dropna().mean(), 2))
add_metric('average_task_coverage_score', round(scores['task_coverage_score'].dropna().mean(), 2))
add_metric('average_evidence_consistency_score', round(scores['evidence_consistency_score'].dropna().mean(), 2))
add_metric('average_engagement_effort_score', round(scores['engagement_effort_score'].dropna().mean(), 2))
add_metric('number_review_flag_no_review_needed', int((scores['review_flag']=='no_review_needed').sum()))
add_metric('number_review_flag_low_feedback_depth', int(scores['review_flag'].str.contains('low_feedback_depth').sum()))
add_metric('number_review_flag_low_task_coverage', int(scores['review_flag'].str.contains('low_task_coverage').sum()))
add_metric('number_review_flag_high_survey_model_conflict', int(scores['review_flag'].str.contains('high_survey_model_conflict').sum()))
add_metric('number_review_flag_possible_low_engagement', int(scores['review_flag'].str.contains('possible_low_engagement').sum()))
add_metric('expected_non_excluded_tasks_used_for_coverage', expected_tasks)
add_metric('open_answer_columns_used', number_of_open_answers)
summary = pd.DataFrame(summary_items)

# Save CSVs.
scores.to_csv(OUT/'tester_quality_scores.csv', index=False)
features.to_csv(OUT/'tester_quality_features.csv', index=False)
summary.to_csv(OUT/'tester_quality_summary.csv', index=False)
unmatched.to_csv(OUT/'unmatched_tester_quality_participants.csv', index=False)

# -----------------------
# Markdown documentation
# -----------------------
score_preview = scores[['participant','email','tester_quality_score','tester_quality_band','review_flag']].copy()
review_needed = scores[scores['review_flag']!='no_review_needed'][['participant','email','tester_quality_score','tester_quality_band','review_flag']]

def md_table(df, max_rows=None):
    d = df.copy()
    if max_rows is not None:
        d = d.head(max_rows)
    return d.to_markdown(index=False)

methodology = f"""# Tester Quality Rating Mini Prototype Methodology

**Author:** Manus AI  
**Date:** 2026-05-15  
**Project:** CS19 Multi-Modal Data Fusion for Automated Accessibility & Usability Scoring

## Purpose

The **Tester Quality Rating** is a third, independent score for the CS19 capstone scoring system. It does **not** evaluate whether the AAMI website is good or bad, and it does **not** judge a participant's ability. Instead, it evaluates whether each tester's feedback appears reliable, specific, useful, and sufficiently evidenced for downstream interpretation.

> Tester Quality Rating should not penalize disability, assistive technology use, slower reading, or ESL status. It only evaluates feedback quality, evidence completeness, and reliability.

## Data Sources

The prototype used the raw AAMI survey export, the structured survey files, Proposal 2 integrated scoring outputs, participant-normalized time signals, LLM-generated individual insight evidence, local transcript segment files, and the earlier manual review sample. The raw survey export supplied the most direct participant/email mapping and open-ended answers. Proposal 2 and individual insights supplied external evidence about task behaviour, model scores, friction severity, and coverage.

| Source | Role in prototype |
|---|---|
| `A_Test_Raw_Survey_Scores_AAMIInsuranceWebsite-Website.xls` | Primary source for tester email, cohort, raw Likert scores, task-specific survey scores, and open-ended written feedback. |
| `proposal2_integrated_l3_time_score.csv` | Source for average L3 score after Proposal 2 time moderation, model-score gaps, changed rows, and mapped Model C tasks. |
| `proposal2_time_signal_result_recomputed_for_integration.csv` | Source for attempted task count, transcript-evidenced task count, session duration, and time signal labels. |
| `proposal1_df_insights.csv` / Individual Insights | Source for LLM friction counts, high/severe/blocker evidence, and insight task coverage. |
| `*_segments.csv` transcript files | Fallback transcript evidence and session-duration evidence where task segmentation/model rows are incomplete. |
| `manual_review_cases.csv` | Small validation evidence used only as a light consistency audit; it does not dominate the score. |
| `aami-website-tasks(1).csv` | Defines the expected non-excluded task count used in task coverage scoring. |

## Why Tester Quality Rating Is Needed

Accessibility and usability scores describe product experience, but client interpretation also depends on the **quality of the evidence** behind those scores. A tester can provide highly valuable feedback even when they experience blockers, are slow, use assistive technology, or rate the product negatively. Conversely, a response can require review when it contains little explanation, has very low task coverage, or shows a severe mismatch between high survey ratings and strong external evidence without any written explanation.

This MVP therefore keeps the rating separate from Proposal 1 and Proposal 2. It is intended for **quality monitoring**, **review prioritisation**, and future confidence weighting, not for changing final accessibility/usability outputs.

## Sub-score Definitions

| Sub-score | Weight | Definition | Main features used |
|---|---:|---|---|
| Feedback Depth Score | 35% | Measures whether open-ended feedback is detailed, specific, and actionable. | total open-text word count, non-empty open answers, specific issue terms, actionable feedback answers, vague answer count. |
| Task Coverage Score | 25% | Measures whether the tester has enough task/component evidence for interpretation. | attempted/evidenced tasks, survey task score responses, transcript-evidenced tasks, LLM insight task coverage, expected non-excluded tasks. |
| Evidence Consistency Score | 25% | Measures whether survey ratings are broadly consistent with model, insight, time, and manual-review evidence. | raw survey average, Proposal 2 L3 average, score gap, high/severe friction count, friction mentions in survey text, manual-review gap when available. |
| Engagement / Effort Score | 15% | Measures whether there is enough evidence of meaningful participation without rewarding or punishing slowness. | survey completion, open-answer completion, attempted tasks, transcript/session duration, extremely short session plus low feedback flag. |

## Formula and Weights

The required formula was applied where all dimensions were available:

```text
tester_quality_score =
0.35 * feedback_depth_score
+ 0.25 * task_coverage_score
+ 0.25 * evidence_consistency_score
+ 0.15 * engagement_effort_score
```

When one or more dimensions were missing, the score was calculated from available dimensions only and the remaining weights were re-normalised. Missing dimensions were recorded in `missing_dimensions` rather than being treated as low-quality evidence.

## Fairness Safeguards

The prototype explicitly avoids direct penalties for disability cohort, screen-reader use, VoiceOver/NVDA/JAWS use, magnification, Deaf/Blind/Low Vision status, ESL status, negative feedback, blockers, or slower completion. Slow task duration is **not** interpreted as low quality. The engagement score only penalises the combination of an **extremely short session plus sparse written feedback**, because that pattern suggests low evidence rather than disability-related access needs.

The Evidence Consistency Score also avoids the simplistic rule “high score plus friction equals low quality.” If a participant gives high ratings but describes concrete friction in survey text, that written explanation mitigates the conflict because it shows reflective and reliable feedback.

## Output Bands

| Score range | Band | Interpretation |
|---:|---|---|
| 85–100 | high_quality | Strong, specific, well-evidenced tester feedback. |
| 70–84 | good_quality | Usable and reliable feedback with only minor limitations. |
| 50–69 | medium_quality | Usable but limited feedback or evidence; review may be useful. |
| 0–49 | low_quality_review_needed | Low evidence, serious mismatch, or low engagement signal requiring review. |

## Limitations

This is a **mini prototype**, not a final psychometric model. The raw survey export provided strong open-text data, but survey-response header timing fields were unusable because recorded start and completion times were identical or blank. Proposal 2 maps only a subset of Model C tasks, so model score gaps are incomplete for some components. The LLM insight table is useful evidence but can over- or under-count repeated friction themes. Several identity mappings required alias handling because the raw survey and transcript/insight exports used different emails for the same tester.

The score should therefore be interpreted as a **review prioritisation signal**, not a definitive judgment of a person. Low or medium scores should prompt human review of the evidence, not automatic exclusion.

## Future Improvements

Future versions should integrate direct platform response IDs, use explicit task-completion events, add rubric-calibrated manual labels for more participants, separate task-level tester reliability from participant-level quality, and include a confidence interval for each score. A future pipeline could use `tester_quality_score` as a confidence modifier for interpreting participant feedback, but this MVP keeps it separate from the core accessibility/usability scoring pipeline.
"""
(OUT/'tester_quality_methodology.md').write_text(methodology, encoding='utf-8')

# Case examples: choose representative cases dynamically.
examples = []
# high quality: top score
if len(scores): examples.append(('High quality tester example', scores.iloc[0]))
# medium: closest to 60-75, prefer medium band
medium_candidates = scores[scores['tester_quality_band'].isin(['medium_quality','good_quality'])].copy()
if len(medium_candidates):
    medium_candidates['dist'] = (medium_candidates['tester_quality_score'] - 70).abs()
    examples.append(('Medium / usable-but-limited example', medium_candidates.sort_values('dist').iloc[0]))
# review: lowest score non no_review if exists
review_candidates = scores[scores['review_flag']!='no_review_needed'].copy()
if len(review_candidates): examples.append(('Review-needed example', review_candidates.sort_values('tester_quality_score').iloc[0]))
# insufficient / external evidence missing
insuff_candidates = scores[scores['missing_dimensions'].str.contains('evidence_consistency_score', na=False)].copy()
if len(insuff_candidates): examples.append(('Insufficient external-evidence example', insuff_candidates.iloc[0]))
# another high conflict if different
conflict_candidates = scores[scores['review_flag'].str.contains('high_survey_model_conflict', na=False)].copy()
if len(conflict_candidates): examples.append(('High survey/model conflict example', conflict_candidates.sort_values('tester_quality_score').iloc[0]))
# Deduplicate by participant, cap 5.
seen=set(); unique_examples=[]
for label, sr in examples:
    if sr['participant'] not in seen:
        unique_examples.append((label,sr)); seen.add(sr['participant'])
    if len(unique_examples)>=5: break

features_idx = features.set_index('participant')
case_md = "# Tester Quality Rating Case Examples\n\n**Author:** Manus AI  \n**Date:** 2026-05-15\n\nThese cases illustrate how the mini prototype should be interpreted. They are examples for review and explanation rather than judgments about participant capability. The rating does not penalise disability, assistive technology use, ESL status, slower reading, or accessibility blockers.\n\n"
for label, sr in unique_examples:
    fr = features_idx.loc[sr['participant']] if sr['participant'] in features_idx.index else pd.Series(dtype=object)
    case_md += f"## {label}: `{sr['participant']}`\n\n"
    case_md += f"| Field | Value |\n|---|---|\n"
    case_md += f"| Email | {sr['email']} |\n"
    case_md += f"| Quality band | {sr['tester_quality_band']} |\n"
    case_md += f"| Tester quality score | {sr['tester_quality_score']} |\n"
    case_md += f"| Review flag | {sr['review_flag']} |\n"
    case_md += f"| Open-text words | {fr.get('total_open_text_word_count', 'NA')} |\n"
    case_md += f"| Attempted/evidenced tasks | {fr.get('number_of_tasks_attempted', 'NA')} |\n"
    case_md += f"| Raw survey vs Proposal 2 average gap | {fr.get('average_score_gap', 'NA')} |\n\n"
    case_md += f"**Key evidence.** {sr['feedback_depth_reason']} {sr['task_coverage_reason']}\n\n"
    case_md += f"**Why the score makes sense.** {sr['overall_quality_reason']}\n\n"
    caution = 'The score is a review-prioritisation signal. It should not be used to discount the participant’s lived accessibility experience without human review.'
    if 'insufficient_data' in sr['review_flag'] or 'evidence_consistency_score' in str(sr['missing_dimensions']):
        caution += ' This case has missing external evidence, so the score is based only on available dimensions.'
    if 'high_survey_model_conflict' in sr['review_flag']:
        caution += ' The model flags a possible score/evidence conflict, but the final decision should inspect the transcript and survey text.'
    case_md += f"**Limitation / caution.** {caution}\n\n"
(OUT/'tester_quality_case_examples.md').write_text(case_md, encoding='utf-8')

# Quality check markdown.
qc_lines=[]
qc_lines.append('# Tester Quality Output Quality Check')
qc_lines.append('')
qc_lines.append('| Check | Result |')
qc_lines.append('|---|---|')
qc_lines.append(f"| All tester_quality_score values in 0–100 | {bool(scores['tester_quality_score'].dropna().between(0,100).all())} |")
sub_ok = all(scores[c].dropna().between(0,100).all() for c in ['feedback_depth_score','task_coverage_score','evidence_consistency_score','engagement_effort_score'])
qc_lines.append(f'| All sub-scores in 0–100 | {bool(sub_ok)} |')
qc_lines.append('| Cohort / assistive technology direct penalty used | False |')
qc_lines.append(f"| Missing dimensions recorded | {bool('missing_dimensions' in scores.columns)} |")
qc_lines.append(f"| Review flags populated | {bool(scores['review_flag'].astype(str).str.len().gt(0).all())} |")
reason_cols = ['feedback_depth_reason','task_coverage_reason','evidence_consistency_reason','engagement_effort_reason','overall_quality_reason']
qc_lines.append(f"| Reason columns populated | {bool(scores[reason_cols].fillna('').apply(lambda s: s.str.len().gt(0)).all().all())} |")
qc_lines.append(f"| Unmatched output created | {bool((OUT/'unmatched_tester_quality_participants.csv').exists())} |")
qc_lines.append(f"| Proposal 1 / Proposal 2 files modified | False |")
(OUT/'tester_quality_quality_check.md').write_text('\n'.join(qc_lines)+'\n', encoding='utf-8')

print('Wrote outputs to', OUT)
print(summary.to_string(index=False))
print('\nReview-needed testers:')
print(review_needed.to_string(index=False))
