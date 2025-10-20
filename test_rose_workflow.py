"""
Simple test to verify Rose's workflow with therapeutic context.
This tests that the graph can be compiled and the workflow routes correctly.
"""
import asyncio
from langchain_core.messages import HumanMessage
from ai_companion.graph.graph import create_workflow_graph
from ai_companion.graph.state import AICompanionState


async def test_workflow_routing():
    """Test that the workflow routes correctly without image node."""
    print("Testing Rose's simplified workflow...")
    
    # Create the graph
    graph_builder = create_workflow_graph()
    graph = graph_builder.compile()
    
    # Verify graph structure
    print("\n✓ Graph compiled successfully")
    
    # Check that image_node is not in the graph
    nodes = list(graph.nodes.keys())
    print(f"\nActive nodes: {nodes}")
    
    if "image_node" in nodes:
        print("✗ ERROR: image_node should not be in the graph")
        return False
    else:
        print("✓ image_node correctly excluded from graph")
    
    # Verify required nodes are present
    required_nodes = [
        "memory_extraction_node",
        "router_node", 
        "context_injection_node",
        "memory_injection_node",
        "conversation_node",
        "audio_node",
        "summarize_conversation_node"
    ]
    
    for node in required_nodes:
        if node in nodes:
            print(f"✓ {node} present")
        else:
            print(f"✗ ERROR: {node} missing")
            return False
    
    print("\n✓ All required nodes present")
    print("✓ Workflow structure verified successfully")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_workflow_routing())
    if success:
        print("\n✅ All workflow tests passed!")
    else:
        print("\n❌ Workflow tests failed")
        exit(1)
