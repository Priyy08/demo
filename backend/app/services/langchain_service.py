# backend/app/services/langchain_service.py
# CORRECTED AND SIMPLIFIED VERSION

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from .memory_service import FirestoreChatMessageHistory
from ..config.settings import settings

# 1. Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.GOOGLE_API_KEY, temperature=0.7)

# 2. Create the Prompt Template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful and friendly assistant. Answer the user's questions clearly and concisely."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

# 3. Create the primary Conversation Chain
conversation_chain = prompt | llm

# 4. Define the history factory function.
# It now accepts user_id directly. The context system is completely gone.
def get_session_history(session_id: str, user_id: str) -> FirestoreChatMessageHistory:
    return FirestoreChatMessageHistory(conversation_id=session_id, user_id=user_id)

# 5. Create the final chain with history.
# This runnable will now expect both 'session_id' and 'user_id' to be in the config.
# We use a lambda function to map the keys from the config to the factory function's arguments.
chain_with_history = RunnableWithMessageHistory(
    conversation_chain,
    lambda session_id, **kwargs: get_session_history(session_id, user_id=kwargs["user_id"]),
    input_messages_key="question",
    history_messages_key="history",
)