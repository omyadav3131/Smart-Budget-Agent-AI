import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

from database import (
    get_all_expenses,
    get_last_entry_date,
    get_monthly_summary,
    get_weekly_summary,
    save_expense,
    delete_expense,
    set_budget,
    get_budgets,
    get_budget_status,
    add_savings_goal,
    get_savings_goals,
    update_savings_goal,
    delete_savings_goal,
    get_dashboard_stats,
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def ask_llm(prompt: str, fallback: str | None = None) -> str:
    if client is None:
        return fallback or ""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        content = response.choices[0].message.content
        return content.strip() if content else (fallback or "")
    except Exception:
        return fallback or ""


def ask_llm_json(prompt: str) -> dict | None:
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a precise data extractor. You must respond in valid JSON format only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
            temperature=0.0
        )
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
    except Exception as e:
        print("JSON LLM error:", e)
    return None


def parse_expense_from_text(user_input: str) -> dict:
    """Legacy regex parser for fallback or testing."""
    cleaned = user_input.strip().lower()
    amount_match = re.search(r"(\d+(?:\.\d+)?)", user_input)
    amount = float(amount_match.group(1)) if amount_match else None

    if amount is None:
        return {"amount": None, "category": "other", "description": user_input.strip()}

    category = "other"
    food_words = ["khana", "khane", "khan", "food", "chai", "coffee", "lunch", "dinner", "breakfast", "snack", "restaurant", "cafe", "tea", "juice"]
    transport_words = ["auto", "bus", "cab", "taxi", "metro", "petrol", "fuel", "train", "bike", "car", "ride", "transport"]
    shopping_words = ["grocery", "market", "shopping", "shop", "cloth", "shoes", "buy", "bought", "mall", "electronics"]
    entertainment_words = ["movie", "ticket", "game", "netflix", "party", "entertainment"]
    bills_words = ["bill", "electricity", "rent", "water", "internet", "mobile", "recharge", "emi"]
    health_words = ["doctor", "medicine", "hospital", "pharmacy", "health"]

    if any(word in cleaned for word in food_words):
        category = "food"
    elif any(word in cleaned for word in transport_words):
        category = "transport"
    elif any(word in cleaned for word in shopping_words):
        category = "shopping"
    elif any(word in cleaned for word in entertainment_words):
        category = "entertainment"
    elif any(word in cleaned for word in bills_words):
        category = "bills"
    elif any(word in cleaned for word in health_words):
        category = "health"

    description = user_input.strip()
    description = re.sub(r"\b(?:rupay|rs|₹|rupees)\b", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\b\d+(?:\.\d+)?\b", "", description)
    description = re.sub(r"\s+", " ", description).strip()
    description = description or "Expense"

    return {"amount": amount, "category": category, "description": description}


def parse_user_input_with_llm(user_input: str, active_goals_list: list) -> dict:
    current_date = datetime.now().strftime("%Y-%m-%d")
    categories_str = ", ".join(["food", "transport", "shopping", "entertainment", "bills", "health", "other"])
    goals_str = ", ".join([f"'{g['name']}' (ID: {g['id']})" for g in active_goals_list]) if active_goals_list else "None"
    
    prompt = f"""
You are an intelligent natural language interface for a personal finance assistant.
Analyze the user's input and classify their intent into one of the following schemas.
Current Date: {current_date}
Valid Categories: {categories_str}
Existing Savings Goals: {goals_str}

User Input: "{user_input}"

You must respond with a JSON object. The keys of the JSON object must match one of the following exact formats based on intent:

1. If user is recording one or more expenses (e.g. "spent 150 on food, 20 on auto"):
{{
  "intent": "add_expense",
  "expenses": [
    {{
      "amount": float,
      "category": "food"|"transport"|"shopping"|"entertainment"|"bills"|"health"|"other",
      "description": "short description of item"
    }}
  ]
}}
Note: If a category is not obvious, map to "other". Make sure the amount is a positive number.

2. If user is setting a category budget limit (e.g. "set food limit to 5000", "shopping budget is 8000"):
{{
  "intent": "set_budget",
  "category": "food"|"transport"|"shopping"|"entertainment"|"bills"|"health"|"other",
  "limit_amount": float
}}

3. If user is managing a savings goal (e.g. "create savings goal for iPhone target 50000", "add 1500 to my laptop goal", "save 2000 for trip"):
{{
  "intent": "manage_goal",
  "action": "create" or "update",
  "name": "goal name" (use the existing goal name if updating),
  "target_amount": float or null (required for "create"),
  "added_amount": float or null (required for "update", the amount they are saving/adding now),
  "target_date": "YYYY-MM-DD" or null
}}

4. If user is asking a question about their spending, trends, budgets, or requesting advice/insights:
{{
  "intent": "analyze_query",
  "query": "original user question"
}}

5. If it is general conversation, greeting, or unclear:
{{
  "intent": "general",
  "reply": "friendly fallback reply in Hinglish if greeting, else ask how you can help"
}}

Ensure that the response is strictly valid JSON matching one of these 5 formats. Do not add any conversational text outside the JSON.
"""
    parsed = ask_llm_json(prompt)
    if parsed and "intent" in parsed:
        return parsed
    # Fallback to general if JSON extraction failed
    return {"intent": "general", "reply": "Mujhe samajh nahi aaya. Kya aap apna expense ya query dusre tarike se likh sakte hain?"}


def run_advisor_persona(intent: str, action_details: str, original_query: str) -> str:
    weekly = get_weekly_summary()
    monthly = get_monthly_summary()
    budgets = get_budget_status()
    goals = get_savings_goals()
    
    context = f"""
You are an Indian middle-class budget advisor uncle/father figure.
You are friendly, witty, slightly strict about spending money unnecessarily, and highly practical.
You speak in friendly Hinglish (Hindi written in English script).

Latest Financial Data:
- Weekly spending (category-wise): {weekly}
- Monthly spending (category-wise): {monthly}
- Budgets status (limit, spent): {budgets}
- Savings Goals: {goals}

Action Taken by System: {action_details}
User Message: {original_query}
Intent Type: {intent}

Your task:
Respond to the user in 3-5 sentences in Hinglish.
- If an expense was logged, confirm it. Warn them if they are spending too much on categories like entertainment/shopping, or if they are close to/exceeding their budget.
- If a budget was set, confirm it with some wise uncle-style advice (e.g. "Chalo, accha kiya. Control rahega.").
- If a savings goal was created/updated, encourage them (e.g., "Shaabash! Aise hi thoda thoda bachao.").
- If they asked a query or requested analysis, answer their query using the financial data provided above in a very friendly, clear, and analytical way, but with that classic Hinglish middle-class advice.
- If it is general chat, reply warmly and steer them back to managing their finances.
"""
    response = ask_llm(context)
    if response:
        return response
    return action_details


def unified_agent(user_input: str) -> str:
    """Main agent entry point that parses intent, executes database actions, and returns persona response."""
    try:
        active_goals = get_savings_goals()
    except Exception:
        active_goals = []
        
    parsed = parse_user_input_with_llm(user_input, active_goals)
    intent = parsed.get("intent", "general")
    action_details = ""
    
    if intent == "add_expense":
        expenses = parsed.get("expenses", [])
        if not expenses:
            # Fallback to legacy regex parser
            parsed_legacy = parse_expense_from_text(user_input)
            if parsed_legacy["amount"] is not None:
                res = save_expense(parsed_legacy["amount"], parsed_legacy["category"], parsed_legacy["description"])
                action_details = res
            else:
                action_details = "Koi expense nahi mila. Example: 'aaj 200 khane pe kharch kiye'"
        else:
            saved_list = []
            for exp in expenses:
                res = save_expense(exp["amount"], exp["category"], exp["description"])
                saved_list.append(res)
            action_details = " aur ".join(saved_list)
            
    elif intent == "set_budget":
        cat = parsed.get("category", "")
        amt = parsed.get("limit_amount", 0.0)
        if cat and amt > 0:
            action_details = set_budget(cat, amt)
        else:
            action_details = "Category budget update nahi ho saka. Limit sahi se bataiye."
            
    elif intent == "manage_goal":
        action = parsed.get("action", "")
        name = parsed.get("name", "")
        target_amount = parsed.get("target_amount")
        added_amount = parsed.get("added_amount")
        target_date = parsed.get("target_date")
        
        if action == "create" and name and target_amount:
            action_details = add_savings_goal(name, target_amount, 0.0, target_date)
        elif action == "update" and name and added_amount:
            # Try to find target goal
            matched_goal = None
            for g in active_goals:
                if g["name"].lower() == name.lower():
                    matched_goal = g
                    break
            if matched_goal:
                action_details = update_savings_goal(matched_goal["id"], added_amount)
            else:
                action_details = f"Goal '{name}' nahi mila. Pehle naya goal create karo."
        else:
            action_details = "Goal operations me invalid inputs mile."
            
    elif intent == "analyze_query":
        action_details = f"User analysis query: {parsed.get('query', user_input)}"
        
    elif intent == "general":
        action_details = parsed.get("reply", "Hello! Main aapka budget consistency helper hoon.")
        
    # Run through persona responder
    return run_advisor_persona(intent, action_details, user_input)


# Maintain backward compatibility
def tracker_agent(user_input: str) -> str:
    return unified_agent(user_input)


def advisor_agent(query: str) -> str:
    return unified_agent(query)


def get_history() -> list:
    return get_all_expenses()