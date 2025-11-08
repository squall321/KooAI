"""
KooAI Load Testing with Locust

Usage:
    # Run with Web UI
    locust --host=http://localhost:8000

    # Run headless
    locust --headless --users 100 --spawn-rate 10 --run-time 5m --host=http://localhost:8000

    # With custom settings
    locust --users 1000 --spawn-rate 100 --run-time 30m --host=http://production-server.com
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import random
import json
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KooAIUser(FastHttpUser):
    """
    Simulates a KooAI user performing typical operations
    """
    
    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)
    
    # Test data
    test_user = {
        "username": "load_test_user@example.com",
        "password": "test_password_123"
    }
    
    def on_start(self):
        """
        Called when a simulated user starts
        Initialize: login and get token
        """
        self.token = None
        self.simulation_id = None
        self.file_id = None
        
        # Login to get token
        self.login()
    
    def login(self):
        """Login and store token"""
        response = self.client.post(
            "/api/auth/login",
            json=self.test_user,
            name="/api/auth/login"
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            logger.info(f"User logged in successfully")
        else:
            logger.error(f"Login failed: {response.status_code}")
    
    def headers(self):
        """Return authentication headers"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    @task(10)
    def view_simulations_list(self):
        """
        Most common operation: view simulations list
        Weight: 10 (happens 10x more often than other tasks)
        """
        params = {
            "skip": random.randint(0, 100),
            "limit": random.choice([10, 25, 50]),
            "status": random.choice(["pending", "completed", "failed", None])
        }
        
        self.client.get(
            "/api/simulations",
            params=params,
            headers=self.headers(),
            name="/api/simulations [LIST]"
        )
    
    @task(5)
    def view_simulation_detail(self):
        """
        View specific simulation details
        Weight: 5
        """
        if self.simulation_id:
            self.client.get(
                f"/api/simulations/{self.simulation_id}",
                headers=self.headers(),
                name="/api/simulations/:id [GET]"
            )
    
    @task(2)
    def create_simulation(self):
        """
        Create new simulation
        Weight: 2
        """
        data = {
            "name": f"Load Test Simulation {random.randint(1, 10000)}",
            "description": "Created by load test",
            "metadata": {
                "solver": random.choice(["OpenFOAM", "ANSYS", "COMSOL"]),
                "version": "v2024"
            }
        }
        
        response = self.client.post(
            "/api/simulations",
            json=data,
            headers=self.headers(),
            name="/api/simulations [POST]"
        )
        
        if response.status_code == 201:
            self.simulation_id = response.json().get("id")
            logger.info(f"Created simulation: {self.simulation_id}")
    
    @task(1)
    def upload_file(self):
        """
        Upload a file (simulated small file)
        Weight: 1
        """
        if not self.simulation_id:
            return
        
        # Simulate small VTK file
        fake_file_content = b"# vtk DataFile Version 3.0\nTest Data\nASCII\n"
        
        files = {
            "file": ("test.vtk", fake_file_content, "application/octet-stream")
        }
        
        response = self.client.post(
            f"/api/simulations/{self.simulation_id}/files",
            files=files,
            headers=self.headers(),
            name="/api/simulations/:id/files [POST]"
        )
        
        if response.status_code == 201:
            self.file_id = response.json().get("file_id")
            logger.info(f"Uploaded file: {self.file_id}")
    
    @task(3)
    def view_simulation_files(self):
        """
        View files for a simulation
        Weight: 3
        """
        if self.simulation_id:
            self.client.get(
                f"/api/simulations/{self.simulation_id}/files",
                headers=self.headers(),
                name="/api/simulations/:id/files [GET]"
            )
    
    @task(1)
    def request_analysis(self):
        """
        Request AI analysis
        Weight: 1 (expensive operation)
        """
        if not self.simulation_id:
            return
        
        data = {
            "analysis_type": "llm",
            "prompt": "Quick summary of results",
            "options": {
                "model": "gpt-4",
                "temperature": 0.7
            }
        }
        
        self.client.post(
            f"/api/simulations/{self.simulation_id}/analyze",
            json=data,
            headers=self.headers(),
            name="/api/simulations/:id/analyze [POST]"
        )
    
    @task(8)
    def health_check(self):
        """
        Health check endpoint (no auth required)
        Weight: 8
        """
        self.client.get(
            "/health",
            name="/health"
        )
    
    @task(2)
    def metrics_endpoint(self):
        """
        Prometheus metrics endpoint
        Weight: 2
        """
        self.client.get(
            "/metrics",
            name="/metrics"
        )


