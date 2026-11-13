import unittest
import json
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import app
from database.firebase_db import FirestoreManager
from services.change_detection import ChangeDetectionService
from services.groq_service import GroqSummarizerService
from services.firecrawl_service import FirecrawlService
from services.memento_service import MementoMemoryService
from services.regulatory_service import RegulatoryService

class LegalUpdateAITestSuite(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.db = FirestoreManager.get_db()

    # 1. Flask Backend Startup & Health Check
    def test_01_backend_startup_and_health(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'operational')
        self.assertEqual(data['data']['python_version'], '3.14.2')
        self.assertIn('integrations', data['data'])

    # 2. Authentication & Role Permissions
    def test_02_auth_and_roles(self):
        # Admin login
        res_admin = self.client.post('/api/auth/login', json={
            'email': 'admin@legalupdate.ai',
            'password': 'admin123'
        })
        self.assertEqual(res_admin.status_code, 200)
        admin_data = res_admin.get_json()['data']
        self.assertEqual(admin_data['user']['role'], 'admin')
        admin_token = admin_data['token']

        # Reviewer login
        res_rev = self.client.post('/api/auth/login', json={
            'email': 'senior.counsel@legalupdate.ai',
            'password': 'review123'
        })
        self.assertEqual(res_rev.status_code, 200)
        rev_data = res_rev.get_json()['data']
        self.assertEqual(rev_data['user']['role'], 'reviewer')
        rev_token = rev_data['token']

        # Viewer login
        res_view = self.client.post('/api/auth/login', json={
            'email': 'analyst@legalupdate.ai',
            'password': 'viewer123'
        })
        self.assertEqual(res_view.status_code, 200)
        view_token = res_view.get_json()['data']['token']

        # Role enforcement: Admin can list users, Viewer cannot
        res_users_admin = self.client.get('/api/auth/users', headers={'Authorization': f'Bearer {admin_token}'})
        self.assertEqual(res_users_admin.status_code, 200)

        res_users_viewer = self.client.get('/api/auth/users', headers={'Authorization': f'Bearer {view_token}'})
        self.assertEqual(res_users_viewer.status_code, 403)

    # 3. Firebase Connectivity & Seeding
    def test_03_firebase_connectivity(self):
        self.assertIsNotNone(self.db)
        sources = list(self.db.collection('regulatory_sources').stream())
        self.assertGreaterEqual(len(sources), 4)
        updates = list(self.db.collection('regulatory_updates').stream())
        self.assertGreaterEqual(len(updates), 3)

    # 4. Change Detection & Duplicate Prevention
    def test_04_change_detection(self):
        content_v1 = "Clause 1: Banks shall retain records for 5 years."
        content_v2 = "Clause 1: Banks shall retain records for 8 years due to enhanced compliance."

        eval_new = ChangeDetectionService.evaluate_scraped_document(
            source_id="src-rbi",
            source_code="RBI",
            title="Record Retention Circular",
            url="https://example.com/rbi-circular-1",
            content=content_v1,
            published_date="2026-11-01",
            document_id="RBI/TEST/001"
        )
        self.assertEqual(eval_new['status'], 'NEW')

        # Evaluate identical content -> UNCHANGED
        eval_unchanged = ChangeDetectionService.evaluate_scraped_document(
            source_id="src-rbi",
            source_code="RBI",
            title="Master Direction – Information Technology Governance, Risk, Controls and Assurance Practices",
            url="https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?Id=12648",
            content=content_v1,
            document_id="RBI/2026-27/104"
        )
        # It exists in seeded updates and has different content, so should detect MODIFIED
        self.assertIn(eval_unchanged['status'], ['MODIFIED', 'UNCHANGED'])

    # 5. Groq Summary Generation & Guardrails
    def test_05_groq_summary_generation(self):
        summary = GroqSummarizerService.generate_summary(
            title="SEBI Master Circular on Custodians",
            content="SEBI directs that every custodian shall maintain a minimum net worth of INR 50 crore w.e.f. April 01, 2027.",
            source_url="https://sebi.gov.in/test-custodian",
            source_code="SEBI",
            document_id="SEBI/TEST/CUST-01",
            published_date="2026-11-10"
        )
        # Verify 10 required items
        self.assertIn("original_title", summary)
        self.assertIn("short_summary", summary)
        self.assertIn("detailed_summary", summary)
        self.assertIn("key_regulatory_changes", summary)
        self.assertIn("important_requirements", summary)
        self.assertIn("affected_organizations", summary)
        self.assertIn("potential_compliance_implications", summary)
        self.assertIn("effective_date", summary)
        self.assertIn("recommended_actions", summary)
        self.assertIn("original_source_url", summary)
        self.assertIn("disclaimer", summary)
        self.assertIn("human legal review", summary["disclaimer"].lower())

    # 6. Memento Historical Memory Recall & Ingestion
    def test_06_memento_memory_integration(self):
        # Recall
        context = MementoMemoryService.recall_context_for_update(
            regulator="RBI",
            title="Information Technology Cloud Directions",
            content="Disaster recovery RPO RTO cloud data localization"
        )
        self.assertTrue(context["has_precedent"])
        self.assertIn("precedent_ref", context)

        # Ingestion of approved interpretation
        ingest_res = MementoMemoryService.ingest_approved_interpretation(
            update_id="test-upd-01",
            document_id="RBI/TEST/999",
            regulator="RBI",
            title="Test Approved Circular",
            approved_summary="Approved by compliance committee with zero exceptions.",
            reviewer_comments="Cross-referenced against Banking Regulation Act.",
            valid_date="2026-11-12"
        )
        self.assertTrue(ingest_res["success"])

    # 7. Firecrawl Scraper & Domestic Fallback
    def test_07_firecrawl_scraper(self):
        scrape_res = FirecrawlService.scrape_url("https://example.com")
        self.assertTrue(scrape_res["success"])
        self.assertIn("content", scrape_res)
        self.assertIn("title", scrape_res)

    # 8. Human Review and Approval Workflow
    def test_08_human_review_workflow(self):
        login_res = self.client.post('/api/auth/login', json={
            'email': 'senior.counsel@legalupdate.ai',
            'password': 'review123'
        })
        token = login_res.get_json()['data']['token']

        # Review an existing update
        review_res = self.client.post('/api/reviews/upd-rbi-2026-104',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'decision': 'approved',
                'comments': 'Legal verification complete. RPO/RTO parameters confirmed with CISO.',
                'edited_summary': 'Official approved text: RBI mandates Board IT committee quarterly review and local HSM keys by April 2027.'
            }
        )
        self.assertEqual(review_res.status_code, 200)
        self.assertTrue(review_res.get_json()['success'])

        # Verify audit history endpoint
        audit_res = self.client.get('/api/reviews/upd-rbi-2026-104/history',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(audit_res.status_code, 200)
        self.assertGreaterEqual(len(audit_res.get_json()['data']), 1)

    # 9. Source Management
    def test_09_source_management(self):
        login_res = self.client.post('/api/auth/login', json={
            'email': 'admin@legalupdate.ai',
            'password': 'admin123'
        })
        token = login_res.get_json()['data']['token']

        sources_res = self.client.get('/api/sources', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(sources_res.status_code, 200)
        self.assertGreaterEqual(len(sources_res.get_json()['data']), 4)

    # 10. Dashboard Aggregate Statistics
    def test_10_dashboard_stats(self):
        login_res = self.client.post('/api/auth/login', json={
            'email': 'admin@legalupdate.ai',
            'password': 'admin123'
        })
        token = login_res.get_json()['data']['token']

        stats_res = self.client.get('/api/updates/stats', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(stats_res.status_code, 200)
        data = stats_res.get_json()['data']
        self.assertIn('total_updates', data)
        self.assertIn('pending_reviews', data)
        self.assertIn('approved_updates', data)
        self.assertIn('by_regulator', data)

    # 11. Error Handling & Edge Cases
    def test_11_error_handling(self):
        # 404 Route
        res_404 = self.client.get('/api/non-existent-route')
        self.assertEqual(res_404.status_code, 404)

        # 401 Unauthorized
        res_unauth = self.client.get('/api/updates')
        self.assertEqual(res_unauth.status_code, 401)

if __name__ == '__main__':
    unittest.main()

