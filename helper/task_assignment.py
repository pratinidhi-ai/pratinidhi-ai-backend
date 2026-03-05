"""
Task Assignment Helper
Generates weekly tasks for SAT prep with structured distribution across
Unexplored / Weak / Strength topics for Math and English, plus AI Tutor
and conditional SAT Score Predictor tasks.
"""

from datetime import datetime, date, timezone, timedelta, time
from typing import Optional, List, Dict, Any, Tuple
import random
import json
import os
import math
import uuid

from models.task_schema import Task, TaskType, TaskFrequency, Subject
from models.users_schema import User
from database.question_db import get_question_db

# ─────────────────────────────────────────────────────────────────────────────
# AREA DEFINITIONS  (exact names — do not rename)
# ─────────────────────────────────────────────────────────────────────────────

MATH_AREAS: List[Dict[str, str]] = [
    {
        "name": "Algebra",
        "sub_category": "algebra",
        "subcategory": "algebra",
        "facet": "math|algebra|11",
        "facet_doc": "math|algebra",
        "display": "Algebra Quiz",
    },
    {
        "name": "Advanced Math",
        "sub_category": "advanced-math",
        "subcategory": "advanced-math",
        "facet": "math|advanced-math|11",
        "facet_doc": "math|advanced-math",
        "display": "Advanced Math Quiz",
    },
    {
        "name": "Problem Solving & Data Analysis",
        "sub_category": "problem-solving-and-data-analysis",
        "subcategory": "problem-solving-data-analysis",
        "facet": "math|problem-solving-and-data-analysis|11",
        "facet_doc": "math|problem-solving-and-data-analysis",
        "display": "Problem Solving & Data Analysis Quiz",
    },
    {
        "name": "Geometry & Trigonometry",
        "sub_category": "geometry-trigonometry",
        "subcategory": "geometry-trigonometry",
        "facet": "math|geometry-trigonometry|11",
        "facet_doc": "math|geometry-trigonometry",
        "display": "Geometry & Trigonometry Quiz",
    },
]

