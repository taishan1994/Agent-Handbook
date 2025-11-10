import sys
from flow import get_flow

def main():
    """Runs the PocketFlow Chat application."""
    # Parse command line arguments
    mode = "voice"  # Default mode
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1].lower()
        if mode_arg == "text":
            mode = "text"
        elif mode_arg == "text_to_voice":
            mode = "text_to_voice"
        else:
            print("Invalid mode. Use 'voice', 'text', or 'text_to_voice'.")
            return
    
    # Print appropriate instructions based on mode
    print(f"Starting PocketFlow {'Text' if mode == 'text' else 'Voice' if mode == 'voice' else 'Text-to-Voice'} Chat...")
    if mode == "text":
        print("Enter your text queries when prompted.")
        print("The conversation will continue until you enter an empty text or an error occurs.")
    elif mode == "text_to_voice":
        print("Enter your text queries when prompted.")
        print("The system will convert text to audio, then to text, then call LLM, then to audio.")
        print("The conversation will continue until you enter an empty text or an error occurs.")
    else:
        print("Speak your query after 'Listening for your query...' appears.")
        print("The conversation will continue until an error occurs or the loop is intentionally stopped.")
    
    shared = {
        "user_audio_data": None,
        "user_audio_sample_rate": None,
        "chat_history": [],
        "continue_conversation": True  # Flag to control the main conversation loop
    }

    # Create the appropriate flow
    chat_flow = get_flow(mode=mode)

    # Run the flow
    # The flow will loop based on the "next_turn" action from TextToSpeechNode
    # and the continue_conversation flag checked within nodes or if an error action is returned.
    chat_flow.run(shared)

if __name__ == "__main__":
    main()
