from pocketflow import Flow
from nodes import GenerateOutline, WriteContent, ApplyStyle

def create_article_flow():
    """
    Create and configure the article writing workflow
    """
    # Create node instances
    outline_node = GenerateOutline()
    content_node = WriteContent()
    style_node = ApplyStyle()
    
    # Connect nodes in sequence
    outline_node >> content_node >> style_node
    
    # Create flow starting with outline node
    article_flow = Flow(start=outline_node)
    
    return article_flow 