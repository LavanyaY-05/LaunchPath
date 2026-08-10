# # # import re
# # # from typing import Dict, List, Any, TypedDict, Optional
# # # from langgraph.graph import StateGraph, END
# # # from retrieval import search, MIN_RELEVANCE_THRESHOLD
# # # from prompts import (
# # #     SYSTEM_PROMPT,
# # #     GENERAL_QA_PROMPT,
# # #     IDEA_COMPARISON_PROMPT,
# # #     FORM_HELPER_PROMPT,
# # #     DOCUMENT_REVIEW_PROMPT,
# # #     SELF_REFLECT_PROMPT
# # # )
# # # from llm import get_llm_response


# # # class AgentState(TypedDict):
# # #     message: str
# # #     uploaded_text: Optional[str]
# # #     domain: Optional[str]
# # #     intent: str
# # #     retrieved_chunks: List[Dict[str, Any]]
# # #     relevance_ok: bool
# # #     answer: str
# # #     sources: List[str]
# # #     follow_ups: List[str]


# # # # ---------------------------------------------------------
# # # # Node 1: classify_intent
# # # # ---------------------------------------------------------
# # # from retrieval import search, MIN_RELEVANCE_THRESHOLD, detect_domain

# # # VAGUE_BUSINESS_PHRASES = [
# # #     "start a business", "start my business", "how can i proceed",
# # #     "want to start a business", "begin a business",
# # # ]

# # # def classify_intent_node(state: AgentState) -> Dict[str, Any]:
# # #     message = (state.get("message") or "").strip().lower()
# # #     uploaded_text = state.get("uploaded_text")
# # #     domain = detect_domain(state.get("message", ""))  # NEW

# # #     is_vague = any(phrase in message for phrase in VAGUE_BUSINESS_PHRASES)
# # #     if is_vague and domain is None:
# # #         return {"intent": "clarify", "domain": domain}  # NEW

# # #     review_keywords = ["review", "improve", "evaluate", "feedback", "critique", "pitch deck", "portfolio", "check"]
# # #     if uploaded_text and any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in review_keywords):
# # #         return {"intent": "document_review", "domain": domain}

# # #     comparison_keywords = ["vs", "compare", "difference between", "better than", "which idea", "choice", "or"]
# # #     if any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in comparison_keywords):
# # #         return {"intent": "idea_comparison", "domain": domain}

# # #     form_keywords = ["scheme", "udyam", "dpiit", "samridh", "form", "register", "registration", "legal", "msme", "apply", "grant", "subsidy", "document required"]
# # #     if any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in form_keywords):
# # #         return {"intent": "form_helper", "domain": domain}

# # #     return {"intent": "general_qa", "domain": domain}  # FIXED: domain now included


# # # # ---------------------------------------------------------
# # # # Node 2: retrieve
# # # # ---------------------------------------------------------
# # # def retrieve_node(state: AgentState) -> Dict[str, Any]:
# # #     message = state.get("message", "")
# # #     domain = state.get("domain")
# # #     intent = state.get("intent", "general_qa")
# # #     uploaded_text = state.get("uploaded_text")

# # #     if intent == "document_review":
# # #         # Search specifically for reference guidance docs
# # #         query = f"pitch deck portfolio guidance structure essentials {message}"
# # #         chunks = search(query, domain="general", k=5)
# # #         if not chunks:
# # #             chunks = search("pitch deck portfolio guidance", domain=None, k=5)
# # #         return {"retrieved_chunks": chunks}

# # #     chunks = search(message, domain=domain, k=5)
# # #     return {"retrieved_chunks": chunks}


# # # # ---------------------------------------------------------
# # # # Node 3: relevance_check
# # # # ---------------------------------------------------------
# # # def relevance_check_node(state: AgentState) -> Dict[str, Any]:
# # #     chunks = state.get("retrieved_chunks", [])
# # #     intent = state.get("intent", "general_qa")

# # #     if not chunks:
# # #         return {"relevance_ok": False}

# # #     if intent == "document_review":
# # #         return {"relevance_ok": True}

# # #     max_score = max((c.get("score", 0.0) for c in chunks), default=0.0)
# # #     # FIXED: threshold is now the actual gate, no bypass
# # #     relevance_ok = max_score >= MIN_RELEVANCE_THRESHOLD

# # #     return {"relevance_ok": relevance_ok}

# # # # Router function for conditional edge after relevance_check
# # # def route_after_relevance(state: AgentState) -> str:
# # #     if state.get("relevance_ok", False):
# # #         return "generate"
# # #     return "out_of_scope_response"


# # # # Out of scope refusal node (no LLM call, no sources)
# # # def out_of_scope_response_node(state: AgentState) -> Dict[str, Any]:
# # #     return {
# # #         "answer": "I don't have relevant information on that right now.",
# # #         "sources": [],
# # #         "follow_ups": []
# # #     }


# # # # ---------------------------------------------------------
# # # # Node 4: generate
# # # # ---------------------------------------------------------
# # # def generate_node(state: AgentState) -> Dict[str, Any]:
# # #     intent = state.get("intent", "general_qa")
# # #     message = state.get("message", "")
# # #     uploaded_text = state.get("uploaded_text", "")
# # #     chunks = state.get("retrieved_chunks", [])
# # #     user_domain = state.get("domain")

# # #     # Coherence Check: Detect if chunks span multiple disparate domains when user_domain is unspecified
# # #     chunk_domains = list(set(c.get("domain") for c in chunks if c.get("domain")))
# # #     coherence_notice = ""
# # #     if len(chunk_domains) > 1 and not user_domain:
# # #         coherence_notice = (
# # #             f"\n\nCOHERENCE CHECK NOTICE: The retrieved chunks span multiple distinct sub-topics ({', '.join(chunk_domains)}). "
# # #             f"Since the user did not specify a particular industry, DO NOT combine unrelated sub-topic details together into one answer. "
# # #             f"Either ask a clarifying question first ('What kind of business are you thinking of—a service, a product, freelancing, something local?') "
# # #             f"or provide only general-purpose steps and skip industry-specific details."
# # #         )

# # #     context_str = "\n\n".join([
# # #         f"Source [{c.get('source_title', 'Guidance')}]: {c.get('content', '')}"
# # #         for c in chunks
# # #     ]) + coherence_notice

# # #     if intent == "document_review":
# # #         prompt = DOCUMENT_REVIEW_PROMPT.format(
# # #             context=context_str,
# # #             uploaded_text=uploaded_text or "No document text uploaded.",
# # #             message=message
# # #         )
# # #     elif intent == "idea_comparison":
# # #         prompt = IDEA_COMPARISON_PROMPT.format(context=context_str, message=message)
# # #     elif intent == "form_helper":
# # #         prompt = FORM_HELPER_PROMPT.format(context=context_str, message=message)
# # #     else:
# # #         prompt = GENERAL_QA_PROMPT.format(context=context_str, message=message)

# # #     raw_answer = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
# # #     return {"answer": raw_answer}


# # # # ---------------------------------------------------------
# # # # Node 5: self_reflect
# # # # ---------------------------------------------------------
# # # def self_reflect_node(state: AgentState) -> Dict[str, Any]:
# # #     answer = state.get("answer", "")
# # #     chunks = state.get("retrieved_chunks", [])
    
