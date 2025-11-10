from pocketflow import Flow
from nodes import TextInputNode, QueryLLMNode, TextToSpeechNode

def create_text_chat_flow() -> Flow:
    """Creates and returns a text-based chat flow that converts responses to audio."""
    # Create nodes
    text_input = TextInputNode()
    query_llm = QueryLLMNode()
    text_to_speech = TextToSpeechNode()

    # Define transitions
    text_input >> query_llm
    query_llm >> text_to_speech

    # Loop back for next turn or end
    text_to_speech - "next_turn" >> text_input
    # "end_conversation" action from any node will terminate the flow naturally

    # Create flow starting with the text input node
    text_chat_flow = Flow(start=text_input)
    return text_chat_flow

if __name__ == "__main__":
    # For direct testing of this flow
    flow = create_text_chat_flow()
    flow.run()