import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

logger = logging.getLogger("legalupdate.firebase")

def get_utc_now():
    return datetime.now(timezone.utc).isoformat()

class LocalDocumentSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return dict(self._data) if self._data else {}

class LocalDocumentReference:
    def __init__(self, collection, doc_id):
        self.collection = collection
        self.id = doc_id

    def get(self):
        data = self.collection.store.get(self.id)
        return LocalDocumentSnapshot(self.id, data)

    def set(self, data, merge=False):
        current = self.collection.store.get(self.id, {}) if merge else {}
        new_data = dict(data)
        new_data["id"] = self.id
        current.update(new_data)
        self.collection.store[self.id] = current
        self.collection.client.save_to_disk()
        return self

    def update(self, data):
        if self.id not in self.collection.store:
            raise KeyError(f"Document {self.id} does not exist in {self.collection.name}")
        self.collection.store[self.id].update(data)
        self.collection.client.save_to_disk()
        return self

    def delete(self):
        if self.id in self.collection.store:
            del self.collection.store[self.id]
            self.collection.client.save_to_disk()

class LocalCollectionReference:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        if name not in client.collections:
            client.collections[name] = {}
        self.store = client.collections[name]

    def document(self, doc_id=None):
        if not doc_id:
            doc_id = str(uuid.uuid4())
        return LocalDocumentReference(self, doc_id)

    def add(self, data):
        doc_id = str(uuid.uuid4())
        ref = self.document(doc_id)
        ref.set(data)
        return None, ref

    def stream(self):
        for doc_id, data in list(self.store.items()):
            yield LocalDocumentSnapshot(doc_id, data)

    def where(self, field, op, val):
        return LocalQuery(self, [(field, op, val)])

    def order_by(self, field, direction="ASCENDING"):
        return LocalQuery(self, [], order_by=(field, direction))

    def limit(self, val):
        return LocalQuery(self, [], limit_val=val)

class LocalQuery:
    def __init__(self, collection, filters, order_by=None, limit_val=None):
        self.collection = collection
        self.filters = filters
        self.order_by_spec = order_by
        self.limit_val = limit_val

    def where(self, field, op, val):
        return LocalQuery(self.collection, self.filters + [(field, op, val)], self.order_by_spec, self.limit_val)

    def order_by(self, field, direction="ASCENDING"):
        return LocalQuery(self.collection, self.filters, (field, direction), self.limit_val)

    def limit(self, val):
        return LocalQuery(self.collection, self.filters, self.order_by_spec, val)

    def stream(self):
        results = []
        for doc_id, data in self.collection.store.items():
            match = True
            for field, op, val in self.filters:
                doc_val = data.get(field)
                if op in ("==", "=") and doc_val != val:
                    match = False
                    break
                elif op == "!=" and doc_val == val:
                    match = False
                    break
                elif op == "in" and (not isinstance(val, (list, tuple, set)) or doc_val not in val):
                    match = False
                    break
                elif op == "array-contains" and (not isinstance(doc_val, list) or val not in doc_val):
                    match = False
                    break
                elif op == ">" and (doc_val is None or not (doc_val > val)):
                    match = False
                    break
                elif op == "<" and (doc_val is None or not (doc_val < val)):
                    match = False
                    break
            if match:
                results.append(LocalDocumentSnapshot(doc_id, data))

        if self.order_by_spec:
            field, direction = self.order_by_spec
            reverse = direction.upper() in ("DESC", "DESCENDING")
            results.sort(key=lambda x: str(x.to_dict().get(field, "")), reverse=reverse)

        if self.limit_val:
            results = results[:self.limit_val]

        for r in results:
            yield r