# # #     if answer == "I don't have relevant information on that right now.":
# # #         return {}

# # #     context_str = "\n".join([c.get("content", "") for c in chunks])
# # #     reflect_prompt = SELF_REFLECT_PROMPT.format(context=context_str, answer=answer)
    
# # #     reflection = get_llm_response(prompt=reflect_prompt)

# # #     if "UNGROUNDED" in reflection:
# # #         # Re-generate once with strict instruction
# # #         message = state.get("message", "")
# # #         intent = state.get("intent", "general_qa")
# # #         uploaded_text = state.get("uploaded_text", "")
        
# # #         stricter_context = context_str + "\n\nCRITICAL: DO NOT ADD ANY EXTRA CLAIMS NOT STATED ABOVE."
# # #         if intent == "document_review":
# # #             prompt = DOCUMENT_REVIEW_PROMPT.format(context=stricter_context, uploaded_text=uploaded_text, message=message)
# # #         else:
# # #             prompt = GENERAL_QA_PROMPT.format(context=stricter_context, message=message)
            
# # #         regenerated = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
# # #         return {"answer": regenerated}

# # #     return {}


# # # # ---------------------------------------------------------
# # # # Node 6: finalize
# # # # ---------------------------------------------------------
# # # def finalize_node(state: AgentState) -> Dict[str, Any]:
# # #     raw_answer = state.get("answer", "")
# # #     chunks = state.get("retrieved_chunks", [])

# # #     if raw_answer == "I don't have relevant information on that right now.":
# # #         return {"answer": raw_answer, "sources": [], "follow_ups": []}

# # #     # Extract unique source titles for UI badges
# # #     sources = []
# # #     for c in chunks:
# # #         st = c.get("source_title")
# # #         if st and st not in sources:
# # #             sources.append(st)

# # #     # Extract follow-up question chips if present
# # #     follow_ups = []
# # #     if "FOLLOW_UPS:" in raw_answer:
# # #         parts = raw_answer.split("FOLLOW_UPS:")
# # #         clean_answer = parts[0].strip()
# # #         chips_str = parts[1].strip()
# # #         # Split by | or newlines
# # #         chips = [c.strip(" -*?123456789.") + "?" for c in re.split(r'[|\n]', chips_str) if c.strip()]
# # #         # Remove trailing double ??
# # #         follow_ups = [re.sub(r'\?+$', '?', c) for c in chips if len(c) > 3][:3]
# # #     else:
# # #         clean_answer = raw_answer

# # #     # Fallback follow-ups if LLM omitted them
# # #     if not follow_ups:
# # #         follow_ups = [
# # #             "What are the step-by-step requirements?",
# # #             "How do I structure my market positioning?",
# # #             "What key metrics should I track first?"
# # #         ]

# # #     return {
# # #         "answer": clean_answer,
# # #         "sources": sources,
# # #         "follow_ups": follow_ups
# # #     }


# # # # ---------------------------------------------------------
# # # # LangGraph StateGraph Construction
# # # # ---------------------------------------------------------
# # # def build_agent_graph():
# # #     workflow = StateGraph(AgentState)

# # #     # Add 6 nodes
# # #     workflow.add_node("classify_intent", classify_intent_node)
# # #     workflow.add_node("retrieve", retrieve_node)
# # #     workflow.add_node("relevance_check", relevance_check_node)
# # #     workflow.add_node("out_of_scope_response", out_of_scope_response_node)
# # #     workflow.add_node("generate", generate_node)
# # #     workflow.add_node("self_reflect", self_reflect_node)
# # #     workflow.add_node("finalize", finalize_node)

# # #     # Graph Edges
# # #     workflow.set_entry_point("classify_intent")
# # #     workflow.add_edge("classify_intent", "retrieve")
# # #     workflow.add_edge("retrieve", "relevance_check")

# # #     # Conditional routing after relevance check
# # #     workflow.add_conditional_edges(
# # #         "relevance_check",
# # #         route_after_relevance,
# # #         {
# # #             "generate": "generate",
# # #             "out_of_scope_response": "out_of_scope_response"
# # #         }
# # #     )

# # #     workflow.add_edge("generate", "self_reflect")
# # #     workflow.add_edge("self_reflect", "finalize")
# # #     workflow.add_edge("out_of_scope_response", END)
# # #     workflow.add_edge("finalize", END)

# # #     return workflow.compile()


# # # app_graph = build_agent_graph()


# # import re
# # from typing import Dict, List, Any, TypedDict, Optional
# # from langgraph.graph import StateGraph, END
# # from retrieval import search, MIN_RELEVANCE_THRESHOLD, detect_domain
# # from prompts import (
# #     SYSTEM_PROMPT,
# #     GENERAL_QA_PROMPT,
# #     IDEA_COMPARISON_PROMPT,
# #     FORM_HELPER_PROMPT,
# #     DOCUMENT_REVIEW_PROMPT,
# #     SELF_REFLECT_PROMPT
# # )
# # from llm import get_llm_response


# # class AgentState(TypedDict):
# #     message: str
# #     uploaded_text: Optional[str]
# #     domain: Optional[str]
# #     intent: str
# #     retrieved_chunks: List[Dict[str, Any]]
# #     relevance_ok: bool
# #     answer: str
# #     sources: List[str]
# #     follow_ups: List[str]


# # VAGUE_BUSINESS_PHRASES = [
# #     "start a business", "start my business", "how can i proceed",
# #     "want to start a business", "begin a business", "get started",
# #     "build a tech", "build a software", "software product",  # NEW — catches your exact failed test case
# # ]


# # # ---------------------------------------------------------
# # # Node 1: classify_intent
# # # ---------------------------------------------------------
# # def classify_intent_node(state: AgentState) -> Dict[str, Any]:
# #     message = (state.get("message") or "").strip().lower()
# #     uploaded_text = state.get("uploaded_text")
# #     domain = detect_domain(state.get("message", ""))

# #     # Vague query with no domain signal -> ask for clarification first
# #     is_vague = any(phrase in message for phrase in VAGUE_BUSINESS_PHRASES)
# #     if is_vague and domain is None:
# #         return {"intent": "clarify", "domain": domain}

# #     review_keywords = ["review", "improve", "evaluate", "feedback", "critique", "pitch deck", "portfolio", "check"]
# #     if uploaded_text and any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in review_keywords):
# #         return {"intent": "document_review", "domain": domain}

# #     comparison_keywords = ["vs", "compare", "difference between", "better than", "which idea", "choice", "or"]
# #     if any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in comparison_keywords):
# #         return {"intent": "idea_comparison", "domain": domain}

# #     form_keywords = ["scheme", "udyam", "dpiit", "samridh", "form", "register", "registration", "legal", "msme", "apply", "grant", "subsidy", "document required"]
# #     if any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in form_keywords):
# #         return {"intent": "form_helper", "domain": domain}

# #     return {"intent": "general_qa", "domain": domain}


# # def route_after_classify(state: AgentState) -> str:
# #     if state.get("intent") == "clarify":
# #         return "clarify_response"
# #     return "retrieve"


