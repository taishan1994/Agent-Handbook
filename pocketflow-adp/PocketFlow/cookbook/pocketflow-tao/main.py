# main.py

from flow import create_tao_flow

def main():
    
    query = """I need to understand the latest developments in artificial intelligence"""
    
    # Create shared data
    shared = {
        "query": query,
        "thoughts": [],
        "observations": [],
        "current_thought_number": 0
    }
    
    # Create and run flow
    tao_flow = create_tao_flow()
    tao_flow.run(shared)
    
    # Print final result
    if "final_answer" in shared:
        print("\nFinal Answer:")
        print(shared["final_answer"])
    else:
        print("\nFlow did not produce a final answer")

if __name__ == "__main__":
    main()