class ReadOnlyUser(FastHttpUser):
    """
    Simulates a user who only reads data (monitoring dashboard, etc.)
    """
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.token = None
        # Simplified login for read-only user
    
    @task(5)
    def health_check(self):
        self.client.get("/health", name="/health [readonly]")
    
    @task(3)
    def metrics(self):
        self.client.get("/metrics", name="/metrics [readonly]")
    
    @task(2)
    def ready_check(self):
        self.client.get("/health/ready", name="/health/ready [readonly]")


class AdminUser(FastHttpUser):
    """
    Simulates an admin user performing management operations
    """
    
    wait_time = between(5, 10)
    
    test_admin = {
        "username": "admin@example.com",
        "password": "admin_password_123"
    }
    
    def on_start(self):
        self.token = None
        response = self.client.post("/api/auth/login", json=self.test_admin)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
    
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    @task(3)
    def view_all_users(self):
        self.client.get(
            "/api/admin/users",
            headers=self.headers(),
            name="/api/admin/users [GET]"
        )
    
    @task(2)
    def view_system_stats(self):
        self.client.get(
            "/api/admin/stats",
            headers=self.headers(),
            name="/api/admin/stats [GET]"
        )
    
    @task(1)
    def cleanup_old_data(self):
        self.client.post(
            "/api/admin/cleanup",
            headers=self.headers(),
            name="/api/admin/cleanup [POST]"
        )


# Event hooks for custom metrics

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    logger.info("=" * 60)
    logger.info("KooAI Load Test Starting")
    logger.info(f"Target: {environment.host}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    logger.info("=" * 60)
    logger.info("KooAI Load Test Completed")
    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Total failures: {environment.stats.total.num_failures}")
    logger.info(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    logger.info(f"RPS: {environment.stats.total.total_rps:.2f}")
    logger.info("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called for each request"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > 1000:  # Log slow requests (>1s)
        logger.warning(f"Slow request: {name} - {response_time:.0f}ms")


# Custom scenarios

class SpikeLoadUser(FastHttpUser):
    """
    Simulates sudden spike in traffic
    Use this to test auto-scaling behavior
    """
    
    wait_time = between(0.1, 0.5)  # Very short wait time for spike
    
    @task
    def rapid_fire(self):
        """Rapid requests"""
        self.client.get("/health")


class SteadyStateUser(FastHttpUser):
    """
    Simulates normal steady-state traffic
    """
    
    wait_time = between(5, 15)
    
    @task(5)
    def normal_browsing(self):
        self.client.get("/health")
    
    @task(2)
    def check_simulations(self):
        self.client.get("/api/simulations")


# Performance test scenarios
# Uncomment the scenario you want to run

# Scenario 1: Normal load (default)
# Run: locust -f locustfile.py --host=http://localhost:8000

# Scenario 2: Spike test
# Run: locust -f locustfile.py KooAIUser SpikeLoadUser --host=http://localhost:8000

# Scenario 3: Steady state
# Run: locust -f locustfile.py SteadyStateUser --host=http://localhost:8000

# Scenario 4: Mixed user types
# Run: locust -f locustfile.py KooAIUser:70 ReadOnlyUser:20 AdminUser:10 --host=http://localhost:8000


if __name__ == "__main__":
    """
    Run locust programmatically
    """
    import subprocess
    import sys
    
    print("KooAI Load Testing")
    print("=" * 60)
    print("\nAvailable test scenarios:")
    print("1. Normal load (KooAIUser)")
    print("2. Spike test (KooAIUser + SpikeLoadUser)")
    print("3. Steady state (SteadyStateUser)")
    print("4. Mixed users (70% KooAI, 20% ReadOnly, 10% Admin)")
    print("\nTo run with web UI:")
    print("  locust --host=http://localhost:8000")
    print("\nTo run headless:")
    print("  locust --headless --users 100 --spawn-rate 10 --run-time 5m --host=http://localhost:8000")
    print("=" * 60)