# # def clarify_response_node(state: AgentState) -> Dict[str, Any]:
# #     return {
# #         "answer": "What kind of business are you thinking about — a product, a service, freelancing, or something local like a shop? That'll help me point you to the right next steps.",
# #         "sources": [],
# #         "follow_ups": [
# #             "I want to build a tech/software product",
# #             "I want to start freelancing",
# #             "I want to open a local shop or food business",
# #         ]
# #     }


# # # ---------------------------------------------------------
# # # Node 2: retrieve
# # # ---------------------------------------------------------
# # def retrieve_node(state: AgentState) -> Dict[str, Any]:
# #     message = state.get("message", "")
# #     domain = state.get("domain")
# #     intent = state.get("intent", "general_qa")

# #     if intent == "document_review":
# #         query = f"pitch deck portfolio guidance structure essentials {message}"
# #         chunks = search(query, domain="general", k=5)
# #         if not chunks:
# #             chunks = search("pitch deck portfolio guidance", domain=None, k=5)
# #         return {"retrieved_chunks": chunks}

# #     chunks = search(message, domain=domain, k=3)
# #     return {"retrieved_chunks": chunks}


# # # ---------------------------------------------------------
# # # Node 3: relevance_check
# # # ---------------------------------------------------------
# # def relevance_check_node(state: AgentState) -> Dict[str, Any]:
# #     chunks = state.get("retrieved_chunks", [])
# #     intent = state.get("intent", "general_qa")

# #     if not chunks:
# #         return {"relevance_ok": False}

# #     if intent == "document_review":
# #         return {"relevance_ok": True}

# #     max_score = max((c.get("score", 0.0) for c in chunks), default=0.0)
# #     relevance_ok = max_score >= MIN_RELEVANCE_THRESHOLD  # real gate, no bypass

# #     return {"relevance_ok": relevance_ok}


# # def route_after_relevance(state: AgentState) -> str:
# #     if state.get("relevance_ok", False):
# #         return "generate"
# #     return "out_of_scope_response"


# # def out_of_scope_response_node(state: AgentState) -> Dict[str, Any]:
# #     return {
# #         "answer": "I don't have relevant information on that right now.",
# #         "sources": [],
# #         "follow_ups": []
# #     }


# # # ---------------------------------------------------------
# # # Node 4: generate
# # # ---------------------------------------------------------
# # def generate_node(state: AgentState) -> Dict[str, Any]:
# #     intent = state.get("intent", "general_qa")
# #     message = state.get("message", "")
# #     uploaded_text = state.get("uploaded_text", "")
# #     chunks = state.get("retrieved_chunks", [])
# #     user_domain = state.get("domain")

# #     chunk_domains = list(set(c.get("domain") for c in chunks if c.get("domain")))
# #     coherence_notice = ""
# #     if len(chunk_domains) > 1 and not user_domain:
# #         coherence_notice = (
# #             f"\n\nCOHERENCE CHECK NOTICE: The retrieved chunks span multiple distinct sub-topics "
# #             f"({', '.join(chunk_domains)}). Since the user did not specify a particular industry, "
# #             f"DO NOT combine unrelated sub-topic details together into one answer. Either ask a "
# #             f"clarifying question first, or provide only general-purpose steps and skip "
# #             f"industry-specific details."
# #         )

# #     context_str = "\n\n".join([
# #         f"Source [{c.get('source_title', 'Guidance')}]: {c.get('content', '')}"
# #         for c in chunks
# #     ]) + coherence_notice

# #     if intent == "document_review":
# #         prompt = DOCUMENT_REVIEW_PROMPT.format(
# #             context=context_str,
# #             uploaded_text=uploaded_text or "No document text uploaded.",
# #             message=message
# #         )
# #     elif intent == "idea_comparison":
# #         prompt = IDEA_COMPARISON_PROMPT.format(context=context_str, message=message)
# #     elif intent == "form_helper":
# #         prompt = FORM_HELPER_PROMPT.format(context=context_str, message=message)
# #     else:
# #         prompt = GENERAL_QA_PROMPT.format(context=context_str, message=message)

# #     raw_answer = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
# #     return {"answer": raw_answer}


# # # ---------------------------------------------------------
# # # Node 5: self_reflect
# # # ---------------------------------------------------------
# # def self_reflect_node(state: AgentState) -> Dict[str, Any]:
# #     answer = state.get("answer", "")
# #     chunks = state.get("retrieved_chunks", [])

# #     if answer == "I don't have relevant information on that right now.":
# #         return {}

# #     context_str = "\n".join([c.get("content", "") for c in chunks])
# #     reflect_prompt = SELF_REFLECT_PROMPT.format(context=context_str, answer=answer)

# #     reflection = get_llm_response(prompt=reflect_prompt)

# #     if "UNGROUNDED" in reflection:
# #         message = state.get("message", "")
# #         intent = state.get("intent", "general_qa")
# #         uploaded_text = state.get("uploaded_text", "")

# #         stricter_context = context_str + "\n\nCRITICAL: DO NOT ADD ANY EXTRA CLAIMS NOT STATED ABOVE."
# #         if intent == "document_review":
# #             prompt = DOCUMENT_REVIEW_PROMPT.format(context=stricter_context, uploaded_text=uploaded_text, message=message)
# #         else:
# #             prompt = GENERAL_QA_PROMPT.format(context=stricter_context, message=message)

# #         regenerated = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
# #         return {"answer": regenerated}

# #     return {}


# # # ---------------------------------------------------------
# # # Node 6: finalize
# # # ---------------------------------------------------------
# # def finalize_node(state: AgentState) -> Dict[str, Any]:
# #     raw_answer = state.get("answer", "")
# #     chunks = state.get("retrieved_chunks", [])

# #     if raw_answer == "I don't have relevant information on that right now.":
# #         return {"answer": raw_answer, "sources": [], "follow_ups": []}

# #     sources = []
# #     for c in chunks:
# #         st = c.get("source_title")
# #         if st and st not in sources:
# #             sources.append(st)

# #     follow_ups = []
# #     if "FOLLOW_UPS:" in raw_answer:
# #         parts = raw_answer.split("FOLLOW_UPS:")
# #         clean_answer = parts[0].strip()
# #         chips_str = parts[1].strip()
# #         chips = [c.strip(" -*?123456789.") + "?" for c in re.split(r'[|\n]', chips_str) if c.strip()]
# #         follow_ups = [re.sub(r'\?+$', '?', c) for c in chips if len(c) > 3][:3]
# #     else:
# #         clean_answer = raw_answer

# #     if not follow_ups:
# #         follow_ups = [
# #             "What are the step-by-step requirements?",
# #             "How do I structure my market positioning?",
# #             "What key metrics should I track first?"
# #         ]

# #     return {
# #         "answer": clean_answer,
# #         "sources": sources,
# #         "follow_ups": follow_ups
# #     }


# # # ---------------------------------------------------------
# # # LangGraph StateGraph Construction
# # # ---------------------------------------------------------
# # def build_agent_graph():
# #     workflow = StateGraph(AgentState)

# #     workflow.add_node("classify_intent", classify_intent_node)
# #     workflow.add_node("clarify_response", clarify_response_node)
# #     workflow.add_node("retrieve", retrieve_node)
# #     workflow.add_node("relevance_check", relevance_check_node)
# #     workflow.add_node("out_of_scope_response", out_of_scope_response_node)
# #     workflow.add_node("generate", generate_node)
# #     workflow.add_node("self_reflect", self_reflect_node)
# #     workflow.add_node("finalize", finalize_node)

