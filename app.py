import streamlit as st
import copy
from agent import chatbot

st.set_page_config(page_title="AI Registration Assistant")
st.title("🤖 AI Registration Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_message = "Hello 👋\nI can help you with:\n1. Create registration\n2. View registration\n3. Update registration\n4. Delete registration\n\nHow can I assist you today?"
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})

if "graph_state" not in st.session_state:
    st.session_state.graph_state = {
        "user_input": "", "messages": [], "active_intent": None, "data": {},
        "missing_fields": [], "validation_errors": {}, "response": "",
        "awaiting_confirmation": False, "operation_complete": False, "last_action": None, "interruption_detected": False
    }

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Perform a deep copy to protect nested dicts from Streamlit rerender wipes
    current_state = copy.deepcopy(st.session_state.graph_state)
    current_state["user_input"] = user_input
    current_state["messages"] = list(st.session_state.messages)

    result = chatbot.invoke(current_state)
    bot_response = result.get("response", "I'm sorry, I encountered an issue processing that.")

    st.session_state.graph_state = result
    st.session_state.messages.append({"role": "assistant", "content": bot_response})

    with st.chat_message("assistant"):
        st.write(bot_response)