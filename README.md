# Smart Budget Agent

Smart Budget Agent is a personal finance assistant built with Flask, SQLite, and AI-powered workflows. It helps users track expenses, manage budgets, save toward goals, and receive friendly financial advice in Hinglish.

## Project Overview

This project combines simple financial tracking with conversational AI. Users can:
- log daily expenses through natural language
- set category budgets
- create and update savings goals
- view dashboard insights and recent transactions
- ask questions about spending habits and receive guidance

## AI and Images Workflows

The project is designed around intelligent financial workflows:
- AI chat workflows for expense entry, budget management, and financial advice
- AI-assisted parsing of natural language inputs into structured expense data
- image-based workflows for future receipt and bill processing, making it easier to capture expenses from photos

These workflows are intended to make money management more natural, faster, and more accessible for everyday users.

## Screenshots

Add your app screenshots in the images folder and reference them here:

![Smart Budget Agent Dashboard](images/dashboard-preview.svg)

> Replace the image above with your real screenshot once you add it to the repository.

## Tech Stack

- Python
- Flask
- SQLite
- Groq AI
- HTML/CSS/JavaScript

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - create a `.env` file
   - add your `GROQ_API_KEY`

3. Run the app:
   ```bash
   python app.py
   ```

4. Open the app in your browser at:
   ```text
   http://127.0.0.1:5000
   ```

## Project Structure

- `app.py` – Flask routes and API endpoints
- `agents.py` – AI agent logic and parsing
- `database.py` – SQLite database operations
- `templates/` – frontend templates
- `tests/` – unit tests for parsing and database operations

## Notes

This project is a practical example of combining AI with personal finance automation and can be extended with image recognition workflows for receipts, invoices, and bills.
