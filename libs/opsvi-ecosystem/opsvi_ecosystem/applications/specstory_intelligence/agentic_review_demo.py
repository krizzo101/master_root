import json

from src.applications.specstory_intelligence.agentic_review_workflow import (
    flag_turn_for_review,
)

# Load a parsed session file
with open(
    "data/artifacts/2025-06-28/specstory_intelligence_processed.json", encoding="utf-8"
) as f:
    data = json.load(f)

# Select the first session and the second turn (assistant response)
session = data["sessions"][0]
turn = session["turns"][1]  # turn_sequence 2, assistant

# Flag the turn for review
annotation = flag_turn_for_review(
    turn,
    reviewer_id="demo_reviewer",
    summary="Assistant response may oversimplify by removing too many critical startup steps.",
    details="The assistant removed multi-agent coordination, external tools, and protocol enforcement, which may be required for robust startup. Recommend review by a domain expert.",
    categories=["oversimplification", "potential_loss_of_critical_functionality"],
)

# Print the annotated turn
print(json.dumps(turn, indent=2))
