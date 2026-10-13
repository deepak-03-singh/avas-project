"""Small dependency-light smoke tests for AVAS assessment output."""
import unittest
from app.assessment import assess_startup
from app.reporting import build_pdf
from app.schemas import AssessmentResponse

SAMPLE = {
    "startup_name": "GreenCart", "industry": "ClimateTech",
    "problem_clarity": 4, "solution_differentiation": 4, "market_demand": 4,
    "competition_intensity": 3, "founder_experience": 3, "team_completeness": 4,
    "traction_level": 3, "revenue_model_clarity": 4,
    "financial_runway_months": 9, "customer_validation_count": 35,
    "monthly_revenue": 12000, "monthly_burn": 18000,
    "funding_needed": 150000, "target_market_size_millions": 800,
    "has_prototype": True, "has_competitor_research": True,
}

class AssessmentSmokeTests(unittest.TestCase):
    def test_explainability_and_growth_indicator_are_returned(self):
        result = assess_startup(SAMPLE)
        self.assertGreaterEqual(result["readiness_score"], 0)
        self.assertLessEqual(result["readiness_score"], 100)
        self.assertGreaterEqual(result["growth_potential_score"], 0)
        self.assertLessEqual(result["growth_potential_score"], 100)
        self.assertTrue(result["explainability"]["positive_signals"])
        self.assertTrue(result["explainability"]["priority_gaps"])
        model_explanation = result["explainability"]["model_explanation"]
        self.assertIn("available", model_explanation)
        self.assertIn("top_positive", model_explanation)
        self.assertIn("top_negative", model_explanation)
        self.assertEqual(result["explainability"]["financial_snapshot"]["monthly_net_burn"], 6000)
        AssessmentResponse(**result)

    def test_pdf_report_is_generated(self):
        result = assess_startup(SAMPLE)
        pdf = build_pdf(result)
        self.assertTrue(pdf.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
