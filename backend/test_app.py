import io
import pytest
from fastapi.testclient import TestClient
from main import app
from graph import classify_intent_node

client = TestClient(app)


def test_classify_intent_document_review():
    state = {
        "message": "Can you review my pitch deck and point out what's missing?",
        "uploaded_text": "Slide 1: Problem. Slide 2: Solution. Slide 3: Team.",
        "intent": "",
        "domain": None,
        "retrieved_chunks": [],
        "relevance_ok": False,
        "answer": "",
        "sources": [],
        "follow_ups": []
    }
    result = classify_intent_node(state)
    assert result["intent"] == "document_review"


def test_classify_intent_idea_comparison():
    state = {"message": "Compare freelance web dev vs building a SaaS app", "uploaded_text": None}
    result = classify_intent_node(state)
    assert result["intent"] == "idea_comparison"


def test_classify_intent_form_helper():
    state = {"message": "How do I apply for Udyam MSME scheme registration?", "uploaded_text": None}
    result = classify_intent_node(state)
    assert result["intent"] == "form_helper"


def test_classify_intent_general_qa():
    state = {"message": "What skills do I need to start as a freelance UI designer?", "uploaded_text": None}
    result = classify_intent_node(state)
    assert result["intent"] == "general_qa"


def test_chat_endpoint_grounded():
    response = client.post(
        "/chat",
        json={"message": "What is the Startup India Seed Fund scheme?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "intent" in data
    assert "follow_ups" in data
    assert isinstance(data["sources"], list)
    assert isinstance(data["follow_ups"], list)


def test_chat_endpoint_out_of_scope():
    response = client.post(
        "/chat",
        json={"message": "xyzqwertyunrelated random string query 999999"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "I don't have relevant information on that right now." in data["answer"]
    assert len(data["sources"]) == 0


def test_explore_endpoint():
    response = client.get("/explore/freelancing")
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "follow_ups" in data


def test_upload_txt_file():
    txt_content = b"Problem Statement: Freelancers struggle with invoices.\nSolution: Automated tool."
    files = {"file": ("pitch_deck.txt", txt_content, "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "pitch_deck.txt"
    assert "Freelancers struggle with invoices" in data["extracted_text"]


def test_upload_file_too_large():
    large_content = b"a" * (4 * 1024 * 1024)  # 4MB
    files = {"file": ("large_doc.txt", large_content, "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


def test_coherence_check_rule():
    # Ambiguous query without specified domain where retrieved chunks might span sub-topics
    response = client.post(
        "/chat",
        json={"message": "How do I get my first customers or clients?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # Verify response is valid and non-empty
    assert len(data["answer"]) > 10

