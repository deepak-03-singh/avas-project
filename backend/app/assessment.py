from pathlib import Path
import json
import joblib
import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "venture_model.joblib"
FEATURES = [
    "problem_clarity", "solution_differentiation", "market_demand",
    "competition_intensity", "founder_experience", "team_completeness",
    "traction_level", "revenue_model_clarity", "financial_runway_months",
    "customer_validation_count", "monthly_revenue", "monthly_burn",
    "funding_needed", "target_market_size_millions", "has_prototype",
    "has_competitor_research"
]

def feature_values(d):
    return {
        "problem_clarity": d["problem_clarity"],
        "solution_differentiation": d["solution_differentiation"],
        "market_demand": d["market_demand"],
        "competition_intensity": d["competition_intensity"],
        "founder_experience": d["founder_experience"],
        "team_completeness": d["team_completeness"],
        "traction_level": d["traction_level"],
        "revenue_model_clarity": d["revenue_model_clarity"],
        "financial_runway_months": d["financial_runway_months"],
        "customer_validation_count": d["customer_validation_count"],
        "monthly_revenue": d["monthly_revenue"],
        "monthly_burn": d["monthly_burn"],
        "funding_needed": d["funding_needed"],
        "target_market_size_millions": d["target_market_size_millions"],
        "has_prototype": int(d["has_prototype"]),
        "has_competitor_research": int(d["has_competitor_research"]),
    }

FEATURE_LABELS = {
    "problem_clarity": "Problem clarity",
    "solution_differentiation": "Solution differentiation",
    "market_demand": "Market demand",
    "competition_intensity": "Competition intensity",
    "founder_experience": "Founder experience",
    "team_completeness": "Team completeness",
    "traction_level": "Traction level",
    "revenue_model_clarity": "Revenue model clarity",
    "financial_runway_months": "Financial runway (months)",
    "customer_validation_count": "Customer validation count",
    "monthly_revenue": "Monthly revenue",
    "monthly_burn": "Monthly burn",
    "funding_needed": "Funding needed",
    "target_market_size_millions": "Target market size (millions)",
    "has_prototype": "Prototype available",
    "has_competitor_research": "Competitor research available",
}

def shap_explanation(model, row, values_by_feature):
    """Return local TreeSHAP contributions when SHAP is installed and compatible."""
    unavailable = {
        "available": False,
        "method": "SHAP TreeExplainer (optional)",
        "note": "SHAP contributions are unavailable. Install backend/requirements-ml.txt and ensure a compatible trained tree model is present.",
        "top_positive": [],
        "top_negative": [],
    }
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        raw_values = explainer.shap_values(row)
        # SHAP versions differ: classifiers may return a list per class or a 3-D array.
        if isinstance(raw_values, list):
            raw_values = raw_values[1] if len(raw_values) > 1 else raw_values[0]
        elif hasattr(raw_values, "values"):
            raw_values = raw_values.values
        shap_array = np.asarray(raw_values)
        if shap_array.ndim == 3:
            if shap_array.shape[0] == 1:
                shap_array = shap_array[0]
            if shap_array.ndim == 2 and shap_array.shape[-1] > 1:
                shap_array = shap_array[:, 1]
        if shap_array.ndim == 2:
            shap_array = shap_array[0]
        if shap_array.ndim != 1 or len(shap_array) != len(FEATURES):
            return unavailable
        contributions = []
        for name, impact in zip(FEATURES, shap_array):
            value = float(impact)
            contributions.append({
                "feature": FEATURE_LABELS.get(name, name),
                "impact": round(value, 6),
                "input_value": values_by_feature[name],
            })
        positive = sorted((x for x in contributions if x["impact"] > 0), key=lambda x: x["impact"], reverse=True)[:4]
        negative = sorted((x for x in contributions if x["impact"] < 0), key=lambda x: x["impact"])[:4]
        return {
            "available": True,
            "method": "SHAP TreeExplainer",
            "note": "Local feature contributions for the model's positive class. Values are in model-output units; they are not causal effects. Synthetic-training models remain unvalidated.",
            "top_positive": positive,
            "top_negative": negative,
        }
    except Exception:
        # The main assessment must continue working if the optional explainer is absent or incompatible.
        return unavailable

