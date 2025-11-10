import streamlit as st
import base64
from flow import create_generation_flow

st.title("PocketFlow Image Generation HITL")

# Initialize session state for shared store
if 'stage' not in st.session_state:
    st.session_state.stage = "initial_input"
    st.session_state.task_input = ""
    st.session_state.generated_image = ""
    st.session_state.final_result = ""
    st.session_state.error_message = ""

# Debug info
with st.expander("Session State"):
    st.json({k: v for k, v in st.session_state.items() if not k.startswith("_")})

# State-based UI
if st.session_state.stage == "initial_input":
    st.header("1. Generate Image")
    
    prompt = st.text_area("Enter image prompt:", value=st.session_state.task_input, height=100)
    
    if st.button("Generate Image"):
        if prompt.strip():
            st.session_state.task_input = prompt
            st.session_state.error_message = ""
            
            try:
                with st.spinner("Generating image..."):
                    flow = create_generation_flow()
                    flow.run(st.session_state)
                st.rerun()
            except Exception as e:
                st.session_state.error_message = str(e)
        else:
            st.error("Please enter a prompt")

elif st.session_state.stage == "user_feedback":
    st.header("2. Review Generated Image")
    
    if st.session_state.generated_image:
        # Display image
        image_bytes = base64.b64decode(st.session_state.generated_image)
        st.image(image_bytes, caption=f"Prompt: {st.session_state.task_input}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Approve", use_container_width=True):
                st.session_state.final_result = st.session_state.generated_image
                st.session_state.stage = "final"
                st.rerun()
        
        with col2:
            if st.button("Regenerate", use_container_width=True):
                try:
                    with st.spinner("Regenerating image..."):
                        flow = create_generation_flow()
                        flow.run(st.session_state)
                    st.rerun()
                except Exception as e:
                    st.session_state.error_message = str(e)

elif st.session_state.stage == "final":
    st.header("3. Final Result")
    st.success("Image approved!")
    
    if st.session_state.final_result:
        image_bytes = base64.b64decode(st.session_state.final_result)
        st.image(image_bytes, caption=f"Final approved image: {st.session_state.task_input}")
    
    if st.button("Start Over", use_container_width=True):
        st.session_state.stage = "initial_input"
        st.session_state.task_input = ""
        st.session_state.generated_image = ""
        st.session_state.final_result = ""
        st.session_state.error_message = ""
        st.rerun()

# Show errors
if st.session_state.error_message:
    st.error(st.session_state.error_message)

