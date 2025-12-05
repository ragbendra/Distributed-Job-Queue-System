#!/usr/bin/env python3
"""
Script to submit test jobs to the queue.
"""
import requests
import time
import random

API_URL = "http://localhost:8000"

def submit_job(job_type, payload, priority="medium"):
    """Submit a job to the queue."""
    response = requests.post(
        f"{API_URL}/api/v1/jobs",
        json={
            "job_type": job_type,
            "priority": priority,
            "payload": payload,
            "max_retries": 3,
        }
    )
    return response.json()

def main():
    """Submit various test jobs."""
    print("🚀 Submitting test jobs...")
    
    # Submit email jobs
    for i in range(5):
        job = submit_job(
            "send_email",
            {
                "to": f"user{i}@example.com",
                "subject": f"Test Email {i}",
                "body": "This is a test email",
                "failure_rate": 0.2,  # 20% failure rate for testing retries
            },
            priority=random.choice(["high", "medium", "low"])
        )
        print(f"✅ Submitted email job: {job['job_id']}")
        time.sleep(0.5)
    
    # Submit video processing jobs
    for i in range(3):
        job = submit_job(
            "process_video",
            {
                "video_url": f"https://example.com/video{i}.mp4",
                "output_format": "mp4",
                "duration": 5,
            },
            priority="medium"
        )
        print(f"✅ Submitted video job: {job['job_id']}")
        time.sleep(0.5)
    
    # Submit web scraping jobs
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://www.python.org",
    ]
    
    for url in urls:
        job = submit_job(
            "scrape_website",
            {
                "url": url,
                "selector": "title",
                "timeout": 10,
            },
            priority="low"
        )
        print(f"✅ Submitted scraper job: {job['job_id']}")
        time.sleep(0.5)
    
    print("\n✨ All test jobs submitted!")
    print(f"📊 View dashboard at: http://localhost:3000")
    print(f"📖 View API docs at: {API_URL}/docs")

if __name__ == "__main__":
    main()
