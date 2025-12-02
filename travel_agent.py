import streamlit as st
import json
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import GoogleSerperAPIWrapper
from agents import generate_itinerary, recommend_activities, fetch_useful_links, weather_forecaster, packing_list_generator, food_culture_recommender, chat_agent
from utils_export import export_to_pdf
import os
from dotenv import load_dotenv
import getpass
#from IPython.display import Image, display

#serper_api_key = os.environ["SERPER_API_KEY"]


# Load environment variables
load_dotenv()


# Initialize LLM
st.set_page_config(page_title="Travel Itinerary Planner", page_icon="✈️", layout="wide")
try:
  llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
except Exception as e:
  st.error(f"Failed to initialize LLM: {str(e)}")
  st.stop()

# Initialzie GoogleSerperAPIWrapper
try:
  search = GoogleSerperAPIWrapper(serper_api_key="679fb58cb84c5e5afe3faaeb08508c2a38af5e49")

except Exception as e:
  st.error(f"Failed to initialize GoogleSerperAPIWrapper: {str(e)}")
  st.stop()

# Define state
class State(TypedDict):
  preferences_text: str
  preferences: dict
  itinerary: str
  activity_suggestions: str
  useful_links: list[dict]
  weather_forecast: str
  packing_list: str
  food_culture_info: str
  chat_history: Annotated[list[dict], "List of question-response pairs"]
  user_question: str
  chat_response: str
  action: Literal["generate_itinerary", "recommend_activities", "fetch_useful_links", "weather_forecaster", "packing_list_generator", "food_culture_recommender", "chat"]

# Router node to direct traffic to different agents
def router_node(state):
    action = state.get("action")
    if action == "generate_itinerary":
        return "generate_itinerary"
    elif action == "recommend_activities":
        return "recommend_activities"
    elif action == "fetch_useful_links":
        return "fetch_useful_links"
    elif action == "weather_forecaster":
        return "weather_forecaster"
    elif action == "packing_list_generator":
        return "packing_list_generator"
    elif action == "food_culture_recommender":
        return "food_culture_recommender"
    elif action == "chat":
        return "chat"
    return "generate_itinerary" # Default or fallback

# Langgraph State
workflow = StateGraph(State)
workflow.add_node("router", router_node) # Add the router node
workflow.add_node("generate_itinerary", generate_itinerary.generate_itinerary)
workflow.add_node("recommend_activities", recommend_activities.recommend_activities)
workflow.add_node("fetch_useful_links", fetch_useful_links.fetch_useful_links) # Fixed typo 'workfloe' to 'workflow'
workflow.add_node("weather_forecaster", weather_forecaster.weather_forecaster)
workflow.add_node("packing_list_generator", packing_list_generator.packing_list_generator)
workflow.add_node("food_culture_recommender", food_culture_recommender.food_culture_recommender)
workflow.add_node("chat", chat_agent.chat_node)

workflow.set_entry_point("router") # Set router as the entry point

# Define conditional edges from the router
workflow.add_conditional_edges(
    "router",
    lambda x: x["action"],
    {
        "generate_itinerary": "generate_itinerary",
        "recommend_activities": "recommend_activities",
        "fetch_useful_links": "fetch_useful_links",
        "weather_forecaster": "weather_forecaster",
        "packing_list_generator": "packing_list_generator",
        "food_culture_recommender": "food_culture_recommender",
        "chat": "chat",
    }
)

# Each agent's execution will end for now, but could be routed back to the router
workflow.add_edge("generate_itinerary", END)
workflow.add_edge("recommend_activities", END)
workflow.add_edge("fetch_useful_links", END)
workflow.add_edge("weather_forecaster", END)
workflow.add_edge("packing_list_generator", END)
workflow.add_edge("food_culture_recommender", END)
workflow.add_edge("chat", END)
graph = workflow.compile()


