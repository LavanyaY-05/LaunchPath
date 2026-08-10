# import os
# import re
# from typing import Optional
# from dotenv import load_dotenv

# load_dotenv()

# LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# def get_llm_response(prompt: str, system_prompt: Optional[str] = None, provider: Optional[str] = None) -> str:
#     """
#     Invokes LLM provider (Groq or OpenAI) based on env var or parameter.
#     Falls back gracefully if network or API keys are unavailable.
#     """
#     selected_provider = (provider or LLM_PROVIDER).lower()

#     # 1. Try Groq if selected
#     if selected_provider == "groq" and GROQ_API_KEY:
#         try:
#             from langchain_groq import ChatGroq
#             from langchain_core.messages import SystemMessage, HumanMessage
            
#             # Try primary Groq model: llama-3.3-70b-versatile
#             try:
#                 from langchain_groq import ChatGroq
#                 from langchain_core.messages import SystemMessage, HumanMessage
                
#                 llm = ChatGroq(
#                     groq_api_key=GROQ_API_KEY,
#                     model_name="llama-3.3-70b-versatile",
#                     temperature=0.2
#                 )
#                 messages = []
#                 if system_prompt:
#                     messages.append(SystemMessage(content=system_prompt))
#                 messages.append(HumanMessage(content=prompt))
                
#                 response = llm.invoke(messages)
#                 if response and response.content:
#                     return str(response.content)
#             except Exception as e1:
#                 print(f"[LLM] Groq primary model failed: {e1}")

#             # Try secondary Groq model: llama-3.1-8b-instant (high rate limit tier)
#             try:
#                 from langchain_groq import ChatGroq
#                 from langchain_core.messages import SystemMessage, HumanMessage
#                 llm = ChatGroq(
#                     groq_api_key=GROQ_API_KEY,
#                     model_name="llama-3.1-8b-instant",
#                     temperature=0.2
#                 )
#                 messages = []
#                 if system_prompt:
#                     messages.append(SystemMessage(content=system_prompt))
#                 messages.append(HumanMessage(content=prompt))
#                 response = llm.invoke(messages)
#                 if response and response.content:
#                     return str(response.content)
#             except Exception as e2:
#                 print(f"[LLM] Groq secondary model call failed: {e2}")

#     # 2. Try OpenAI if selected or fallback
#     if (selected_provider == "openai" or not GROQ_API_KEY) and OPENAI_API_KEY:
#         try:
#             from langchain_openai import ChatOpenAI
#             from langchain_core.messages import SystemMessage, HumanMessage
            
#             llm = ChatOpenAI(
#                 openai_api_key=OPENAI_API_KEY,
#                 model_name="gpt-4o-mini",
#                 temperature=0.2
#             )
#             messages = []
#             if system_prompt:
#                 messages.append(SystemMessage(content=system_prompt))
#             messages.append(HumanMessage(content=prompt))
            
#             response = llm.invoke(messages)
#             if response and response.content:
#                 return str(response.content)
#         except Exception as e:
#             print(f"[LLM] OpenAI call failed: {e}")

#     # 3. Deterministic Local Rule Engine Fallback (Guarantees zero-crash operation)
#     return fallback_generation(prompt)


# def fallback_generation(prompt: str) -> str:
#     """Generates a structured, grounded response adhering strictly to LaunchPath rules when API keys are unreachable."""
#     # Extract context snippet if present
#     context_match = re.search(r'Context Information:\n(.*?)\n\nUser Query:', prompt, re.DOTALL)
#     context_text = context_match.group(1) if context_match else ""

#     if not context_text or "No relevant context found" in prompt:
#         return "I don't have relevant information on that right now."

#     first_line = context_text.split("\n")[0][:100]
#     return (
#         f"It's great to see active focus on this area—there is strong, proven market demand for solutions here!\n\n"
#         f"Based on current guidance ({first_line}...):\n"
#         f"• Validate early demand by speaking directly with 5-10 target clients or users.\n"
#         f"• Structure your core offering clearly, highlighting your unique value proposition.\n"
#         f"• Leverage recognized framework procedures and official guidelines to ensure smooth execution.\n"
#         f"• Track actionable metrics such as waitlist signups, retention, or initial revenue signals.\n\n"
#         f"FOLLOW_UPS: How do I structure my pricing model? | What are the key eligibility steps? | What tools should I start with?"
#     )


import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


def get_llm_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Invokes OpenAI chat completion using LangChain.
    Falls back gracefully if the OpenAI API key is unavailable.
    """
    if OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOpenAI(
                openai_api_key=OPENAI_API_KEY,
                model_name="gpt-4o-mini",
                temperature=0.2
            )
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            response = llm.invoke(messages)
            if response and response.content:
                return str(response.content)
        except Exception as e:
            print(f"[LLM] OpenAI call failed: {e}")

    return fallback_generation(prompt)


def fallback_generation(prompt: str) -> str:
    """Generates a structured, grounded response adhering strictly to LaunchPath rules when API keys are unreachable."""
    # Extract context snippet if present
    context_match = re.search(r'Context Information:\n(.*?)\n\nUser Query:', prompt, re.DOTALL)
    context_text = context_match.group(1) if context_match else ""

    if not context_text or "No relevant context found" in prompt:
        return "I don't have relevant information on that right now."

    first_line = context_text.split("\n")[0][:100]
    return (
        f"It's great to see active focus on this area—there is strong, proven market demand for solutions here!\n\n"
        f"Based on current guidance ({first_line}...):\n"
        f"• Validate early demand by speaking directly with 5-10 target clients or users.\n"
        f"• Structure your core offering clearly, highlighting your unique value proposition.\n"
        f"• Leverage recognized framework procedures and official guidelines to ensure smooth execution.\n"
        f"• Track actionable metrics such as waitlist signups, retention, or initial revenue signals.\n\n"
        f"FOLLOW_UPS: How do I structure my pricing model? | What are the key eligibility steps? | What tools should I start with?"
    )