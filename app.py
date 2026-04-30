"""
WanderMind — Flask Application
================================
6 AI-powered travel features:
  1. Travel Plan Generator  (/planner  → /result)
  2. Destination Research   (/research)
  3. AI Chat Assistant      (/chat)
  4. Destination Comparator (/compare)
  5. Budget Optimizer       (/budget)
  6. Smart Packing List     (/packing)
  + My Trips Memory Viewer  (/trips)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

load_dotenv() # Load from .env file

from memory.memento import get_memory
from services.ollama_service import OllamaService
from services.firecrawl_service import FirecrawlService

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Service singletons ────────────────────────────────────────────────────────
try:
    ollama = OllamaService()
except Exception as e:
    print(f"[WARN] {e}")
    ollama = None

firecrawl = FirecrawlService()
memory    = get_memory()


def _ollama_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not ollama:
            return jsonify({"error": "Ollama service not available."}), 503
        return fn(*args, **kwargs)
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/planner")
def planner():
    return render_template("planner.html")

@app.route("/result")
def result():
    return render_template("result.html")

@app.route("/research")
def research():
    return render_template("research.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/compare")
def compare():
    return render_template("compare.html")

@app.route("/budget")
def budget():
    return render_template("budget.html")

@app.route("/packing")
def packing():
    return render_template("packing.html")

@app.route("/trips")
def trips():
    return render_template("trips.html")


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — TRAVEL PLAN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/plan", methods=["POST"])
@_ollama_required
def api_plan():
    d = request.get_json()
    required = ["origin", "destination", "budget", "duration", "interests"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "All fields are required."}), 400

    try:
        # 1. Firecrawl — fetch real web data
        web_data = firecrawl.get_travel_tips(d["destination"])

        # 2. Ollama — generate plan
        plan = ollama.generate_travel_plan(
            origin       = d["origin"],
            destination  = d["destination"],
            budget       = d["budget"],
            duration     = int(d["duration"]),
            interests    = d["interests"],
            travel_style = d.get("travel_style", "comfort"),
            web_data     = web_data,
            memory_ctx   = memory.context_summary(),
        )

        # 3. Memento — save trip
        memory.add_trip({
            "destination": d["destination"],
            "origin": d["origin"],
            "budget": d["budget"],
            "duration": d["duration"],
            "interests": d["interests"],
        })
        memory.update_profile(
            budget_preference=d["budget"],
            interests=d["interests"].split(", "),
            home_city=d["origin"],
            travel_style=d.get("travel_style", "comfort"),
        )

        return jsonify({"success": True, "plan": plan,
                        "origin": d["origin"], "destination": d["destination"],
                        "firecrawl_status": firecrawl.enabled})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — DESTINATION RESEARCH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/research", methods=["POST"])
@_ollama_required
def api_research():
    d = request.get_json()
    destination = d.get("destination", "").strip()
    if not destination:
        return jsonify({"error": "Destination is required."}), 400

    try:
        # Firecrawl collects multi-source data
        scraped = firecrawl.research_destination(destination)
        web_text = "\n\n".join(scraped["scraped"].values()) if scraped["scraped"] else ""

        # Ollama synthesises
        profile = ollama.research_destination(destination, web_text)
        profile["data_sources"] = scraped["source_count"]
        profile["firecrawl_status"] = firecrawl.enabled

        return jsonify({"success": True, "profile": profile})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — AI CHAT ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
@_ollama_required
def api_chat():
    d = request.get_json()
    msg = d.get("message", "").strip()
    if not msg:
        return jsonify({"error": "Message required."}), 400

    try:
        history = memory.get_chat_history()
        reply   = ollama.chat(msg, history, memory.context_summary())
        memory.add_chat("user", msg)
        memory.add_chat("assistant", reply)
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — DESTINATION COMPARATOR
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/compare", methods=["POST"])
@_ollama_required
def api_compare():
    d = request.get_json()
    if not d.get("dest_a") or not d.get("dest_b"):
        return jsonify({"error": "Two destinations required."}), 400

    try:
        result = ollama.compare_destinations(
            dest_a    = d["dest_a"],
            dest_b    = d["dest_b"],
            budget    = d.get("budget", "2000"),
            duration  = int(d.get("duration", 7)),
            interests = d.get("interests", "general travel"),
            memory_ctx= memory.context_summary(),
        )
        return jsonify({"success": True, "comparison": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — BUDGET OPTIMIZER
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/budget", methods=["POST"])
@_ollama_required
def api_budget():
    d = request.get_json()
    if not d.get("destination") or not d.get("total_budget"):
        return jsonify({"error": "Destination and budget required."}), 400

    try:
        result = ollama.optimize_budget(
            destination  = d["destination"],
            total_budget = d["total_budget"],
            duration     = int(d.get("duration", 7)),
            travel_style = d.get("travel_style", "comfort"),
            priorities   = d.get("priorities", []),
        )
        return jsonify({"success": True, "budget": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 6 — PACKING LIST GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/packing", methods=["POST"])
@_ollama_required
def api_packing():
    d = request.get_json()
    if not d.get("destination"):
        return jsonify({"error": "Destination required."}), 400

    try:
        result = ollama.generate_packing_list(
            destination  = d["destination"],
            duration     = int(d.get("duration", 7)),
            activities   = d.get("activities", "general sightseeing"),
            travel_style = d.get("travel_style", "comfort"),
            season       = d.get("season", "unknown"),
        )
        return jsonify({"success": True, "packing": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# MEMORY API
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/memory", methods=["GET"])
def api_memory():
    return jsonify({
        "profile": memory.profile.get_state(),
        "history": memory.get_history_summary(),
        "trips": memory.get_trips(),
    })

@app.route("/api/memory/clear", methods=["POST"])
def api_memory_clear():
    memory.clear()
    return jsonify({"success": True})

@app.route("/api/memory/profile", methods=["POST"])
def api_update_profile():
    d = request.get_json()
    allowed = ["name", "home_city", "budget_preference", "travel_style",
               "interests", "dietary_preferences"]
    kwargs = {k: d[k] for k in allowed if k in d}
    memory.update_profile(**kwargs)
    return jsonify({"success": True, "profile": memory.profile.get_state()})


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🌍 WanderMind starting on http://localhost:5000\n")
    app.run(debug=True, port=5000)