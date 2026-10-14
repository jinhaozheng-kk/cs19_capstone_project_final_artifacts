"""
Tester Quality Rating — adapted from build_tester_quality_rating.py
Uses relative paths; called via exec() from notebook 04.
"""
from pathlib import Path
import re, json, math
import numpy as np
import pandas as pd
from collections import defaultdict

BASE_DIR    = Path(".").resolve()
INPUT_DIR   = BASE_DIR
OUTPUT_DIR  = BASE_DIR / "outputs"
TQ_OUT      = OUTPUT_DIR / "tester_quality_outputs"
SEGMENT_DIR = BASE_DIR / "proposal2_segments"
TQ_OUT.mkdir(parents=True, exist_ok=True)

RAW_SURVEY_PATH        = INPUT_DIR / "A_Test_Raw_Survey_Scores_AAMIInsuranceWebsite-Website.xls"
PROPOSAL2_INTEGRATED   = OUTPUT_DIR / "proposal2_integrated_l3_time_score.csv"
PROPOSAL2_TIME_PATH    = OUTPUT_DIR / "proposal2_time_signal_result_recomputed_for_integration.csv"
INSIGHTS_PATH          = OUTPUT_DIR / "proposal1_df_insights.csv"
MANUAL_REVIEW_PATH     = OUTPUT_DIR / "manual_review_outputs" / "manual_review_cases.csv"
TASKS_PATH             = INPUT_DIR / "aami-website-tasks(1).csv"

for p in [RAW_SURVEY_PATH, PROPOSAL2_INTEGRATED, PROPOSAL2_TIME_PATH, INSIGHTS_PATH, TASKS_PATH]:
    assert p.exists(), f"Missing: {p}"

# ── Identity alias map ─────────────────────────────────────────────────────
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

def norm_email(x):
    if pd.isna(x): return ''
    return str(x).strip().lower()

def keyify(x):
    if pd.isna(x): return ''
    return re.sub(r'[^a-z0-9]+', '', str(x).strip().lower())

def email_local(email):
    e = norm_email(email)
    return e.split('@')[0] if '@' in e else e

def participant_from_email(email):
    e = norm_email(email)
    if e in EMAIL_TO_PARTICIPANT:
        return EMAIL_TO_PARTICIPANT[e]
    return keyify(email_local(e))

# ── Text analysis helpers ──────────────────────────────────────────────────
VAGUE_PATTERNS = [
    r'^\s*$', r'^(no|none|nothing|n/a|na|nil|not sure|unsure)\.?$',
    r'^(good|fine|ok|okay|great|easy|nice|clear|yes)\.?$',
    r'^(all good|not much|no issues|nothing really)\.?$'
]
SPECIFIC_TERMS = [
    'search','search box','voiceover','screen reader','nvda','jaws','pdf','pds',
    'product disclosure','quote','home page','homepage','navigation','menu','heading',
    'link','button','label','form','chat','live chat','emergency','natural disaster',
    'financial hardship','faq','disclosure','document','glossary','keyboard','mobile',
    'browser','safari','chrome','inaccessible','difficult','confusing','could not',
    "couldn't",'unable','locate','find','read','understand','plain english','contrast',
    'magnification','subtitles','auslan','error','login','account','payment'
]
ACTION_TERMS = [
    'should','could','would','need','needs','make','add','improve','redesign',
    'include','provide','clearer','visible','easier','plain english','larger','better',
    'simplify','label','heading','link directly','search box','filter','guide','tool'
]
FRICTION_TERMS = [
    'difficult','confusing','frustrating','could not',"couldn't",'unable','hard',
    'blocked','inaccessible','not accessible','issue','problem','barrier','struggle',
    'difficult to locate','not locate','not find','unclear','overwhelming','slow',
    'did not understand',"didn't understand"
]
EXCLUDE_OPEN_COL_TERMS = [
    'timestamp','email address','type of tester','assistive technolog','adaption',
    'age range','gender','device','browser','state where','location','postcode',
    'previously explored','considered aami','select all','select the option',
    'how digitally proficient','most important','how did you begin','how do you usually prefer',
    'when you need to','generally speaking','now considering','personal information',
    'passwords','account?'
]
INCLUDE_OPEN_COL_TERMS = [
    'explain','describe','what would make','what information','did you find anything',
    'before you began','previously experienced','best thing','most difficult',
    'three issues','redesign','best insurance website','compare with other services',
    'product disclosure pdf','feedback trying','terminology and services',
    'met your expectations','blocked from completing','independently answer questions',
    'ease of navigating online services'
]
SCORE_COLS = [
    'Overall, how accessible did you find the AAMI website?',
    'How well were you able to navigate and access the information you needed?',
    'How would you rate the overall usability and ease of use of this experience?',
    'How accessible was your overall experience with this digital product?',
]
TASK_SURVEY_SCORE_COLS = [
    'How user-friendly was the AAMI Homepage?',
    'How easy was it to find and read a product disclosure statement?',
    'How easy and clear was the information on Natural disasters?',
    'How user-friendly was the search function?',
    'How user friendly was the live chat?',
    'How easy was it to navigate around the website?',
]

