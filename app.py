from flask import Flask, render_template, request, jsonify
from database import init_db, delete_expense, set_budget, get_budget_status, add_savings_goal, get_savings_goals, update_savings_goal, delete_savings_goal, get_dashboard_stats
from agents import tracker_agent, advisor_agent, get_history, unified_agent

app = Flask(__name__)
init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/track', methods=['POST'])
def track():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'response': 'Message khali hai. Kuch expense batao.'}), 400

    try:
        response = tracker_agent(message)
    except Exception as exc:
        response = f'Server error: {exc}'

    return jsonify({'response': response})


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'response': 'Kuch sawaal poochho.'}), 400

    try:
        response = advisor_agent(message)
    except Exception as exc:
        response = f'Server error: {exc}'

    return jsonify({'response': response})


@app.route('/history', methods=['GET'])
def history():
    expenses = get_history()
    return jsonify({'expenses': expenses})


@app.route('/api/dashboard', methods=['GET'])
def dashboard_stats():
    try:
        stats = get_dashboard_stats()
        budgets = get_budget_status()
        goals = get_savings_goals()
        return jsonify({
            'status': 'success',
            'stats': stats,
            'budgets': budgets,
            'goals': goals
        })
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'response': 'Message cannot be empty.'}), 400

    try:
        response = unified_agent(message)
        return jsonify({'response': response})
    except Exception as exc:
        return jsonify({'response': f'Server error: {exc}'}), 500


@app.route('/api/budgets', methods=['POST'])
def api_set_budget():
    data = request.get_json(silent=True) or {}
    category = data.get('category', '').strip()
    limit_amount = data.get('limit_amount')
    
    if not category or limit_amount is None:
        return jsonify({'status': 'error', 'message': 'Missing category or limit_amount.'}), 400

    try:
        limit_amount = float(limit_amount)
        msg = set_budget(category, limit_amount)
        return jsonify({'status': 'success', 'message': msg})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/goals', methods=['POST'])
def api_add_goal():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    target_amount = data.get('target_amount')
    current_amount = data.get('current_amount', 0.0)
    target_date = data.get('target_date', None)

    if not name or target_amount is None:
        return jsonify({'status': 'error', 'message': 'Missing name or target_amount.'}), 400

    try:
        target_amount = float(target_amount)
        current_amount = float(current_amount)
        msg = add_savings_goal(name, target_amount, current_amount, target_date)
        return jsonify({'status': 'success', 'message': msg})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/goals/add_fund', methods=['POST'])
def api_add_fund():
    data = request.get_json(silent=True) or {}
    goal_id = data.get('goal_id')
    amount = data.get('amount')

    if goal_id is None or amount is None:
        return jsonify({'status': 'error', 'message': 'Missing goal_id or amount.'}), 400

    try:
        goal_id = int(goal_id)
        amount = float(amount)
        msg = update_savings_goal(goal_id, amount)
        return jsonify({'status': 'success', 'message': msg})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def api_delete_expense(expense_id):
    try:
        msg = delete_expense(expense_id)
        return jsonify({'status': 'success', 'message': msg})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
def api_delete_goal(goal_id):
    try:
        msg = delete_savings_goal(goal_id)
        return jsonify({'status': 'success', 'message': msg})
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500


if __name__ == '__main__':
    app.run(debug=True)