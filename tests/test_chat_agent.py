import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import pytest
from app.agents.nodes import (
    detect_language_heuristics, 
    detect_sentiment_heuristics, 
    classify_intent_heuristics
)
from app.agents.graph import route_from_detector, route_from_faq, END, support_graph

def test_language_heuristics():
    # Bangla text detection
    assert detect_language_heuristics("আমার নাম কি?") == "bn"
    
    # English text detection
    assert detect_language_heuristics("Where is my product package?") == "en"
    
    # Mixed Banglish text detection
    assert detect_language_heuristics("আমার order কোথায়?") == "mixed"

def test_sentiment_heuristics():
    # Negative triggers
    assert detect_sentiment_heuristics("এই সার্ভিসটি অত্যন্ত বাজে!") == "negative"
    assert detect_sentiment_heuristics("I hate this slow shipping delay") == "negative"
    
    # Positive triggers
    assert detect_sentiment_heuristics("অনেক সুন্দর ও উপকারী অ্যাপ") == "positive"
    assert detect_sentiment_heuristics("Thank you very much, great support") == "positive"
    
    # Neutral
    assert detect_sentiment_heuristics("হ্যালো কেমন আছেন?") == "neutral"

def test_intent_routing_heuristics():
    assert classify_intent_heuristics("পেমেন্ট করতে পারছি না কেন?") == "billing"
    assert classify_intent_heuristics("আমার প্রোডাক্ট কখন আসবে?") == "order"
    assert classify_intent_heuristics("হ্যালো") == "greeting"
    assert classify_intent_heuristics("সরাসরি এজেন্টের সাথে কথা বলুন") == "escalation"
    assert classify_intent_heuristics("বাজে ডেলিভারি নিয়ে অভিযোগ জানাতে চাই") == "complaint"
    assert classify_intent_heuristics("সাধারণ কোশ্চেন") == "faq"

def test_graph_routing_edges():
    # Mock states
    state1 = {"category": "billing"}
    assert route_from_detector(state1) == "billing"
    
    state2 = {"category": "faq"}
    assert route_from_detector(state2) == "faq"
    
    state3 = {"category": "escalation"}
    assert route_from_faq(state3) == "escalation"
    
    state4 = {"category": "faq"}
    assert route_from_faq(state4) == END
