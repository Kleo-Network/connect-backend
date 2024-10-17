from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from ...core.models.constants import ACTIVITIES

kw_model = KeyBERT()
model = SentenceTransformer("all-mpnet-base-v2")


def get_relevant_activity_via_context(passages):
    # Generate embeddings for all passages in the batch
    passage_embeddings = model.encode(passages, convert_to_tensor=True)

    # Initialize a dictionary to hold scores for each passage
    activities_for_passages = []

    # Generate embeddings for each activity's name
    activity_embeddings = {
        activity: model.encode(activity, convert_to_tensor=True)
        for activity in ACTIVITIES
    }

    # Iterate over each passage embedding to calculate similarities
    for passage_embedding in passage_embeddings:
        activity_scores = {activity: 0 for activity in ACTIVITIES}

        # Score based on similarity between the passage and each activity
        for activity, activity_embedding in activity_embeddings.items():
            similarity = util.pytorch_cos_sim(
                passage_embedding, activity_embedding
            ).item()
            activity_scores[activity] += similarity

        # Find the activity with the highest score for this passage
        most_relevant_activity = max(activity_scores, key=activity_scores.get)
        activities_for_passages.append(most_relevant_activity)

    # Return the list of activities in the same order as the input passages
    return activities_for_passages


def get_most_relevant_activity(contents):
    # Call the updated function to process the batch
    return get_relevant_activity_via_context(contents)