class LocalFirestoreClient:
    """In-memory & JSON file-backed Firestore client for local development when credentials are absent."""
    def __init__(self, persistence_file=None):
        self.collections = {}
        self.persistence_file = persistence_file or str(Path(__file__).resolve().parent.parent / "data" / "local_firestore.json")
        self.load_from_disk()

    def collection(self, name):
        return LocalCollectionReference(self, name)

    def save_to_disk(self):
        try:
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(self.collections, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed saving local firestore state: %s", e)

    def load_from_disk(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    self.collections = json.load(f)
            except Exception as e:
                logger.error("Failed reading local firestore state: %s", e)
                self.collections = {}

class FirestoreManager:
    _instance = None
    _db = None
    _is_live = False

    @classmethod
    def get_db(cls):
        if cls._db is not None:
            return cls._db

        service_key_path = Config.FIREBASE_SERVICE_ACCOUNT_KEY
        if service_key_path and os.path.exists(service_key_path):
            try:
                logger.info("Initializing live Firebase Admin SDK from: %s", service_key_path)
                cred = credentials.Certificate(service_key_path)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred, {
                        'projectId': Config.FIREBASE_PROJECT_ID
                    })
                client = firestore.client()
                # Test connectivity
                list(client.collection("users").limit(1).stream())
                cls._db = client
                cls._is_live = True
                logger.info("Connected to live Firebase Firestore project: %s", Config.FIREBASE_PROJECT_ID)
            except Exception as e:
                logger.warning(
                    "Cloud Firestore connection could not be established (%s).\n"
                    "TIP: If using Firebase project '%s', ensure Firestore is enabled by clicking 'Create database' at:\n"
                    "https://console.firebase.google.com/project/%s/firestore\n"
                    "Operating safely with Local Firestore state store in the meantime.",
                    e, Config.FIREBASE_PROJECT_ID, Config.FIREBASE_PROJECT_ID
                )
                cls._db = LocalFirestoreClient()
                cls._is_live = False
        else:
            logger.info("No Firebase Service Account Key provided. Operating with Local Firestore state store.")
            cls._db = LocalFirestoreClient()
            cls._is_live = False

        cls._seed_initial_data()
        return cls._db

    @classmethod
    def is_live_firebase(cls):
        return cls._is_live

    @classmethod
    def _seed_initial_data(cls):
        """Seed realistic sources, users, regulatory updates, versions, summaries, and memories."""
        db = cls._db
        
        # 1. Users
        users_ref = db.collection("users")
        existing_users = list(users_ref.limit(1).stream())
        if not existing_users:
            import hashlib
            def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

            sample_users = [
                {
                    "uid": "usr-admin-01",
                    "email": "admin@legalupdate.ai",
                    "display_name": "Sarah Jenkins",
                    "role": "admin",
                    "department": "Legal & Regulatory Compliance Head",
                    "password_hash": hash_pw("admin123"),
                    "created_at": get_utc_now(),
                    "last_login_at": get_utc_now()
                },
                {
                    "uid": "usr-reviewer-01",
                    "email": "senior.counsel@legalupdate.ai",
                    "display_name": "Vikram Mehta",
                    "role": "reviewer",
                    "department": "Banking & Capital Markets Regulatory",
                    "password_hash": hash_pw("review123"),
                    "created_at": get_utc_now(),
                    "last_login_at": get_utc_now()
                },
                {
                    "uid": "usr-reviewer-02",
                    "email": "compliance.officer@legalupdate.ai",
                    "display_name": "Ananya Sharma",
                    "role": "reviewer",
                    "department": "Corporate Governance & Ethics",
                    "password_hash": hash_pw("review123"),
                    "created_at": get_utc_now(),
                    "last_login_at": get_utc_now()
                },
                {
                    "uid": "usr-viewer-01",
                    "email": "analyst@legalupdate.ai",
                    "display_name": "Rohan Gupta",
                    "role": "viewer",
                    "department": "Regulatory Intelligence Analyst",
                    "password_hash": hash_pw("viewer123"),
                    "created_at": get_utc_now(),
                    "last_login_at": get_utc_now()
                }
            ]
            for u in sample_users:
                users_ref.document(u["uid"]).set(u)
            logger.info("Seeded %d initial users in Firestore.", len(sample_users))

        # 2. Regulatory Sources
        sources_ref = db.collection("regulatory_sources")
        existing_sources = list(sources_ref.limit(1).stream())
        if not existing_sources:
            sample_sources = [
                {
                    "source_id": "src-rbi",
                    "source_code": "RBI",
                    "name": "Reserve Bank of India (RBI)",
                    "jurisdiction": "India",
                    "regulator_type": "Central Banking & Monetary Authority",
                    "base_url": "https://www.rbi.org.in",
                    "crawl_url": "https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx",
                    "category": "Banking, NBFCs, Fintech, Payment Systems",
                    "is_active": True,
                    "crawl_frequency_minutes": 60,
                    "last_crawled_at": get_utc_now(),
                    "created_at": get_utc_now(),
                    "description": "Official notifications, Master Directions, prudential norms, and guidelines for scheduled commercial banks and NBFCs."
                },
                {
                    "source_id": "src-sebi",
                    "source_code": "SEBI",
                    "name": "Securities and Exchange Board of India (SEBI)",
                    "jurisdiction": "India",
                    "regulator_type": "Securities Market Regulator",
                    "base_url": "https://www.sebi.gov.in",
                    "crawl_url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&smid=0&ssid=7",
                    "category": "Capital Markets, Listed Entities, Mutual Funds, Custodians",
                    "is_active": True,
                    "crawl_frequency_minutes": 60,
                    "last_crawled_at": get_utc_now(),
                    "created_at": get_utc_now(),
                    "description": "Regulatory circulars, listing obligations (LODR), market infrastructure, insider trading prevention, and ESG disclosure norms."
                },
                {
                    "source_id": "src-mca",
                    "source_code": "MCA",
                    "name": "Ministry of Corporate Affairs (MCA)",
                    "jurisdiction": "India",
                    "regulator_type": "Company Law & Corporate Governance",
                    "base_url": "https://www.mca.gov.in",
                    "crawl_url": "https://www.mca.gov.in/content/mca/global/en/notifications-circulars/circulars.html",
                    "category": "Companies Act, CSR, LLP, Secretarial Compliance",
                    "is_active": True,
                    "crawl_frequency_minutes": 120,
                    "last_crawled_at": get_utc_now(),
                    "created_at": get_utc_now(),
                    "description": "Statutory rules, significant beneficial ownership, statutory auditor reporting, and corporate governance amendments."
                },
                {
                    "source_id": "src-irdai",
                    "source_code": "IRDAI",
                    "name": "Insurance Regulatory and Development Authority of India (IRDAI)",
                    "jurisdiction": "India",
                    "regulator_type": "Insurance Sector Regulator",
                    "base_url": "https://irdai.gov.in",
                    "crawl_url": "https://irdai.gov.in/circulars",
                    "category": "Insurers, Brokers, Health & Life Insurance Products",
                    "is_active": True,
                    "crawl_frequency_minutes": 180,
                    "last_crawled_at": get_utc_now(),
                    "created_at": get_utc_now(),
                    "description": "Prudential limits, solvency margin guidelines, and policyholder protection circulars."
                }
            ]
            for s in sample_sources:
                sources_ref.document(s["source_id"]).set(s)
            logger.info("Seeded %d regulatory sources in Firestore.", len(sample_sources))

        # 3. Regulatory Updates, Summaries, Versions, Memories & Review History
        updates_ref = db.collection("regulatory_updates")
        existing_updates = list(updates_ref.limit(1).stream())
        if not existing_updates:
            import hashlib
            def hash_text(t): return hashlib.sha256(" ".join(t.split()).strip().encode()).hexdigest()

            curated_updates = [
                {
                    "id": "upd-rbi-2026-104",
                    "document_id": "RBI/2026-27/104",
                    "source_id": "src-rbi",
                    "source_code": "RBI",
                    "title": "Master Direction – Information Technology Governance, Risk, Controls and Assurance Practices",
                    "source_url": "https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx?Id=12648",
                    "published_date": "2026-11-04",
                    "collected_at": get_utc_now(),
                    "current_status": "pending_review",
                    "version": 1,
                    "content": """RESERVE BANK OF INDIA
DEPARTMENT OF REGULATION, CENTRAL OFFICE
MUMBAI - 400 001

RBI/2026-27/104
DoR.MCS.REC.52/01.01.003/2026-27
November 04, 2026

To: All Commercial Banks, Small Finance Banks, Payment Banks, and Upper/Middle Layer NBFCs

Master Direction – Information Technology Governance, Risk, Controls and Assurance Practices (Amendment 2026)

Please refer to earlier Master Direction on Information Technology Governance dated November 07, 2023. In view of accelerated cloud migrations, systemic concentration risk, and heightened cyber resilience requirements across the regulated sector, the Reserve Bank has finalized enhanced baseline requirements.

1. Applicability:
These revised directions apply to all Commercial Banks (excluding Regional Rural Banks), Small Finance Banks, Payments Banks, and NBFCs categorized under Upper Layer and Middle Layer of the Scale Based Regulation (SBR) framework.

2. Board Oversight and IT Strategy Committee:
The Board of Directors shall institute an IT Strategy Committee headed by an independent director. The committee shall meet at least quarterly to review cybersecurity posture, core banking platform resilience, third-party vendor dependencies, and disaster recovery recovery point objectives (RPO < 15 minutes, RTO < 60 minutes for mission-critical payment services).

3. Cloud Computing & Critical Outsourcing:
Regulated Entities (REs) hosting core accounting or customer PII in cloud environments must ensure data localization within sovereign Indian data centers, retain cryptographic keys locally under Hardware Security Modules (HSM), and mandate multi-vendor exit strategies within 90 days of contract termination.

4. Effective Date and Transition:
These directions take effect from April 01, 2027. Regulated entities shall submit a Board-approved gap assessment and execution road map to the Department of Supervision by January 31, 2027.

Yours faithfully,
Chief General Manager-in-Charge
Department of Regulation""",
                    "ai_summary": {
                        "short_summary": "RBI has issued amended IT Governance and Risk Directions mandating enhanced Board committee oversight, strict disaster recovery RPO/RTO thresholds, Indian cloud data localization, and vendor exit strategies effective April 01, 2027.",
                        "detailed_summary": "The Reserve Bank of India updated its Master Direction on IT Governance, addressing elevated cyber risks and cloud migrations across Commercial Banks and Upper/Middle Layer NBFCs. The circular mandates an IT Strategy Committee chaired by an independent director, enforces an RPO under 15 minutes and RTO under 60 minutes for payment systems, and enforces domestic data localization with local HSM key management for cloud workloads. A Board-approved transition plan is due by January 31, 2027.",
                        "key_regulatory_changes": [
                            "Mandatory Board IT Strategy Committee chaired by an Independent Director meeting quarterly.",
                            "Stricter disaster recovery metrics: RPO < 15 minutes, RTO < 60 minutes for critical payment workloads.",
                            "Cloud workloads holding customer PII must reside in Indian data centers with locally held HSM keys.",
                            "Regulated entities must implement a guaranteed 90-day multi-vendor cloud exit plan.",
                            "Board-approved gap assessment submission mandated by January 31, 2027."
                        ],
                        "important_requirements": [
                            "Conduct comprehensive technology architecture gap assessment against revised baseline standards.",
                            "Establish local HSM key management custody for all hybrid/multi-cloud deployments.",
                            "Obtain Board sign-off on IT governance framework and submit roadmap to RBI Department of Supervision."
                        ],
                        "affected_organizations": [
                            "Scheduled Commercial Banks (excluding RRBs)",
                            "Small Finance Banks & Payments Banks",
                            "Upper Layer and Middle Layer NBFCs"
                        ],
                        "potential_compliance_implications": [
                            "High operational expenditure for cloud re-architecture and HSM cryptographic key migration.",
                            "Contract renegotiations with global cloud service providers (AWS, Azure, GCP) to fulfill the 90-day exit clause.",
                            "Supervisory penalty and inspection audit points if transition roadmap is not filed by January 31, 2027."
                        ],
                        "effective_date": "2027-04-01 (Interim gap assessment roadmap due 2027-01-31)",
                        "recommended_actions": [
                            "Legal counsel should review existing master service agreements with cloud and SaaS vendors for exit terms compliance.",
                            "CISO and Head of Technology must benchmark current RPO/RTO metrics against the 15/60 minute threshold.",
                            "Prepare Board resolution charter for the IT Strategy Committee independent chairmanship."
                        ],
                        "confidence_score": 0.94,
                        "model_used": "llama-3.3-70b-versatile",
                        "disclaimer": "AI-generated regulatory analysis. Presented for human legal review. Does not constitute authoritative legal advice."
                    },
                    "historical_context": {
                        "memory_id": "mem-rbi-it-governance-2023",
                        "precedent_ref": "RBI/2023-24/MD-IT-01",
                        "precedent_date": "2023-11-07",
                        "recalled_insight": "Supercedes baseline directions from Nov 2023. Earlier policy allowed offshore disaster recovery mirrors with regulatory approval; the 2026 amendment eliminates foreign sovereign jurisdiction exemptions for core customer PII.",
                        "continuity_status": "Amended & Elevated Requirements",
                        "valid_time": "2026-11-04",
                        "transaction_time": get_utc_now(),
                        "entity_tags": ["RBI", "IT Governance", "Cloud", "Cybersecurity", "Disaster Recovery"]
                    }
                },
                {
                    "id": "upd-sebi-2026-158",
                    "document_id": "SEBI/HO/CFD/PoD-2/P/CIR/2026/158",
                    "source_id": "src-sebi",
                    "source_code": "SEBI",
                    "title": "Circular on Enhanced BRSR Core Disclosures and ESG Rating Provider Assurance Verifications",
                    "source_url": "https://www.sebi.gov.in/legal/circulars/nov-2026/enhanced-brsr-core-disclosures_158.html",
                    "published_date": "2026-11-08",
                    "collected_at": get_utc_now(),
                    "current_status": "approved",
                    "version": 1,
                    "content": """SECURITIES AND EXCHANGE BOARD OF INDIA
CORPORATE FINANCE DEPARTMENT
SEBI BHAWAN, BANDRA KURLA COMPLEX, MUMBAI

SEBI/HO/CFD/PoD-2/P/CIR/2026/158
November 08, 2026

To: All Listed Entities, Recognized Stock Exchanges, Registered ESG Rating Providers (ERPs)

Sub: Extension of BRSR Core Assurance Mandate to Top 500 Listed Entities and Value Chain Transparency

1. Under Regulation 34(2)(f) of SEBI (Listing Obligations and Disclosure Requirements) Regulations, 2015, the top 1000 listed entities by market capitalization are required to submit Business Responsibility and Sustainability Reports (BRSR).

2. It has now been decided to expand reasonable assurance of BRSR Core parameters to the top 500 listed entities commencing with FY 2026-27 annual reports. Furthermore, value chain disclosures (Scope 3 GHG emissions, job creation in small towns, supplier ethical compliance) covering at least 75% of purchases by value must be certified by an accredited independent assurance provider.

3. Conflicts of Interest for ESG Rating Providers:
ESG Rating Providers (ERPs) registered with SEBI under Chapter VIII-A of the Intermediaries Regulations shall not provide advisory, consulting, or software audit services to any entity they rate for a cooling-off period of 24 months.

4. Implementation Schedule:
The circular comes into force immediately for rating integrity norms. Mandatory assurance for top 500 companies takes effect from the financial year ending March 31, 2027.

Deputy General Manager
Corporate Finance Department""",
                    "ai_summary": {
                        "short_summary": "SEBI has broadened the mandatory reasonable assurance for BRSR Core sustainability disclosures to the top 500 listed entities and instituted strict 24-month conflict-of-interest cooling periods for ESG Rating Providers.",
                        "detailed_summary": "SEBI expanded ESG compliance requirements under LODR Regulation 34(2)(f). Beginning FY 2026-27, the top 500 listed entities must secure independent reasonable assurance on BRSR Core indicators and audit 75% of their value chain suppliers for Scope 3 emissions and ethical practices. To protect market objectivity, registered ESG Rating Providers are strictly prohibited from offering consulting or advisory services to rated corporates, enforced by a 24-month cooling-off window.",
                        "key_regulatory_changes": [
                            "Mandatory reasonable assurance of BRSR Core expanded from top 250 to top 500 listed companies by market cap.",
                            "Value chain assurance mandate covering at least 75% of purchases by value (Scope 3 GHG emissions and fair wages).",
                            "24-month cooling-off period prohibiting ESG Rating Providers from offering advisory services to rated entities."
                        ],
                        "important_requirements": [
                            "Appoint accredited independent assurance providers for FY 2026-27 sustainability report audits.",
                            "Establish automated supplier ESG data collection covering minimum 75% vendor supply chain volume.",
                            "Update corporate insider trading and conflict-of-interest declarations for ESG rating agency engagements."
                        ],
                        "affected_organizations": [
                            "Top 500 Listed Companies by Market Capitalization",
                            "SEBI-Registered ESG Rating Providers (ERPs)",
                            "Key Tier-1 and Tier-2 Supply Chain Vendors"
                        ],
                        "potential_compliance_implications": [
                            "Increased compliance auditing fees for supply chain verification.",
                            "Risk of stock exchange query or non-compliance fine under LODR if Scope 3 assurance cannot be verified.",
                            "Discontinuation of bundled consulting engagements by ESG agencies."
                        ],
                        "effective_date": "Immediate for rating agency conflict norms; FY 2026-27 for reporting entities",
                        "recommended_actions": [
                            "Audit current vendor procurement database to verify readiness for Scope 3 emissions tracing.",
                            "Engage statutory ESG auditors for gap audit before Q4 FY 2026-27 close.",
                            "Circulate notice to Procurement and Investor Relations teams."
                        ],
                        "confidence_score": 0.96,
                        "model_used": "llama-3.3-70b-versatile",
                        "disclaimer": "AI-generated regulatory analysis. Presented for human legal review. Does not constitute authoritative legal advice."
                    },
                    "historical_context": {
                        "memory_id": "mem-sebi-brsr-2023",
                        "precedent_ref": "SEBI/CIR/2023/127",
                        "precedent_date": "2023-07-12",
                        "recalled_insight": "Phased implementation of BRSR Core. Previously applied solely on a voluntary/comply-or-explain basis for entities beyond top 250. This circular converts the top 500 mandate into enforceable statutory compliance.",
                        "continuity_status": "Expansion of Pre-existing Framework",
                        "valid_time": "2026-11-08",
                        "transaction_time": get_utc_now(),
                        "entity_tags": ["SEBI", "LODR", "BRSR", "ESG", "Scope 3 Emissions"]
                    },
                    "review_history": {
                        "decision": "approved",
                        "reviewer_id": "usr-reviewer-01",
                        "reviewer_name": "Vikram Mehta",
                        "reviewer_email": "senior.counsel@legalupdate.ai",
                        "comments": "Verified against SEBI official circular repository. BRSR Core scope expansion confirmed for top 500. Summary accurately reflects 24mo cooling period.",
                        "reviewed_at": get_utc_now(),
                        "edited_summary": None
                    }
                },
                {
                    "id": "upd-mca-2026-gsr78",
                    "document_id": "MCA/CL-IV/2026/GSR-78",
                    "source_id": "src-mca",
                    "source_code": "MCA",
                    "title": "Companies (Significant Beneficial Ownership) Amendment Rules, 2026 – Digital Identification Norms",
                    "source_url": "https://www.mca.gov.in/content/mca/global/en/notifications-circulars/sbo-amendment-2026.html",
                    "published_date": "2026-11-10",
                    "collected_at": get_utc_now(),
                    "current_status": "needs_modification",
                    "version": 1,
                    "content": """MINISTRY OF CORPORATE AFFAIRS
GOVERNMENT OF INDIA
SHASTRI BHAWAN, NEW DELHI

Notification No. G.S.R. 78(E)
November 10, 2026

G.S.R. 78(E).—In exercise of the powers conferred by section 90 read with sub-sections (1) and (2) of section 469 of the Companies Act, 2013 (18 of 2013), the Central Government hereby makes the following rules further to amend the Companies (Significant Beneficial Ownership) Rules, 2018.

1. Short title and commencement:
(1) These rules may be called the Companies (Significant Beneficial Ownership) Amendment Rules, 2026.
(2) They shall come into force on the date of their publication in the Official Gazette.

2. Mandatory Digital Verified Identifier:
In the Principal Rules, after rule 4, the following rule shall be inserted, namely:
"4A. Digital Authentication of Non-Resident Beneficial Owners:
Every individual holding significant beneficial ownership (SBO) of 10% or more voting rights in a reporting company who is not a resident in India shall provide a verified Legal Entity Identifier (LEI) or certified Apostilled Passport digital credential via the MCA21 portal within 60 days of acquiring such interest."

3. Enhanced Reporting Penalties:
Failure to register Form BEN-2 within the prescribed timeline shall attract an automatic compounding inquiry under Section 454 of the Act.

Joint Secretary to the Government of India""",
                    "ai_summary": {
                        "short_summary": "MCA amended the SBO Rules requiring non-resident individuals holding 10% or more beneficial voting rights to register verified LEI or apostilled digital credentials via MCA21 within 60 days.",
                        "detailed_summary": "The Ministry of Corporate Affairs notified the Companies (Significant Beneficial Ownership) Amendment Rules, 2026. Non-resident individuals holding 10% or more significant beneficial ownership in an Indian entity must now supply verified Legal Entity Identifier (LEI) or apostilled passport credentials directly on MCA21 within 60 days. Default triggers automatic compounding procedures under Section 454.",
                        "key_regulatory_changes": [
                            "Insertion of Rule 4A requiring mandatory digital credentials (LEI or Apostilled Passport) for foreign SBOs.",
                            "Strict 60-day deadline from date of acquiring 10% or higher interest.",
                            "Direct automation of adjudication and compounding under Section 454 for BEN-2 filing defaults."
                        ],
                        "important_requirements": [
                            "Identify all non-resident shareholders possessing >= 10% voting rights or indirect control.",
                            "Procure certified digital apostilled documentation or LEI validation from international holding tiers.",
                            "File updated Form BEN-2 on the MCA21 portal within the 60-day window."
                        ],
                        "affected_organizations": [
                            "All Indian Private and Public Limited Companies with foreign shareholding tiers",
                            "Overseas corporate bodies (OCBs) and foreign family offices investing in India"
                        ],
                        "potential_compliance_implications": [
                            "Freezing of dividend and voting rights under Section 90(7) for non-compliant foreign beneficial owners.",
                            "Substantial monetary penalties on company directors and designated compliance officers."
                        ],
                        "effective_date": "Date of publication in the Official Gazette (November 10, 2026)",
                        "recommended_actions": [
                            "Dispatch urgent SBO inquiry notices (Form BEN-4) to overseas parent holding structures.",
                            "Audit company register of members against the updated Rule 4A digital identifier requirement."
                        ],
                        "confidence_score": 0.92,
                        "model_used": "llama-3.3-70b-versatile",
                        "disclaimer": "AI-generated regulatory analysis. Presented for human legal review. Does not constitute authoritative legal advice."
                    },
                    "historical_context": {
                        "memory_id": "mem-mca-sbo-2018",
                        "precedent_ref": "MCA/SBO-2018/PRINCIPAL",
                        "precedent_date": "2018-06-13",
                        "recalled_insight": "Under the 2018 SBO rules, basic physical notarized declarations were accepted with significant processing delays. Rule 4A replaces physical attestation with digital cryptographic verification.",
                        "continuity_status": "Procedural Tightening",
                        "valid_time": "2026-11-10",
                        "transaction_time": get_utc_now(),
                        "entity_tags": ["MCA", "Companies Act", "SBO", "BEN-2", "Beneficial Ownership"]
                    },
                    "review_history": {
                        "decision": "needs_modification",
                        "reviewer_id": "usr-reviewer-02",
                        "reviewer_name": "Ananya Sharma",
                        "reviewer_email": "compliance.officer@legalupdate.ai",
                        "comments": "Please explicitly highlight whether the 60-day period runs from receipt of notice or acquisition date. Clarify Section 90 penalty limits.",
                        "reviewed_at": get_utc_now(),
                        "edited_summary": None
                    }
                }
            ]

            for item in curated_updates:
                content_hash = hash_text(item["content"])
                update_id = item["id"]

                # 1. Store Update
                update_doc = {
                    "id": update_id,
                    "document_id": item["document_id"],
                    "source_id": item["source_id"],
                    "source_code": item["source_code"],
                    "title": item["title"],
                    "source_url": item["source_url"],
                    "published_date": item["published_date"],
                    "collected_at": item["collected_at"],
                    "current_status": item["current_status"],
                    "version": item["version"],
                    "content": item["content"],
                    "content_hash": content_hash,
                    "created_at": item["collected_at"],
                    "updated_at": item["collected_at"]
                }
                updates_ref.document(update_id).set(update_doc)

                # 2. Store Document Version
                v_doc = {
                    "id": f"ver-{update_id}-1",
                    "update_id": update_id,
                    "version_number": 1,
                    "title": item["title"],
                    "content": item["content"],
                    "content_hash": content_hash,
                    "diff": None,
                    "created_at": item["collected_at"]
                }
                db.collection("document_versions").document(v_doc["id"]).set(v_doc)

                # 3. Store AI Summary
                ai_sum = dict(item["ai_summary"])
                ai_sum["id"] = f"sum-{update_id}"
                ai_sum["update_id"] = update_id
                ai_sum["created_at"] = item["collected_at"]
                ai_sum["is_approved"] = (item["current_status"] == "approved")
                db.collection("ai_summaries").document(ai_sum["id"]).set(ai_sum)

                # 4. Store Historical Context (Memento Memory)
                hist = dict(item["historical_context"])
                hist["id"] = f"ctx-{update_id}"
                hist["update_id"] = update_id
                hist["document_id"] = item["document_id"]
                hist["regulator"] = item["source_code"]
                hist["created_at"] = get_utc_now()
                db.collection("historical_context").document(hist["id"]).set(hist)

                # 5. Store Review History if applicable
                if "review_history" in item:
                    rev = dict(item["review_history"])
                    rev["id"] = f"rev-{update_id}-1"
                    rev["update_id"] = update_id
                    db.collection("review_history").document(rev["id"]).set(rev)

            logger.info("Seeded %d realistic regulatory updates with AI summaries, versions, memories & reviews in Firestore.", len(curated_updates))
