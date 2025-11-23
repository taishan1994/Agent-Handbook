import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import gradio as gr
from gradio import ChatMessage

from flow import create_flow

# create global thread pool
chatflow_thread_pool = ThreadPoolExecutor(
    max_workers=5,
    thread_name_prefix="chatflow_worker",
)


def chat_fn(message, history, uuid):
    """
    Main chat function that handles the conversation flow and message processing.
    
    Args:
        message (str): The current user message
        history (list): Previous conversation history
        uuid (UUID): Unique identifier for the conversation
    
    Yields:
        ChatMessage: Streams of thought process and chat responses
    """
    # Log conversation details
    print(f"Conversation ID: {str(uuid)}\nHistory: {history}\nQuery: {message}\n---")
    
    # Initialize queues for chat messages and flow thoughts
    chat_queue = Queue()
    flow_queue = Queue()
    
    # Create shared context for the flow
    shared = {
        "conversation_id": str(uuid),
        "query": message,
        "history": history,
        "queue": chat_queue,
        "flow_queue": flow_queue,
    }
    
    # Create and run the chat flow in a separate thread
    chat_flow = create_flow()
    chatflow_thread_pool.submit(chat_flow.run, shared)

    # Initialize thought response tracking
    start_time = time.time()
    thought_response = ChatMessage(
        content="", metadata={"title": "Flow Log", "id": 0, "status": "pending"}
    )
    yield thought_response

    # Process and accumulate thoughts from the flow queue
    accumulated_thoughts = ""
    while True:
        thought = flow_queue.get()
        if thought is None:
            break
        accumulated_thoughts += f"- {thought}\n\n"
        thought_response.content = accumulated_thoughts.strip()
        yield thought_response
        flow_queue.task_done()

    # Mark thought processing as complete and record duration
    thought_response.metadata["status"] = "done"
    thought_response.metadata["duration"] = time.time() - start_time
    yield thought_response

    # Process and yield chat messages from the chat queue
    while True:
        msg = chat_queue.get()
        if msg is None:
            break
        chat_response = [thought_response, ChatMessage(content=msg)]
        yield chat_response
        chat_queue.task_done()


def clear_fn():
    print("Clearing conversation")
    return uuid.uuid4()


with gr.Blocks(fill_height=True, theme="ocean") as demo:
    uuid_state = gr.State(uuid.uuid4())
    demo.load(clear_fn, outputs=[uuid_state])

    chatbot = gr.Chatbot(type="messages", scale=1)
    chatbot.clear(clear_fn, outputs=[uuid_state])

    gr.ChatInterface(
        fn=chat_fn,
        type="messages",
        additional_inputs=[uuid_state],
        chatbot=chatbot,
        title="PocketFlow Gradio Demo",
    )


demo.launch()
