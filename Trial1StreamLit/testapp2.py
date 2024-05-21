# To run this code, run this command in the terminal:
# streamlit run testapp_almost_clear.py

# Import necessary libraries
import os  # Module to interact with the operating system
import openai  # OpenAI's library for accessing its API
import streamlit as st  # Streamlit library for building web applications
from langchain_google_community import GoogleSearchAPIWrapper  # Custom wrapper for Google Search API
import requests
from bs4 import BeautifulSoup

# Set up API keys by setting environment variables
os.environ["OPENAI_API_KEY"] = "sk-proj-YcXN3RqeYPmOFAzGBa6uT3BlbkFJpiNKLtMtGvothmVUVUD9"
os.environ["GOOGLE_API_KEY"] = "AIzaSyC_YRuIBDGxffMmnE02y7n33Q5kK399ueU"
os.environ["GOOGLE_CSE_ID"] = "f25ef6a71b8714b28"

# Initialize OpenAI and Google Search clients
openai.api_key = os.getenv("OPENAI_API_KEY")  # Fetch OpenAI API key from environment variables
search = GoogleSearchAPIWrapper()  # Create an instance of the Google Search API wrapper

# Function to fetch the full content of a web page
def fetch_full_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Get all text content from the webpage
        content = ' '.join([p.get_text() for p in soup.find_all('p')])
        return content
    except requests.RequestException as e:
        st.write(f"Error fetching content from {url}: {e}")
        return None

# Function to fetch the best matching information using Google Search
def fetch_information_from_url(query):
    try:
        # Perform Google search and fetch top 1 result (most relevant)
        results = search.results(query, 1)
        if not results:
            return None
        top_result_url = results[0]['link']
        full_content = fetch_full_content(top_result_url)
        if full_content:
            return full_content
        else:
            return "Failed to fetch content from the top result."
    except Exception as e:
        st.write(f"HTTP error occurred: {e}")
        return None

# Function to check if the query is a greeting
def is_greeting(query):
    # Construct messages for the model to determine if the query is a greeting
    messages = [
        {"role": "system", "content": "Determine if the following text is a greeting. Respond with 'yes' or 'no'."},
        {"role": "user", "content": query}
    ]
    
    # Call OpenAI's API to get the response
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=5
    )
    
    # Return True if the response is 'yes', otherwise False
    return response.choices[0].message.content.strip().lower() == "yes"

# Function to check if the query is related to CGU
def is_related_to_cgu(query, conversation_history):
    # Construct messages for the model to determine if the query is related to CGU
    messages = [
        {"role": "system", "content": "Determine if the following conversation, considering the history and current message, is talking about Claremont Graduate University (CGU) or if it is getting too general. Respond with 'cgu' or 'general'."},
        {"role": "user", "content": f"Conversation history: {conversation_history}\nCurrent message: {query}"}
    ]
    
    # Call OpenAI's API to get the response
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=5
    )
    
    # Return the response which indicates if the query is related to CGU or not
    return response.choices[0].message.content.strip().lower()

# Function to process incoming queries
def process_query(query, conversation_history):
    # Check if the query is a greeting and is short (<= 3 words)
    if is_greeting(query) and len(query.split()) <= 3:
        return "greeting"
    
    # Check if the query is related to CGU
    if is_related_to_cgu(query, conversation_history) == "cgu":
        return "cgu_related"
    
    # Otherwise, classify the query as not related to CGU
    return "not_related"

# Function to summarize conversation history
def summarize_conversation_history(conversation_history):
    # Construct messages for the model to summarize the conversation history
    messages = [
        {"role": "system", "content": "Summarize the following conversation history, keeping the important points."},
        {"role": "user", "content": conversation_history}
    ]
    
    # Call OpenAI's API to get the summary
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300
    )
    
    # Return the summarized conversation history
    return response.choices[0].message.content.strip()

# Function to generate response using the language model
def generate_response(query, conversation_history, query_type, cached_content=None):
    # Summarize conversation history if it exceeds 3000 tokens
    if len(conversation_history.split()) > 3000:
        conversation_history = summarize_conversation_history(conversation_history)
    
    # Generate a response for greeting queries
    if query_type == "greeting":
        messages = [
            {"role": "system", "content": "Generate a friendly greeting response."},
            {"role": "user", "content": ""}
        ]
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150  # Increase token limit for greeting responses
        )
        return response.choices[0].message.content.strip(), None

    # Generate a response for non-CGU related queries
    if query_type == "not_related":
        return ("I can only answer questions related to Claremont Graduate University (CGU). "
                "Here are some example questions you can ask:\n"
                "- What are the top programs at Claremont Graduate University?\n"
                "- How does one apply to CGU?\n"
                "- What are the tuition fees at Claremont Graduate University?\n"
                "- Can you tell me about the student life or campus culture at CGU?"), None

    # Fetch information using Google Search for CGU-related queries
    if not cached_content:
        full_content = fetch_information_from_url(query)
        if full_content:
            cached_content = full_content
        else:
            return "Failed to fetch relevant information.", None

    # Use the language model to generate a response using the cached content
    messages = [
        {"role": "system", "content": "Answer the following question using the information provided, include relevant links and detailed steps where applicable."},
        {"role": "user", "content": f"Question: {query}\n\nConversation history: {conversation_history}\n\nInformation:\n{cached_content}"}
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=800  # Drastically increase token limit for detailed responses
    )

    return response.choices[0].message.content.strip(), cached_content

# Main function to handle incoming messages
def handle_message(message, conversation_history, cached_content=None):
    # Process the incoming message/query to determine its type
    query_type = process_query(message, conversation_history)
    
    # Generate a response for the processed query
    response, cached_content = generate_response(message, conversation_history, query_type, cached_content)
    
    # Update conversation history with the latest message and response
    conversation_history += f"User: {message}\nAssistant: {response}\n"
    
    # Return the generated response and updated conversation history
    return response, conversation_history, cached_content

# Set up the chatbot using Streamlit for basic display and testing
if __name__ == "__main__":
    # Streamlit UI setup
    st.title("Claremont Graduate University Chatbot")
    user_input = st.text_input("Ask a question about Claremont Graduate University:")  # Input field for user queries
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = ""  # Initialize conversation history in session state
    if 'cached_content' not in st.session_state:
        st.session_state.cached_content = None  # Initialize cached content in session state

    if user_input:
        # Handle the user input and update conversation history and cached content
        response, st.session_state.conversation_history, st.session_state.cached_content = handle_message(
            user_input, st.session_state.conversation_history, st.session_state.cached_content
        )
        st.write("Response:", response)  # Display the response in the Streamlit app
