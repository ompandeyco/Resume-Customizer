"""
Manual test for core.pdf_builder.build_resume_pdf().
Generates a PDF from realistic sample data and saves it to disk for visual
inspection. Open the output file to confirm the layout looks professional.

Run:  python test_pdf_builder.py
"""

import os
from core.pdf_builder import build_resume_pdf

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


def main():
    pdf_bytes = build_resume_pdf(SAMPLE_RESUME)

    output_path = os.path.join(os.path.dirname(__file__), "test_output_resume.pdf")
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    size_kb = len(pdf_bytes) / 1024
    print(f"[OK] PDF generated: {output_path}")
    print(f"  Size: {size_kb:.1f} KB  ({len(pdf_bytes):,} bytes)")
    print("  Open the file to visually inspect the layout.")


if __name__ == "__main__":
    main()
