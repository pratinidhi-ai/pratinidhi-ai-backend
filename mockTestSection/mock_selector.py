# mockTestSection/mock_selector.py
import random
from typing import Dict, List, Tuple, Optional
from google.cloud.firestore_v1.base_query import FieldFilter
from database.firebase_client import get_firestore_client


# Image question sub-categories mapping
# Maps (subject, sub_category) to list of image sub_categories available
IMAGE_QUESTION_SUBCATEGORIES = {
    ("math", "advanced-math"): ["data_analytics", "inequality", "statistics"],
    ("math", "algebra"): ["data_analytics", "inequality", "statistics"],
    ("math", "problem-solving-and-data-analysis"): ["data_analytics", "statistics", "table"],
    ("math", "geometry-and-trigonometry"): ["data_analytics", "inequality", "statistics"],
}

# Image question percentage range for math modules (20-30%)
IMAGE_QUESTION_MIN_PERCENT = 0.20
IMAGE_QUESTION_MAX_PERCENT = 0.30


def _round_counts(total: int, mix: Dict[int, float]) -> Dict[int, int]:
    raw = {k: int(round(total * v)) for k, v in mix.items()}
    delta = total - sum(raw.values())
    order = sorted(mix.keys(), key=lambda d: (-mix[d], d))
    i = 0
    while delta:
        k = order[i % len(order)]
        raw[k] += 1 if delta > 0 else -1
        delta += -1 if delta > 0 else 1
        i += 1
    return raw

def _fetch_question_docs_base(db, subject: str, sub_category: str, difficulty: int, n: int,
                               theme=None, tags=None, tag=None, seen_ids=None) -> List[Dict]:
    """
    Base function to fetch question docs from question_bank with optional filters.
    
    Args:
        seen_ids: Set of question IDs to exclude (to avoid duplicates when doing fallback)
    """
    if n <= 0:
        return []
    
    seen_ids = seen_ids or set()

    doc_path = f"{subject}|{sub_category}"
    ref = (db.collection('question_bank')
             .document(doc_path)
             .collection('difficulty_levels')
             .document(str(difficulty))
             .collection('questions'))

    if theme:
        ref = ref.where(filter=FieldFilter('theme', '==', theme))
    if tags and isinstance(tags, list) and len(tags) > 0:
        ref = ref.where(filter=FieldFilter('tags', 'array_contains_any', tags[:10]))
    elif tag:
        ref = ref.where(filter=FieldFilter('tags', 'array_contains', tag))

    rand_value = random.random()
    out: List[Dict] = []

    # pass 1
    q1 = (ref.where(filter=FieldFilter('random_value', '>=', rand_value))
             .order_by('random_value')
             .limit(n + len(seen_ids)))  # Fetch extra to account for exclusions
    docs1 = list(q1.stream())
    for d in docs1:
        if d.id not in seen_ids:
            obj = d.to_dict() or {}
            obj['id'] = d.id
            obj['is_image_question'] = False  # Mark as regular question
            out.append(obj)
            if len(out) >= n:
                break

    # pass 2 if needed
    if len(out) < n:
        remaining = n - len(out)
        q2 = (ref.where(filter=FieldFilter('random_value', '<', rand_value))
                .order_by('random_value')
                .limit(remaining + len(seen_ids)))
        docs2 = list(q2.stream())
        for d in docs2:
            if d.id not in seen_ids:
                obj = d.to_dict() or {}
                obj['id'] = d.id
                obj['is_image_question'] = False  # Mark as regular question
                out.append(obj)
                if len(out) >= n:
                    break

    random.shuffle(out)
    return out[:n]


