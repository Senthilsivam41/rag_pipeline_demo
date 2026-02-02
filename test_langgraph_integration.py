"""Test LangGraph agent integration for app_hybrid.py"""
import pandas as pd
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama


def test_langgraph_agent_integration():
    """Test that LangGraph agent works with our aggregation tools."""
    
    # Create sample data
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie", "Diana"],
        "Department": ["IT", "Sales", "IT", "HR"],
        "Salary": [100000, 80000, 110000, 70000]
    })
    
    # Create a simple tool
    @tool
    def get_total_salary() -> float:
        """Get total salary of all employees."""
        return float(df["Salary"].sum())
    
    @tool
    def get_employee_count() -> int:
        """Get total number of employees."""
        return len(df)
    
    tools = [get_total_salary, get_employee_count]
    
    # Create LLM
    llm = ChatOllama(model="llama3.2:1b", temperature=0)
    
    # Create agent
    system_prompt = "You are a helpful assistant with access to employee data tools."
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    
    # Test invoking the agent
    try:
        result = agent.invoke({"messages": [
            {"role": "user", "content": "How many employees are there?"}
        ]})
        
        # Check if we got a response
        if "messages" in result and result["messages"]:
            print("✅ LangGraph agent integration successful!")
            print(f"   Response type: {type(result['messages'][-1])}")
            return True
        else:
            print("✗ No messages in response")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_langgraph_agent_integration()
    exit(0 if success else 1)
