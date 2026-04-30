"""
Ollama Service — All LLM interactions via local Ollama server
=============================================================
Replaces Gemini entirely. Uses the `ollama` Python SDK which
talks to a locally running Ollama server (http://localhost:11434).

Default model : llama3.2   (override with OLLAMA_MODEL env var)
Ollama host   : localhost  (override with OLLAMA_HOST env var)

To pull a model before running:
    ollama pull llama3.2
    ollama pull mistral
    ollama pull qwen2.5
    ollama pull deepseek-r1

Supports any model available in your local Ollama installation.
"""

import os
import json
import re
import requests

# ── Config ────────────────────────────────────────────────────────────────────
_DEFAULT_MODEL = "llama3.2"
_OLLAMA_HOST   = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")


class OllamaService:
    def __init__(self):
        self.model  = os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)
        self.host   = _OLLAMA_HOST
        self.base   = f"{self.host}/api"
        self._check_connection()

    def _check_connection(self):
        """Verify Ollama is running and the model is available."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            r.raise_for_status()
            tags = r.json()
            models = [m["name"].split(":")[0] for m in tags.get("models", [])]
            model_base = self.model.split(":")[0]
            if model_base in models:
                print(f"[Ollama] ✅ Connected — model: {self.model} (local)")
            else:
                avail = ", ".join(models) if models else "none pulled yet"
                print(f"[Ollama] ⚠  Model '{self.model}' not found locally.")
                print(f"[Ollama]    Available: {avail}")
                print(f"[Ollama]    Run: ollama pull {self.model}")
        except requests.exceptions.ConnectionError:
            print(f"[Ollama] ❌  Cannot connect to Ollama at {self.host}")
            print( "[Ollama]    Make sure Ollama is running: https://ollama.com/download")

    # ── Low-level call ────────────────────────────────────────────────────────
    def _chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """Call Ollama /api/chat and return the assistant text."""
        payload = {
            "model":   self.model,
            "messages": messages,
            "stream":  False,
            "options": {"temperature": temperature, "num_predict": 8192},
        }
        resp = requests.post(
            f"{self.base}/chat",
            json=payload,
            timeout=300,          # local models can be slow
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()

    def _call_json(self, system: str, user: str, temperature: float = 0.7) -> dict:
        """Call with explicit system prompt, parse response as JSON."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
        raw = self._chat(messages, temperature)
        # Strip markdown fences if the model adds them
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$",           "", raw.strip())
        # Find the first { ... } block in case the model adds preamble
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group(0)
        return json.loads(raw)

    def _call_text(self, system: str, user: str, temperature: float = 0.75) -> str:
        """Call and return plain text."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
        return self._chat(messages, temperature)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. TRAVEL PLAN GENERATOR
    # ──────────────────────────────────────────────────────────────────────────
    def generate_travel_plan(
        self,
        origin: str,
        destination: str,
        budget: str,
        duration: int,
        interests: str,
        travel_style: str,
        web_data: str,
        memory_ctx: str,
    ) -> dict:
        system = (
            "You are an expert travel planner. "
            "You MUST return ONLY valid JSON with no markdown fences, "
            "no preamble, and no trailing text. Start your response with { and end with }. "
            "Be concise."
        )
        user = f"""Generate a concise, personalised travel plan.

=== USER PROFILE (from Memento memory) ===
{memory_ctx}

=== TRIP DETAILS ===
From: {origin}
To: {destination}
Budget: INR {budget}
Duration: {duration} days
Interests: {interests}
Travel style: {travel_style}

=== LIVE WEB DATA (Firecrawl) ===
{web_data[:3000] if web_data else "Not available — use your knowledge."}

=== REQUIRED JSON SCHEMA ===
Return ONLY this JSON structure:
{{
  "destination": "string",
  "duration": {duration},
  "total_budget_inr": "string",
  "overview": "string",
  "highlights": ["string"],
  "days": [
    {{
      "day": 1,
      "theme": "string",
      "morning":   {{"activity": "string", "tip": "string", "cost_inr": "string"}},
      "afternoon": {{"activity": "string", "tip": "string", "cost_inr": "string"}},
      "evening":   {{"activity": "string", "tip": "string", "cost_inr": "string"}},
      "accommodation": "string",
      "local_food": "string",
      "daily_budget_inr": "string"
    }}
  ],
  "top_attractions": ["string"],
  "food_guide": ["string"],
  "budget_breakdown": {{"accommodation": "string", "food": "string", "transport": "string", "activities": "string", "misc": "string"}},
  "practical_info": {{"best_time": "string", "currency": "string", "language": "string", "visa": "string", "transport": "string"}},
  "packing_essentials": ["string"],
  "safety_tips": ["string"]
}}"""
        return self._call_json(system, user)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. DESTINATION RESEARCH
    # ──────────────────────────────────────────────────────────────────────────
    def research_destination(self, destination: str, web_data: str) -> dict:
        system = (
            "You are a destination research expert. "
            "Return ONLY valid JSON — no markdown, no extra text. "
            "Start with { and end with }."
        )
        user = f"""Create a comprehensive destination profile for: {destination}

Web data from Firecrawl:
{web_data[:4000] if web_data else "Use your knowledge."}

