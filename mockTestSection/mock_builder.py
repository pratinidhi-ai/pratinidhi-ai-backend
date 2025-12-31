# mockTestSection/mock_builder.py
import random
import datetime
from typing import Dict, Optional

from mockTestSection.sat_blueprint import SAT_BLUEPRINT
from mockTestSection.mock_selector import build_module_docs
from mockTestSection.mock_store import create_mock_parent, save_module_questions


def build_and_store_one_mock(
    name: str,
    seed: Optional[int] = None,
    filters: Optional[Dict] = None,
) -> str:
    """
    Build one mock using the SAT blueprint, fetch FULL question docs (incl. answers),
    and store them under a single parent document with 6 subcollections.
    Returns the parent mock_id (same as the mock name).
    """
    rng = random.Random(seed)
    filters = filters or {}
    theme = filters.get("theme")
    tags = filters.get("tags")
    tag = filters.get("tag")

    bp = SAT_BLUEPRINT

    # 1️⃣ Create parent document with 'name' as ID
    mock_id = name  # doc name = mock name

    create_mock_parent(
        mock_id=mock_id,
        exam="SAT",
        name=name,  # Explicitly pass name for display
    )

    # 2️⃣ Build all 6 modules
    rw_m1 = build_module_docs(bp["rw"]["module1_balanced"], rng, theme, tags, tag)
    rw_m2_e = build_module_docs(bp["rw"]["module2_easy"], rng, theme, tags, tag)
    rw_m2_h = build_module_docs(bp["rw"]["module2_hard"], rng, theme, tags, tag)
    math_m1 = build_module_docs(bp["math"]["module1_balanced"], rng, theme, tags, tag)
    math_m2_e = build_module_docs(bp["math"]["module2_easy"], rng, theme, tags, tag)
    math_m2_h = build_module_docs(bp["math"]["module2_hard"], rng, theme, tags, tag)

    # 3️⃣ Save all modules
    save_module_questions(mock_id, "rw", "module1_balanced", rw_m1)
    save_module_questions(mock_id, "rw", "module2_easy", rw_m2_e)
    save_module_questions(mock_id, "rw", "module2_hard", rw_m2_h)

    save_module_questions(mock_id, "math", "module1_balanced", math_m1)
    save_module_questions(mock_id, "math", "module2_easy", math_m2_e)
    save_module_questions(mock_id, "math", "module2_hard", math_m2_h)

    return mock_id