def assess_startup(data: dict) -> dict:
    ratings = [
        data["problem_clarity"], data["solution_differentiation"], data["market_demand"],
        6-data["competition_intensity"], data["founder_experience"], data["team_completeness"],
        data["traction_level"], data["revenue_model_clarity"]
    ]
    # Transparent rubric: this is a heuristic, not an ML probability.
    score = (sum(ratings)/(len(ratings)*5))*70
    score += min(data["financial_runway_months"]/12, 1)*10
    score += min(data["customer_validation_count"]/100, 1)*8
    score += 6 if data["has_prototype"] else 0
    score += 6 if data["has_competitor_research"] else 0
    score = int(round(min(100, score)))
    band = ("Strong readiness signals" if score >= 80 else
            "Promising, needs validation" if score >= 60 else
            "Early-stage / significant gaps" if score >= 40 else "High uncertainty")

    risks = []
    if data["financial_runway_months"] < 6: risks.append("Short financial runway: under 6 months.")
    if data["monthly_burn"] > data["monthly_revenue"] and data["financial_runway_months"] < 12:
        risks.append("Monthly burn exceeds revenue while runway is limited.")
    if data["customer_validation_count"] < 10: risks.append("Limited customer validation evidence.")
    if data["traction_level"] <= 2: risks.append("Traction signals are still weak.")
    if data["competition_intensity"] >= 4 and data["solution_differentiation"] <= 3:
        risks.append("High competition with limited differentiation.")
    if not data["has_competitor_research"]: risks.append("Competitor research has not been recorded.")
    if data["revenue_model_clarity"] <= 2: risks.append("Revenue model needs clarification.")
    if not risks: risks.append("No critical checklist flags; validate assumptions with real evidence.")
    risk_level = "High" if len(risks) >= 4 else "Medium" if len(risks) >= 2 else "Low"

    strengths, weaknesses, opportunities, threats = [], [], [], []
    (strengths if data["problem_clarity"] >= 4 else weaknesses).append(
        "Problem statement is clear." if data["problem_clarity"] >= 4 else "Problem statement needs sharper definition.")
    (strengths if data["solution_differentiation"] >= 4 else weaknesses).append(
        "Solution shows differentiation." if data["solution_differentiation"] >= 4 else "Differentiation needs evidence.")
    (strengths if data["traction_level"] >= 4 else weaknesses).append(
        "Strong early traction signals." if data["traction_level"] >= 4 else "Traction is not yet strong.")
    (strengths if data["has_prototype"] else weaknesses).append(
        "Prototype is available for testing." if data["has_prototype"] else "A testable prototype is not reported.")
    opportunities = ["Run structured customer interviews and test willingness to pay.",
                     "Explore a focused niche before expanding to adjacent markets."]
    threats = ["Competitors may respond quickly; monitor alternatives and switching costs."]
    if data["competition_intensity"] >= 4: threats.append("Reported competition intensity is high.")
    if data["financial_runway_months"] < 6: threats.append("Short runway may limit experimentation time.")

    recs = []
    if data["customer_validation_count"] < 20:
        recs.append("Interview 15–20 target customers; document pain points, alternatives and willingness to pay.")
    if not data["has_prototype"]: recs.append("Build a small prototype or landing-page test around one core problem.")
    if not data["has_competitor_research"]: recs.append("Create a competitor matrix covering pricing, audience and differentiation.")
    if data["financial_runway_months"] < 6:
        recs.append("Prepare a 13-week cash-flow forecast and review non-essential spending.")
    if data["revenue_model_clarity"] <= 3: recs.append("Test 2–3 pricing options with target customers before scaling.")
    if data["traction_level"] <= 3: recs.append("Choose one traction metric and review it weekly.")
    if data["team_completeness"] <= 3: recs.append("Map capability gaps and find advisors or collaborators to cover critical needs.")
    if not recs: recs.append("Run a small paid pilot and track retention, gross margin and acquisition cost.")

    # Explainable, rule-based growth indicator. This is NOT an ML forecast.
    growth_inputs = [
        data["market_demand"], data["solution_differentiation"],
        data["founder_experience"], data["team_completeness"],
        data["traction_level"], data["revenue_model_clarity"]
    ]
    growth_score = (sum(growth_inputs) / (len(growth_inputs) * 5)) * 65
    growth_score += min(data["target_market_size_millions"] / 1000, 1) * 10
    growth_score += min(data["customer_validation_count"] / 100, 1) * 10
    growth_score += min(data["financial_runway_months"] / 12, 1) * 10
    growth_score += 5 if data["monthly_revenue"] > 0 else 0
    growth_score = int(round(min(100, growth_score)))

    factor_scores = {
        "Problem clarity": data["problem_clarity"],
        "Solution differentiation": data["solution_differentiation"],
        "Market demand": data["market_demand"],
        "Competition position": 6 - data["competition_intensity"],
        "Founder experience": data["founder_experience"],
        "Team completeness": data["team_completeness"],
        "Traction": data["traction_level"],
        "Revenue model clarity": data["revenue_model_clarity"],
    }
    positive_signals = [f"{name} is rated {value}/5." for name, value in sorted(factor_scores.items(), key=lambda item: item[1], reverse=True)[:3] if value >= 4]
    priority_gaps = [f"{name} is rated {value}/5 and needs validation." for name, value in sorted(factor_scores.items(), key=lambda item: item[1])[:3] if value <= 3]
    if not positive_signals:
        positive_signals = ["No rating reached 4/5; strengthen evidence across the core readiness dimensions."]
    if not priority_gaps:
        priority_gaps = ["No rating was 3/5 or lower; validate the self-reported ratings with external evidence."]

    monthly_net_burn = round(data["monthly_burn"] - data["monthly_revenue"], 2)
    financial_snapshot = {
        "runway_months": data["financial_runway_months"],
        "monthly_net_burn": monthly_net_burn,
        "revenue_covers_burn": data["monthly_revenue"] >= data["monthly_burn"],
        "runway_alert": "Critical: under 3 months" if data["financial_runway_months"] < 3 else "Watch: under 6 months" if data["financial_runway_months"] < 6 else "No short-runway flag from entered months"
    }

    probability, model_status = None, "No trained model artifact loaded; rubric-only assessment."
    model_explanation = {"available": False, "method": "SHAP TreeExplainer (optional)", "note": "No trained model artifact is loaded, so model contributions cannot be calculated.", "top_positive": [], "top_negative": []}
    if MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
            values_by_feature = feature_values(data)
            row = np.array([[values_by_feature[c] for c in FEATURES]], dtype=float)
            probability = round(float(model.predict_proba(row)[0][1])*100, 1)
            model_explanation = shap_explanation(model, row, values_by_feature)
            metadata_path = MODEL_PATH.parent / "model_metadata.json"
            provenance = "unknown"
            if metadata_path.exists():
                try:
                    provenance = json.loads(metadata_path.read_text(encoding="utf-8")).get("data_provenance", "unknown")
                except (ValueError, OSError):
                    provenance = "unknown"
            if provenance == "synthetic-or-unverified":
                model_status = "Synthetic / unverified data model"
            elif provenance == "real-labeled":
                model_status = "Model trained with user-declared real labels; independent validation still required"
            else:
                model_status = "Model loaded; training-data provenance unknown"
        except Exception:
            model_status = "Model artifact could not be loaded; rubric-only assessment."

    return {
        "startup_name": data["startup_name"], "industry": data["industry"],
        "readiness_score": score, "score_band": band,
        "demonstration_success_probability": probability,
        "probability_warning": "If the model was trained on synthetic data, this is a synthetic-demo probability, not a real-world success forecast. Never use it alone for investment decisions.",
        "risk_level": risk_level, "risk_flags": risks,
        "growth_potential_score": growth_score,
        "growth_score_note": "Heuristic indicator based on entered market, team, traction, validation and runway inputs; not a validated growth forecast.",
        "explainability": {
            "method": "Rule-based explanation of self-reported ratings; not SHAP and not a causal explanation.",
            "positive_signals": positive_signals,
            "priority_gaps": priority_gaps,
            "financial_snapshot": financial_snapshot,
            "model_explanation": model_explanation
        },
        "swot": {"strengths": strengths, "weaknesses": weaknesses, "opportunities": opportunities, "threats": threats},
        "recommendations": recs,
        "factor_summary": {
            "Problem clarity": round(data["problem_clarity"]/5*100,1),
            "Differentiation": round(data["solution_differentiation"]/5*100,1),
            "Market demand": round(data["market_demand"]/5*100,1),
            "Team": round((data["founder_experience"]+data["team_completeness"])/10*100,1),
            "Traction": round(data["traction_level"]/5*100,1),
            "Business model": round(data["revenue_model_clarity"]/5*100,1)
        },
        "model_status": model_status
    }
