# PocketFlow FastAPI WebSocket Chat

Real-time chat interface with streaming LLM responses using PocketFlow, FastAPI, and WebSocket.

<p align="center">
  <img 
    src="./assets/banner.png" width="800"
  />
</p>

## Features

- **Real-time Streaming**: See AI responses typed out in real-time as the LLM generates them
- **Conversation Memory**: Maintains chat history across messages
- **Modern UI**: Clean, responsive chat interface with gradient design
- **WebSocket Connection**: Persistent connection for instant communication
- **PocketFlow Integration**: Uses PocketFlow `AsyncNode` and `AsyncFlow` for streaming

## How to Run

1. **Set OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python main.py
   ```

4. **Access the Web UI:**
   Open `http://localhost:8000` in your browser.

## Usage

1. **Type Message**: Enter your message in the input field
2. **Send**: Press Enter or click Send button
3. **Watch Streaming**: See the AI response appear in real-time
4. **Continue Chat**: Conversation history is maintained automatically

## Files

- [`main.py`](./main.py): FastAPI application with WebSocket endpoint
- [`nodes.py`](./nodes.py): PocketFlow `StreamingChatNode` definition
- [`flow.py`](./flow.py): PocketFlow `AsyncFlow` for chat processing
- [`utils/stream_llm.py`](./utils/stream_llm.py): OpenAI streaming utility
- [`static/index.html`](./static/index.html): Modern chat interface
- [`requirements.txt`](./requirements.txt): Project dependencies
- [`docs/design.md`](./docs/design.md): System design documentation
- [`README.md`](./README.md): This file 