Return ONLY this JSON:
{{
  "destination": "string",
  "tagline": "string",
  "overview": "string",
  "best_time_to_visit": "string",
  "climate": "string",
  "top_experiences": [{{"name": "string", "description": "string", "cost": "string"}}],
  "neighbourhoods": [{{"name": "string", "vibe": "string", "best_for": "string"}}],
  "cuisine_highlights": ["string"],
  "hidden_gems": ["string"],
  "cultural_etiquette": ["string"],
  "budget_tiers": {{
    "budget":  {{"daily_inr": "string", "stays": "string", "food": "string"}},
    "mid":     {{"daily_inr": "string", "stays": "string", "food": "string"}},
    "luxury":  {{"daily_inr": "string", "stays": "string", "food": "string"}}
  }},
  "getting_there": "string",
  "getting_around": "string",
  "safety_rating": "string",
  "visa_info": "string",
  "useful_phrases": [{{"phrase": "string", "meaning": "string"}}],
  "emergency_numbers": {{"police": "string", "ambulance": "string", "tourist_helpline": "string"}}
}}"""
        return self._call_json(system, user)

    # ──────────────────────────────────────────────────────────────────────────
    # 3. CHAT ASSISTANT
    # ──────────────────────────────────────────────────────────────────────────
    def chat(self, message: str, history: list, memory_ctx: str) -> str:
        system = f"""You are WanderMind, a friendly and knowledgeable AI travel assistant.
Answer travel questions clearly and helpfully. Use bullet points for lists.
Keep responses focused (2-4 paragraphs max).

User memory context:
{memory_ctx}"""

        messages = [{"role": "system", "content": system}]
        for msg in history[-12:]:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        return self._chat(messages, temperature=0.75)

    # ──────────────────────────────────────────────────────────────────────────
    # 4. DESTINATION COMPARISON
    # ──────────────────────────────────────────────────────────────────────────
    def compare_destinations(
        self,
        dest_a: str,
        dest_b: str,
        budget: str,
        duration: int,
        interests: str,
        memory_ctx: str,
    ) -> dict:
        system = (
            "You are a travel comparison expert. "
            "Return ONLY valid JSON — no markdown fences, no extra text."
        )
        user = f"""Compare two travel destinations for a user.

User profile:
{memory_ctx}

Trip: {duration} days, budget USD {budget}, interests: {interests}
Destination A: {dest_a}
Destination B: {dest_b}

Return ONLY this JSON:
{{
  "summary": "string",
  "recommendation": "string",
  "winner": "string (name of winning destination)",
  "destinations": {{
    "a": {{
      "name": "{dest_a}",
      "tagline": "string",
      "best_for": "string",
      "estimated_cost_usd": "string",
      "pros": ["string"],
      "cons": ["string"],
      "vibe": "string",
      "ideal_traveller": "string"
    }},
    "b": {{
      "name": "{dest_b}",
      "tagline": "string",
      "best_for": "string",
      "estimated_cost_inr": "string",
      "pros": ["string"],
      "cons": ["string"],
      "vibe": "string",
      "ideal_traveller": "string"
    }}
  }},
  "comparison_table": [
    {{"category": "string", "dest_a": "string", "dest_b": "string"}}
  ]
}}"""
        return self._call_json(system, user)

    # ──────────────────────────────────────────────────────────────────────────
    # 5. BUDGET OPTIMIZER
    # ──────────────────────────────────────────────────────────────────────────
    def optimize_budget(
        self,
        destination: str,
        total_budget: str,
        duration: int,
        travel_style: str,
        priorities: list,
    ) -> dict:
        system = (
            "You are a travel budget expert. "
            "Return ONLY valid JSON — no markdown fences, no extra text."
        )
        user = f"""Optimize a travel budget with smart allocation.

Destination: {destination}
Total budget: USD {total_budget}
Duration: {duration} days
Travel style: {travel_style}
User priorities: {', '.join(priorities) if priorities else 'balanced'}

Return ONLY this JSON:
{{
  "destination": "string",
  "total_budget_inr": 0,
  "daily_budget_inr": 0,
  "summary": "string",
  "breakdown": [
    {{"category": "string", "amount_usd": 0, "percentage": 0, "tips": "string", "icon": "emoji"}}
  ],
  "money_saving_tips": ["string"],
  "splurge_recommendations": ["string"],
  "free_activities": ["string"],
  "budget_hotels": ["string"],
  "budget_restaurants": ["string"],
  "hidden_costs": ["string"],
  "currency_tips": "string",
  "score": {{"value_for_money": 0, "affordability": 0, "experience_quality": 0}}
}}

Use real numbers for amount_inr (summing to {total_budget}), percentage (summing to 100),
and scores 1-10. All numbers must be integers or floats, NOT strings."""
        return self._call_json(system, user)

    # ──────────────────────────────────────────────────────────────────────────
    # 6. PACKING LIST GENERATOR
    # ──────────────────────────────────────────────────────────────────────────
    def generate_packing_list(
        self,
        destination: str,
        duration: int,
        activities: str,
        travel_style: str,
        season: str,
    ) -> dict:
        system = (
            "You are a smart travel packing assistant. "
            "Return ONLY valid JSON — no markdown fences, no extra text."
        )
        user = f"""Generate a smart packing list for:

Destination: {destination}
Duration: {duration} days
Season/weather: {season}
Activities: {activities}
Travel style: {travel_style}

Return ONLY this JSON:
{{
  "destination": "string",
  "total_items": 0,
  "categories": [
    {{
      "name": "string",
      "icon": "emoji",
      "items": [
        {{"item": "string", "quantity": "string", "essential": true, "tip": "string"}}
      ]
    }}
  ],
  "size_guide": "string",
  "airline_tips": "string",
  "tech_essentials": ["string"],
  "destination_specific": ["string"],
  "things_to_leave_behind": ["string"]
}}

Include at least 6 categories: Clothing, Toiletries, Documents, Electronics, Health & Safety, Footwear.
total_items must be an integer."""
        return self._call_json(system, user)

    # ──────────────────────────────────────────────────────────────────────────
    # Utility: list available local models
    # ──────────────────────────────────────────────────────────────────────────
    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def get_model_info(self) -> dict:
        return {
            "model":   self.model,
            "host":    self.host,
            "available_models": self.list_models(),
        }