# #     workflow.set_entry_point("classify_intent")

# #     workflow.add_conditional_edges(
# #         "classify_intent",
# #         route_after_classify,
# #         {"clarify_response": "clarify_response", "retrieve": "retrieve"}
# #     )

# #     workflow.add_edge("clarify_response", END)
# #     workflow.add_edge("retrieve", "relevance_check")

# #     workflow.add_conditional_edges(
# #         "relevance_check",
# #         route_after_relevance,
# #         {"generate": "generate", "out_of_scope_response": "out_of_scope_response"}
# #     )

# #     workflow.add_edge("generate", "self_reflect")
# #     workflow.add_edge("self_reflect", "finalize")
# #     workflow.add_edge("out_of_scope_response", END)
# #     workflow.add_edge("finalize", END)

# #     return workflow.compile()


# # app_graph = build_agent_graph()


# import re
# from typing import Dict, List, Any, TypedDict, Optional
# from langgraph.graph import StateGraph, END
# from retrieval import search, MIN_RELEVANCE_THRESHOLD, detect_domain
# from prompts import (
#     SYSTEM_PROMPT,
#     GENERAL_QA_PROMPT,
#     IDEA_COMPARISON_PROMPT,
#     FORM_HELPER_PROMPT,
#     DOCUMENT_REVIEW_PROMPT,
#     SELF_REFLECT_PROMPT
# )
# from llm import get_llm_response


# class AgentState(TypedDict):
#     message: str
#     uploaded_text: Optional[str]
#     domain: Optional[str]
#     previous_domain: Optional[str]   # NEW: carried from the prior turn
#     intent: str
#     retrieved_chunks: List[Dict[str, Any]]
#     relevance_ok: bool
#     answer: str
#     sources: List[str]
#     follow_ups: List[str]


# # NOTE: removed "how can i proceed" and "get started" — these are too
# # generic and were firing mid-conversation on follow-up turns that had
# # valid carried-over context
# VAGUE_BUSINESS_PHRASES = [
#     "start a business", "start my business", "want to start a business",
#     "begin a business", "build a tech", "build a software", "software product",
# ]

# # NOTE: added "compare to" / "compared to" so comparison follow-ups route
# # correctly even without a domain keyword in the same sentence
# COMPARISON_KEYWORDS = [
#     "vs", "compare", "compare to", "compared to", "difference between",
#     "better than", "which idea", "choice",
# ]


# # ---------------------------------------------------------
# # Node 1: classify_intent
# # ---------------------------------------------------------
# def classify_intent_node(state: AgentState) -> Dict[str, Any]:
#     message = (state.get("message") or "").strip().lower()
#     uploaded_text = state.get("uploaded_text")
#     previous_domain = state.get("previous_domain")
#     previous_role = state.get("previous_role")  # NEW

#     detected_domain = detect_domain(state.get("message", ""))
#     detected_role = detect_role(state.get("message", ""))  # NEW

#     domain = detected_domain or previous_domain
#     role = detected_role or previous_role  # NEW — carries "web_developer" forward

#     # ... rest of intent classification same as before ...

#     return {"intent": intent_value, "domain": domain, "role": role}

# def route_after_classify(state: AgentState) -> str:
#     if state.get("intent") == "clarify":
#         return "clarify_response"
#     return "retrieve"


# def clarify_response_node(state: AgentState) -> Dict[str, Any]:
#     return {
#         "answer": "What kind of business are you thinking about — a product, a service, freelancing, or something local like a shop? That'll help me point you to the right next steps.",
#         "sources": [],
#         "follow_ups": [
#             "I want to build a tech/software product",
#             "I want to start freelancing",
#             "I want to open a local shop or food business",
#         ]
#     }


# # ---------------------------------------------------------
# # Node 2: retrieve
# # ---------------------------------------------------------
# def retrieve_node(state: AgentState) -> Dict[str, Any]:
#     message = state.get("message", "")
#     domain = state.get("domain")
#     role = state.get("role")  # NEW

#     query = message
#     if role:
#         # inject the role into the query so retrieval stays anchored to it
#         query = f"{message} ({role.replace('_', ' ')})"

#     chunks = search(query, domain=domain, k=3)
#     return {"retrieved_chunks": chunks}

# # ---------------------------------------------------------
# # Node 3: relevance_check
# # ---------------------------------------------------------
# def relevance_check_node(state: AgentState) -> Dict[str, Any]:
#     chunks = state.get("retrieved_chunks", [])
#     intent = state.get("intent", "general_qa")

#     if not chunks:
#         return {"relevance_ok": False}

#     if intent == "document_review":
#         return {"relevance_ok": True}

#     max_score = max((c.get("score", 0.0) for c in chunks), default=0.0)
#     relevance_ok = max_score >= MIN_RELEVANCE_THRESHOLD

#     return {"relevance_ok": relevance_ok}


# def route_after_relevance(state: AgentState) -> str:
#     if state.get("relevance_ok", False):
#         return "generate"
#     return "out_of_scope_response"


# def out_of_scope_response_node(state: AgentState) -> Dict[str, Any]:
#     return {
#         "answer": "I don't have relevant information on that right now.",
#         "sources": [],
#         "follow_ups": []
#     }


# # ---------------------------------------------------------
# # Node 4: generate
# # ---------------------------------------------------------
# def generate_node(state: AgentState) -> Dict[str, Any]:
#     intent = state.get("intent", "general_qa")
#     message = state.get("message", "")
#     uploaded_text = state.get("uploaded_text", "")
#     chunks = state.get("retrieved_chunks", [])
#     user_domain = state.get("domain")

#     chunk_domains = list(set(c.get("domain") for c in chunks if c.get("domain")))
#     coherence_notice = ""
#     if len(chunk_domains) > 1 and not user_domain:
#         coherence_notice = (
#             f"\n\nCOHERENCE CHECK NOTICE: The retrieved chunks span multiple distinct sub-topics "
#             f"({', '.join(chunk_domains)}). Since the user did not specify a particular industry, "
#             f"DO NOT combine unrelated sub-topic details together into one answer. Either ask a "
#             f"clarifying question first, or provide only general-purpose steps and skip "
#             f"industry-specific details."
#         )

#     context_str = "\n\n".join([
#         f"Source [{c.get('source_title', 'Guidance')}]: {c.get('content', '')}"
#         for c in chunks
#     ]) + coherence_notice

#     if intent == "document_review":
#         prompt = DOCUMENT_REVIEW_PROMPT.format(
#             context=context_str,
#             uploaded_text=uploaded_text or "No document text uploaded.",
#             message=message
#         )
#     elif intent == "idea_comparison":
#         prompt = IDEA_COMPARISON_PROMPT.format(context=context_str, message=message)
#     elif intent == "form_helper":
#         prompt = FORM_HELPER_PROMPT.format(context=context_str, message=message)
#     else:
#         prompt = GENERAL_QA_PROMPT.format(context=context_str, message=message)

#     raw_answer = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
#     return {"answer": raw_answer}


