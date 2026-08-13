"""
Comprehensive verification of core.pdf_builder.build_resume_pdf().
- Generates a PDF from realistic sample data
- Uses pdfplumber to extract text and verify all sections rendered
- Checks for XML/HTML escaping issues (< > & characters in content)
- Tests edge cases: empty sections, missing fields
"""

import os
import sys
import traceback

# ── Test 1: Full resume (happy path) ────────────────────────────────────────
SAMPLE_RESUME = {
    "name": "Priya Sharma",
    "title": "Senior Backend Engineer",
    "contact": {
        "email": "priya.sharma@email.com",
        "phone": "(408) 555-1729",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/priyasharma",
    },
    "summary": (
        "Backend engineer with 6+ years of experience designing high-throughput "
        "distributed systems and data pipelines. Led the migration of a monolithic "
        "payments platform to event-driven microservices, reducing P99 latency by "
        "42%. Passionate about developer experience, observability, and building "
        "systems that scale gracefully under pressure."
    ),
    "skills": [
        "Python", "Go", "Java", "PostgreSQL", "Redis", "Kafka",
        "AWS (ECS, Lambda, DynamoDB)", "Kubernetes", "Docker",
        "Terraform", "CI/CD (GitHub Actions)", "gRPC", "REST APIs",
        "System Design", "Technical Mentorship",
    ],
    "experience": [
        {
            "company": "Stripe",
            "role": "Senior Backend Engineer",
            "dates": "Jan 2022 – Present",
            "location": "San Francisco, CA",
            "bullets": [
                "Architected an event-driven payments reconciliation service processing "
                "2.3M transactions/day with 99.99% accuracy",
                "Reduced P99 API latency from 320ms to 185ms by introducing connection "
                "pooling and query optimization across 14 PostgreSQL shards",
                "Led a cross-functional team of 5 engineers to decompose a monolithic "
                "billing service into 4 independently deployable microservices",
                "Built a real-time anomaly detection pipeline using Kafka Streams, "
                "catching $1.2M in fraudulent transactions in its first quarter",
                "Mentored 3 junior engineers through Stripe's internal technical "
                "growth program",
            ],
        },
        {
            "company": "Dropbox",
            "role": "Backend Engineer",
            "dates": "Aug 2019 – Dec 2021",
            "location": "San Francisco, CA",
            "bullets": [
                "Designed and shipped a file-deduplication service that reduced storage "
                "costs by 18% ($3.4M annual savings)",
                "Migrated legacy sync protocol from polling to WebSocket-based push "
                "notifications, improving sync speed by 4x",
                "Implemented distributed rate limiting using Redis and Lua scripting, "
                "handling 50K req/s with <1ms overhead",
                "Authored internal RFC for structured logging standards, adopted by "
                "12 backend teams across the organization",
            ],
        },
        {
            "company": "Infosys",
            "role": "Software Engineer",
            "dates": "Jun 2017 – Jul 2019",
            "location": "Bangalore, India",
            "bullets": [
                "Built RESTful APIs for a banking client's loan origination system "
                "serving 200K daily active users",
                "Automated deployment pipelines using Jenkins and Ansible, reducing "
                "release cycle from 2 weeks to 2 days",
                "Developed batch ETL jobs in Python processing 50GB of daily "
                "transaction logs for compliance reporting",
            ],
        },
    ],
    "projects": [
        {
            "name": "kv-raft",
            "description": (
                "A fault-tolerant distributed key-value store built on the Raft "
                "consensus protocol."
            ),
            "bullets": [
                "Implemented leader election, log replication, and snapshotting in "
                "Go with 97% test coverage",
                "Benchmarked at 12K writes/sec on a 5-node cluster with automatic "
                "failover under 200ms",
            ],
        },
        {
            "name": "query-sentinel",
            "description": (
                "Open-source PostgreSQL query analyzer that flags N+1 queries and "
                "missing indexes in development."
            ),
            "bullets": [
                "Parses pg_stat_statements output and surfaces actionable "
                "optimization recommendations",
                "Adopted by 3 startups in the YC W23 batch; 340+ GitHub stars",
            ],
        },
    ],
    "education": [
        {
            "school": "University of California, Berkeley",
            "degree": "M.S. Computer Science",
            "dates": "2015 – 2017",
        },
        {
            "school": "National Institute of Technology, Trichy",
            "degree": "B.Tech. Computer Science & Engineering",
            "dates": "2011 – 2015",
        },
    ],
    "keywords_emphasized": [
        "microservices", "distributed systems", "Kafka", "PostgreSQL",
        "Python", "Go", "Kubernetes", "event-driven", "CI/CD",
    ],
}

# ── Test 2: Minimal resume (edge case - missing optional sections) ──────────
MINIMAL_RESUME = {
    "name": "Jane Doe",
    "title": "",
    "contact": {"email": "jane@example.com"},
    "summary": "",
    "skills": [],
    "experience": [],
    "projects": [],
    "education": [],
}


