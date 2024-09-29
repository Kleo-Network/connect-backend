from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from ...core.models.constants import ACTIVITIES


kw_model = KeyBERT()
model = SentenceTransformer("all-mpnet-base-v2")


def get_relevant_activity_via_context(pass_content):
    # Generate embedding for the full passage
    passage_embedding = model.encode(pass_content, convert_to_tensor=True)

    # Initialize a dictionary to hold scores for each activity
    activity_scores = {activity: 0 for activity in ACTIVITIES}

    # Generate embeddings for each activity's name (since we no longer have keywords)
    activity_embeddings = {
        activity: model.encode(activity, convert_to_tensor=True)
        for activity in ACTIVITIES
    }

    # Score based on full passage
    for activity, activity_embedding in activity_embeddings.items():
        # Calculate similarity between the passage and the activity name embedding
        similarity = util.pytorch_cos_sim(passage_embedding, activity_embedding).item()
        activity_scores[activity] += similarity

    # Return the activity with the highest score
    return max(activity_scores, key=activity_scores.get)


def get_most_relevant_activity(content):
    print("-" * 50)
    print("Content : ", content)
    most_relevant_activity = get_relevant_activity_via_context(content)
    print(f"The most relevant activity is: {most_relevant_activity}")
    print("-" * 50)
    return most_relevant_activity