# # ---------------------------------------------------------
# # Node 5: self_reflect
# # ---------------------------------------------------------
# def self_reflect_node(state: AgentState) -> Dict[str, Any]:
#     answer = state.get("answer", "")
#     chunks = state.get("retrieved_chunks", [])

#     if answer == "I don't have relevant information on that right now.":
#         return {}

#     context_str = "\n".join([c.get("content", "") for c in chunks])
#     reflect_prompt = SELF_REFLECT_PROMPT.format(context=context_str, answer=answer)

#     reflection = get_llm_response(prompt=reflect_prompt)

#     if "UNGROUNDED" in reflection:
#         message = state.get("message", "")
#         intent = state.get("intent", "general_qa")
#         uploaded_text = state.get("uploaded_text", "")

#         stricter_context = context_str + "\n\nCRITICAL: DO NOT ADD ANY EXTRA CLAIMS NOT STATED ABOVE."
#         if intent == "document_review":
#             prompt = DOCUMENT_REVIEW_PROMPT.format(context=stricter_context, uploaded_text=uploaded_text, message=message)
#         else:
#             prompt = GENERAL_QA_PROMPT.format(context=stricter_context, message=message)

#         regenerated = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
#         return {"answer": regenerated}

#     return {}


# # ---------------------------------------------------------
# # Node 6: finalize
# # ---------------------------------------------------------
# def finalize_node(state: AgentState) -> Dict[str, Any]:
#     raw_answer = state.get("answer", "")
#     chunks = state.get("retrieved_chunks", [])

#     if raw_answer == "I don't have relevant information on that right now.":
#         return {"answer": raw_answer, "sources": [], "follow_ups": []}

#     sources = []
#     for c in chunks:
#         st = c.get("source_title")
#         if st and st not in sources:
#             sources.append(st)

#     follow_ups = []
#     if "FOLLOW_UPS:" in raw_answer:
#         parts = raw_answer.split("FOLLOW_UPS:")
#         clean_answer = parts[0].strip()
#         chips_str = parts[1].strip()
#         chips = [c.strip(" -*?123456789.") + "?" for c in re.split(r'[|\n]', chips_str) if c.strip()]
#         follow_ups = [re.sub(r'\?+$', '?', c) for c in chips if len(c) > 3][:3]
#     else:
#         clean_answer = raw_answer

#     if not follow_ups:
#         follow_ups = [
#             "What are the step-by-step requirements?",
#             "How do I structure my market positioning?",
#             "What key metrics should I track first?"
#         ]

#     return {
#         "answer": clean_answer,
#         "sources": sources,
#         "follow_ups": follow_ups
#     }


# # ---------------------------------------------------------
# # LangGraph StateGraph Construction
# # ---------------------------------------------------------
# def build_agent_graph():
#     workflow = StateGraph(AgentState)

#     workflow.add_node("classify_intent", classify_intent_node)
#     workflow.add_node("clarify_response", clarify_response_node)
#     workflow.add_node("retrieve", retrieve_node)
#     workflow.add_node("relevance_check", relevance_check_node)
#     workflow.add_node("out_of_scope_response", out_of_scope_response_node)
#     workflow.add_node("generate", generate_node)
#     workflow.add_node("self_reflect", self_reflect_node)
#     workflow.add_node("finalize", finalize_node)

#     workflow.set_entry_point("classify_intent")

#     workflow.add_conditional_edges(
#         "classify_intent",
#         route_after_classify,
#         {"clarify_response": "clarify_response", "retrieve": "retrieve"}
#     )

#     workflow.add_edge("clarify_response", END)
#     workflow.add_edge("retrieve", "relevance_check")

#     workflow.add_conditional_edges(
#         "relevance_check",
#         route_after_relevance,
#         {"generate": "generate", "out_of_scope_response": "out_of_scope_response"}
#     )

#     workflow.add_edge("generate", "self_reflect")
#     workflow.add_edge("self_reflect", "finalize")
#     workflow.add_edge("out_of_scope_response", END)
#     workflow.add_edge("finalize", END)

#     return workflow.compile()


# app_graph = build_agent_graph()


# import re
# from typing import Dict, List, Any, TypedDict, Optional
# from langgraph.graph import StateGraph, END
# from retrieval import search, MIN_RELEVANCE_THRESHOLD, detect_domain, detect_role
# from prompts import (
#     SYSTEM_PROMPT,
#     GENERAL_QA_PROMPT,
#     IDEA_COMPARISON_PROMPT,
#     FORM_HELPER_PROMPT,
#     DOCUMENT_REVIEW_PROMPT,
#     SUMMARIZE_PROMPT,
#     SELF_REFLECT_PROMPT
# )
# from llm import get_llm_response


# class AgentState(TypedDict):
#     message: str
#     uploaded_text: Optional[str]
#     uploaded_files: Optional[List[Dict[str, str]]]
#     domain: Optional[str]
#     previous_domain: Optional[str]
#     role: Optional[str]
#     previous_role: Optional[str]
#     intent: str
#     retrieved_chunks: List[Dict[str, Any]]
#     relevance_ok: bool
#     answer: str
#     sources: List[str]
#     follow_ups: List[str]


# VAGUE_BUSINESS_PHRASES = [
#     "start a business", "start my business", "want to start a business",
#     "begin a business", "build a tech", "build a software", "software product",
# ]

# COMPARISON_KEYWORDS = [
#     "vs", "compare", "compare to", "compared to", "difference between",
#     "better than", "which idea", "choice",
# ]

# REVIEW_KEYWORDS = ["review", "improve", "evaluate", "feedback", "critique", "pitch deck", "portfolio", "check"]

# FORM_KEYWORDS = ["scheme", "udyam", "dpiit", "samridh", "form", "register", "registration", "legal", "msme", "apply", "grant", "subsidy", "document required"]


# # ---------------------------------------------------------
# # Node 1: classify_intent
# # ---------------------------------------------------------
# def classify_intent_node(state: AgentState) -> Dict[str, Any]:
#     message = (state.get("message") or "").strip().lower()
#     uploaded_text = state.get("uploaded_text")
#     uploaded_files = state.get("uploaded_files") or []
#     previous_domain = state.get("previous_domain")
#     previous_role = state.get("previous_role")

#     detected_domain = detect_domain(state.get("message", ""))
#     detected_role = detect_role(state.get("message", ""))

#     domain = detected_domain or previous_domain
#     role = detected_role or previous_role

#     is_vague = any(phrase in message for phrase in VAGUE_BUSINESS_PHRASES)
#     file_count = len([f for f in uploaded_files if isinstance(f, dict) and f.get("extracted_text")])
#     summarize_keywords = ["summarize", "summary", "summarise"]
#     wants_summary = any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in summarize_keywords)

#     if file_count > 0 and wants_summary:
#         if file_count == 1:
#             intent_value = "summarize"
#         else:
#             selected_file = None
#             for f in uploaded_files:
#                 filename = f.get("filename", "").lower()
#                 if filename and filename in message:
#                     selected_file = f
#                     break
#             if selected_file:
#                 return {
#                     "intent": "summarize",
#                     "domain": domain,
#                     "role": role,
#                     "uploaded_text": selected_file.get("extracted_text") or uploaded_text,
#                     "uploaded_files": uploaded_files
#                 }
#             intent_value = "summarize_clarify"
#     elif is_vague and domain is None:
#         intent_value = "clarify"
#     elif uploaded_text and any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in REVIEW_KEYWORDS):
#         intent_value = "document_review"
#     elif any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in COMPARISON_KEYWORDS):
#         intent_value = "idea_comparison"
#     elif any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in FORM_KEYWORDS):
#         intent_value = "form_helper"
#     else:
#         intent_value = "general_qa"