def count_words(s):
    if pd.isna(s): return 0
    return len(re.findall(r'\b\w+\b', str(s)))

def is_vague(s):
    if pd.isna(s): return False
    if count_words(s) <= 2: return True
    return any(re.match(p, str(s).strip().lower()) for p in VAGUE_PATTERNS)

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

# ── Load data ──────────────────────────────────────────────────────────────
raw = pd.read_csv(RAW_SURVEY_PATH)
raw['email']       = raw['Please enter your email address'].map(norm_email)
raw['participant'] = raw['email'].map(participant_from_email)
raw['primary_cohort'] = raw['What type of tester are you? (Select all that apply)'].astype(str).str.replace(';',',',regex=False)

p2 = pd.read_csv(PROPOSAL2_INTEGRATED)
p2['email_norm']         = p2['email'].map(norm_email)
p2['participant_unified'] = p2.apply(
    lambda r: participant_from_email(r['email_norm']) if r.get('email_norm') else keyify(r.get('participant','')), axis=1)

time_df = pd.read_csv(PROPOSAL2_TIME_PATH)
time_df['email_norm']         = time_df['email'].map(norm_email)
time_df['participant_unified'] = time_df.apply(
    lambda r: participant_from_email(r['email_norm']) if r.get('email_norm') else keyify(r.get('participant','')), axis=1)

ins = pd.read_csv(INSIGHTS_PATH)
ins['email_norm']         = ins['tester_email'].map(norm_email)
ins['participant_unified'] = ins.apply(
    lambda r: participant_from_email(r['email_norm']) if r['email_norm'] else keyify(r.get('tester_name','')), axis=1)

try:
    manual = pd.read_csv(MANUAL_REVIEW_PATH)
    manual['email_norm']         = manual['email'].map(norm_email)
    manual['participant_unified'] = manual.apply(
        lambda r: participant_from_email(r['email_norm']) if r['email_norm'] else keyify(r.get('participant','')), axis=1)
except Exception:
    manual = pd.DataFrame()

tasks = pd.read_csv(TASKS_PATH)
expected_tasks = int((tasks['ExcludeFromCollation'].astype(str).str.lower() != 'true').sum()) if 'ExcludeFromCollation' in tasks.columns else 10
if expected_tasks <= 0: expected_tasks = 10

# Segment stats
segment_stats = {}
for seg_path in sorted(SEGMENT_DIR.glob('*_segments.csv')):
    p = keyify(seg_path.name.replace('_segments.csv',''))
    try:
        sdf = pd.read_csv(seg_path)
        if len(sdf):
            end_max = pd.to_numeric(sdf['end_time'], errors='coerce').max() if 'end_time' in sdf.columns else np.nan
            text_words = sdf['text'].fillna('').map(count_words).sum() if 'text' in sdf.columns else 0
            segment_stats[p] = {
                'segment_file': seg_path.name,
                'segment_count': len(sdf),
                'segment_duration_minutes': float(end_max)/60 if pd.notna(end_max) else np.nan,
                'transcript_word_count': int(text_words)
            }
    except Exception:
        pass

