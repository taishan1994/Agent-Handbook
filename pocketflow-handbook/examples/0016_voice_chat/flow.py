from pocketflow import Flow
from nodes import CaptureAudioNode, SpeechToTextNode, QueryLLMNode, TextToSpeechNode, TextInputNode, TextToAudioNode

def create_voice_chat_flow() -> Flow:
    """Creates and returns the voice chat flow."""
    # Create nodes
    capture_audio = CaptureAudioNode()
    speech_to_text = SpeechToTextNode()
    query_llm = QueryLLMNode()
    text_to_speech = TextToSpeechNode()

    # Define transitions
    capture_audio >> speech_to_text
    speech_to_text >> query_llm
    query_llm >> text_to_speech

    # Loop back for next turn or end
    text_to_speech - "next_turn" >> capture_audio
    # "end_conversation" action from any node will terminate the flow naturally
    # if no transition is defined for it from the current node.
    # Alternatively, one could explicitly transition to an EndNode if desired.

    # Create flow starting with the capture audio node
    voice_chat_flow = Flow(start=capture_audio)
    return voice_chat_flow 

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

    # Create flow starting with the text input node
    text_chat_flow = Flow(start=text_input)
    return text_chat_flow

def create_text_to_voice_chat_flow() -> Flow:
    """Creates and returns a text-based chat flow with audio conversion loop.
    
    Flow: TextInput → TextToAudio → SpeechToText → QueryLLM → TextToSpeech → TextInput
    """
    # Create nodes
    text_input = TextInputNode()
    text_to_audio = TextToAudioNode()
    speech_to_text = SpeechToTextNode()
    query_llm = QueryLLMNode()
    text_to_speech = TextToSpeechNode()

    # Define transitions
    text_input >> text_to_audio
    text_to_audio >> speech_to_text
    speech_to_text >> query_llm
    query_llm >> text_to_speech

    # Loop back for next turn
    text_to_speech - "next_turn" >> text_input

    # Create flow starting with the text input node
    text_to_voice_flow = Flow(start=text_input)
    return text_to_voice_flow

def get_flow(mode="voice") -> Flow:
    """Returns the appropriate flow based on the mode parameter.
    
    Args:
        mode: "voice" for voice input, "text" for direct text-to-LLM,
              "text_to_voice" for text-to-audio-to-text-to-LLM flow
        
    Returns:
        The appropriate flow instance
    """
    if mode == "text":
        return create_text_chat_flow()
    elif mode == "text_to_voice":
        return create_text_to_voice_chat_flow()
    else:
        return create_voice_chat_flow()