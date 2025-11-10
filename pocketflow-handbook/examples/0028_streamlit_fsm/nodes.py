from pocketflow import Node
from utils.generate_image import generate_image

class GenerateImageNode(Node):
    """Generates image from text prompt using OpenAI API."""
    
    def prep(self, shared):
        return shared.get("task_input", "")

    def exec(self, prompt):
        return generate_image(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["input_used_by_process"] = prep_res
        shared["generated_image"] = exec_res
        shared["stage"] = "user_feedback"
        return "default"