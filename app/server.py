#!/usr/bin/env python
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain import hub
from langchain_core.messages import BaseMessage

# Initialize the FastAPI app
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces"
)

# Define input and output data models for FastAPI
class Input(BaseModel):
    input: str
    chat_history: List[BaseMessage] = []

class Output(BaseModel):
    output: str

# Load and prepare the Retriever
loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
embeddings = OpenAIEmbeddings()
vector = FAISS.from_documents(documents, embeddings)
retriever = vector.as_retriever()
retriever_tool = create_retriever_tool(
    retriever,
    "langsmith_search",
    "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!"
)

# Create the search tool
api_key = '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'
search = TavilySearchResults(api_wrapper=api_wrapper)
tools = [retriever_tool, search]

# Setup the LangChain agent
prompt = hub.pull("hwchase17/openai-functions-agent")
llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=os.getenv("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"), temperature=0)
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# FastAPI route to handle requests
@app.post("/agent", response_model=Output)
async def run_agent(input_data: Input):
    try:
        result = await agent_executor.run_async(input_data.input, input_data.chat_history)
        return Output(output=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the app using Uvicorn, if the script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
