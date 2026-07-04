import sqlite3
from datetime import datetime

DB_NAME = "budget.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    ''')
    # Budgets table (limit per category)
    c.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            limit_amount REAL NOT NULL
        )
    ''')
    # Savings goals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0.0,
            target_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_expense(amount: float, category: str, description: str, date_str: str = None) -> str:
    """Save a new expense to database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    c.execute(
        'INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)',
        (amount, category, description, date_str)
    )
    conn.commit()
    conn.close()
    return f"✅ Saved: ₹{amount} in {category}"

def get_weekly_summary() -> list:
    """Get category-wise spending for last 7 days."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE date >= date('now', '-7 days')
        GROUP BY category
        ORDER BY total DESC
    ''')
    results = c.fetchall()
    conn.close()
    return results

def get_monthly_summary() -> list:
    """Get category-wise spending for last 30 days."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date >= date('now', '-30 days')
        GROUP BY category
        ORDER BY total DESC
    ''')
    results = c.fetchall()
    conn.close()
    return results

def get_last_entry_date() -> str:
    """Get date of most recent expense entry."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT date FROM expenses ORDER BY date DESC LIMIT 1')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_expenses() -> list:
    """Get all expenses as dictionaries."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, amount, category, description, date FROM expenses ORDER BY date DESC, id DESC LIMIT 50')
    results = c.fetchall()
    conn.close()
    return [{"id": r[0], "amount": r[1], "category": r[2], "description": r[3], "date": r[4]} for r in results]

def delete_expense(expense_id: int) -> str:
    """Delete an expense by ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()
    return "Expense deleted successfully"

def set_budget(category: str, limit_amount: float) -> str:
    """Set or update a budget limit for a category."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO budgets (category, limit_amount)
        VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET limit_amount = excluded.limit_amount
    ''', (category.lower(), limit_amount))
    conn.commit()
    conn.close()
    return f"🎯 Budget limit for {category} set to ₹{limit_amount}"

def get_budgets() -> dict:
    """Get all budgets."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT category, limit_amount FROM budgets')
    results = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in results}

def get_budget_status() -> list:
    """Get budget status (limit, spend, etc.) for all categories in current month."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get all budget limits
    c.execute('SELECT category, limit_amount FROM budgets')
    budgets = c.fetchall()
    
    # Get actual spending in current month
    current_month = datetime.now().strftime('%Y-%m')
    c.execute('''
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date LIKE ?
        GROUP BY category
    ''', (f"{current_month}%",))
    spending = dict(c.fetchall())
    conn.close()
    
    status = []
    for category, limit in budgets:
        spend = spending.get(category.lower(), 0.0)
        status.append({
            "category": category,
            "limit": limit,
            "spent": spend,
            "remaining": max(0.0, limit - spend),
            "percentage": min(100.0, (spend / limit * 100.0) if limit > 0 else 0.0)
        })
    return status

def add_savings_goal(name: str, target_amount: float, current_amount: float = 0.0, target_date: str = None) -> str:
    """Create a new savings goal."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'INSERT INTO savings_goals (name, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?)',
        (name, target_amount, current_amount, target_date)
    )
    conn.commit()
    conn.close()
    return f"🚀 Savings goal '{name}' of ₹{target_amount} created!"

def get_savings_goals() -> list:
    """List all savings goals."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, target_amount, current_amount, target_date FROM savings_goals')
    results = c.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "name": r[1],
        "target_amount": r[2],
        "current_amount": r[3],
        "target_date": r[4],
        "percentage": min(100.0, (r[3] / r[2] * 100.0) if r[2] > 0 else 0.0)
    } for r in results]

def update_savings_goal(goal_id: int, added_amount: float) -> str:
    """Add funds to a savings goal."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ?', (added_amount, goal_id))
    c.execute('SELECT name, current_amount, target_amount FROM savings_goals WHERE id = ?', (goal_id,))
    res = c.fetchone()
    conn.commit()
    conn.close()
    if res:
        return f"💰 Added fund to '{res[0]}'. New balance: ₹{res[1]} / ₹{res[2]}"
    return "Savings goal not found"

def delete_savings_goal(goal_id: int) -> str:
    """Delete a savings goal."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM savings_goals WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()
    return "Goal deleted successfully"

def get_dashboard_stats() -> dict:
    """Retrieve aggregate financial status for dashboard."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Total spent this month
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{current_month}%",))
    monthly_spend = c.fetchone()[0] or 0.0
    
    # 2. Total spent this week (last 7 days)
    c.execute("SELECT SUM(amount) FROM expenses WHERE date >= date('now', '-7 days')")
    weekly_spend = c.fetchone()[0] or 0.0
    
    # 3. Category distribution (last 30 days)
    c.execute('''
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date >= date('now', '-30 days')
        GROUP BY category
    ''')
    category_distribution = dict(c.fetchall())
    
    # 4. Recent transactions
    c.execute('SELECT id, amount, category, description, date FROM expenses ORDER BY date DESC, id DESC LIMIT 10')
    recent_expenses = [{
        "id": r[0],
        "amount": r[1],
        "category": r[2],
        "description": r[3],
        "date": r[4]
    } for r in c.fetchall()]
    
    conn.close()
    
    # Calculate top category
    top_category = "None"
    if category_distribution:
        top_category = max(category_distribution, key=category_distribution.get)
        
    return {
        "monthly_spend": monthly_spend,
        "weekly_spend": weekly_spend,
        "category_distribution": category_distribution,
        "recent_expenses": recent_expenses,
        "top_category": top_category
    }