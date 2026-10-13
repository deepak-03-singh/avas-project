import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.database import Base
from app.models import User, Assessment, PortfolioEntry
from app.main import get_portfolio, add_to_portfolio, update_portfolio_entry, remove_from_portfolio

class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.db = self.Session()
        self.user = User(full_name='Test User', email='portfolio@example.test', password_hash='hash')
        self.db.add(self.user); self.db.commit(); self.db.refresh(self.user)
        self.assessment = Assessment(owner_id=self.user.id, startup_name='GreenCart', industry='ClimateTech',
                                     readiness_score=72, risk_level='Medium', result_json='{}')
        self.db.add(self.assessment); self.db.commit(); self.db.refresh(self.assessment)

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def test_add_update_list_and_remove(self):
        created = add_to_portfolio({'assessment_id': self.assessment.id, 'status': 'Watching', 'notes': 'Verify revenue'}, self.user, self.db)
        self.assertEqual(created['startup_name'], 'GreenCart')
        self.assertEqual(created['notes'], 'Verify revenue')
        listed = get_portfolio(self.user, self.db)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]['status'], 'Watching')
        updated = update_portfolio_entry(created['id'], {'status': 'Due diligence', 'notes': 'Request bank statements'}, self.user, self.db)
        self.assertEqual(updated['status'], 'Due diligence')
        self.assertEqual(get_portfolio(self.user, self.db)[0]['notes'], 'Request bank statements')
        response = remove_from_portfolio(created['id'], self.user, self.db)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(get_portfolio(self.user, self.db), [])
        self.assertIsNotNone(self.db.get(Assessment, self.assessment.id), 'Removing portfolio entry must not delete the assessment')

    def test_cannot_add_another_users_assessment(self):
        other = User(full_name='Other', email='other@example.test', password_hash='hash')
        self.db.add(other); self.db.commit(); self.db.refresh(other)
        with self.assertRaises(HTTPException) as exc:
            add_to_portfolio({'assessment_id': self.assessment.id}, other, self.db)
        self.assertEqual(exc.exception.status_code, 404)

    def test_duplicate_and_invalid_status_are_rejected(self):
        add_to_portfolio({'assessment_id': self.assessment.id}, self.user, self.db)
        with self.assertRaises(HTTPException) as exc:
            add_to_portfolio({'assessment_id': self.assessment.id}, self.user, self.db)
        self.assertEqual(exc.exception.status_code, 409)
        with self.assertRaises(HTTPException) as exc:
            update_portfolio_entry(1, {'status': 'Definitely Investing'}, self.user, self.db)
        self.assertEqual(exc.exception.status_code, 422)

if __name__ == '__main__':
    unittest.main()
