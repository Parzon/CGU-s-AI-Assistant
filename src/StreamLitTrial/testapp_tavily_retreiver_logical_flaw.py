# Import necessary libraries
import os
import openai
import streamlit as st
from langchain_community.retrievers.tavily_search_api import TavilySearchAPIRetriever
from openai import OpenAI

Client = OpenAI()

# Export the API keys for OpenAI model and Tavily Search
os.environ["OPENAI_API_KEY"] = "sk-proj-YcXN3RqeYPmOFAzGBa6uT3BlbkFJpiNKLtMtGvothmVUVUD9"
os.environ["TAVILY_API_KEY"] = "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"

# Initialize API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Define the list of URLs that the chatbot is allowed to access
allowed_urls = [
    "https://www.cgu.edu",
    "https://www.cgu.edu/academics/",
    "https://www.cgu.edu/admissions/",
    # Add more allowed URLs here
]

# Function to fetch information from allowed URLs
def fetch_information_from_url(query):
    retriever = TavilySearchAPIRetriever(
        api_key=tavily_api_key,
        include_domains=allowed_urls,
        k=5
    )
    
    results = retriever.get_relevant_documents(query=query)
    
    # Extract relevant information from the results
    search_results = [result.page_content for result in results]
    
    return search_results

# Function to check if the query is a greeting
def is_greeting(query):
    messages = [
        {"role": "system", "content": "Determine if the following text is a greeting. Respond with 'yes' or 'no'."},
        {"role": "user", "content": query}
    ]
    
    response = Client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=5
    )
    
    return response.choices[0].message.content.strip().lower() == "yes"

# Function to check if the query is related to CGU
def is_related_to_cgu(query, conversation_history):
    messages = [
        {"role": "system", "content": "Determine if the following conversation, considering the history and current message, is talking about Claremont Graduate University (CGU) or if it is getting too general. Respond with 'cgu' or 'general'."},
        {"role": "user", "content": f"Conversation history: {conversation_history}\nCurrent message: {query}"}
    ]
    
    response = Client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=5
    )
    
    return response.choices[0].message.content.strip().lower() == "cgu"

# Function to process incoming queries
def process_query(query, conversation_history):
    if is_greeting(query):
        return "greeting"
    
    if not is_related_to_cgu(query, conversation_history):
        return "not_related"
    
    return query

# Function to generate response using the language model
def generate_response(query, conversation_history):
    if query == "greeting":
        messages = [
            {"role": "system", "content": "Generate a friendly greeting response."},
            {"role": "user", "content": ""}
        ]
        response = Client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    
    if query == "not_related":
        messages = [
            {"role": "system", "content": "Respond to the user by stating that you can only answer questions related to Claremont Graduate University."},
            {"role": "user", "content": ""}
        ]
        response = Client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    
    # Fetch information from the allowed URLs
    search_results = fetch_information_from_url(query)
    
    # Use the language model to generate a response using the search results
    combined_search_results = "\n".join(search_results)
    messages = [
        {"role": "system", "content": "Answer the following question using the information provided."},
        {"role": "user", "content": f"Question: {query}\n\nInformation:\n{combined_search_results}"}
    ]
    response = Client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip()

# Main function to handle incoming messages
def handle_message(message, conversation_history):
    # Process the incoming message/query
    processed_query = process_query(message, conversation_history)
    
    # Generate a response for the processed query
    response = generate_response(processed_query, conversation_history)
    
    # Update conversation history
    conversation_history += f"User: {message}\nAssistant: {response}\n"
    
    # Return the generated response and updated conversation history
    return response, conversation_history

# Set up the chatbot using Streamlit for basic display and testing
if __name__ == "__main__":
    # Streamlit UI setup
    st.title("Claremont Graduate University Chatbot")
    user_input = st.text_input("Ask a question about Claremont Graduate University:")
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = ""

    if user_input:
        response, st.session_state.conversation_history = handle_message(user_input, st.session_state.conversation_history)
        st.write(response)
