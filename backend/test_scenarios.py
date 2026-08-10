import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------------------------------------------------------
# STARTUP 1: AI Customer Support
# ---------------------------------------------------------
def test_startup1_idea_evaluation():
    resp = client.post("/chat", json={"message": "I want to build an AI chatbot that handles customer support for small e-commerce stores. Is this worth pursuing?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup1_skill_suggestion():
    resp = client.post("/chat", json={"message": "What skills do I actually need to build this?", "previous_domain": "startups"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup1_scheme_funding():
    resp = client.post("/chat", json={"message": "How do I get funding for this?", "previous_domain": "startups"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup1_steps_dpiit():
    resp = client.post("/chat", json={"message": "Okay, walk me through DPIIT recognition.", "previous_domain": "schemes"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup1_document_review():
    uploaded_text = (
        "Slide 1: Problem\nSmall e-commerce businesses lose customers due to slow support response times.\n"
        "Slide 2: Solution\nAn AI chatbot trained on product & policy docs.\n"
        "Slide 3: Product\nChat widget for Shopify.\n"
        "Slide 4: Team\nTwo co-founders."
    )
    resp = client.post("/chat", json={
        "message": "Can you review this and tell me what's missing?",
        "uploaded_text": uploaded_text
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "document_review"
    assert "answer" in data and len(data["answer"]) > 20


# ---------------------------------------------------------
# STARTUP 2: Delivery Route Optimization
# ---------------------------------------------------------
def test_startup2_idea_evaluation():
    resp = client.post("/chat", json={"message": "I have an idea for route-optimization software for small local delivery businesses. Good idea?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup2_comparison():
    resp = client.post("/chat", json={"message": "How does this compare to what's already out there?", "previous_domain": "startups"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup2_steps_to_proceed():
    resp = client.post("/chat", json={"message": "Okay so how do I actually get started?", "previous_domain": "startups"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_startup2_document_review():
    uploaded_text = "Idea: A dashboard for small local delivery businesses that automatically plans efficient delivery routes for their drivers."
    resp = client.post("/chat", json={
        "message": "Is this idea clear enough, or does it need work?",
        "uploaded_text": uploaded_text
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


# ---------------------------------------------------------
# FREELANCING 1: GenAI Developer
# ---------------------------------------------------------
def test_freelancing1_how_to_start():
    resp = client.post("/chat", json={"message": "I want to start freelancing as a GenAI developer, where do I begin?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_freelancing1_skill_suggestion():
    resp = client.post("/chat", json={"message": "What skills should I focus on?", "previous_domain": "freelancing"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_freelancing1_portfolio_review():
    uploaded_text = "I'm a self-taught developer with 8 months experience. Built a PDF chatbot with OpenAI API & vector search."
    resp = client.post("/chat", json={
        "message": "Can you look at this and tell me if I'm ready to start taking clients?",
        "uploaded_text": uploaded_text
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "document_review"
    assert "answer" in data and len(data["answer"]) > 20


def test_freelancing1_pricing():
    resp = client.post("/chat", json={"message": "How much should I charge for a first project?", "previous_domain": "freelancing"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


# ---------------------------------------------------------
# FREELANCING 2: Web Developer
# ---------------------------------------------------------
def test_freelancing2_how_to_start():
    resp = client.post("/chat", json={"message": "I want to freelance as a web developer, how do I start?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_freelancing2_portfolio_review():
    uploaded_text = "I've been doing web dev for 1.5 years. Built a photography landing page and booking form. Looking for paid clients."
    resp = client.post("/chat", json={
        "message": "Am I ready to take paid clients?",
        "uploaded_text": uploaded_text
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "document_review"
    assert "answer" in data and len(data["answer"]) > 20


def test_freelancing2_marketing():
    resp = client.post("/chat", json={"message": "How do I market myself to get clients?", "previous_domain": "freelancing"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20


def test_freelancing2_client_approach():
    resp = client.post("/chat", json={"message": "A potential client just messaged me. What should I ask them?", "previous_domain": "freelancing"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data and len(data["answer"]) > 20
