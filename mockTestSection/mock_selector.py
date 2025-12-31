# mockTestSection/mock_selector.py
import random
from typing import Dict, List, Tuple
from google.cloud.firestore_v1.base_query import FieldFilter
from database.firebase_client import get_firestore_client

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

def _fetch_question_docs(db, subject: str, sub_category: str, difficulty: int, n: int,
                         theme=None, tags=None, tag=None) -> List[Dict]:
    """Fetch full question docs (incl. answer/options/etc.)."""
    if n <= 0:
        return []

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
             .limit(n))
    docs1 = list(q1.stream())
    for d in docs1:
        obj = d.to_dict() or {}
        obj['id'] = d.id
        out.append(obj)

    # pass 2 if needed
    if len(out) < n:
        remaining = n - len(out)
        q2 = (ref.where(filter=FieldFilter('random_value', '<', rand_value))
                .order_by('random_value')
                .limit(remaining))
        docs2 = list(q2.stream())
        for d in docs2:
            obj = d.to_dict() or {}
            obj['id'] = d.id
            out.append(obj)

    random.shuffle(out)
    return out[:n]

# mockTestSection/mock_selector.py

def build_module_docs(module_cfg: Dict, rng: random.Random,
                      theme=None, tags=None, tag=None) -> List[Dict]:
    """
    Return a list of full question docs for the module (not IDs),
    ensuring we always hit the target total.
    """
    db = get_firestore_client()
    if db is None:
        raise RuntimeError("Firestore client not initialized")

    total = module_cfg["total"]
    topics = module_cfg["topics"]
    per_diff = _round_counts(total, module_cfg["difficulty_mix"])

    picked: List[Dict] = []
    seen_ids = set()

    # pass 1 — try to fetch by difficulty/topic
    for diff, cnt in per_diff.items():
        per_topic = cnt // len(topics)
        rem       = cnt %  len(topics)
        for i, topic in enumerate(topics):
            need = per_topic + (1 if i < rem else 0)
            subject, sub = topic.split("|", 1)
            docs = _fetch_question_docs(db, subject, sub, diff, need, theme=theme, tags=tags, tag=tag)
            for d in docs:
                qid = d.get("id")
                if qid and qid not in seen_ids:
                    picked.append(d)
                    seen_ids.add(qid)

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
            extra = _fetch_question_docs(db, section, topic, diff, missing, theme=theme, tags=tags, tag=tag)
            for d in extra:
                qid = d.get("id")
                if qid and qid not in seen_ids:
                    picked.append(d)
                    seen_ids.add(qid)
                    missing -= 1
                    if missing <= 0:
                        break
            tries += 1

    rng.shuffle(picked)
    if len(picked) > total:
        picked = picked[:total]
    return picked
