"""
Locust load testing configuration

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""

import os
import json
import random
from io import BytesIO
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


class SimulationAPIUser(FastHttpUser):
    """
    Simulates a user interacting with the Simulation API
    
    - Upload simulations
    - Retrieve simulation details
    - Analyze fields
    - List simulations
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.simulation_ids = []
        self.uploaded_count = 0
    
    @task(3)
    def list_simulations(self):
        """List all simulations (high frequency task)"""
        with self.client.get(
            "/api/v1/simulations",
            catch_response=True,
            name="/api/v1/simulations [LIST]"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Store simulation IDs for other tasks
                    if data and len(data) > 0:
                        self.simulation_ids = [s.get("simulation_id") for s in data if s.get("simulation_id")]
                    response.success()
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_simulation_details(self):
        """Get details of a specific simulation"""
        if not self.simulation_ids:
            return
        
        sim_id = random.choice(self.simulation_ids)
        with self.client.get(
            f"/api/v1/simulations/{sim_id}",
            catch_response=True,
            name="/api/v1/simulations/[id] [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Remove from list if not found
                if sim_id in self.simulation_ids:
                    self.simulation_ids.remove(sim_id)
                response.success()  # Not a failure, just not found
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def upload_simulation(self):
        """Upload a new simulation (lower frequency)"""
        # Generate small CSV data
        csv_data = self._generate_csv_data(points=50)
        
        files = {
            "file": ("test_simulation.csv", csv_data, "text/csv")
        }
        data = {
            "name": f"Load Test Simulation {self.uploaded_count}",
            "auto_analyze": "false"
        }
        
        with self.client.post(
            "/api/v1/simulations/upload",
            files=files,
            data=data,
            catch_response=True,
            name="/api/v1/simulations/upload [POST]"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    sim_id = result.get("simulation_id")
                    if sim_id:
                        self.simulation_ids.append(sim_id)
                        self.uploaded_count += 1
                    response.success()
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def analyze_field(self):
        """Analyze a field of a simulation"""
        if not self.simulation_ids:
            return
        
        sim_id = random.choice(self.simulation_ids)
        field_name = random.choice(["temperature", "pressure", "velocity"])
        
        payload = {
            "field_name": field_name,
            "include_extremes": random.choice([True, False]),
            "include_outliers": random.choice([True, False])
        }
        
        with self.client.post(
            f"/api/v1/simulations/{sim_id}/analyze",
            json=payload,
            catch_response=True,
            name="/api/v1/simulations/[id]/analyze [POST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [400, 404]:
                # Field not found or simulation not found
                response.success()  # Not a performance failure
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def convergence_analysis(self):
        """Run convergence analysis"""
        if not self.simulation_ids:
            return
        
        sim_id = random.choice(self.simulation_ids)
        
        payload = {
            "field_name": "temperature",
            "window_size": random.randint(3, 10)
        }
        
        with self.client.post(
            f"/api/v1/simulations/{sim_id}/convergence",
            json=payload,
            catch_response=True,
            name="/api/v1/simulations/[id]/convergence [POST]"
        ) as response:
            if response.status_code in [200, 400, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def spatial_analysis(self):
        """Run spatial analysis"""
        if not self.simulation_ids:
            return
        
        sim_id = random.choice(self.simulation_ids)
        
        payload = {
            "field_name": "temperature",
            "min_value": 300.0,
            "max_value": 500.0
        }
        
        with self.client.post(
            f"/api/v1/simulations/{sim_id}/spatial",
            json=payload,
            catch_response=True,
            name="/api/v1/simulations/[id]/spatial [POST]"
        ) as response:
            if response.status_code in [200, 400, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check API health"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    def _generate_csv_data(self, points: int = 100) -> BytesIO:
        """Generate CSV simulation data"""
        csv_lines = ["x,y,z,temperature,pressure"]
        
        for i in range(points):
            x = random.uniform(0, 10)
            y = random.uniform(0, 10)
            z = random.uniform(0, 10)
            temp = random.uniform(300, 500)
            pressure = random.uniform(100000, 102000)
            csv_lines.append(f"{x:.2f},{y:.2f},{z:.2f},{temp:.2f},{pressure:.2f}")
        
        csv_content = "\n".join(csv_lines)
        return BytesIO(csv_content.encode('utf-8'))


class ReadOnlyUser(FastHttpUser):
    """
    Read-only user that only queries data (no uploads)
    
    Useful for testing read-heavy workloads
    """
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.simulation_ids = []
        # Get initial list of simulations
        self.list_simulations()
    
    @task(5)
    def list_simulations(self):
        """List simulations frequently"""
        response = self.client.get("/api/v1/simulations")
        if response.status_code == 200:
            data = response.json()
            if data:
                self.simulation_ids = [s.get("simulation_id") for s in data if s.get("simulation_id")]
    
    @task(3)
    def get_simulation(self):
        """Get simulation details"""
        if self.simulation_ids:
            sim_id = random.choice(self.simulation_ids)
            self.client.get(f"/api/v1/simulations/{sim_id}")
    
    @task(2)
    def analyze_field(self):
        """Analyze field"""
        if self.simulation_ids:
            sim_id = random.choice(self.simulation_ids)
            self.client.post(
                f"/api/v1/simulations/{sim_id}/analyze",
                json={"field_name": "temperature"}
            )
    
    @task(1)
    def health_check(self):
        """Health check"""
        self.client.get("/health")


class WriteHeavyUser(FastHttpUser):
    """
    Write-heavy user that frequently uploads simulations
    
    Useful for testing write-heavy workloads and database performance
    """
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.upload_count = 0
    
    @task(5)
    def upload_simulation(self):
        """Upload simulation frequently"""
        csv_data = self._generate_csv_data(points=100)
        
        files = {"file": ("test.csv", csv_data, "text/csv")}
        data = {"name": f"Write Test {self.upload_count}"}
        
        response = self.client.post(
            "/api/v1/simulations/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            self.upload_count += 1
    
    @task(1)
    def list_simulations(self):
        """Check simulations occasionally"""
        self.client.get("/api/v1/simulations")
    
    def _generate_csv_data(self, points: int = 100) -> BytesIO:
        """Generate CSV data"""
        csv_lines = ["x,y,z,temperature,pressure"]
        for i in range(points):
            csv_lines.append(f"{i},{i},{i},{300+i},{101325}")
        return BytesIO("\n".join(csv_lines).encode('utf-8'))


# Event listeners for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("Load test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
