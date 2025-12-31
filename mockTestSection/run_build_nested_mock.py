# mockTestSection/run_build_nested_mock.py
from dotenv import load_dotenv
from mockTestSection.mock_builder import build_and_store_one_mock
from database.firebase_client import get_firestore_client

def get_next_mock_name(prefix="SATMock"):
    """
    Automatically finds the next mock name by counting existing mocks
    in Firestore and returning 'SATMockX' where X = next number.
    """
    db = get_firestore_client()
    coll = db.collection("mock_tests")
    docs = list(coll.stream())

    # Count how many mocks already exist with the given prefix
    count = sum(1 for d in docs if d.id.startswith(prefix) or d.to_dict().get("name", "").startswith(prefix))
    next_num = count + 1

    return f"{prefix}{next_num}"

if __name__ == "__main__":
    load_dotenv()

    mock_name = get_next_mock_name("SATMock")  # → SATMock1, SATMock2, etc.
    print(f"🧩 Creating new mock: {mock_name}")

    mock_id = build_and_store_one_mock(
        name=mock_name,
        seed=None,     # None → random shuffle each time
        filters={},    # optionally pass filters like {"tags": ["geometry"]}
    )

    print("✅ Created mock:", mock_id)
