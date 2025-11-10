conversation_cache = {}


def load_conversation(conversation_id: str):
    print(f"Loading conversation {conversation_id}")
    return conversation_cache.get(conversation_id, {})


def save_conversation(conversation_id: str, session: dict):
    print(f"Saving conversation {session}")
    conversation_cache[conversation_id] = session
