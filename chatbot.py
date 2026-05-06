"""
chatbot.py  —  PlasticBot: Plastics-Only Recycling Assistant
─────────────────────────────────────────────────────────────
Run:   python chatbot.py
Quit:  type 'exit' or press Ctrl+C

Flow (mirrors the system flowchart):
  1. Employee types a question
  2. Intent is detected  →  disposal / faq / report
  3. Relevant CSV is searched for context
  4. Context is sent to Claude API
  5. Answer is returned and printed
  6. For reports: structured issue record is created
"""

import sys
import textwrap

from data_loader import load_rules, load_faq
from matcher    import detect_intent, find_best_rule, find_best_faq
from api_client import call_claude
from reporter   import create_record, format_record

# ── Terminal colour helpers ───────────────────────────────────────────────────
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

WIDTH = 72  # wrap width for output


def hr(char="─"):
    print(DIM + char * WIDTH + RESET)


def wrap(text: str, indent: int = 0) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=WIDTH, initial_indent=prefix,
                         subsequent_indent=prefix)


def print_banner():
    print()
    print(GREEN + BOLD + "♻️  PlasticBot — Plastics-Only Recycling Assistant" + RESET)
    print(DIM + "  Powered by Claude AI  |  Data: recycling_rules + faq CSVs" + RESET)
    hr()
    print(wrap("Commands: just type your question, or use one of these shortcuts:"))
    print(f"  {CYAN}report issue{RESET}  — log a bin problem to facilities/sustainability")
    print(f"  {CYAN}history{RESET}       — show reported issues this session")
    print(f"  {CYAN}exit{RESET}          — quit")
    hr()


# ── Disposal answer formatter ─────────────────────────────────────────────────
def format_disposal(rule: dict) -> str:
    accepted = rule["accepted"].lower()
    if accepted == "yes":
        tag = GREEN + BOLD + "✅  ACCEPTED" + RESET
    elif accepted == "no":
        tag = RED + BOLD + "❌  NOT ACCEPTED" + RESET
    else:
        tag = YELLOW + BOLD + "⚠️   CONDITIONAL" + RESET

    lines = [tag, BOLD + rule["title"] + RESET, "", wrap(rule["response"])]

    if rule["prep"]:
        lines += ["", GREEN + "🔧 Preparation:" + RESET, wrap(rule["prep"], indent=3)]

    if rule["redirect"]:
        lines += ["", RED + "↪️  If not accepted:" + RESET, wrap(rule["redirect"], indent=3)]

    return "\n".join(lines)


# ── FAQ answer formatter ──────────────────────────────────────────────────────
def format_faq(faq: dict) -> str:
    lines = [
        CYAN + BOLD + "❓ FAQ" + RESET,
        BOLD + faq["question"] + RESET,
        "",
        wrap(faq["full"]),
    ]
    if faq["followup"]:
        lines += ["", DIM + "💬 " + faq["followup"] + RESET]
    return "\n".join(lines)


# ── Report flow ───────────────────────────────────────────────────────────────
def run_report_flow() -> str:
    print()
    print(YELLOW + BOLD + "🔔  Report a Bin Issue" + RESET)
    hr()

    location = input("  📍 Location / Bin ID (e.g. Level 3 Pantry): ").strip()
    if not location:
        return "Report cancelled — no location provided."

    issue_types = [
        "Bin is full / overflowing",
        "Bin is damaged",
        "Contamination observed",
        "Bin is missing",
        "Other",
    ]
    print("\n  Issue type:")
    for i, t in enumerate(issue_types, 1):
        print(f"    {i}. {t}")

    choice = input("  Enter number: ").strip()
    try:
        issue_type = issue_types[int(choice) - 1]
    except (ValueError, IndexError):
        return "Report cancelled — invalid issue type."

    description = input("  Description (optional, press Enter to skip): ").strip()

    record = create_record(location, issue_type, description)
    return (
        YELLOW + BOLD + "🔔  Issue Reported" + RESET + "\n"
        + format_record(record) + "\n\n"
        + GREEN + "✅ The facilities and sustainability team have been notified." + RESET
    )