ENGLISH_AREAS: List[Dict[str, str]] = [
    {
        "name": "Craft and Structure",
        "sub_category": "craft-and-structure",
        "subcategory": "craft-and-structure",
        "facet": "reading-and-writing|craft-and-structure|11",
        "facet_doc": "reading-and-writing|craft-and-structure",
        "display": "Craft and Structure Quiz",
    },
    {
        "name": "Expression of Ideas",
        "sub_category": "expression-of-ideas",
        "subcategory": "expression-of-ideas",
        "facet": "reading-and-writing|expression-of-ideas|11",
        "facet_doc": "reading-and-writing|expression-of-ideas",
        "display": "Expression of Ideas Quiz",
    },
    {
        "name": "Information and Ideas",
        "sub_category": "information-and-ideas",
        "subcategory": "information-and-ideas",
        "facet": "reading-and-writing|information-and-ideas|11",
        "facet_doc": "reading-and-writing|information-and-ideas",
        "display": "Information and Ideas Quiz",
    },
    {
        "name": "Standard English Conventions",
        "sub_category": "standard-english-conventions",
        "subcategory": "standard-english-conventions",
        "facet": "reading-and-writing|standard-english-conventions|11",
        "facet_doc": "reading-and-writing|standard-english-conventions",
        "display": "Standard English Conventions Quiz",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# TAG TAXONOMY  (mirrors analytics_routing.SUBJECT_TAG_TAXONOMY exactly)
# ─────────────────────────────────────────────────────────────────────────────

MATH_TAG_TAXONOMY: Dict[str, List[str]] = {
    "algebra": [
        "single-variable-linear-equations", "linear-inequalities", "slope-intercept",
        "graphing-linear-equations", "parallel-perpendicular-lines", "systems-of-equations",
        "systems-of-inequalities", "linear-word-problems", "system-word-problems",
        "literal-equations", "inequality-word-problems", "mixture-problems",
        "distance-rate-time", "direct-variation", "age-problems",
    ],
    "advanced-math": [
        "absolute-value-equations", "absolute-value-inequalities", "quadratic-equations",
        "factoring-polynomials", "expanding-polynomials", "rational-expressions",
        "rational-equations", "radical-equations", "radical-simplification",
        "exponent-properties", "exponential-equations", "exponential-models",
        "function-notation", "function-composition", "nonlinear-systems",
    ],
    "problem-solving-and-data-analysis": [
        "ratio-proportion", "unit-conversion", "percentage-calculation", "mean-median",
        "variability", "data-distributions", "scatterplots", "best-fit-line",
        "probability", "conditional-probability", "two-way-tables", "sampling-methods",
        "experimental-design", "margin-of-error", "statistical-inference",
    ],
    "geometry-trigonometry": [
        "area-volume", "lines-angles", "triangles", "right-triangles-trigonometry",
        "circles", "congruence-similarity", "coordinate-geometry", "arc-sector",
        "surface-area", "3d-shapes", "pythagorean-theorem", "special-triangles",
        "radian-degree-conversion", "unit-circle", "trig-identities",
    ],
}

ENGLISH_TAG_TAXONOMY: Dict[str, List[str]] = {
    "craft-and-structure": [
        "word-in-context", "phrase-in-context", "figurative-language", "word-choice-effect",
        "text-structure", "main-purpose", "author-tone", "author-attitude",
        "point-of-view", "sentence-function", "author-technique", "argument-structure",
        "cross-text-comparison", "cross-text-synthesis", "intended-audience",
    ],
    "expression-of-ideas": [
        "conciseness", "clarity", "precise-wording", "tone-consistency", "relevance",
        "supporting-evidence", "introduction-focus", "conclusion-summary", "logical-flow",
        "transitions", "sentence-combination", "paragraph-organization",
        "integrating-information", "active-voice", "formal-tone",
    ],
    "information-and-ideas": [
        "main-idea", "supporting-detail", "inference", "evidence-support",
        "data-interpretation", "graph-reading", "author-claim", "counterargument",
        "fact-opinion", "quantitative-reasoning", "analogy", "comparison",
        "cause-effect", "sequence-of-events", "summarizing",
    ],
    "standard-english-conventions": [
        "subject-verb-agreement", "pronoun-agreement", "verb-tense", "parallel-structure",
        "comma-usage", "semicolon-usage", "colon-usage", "apostrophe-usage",
        "modifier-placement", "sentence-boundaries", "word-choice-usage",
        "noun-agreement", "idiom-usage", "logical-comparisons", "redundancy",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# TASK DISTRIBUTION  (3 unexplored | 2 weakness | 1 strength)
# ─────────────────────────────────────────────────────────────────────────────

# Each tuple: (category_label, count).  Total must equal 6.
TASK_DISTRIBUTION: List[Tuple[str, int]] = [
    ("unexplored", 3),
    ("weakness",   2),
    ("strength",   1),
]

# Classification thresholds  (must match get_my_comprehensive_performance_analytics logic)
STRENGTH_THRESHOLD: float = 75.0   # accuracy >= 75% → strength
# unexplored threshold is dynamic: tags with attempts < 50% of mean are unexplored

NUM_QUIZ_TASKS_PER_SUBJECT: int = 6   # 6 Math + 6 English
NUM_AI_TUTOR_TASKS: int = 2
MOCK_TEST_SET_THRESHOLD: int = 3     # assign a mock test task after every Nth completed task set

# ─────────────────────────────────────────────────────────────────────────────
# DATE UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def get_week_start(date_input: Optional[datetime] = None) -> datetime:
    """Return Monday 00:00:00 UTC of the week containing date_input."""
    if date_input is None:
        current_dt = datetime.now(timezone.utc)
    elif isinstance(date_input, datetime):
        current_dt = date_input
    elif isinstance(date_input, date):
        current_dt = datetime.combine(date_input, time.min).replace(tzinfo=timezone.utc)
    else:
        current_dt = datetime.now(timezone.utc)

    days_since_monday = current_dt.weekday()
    monday_date = current_dt.date() - timedelta(days=days_since_monday)
    return datetime.combine(monday_date, time.min).replace(tzinfo=timezone.utc)


def get_days_left_in_week(dt: Optional[datetime] = None) -> int:
    """Return the number of days remaining in the current week (including today)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return max(1, 6 - dt.weekday() + 1)


def _ensure_datetime(dt: Optional[object]) -> datetime:
    """Return a timezone-aware UTC datetime from None / str / date / datetime."""
    if dt is None:
        return datetime.now(timezone.utc)
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            try:
                dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
            except Exception:
                return datetime.now(timezone.utc)
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)



# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_performance_summary(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the analytics performance_summary document for a user. Returns None on any error."""
    try:
        from database.analytics_db import get_analytics_db
        result = get_analytics_db().get_performance_summary(user_id)
        if result is None:
            print(f"[task_assignment] No performance summary found for user {user_id} — all topics will be treated as unexplored")
        return result
    except Exception as e:
        print(f"[task_assignment] ERROR fetching performance summary for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def _normalize_key(value: Optional[str]) -> str:
    """Normalize subject/subcategory/tag keys for resilient matching."""
    if not value:
        return ""
    return str(value).strip().lower().replace("_", "-").replace(" ", "-")


def _get_normalized_dict_entry(data: Dict[str, Any], target_key: str) -> Optional[Any]:
    """
    Return value from dict by exact key first, else by normalized-key match.
    Helps when stored analytics keys differ only by case/format.
    """
    if target_key in data:
        return data[target_key]

    normalized_target = _normalize_key(target_key)
    for k, v in data.items():
        if _normalize_key(k) == normalized_target:
            return v
    return None


def _classify_topics(
    sub_category: str,
    tag_taxonomy: List[str],
    summary: Optional[Dict[str, Any]],
    subject_key: str,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Partition tag_taxonomy tags into three lists using the same logic as
    POST /api/analytics/get-my-comprehensive-performance-analytics:

        unexplored: total_questions_attempted == 0  OR  < 50% of mean attempts
        strength:   accuracy >= STRENGTH_THRESHOLD (75%)  AND not unexplored
        weakness:   accuracy < STRENGTH_THRESHOLD (75%)   AND not unexplored

    All returned tags come strictly from tag_taxonomy.
    """
    unexplored: List[str] = []
    weakness: List[str] = []
    strength: List[str] = []

    # ── Build normalized tag map from stored analytics ────────────────────
    tag_data: Dict[str, Any] = {}
    if summary and "subjects" in summary:
        subjects = summary.get("subjects", {}) or {}
        subject_block = _get_normalized_dict_entry(subjects, subject_key) or {}
        sub_categories = subject_block.get("sub_categories", {}) if isinstance(subject_block, dict) else {}
        sub_category_block = _get_normalized_dict_entry(sub_categories, sub_category) or {}
        raw_tag_data = sub_category_block.get("tags", {}) if isinstance(sub_category_block, dict) else {}

        if isinstance(raw_tag_data, dict):
            for k, v in raw_tag_data.items():
                tag_data[_normalize_key(k)] = v

    # ── Calculate mean attempts (same as API: only over attempted tags) ───
    total_attempted_sum = 0
    attempted_count = 0
    for tag in tag_taxonomy:
        entry = tag_data.get(_normalize_key(tag))
        if entry:
            q = entry.get("total_questions_attempted", 0)
            total_attempted_sum += q
            if q > 0:
                attempted_count += 1

    mean_questions_attempted = total_attempted_sum / attempted_count if attempted_count > 0 else 0
    unexplored_threshold = mean_questions_attempted * 0.5

    # ── Classify each tag ─────────────────────────────────────────────────
    for tag in tag_taxonomy:
        normalized_tag = _normalize_key(tag)
        entry = tag_data.get(normalized_tag)

        if not entry:
            # Never attempted at all → unexplored
            unexplored.append(tag)
            continue

        attempted = entry.get("total_questions_attempted", 0)

        # Unexplored: zero attempts OR below 50% of mean
        if attempted == 0 or attempted < unexplored_threshold:
            unexplored.append(tag)
            continue

        # Compute accuracy reliably
        accuracy = entry.get("accuracy", 0.0)
        if accuracy == 0.0 and entry.get("total_correct_answers", 0) > 0 and attempted > 0:
            accuracy = round(entry["total_correct_answers"] / attempted * 100, 2)

        if accuracy >= STRENGTH_THRESHOLD:
            strength.append(tag)
        else:
            weakness.append(tag)

    return unexplored, weakness, strength


def _pick_tags_for_task(
    sub_category: str,
    tag_taxonomy: List[str],
    summary: Optional[Dict[str, Any]],
    subject_key: str,
    category: str,
    num_tags: int = 10,
) -> List[str]:
    """
    Select num_tags from the appropriate pool (unexplored / weak / strength).
    Falls back through available pools so the task always has tags.
    Only uses tags from the system-defined tag_taxonomy.
    """
    unexplored, weakness, strength = _classify_topics(
        sub_category, tag_taxonomy, summary, subject_key
    )

    if category == "unexplored":
        pools = [unexplored, weakness, strength]
    elif category in ("weakness", "weak"):
        pools = [weakness, unexplored, strength]
    else:  # "strength"
        pools = [strength, weakness, unexplored]

    combined: List[str] = []
    for pool in pools:
        needed = num_tags - len(combined)
        if needed <= 0:
            break
        combined.extend(random.sample(pool, min(needed, len(pool))))

    # Last resort: any tag not yet selected
    if len(combined) < num_tags:
        remaining = [t for t in tag_taxonomy if t not in combined]
        needed = num_tags - len(combined)
        combined.extend(random.sample(remaining, min(needed, len(remaining))))

    return combined[:num_tags]


# ─────────────────────────────────────────────────────────────────────────────
# QUIZ TASK CREATION
# ─────────────────────────────────────────────────────────────────────────────

def get_random_tags_for_facet(facet_doc: str, num_tags: int = 10) -> List[str]:
    """Fetch random available tags from the question bank. Falls back gracefully on error."""
    try:
        tags = get_question_db().get_random_tags_by_facets(facet_doc, num_tags)
        if tags:
            return tags
    except Exception:
        pass
    parts = facet_doc.split("|")
    base = parts[-1] if parts else "topic"
    return [f"{base}-topic-{i}" for i in range(1, num_tags + 1)]


def _pick_weekly_subcategory(
    areas: List[Dict[str, str]],
    tag_taxonomy: Dict[str, List[str]],
    summary: Optional[Dict[str, Any]],
    subject_key: str,
) -> Dict[str, str]:
    """
    Pick the ONE subcategory to focus on this week.
    Scores each: weakness_count*3 + unexplored_count*2 + strength_count*1.
    Returns the area dict with the highest score (ties broken randomly).
    """
    scored: List[Tuple[int, int, Dict[str, str]]] = []
    for idx, area in enumerate(areas):
        sub_cat = area["sub_category"]
        all_tags = tag_taxonomy.get(sub_cat, [])
        if not all_tags:
            scored.append((0, idx, area))
            continue
        unexplored, weakness, strength = _classify_topics(sub_cat, all_tags, summary, subject_key)
        score = len(weakness) * 3 + len(unexplored) * 2 + len(strength) * 1
        scored.append((score, idx, area))

    scored.sort(key=lambda x: x[0], reverse=True)
    # If top scores are tied, pick randomly among them
    top_score = scored[0][0]
    top_areas = [a for s, _, a in scored if s == top_score]
    return random.choice(top_areas)


def _select_topics_by_area(
    sub_category: str,
    tag_taxonomy: Dict[str, List[str]],
    summary: Optional[Dict[str, Any]],
    subject_key: str,
) -> List[Tuple[str, str]]:
    """
    Select exactly NUM_QUIZ_TASKS_PER_SUBJECT (6) topics from one subcategory.

    Distribution: 3 unexplored | 2 weakness | 1 strength
    Fallback order per bucket (same subcategory only):
        unexplored shortfall → refill from weakness, then strength
        weakness shortfall   → refill from unexplored, then strength
        strength shortfall   → refill from weakness, then unexplored

    Returns a list of (area_label, topic) tuples — length ≤ 6.
    All topics are distinct.
    """
    all_tags = tag_taxonomy.get(sub_category, [])
    if not all_tags:
        return []

    unexplored, weakness, strength = _classify_topics(sub_category, all_tags, summary, subject_key)

    # Shuffle each pool for random selection
    random.shuffle(unexplored)
    random.shuffle(weakness)
    random.shuffle(strength)

    fallback_order = {
        "unexplored": ["weakness", "strength"],
        "weakness":   ["unexplored", "strength"],
        "strength":   ["weakness", "unexplored"],
    }
    pools = {"unexplored": unexplored, "weakness": weakness, "strength": strength}

    selected: List[Tuple[str, str]] = []
    used: set = set()

    for area_label, count in TASK_DISTRIBUTION:
        picked = 0
        # Primary pool
        for topic in pools[area_label]:
            if picked >= count:
                break
            if topic not in used:
                selected.append((area_label, topic))
                used.add(topic)
                picked += 1
        # Fallback pools (same subcategory)
        if picked < count:
            for fallback in fallback_order[area_label]:
                for topic in pools[fallback]:
                    if picked >= count:
                        break
                    if topic not in used:
                        selected.append((fallback, topic))
                        used.add(topic)
                        picked += 1
                if picked >= count:
                    break

    return selected


def _create_subcategory_tasks(
    user_id: str,
    area: Dict[str, str],
    tag_taxonomy: Dict[str, List[str]],
    subject_enum: "Subject",
    subject_key: str,
    summary: Optional[Dict[str, Any]],
    base_task_number: int,
    week_start: datetime,
    week_end: datetime,
    current_due_date: datetime,
    days_per_task: float,
    task_offset: int,
) -> List[Task]:
    """
    Generate up to NUM_QUIZ_TASKS_PER_SUBJECT (6) quiz tasks for ONE subcategory.

    Each task covers exactly ONE topic (10 questions, all from that topic).
    quiz_related_attributes keys:
        subcategory – display-safe subcategory slug
        topic       – single topic string
        area        – "unexplored" | "weakness" | "strength"
        facet       – Firestore facet path
        tags        – [topic]  (kept for query compatibility)
        num_questions, difficulty_level, duration_minutes, passing_score
    """
    sub_cat = area["sub_category"]
    subcategory_out = area.get("subcategory", sub_cat)
    topic_area_pairs = _select_topics_by_area(sub_cat, tag_taxonomy, summary, subject_key)

    # Fallback: use random facet tags if classification returned nothing
    if not topic_area_pairs:
        fallback_tags = get_random_tags_for_facet(area["facet_doc"], NUM_QUIZ_TASKS_PER_SUBJECT)
        topic_area_pairs = [("unexplored", t) for t in fallback_tags]

    tasks: List[Task] = []
    task_number = base_task_number

    for pos_idx, (area_label, topic) in enumerate(topic_area_pairs):
        slot = task_offset + pos_idx
        due_date = current_due_date + timedelta(days=int(slot * days_per_task))
        due_date = min(due_date, week_end)

        description = (
            f"Complete a {area['display']} quiz on: "
            f"{topic.replace('-', ' ').title()} ({area_label})."
        )

        task = Task.create_quiz_task(
            title=area["display"],
            description=description,
            due_date=due_date,
            task_number=task_number,
            user_id=user_id,
            subject=subject_enum,
            facet=area["facet"],
            tags=[topic],
            num_questions=10,
            difficulty_level=3,
            duration_minutes=10,
            passing_score=70.0,
            start_date_of_week=week_start,
            subcategory=subcategory_out,
            topic=topic,
            area=area_label,
        )
        tasks.append(task)
        task_number += 1

    return tasks


# ─────────────────────────────────────────────────────────────────────────────
# AI TUTOR TASK CREATION
# ─────────────────────────────────────────────────────────────────────────────

def load_lecture_notes() -> Dict[str, Any]:
    """Load lecture notes from the config file."""
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "lecture_notes.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_ai_tutorial_task(
    user_id: str,
    chapter_id: str,
    task_number: int,
    due_date: datetime,
    week_start: datetime,
) -> Optional[Task]:
    """Create an AI tutorial task for the given chapter."""
    try:
        lecture_notes = load_lecture_notes()
        chapter_info = lecture_notes["SAT"]["chapters"].get(chapter_id)
        if not chapter_info:
            return None

        description = (
            f"Complete the AI tutorial for {chapter_info['title']}. "
            f"{chapter_info.get('summary', '')[:100]}..."
        )
        return Task.create_ai_tutorial_task(
            title=f"AI Tutorial: {chapter_info['title']}",
            description=description,
            due_date=due_date,
            task_number=task_number,
            user_id=user_id,
            chapter_id=chapter_id,
            chapter_title=chapter_info["title"],
            start_date_of_week=week_start,
            estimated_duration_minutes=30,
        )
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SAT PREDICTOR TASK CREATION
# ─────────────────────────────────────────────────────────────────────────────

def _get_total_quizzes(summary: Optional[Dict[str, Any]]) -> int:
    """Return total normal quizzes completed from the performance summary."""
    return summary.get("total_quizzes", 0) if summary else 0


def _get_next_mock_test(user_id: str) -> Optional[Dict[str, str]]:
    """
    Return the next mock test to assign — the first one the user hasn't attempted yet.
    Falls back to the first available mock test if all have been attempted.
    Returns a dict with 'id' and 'name', or None on any error.
    """
    try:
        from database.firebase_client import get_firestore_client
        db = get_firestore_client()
        if db is None:
            return None

        # Fetch all available mock tests (id + name only)
        mock_docs = list(
            db.collection("mock_tests")
            .select(["id", "name"])
            .order_by("created_at")
            .stream()
        )
        if not mock_docs:
            return None

        # Fetch IDs the user has already attempted
        attempted_ids = {
            doc.id
            for doc in db.collection("users").document(user_id)
            .collection("mock_attempts")
            .stream()
        }

        # Pick first unattempted; fallback to first mock
        unattempted = [d for d in mock_docs if d.id not in attempted_ids]
        chosen = unattempted[0] if unattempted else mock_docs[0]
        data = chosen.to_dict() or {}
        return {
            "id": chosen.id,
            "name": data.get("name") or chosen.id,
        }
    except Exception:
        return None


def _get_predictor_score(user: User) -> Optional[int]:
    """Return the user's last SAT predictor total score, or None if unavailable."""
    ps = getattr(user, "predicted_score", None)
    if ps is None:
        return None
    if hasattr(ps, "total_score"):
        score = ps.total_score
        return int(score) if score else None
    if isinstance(ps, int):
        return ps if ps > 0 else None
    return None


def _create_mock_test_task(
    user_id: str,
    mock_id: str,
    mock_name: str,
    task_number: int,
    due_date: datetime,
    week_start: datetime,
) -> Task:
    """Create a Mock Test task for the given mock test."""
    description = (
        f"Take the full-length mock test '{mock_name}' to simulate real SAT exam conditions "
        f"and track your overall progress."
    )
    return Task(
        id=str(uuid.uuid4()),
        title=f"Mock Test: {mock_name}",
        description=description,
        due_date=due_date,
        completed=False,
        type_of_task=TaskType.MOCK_TEST,
        created_at=datetime.now(timezone.utc),
        frequency=TaskFrequency.WEEKLY,
        task_number=task_number,
        user_id=user_id,
        subject=Subject.MATH,
        start_date_of_week=week_start,
        quiz_related_attributes={
            'mock_id': mock_id,
            'mock_name': mock_name,
            'duration_minutes': 70,
        },
        attempts_info={'attempts': 0, 'best_score': None, 'last_attempt': None},
    )


def _create_sat_predictor_task(
    user_id: str,
    task_number: int,
    due_date: datetime,
    week_start: datetime,
    existing_score: Optional[int],
) -> Task:
    """Create a SAT Score Predictor task."""
    if existing_score:
        description = (
            f"Your last predicted SAT score was {existing_score}. "
            "Take the predictor quiz again to track your progress."
        )
    else:
        description = (
            "Take the SAT Score Predictor quiz to get your estimated SAT score "
            "and personalise your preparation plan."
        )
    return Task.create_quiz_task(
        title="SAT Score Predictor",
        description=description,
        due_date=due_date,
        task_number=task_number,
        user_id=user_id,
        subject=Subject.MATH,
        facet="sat_predictor",
        tags=[],
        num_questions=24,
        difficulty_level=3,
        duration_minutes=15,
        passing_score=0.0,
        start_date_of_week=week_start,
        task_type_override=TaskType.SAT_PREDICTOR.value,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ASSIGNMENT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def assign_weekly_tasks(
    user: User,
    current_date: Optional[datetime] = None,
) -> List[Task]:
    """
    Assign tasks for a user for the current week.

    Stage 1 — SAT Predictor (sat_score_test_given is False):
        Returns a single SAT Predictor task. On completion, sat_score_test_given
        is set to True and this function is called again to produce Stage 2 tasks.

    Stage 2 — Full weekly tasks (sat_score_test_given is True):
        Math  (6 quiz tasks):    3 Unexplored | 2 Weak | 1 Strength
        English (6 quiz tasks):  3 Unexplored | 2 Weak | 1 Strength
        AI Tutor : exactly 2 tasks
        Mock Test: 1 task, added when total normal quizzes is a multiple of 7 (7, 14, 21, ...)
    """
    # ── Date setup ────────────────────────────────────────────────────────────
    current_date = _ensure_datetime(current_date)
    if getattr(user, "current_week_start", None) is not None:
        user.current_week_start = _ensure_datetime(user.current_week_start)

    week_start = get_week_start(current_date)
    week_end   = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    base_due   = current_date.replace(hour=23, minute=59, second=59, microsecond=0)
    user.current_week_start = week_start

    days_left = get_days_left_in_week(current_date)

    # Estimate total slots for even due-date spacing
    total_slots = NUM_QUIZ_TASKS_PER_SUBJECT * 2 + NUM_AI_TUTOR_TASKS + 1
    days_per_task: float = max(1.0, days_left / total_slots)

    # ── Stage 1: SAT Predictor (user has never taken it) ─────────────────────
    if not getattr(user, "sat_score_test_given", False):
        print("[assign] Stage 1: returning SAT Predictor task")
        predictor_due = min(base_due, week_end)
        return [_create_sat_predictor_task(
            user_id=user.id,
            task_number=1,
            due_date=predictor_due,
            week_start=week_start,
            existing_score=None,
        )]

    print("[assign] Stage 2: generating full task set")
    # ── Fetch analytics once ─────────────────────────────────────────────────
    summary = _fetch_performance_summary(user.id)

    all_tasks: List[Task] = []
    task_number = 1

    # ── Pick subcategories by rotation index ──────────────────────────────────
    math_idx = getattr(user, 'math_subcategory_index', 0) % len(MATH_AREAS)
    english_idx = getattr(user, 'english_subcategory_index', 0) % len(ENGLISH_AREAS)

    # ── Math quiz tasks (6) ───────────────────────────────────────────────────
    math_area = MATH_AREAS[math_idx]
    print(f"[assign] Math subcategory (index {math_idx}): {math_area.get('sub_category')}")
    math_tasks = _create_subcategory_tasks(
        user_id=user.id,
        area=math_area,
        tag_taxonomy=MATH_TAG_TAXONOMY,
        subject_enum=Subject.MATH,
        subject_key="math",
        summary=summary,
        base_task_number=task_number,
        week_start=week_start,
        week_end=week_end,
        current_due_date=base_due,
        days_per_task=days_per_task,
        task_offset=0,
    )
    print(f"[assign] Math tasks generated: {len(math_tasks)}")
    all_tasks.extend(math_tasks)
    task_number += len(math_tasks)

    # ── English quiz tasks (6) ────────────────────────────────────────────────
    english_area = ENGLISH_AREAS[english_idx]
    print(f"[assign] English subcategory (index {english_idx}): {english_area.get('sub_category')}")
    english_tasks = _create_subcategory_tasks(
        user_id=user.id,
        area=english_area,
        tag_taxonomy=ENGLISH_TAG_TAXONOMY,
        subject_enum=Subject.READING_WRITING,
        subject_key="reading-and-writing",
        summary=summary,
        base_task_number=task_number,
        week_start=week_start,
        week_end=week_end,
        current_due_date=base_due,
        days_per_task=days_per_task,
        task_offset=NUM_QUIZ_TASKS_PER_SUBJECT,
    )
    print(f"[assign] English tasks generated: {len(english_tasks)}")
    all_tasks.extend(english_tasks)
    task_number += len(english_tasks)

    # ── AI Tutor tasks (exactly 2) ────────────────────────────────────────────
    chapters_assigned: List[str] = []
    tutor_slot_start = NUM_QUIZ_TASKS_PER_SUBJECT * 2

    for i in range(NUM_AI_TUTOR_TASKS):
        next_chapter = user.get_next_chapter(already_selected_chapters=chapters_assigned)
        if not next_chapter:
            break
        chapters_assigned.append(next_chapter)

        due_date = base_due + timedelta(days=int((tutor_slot_start + i) * days_per_task))
        due_date = min(due_date, week_end)

        tutor_task = create_ai_tutorial_task(
            user_id=user.id,
            chapter_id=next_chapter,
            task_number=task_number,
            due_date=due_date,
            week_start=week_start,
        )
        if tutor_task:
            all_tasks.append(tutor_task)
            task_number += 1
    print(f"[assign] AI Tutor tasks generated: {sum(1 for t in all_tasks if t.type_of_task == TaskType.AI_TUTORIAL)}")

    # ── Mock Test task (every MOCK_TEST_SET_THRESHOLD completed task sets: 3, 6, 9 ...) ──
    completed_sets = getattr(user, 'completed_task_sets', 0)
    if completed_sets > 0 and completed_sets % MOCK_TEST_SET_THRESHOLD == 0:
        mock_info = _get_next_mock_test(user.id)
        if mock_info:
            mock_slot = tutor_slot_start + NUM_AI_TUTOR_TASKS + 1
            mock_due  = base_due + timedelta(days=int(mock_slot * days_per_task))
            mock_due  = min(mock_due, week_end)

            mock_task = _create_mock_test_task(
                user_id=user.id,
                mock_id=mock_info["id"],
                mock_name=mock_info["name"],
                task_number=task_number,
                due_date=mock_due,
                week_start=week_start,
            )
            all_tasks.append(mock_task)

    return all_tasks


# ─────────────────────────────────────────────────────────────────────────────
# ELIGIBILITY CHECK
# ─────────────────────────────────────────────────────────────────────────────

def should_assign_new_tasks(
    user: User,
    current_date: Optional[datetime] = None,
    has_incomplete_tasks: bool = False,
) -> bool:
    """
    Return True if new tasks should be assigned.

    Stage 1 (SAT Predictor not yet taken): always True.
    Stage 2: only when the caller confirms there are no incomplete tasks left
             (has_incomplete_tasks=False).  New sets are triggered by task
             completion, not by the calendar.
    """
    # Stage 1: predictor not yet taken — always need the predictor task
    if not getattr(user, "sat_score_test_given", False):
        return True

    # Stage 2: assign only when all current tasks are done
    return not has_incomplete_tasks


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY & ANALYTICS UTILITIES  (unchanged API — used by task_service.py)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_task_priority(
    task: Task,
    current_date: Optional[datetime] = None,
) -> int:
    """
    Calculate a priority score for sorting (lower = higher priority).
    Overdue tasks surface to the top; completed tasks sink to the bottom.
    """
    if current_date is None:
        current_date = datetime.now(timezone.utc)

    priority_score = 0

    if task.due_date:
        days_until_due = (task.due_date.date() - current_date.date()).days
        priority_score += max(0, days_until_due) * 10

    priority_score += task.task_number

    if task.completed:
        priority_score += 1000

    if task.is_overdue():
        priority_score = -1000 + task.task_number

    return priority_score


def get_current_week_tasks_query_filter(
    user_id: str,
    current_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return a Firestore query filter dict for the current week's tasks."""
    if current_date is None:
        current_date = datetime.now(timezone.utc)

    week_start = get_week_start(current_date)
    week_end   = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return {
        "user_id": user_id,
        "start_date_of_week": week_start.isoformat(),
        "due_date_range": {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
    }


def get_or_assign_user_tasks(
    user: User,
    firestore_client=None,
) -> List[Task]:
    """
    Get current tasks for a user or assign new ones if needed.
    (Thin wrapper kept for backward compatibility.)
    """
    if should_assign_new_tasks(user):
        new_tasks = assign_weekly_tasks(user)
        if firestore_client:
            pass  # caller is responsible for persisting
        return new_tasks
    return []


def get_user_task_analytics(tasks: List[Task]) -> Dict[str, Any]:
    """Generate high-level analytics for a user's task list."""
    if not tasks:
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "overdue_tasks": 0,
            "completion_rate": 0.0,
            "quiz_tasks": 0,
            "tutorial_tasks": 0,
        }

    total_tasks     = len(tasks)
    completed_tasks = len([t for t in tasks if t.completed])
    pending_tasks   = total_tasks - completed_tasks
    overdue_tasks   = len([t for t in tasks if t.is_overdue()])
    quiz_tasks      = len([t for t in tasks if t.type_of_task == TaskType.QUIZ])
    tutorial_tasks  = len([t for t in tasks if t.type_of_task == TaskType.AI_TUTORIAL])
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks else 0.0

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": round(completion_rate, 2),
        "quiz_tasks": quiz_tasks,
        "tutorial_tasks": tutorial_tasks,
    }
