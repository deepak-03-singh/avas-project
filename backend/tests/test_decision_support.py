import unittest
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from app.decision_support import build_decision_support

class DecisionSupportTests(unittest.TestCase):
    def test_alerts_and_same_name_progress(self):
        now = datetime.now(timezone.utc)
        assessments = [
            SimpleNamespace(id=1, startup_name='GreenCart', industry='ClimateTech', readiness_score=42,
                            risk_level='High', result_json='{"explainability":{"financial_snapshot":{"runway_months":2},"priority_gaps":["Validate repeat purchases"]}}', created_at=now-timedelta(days=30)),
            SimpleNamespace(id=2, startup_name='GreenCart', industry='ClimateTech', readiness_score=61,
                            risk_level='Medium', result_json='{"explainability":{"financial_snapshot":{"runway_months":8}}}', created_at=now),
            SimpleNamespace(id=3, startup_name='OtherCo', industry='Retail', readiness_score=77,
                            risk_level='Low', result_json='{}', created_at=now),
        ]
        entry = SimpleNamespace(assessment_id=1, status='Due diligence', readiness_score=42)
        result = build_decision_support(assessments, [entry])
        self.assertEqual(result['summary']['assessments_count'], 3)
        self.assertEqual(result['summary']['high_risk_count'], 1)
        self.assertEqual(result['summary']['portfolio_count'], 1)
        trend = next(t for t in result['trends'] if t['startup_name'] == 'GreenCart')
        self.assertEqual(trend['score_change'], 19)
        self.assertEqual(trend['direction'], 'Improved')
        self.assertTrue(any(a['type'] == 'Short runway' and a['assessment_id'] == 1 for a in result['alerts']))
        self.assertTrue(any(a['type'] == 'Diligence follow-up' for a in result['alerts']))

    def test_no_false_trend_for_single_assessment_and_empty_portfolio(self):
        row = SimpleNamespace(id=1, startup_name='Solo', industry='AI', readiness_score=70,
                              risk_level='Low', result_json='{}', created_at=None)
        result = build_decision_support([row], [])
        self.assertEqual(result['trends'], [])
        self.assertIsNone(result['summary']['average_portfolio_readiness'])
        self.assertEqual(result['summary']['portfolio_count'], 0)

if __name__ == '__main__':
    unittest.main()