# Open-ended columns
open_cols = []
for c in raw.columns:
    lc = c.lower().strip()
    if c in ['Timestamp','Please enter your email address']: continue
    if c in SCORE_COLS: continue
    if any(term in lc for term in INCLUDE_OPEN_COL_TERMS):
        open_cols.append(c)
    elif any(term in lc for term in EXCLUDE_OPEN_COL_TERMS):
        continue
open_cols = list(dict.fromkeys(open_cols))
number_of_open_answers = len(open_cols)

# Aggregates
p2_part = p2.groupby('participant_unified').agg(
    average_l3_after_proposal2_time=('l3_score_after_proposal2_time','mean'),
    average_l3_before_time=('l3_score_before_time','mean'),
    number_of_model_rows=('model_c_task','count'),
    matched_model_tasks=('model_c_task_key', lambda x: x.dropna().nunique()),
    p2_changed_rows=('proposal2_changed_score', lambda x: int((x.astype(str).str.lower()=='true').sum())),
    p2_strong_time_rows=('time_signal', lambda x: int((x.astype(str)=='strong_time_friction').sum())),
).reset_index()

time_part = time_df.groupby('participant_unified').agg(
    number_of_tasks_with_transcript_evidence=('task_id', lambda x: x.dropna().astype(str).nunique()),
    total_session_duration_minutes=('end_seconds', lambda x: pd.to_numeric(x, errors='coerce').max()/60),
    strong_time_friction_count=('time_signal', lambda x: int((x.astype(str)=='strong_time_friction').sum())),
    medium_time_friction_count=('time_signal', lambda x: int((x.astype(str)=='medium_time_friction').sum())),
    task_rows_with_time=('task_id','count')
).reset_index()

def weighted_severity(series):
    weights = {'low':1,'medium':2,'high':3,'severe':4,'blocker':5}
    return sum(weights.get(str(s).strip().lower(),0) for s in series.dropna())

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
    manual_valid['manual_abs_gap_after'] = (
        pd.to_numeric(manual_valid['l3_score_after_proposal2_time'], errors='coerce') -
        pd.to_numeric(manual_valid['manual_ground_truth_score'], errors='coerce')
    ).abs()
    man_part = manual_valid.groupby('participant_unified').agg(
        manual_review_case_count=('case_id','count'),
        manual_avg_abs_gap_after=('manual_abs_gap_after','mean'),
        manual_insufficient_count=('manual_label', lambda x: int((x.astype(str)=='insufficient_evidence').sum()))
    ).reset_index()
else:
    man_part = pd.DataFrame(columns=['participant_unified','manual_review_case_count','manual_avg_abs_gap_after','manual_insufficient_count'])

# ── Per-participant scoring ────────────────────────────────────────────────
feature_rows = []
score_rows   = []
unmatched_rows = []
weights_dict = {
    'feedback_depth_score': 0.35,
    'task_coverage_score': 0.25,
    'evidence_consistency_score': 0.25,
    'engagement_effort_score': 0.15,
}

