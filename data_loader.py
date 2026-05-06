"""
data_loader.py
Loads recycling rules and FAQ data from CSV files.
"""

import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_rules(filename="recycling_rules_plastics_only.csv") -> list[dict]:
    """Load recycling disposal rules from CSV."""
    path = os.path.join(DATA_DIR, filename)
    rules = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append({
                "id":           row.get("rule_id", "").strip(),
                "keywords":     row.get("item_keywords", "").strip(),
                "accepted":     row.get("accepted_in_plastic_only_bin", "").strip(),
                "title":        row.get("answer_title", "").strip(),
                "response":     row.get("chatbot_response", "").strip(),
                "prep":         row.get("preparation_steps", "").strip(),
                "redirect":     row.get("redirect_if_not_accepted", "").strip(),
                "escalation":   row.get("escalation_trigger", "").strip(),
            })
    return rules


def load_faq(filename="recycling_faq_plastics_only.csv") -> list[dict]:
    """Load FAQ entries from CSV."""
    path = os.path.join(DATA_DIR, filename)
    faqs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            faqs.append({
                "id":       row.get("faq_id", "").strip(),
                "keywords": row.get("question_keywords", "").strip(),
                "question": row.get("user_question", "").strip(),
                "short":    row.get("short_answer", "").strip(),
                "full":     row.get("full_chatbot_answer", "").strip(),
                "followup": row.get("follow_up_prompt", "").strip(),
            })
    return faqs