# ── Build CSV context string for the API call ─────────────────────────────────
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


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    print_banner()

    # Load CSV data once at startup
    print(DIM + "Loading data... " + RESET, end="", flush=True)
    rules = load_rules()
    faqs  = load_faq()
    print(DIM + f"OK  ({len(rules)} rules, {len(faqs)} FAQs)\n" + RESET)

    while True:
        try:
            user_input = input(BOLD + "You: " + RESET).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! ♻️")
            sys.exit(0)

        if not user_input:
            continue

        cmd = user_input.lower()

        # ── Built-in commands ─────────────────────────────────────────────
        if cmd in ("exit", "quit", "q"):
            print("Goodbye! ♻️")
            sys.exit(0)

        if cmd in ("report", "report issue", "report bin", "report a bin issue"):
            print()
            result = run_report_flow()
            print()
            print(result)
            hr()
            print()
            continue

        if cmd in ("history", "issues", "reported issues"):
            from reporter import all_records, format_record
            records = all_records()
            print()
            if not records:
                print(DIM + "  No issues reported this session." + RESET)
            else:
                print(BOLD + f"  {len(records)} issue(s) reported this session:" + RESET)
                for r in records:
                    print(format_record(r))
                    print()
            hr()
            print()
            continue

        # ── Intent detection ──────────────────────────────────────────────
        intent = detect_intent(user_input)

        # Redirect to report flow if intent detected
        if intent == "report":
            print(
                "\n" + YELLOW +
                "It looks like you want to report a bin issue. "
                "Let me open the report form for you." + RESET
            )
            print()
            result = run_report_flow()
            print()
            print(result)
            hr()
            print()
            continue

        # ── CSV lookup ────────────────────────────────────────────────────
        local_card = None
        context    = ""

        if intent == "disposal":
            rule = find_best_rule(user_input, rules)
            if rule:
                local_card = format_disposal(rule)
                context    = build_rule_context(rule)
            else:
                faq = find_best_faq(user_input, faqs)
                if faq:
                    local_card = format_faq(faq)
                    context    = build_faq_context(faq)
        else:  # faq
            faq = find_best_faq(user_input, faqs)
            if faq:
                local_card = format_faq(faq)
                context    = build_faq_context(faq)
            else:
                rule = find_best_rule(user_input, rules)
                if rule:
                    local_card = format_disposal(rule)
                    context    = build_rule_context(rule)

        # ── Print structured card ─────────────────────────────────────────
        print()
        if local_card:
            print(local_card)
            print()

        # ── Call Claude API ───────────────────────────────────────────────
        print(DIM + "PlasticBot is thinking..." + RESET, end="\r", flush=True)
        try:
            ai_reply = call_claude(user_input, context)
            print(" " * 30, end="\r")  # clear the thinking line

            if local_card:
                # Show AI reply as an elaboration beneath the card
                print(DIM + "─" * WIDTH + RESET)
                print(DIM + "🤖 AI elaboration:" + RESET)
                print(wrap(ai_reply, indent=2))
            else:
                # No CSV match — show AI reply as primary answer
                print(CYAN + BOLD + "🤖 PlasticBot:" + RESET)
                print(wrap(ai_reply, indent=2))

        except RuntimeError as e:
            print(" " * 30, end="\r")
            if local_card:
                print(DIM + f"  (AI elaboration unavailable: {e})" + RESET)
            else:
                print(
                    RED + "⚠️  Could not reach the AI backend." + RESET + "\n" +
                    wrap("Quick rule: only clean, empty, dry rigid plastics belong in "
                         "this bin. When in doubt, use general waste.")
                )

        print()
        hr()
        print()


if __name__ == "__main__":
    main()
