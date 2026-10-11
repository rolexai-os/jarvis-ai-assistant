"""Safe command routing for JARVIS. No arbitrary shell command execution."""
import ast
import operator
import re
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus

WEBSITES = {
    "google": "https://www.google.com", "youtube": "https://www.youtube.com",
    "github": "https://github.com", "wikipedia": "https://www.wikipedia.org",
    "gmail": "https://mail.google.com", "chatgpt": "https://chatgpt.com",
}
APPS = {"notepad": ["notepad.exe"], "calculator": ["calc.exe"], "explorer": ["explorer.exe"]}
_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
           ast.Pow: operator.pow}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_calculate(expression):
    if len(expression) > 120:
        raise ValueError("Expression too long.")
    tree = ast.parse(expression, mode="eval")
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 10**12:
                raise ValueError("Number too large.")
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Exponent too large.")
            result = _BINOPS[type(node.op)](left, right)
            if abs(result) > 10**15:
                raise ValueError("Result too large.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](visit(node.operand))
        raise ValueError("Only basic arithmetic is allowed.")
    return visit(tree)


def handle_command(command, services=None):
    services = services or {}
    text = command.strip()
    low = text.lower()
    if not text:
        return "I'm listening. Say 'JARVIS' followed by a command, or type one below."
    if low in {"help", "commands"}:
        return ("Commands: help, time, system status, open <website or installed app>, "
                "search web <words>, calculate <math>, remind me to <task> in 10 minutes, "
                "reminders, search files <words>, lock PC, clear, exit.")
    if low in {"time", "what time is it", "what time is it?"}:
        return datetime.now().astimezone().strftime("Local time: %A, %d %B %Y, %I:%M:%S %p")
    if low in {"system status", "status"}:
        return services["system_status"]() if services.get("system_status") else "See dashboard for status."
    if low in {"lock pc", "lock computer", "lock my pc", "lock workstation"}:
        fn = services.get("lock_pc")
        return fn() if fn else "PC lock is available on Windows only."
    if low.startswith("open "):
        target = text[5:].strip()
        target_low = target.lower()
        if target_low in WEBSITES:
            webbrowser.open(WEBSITES[target_low])
            return f"Opening {target}."
        if target_low in APPS:
            return services["launch_app"](target_low) if services.get("launch_app") else "Windows app action unavailable."
        if services.get("open_app"):
            return services["open_app"](target)
        return "App launcher unavailable. Try a website, Notepad, Calculator or Explorer."
    if low.startswith("search web "):
        query = text[11:].strip()
        if not query:
            return "Add search terms."
        webbrowser.open("https://www.google.com/search?q=" + quote_plus(query))
        return "Searching the web for: " + query
    if low.startswith("calculate "):
        try:
            return "Result: " + str(safe_calculate(text[10:].strip()))
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
            return "Calculation error: " + str(exc)
    if low.startswith("remind me to "):
        match = re.match(r"remind me to (.+?) in (\d+)\s*(seconds?|minutes?|mins?|hours?|hrs?)$", text, re.I)
        if not match or not services.get("reminders"):
            return "Try: remind me to stretch in 10 minutes"
        task, amount, unit = match.groups()
        seconds = int(amount) * (3600 if unit.lower().startswith("h") else 60 if unit.lower().startswith("m") else 1)
        if not 1 <= seconds <= 365 * 24 * 3600:
            return "Reminder must be between 1 second and 365 days."
        item = services["reminders"].add(task.strip(), seconds)
        return f"Reminder saved: {item['task']} at {item['due']}"
    if low == "reminders":
        items = services["reminders"].list_items() if services.get("reminders") else []
        return "\\n".join(f"- {i['task']} — {i['due']}" for i in items) if items else "No pending reminders."
    if low.startswith("search files "):
        return services["search_files"](text[13:].strip()) if services.get("search_files") else "Choose a folder using Search files first."
    if low == "clear":
        if services.get("clear"):
            services["clear"]()
        return "Conversation cleared."
    if low in {"exit", "quit", "close jarvis"}:
        if services.get("exit"):
            services["exit"]()
        return "Closing the JARVIS interface."
    if services.get("ai_chat"):
        try:
            answer = services["ai_chat"](text)
            if answer:
                return answer
        except Exception as exc:
            return "AI chat unavailable: " + str(exc)
    return "I don't recognize that command yet. Type 'help' to see available commands."