for _, row in raw.iterrows():
    email       = row['email']
    participant = row['participant']
    primary_cohort = row['primary_cohort'] if pd.notna(row['primary_cohort']) else ''

    answer_texts = []
    for c in open_cols:
        v = row.get(c, np.nan)
        answer_texts.append(str(v) if pd.notna(v) else '')
    non_empty_answers = [a for a in answer_texts if a.strip()]
    word_counts = [count_words(a) for a in answer_texts]
    total_open_words = int(sum(word_counts))
    avg_open_words = float(np.mean([w for w,a in zip(word_counts,answer_texts) if a.strip()])) if non_empty_answers else 0.0
    vague_count = int(sum(is_vague(a) for a in answer_texts if a.strip()))
    full_open_text = '\n'.join(non_empty_answers)
    specific_terms_count = int(count_terms(full_open_text, SPECIFIC_TERMS))
    actionable_count = int(sum(1 for a in non_empty_answers if count_terms(a, ACTION_TERMS) > 0))
    survey_mentions_friction_count = int(count_terms(full_open_text, FRICTION_TERMS))
    open_completion_ratio = len(non_empty_answers)/number_of_open_answers if number_of_open_answers else np.nan

    raw_scores = []
    for c in SCORE_COLS:
        val = pd.to_numeric(row.get(c, np.nan), errors='coerce')
        if pd.notna(val): raw_scores.append(float(val)*20.0)
    avg_raw_score = float(np.mean(raw_scores)) if raw_scores else np.nan
    task_survey_count = int(sum(pd.notna(pd.to_numeric(row.get(c, np.nan), errors='coerce')) for c in TASK_SURVEY_SCORE_COLS))

    p2r = p2_part[p2_part['participant_unified']==participant]
    tr  = time_part[time_part['participant_unified']==participant]
    ir  = ins_part[ins_part['participant_unified']==participant]
    mr  = man_part[man_part['participant_unified']==participant]
    p2dict = p2r.iloc[0].to_dict() if len(p2r) else {}
    tdict  = tr.iloc[0].to_dict()  if len(tr)  else {}
    idict  = ir.iloc[0].to_dict()  if len(ir)  else {}
    mdict  = mr.iloc[0].to_dict()  if len(mr)  else {}
    sdict  = segment_stats.get(participant, {})

    n_transcript_tasks = tdict.get('number_of_tasks_with_transcript_evidence', np.nan)
    total_session_duration = tdict.get('total_session_duration_minutes', np.nan)
    if pd.isna(total_session_duration):
        total_session_duration = sdict.get('segment_duration_minutes', np.nan)

    candidates = [x for x in [
        n_transcript_tasks, task_survey_count,
        p2dict.get('matched_model_tasks', np.nan),
        idict.get('insight_task_coverage', np.nan)
    ] if not pd.isna(x)]
    number_of_tasks_attempted = float(np.nanmax(candidates)) if candidates else np.nan
    task_coverage_ratio = float(min(number_of_tasks_attempted/expected_tasks, 1.0)) if pd.notna(number_of_tasks_attempted) else np.nan
    avg_l3_after = p2dict.get('average_l3_after_proposal2_time', np.nan)
    avg_gap = float(avg_raw_score - avg_l3_after) if pd.notna(avg_raw_score) and pd.notna(avg_l3_after) else np.nan
    high_sev = int(idict.get('high_severe_blocker_insight_count', 0) or 0)
    friction_count = int(idict.get('friction_insight_count', 0) or 0)
    blocker_count = int(idict.get('blocker_insight_count', 0) or 0)
    high_score_with_high_friction_count = int(high_sev if pd.notna(avg_raw_score) and avg_raw_score >= 80 else 0)
    survey_completion_ratio = float(row.dropna().shape[0]/len(raw.columns))
    extremely_short_session_flag = bool(pd.notna(total_session_duration) and total_session_duration < 10)
    extremely_short_plus_no_feedback_flag = bool(extremely_short_session_flag and total_open_words < 80 and open_completion_ratio < 0.6)

    # Feedback depth
    depth  = 20
    depth += min(total_open_words/12.0, 35)
    depth += min(len(non_empty_answers)/max(number_of_open_answers,1)*20, 20)
    depth += min(specific_terms_count*1.2, 18)
    depth += min(actionable_count*2.5, 17)
    depth -= min(vague_count*4.0, 20)
    feedback_depth_score = clamp(depth)
    if total_open_words >= 650 and specific_terms_count >= 20 and actionable_count >= 6:
        fd_reason = f'Open-ended feedback is very detailed ({total_open_words} words), with {specific_terms_count} concrete issue/task terms and {actionable_count} actionable answers.'
    elif total_open_words >= 300 and specific_terms_count >= 8:
        fd_reason = f'Open-ended feedback is usable and reasonably specific ({total_open_words} words, {specific_terms_count} concrete terms), though not uniformly detailed across every answer.'
    elif total_open_words >= 120:
        fd_reason = f'Open-ended feedback has some usable detail ({total_open_words} words), but specificity/actionability is limited relative to stronger testers.'
    else:
        fd_reason = f'Open-ended feedback is short or sparse ({total_open_words} words), so depth is limited even if some answers are complete.'

    # Task coverage
    if pd.isna(task_coverage_ratio):
        task_coverage_score = np.nan
        tc_reason = 'No reliable task coverage evidence was available from task segmentation, transcript segments, Proposal 2, or survey task responses.'
    else:
        tc_base = 35 + 65*task_coverage_ratio
        has_external = (pd.notna(n_transcript_tasks) and n_transcript_tasks > 0) or idict.get('insight_task_coverage',0) > 0
        if not has_external: tc_base = min(tc_base, 72)
        if task_coverage_ratio < 0.5 and total_open_words >= 500: tc_base += 10
        task_coverage_score = clamp(tc_base)
        n_t = int(number_of_tasks_attempted) if pd.notna(number_of_tasks_attempted) else 'NA'
        n_tr = int(n_transcript_tasks) if pd.notna(n_transcript_tasks) else 'NA'
        tc_reason = f'Coverage estimate uses {n_t} attempted/evidenced tasks against {expected_tasks} expected non-excluded tasks; survey task score responses={task_survey_count}, transcript-evidenced tasks={n_tr}, insight task coverage={idict.get("insight_task_coverage",0)}.'

    # Evidence consistency
    evidence_missing = len(p2r)==0 and len(ir)==0 and len(mr)==0
    if evidence_missing:
        evidence_consistency_score = np.nan
        ec_reason = 'No Proposal 2/model rows, LLM insight rows, or manual-review cases were available, so consistency was not scored.'
    else:
        ec = 88
        if pd.notna(avg_gap):
            if avg_gap > 35:   ec -= 24
            elif avg_gap > 25: ec -= 16
            elif avg_gap > 15: ec -= 8
            elif avg_gap < -25: ec -= 6
        if high_score_with_high_friction_count >= 5:   ec -= 22
        elif high_score_with_high_friction_count >= 3: ec -= 14
        elif high_score_with_high_friction_count >= 1: ec -= 6
        if survey_mentions_friction_count >= 8:   ec += 16
        elif survey_mentions_friction_count >= 4: ec += 10
        elif survey_mentions_friction_count >= 2: ec += 5
        if total_open_words < 150 and high_sev >= 2 and pd.notna(avg_raw_score) and avg_raw_score >= 80:
            ec -= 18
        if blocker_count > 0 and survey_mentions_friction_count == 0 and pd.notna(avg_raw_score) and avg_raw_score >= 80:
            ec -= 18
        man_gap = mdict.get('manual_avg_abs_gap_after', np.nan)
        if pd.notna(man_gap):
            if man_gap > 30: ec -= 8
            elif man_gap <= 15: ec += 3
        evidence_consistency_score = clamp(ec)
        conflict_note = 'no large unexplained conflict' if evidence_consistency_score >= 75 else 'some survey/evidence tension requiring review'
        avg_l3_txt = 'NA' if pd.isna(avg_l3_after) else f'{float(avg_l3_after):.1f}'
        avg_gap_txt = 'NA' if pd.isna(avg_gap) else f'{avg_gap:.1f}'
        avg_raw_txt = 'NA' if pd.isna(avg_raw_score) else f'{avg_raw_score:.1f}'
        ec_reason = f'Average raw survey score={avg_raw_txt} and average Proposal 2 L3 score={avg_l3_txt}; score gap={avg_gap_txt}. LLM insight high/severe/blocker count={high_sev}, survey friction mentions={survey_mentions_friction_count}; {conflict_note}.'

    # Engagement
    engagement_missing = pd.isna(total_session_duration) and pd.isna(number_of_tasks_attempted)
    if engagement_missing:
        engagement_effort_score = np.nan
        ee_reason = 'No session duration or task-attempt evidence was available, so engagement/effort was not scored.'
    else:
        ee = 45
        ee += min((number_of_tasks_attempted if pd.notna(number_of_tasks_attempted) else 0)/expected_tasks*30, 30)
        ee += min(open_completion_ratio*15 if pd.notna(open_completion_ratio) else 0, 15)
        ee += 10 if survey_completion_ratio >= 0.9 else 5 if survey_completion_ratio >= 0.75 else 0
        if pd.notna(total_session_duration):
            if total_session_duration >= 45: ee += 5
            elif total_session_duration < 10: ee -= 18
            elif total_session_duration < 20: ee -= 6
        if extremely_short_plus_no_feedback_flag: ee -= 22
        if total_open_words >= 350 and (number_of_tasks_attempted if pd.notna(number_of_tasks_attempted) else 0) >= 5:
            ee += 5
        engagement_effort_score = clamp(ee)
        dur_txt = f'{float(total_session_duration):.1f}' if pd.notna(total_session_duration) else 'NA'
        n_t_txt = int(number_of_tasks_attempted) if pd.notna(number_of_tasks_attempted) else 'NA'
        ee_reason = (f'Engagement uses survey completion ratio={survey_completion_ratio:.2f}, '
                     f'open-answer completion={open_completion_ratio:.2f}, '
                     f'attempted/evidenced tasks={n_t_txt}, and session duration={dur_txt} minutes. '
                     f'Slow completion was not penalized; only very short sessions with little feedback are flagged.')

    dims = {
        'feedback_depth_score': feedback_depth_score,
        'task_coverage_score': task_coverage_score,
        'evidence_consistency_score': evidence_consistency_score,
        'engagement_effort_score': engagement_effort_score,
    }
    avail   = [k for k,v in dims.items() if pd.notna(v)]
    missing = [k for k,v in dims.items() if pd.isna(v)]
    if avail:
        denom = sum(weights_dict[k] for k in avail)
        total_score = round(clamp(sum(dims[k]*weights_dict[k] for k in avail)/denom), 2)
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

    fd_s  = f'{feedback_depth_score:.1f}' if pd.notna(feedback_depth_score) else 'NA'
    tc_s  = f'{task_coverage_score:.1f}' if pd.notna(task_coverage_score) else 'NA'
    ec_s  = f'{evidence_consistency_score:.1f}' if pd.notna(evidence_consistency_score) else 'NA'
    ee_s  = f'{engagement_effort_score:.1f}' if pd.notna(engagement_effort_score) else 'NA'
    overall_quality_reason = (
        f'Overall score combines available dimensions ({", ".join(avail)}) using the required weights '
        f'with renormalisation for missing dimensions. '
        f'Main drivers: feedback_depth={fd_s}, task_coverage={tc_s}, '
        f'evidence_consistency={ec_s}, engagement_effort={ee_s}. '
        f'Review flag: {review_flag}.'
    )

    feature_rows.append({
        'participant': participant, 'email': email,
        'total_open_text_word_count': total_open_words,
        'average_open_answer_word_count': round(avg_open_words,2),
        'number_of_open_answers': number_of_open_answers,
        'number_of_non_empty_open_answers': len(non_empty_answers),
        'open_answer_completion_ratio': round(open_completion_ratio,4) if pd.notna(open_completion_ratio) else np.nan,
        'vague_answer_count': vague_count,
        'specific_issue_terms_count': specific_terms_count,
        'actionable_feedback_count': actionable_count,
        'number_of_tasks_attempted': np.nan if pd.isna(number_of_tasks_attempted) else int(number_of_tasks_attempted),
        'number_of_tasks_with_survey_response': task_survey_count,
        'number_of_tasks_with_transcript_evidence': np.nan if pd.isna(n_transcript_tasks) else int(n_transcript_tasks),
        'task_coverage_ratio': np.nan if pd.isna(task_coverage_ratio) else round(task_coverage_ratio,4),
        'average_raw_survey_score': np.nan if pd.isna(avg_raw_score) else round(avg_raw_score,2),
        'average_l3_after_proposal2_time': np.nan if pd.isna(avg_l3_after) else round(float(avg_l3_after),2),
        'average_score_gap': np.nan if pd.isna(avg_gap) else round(avg_gap,2),
        'high_score_with_high_friction_count': high_score_with_high_friction_count,
        'total_session_duration_minutes': np.nan if pd.isna(total_session_duration) else round(float(total_session_duration),2),
        'extremely_short_session_flag': extremely_short_session_flag,
        'extremely_short_plus_no_feedback_flag': extremely_short_plus_no_feedback_flag,
        'survey_mentions_friction_count': survey_mentions_friction_count,
        'llm_friction_insight_count': friction_count,
        'llm_high_severe_blocker_insight_count': high_sev,
        'llm_blocker_insight_count': blocker_count,
        'proposal2_changed_rows': int(p2dict.get('p2_changed_rows',0) or 0),
        'segment_file': sdict.get('segment_file',''),
        'transcript_word_count': sdict.get('transcript_word_count', np.nan),
    })
    score_rows.append({
        'participant': participant, 'email': email, 'primary_cohort': primary_cohort,
        'tester_quality_score': total_score,
        'tester_quality_band': band,
        'feedback_depth_score': round(feedback_depth_score,2) if pd.notna(feedback_depth_score) else np.nan,
        'task_coverage_score': round(task_coverage_score,2) if pd.notna(task_coverage_score) else np.nan,
        'evidence_consistency_score': round(evidence_consistency_score,2) if pd.notna(evidence_consistency_score) else np.nan,
        'engagement_effort_score': round(engagement_effort_score,2) if pd.notna(engagement_effort_score) else np.nan,
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
            'participant': participant, 'email': email,
            'missing_area': 'external_evidence_mapping',
            'reason': 'Raw survey participant could not be matched to Proposal 2/model rows, LLM insights, or manual-review evidence.'
        })