def _fetch_question_docs(db, subject: str, sub_category: str, difficulty: int, n: int,
                         theme=None, tags=None, tag=None) -> List[Dict]:
    """
    Fetch full question docs (incl. answer/options/etc.) from question_bank.
    
    If a theme is provided, first tries to fetch themed questions, then fills
    the remaining slots with regular (non-themed) questions.
    """
    if n <= 0:
        return []

    out: List[Dict] = []
    seen_ids: set = set()
    
    # Step 1: If theme is provided, first try to get themed questions
    if theme:
        themed_docs = _fetch_question_docs_base(db, subject, sub_category, difficulty, n,
                                                 theme=theme, tags=tags, tag=tag, seen_ids=seen_ids)
        for d in themed_docs:
            out.append(d)
            seen_ids.add(d['id'])
        
        if len(out) < n:
            print(f"📚 Theme '{theme}': got {len(out)}/{n} questions for {subject}|{sub_category} (diff={difficulty}), filling rest with regular")
    
    # Step 2: Fill remaining slots with regular questions (no theme filter)
    remaining = n - len(out)
    if remaining > 0:
        regular_docs = _fetch_question_docs_base(db, subject, sub_category, difficulty, remaining,
                                                  theme=None, tags=tags, tag=tag, seen_ids=seen_ids)
        out.extend(regular_docs)
    
    random.shuffle(out)
    return out[:n]


def _fetch_image_question_docs_base(db, subject: str, sub_category: str, difficulty: int, n: int,
                                     theme=None, tags=None, tag=None, seen_ids=None) -> List[Dict]:
    """
    Base function to fetch question docs from image_question_bank with optional filters.
    
    Image questions have an additional sub_category level:
    image_question_bank/{subject}|{sub_category}|{image_sub_category}/difficulty_levels/{difficulty}/questions
    
    Args:
        seen_ids: Set of question IDs to exclude (to avoid duplicates when doing fallback)
    """
    if n <= 0:
        return []
    
    seen_ids = seen_ids or set()

    # Check if this subject|sub_category has image questions
    key = (subject, sub_category)
    if key not in IMAGE_QUESTION_SUBCATEGORIES:
        return []

    image_sub_categories = IMAGE_QUESTION_SUBCATEGORIES[key]
    out: List[Dict] = []

    # Distribute n across all image sub-categories randomly
    random.shuffle(image_sub_categories)
    
    for img_sub_cat in image_sub_categories:
        if len(out) >= n:
            break
            
        remaining_needed = n - len(out)
        doc_path = f"{subject}|{sub_category}|{img_sub_cat}"
        
        ref = (db.collection('image_question_bank')
                 .document(doc_path)
                 .collection('difficulty_levels')
                 .document(str(difficulty))
                 .collection('questions'))

        if theme:
            ref = ref.where(filter=FieldFilter('theme', '==', theme))
        if tags and isinstance(tags, list) and len(tags) > 0:
            ref = ref.where(filter=FieldFilter('tags', 'array_contains_any', tags[:10]))
        elif tag:
            ref = ref.where(filter=FieldFilter('tags', 'array_contains', tag))

        rand_value = random.random()

        # pass 1
        q1 = (ref.where(filter=FieldFilter('random_value', '>=', rand_value))
                 .order_by('random_value')
                 .limit(remaining_needed + len(seen_ids)))
        docs1 = list(q1.stream())
        for d in docs1:
            if d.id not in seen_ids:
                obj = d.to_dict() or {}
                obj['id'] = d.id
                obj['is_image_question'] = True  # Mark as image question
                obj['image_sub_category'] = img_sub_cat
                out.append(obj)
                if len(out) >= n:
                    break

        # pass 2 if needed
        if len(out) < n:
            still_needed = n - len(out)
            q2 = (ref.where(filter=FieldFilter('random_value', '<', rand_value))
                    .order_by('random_value')
                    .limit(still_needed + len(seen_ids)))
            docs2 = list(q2.stream())
            for d in docs2:
                if d.id not in seen_ids:
                    obj = d.to_dict() or {}
                    obj['id'] = d.id
                    obj['is_image_question'] = True  # Mark as image question
                    obj['image_sub_category'] = img_sub_cat
                    out.append(obj)
                    if len(out) >= n:
                        break

    random.shuffle(out)
    return out[:n]


