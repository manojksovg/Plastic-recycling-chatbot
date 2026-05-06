"""
webapp.py
Website version of PlasticBot.

Run:
    pip install flask
    python webapp.py

Then open:
    http://127.0.0.1:5000

Expected project structure:
plasticbot/
├── chatbot.py
├── webapp.py
├── api_client.py
├── data_loader.py
├── matcher.py
├── reporter.py
├── data/
│   ├── recycling_rules_plastics_only.csv
│   └── recycling_faq_plastics_only.csv
└── templates/
    ├── index.html
    └── report.html
"""

from markupsafe import Markup, escape
from flask import Flask, render_template, request, redirect, url_for

from data_loader import load_rules, load_faq
from matcher import detect_intent, find_best_rule, find_best_faq
from api_client import call_claude
from reporter import create_record, all_records


app = Flask(__name__)

RULES = load_rules()
FAQS = load_faq()


def build_rule_context(rule: dict) -> str:
    return (
        f"RECYCLING RULE MATCH:\n"
        f"ID: {rule['id']}\n"
        f"Item keywords: {rule['keywords']}\n"
        f"Accepted: {rule['accepted']}\n"
        f"Title: {rule['title']}\n"
        f"Response: {rule['response']}\n"
        f"Preparation: {rule['prep']}\n"
        f"Redirect: {rule['redirect']}\n"
        f"Escalation: {rule['escalation']}"
    )


def build_faq_context(faq: dict) -> str:
    return (
        f"FAQ MATCH:\n"
        f"Question: {faq['question']}\n"
        f"Answer: {faq['full']}\n"
        f"Follow-up: {faq['followup']}"
    )


def rule_card(rule: dict) -> Markup:
    accepted = rule["accepted"].lower()

    if accepted == "yes":
        badge = "ACCEPTED"
        badge_class = "ok"
    elif accepted == "no":
        badge = "NOT ACCEPTED"
        badge_class = "no"
    else:
        badge = "CONDITIONAL"
        badge_class = "warn"

    html = f"""
    <div class="result-card">
        <div class="badge {badge_class}">{escape(badge)}</div>
        <h2>{escape(rule['title'])}</h2>
        <p>{escape(rule['response'])}</p>
    """

    if rule["prep"]:
        html += f"""
        <div class="mini-section">
            <strong>Preparation</strong>
            <p>{escape(rule['prep'])}</p>
        </div>
        """

    if rule["redirect"]:
        html += f"""
        <div class="mini-section">
            <strong>If not accepted</strong>
            <p>{escape(rule['redirect'])}</p>
        </div>
        """

    html += "</div>"
    return Markup(html)


def faq_card(faq: dict) -> Markup:
    html = f"""
    <div class="result-card">
        <div class="badge faq">FAQ</div>
        <h2>{escape(faq['question'])}</h2>
        <p>{escape(faq['full'])}</p>
    """
    if faq["followup"]:
        html += f'<p class="followup">{escape(faq["followup"])}</p>'
    html += "</div>"
    return Markup(html)


def get_answer(user_query: str):
    intent = detect_intent(user_query)
    context = ""
    local_card = None

    if intent == "report":
        return "report", None, None

    if intent == "disposal":
        rule = find_best_rule(user_query, RULES)
        if rule:
            local_card = rule_card(rule)
            context = build_rule_context(rule)
        else:
            faq = find_best_faq(user_query, FAQS)
            if faq:
                local_card = faq_card(faq)
                context = build_faq_context(faq)

    else:
        faq = find_best_faq(user_query, FAQS)
        if faq:
            local_card = faq_card(faq)
            context = build_faq_context(faq)
        else:
            rule = find_best_rule(user_query, RULES)
            if rule:
                local_card = rule_card(rule)
                context = build_rule_context(rule)

    ai_reply = call_claude(user_query, context)
    return "answer", local_card, ai_reply


@app.route("/", methods=["GET", "POST"])
def index():
    local_card = None
    ai_reply = None
    user_query = ""

    if request.method == "POST":
        user_query = request.form.get("query", "").strip()
        if user_query:
            result_type, local_card, ai_reply = get_answer(user_query)
            if result_type == "report":
                return redirect(url_for("report"))

    return render_template(
        "index.html",
        user_query=user_query,
        local_card=local_card,
        ai_reply=ai_reply,
        issues=all_records(),
    )


@app.route("/report", methods=["GET", "POST"])
def report():
    confirmation = None

    if request.method == "POST":
        location = request.form.get("location", "").strip()
        issue_type = request.form.get("issue_type", "").strip()
        description = request.form.get("description", "").strip()

        if location and issue_type:
            record = create_record(location, issue_type, description)
            confirmation = record
        else:
            confirmation = "Please provide both the bin location and issue type."

    return render_template("report.html", confirmation=confirmation)


if __name__ == "__main__":
    app.run(debug=True)
