# flow.py

from pocketflow import Flow
from nodes import ThinkNode, ActionNode, ObserveNode, EndNode

def create_tao_flow():
    """
    Create a Thought-Action-Observation loop flow
    
    How the flow works:
    1. ThinkNode decides the next action
    2. ActionNode executes the action
    3. ObserveNode observes the action result
    4. Return to ThinkNode to continue thinking, or end the flow
    
    Returns:
        Flow: Complete TAO loop flow
    """
    # Create node instances
    think = ThinkNode()
    action = ActionNode()
    observe = ObserveNode()
    end = EndNode()
    
    # Connect nodes
    # If ThinkNode returns "action", go to ActionNode
    think - "action" >> action
    
    # If ThinkNode returns "end", end the flow
    think - "end" >> end
    
    # After ActionNode completes, go to ObserveNode
    action - "observe" >> observe
    
    # After ObserveNode completes, return to ThinkNode
    observe - "think" >> think
    
    # Create and return flow, starting from ThinkNode
    return Flow(start=think)