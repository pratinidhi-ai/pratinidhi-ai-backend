# mockTestSection/run_build_nested_mock.py
import time
import argparse
from dotenv import load_dotenv
from mockTestSection.mock_builder import build_and_store_one_mock
from database.firebase_client import get_firestore_client


def get_next_mock_name(prefix="SATMock", theme=None):
    """
    Automatically finds the next mock name by counting existing mocks
    in Firestore and returning 'SATMockX' or 'SATMock_Theme_X' where X = next number.
    
    Args:
        prefix: Base prefix for mock name (default: "SATMock")
        theme: Optional theme to include in the name (e.g., "Science", "History")
        
    Returns:
        str: Next mock name like "SATMock1" or "SATMock_Science_1"
    """
    db = get_firestore_client()
    coll = db.collection("mock_tests")
    docs = list(coll.stream())

    # Build the full prefix including theme if provided
    if theme:
        # Capitalize theme and replace spaces with underscores for clean naming
        clean_theme = theme.strip().title().replace(" ", "_")
        full_prefix = f"{prefix}_{clean_theme}"
    else:
        full_prefix = prefix

    # Count how many mocks already exist with the given prefix
    count = sum(1 for d in docs if d.id.startswith(full_prefix) or d.to_dict().get("name", "").startswith(full_prefix))
    next_num = count + 1

    return f"{full_prefix}_{next_num}"


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Build and store a new SAT mock test")
    parser.add_argument(
        "--theme", "-t",
        type=str,
        default=None,
        help="Theme for the mock test (e.g., 'Science', 'History', 'Literature'). "
             "Questions matching this theme will be prioritized."
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducible question selection"
    )
    parser.add_argument(
        "--check-similarity", "-c",
        action="store_true",
        help="Enable LLM-based similarity checking to avoid duplicate/similar questions. "
             "This makes the process slower but ensures no two questions are too similar."
    )
    args = parser.parse_args()
    
    # Get theme from args
    theme = args.theme
    
    # Generate mock name (includes theme if provided)
    mock_name = get_next_mock_name("SAT_Practice_Test", theme=theme)
    
    print(f"🧩 Creating new mock: {mock_name}")
    if theme:
        print(f"🎨 Theme: {theme}")
    if args.check_similarity:
        print(f"🔍 Similarity checking: ENABLED")
    
    # Build filters dict with theme if provided
    filters = {}
    if theme:
        filters["theme"] = theme
    
    mock_id = build_and_store_one_mock(
        name=mock_name,
        seed=args.seed,
        filters=filters,
        check_similarity=args.check_similarity,
    )

    print("✅ Created mock:", mock_id)
    print(f"⏱️  Time taken: {time.time() - start_time:.2f} seconds")