def _fetch_image_question_docs(db, subject: str, sub_category: str, difficulty: int, n: int,
                                theme=None, tags=None, tag=None) -> List[Dict]:
    """
    Fetch full question docs from image_question_bank.
    
    If a theme is provided, first tries to fetch themed image questions, then fills
    the remaining slots with regular (non-themed) image questions.
    """
    if n <= 0:
        return []

    out: List[Dict] = []
    seen_ids: set = set()
    
    # Step 1: If theme is provided, first try to get themed image questions
    if theme:
        themed_docs = _fetch_image_question_docs_base(db, subject, sub_category, difficulty, n,
                                                       theme=theme, tags=tags, tag=tag, seen_ids=seen_ids)
        for d in themed_docs:
            out.append(d)
            seen_ids.add(d['id'])
        
        if len(out) < n:
            print(f"🖼️ Theme '{theme}': got {len(out)}/{n} image questions for {subject}|{sub_category} (diff={difficulty}), filling rest with regular")
    
    # Step 2: Fill remaining slots with regular image questions (no theme filter)
    remaining = n - len(out)
    if remaining > 0:
        regular_docs = _fetch_image_question_docs_base(db, subject, sub_category, difficulty, remaining,
                                                        theme=None, tags=tags, tag=tag, seen_ids=seen_ids)
        out.extend(regular_docs)
    
    random.shuffle(out)
    return out[:n]


def _fetch_mixed_question_docs(db, subject: str, sub_category: str, difficulty: int, n: int,
                                image_probability: float, theme=None, tags=None, tag=None) -> List[Dict]:
    """
    Fetch questions from both question_bank and image_question_bank based on image_probability.
    
    Args:
        db: Firestore client
        subject: Subject (e.g., 'math')
        sub_category: Sub-category (e.g., 'algebra')
        difficulty: Difficulty level (1-5)
        n: Number of questions needed
        image_probability: Probability of fetching an image question (0.0 to 1.0)
        theme, tags, tag: Optional filters
        
    Returns:
        List of question dicts, mixed from both question banks
    """
    if n <= 0:
        return []

    # Only math questions have image questions
    if subject != "math":
        return _fetch_question_docs(db, subject, sub_category, difficulty, n, theme, tags, tag)

    # Calculate how many image questions to fetch (based on probability)
    image_count = sum(1 for _ in range(n) if random.random() < image_probability)
    regular_count = n - image_count

    out: List[Dict] = []

    # Fetch image questions first
    if image_count > 0:
        image_docs = _fetch_image_question_docs(db, subject, sub_category, difficulty, image_count, theme, tags, tag)
        out.extend(image_docs)

    # Fetch regular questions
    if regular_count > 0:
        regular_docs = _fetch_question_docs(db, subject, sub_category, difficulty, regular_count, theme, tags, tag)
        out.extend(regular_docs)

    # If we didn't get enough image questions, fill with regular questions
    if len(out) < n:
        shortfall = n - len(out)
        extra_regular = _fetch_question_docs(db, subject, sub_category, difficulty, shortfall, theme, tags, tag)
        out.extend(extra_regular)

    random.shuffle(out)
    return out[:n]

# mockTestSection/mock_selector.py

