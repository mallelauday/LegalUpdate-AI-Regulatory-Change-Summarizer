import logging
import hashlib
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import mongomock
from config import Config
from utils.helpers import get_utc_now, generate_content_hash

logger = logging.getLogger("legalupdate.database")

class Database:
    client = None
    db = None
    is_mock = False

    @classmethod
    def connect(cls):
        """Connect to MongoDB Atlas or local MongoDB; fallback to mongomock if unavailable."""
        if cls.db is not None:
            return cls.db

        try:
            logger.info("Attempting MongoDB connection: %s", Config.MONGO_URI)
            client = MongoClient(
                Config.MONGO_URI,
                serverSelectionTimeoutMS=2500,
                connectTimeoutMS=2500
            )
            # Force server connection check
            client.admin.command('ping')
            cls.client = client
            cls.db = client[Config.MONGO_DB_NAME]
            cls.is_mock = False
            logger.info("Connected to MongoDB successfully: %s", Config.MONGO_DB_NAME)
        except Exception as e:
            logger.warning(
                "Could not connect to external MongoDB (%s). Initializing in-memory Mongomock database for safe, reliable operation.",
                str(e)
            )
            cls.client = mongomock.MongoClient()
            cls.db = cls.client[Config.MONGO_DB_NAME]
            cls.is_mock = True

        cls._init_indexes()
        cls._seed_initial_data()
        return cls.db

    @classmethod
    def get_collection(cls, name: str):
        if cls.db is None:
            cls.connect()
        return cls.db[name]

    @classmethod
    def _init_indexes(cls):
        """Create optimized indexes for all core collections."""
        try:
            db = cls.db
            db.users.create_index([("email", ASCENDING)], unique=True)
            db.regulatory_sources.create_index([("source_code", ASCENDING)], unique=True)
            db.regulatory_updates.create_index([("source_id", ASCENDING), ("source_url", ASCENDING)])
            db.regulatory_updates.create_index([("content_hash", ASCENDING)])
            db.regulatory_updates.create_index([("published_date", DESCENDING)])
            db.regulatory_updates.create_index([("current_status", ASCENDING)])
            db.update_versions.create_index([("update_id", ASCENDING), ("version_number", DESCENDING)])
            db.ai_summaries.create_index([("update_id", ASCENDING)])
            db.review_history.create_index([("update_id", ASCENDING)])
            db.memory_references.create_index([("update_id", ASCENDING)])
            db.memory_references.create_index([("memory_id", ASCENDING)])
            logger.info("Database indexes initialized successfully.")
        except Exception as e:
            logger.error("Error creating indexes: %s", e)

    @classmethod
    def _seed_initial_data(cls):
        """Seed default sources, users, and realistic regulatory updates if empty."""
        db = cls.db
        
        # 1. Seed Users
        if db.users.count_documents({}) == 0:
            def hash_pw(pw: str) -> str:
                return hashlib.sha256(pw.encode()).hexdigest()

            sample_users = [
                {
                    "name": "Sarah Jenkins",
                    "email": "admin@legalupdate.ai",
                    "password_hash": hash_pw("admin123"),
                    "role": "admin",
                    "department": "Legal & Compliance Leadership",
                    "created_at": get_utc_now()
                },
                {
                    "name": "Vikram Mehta",
                    "email": "senior.counsel@legalupdate.ai",
                    "password_hash": hash_pw("review123"),
                    "role": "reviewer",
                    "department": "Banking & Capital Markets Regulatory",
                    "created_at": get_utc_now()
                },
                {
                    "name": "Ananya Sharma",
                    "email": "compliance.officer@legalupdate.ai",
                    "password_hash": hash_pw("review123"),
                    "role": "reviewer",
                    "department": "Corporate Governance & Ethics",
                    "created_at": get_utc_now()
                },
                {
                    "name": "Rohan Gupta",
                    "email": "analyst@legalupdate.ai",
                    "password_hash": hash_pw("viewer123"),
                    "role": "viewer",
                    "department": "Regulatory Intelligence Analyst",
                    "created_at": get_utc_now()
                }
            ]
            db.users.insert_many(sample_users)
            logger.info("Seeded %d initial users.", len(sample_users))

        # 2. Seed Regulatory Sources
        if db.regulatory_sources.count_documents({}) == 0:
            sample_sources = [
                {
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
                    "description": "Official circulars, notifications, master directions, and monetary policy guidelines issued by RBI."
                },
                {
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
                    "description": "Regulatory circulars, listing obligations (LODR), insider trading norms, and investment management updates."
                },
                {
                    "source_code": "MCA",
                    "name": "Ministry of Corporate Affairs (MCA)",
                    "jurisdiction": "India",
                    "regulator_type": "Corporate Governance & Company Law",
                    "base_url": "https://www.mca.gov.in",
                    "crawl_url": "https://www.mca.gov.in/content/mca/global/en/notifications-circulars/circulars.html",
                    "category": "Companies Act, CSR, LLP, Secretarial Compliance",
                    "is_active": True,
                    "crawl_frequency_minutes": 120,
                    "last_crawled_at": get_utc_now(),
                    "created_at": get_utc_now(),
                    "description": "Company law amendments, filing rules, ESG disclosures, and corporate governance notifications."
                },
                {
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
            db.regulatory_sources.insert_many(sample_sources)
            logger.info("Seeded %d regulatory sources.", len(sample_sources))

        # 3. Seed Realistic Regulatory Updates, AI Summaries & Memento References
        if db.regulatory_updates.count_documents({}) == 0:
            rbi_source = db.regulatory_sources.find_one({"source_code": "RBI"})
            sebi_source = db.regulatory_sources.find_one({"source_code": "SEBI"})
            mca_source = db.regulatory_sources.find_one({"source_code": "MCA"})

            updates_data = [
                {
                    "document_id": "RBI/2026-27/104",
                    "source_id": str(rbi_source["_id"]) if rbi_source else "RBI",
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

Madam / Dear Sir,

Master Direction – Information Technology Governance, Risk, Controls and Assurance Practices (Amendment 2026)

Please refer to the earlier Master Direction on Information Technology Governance dated November 07, 2023. In view of rapid digital transformation, cloud adoption, and heightened cyber resiliency imperatives across the regulated sector, the Reserve Bank has finalized enhanced baseline requirements for enterprise technology governance.

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
                    "memento_context": {
                        "historical_precedent_id": "RBI/2023-24/MD-IT-01",
                        "related_circular_date": "2023-11-07",
                        "recalled_insight": "Supercedes baseline directions from Nov 2023. Earlier policy allowed offshore disaster recovery mirrors with regulatory approval; the 2026 amendment eliminates foreign sovereign jurisdiction exemptions for core customer PII.",
                        "continuity_status": "Amended & Elevated Requirements"
                    }
                },
                {
                    "document_id": "SEBI/HO/CFD/PoD-2/P/CIR/2026/158",
                    "source_id": str(sebi_source["_id"]) if sebi_source else "SEBI",
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
                    "memento_context": {
                        "historical_precedent_id": "SEBI/CIR/2023/127",
                        "related_circular_date": "2023-07-12",
                        "recalled_insight": "Phased implementation of BRSR Core. Previously applied solely on a voluntary/comply-or-explain basis for entities beyond top 250. This circular converts the top 500 mandate into enforceable statutory compliance.",
                        "continuity_status": "Expansion of Pre-existing Framework"
                    }
                },
                {
                    "document_id": "MCA/CL-IV/2026/GSR-78",
                    "source_id": str(mca_source["_id"]) if mca_source else "MCA",
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
                    "memento_context": {
                        "historical_precedent_id": "MCA/SBO-2018/PRINCIPAL",
                        "related_circular_date": "2018-06-13",
                        "recalled_insight": "Under the 2018 SBO rules, basic physical notarized declarations were accepted with significant processing delays. Rule 4A replaces physical attestation with digital cryptographic verification.",
                        "continuity_status": "Procedural Tightening"
                    }
                }
            ]

            for item in updates_data:
                content_hash = generate_content_hash(item["content"])
                update_doc = {
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
                res = db.regulatory_updates.insert_one(update_doc)
                update_id = str(res.inserted_id)

                # Store initial version
                db.update_versions.insert_one({
                    "update_id": update_id,
                    "version_number": 1,
                    "title": item["title"],
                    "content": item["content"],
                    "content_hash": content_hash,
                    "diff": None,
                    "created_at": item["collected_at"]
                })

                # Store AI summary
                ai_sum = item["ai_summary"]
                ai_sum["update_id"] = update_id
                ai_sum["created_at"] = item["collected_at"]
                ai_sum["is_approved"] = (item["current_status"] == "approved")
                db.ai_summaries.insert_one(ai_sum)

                # Store Memento Memory Reference
                mem_ctx = item["memento_context"]
                mem_doc = {
                    "memory_id": f"mem-{item['document_id'].replace('/', '-').lower()}",
                    "update_id": update_id,
                    "document_id": item["document_id"],
                    "regulator": item["source_code"],
                    "precedent_ref": mem_ctx.get("historical_precedent_id"),
                    "precedent_date": mem_ctx.get("related_circular_date"),
                    "recalled_context": mem_ctx.get("recalled_insight"),
                    "continuity_status": mem_ctx.get("continuity_status"),
                    "valid_time": item["published_date"],
                    "transaction_time": item["collected_at"],
                    "entity_tags": [item["source_code"], "Compliance", "Regulatory Change"],
                    "created_at": get_utc_now()
                }
                db.memory_references.insert_one(mem_doc)

                # If status is approved or needs modification, add review history
                if item["current_status"] == "approved":
                    db.review_history.insert_one({
                        "update_id": update_id,
                        "reviewer_name": "Vikram Mehta",
                        "reviewer_email": "senior.counsel@legalupdate.ai",
                        "decision": "approved",
                        "comments": "Verified against SEBI official gazette. BRSR Core scope expansion confirmed for top 500. Summary accurately reflects 24mo cooling period.",
                        "reviewed_at": get_utc_now(),
                        "edited_summary": None
                    })
                elif item["current_status"] == "needs_modification":
                    db.review_history.insert_one({
                        "update_id": update_id,
                        "reviewer_name": "Ananya Sharma",
                        "reviewer_email": "compliance.officer@legalupdate.ai",
                        "decision": "needs_modification",
                        "comments": "Please explicitly highlight whether the 60-day period runs from receipt of notice or acquisition date. Clarify Section 90 penalty limits.",
                        "reviewed_at": get_utc_now(),
                        "edited_summary": None
                    })

            logger.info("Seeded %d realistic regulatory updates with AI summaries and Memento references.", len(updates_data))

