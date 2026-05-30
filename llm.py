from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="models/gemini-flash-lite-latest",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)