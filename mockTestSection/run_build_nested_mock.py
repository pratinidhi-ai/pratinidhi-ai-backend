# mockTestSection/run_build_nested_mock.py
import time
from dotenv import load_dotenv
from mockTestSection.mock_builder import build_and_store_one_mock
from database.firebase_client import get_firestore_client

def get_next_mock_name(prefix="SATMock"):
    """
    Automatically finds the next mock name by filling gaps in the numbering sequence.
    
    If mocks 4, 5, 6 exist, it will create 1, 2, 3 first.
    After all gaps are filled, it creates the next sequential number.
    
    Example:
    - Existing: SATMock4, SATMock5, SATMock6
    - Returns: SATMock1 (first gap)
    - Next call: SATMock2
    - After gaps filled: SATMock7
    """
    db = get_firestore_client()
    coll = db.collection("mock_tests")
    docs = list(coll.stream())

    # Extract existing mock numbers with the given prefix
    existing_numbers = set()
    for d in docs:
        # Check both document ID and name field
        mock_name = d.id if d.id.startswith(prefix) else d.to_dict().get("name", "")
        if mock_name.startswith(prefix):
            try:
                # Extract number from "SATMock123" -> 123
                num_str = mock_name[len(prefix):]
                if num_str.isdigit():
                    existing_numbers.add(int(num_str))
            except (ValueError, IndexError):
                continue
    
    if not existing_numbers:
        # No mocks exist yet, start with 1
        return f"{prefix}1"
    
    # Find the first gap in the sequence starting from 1
    max_num = max(existing_numbers)
    for i in range(1, max_num + 1):
        if i not in existing_numbers:
            # Found a gap, fill it
            return f"{prefix}{i}"
    
    # No gaps found, create the next sequential number
    return f"{prefix}{max_num + 1}"

if __name__ == "__main__":
    load_dotenv()

    mock_name = get_next_mock_name("SATMock")  # → SATMock1, SATMock2, etc.
    print(f"🧩 Creating new mock: {mock_name}")
    start_time = time.time()
    mock_id = build_and_store_one_mock(
        name=mock_name,
        seed=None,     # None → random shuffle each time
        filters={},    # optionally pass filters like {"tags": ["geometry"]}
    )

    print("✅ Created mock:", mock_id)
    print(f"⏱️  Time taken: {time.time() - start_time:.2f} seconds")
