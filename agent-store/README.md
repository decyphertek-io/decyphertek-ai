# LangChain Agent Store

Build and deploy AI agents using **LangChain** and **LangGraph** in your mobile app.

## 📚 Documentation

- **LangChain Tutorials**: https://python.langchain.com/docs/tutorials/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://docs.smith.langchain.com/

## 🤖 What are Agents?

Agents are AI systems that can:
- Use tools and call external APIs
- Make decisions based on context
- Chain multiple actions together
- Remember past interactions
- Execute complex workflows

## 🏗️ Agent Types

### 1. **RAG Q&A Agent**
Build question-answering agents that retrieve information from your documents.

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools.retriever import create_retriever_tool

# Create retriever tool from your vector store
retriever_tool = create_retriever_tool(
    retriever,
    "document_search",
    "Search for information in uploaded documents"
)

# Create agent with tools
agent = create_openai_tools_agent(llm, [retriever_tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[retriever_tool])
```

**Tutorial**: [Build a RAG Application](https://python.langchain.com/docs/tutorials/)

### 2. **Tool Calling Agent**
Agents that can use external tools like web search, calculators, APIs, etc.

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool

# Define custom tools
def web_search(query: str) -> str:
    # Your search implementation
    return results

search_tool = Tool(
    name="web_search",
    description="Search the web for current information",
    func=web_search
)

# Create agent with tools
agent = create_tool_calling_agent(llm, [search_tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[search_tool])
```

**Tutorial**: [Build an Agent](https://python.langchain.com/docs/tutorials/agents/)

### 3. **Conversational Agent**
Chat agents with memory that remember conversation history.

```python
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor

# Add memory to your agent
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)
```

**Tutorial**: [Build a Chatbot](https://python.langchain.com/docs/tutorials/chatbot/)

### 4. **SQL Query Agent**
Natural language to SQL query execution.

```python
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///your_database.db")
agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools")
```

**Tutorial**: [Build a SQL Q&A System](https://python.langchain.com/docs/tutorials/sql_qa/)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install langchain langchain-openai langgraph langsmith
```

### 2. Basic Agent Template

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

# Initialize LLM (works with OpenRouter too!)
llm = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key="your-openrouter-key",
    model_name="openai/gpt-4-turbo"
)

# Define your tools
def my_tool(input: str) -> str:
    return f"Processed: {input}"

tools = [
    Tool(
        name="my_tool",
        description="Describe what your tool does",
        func=my_tool
    )
]

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Create and run agent
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Run the agent
result = agent_executor.invoke({"input": "Your question here"})
print(result["output"])
```

## 📖 LangChain Tutorials

Based on the official [LangChain Tutorials](https://python.langchain.com/docs/tutorials/):

### Get Started
1. **Chat models and prompts**: Build a simple LLM application
2. **Semantic search**: Build a semantic search engine over PDFs
3. **Classification**: Classify text into categories
4. **Extraction**: Extract structured data from text

### Orchestration with LangGraph
1. **Chatbots**: Build a chatbot with memory
2. **Agents**: Build an agent that interacts with tools
3. **RAG Part 1**: Build document-based Q&A
4. **RAG Part 2**: Build advanced RAG with memory
5. **SQL Q&A**: Query databases with natural language
6. **Summarization**: Generate summaries of long texts
7. **Graph Databases**: Query graph databases

### Advanced Patterns
- **Streaming**: Stream responses for better UX
- **Memory**: Add conversation memory
- **Tool calling**: Give agents access to external tools
- **Error handling**: Handle failures gracefully
- **Human-in-the-loop**: Add human approval steps

## 🔧 Integration with This App

### Using OpenRouter
All agents work with OpenRouter API! Just configure your API key in the Settings tab.

### Using Local Vector Store (Qdrant)
Your RAG agents can use the documents uploaded in the RAG tab.

### Using MCP Servers
Connect agents to your MCP servers for extended capabilities.

## 🎯 Example: RAG Agent with Memory

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools.retriever import create_retriever_tool
from langchain.memory import ConversationBufferMemory
from qdrant_client import QdrantClient

# Setup
llm = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="openai/gpt-4-turbo"
)

# Create retriever from your Qdrant store
retriever = your_vector_store.as_retriever()

# Create retriever tool
retriever_tool = create_retriever_tool(
    retriever,
    "search_documents",
    "Search through uploaded documents for relevant information"
)

# Add memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Create agent
agent = create_openai_tools_agent(llm, [retriever_tool], prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=[retriever_tool],
    memory=memory,
    verbose=True
)

# Use it!
result = agent_executor.invoke({
    "input": "What did we discuss about project deadlines?"
})
```

## 📝 Creating Custom Agents

Store your agents in this directory:

```
agent-store/
├── README.md
├── rag-qa-agent/
│   ├── agent.py
│   ├── config.json
│   └── requirements.txt
├── tool-calling-agent/
│   ├── agent.py
│   ├── config.json
│   └── requirements.txt
└── custom-agent/
    ├── agent.py
    ├── config.json
    └── requirements.txt
```

### Agent Structure

**agent.py**: Main agent implementation
```python
from langchain.agents import AgentExecutor

class MyAgent:
    def __init__(self, llm, config):
        self.llm = llm
        self.config = config
        self.agent_executor = self._create_agent()
    
    def _create_agent(self):
        # Your agent setup
        pass
    
    def run(self, input: str) -> str:
        return self.agent_executor.invoke({"input": input})
```

**config.json**: Agent configuration
```json
{
  "name": "My Custom Agent",
  "description": "What this agent does",
  "model": "openai/gpt-4-turbo",
  "temperature": 0.7,
  "tools": ["tool1", "tool2"],
  "memory_type": "buffer"
}
```

## 🌟 Resources

- **LangChain Docs**: https://python.langchain.com
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangSmith (Tracing)**: https://docs.smith.langchain.com/
- **Community Examples**: https://github.com/langchain-ai/langchain

## 🔗 Integration Points

This agent store integrates with:
- **OpenRouter API** (Settings tab) - Powers the LLMs
- **Qdrant RAG** (RAG tab) - Document retrieval
- **MCP Servers** (MCP tab) - External tools
- **Local Storage** - Agent configurations

## 🚦 Status

- ✅ Framework ready
- ✅ OpenRouter integration
- ✅ Qdrant vector store
- 🔄 Agent templates (in progress)
- 🔄 Custom agent builder (in progress)
- 🔄 Agent execution engine (in progress)

---

**Need help?** Check out the [LangChain tutorials](https://python.langchain.com/docs/tutorials/) for step-by-step guides!
