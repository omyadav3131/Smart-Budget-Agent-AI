import unittest
import os
import sqlite3
from agents import parse_expense_from_text
from database import (
    init_db,
    set_budget,
    get_budgets,
    get_budget_status,
    add_savings_goal,
    get_savings_goals,
    update_savings_goal,
    delete_savings_goal,
    save_expense,
    delete_expense,
    get_all_expenses,
)


class ParseExpenseTests(unittest.TestCase):
    def test_parses_simple_food_expense(self):
        parsed = parse_expense_from_text("aaj 200 rupay khane pe kharch kiye")
        self.assertEqual(parsed["amount"], 200)
        self.assertEqual(parsed["category"], "food")
        self.assertIn("khane", parsed["description"].lower())

    def test_parses_transport_expense(self):
        parsed = parse_expense_from_text("auto 50 ka tha")
        self.assertEqual(parsed["amount"], 50)
        self.assertEqual(parsed["category"], "transport")
        self.assertIn("auto", parsed["description"].lower())


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database is initialized
        init_db()

    def test_budget_operations(self):
        # Set a category budget
        msg = set_budget("food", 5000)
        self.assertIn("set to ₹5000", msg)

        # Get budgets
        budgets = get_budgets()
        self.assertEqual(budgets.get("food"), 5000)

        # Check status (should return a list with food status)
        status = get_budget_status()
        self.assertTrue(any(s["category"] == "food" for s in status))

    def test_savings_goal_operations(self):
        # Create goal
        msg = add_savings_goal("Test Goal", 10000, 1000, "2026-12-31")
        self.assertIn("Test Goal", msg)

        # Get goals
        goals = get_savings_goals()
        matched = [g for g in goals if g["name"] == "Test Goal"]
        self.assertEqual(len(matched), 1)
        goal = matched[0]
        self.assertEqual(goal["target_amount"], 10000)
        self.assertEqual(goal["current_amount"], 1000)
        self.assertEqual(goal["target_date"], "2026-12-31")

        # Update goal fund
        msg_update = update_savings_goal(goal["id"], 500)
        self.assertIn("New balance: ₹1500", msg_update)

        # Delete goal
        msg_delete = delete_savings_goal(goal["id"])
        self.assertEqual(msg_delete, "Goal deleted successfully")

    def test_expense_logging_and_deletion(self):
        # Save expense
        msg = save_expense(150, "transport", "test cab expense", "2026-07-04")
        self.assertIn("Saved: ₹150", msg)

        # Find the expense ID
        expenses = get_all_expenses()
        matched = [e for e in expenses if e["description"] == "test cab expense"]
        self.assertEqual(len(matched), 1)
        expense = matched[0]
        self.assertEqual(expense["amount"], 150)

        # Delete the expense
        msg_delete = delete_expense(expense["id"])
        self.assertEqual(msg_delete, "Expense deleted successfully")


if __name__ == "__main__":
    unittest.main()
