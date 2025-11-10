def format_chat_history(history):
    """
    Format the chat history for LLM

    Args:
        history (list): The chat history list, each element contains role and content

    Returns:
        str: The formatted chat history string
    """
    if not history:
        return "No history"

    formatted_history = []
    for message in history:
        role = "user" if message["role"] == "user" else "assistant"
        content = message["content"]
        # filter out the thinking content
        if role == "assistant":
            if (
                content.startswith("- 🤔")
                or content.startswith("- ➡️")
                or content.startswith("- ⬅️")
            ):
                continue
        formatted_history.append(f"{role}: {content}")

    return "\n".join(formatted_history)