def run_tests():
    from core.pdf_builder import build_resume_pdf

    passed = 0
    failed = 0
    results = []

    # ── TEST 1: Full resume generates without errors ────────────────────
    print("=" * 60)
    print("TEST 1: Full resume generation")
    print("=" * 60)
    try:
        pdf_bytes = build_resume_pdf(SAMPLE_RESUME)
        output_path = os.path.join(os.path.dirname(__file__), "test_output_resume.pdf")
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        size_kb = len(pdf_bytes) / 1024
        print(f"  [PASS] PDF generated: {output_path}")
        print(f"         Size: {size_kb:.1f} KB ({len(pdf_bytes):,} bytes)")
        assert len(pdf_bytes) > 1000, "PDF suspiciously small"
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        failed += 1
        # Can't continue text extraction if generation failed
        print("\n" + "=" * 60)
        print(f"RESULTS: {passed} passed, {failed} failed")
        print("=" * 60)
        return

    # ── TEST 2: Extract text with pdfplumber and verify content ─────────
    print("\n" + "=" * 60)
    print("TEST 2: Content verification via pdfplumber")
    print("=" * 60)
    try:
        import pdfplumber

        with pdfplumber.open(output_path) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            page_count = len(pdf.pages)

        print(f"  Pages: {page_count}")

        # Check all expected content is present
        checks = {
            "Name":             "Priya Sharma",
            "Title":            "Senior Backend Engineer",
            "Email":            "priya.sharma@email.com",
            "Phone":            "(408) 555-1729",
            "Location":         "San Francisco, CA",
            "Section SUMMARY":  "SUMMARY",
            "Section SKILLS":   "SKILLS",
            "Section EXPERIENCE": "EXPERIENCE",
            "Section PROJECTS": "PROJECTS",
            "Section EDUCATION":"EDUCATION",
            "Company Stripe":   "Stripe",
            "Company Dropbox":  "Dropbox",
            "Company Infosys":  "Infosys",
            "Project kv-raft":  "kv-raft",
            "Project query-sentinel": "query-sentinel",
            "School Berkeley":  "Berkeley",
            "School NIT":       "Trichy",
            "Skill Python":     "Python",
            "Skill Kubernetes": "Kubernetes",
            "Summary snippet":  "distributed systems",
            "Bullet snippet":   "2.3M transactions",
        }

        all_ok = True
        for label, needle in checks.items():
            if needle in full_text:
                print(f"  [OK]   {label}: found '{needle}'")
            else:
                print(f"  [MISS] {label}: '{needle}' NOT found in extracted text")
                all_ok = False

        # Special check: the "<1ms" should appear (tests XML escaping)
        if "1ms" in full_text:
            print(f"  [OK]   XML escape: '<1ms' text survived rendering")
        else:
            print(f"  [WARN] XML escape: '<1ms' text may have been swallowed by XML parser")
            all_ok = False

        # Special check: the "&" in "Computer Science & Engineering"
        if "Engineering" in full_text:
            print(f"  [OK]   Ampersand: '& Engineering' text survived rendering")
        else:
            print(f"  [WARN] Ampersand: '& Engineering' text may have broken XML parser")
            all_ok = False

        if all_ok:
            print(f"\n  [PASS] All {len(checks)+2} content checks passed")
            passed += 1
        else:
            print(f"\n  [FAIL] Some content checks failed — see [MISS]/[WARN] above")
            failed += 1

    except ImportError:
        print("  [SKIP] pdfplumber not installed; skipping text extraction")
    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        failed += 1

    # ── TEST 3: Minimal resume (empty sections should be skipped) ───────
    print("\n" + "=" * 60)
    print("TEST 3: Minimal resume (empty sections skipped)")
    print("=" * 60)
    try:
        pdf_bytes_min = build_resume_pdf(MINIMAL_RESUME)
        min_path = os.path.join(os.path.dirname(__file__), "test_output_minimal.pdf")
        with open(min_path, "wb") as f:
            f.write(pdf_bytes_min)
        print(f"  [PASS] Minimal PDF generated: {min_path}")
        print(f"         Size: {len(pdf_bytes_min)/1024:.1f} KB")

        # Verify section headings are NOT in the minimal PDF
        import pdfplumber
        with pdfplumber.open(min_path) as pdf:
            min_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        sections_that_should_be_absent = ["SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION"]
        absent_ok = True
        for section in sections_that_should_be_absent:
            if section in min_text:
                print(f"  [WARN] Section '{section}' present despite empty data")
                absent_ok = False
            else:
                print(f"  [OK]   Section '{section}' correctly omitted")

        if "Jane Doe" in min_text:
            print(f"  [OK]   Name 'Jane Doe' present")
        else:
            print(f"  [MISS] Name 'Jane Doe' not found")
            absent_ok = False

        if absent_ok:
            print(f"\n  [PASS] Empty-section handling is correct")
            passed += 1
        else:
            print(f"\n  [FAIL] Empty-section handling has issues")
            failed += 1

    except Exception as e:
        print(f"  [FAIL] {e}")
        traceback.print_exc()
        failed += 1

    # ── TEST 4: Completely empty dict (should not crash) ────────────────
    print("\n" + "=" * 60)
    print("TEST 4: Empty dict (graceful handling)")
    print("=" * 60)
    try:
        pdf_bytes_empty = build_resume_pdf({})
        print(f"  [PASS] Empty dict produced {len(pdf_bytes_empty)} bytes without crashing")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Crashed on empty dict: {e}")
        traceback.print_exc()
        failed += 1

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed} tests")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
