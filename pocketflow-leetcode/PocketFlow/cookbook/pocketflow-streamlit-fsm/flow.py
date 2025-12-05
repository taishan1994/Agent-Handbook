from pocketflow import Flow
from nodes import GenerateImageNode

def create_generation_flow():
    """Creates a flow for image generation (initial or regeneration)."""
    generate_image_node = GenerateImageNode()
    return Flow(start=generate_image_node)