#     return {"intent": intent_value, "domain": domain, "role": role, "uploaded_files": uploaded_files}


# def route_after_classify(state: AgentState) -> str:
#     if state.get("intent") == "clarify":
#         return "clarify_response"
#     return "retrieve"


# def clarify_response_node(state: AgentState) -> Dict[str, Any]:
#     uploaded_files = state.get("uploaded_files") or []
#     if state.get("intent") == "summarize_clarify" and len(uploaded_files) > 1:
#         filenames = [f.get("filename", "Unnamed") for f in uploaded_files]
#         follow_ups = [f"Summarize {name}" for name in filenames[:3]]
#         return {
#             "answer": f"I see multiple files attached: {', '.join(filenames)}. Which one should I summarize?",
#             "sources": [],
#             "follow_ups": follow_ups
#         }

#     return {
#         "answer": "What kind of business are you thinking about — a product, a service, freelancing, or something local like a shop? That'll help me point you to the right next steps.",
#         "sources": [],
#         "follow_ups": [
#             "I want to build a tech/software product",
#             "I want to start freelancing",
#             "I want to open a local shop or food business",
#         ]
#     }


# # ---------------------------------------------------------
# # Node 2: retrieve
# # ---------------------------------------------------------
# def retrieve_node(state: AgentState) -> Dict[str, Any]:
#     message = state.get("message", "")
#     domain = state.get("domain")
#     role = state.get("role")
#     intent = state.get("intent", "general_qa")

#     if intent == "summarize":
#         return {"retrieved_chunks": []}

#     if intent == "document_review":
#         query = f"pitch deck portfolio guidance structure essentials {message}"
#         chunks = search(query, domain="general", k=5)
#         if not chunks:
#             chunks = search("pitch deck portfolio guidance", domain=None, k=5)
#         return {"retrieved_chunks": chunks}

#     query = message
#     if role:
#         query = f"{message} ({role.replace('_', ' ')})"

#     chunks = search(query, domain=domain, k=3)
#     return {"retrieved_chunks": chunks}


# # ---------------------------------------------------------
# # Node 3: relevance_check
# # ---------------------------------------------------------
# def relevance_check_node(state: AgentState) -> Dict[str, Any]:
#     chunks = state.get("retrieved_chunks", [])
#     intent = state.get("intent", "general_qa")

#     if not chunks:
#         return {"relevance_ok": False}

#     if intent == "document_review":
#         return {"relevance_ok": True}

#     max_score = max((c.get("score", 0.0) for c in chunks), default=0.0)
#     relevance_ok = max_score >= MIN_RELEVANCE_THRESHOLD

#     return {"relevance_ok": relevance_ok}


# def route_after_relevance(state: AgentState) -> str:
#     if state.get("relevance_ok", False):
#         return "generate"
#     return "out_of_scope_response"


# def out_of_scope_response_node(state: AgentState) -> Dict[str, Any]:
#     return {
#         "answer": "I don't have relevant information on that right now.",
#         "sources": [],
#         "follow_ups": []
#     }


# # ---------------------------------------------------------
# # Node 4: generate
# # ---------------------------------------------------------
# def generate_node(state: AgentState) -> Dict[str, Any]:
#     intent = state.get("intent", "general_qa")
#     message = state.get("message", "")
#     uploaded_text = state.get("uploaded_text", "")
#     chunks = state.get("retrieved_chunks", [])
#     user_domain = state.get("domain")

#     chunk_domains = list(set(c.get("domain") for c in chunks if c.get("domain")))
#     coherence_notice = ""
#     if len(chunk_domains) > 1 and not user_domain:
#         coherence_notice = (
#             f"\n\nCOHERENCE CHECK NOTICE: The retrieved chunks span multiple distinct sub-topics "
#             f"({', '.join(chunk_domains)}). Since the user did not specify a particular industry, "
#             f"DO NOT combine unrelated sub-topic details together into one answer. Either ask a "
#             f"clarifying question first, or provide only general-purpose steps and skip "
#             f"industry-specific details."
#         )

#     context_str = "\n\n".join([
#         f"Source [{c.get('source_title', 'Guidance')}]: {c.get('content', '')}"
#         for c in chunks
#     ]) + coherence_notice

#     if intent == "summarize":
#         prompt = SUMMARIZE_PROMPT.format(uploaded_text=uploaded_text or "", message=message)
#     elif intent == "document_review":
#         prompt = DOCUMENT_REVIEW_PROMPT.format(
#             context=context_str,
#             uploaded_text=uploaded_text or "No document text uploaded.",
#             message=message
#         )
#     elif intent == "idea_comparison":
#         prompt = IDEA_COMPARISON_PROMPT.format(context=context_str, message=message)
#     elif intent == "form_helper":
#         prompt = FORM_HELPER_PROMPT.format(context=context_str, message=message)
#     else:
#         prompt = GENERAL_QA_PROMPT.format(context=context_str, message=message)

#     raw_answer = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
#     return {"answer": raw_answer}


# # ---------------------------------------------------------
# # Node 5: self_reflect
# # ---------------------------------------------------------
# def self_reflect_node(state: AgentState) -> Dict[str, Any]:
#     answer = state.get("answer", "")
#     chunks = state.get("retrieved_chunks", [])

#     if answer == "I don't have relevant information on that right now.":
#         return {}

#     context_str = "\n".join([c.get("content", "") for c in chunks])
#     reflect_prompt = SELF_REFLECT_PROMPT.format(context=context_str, answer=answer)

#     reflection = get_llm_response(prompt=reflect_prompt)

#     if "UNGROUNDED" in reflection:
#         message = state.get("message", "")
#         intent = state.get("intent", "general_qa")
#         uploaded_text = state.get("uploaded_text", "")

#         stricter_context = context_str + "\n\nCRITICAL: DO NOT ADD ANY EXTRA CLAIMS NOT STATED ABOVE."
#         if intent == "document_review":
#             prompt = DOCUMENT_REVIEW_PROMPT.format(context=stricter_context, uploaded_text=uploaded_text, message=message)
#         else:
#             prompt = GENERAL_QA_PROMPT.format(context=stricter_context, message=message)

#         regenerated = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
#         return {"answer": regenerated}

#     return {}


# # ---------------------------------------------------------
# # Node 6: finalize
# # ---------------------------------------------------------
# def finalize_node(state: AgentState) -> Dict[str, Any]:
#     raw_answer = state.get("answer", "")
#     chunks = state.get("retrieved_chunks", [])

#     if raw_answer == "I don't have relevant information on that right now.":
#         return {"answer": raw_answer, "sources": [], "follow_ups": []}

#     sources = []
#     for c in chunks:
#         st = c.get("source_title")
#         if st and st not in sources:
#             sources.append(st)

