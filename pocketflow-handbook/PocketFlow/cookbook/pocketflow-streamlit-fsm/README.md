# PocketFlow Streamlit Image Generation HITL

Human-in-the-Loop (HITL) image generation application using PocketFlow and Streamlit. Enter text prompts, generate images with OpenAI, and approve/regenerate results.

<p align="center">
  <img 
    src="./assets/banner.png" width="800"
  />
</p>

## Features

-   **Image Generation:** Uses OpenAI's `gpt-image-1` model to generate images from text prompts
-   **Human Review:** Interactive interface to approve or regenerate images
-   **State Machine:** Clean state-based workflow (`initial_input` → `user_feedback` → `final`)
-   **PocketFlow Integration:** Uses PocketFlow `Node` and `Flow` for image generation with built-in retries
-   **Session State Management:** Streamlit session state acts as PocketFlow's shared store
-   **In-Memory Images:** Images stored as base64 strings, no disk storage required

## How to Run

1.  **Set OpenAI API Key:**
    ```bash
    export OPENAI_API_KEY="your-openai-api-key"
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit Application:**
    ```bash
    streamlit run app.py
    ```

4.  **Access the Web UI:**
    Open the URL provided by Streamlit (usually `http://localhost:8501`).

## Usage

1. **Enter Prompt**: Describe the image you want to generate
2. **Generate**: Click "Generate Image" to create the image
3. **Review**: View the generated image and choose:
   - **Approve**: Accept the image and move to final result
   - **Regenerate**: Generate a new image with the same prompt
4. **Final**: View approved image and optionally start over

## Files

-   [`app.py`](./app.py): Main Streamlit application with state-based UI
-   [`nodes.py`](./nodes.py): PocketFlow `GenerateImageNode` definition
-   [`flow.py`](./flow.py): PocketFlow `Flow` for image generation
-   [`utils/generate_image.py`](./utils/generate_image.py): OpenAI image generation utility
-   [`requirements.txt`](./requirements.txt): Project dependencies
-   [`docs/design.md`](./docs/design.md): System design documentation
-   [`README.md`](./README.md): This file
