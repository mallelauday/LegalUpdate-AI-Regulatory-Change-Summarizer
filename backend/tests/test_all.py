import unittest
import json
import os
import sys
import hmac
import hashlib
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import app
from config import Config
from database.firebase_db import FirestoreManager
from services.change_detection import ChangeDetectionService
from services.groq_service import GroqSummarizerService
from services.firecrawl_service import FirecrawlService
from services.firecrawl_monitor_service import FirecrawlMonitorService
from services.memento_service import MementoMemoryService
from services.regulatory_service import RegulatoryService
from worker import BackgroundIngestionWorker

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

    # 2. Authentication & 4-Tier Role Permissions
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

        # Senior Reviewer login
        res_rev = self.client.post('/api/auth/login', json={
            'email': 'senior.counsel@legalupdate.ai',
            'password': 'review123'
        })
        self.assertEqual(res_rev.status_code, 200)
        rev_data = res_rev.get_json()['data']
        self.assertIn(rev_data['user']['role'], ['reviewer', 'senior_reviewer'])
        rev_token = rev_data['token']

        # Compliance Reviewer login
        res_comp = self.client.post('/api/auth/login', json={
            'email': 'compliance.officer@legalupdate.ai',
            'password': 'review123'
        })
        self.assertEqual(res_comp.status_code, 200)
        comp_data = res_comp.get_json()['data']
        self.assertIn(comp_data['user']['role'], ['reviewer', 'compliance_reviewer'])

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

    # 3. Firebase Connectivity & 12 Collections
    def test_03_firebase_connectivity(self):
        self.assertIsNotNone(self.db)
        sources = list(self.db.collection('regulatory_sources').stream())
        self.assertGreaterEqual(len(sources), 4)
        updates = list(self.db.collection('regulatory_updates').stream())
        self.assertGreaterEqual(len(updates), 3)
        monitors = list(self.db.collection('monitor_configs').stream())
        self.assertGreaterEqual(len(monitors), 4)

    # 4. Change Detection & Duplicate Prevention
    def test_04_change_detection(self):
        content_v1 = "Clause 1: Banks shall retain records for 5 years."

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

        eval_unchanged = ChangeDetectionService.evaluate_scraped_document(
            source_id="src-rbi",
            source_code="RBI",
            title="Master Direction – Information Technology Governance, Risk, Controls and Assurance Practices",
            url="https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?Id=12648",
            content=content_v1,
            document_id="RBI/2026-27/104"
        )
        self.assertIn(eval_unchanged['status'], ['MODIFIED', 'UNCHANGED'])

    # 5. Groq Summary Generation & Strict Guardrails
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
        context = MementoMemoryService.recall_context_for_update(
            regulator="RBI",
            title="Information Technology Cloud Directions",
            content="Disaster recovery RPO RTO cloud data localization"
        )
        self.assertTrue(context["has_precedent"])
        self.assertIn("precedent_ref", context)

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
        res_404 = self.client.get('/api/non-existent-route')
        self.assertEqual(res_404.status_code, 404)

        res_unauth = self.client.get('/api/updates')
        self.assertEqual(res_unauth.status_code, 401)

    # 12. 15-Minute Regulatory Source Monitors
    def test_12_firecrawl_monitors(self):
        monitors = FirecrawlMonitorService.get_monitors()
        self.assertGreaterEqual(len(monitors), 4)
        codes = [m.get("source_code") for m in monitors]
        for expected in ["RBI", "SEBI", "MCA", "IRDAI"]:
            self.assertIn(expected, codes)
        for m in monitors:
            self.assertEqual(m.get("schedule"), "every 15 minutes")
            self.assertEqual(m.get("timezone"), "Asia/Kolkata")

    # 13. Firecrawl Webhooks with HMAC Signature & Idempotency
    def test_13_firecrawl_webhook_and_queue(self):
        import uuid
        test_event_id = f"wh-test-event-{uuid.uuid4().hex[:8]}"
        secret = Config.FIRECRAWL_WEBHOOK_SECRET
        payload = {
            "id": test_event_id,
            "url": "https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?Id=99999",
            "source_code": "RBI",
            "data": {
                "title": "RBI Automated Webhook Circular on Cloud Controls",
                "markdown": "Mandatory directive on cloud storage encryption and disaster recovery protocols for commercial banks."
            }
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        # Post webhook
        res = self.client.post(
            '/api/webhooks/firecrawl',
            data=body_bytes,
            headers={
                'Content-Type': 'application/json',
                'x-firecrawl-signature': f"sha256={sig}"
            }
        )
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()['data']
        self.assertIn("job_id", res_data)

        # Re-posting same event returns duplicate status (idempotency)
        res_dup = self.client.post(
            '/api/webhooks/firecrawl',
            data=body_bytes,
            headers={
                'Content-Type': 'application/json',
                'x-firecrawl-signature': f"sha256={sig}"
            }
        )
        self.assertEqual(res_dup.status_code, 200)
        self.assertEqual(res_dup.get_json()['data']['status'], 'duplicate')

    # 14. Render Background Worker Queue Processing
    def test_14_background_worker_execution(self):
        worker = BackgroundIngestionWorker(poll_interval=1)
        count = worker.process_pending_jobs()
        self.assertIsInstance(count, int)

    # 15. Route Aliases & Root Health Check
    def test_15_api_aliases_and_root_health(self):
        # Top-level /health
        res_root = self.client.get('/health')
        self.assertEqual(res_root.status_code, 200)
        self.assertEqual(res_root.get_json()['data']['status'], 'operational')

        # Login to get token
        login_res = self.client.post('/api/auth/login', json={
            'email': 'admin@legalupdate.ai',
            'password': 'admin123'
        })
        token = login_res.get_json()['data']['token']
        headers = {'Authorization': f'Bearer {token}'}

        # /api/regulatory-updates alias
        res_alias_upd = self.client.get('/api/regulatory-updates', headers=headers)
        self.assertEqual(res_alias_upd.status_code, 200)

        # /api/ai-summaries alias
        res_alias_sum = self.client.get('/api/ai-summaries', headers=headers)
        self.assertEqual(res_alias_sum.status_code, 200)

        # /api/historical-context alias
        res_alias_hist = self.client.get('/api/historical-context', headers=headers)
        self.assertEqual(res_alias_hist.status_code, 200)

if __name__ == '__main__':
    unittest.main()
