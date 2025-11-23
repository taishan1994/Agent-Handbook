from pocketflow import Flow
from nodes import GetTopicNode, GenerateJokeNode, GetFeedbackNode

def create_joke_flow() -> Flow:
    """Creates and returns the joke generation flow."""
    get_topic_node = GetTopicNode()
    generate_joke_node = GenerateJokeNode()
    get_feedback_node = GetFeedbackNode()

    get_topic_node >> generate_joke_node
    generate_joke_node >> get_feedback_node
    get_feedback_node - "Disapprove" >> generate_joke_node

    joke_flow = Flow(start=get_topic_node)
    return joke_flow 