features = pd.DataFrame(feature_rows).sort_values('participant')
scores   = pd.DataFrame(score_rows).sort_values('tester_quality_score', ascending=False, na_position='last')
unmatched = pd.DataFrame(unmatched_rows, columns=['participant','email','missing_area','reason'])

# Summary
summary_items = []
def add_metric(metric, value):
    summary_items.append({'metric': metric, 'value': value})

add_metric('number_of_testers', len(scores))
add_metric('average_tester_quality_score', round(scores['tester_quality_score'].dropna().mean(), 2))
add_metric('number_high_quality',           int((scores['tester_quality_band']=='high_quality').sum()))
add_metric('number_good_quality',           int((scores['tester_quality_band']=='good_quality').sum()))
add_metric('number_medium_quality',         int((scores['tester_quality_band']=='medium_quality').sum()))
add_metric('number_low_quality_review_needed', int((scores['tester_quality_band']=='low_quality_review_needed').sum()))
add_metric('number_insufficient_data',      int((scores['tester_quality_band']=='insufficient_data').sum()))
add_metric('number_with_missing_dimensions',int(scores['missing_dimensions'].fillna('').astype(str).str.len().gt(0).sum()))
add_metric('average_feedback_depth_score',  round(scores['feedback_depth_score'].dropna().mean(), 2))
add_metric('average_task_coverage_score',   round(scores['task_coverage_score'].dropna().mean(), 2))
add_metric('average_evidence_consistency_score', round(scores['evidence_consistency_score'].dropna().mean(), 2))
add_metric('average_engagement_effort_score', round(scores['engagement_effort_score'].dropna().mean(), 2))
add_metric('number_review_flag_no_review_needed', int((scores['review_flag']=='no_review_needed').sum()))
add_metric('number_review_flag_high_survey_model_conflict', int(scores['review_flag'].str.contains('high_survey_model_conflict').sum()))
add_metric('expected_non_excluded_tasks_used_for_coverage', expected_tasks)
add_metric('open_answer_columns_used', number_of_open_answers)
tq_summary = pd.DataFrame(summary_items)

# Save
scores.to_csv(TQ_OUT / 'tester_quality_scores.csv', index=False)
features.to_csv(TQ_OUT / 'tester_quality_features.csv', index=False)
tq_summary.to_csv(TQ_OUT / 'tester_quality_summary.csv', index=False)
unmatched.to_csv(TQ_OUT / 'unmatched_tester_quality_participants.csv', index=False)

print(f"tester_quality_scores.csv:   {len(scores)} rows")
print(f"tester_quality_features.csv: {len(features)} rows")
print(f"tester_quality_summary.csv:  {len(tq_summary)} metrics")
print(f"unmatched:                   {len(unmatched)} rows")
print()
print("Band distribution:")
print(scores['tester_quality_band'].value_counts().to_string())
print()
print("Review flags:")
print(scores['review_flag'].value_counts().to_string())