def build_module_docs(module_cfg: Dict, rng: random.Random,
                      theme=None, tags=None, tag=None,
                      check_similarity: bool = False,
                      existing_questions: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Return a list of full question docs for the module (not IDs),
    ensuring we always hit the target total.
    
    For math modules, includes 20-30% image questions from image_question_bank.
    
    Args:
        module_cfg: Module configuration from SAT_BLUEPRINT
        rng: Random number generator for reproducibility
        theme: Optional theme filter
        tags: Optional tags filter
        tag: Optional single tag filter
        check_similarity: If True, use LLM to check for similar questions
        existing_questions: Questions already in the paper (for cross-module similarity check)
    """
    db = get_firestore_client()
    if db is None:
        raise RuntimeError("Firestore client not initialized")

    # Import similarity checker only if needed (to avoid circular imports)
    if check_similarity:
        from mockTestSection.similarity_checker import check_question_similarity

    total = module_cfg["total"]
    topics = module_cfg["topics"]
    per_diff = _round_counts(total, module_cfg["difficulty_mix"])

    # Determine if this is a math module (for image question mixing)
    is_math_module = any(topic.startswith("math|") for topic in topics)
    
    # Generate random image question probability for this module (20-30%)
    image_probability = 0.0
    if is_math_module:
        image_probability = rng.uniform(IMAGE_QUESTION_MIN_PERCENT, IMAGE_QUESTION_MAX_PERCENT)
        print(f"📊 Math module: targeting {image_probability*100:.1f}% image questions")

    picked: List[Dict] = []
    seen_ids = set()
    
    # Initialize similarity context with existing questions from other modules
    similarity_context: List[Dict] = list(existing_questions) if existing_questions else []

    # Helper function to add question with optional similarity check
    def _try_add_question(q: Dict) -> bool:
        """Try to add a question, checking for similarity if enabled. Returns True if added."""
        qid = q.get("id")
        if not qid or qid in seen_ids:
            return False
        
        # Check for similarity if enabled
        if check_similarity and (picked or similarity_context):
            all_existing = similarity_context + picked
            is_similar, reason = check_question_similarity(q, all_existing)
            if is_similar:
                print(f"🚫 Skipping similar question ({qid}): {reason}")
                return False
        
        picked.append(q)
        seen_ids.add(qid)
        return True

    # Get topic mix (sub-category distribution) if specified
    topic_mix = module_cfg.get("topic_mix")
    
    # pass 1 — try to fetch by difficulty/topic
    for diff, cnt in per_diff.items():
        # Calculate how many questions needed per topic based on topic_mix or equal distribution
        if topic_mix:
            # Use explicit topic distribution
            for topic in topics:
                need = round(cnt * topic_mix.get(topic, 1.0 / len(topics)))
                subject, sub = topic.split("|", 1)
                
                # Use mixed fetch for math, regular fetch for RW
                if is_math_module:
                    docs = _fetch_mixed_question_docs(db, subject, sub, diff, need, 
                                                       image_probability, theme=theme, tags=tags, tag=tag)
                else:
                    docs = _fetch_question_docs(db, subject, sub, diff, need, theme=theme, tags=tags, tag=tag)
                
                for d in docs:
                    _try_add_question(d)
        else:
            # Use equal distribution (legacy behavior)
            per_topic = cnt // len(topics)
            rem       = cnt %  len(topics)
            for i, topic in enumerate(topics):
                need = per_topic + (1 if i < rem else 0)
                subject, sub = topic.split("|", 1)
                
                # Use mixed fetch for math, regular fetch for RW
                if is_math_module:
                    docs = _fetch_mixed_question_docs(db, subject, sub, diff, need, 
                                                       image_probability, theme=theme, tags=tags, tag=tag)
                else:
                    docs = _fetch_question_docs(db, subject, sub, diff, need, theme=theme, tags=tags, tag=tag)
                
                for d in docs:
                    _try_add_question(d)

    # fallback — if we still don't have enough, pull from broader pools
    missing = total - len(picked)
    if missing > 0:
        print(f"⚠️ Only got {len(picked)} / {total} → fetching {missing} fallback questions.")
        # Try same section any topic, all difficulties
        section = topics[0].split("|", 1)[0]
        all_topics = [t.split("|", 1)[1] for t in topics]
        all_diffs = list(per_diff.keys())
        tries = 0
        while missing > 0 and tries < 5:
            # pick random (topic,diff)
            topic = rng.choice(all_topics)
            diff = rng.choice(all_diffs)
            
            # Use mixed fetch for math fallback as well
            if is_math_module:
                extra = _fetch_mixed_question_docs(db, section, topic, diff, missing,
                                                    image_probability, theme=theme, tags=tags, tag=tag)
            else:
                extra = _fetch_question_docs(db, section, topic, diff, missing, theme=theme, tags=tags, tag=tag)
            
            for d in extra:
                if _try_add_question(d):
                    missing -= 1
                    if missing <= 0:
                        break
            tries += 1

    # Log image question stats for math modules
    if is_math_module:
        image_count = sum(1 for q in picked if q.get("is_image_question", False))
        print(f"📈 Math module result: {image_count}/{len(picked)} image questions ({image_count/len(picked)*100:.1f}%)")

    rng.shuffle(picked)
    if len(picked) > total:
        picked = picked[:total]
    return picked