#     follow_ups = []
#     if "FOLLOW_UPS:" in raw_answer:
#         parts = raw_answer.split("FOLLOW_UPS:")
#         clean_answer = parts[0].strip()
#         chips_str = parts[1].strip()
#         chips = [c.strip(" -*?123456789.") + "?" for c in re.split(r'[|\n]', chips_str) if c.strip()]
#         follow_ups = [re.sub(r'\?+$', '?', c) for c in chips if len(c) > 3][:3]
#     else:
#         clean_answer = raw_answer

#     if not follow_ups:
#         follow_ups = [
#             "What are the step-by-step requirements?",
#             "How do I structure my market positioning?",
#             "What key metrics should I track first?"
#         ]

#     return {
#         "answer": clean_answer,
#         "sources": sources,
#         "follow_ups": follow_ups
#     }


# # ---------------------------------------------------------
# # LangGraph StateGraph Construction
# # ---------------------------------------------------------
# def build_agent_graph():
#     workflow = StateGraph(AgentState)

#     workflow.add_node("classify_intent", classify_intent_node)
#     workflow.add_node("clarify_response", clarify_response_node)
#     workflow.add_node("retrieve", retrieve_node)
#     workflow.add_node("relevance_check", relevance_check_node)
#     workflow.add_node("out_of_scope_response", out_of_scope_response_node)
#     workflow.add_node("generate", generate_node)
#     workflow.add_node("self_reflect", self_reflect_node)
#     workflow.add_node("finalize", finalize_node)

#     workflow.set_entry_point("classify_intent")

#     workflow.add_conditional_edges(
#         "classify_intent",
#         route_after_classify,
#         {"clarify_response": "clarify_response", "retrieve": "retrieve"}
#     )

#     workflow.add_edge("clarify_response", END)
#     workflow.add_edge("retrieve", "relevance_check")

#     workflow.add_conditional_edges(
#         "relevance_check",
#         route_after_relevance,
#         {"generate": "generate", "out_of_scope_response": "out_of_scope_response"}
#     )

#     workflow.add_edge("generate", "self_reflect")
#     workflow.add_edge("self_reflect", "finalize")
#     workflow.add_edge("out_of_scope_response", END)
#     workflow.add_edge("finalize", END)

#     return workflow.compile()


# app_graph = build_agent_graph()


import re
from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from retrieval import search, MIN_RELEVANCE_THRESHOLD, detect_domain, detect_role
from prompts import (
    SYSTEM_PROMPT,
    GENERAL_QA_PROMPT,
    IDEA_COMPARISON_PROMPT,
    FORM_HELPER_PROMPT,
    DOCUMENT_REVIEW_PROMPT,
    SUMMARIZE_PROMPT,
    SELF_REFLECT_PROMPT
)
from llm import get_llm_response


class AgentState(TypedDict):
    message: str
    uploaded_text: Optional[str]
    uploaded_files: Optional[List[Dict[str, str]]]
    domain: Optional[str]
    previous_domain: Optional[str]
    role: Optional[str]
    previous_role: Optional[str]
    intent: str
    retrieved_chunks: List[Dict[str, Any]]
    relevance_ok: bool
    answer: str
    sources: List[str]
    follow_ups: List[str]


VAGUE_BUSINESS_PHRASES = [
    "start a business", "start my business", "want to start a business",
    "begin a business", "build a tech", "build a software", "software product",
]

COMPARISON_KEYWORDS = [
    "vs", "compare", "compare to", "compared to", "difference between",
    "better than", "which idea", "choice",
]

REVIEW_KEYWORDS = ["review", "improve", "evaluate", "feedback", "critique", "pitch deck", "portfolio", "check"]

FORM_KEYWORDS = ["scheme", "udyam", "dpiit", "samridh", "form", "register", "registration", "legal", "msme", "apply", "grant", "subsidy", "document required"]


# ---------------------------------------------------------
# Node 1: classify_intent (Router Agent)
# ---------------------------------------------------------
def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    message = (state.get("message") or "").strip().lower()
    uploaded_text = state.get("uploaded_text")
    uploaded_files = state.get("uploaded_files") or []
    previous_domain = state.get("previous_domain")
    previous_role = state.get("previous_role")

    detected_domain = detect_domain(state.get("message", ""))
    detected_role = detect_role(state.get("message", ""))

    domain = detected_domain or previous_domain
    role = detected_role or previous_role

    is_vague = any(phrase in message for phrase in VAGUE_BUSINESS_PHRASES)
    file_count = len([f for f in uploaded_files if isinstance(f, dict) and f.get("extracted_text")])
    summarize_keywords = ["summarize", "summary", "summarise"]
    wants_summary = any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in summarize_keywords)

    if file_count > 0 and wants_summary:
        if file_count == 1:
            single_file = next(f for f in uploaded_files if f.get("extracted_text"))
            return {
                "intent": "summarize",
                "domain": domain,
                "role": role,
                "uploaded_text": single_file.get("extracted_text"),
                "uploaded_files": uploaded_files
            }
        else:
            selected_file = None
            for f in uploaded_files:
                filename = f.get("filename", "").lower()
                if filename and filename in message:
                    selected_file = f
                    break
            if selected_file:
                return {
                    "intent": "summarize",
                    "domain": domain,
                    "role": role,
                    "uploaded_text": selected_file.get("extracted_text") or uploaded_text,
                    "uploaded_files": uploaded_files
                }
            return {
                "intent": "summarize_clarify",
                "domain": domain,
                "role": role,
                "uploaded_files": uploaded_files
            }

    if is_vague and domain is None:
        intent_value = "clarify"
    elif uploaded_text and any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in REVIEW_KEYWORDS):
        intent_value = "document_review"
    elif any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in COMPARISON_KEYWORDS):
        intent_value = "idea_comparison"
    elif any(re.search(rf"\b{re.escape(kw)}\b", message) for kw in FORM_KEYWORDS):
        intent_value = "form_helper"
    else:
        intent_value = "general_qa"

    return {"intent": intent_value, "domain": domain, "role": role, "uploaded_files": uploaded_files}


def route_after_classify(state: AgentState) -> str:
    if state.get("intent") in ("clarify", "summarize_clarify"):
        return "clarify_response"
    return "retrieve"


def clarify_response_node(state: AgentState) -> Dict[str, Any]:
    uploaded_files = state.get("uploaded_files") or []
    if state.get("intent") == "summarize_clarify" and len(uploaded_files) > 1:
        filenames = [f.get("filename", "Unnamed") for f in uploaded_files]
        follow_ups = [f"Summarize {name}" for name in filenames[:3]]
        return {
            "answer": f"I see multiple files attached: {', '.join(filenames)}. Which one should I summarize?",
            "sources": [],
            "follow_ups": follow_ups
        }

    return {
        "answer": "What kind of business are you thinking about — a product, a service, freelancing, or something local like a shop? That'll help me point you to the right next steps.",
        "sources": [],
        "follow_ups": [
            "I want to build a tech/software product",
            "I want to start freelancing",
            "I want to open a local shop or food business",
        ]
    }


