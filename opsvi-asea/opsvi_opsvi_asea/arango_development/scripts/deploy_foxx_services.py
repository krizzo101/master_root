#!/usr/bin/env python3
"""
Foxx Services Deployment
========================

Deploys our Knowledge API and Graph Analytics API as accessible HTTP endpoints
"""

import json
import logging
import time
import requests
from typing import Dict, List, Any
from arango import ArangoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FoxxServiceDeployer:
    """Deploy and manage Foxx services"""

    def __init__(self):
        """Initialize with database connection"""
        self.client = ArangoClient(hosts="http://127.0.0.1:8529")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_dev_password"
        )
        self.base_url = "http://127.0.0.1:8529"
        self.auth = ("root", "arango_dev_password")

    def deploy_service(
        self, service_path: str, mount_point: str, service_name: str
    ) -> Dict[str, Any]:
        """Deploy a Foxx service"""
        logger.info(f"Deploying {service_name} to {mount_point}...")

        try:
            # Create service bundle (simplified - in production would use proper bundling)
            import zipfile
            import os

            bundle_path = f"/tmp/{service_name}_bundle.zip"

            with zipfile.ZipFile(bundle_path, "w") as bundle:
                # Add manifest.json
                manifest_path = f"{service_path}/manifest.json"
                if os.path.exists(manifest_path):
                    bundle.write(manifest_path, "manifest.json")

                # Add index.js
                index_path = f"{service_path}/index.js"
                if os.path.exists(index_path):
                    bundle.write(index_path, "index.js")

            # Deploy via Foxx API
            deploy_url = f"{self.base_url}/_db/asea_prod_db/_api/foxx/service"

            with open(bundle_path, "rb") as bundle_file:
                files = {"service": bundle_file}
                params = {"mount": mount_point}

                response = requests.post(
                    deploy_url, files=files, params=params, auth=self.auth
                )

            # Clean up bundle
            os.remove(bundle_path)

            if response.status_code in [200, 201]:
                logger.info(f"✓ {service_name} deployed successfully")
                return {
                    "service_name": service_name,
                    "mount_point": mount_point,
                    "status": "deployed",
                    "response": response.json() if response.text else {},
                }
            else:
                logger.error(
                    f"✗ {service_name} deployment failed: {response.status_code} - {response.text}"
                )
                return {
                    "service_name": service_name,
                    "mount_point": mount_point,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            logger.error(f"✗ {service_name} deployment error: {e}")
            return {
                "service_name": service_name,
                "mount_point": mount_point,
                "status": "error",
                "error": str(e),
            }

    def test_service_endpoints(
        self, mount_point: str, service_name: str
    ) -> Dict[str, Any]:
        """Test deployed service endpoints"""
        logger.info(f"Testing {service_name} endpoints...")

        endpoint_tests = []
        base_service_url = f"{self.base_url}/_db/asea_prod_db{mount_point}"

        # Define test endpoints based on service
        if "knowledge" in service_name.lower():
            test_endpoints = [
                {"path": "/health", "method": "GET", "description": "Health check"},
                {
                    "path": "/search",
                    "method": "GET",
                    "params": {"q": "machine learning"},
                    "description": "Search functionality",
                },
                {
                    "path": "/stats",
                    "method": "GET",
                    "description": "Knowledge statistics",
                },
            ]
        else:  # graph analytics
            test_endpoints = [
                {"path": "/health", "method": "GET", "description": "Health check"},
                {
                    "path": "/graph/stats",
                    "method": "GET",
                    "description": "Graph statistics",
                },
                {
                    "path": "/influence",
                    "method": "GET",
                    "description": "Influence analysis",
                },
            ]

        for endpoint in test_endpoints:
            try:
                url = base_service_url + endpoint["path"]

                if endpoint["method"] == "GET":
                    response = requests.get(
                        url,
                        params=endpoint.get("params", {}),
                        auth=self.auth,
                        timeout=10,
                    )
                else:
                    response = requests.post(url, auth=self.auth, timeout=10)

                endpoint_result = {
                    "endpoint": endpoint["path"],
                    "method": endpoint["method"],
                    "description": endpoint["description"],
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "working": response.status_code == 200,
                    "response_preview": response.text[:200] if response.text else None,
                }

                endpoint_tests.append(endpoint_result)

                status_icon = "✓" if response.status_code == 200 else "✗"
                logger.info(
                    f"{status_icon} {endpoint['path']}: {response.status_code} ({response.elapsed.total_seconds():.3f}s)"
                )

            except Exception as e:
                endpoint_tests.append(
                    {
                        "endpoint": endpoint["path"],
                        "method": endpoint["method"],
                        "description": endpoint["description"],
                        "working": False,
                        "error": str(e),
                    }
                )
                logger.error(f"✗ {endpoint['path']}: {e}")

        return {
            "service_name": service_name,
            "mount_point": mount_point,
            "endpoint_tests": endpoint_tests,
            "working_endpoints": len(
                [t for t in endpoint_tests if t.get("working", False)]
            ),
            "total_endpoints": len(endpoint_tests),
        }

    def list_deployed_services(self) -> List[Dict[str, Any]]:
        """List all deployed Foxx services"""
        logger.info("Listing deployed Foxx services...")

        try:
            list_url = f"{self.base_url}/_db/asea_prod_db/_api/foxx"
            response = requests.get(list_url, auth=self.auth)

            if response.status_code == 200:
                services = response.json()
                logger.info(f"Found {len(services)} deployed services")
                return services
            else:
                logger.error(f"Failed to list services: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error listing services: {e}")
            return []

    def create_service_documentation(
        self, deployment_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create documentation for deployed services"""
        logger.info("Creating service documentation...")

        documentation = {
            "deployment_timestamp": time.time(),
            "base_url": f"{self.base_url}/_db/asea_prod_db",
            "authentication": "Basic Auth (root/arango_dev_password)",
            "services": [],
        }

        for result in deployment_results:
            if result["status"] == "deployed":
                service_doc = {
                    "name": result["service_name"],
                    "mount_point": result["mount_point"],
                    "full_url": f"{self.base_url}/_db/asea_prod_db{result['mount_point']}",
                    "endpoints": self._get_service_endpoints(result["service_name"]),
                    "status": "active",
                }
                documentation["services"].append(service_doc)

        return documentation

    def _get_service_endpoints(self, service_name: str) -> List[Dict[str, Any]]:
        """Get endpoint documentation for a service"""
        if "knowledge" in service_name.lower():
            return [
                {
                    "path": "/search",
                    "method": "GET",
                    "description": "Full-text search across knowledge collections",
                    "parameters": [
                        "q (search term)",
                        "limit (max results)",
                        "collections (filter)",
                    ],
                    "example": "/search?q=machine%20learning&limit=10",
                },
                {
                    "path": "/search/advanced",
                    "method": "POST",
                    "description": "Advanced search with filters and sorting",
                    "body": {
                        "searchTerm": "string",
                        "filters": "object",
                        "sort": "string",
                    },
                    "example": "POST with JSON body",
                },
                {
                    "path": "/entity/{id}/relationships",
                    "method": "GET",
                    "description": "Get entity relationships through knowledge graph",
                    "parameters": [
                        "depth (traversal depth)",
                        "minStrength (min relationship strength)",
                    ],
                    "example": "/entity/entities%2F123/relationships?depth=2",
                },
                {
                    "path": "/entity",
                    "method": "POST",
                    "description": "Create new entity with optional relationships",
                    "body": {"entity": "object", "relationships": "array"},
                    "example": "POST with entity data",
                },
                {
                    "path": "/analytics/centrality",
                    "method": "GET",
                    "description": "Analyze entity centrality in knowledge graph",
                    "parameters": ["minConnections", "limit"],
                    "example": "/analytics/centrality?minConnections=1&limit=20",
                },
                {
                    "path": "/stats",
                    "method": "GET",
                    "description": "Get knowledge graph statistics",
                    "parameters": [],
                    "example": "/stats",
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check endpoint",
                    "parameters": [],
                    "example": "/health",
                },
            ]
        else:  # graph analytics
            return [
                {
                    "path": "/graph/stats",
                    "method": "GET",
                    "description": "Get comprehensive graph statistics",
                    "parameters": ["graph (graph name)"],
                    "example": "/graph/stats?graph=knowledge_network",
                },
                {
                    "path": "/communities",
                    "method": "GET",
                    "description": "Detect communities in the graph",
                    "parameters": ["graph", "minSize", "limit"],
                    "example": "/communities?graph=knowledge_network&minSize=3",
                },
                {
                    "path": "/paths/{from}/{to}",
                    "method": "GET",
                    "description": "Find shortest paths between vertices",
                    "parameters": ["graph", "limit"],
                    "example": "/paths/entities%2F123/entities%2F456?graph=knowledge_network",
                },
                {
                    "path": "/influence",
                    "method": "GET",
                    "description": "Analyze vertex influence and reach",
                    "parameters": ["vertex", "graph", "depth", "limit"],
                    "example": "/influence?vertex=entities%2F123&depth=3",
                },
                {
                    "path": "/clustering",
                    "method": "GET",
                    "description": "Analyze graph clustering coefficient",
                    "parameters": ["graph", "sample"],
                    "example": "/clustering?graph=knowledge_network&sample=100",
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check endpoint",
                    "parameters": [],
                    "example": "/health",
                },
            ]

    def deploy_all_services(self) -> Dict[str, Any]:
        """Deploy all Foxx services"""
        logger.info("Deploying all Foxx services...")

        services_to_deploy = [
            {
                "path": "/home/opsvi/asea/foxx_services/knowledge_api",
                "mount": "/knowledge",
                "name": "knowledge_api",
            },
            {
                "path": "/home/opsvi/asea/foxx_services/graph_analytics_api",
                "mount": "/analytics",
                "name": "graph_analytics_api",
            },
        ]

        deployment_results = []
        testing_results = []

        # Deploy services
        for service in services_to_deploy:
            result = self.deploy_service(
                service["path"], service["mount"], service["name"]
            )
            deployment_results.append(result)

            # Test endpoints if deployment was successful
            if result["status"] == "deployed":
                test_result = self.test_service_endpoints(
                    service["mount"], service["name"]
                )
                testing_results.append(test_result)

        # Create documentation
        documentation = self.create_service_documentation(deployment_results)

        # List all services
        all_services = self.list_deployed_services()

        return {
            "deployment_results": deployment_results,
            "testing_results": testing_results,
            "documentation": documentation,
            "all_deployed_services": all_services,
            "summary": {
                "total_services": len(services_to_deploy),
                "successfully_deployed": len(
                    [r for r in deployment_results if r["status"] == "deployed"]
                ),
                "working_services": len(
                    [t for t in testing_results if t["working_endpoints"] > 0]
                ),
                "total_endpoints": sum(t["total_endpoints"] for t in testing_results),
                "working_endpoints": sum(
                    t["working_endpoints"] for t in testing_results
                ),
            },
        }


def main():
    """Execute Foxx service deployment"""
    try:
        # Initialize deployer
        deployer = FoxxServiceDeployer()

        # Deploy all services
        results = deployer.deploy_all_services()

        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"/home/opsvi/asea/foxx_deployment_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("Foxx Services Deployment Complete!")
        print(f"Results saved to: {filename}")

        # Print summary
        summary = results.get("summary", {})
        print(f"\nDeployment Summary:")
        print(
            f"- Services deployed: {summary.get('successfully_deployed', 0)}/{summary.get('total_services', 0)}"
        )
        print(f"- Working services: {summary.get('working_services', 0)}")
        print(
            f"- Working endpoints: {summary.get('working_endpoints', 0)}/{summary.get('total_endpoints', 0)}"
        )

        # Print service URLs
        documentation = results.get("documentation", {})
        if documentation.get("services"):
            print(f"\nDeployed Service URLs:")
            for service in documentation["services"]:
                print(f"- {service['name']}: {service['full_url']}")

        return results

    except Exception as e:
        logger.error(f"Foxx deployment failed: {e}")
        return None


if __name__ == "__main__":
    main()
