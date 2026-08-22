import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model


load_dotenv(override=True)

llm = init_chat_model(
    model="deepseek:deepseek-chat",
    api_key = os.getenv("DEEPSEEK_API_KEY"),
    api_base = os.getenv("DEEPSEEK_API_BASE")
)