# ---------------------------------------------------------
# Node 2: retrieve (Research Agent)
# ---------------------------------------------------------
def retrieve_node(state: AgentState) -> Dict[str, Any]:
    message = state.get("message", "")
    domain = state.get("domain")
    role = state.get("role")
    intent = state.get("intent", "general_qa")

    if intent == "summarize":
        # No knowledge-base retrieval needed — the source is the uploaded file
        return {"retrieved_chunks": []}

    if intent == "document_review":
        query = f"pitch deck portfolio guidance structure essentials {message}"
        chunks = search(query, domain="general", k=5)
        if not chunks:
            chunks = search("pitch deck portfolio guidance", domain=None, k=5)
        return {"retrieved_chunks": chunks}

    query = message
    if role:
        query = f"{message} ({role.replace('_', ' ')})"

    chunks = search(query, domain=domain, k=3)
    return {"retrieved_chunks": chunks}


# ---------------------------------------------------------
# Node 3: relevance_check (Quality Gate Agent)
# ---------------------------------------------------------
def relevance_check_node(state: AgentState) -> Dict[str, Any]:
    chunks = state.get("retrieved_chunks", [])
    intent = state.get("intent", "general_qa")

    # summarize and document_review don't depend on retrieved chunks to proceed —
    # summarize uses uploaded_text directly, document_review already handled below
    if intent in ("summarize", "document_review"):
        return {"relevance_ok": True}

    if not chunks:
        return {"relevance_ok": False}

    max_score = max((c.get("score", 0.0) for c in chunks), default=0.0)
    relevance_ok = max_score >= MIN_RELEVANCE_THRESHOLD

    return {"relevance_ok": relevance_ok}


def route_after_relevance(state: AgentState) -> str:
    if state.get("relevance_ok", False):
        return "generate"
    return "out_of_scope_response"


def out_of_scope_response_node(state: AgentState) -> Dict[str, Any]:
    return {
        "answer": "I don't have relevant information on that right now.",
        "sources": [],
        "follow_ups": []
    }


# ---------------------------------------------------------
# Node 4: generate (Advisor Agent)
# ---------------------------------------------------------
def generate_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent", "general_qa")
    message = state.get("message", "")
    uploaded_text = state.get("uploaded_text", "")
    chunks = state.get("retrieved_chunks", [])
    user_domain = state.get("domain")

    chunk_domains = list(set(c.get("domain") for c in chunks if c.get("domain")))
    coherence_notice = ""
    if len(chunk_domains) > 1 and not user_domain:
        coherence_notice = (
            f"\n\nCOHERENCE CHECK NOTICE: The retrieved chunks span multiple distinct sub-topics "
            f"({', '.join(chunk_domains)}). Since the user did not specify a particular industry, "
            f"DO NOT combine unrelated sub-topic details together into one answer. Either ask a "
            f"clarifying question first, or provide only general-purpose steps and skip "
            f"industry-specific details."
        )

    context_str = "\n\n".join([
        f"Source [{c.get('source_title', 'Guidance')}]: {c.get('content', '')}"
        for c in chunks
    ]) + coherence_notice

    if intent == "summarize":
        prompt = SUMMARIZE_PROMPT.format(uploaded_text=uploaded_text or "", message=message)
    elif intent == "document_review":
        prompt = DOCUMENT_REVIEW_PROMPT.format(
            context=context_str,
            uploaded_text=uploaded_text or "No document text uploaded.",
            message=message
        )
    elif intent == "idea_comparison":
        prompt = IDEA_COMPARISON_PROMPT.format(context=context_str, message=message)
    elif intent == "form_helper":
        prompt = FORM_HELPER_PROMPT.format(context=context_str, message=message)
    else:
        prompt = GENERAL_QA_PROMPT.format(context=context_str, message=message)

    raw_answer = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
    return {"answer": raw_answer}


# ---------------------------------------------------------
# Node 5: self_reflect (Critic Agent)
# ---------------------------------------------------------
def self_reflect_node(state: AgentState) -> Dict[str, Any]:
    answer = state.get("answer", "")
    chunks = state.get("retrieved_chunks", [])
    intent = state.get("intent", "general_qa")

    # Summarize has no retrieved-chunk context to check against — its
    # grounding is the uploaded file itself, not the knowledge base —
    # so skip the ungrounded-claims check for this intent
    if answer == "I don't have relevant information on that right now." or intent == "summarize":
        return {}

    context_str = "\n".join([c.get("content", "") for c in chunks])
    reflect_prompt = SELF_REFLECT_PROMPT.format(context=context_str, answer=answer)

    reflection = get_llm_response(prompt=reflect_prompt)

    if "UNGROUNDED" in reflection:
        message = state.get("message", "")
        uploaded_text = state.get("uploaded_text", "")

        stricter_context = context_str + "\n\nCRITICAL: DO NOT ADD ANY EXTRA CLAIMS NOT STATED ABOVE."
        if intent == "document_review":
            prompt = DOCUMENT_REVIEW_PROMPT.format(context=stricter_context, uploaded_text=uploaded_text, message=message)
        else:
            prompt = GENERAL_QA_PROMPT.format(context=stricter_context, message=message)

        regenerated = get_llm_response(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        return {"answer": regenerated}

    return {}


# ---------------------------------------------------------
# Node 6: finalize (Formatter Agent)
# ---------------------------------------------------------
def finalize_node(state: AgentState) -> Dict[str, Any]:
    raw_answer = state.get("answer", "")
    chunks = state.get("retrieved_chunks", [])

    if raw_answer == "I don't have relevant information on that right now.":
        return {"answer": raw_answer, "sources": [], "follow_ups": []}

    sources = []
    for c in chunks:
        st = c.get("source_title")
        if st and st not in sources:
            sources.append(st)

    follow_ups = []
    if "FOLLOW_UPS:" in raw_answer:
        parts = raw_answer.split("FOLLOW_UPS:")
        clean_answer = parts[0].strip()
        chips_str = parts[1].strip()
        chips = [c.strip(" -*?123456789.") + "?" for c in re.split(r'[|\n]', chips_str) if c.strip()]
        follow_ups = [re.sub(r'\?+$', '?', c) for c in chips if len(c) > 3][:3]
    else:
        clean_answer = raw_answer

    if not follow_ups:
        follow_ups = [
            "What are the step-by-step requirements?",
            "How do I structure my market positioning?",
            "What key metrics should I track first?"
        ]

    return {
        "answer": clean_answer,
        "sources": sources,
        "follow_ups": follow_ups
    }


# ---------------------------------------------------------
# LangGraph StateGraph Construction
# ---------------------------------------------------------
def build_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("clarify_response", clarify_response_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("relevance_check", relevance_check_node)
    workflow.add_node("out_of_scope_response", out_of_scope_response_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("self_reflect", self_reflect_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {"clarify_response": "clarify_response", "retrieve": "retrieve"}
    )

    workflow.add_edge("clarify_response", END)
    workflow.add_edge("retrieve", "relevance_check")

    workflow.add_conditional_edges(
        "relevance_check",
        route_after_relevance,
        {"generate": "generate", "out_of_scope_response": "out_of_scope_response"}
    )

    workflow.add_edge("generate", "self_reflect")
    workflow.add_edge("self_reflect", "finalize")
    workflow.add_edge("out_of_scope_response", END)
    workflow.add_edge("finalize", END)

    return workflow.compile()


app_graph = build_agent_graph()