import unittest
from app.assessment import assess_startup
from app.investment_memo import build_memo, build_investment_memo_pdf

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

class InvestmentMemoTests(unittest.TestCase):
    def test_memo_has_expected_sections_and_financials(self):
        result = assess_startup(SAMPLE)
        result["input_snapshot"] = SAMPLE
        memo = build_memo(result, 42, "2026-10-11T00:00:00+00:00")
        self.assertEqual(memo["assessment_id"], 42)
        self.assertIn("executive_summary", memo)
        self.assertEqual(memo["financial_overview"]["monthly_revenue"], 12000)
        self.assertTrue(memo["evidence_gaps"])
        self.assertIn("strengths", memo["swot"])

    def test_memo_pdf_is_valid_pdf(self):
        result = assess_startup(SAMPLE)
        result["input_snapshot"] = SAMPLE
        pdf = build_investment_memo_pdf(build_memo(result, 7))
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)

if __name__ == "__main__":
    unittest.main()
