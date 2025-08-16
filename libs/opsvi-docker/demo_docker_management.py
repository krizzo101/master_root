#!/usr/bin/env python3
"""
Docker Management Demo

Comprehensive demonstration of OPSVI Docker management capabilities.
Showcases containers, images, networks, volumes, compose, registry, and monitoring.
"""

import asyncio
import logging
import os
import sys

# Add the library to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opsvi_docker import (
    ComposeConfig,
    DockerConfig,
    DockerProvider,
)
from opsvi_docker.utils import (
    ContainerUtils,
    DockerUtils,
    HealthUtils,
    ImageUtils,
    MonitoringUtils,
    NetworkUtils,
    VolumeUtils,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DockerManagementDemo:
    """Comprehensive Docker management demonstration."""

    def __init__(self):
        self.provider = None
        self.demo_results = {}

    async def setup(self):
        """Set up the Docker provider for demos."""
        print("🔧 Setting up Docker provider...")

        config = DockerConfig(
            base_url="unix://var/run/docker.sock", timeout=30, max_pool_size=10
        )

        self.provider = DockerProvider(config)
        await self.provider.initialize()

        print("✅ Docker provider initialized successfully")

    async def demo_container_management(self):
        """Demonstrate container management capabilities."""
        print("\n🐳 Container Management Demo")
        print("=" * 50)

        try:
            # List containers
            containers = await self.provider.container_manager.list_containers()
            print(f"📋 Found {len(containers)} containers")

            # Get container info for first container (if any)
            if containers:
                container_info = (
                    await self.provider.container_manager.get_container_info(
                        containers[0].id
                    )
                )
                print(
                    f"📊 Container info: {container_info.name} ({container_info.status})"
                )

                # Get container stats
                stats = await self.provider.container_manager.get_container_stats(
                    containers[0].id
                )
                print(
                    f"📈 Container stats: CPU {stats.cpu_percent:.1f}%, Memory {stats.memory_usage_mb:.1f}MB"
                )

                # Analyze container config
                config_analysis = ContainerUtils.analyze_container_config(
                    container_info.config
                )
                print(
                    f"🔍 Security score: {config_analysis.get('security_score', 0)}/100"
                )

            # Demo container utilities
            print("\n🔧 Container Utilities Demo:")

            # Format container logs (mock)
            mock_logs = "2024-01-01T10:00:00Z Container started\n2024-01-01T10:01:00Z Application ready"
            formatted_logs = ContainerUtils.format_container_logs(mock_logs)
            print(f"📝 Formatted logs:\n{formatted_logs}")

            self.demo_results["container_management"] = "✅ Success"

        except Exception as e:
            print(f"❌ Container management demo failed: {e}")
            self.demo_results["container_management"] = f"❌ Failed: {e}"

    async def demo_image_management(self):
        """Demonstrate image management capabilities."""
        print("\n🖼️  Image Management Demo")
        print("=" * 50)

        try:
            # List images
            images = await self.provider.image_manager.list_images()
            print(f"📋 Found {len(images)} images")

            # Get image info for first image (if any)
            if images:
                image_info = await self.provider.image_manager.get_image_info(
                    images[0].id
                )
                print(f"📊 Image info: {image_info.name} ({image_info.tag})")
                print(f"💾 Size: {ImageUtils.format_image_size(image_info.size)}")

                # Analyze image layers
                layer_analysis = ImageUtils.analyze_image_layers(image_info.config)
                print(f"🔍 Layer analysis: {layer_analysis['total_layers']} layers")

                # Calculate image size
                size_info = ImageUtils.calculate_image_size(image_info.config)
                print(
                    f"📏 Virtual size: {size_info['size_breakdown']['virtual_size_formatted']}"
                )

            # Demo image utilities
            print("\n🔧 Image Utilities Demo:")

            # Parse image name
            parsed = ImageUtils.parse_docker_image_name(
                "docker.io/library/nginx:latest"
            )
            print(f"🔍 Parsed image: {parsed}")

            # Build image name
            built_name = ImageUtils.build_docker_image_name(
                "myapp", "v1.0", "myregistry.com"
            )
            print(f"🔨 Built image name: {built_name}")

            self.demo_results["image_management"] = "✅ Success"

        except Exception as e:
            print(f"❌ Image management demo failed: {e}")
            self.demo_results["image_management"] = f"❌ Failed: {e}"

    async def demo_network_management(self):
        """Demonstrate network management capabilities."""
        print("\n🌐 Network Management Demo")
        print("=" * 50)

        try:
            # List networks
            networks = await self.provider.network_manager.list_networks()
            print(f"📋 Found {len(networks)} networks")

            # Get network info for first network (if any)
            if networks:
                network_info = await self.provider.network_manager.get_network_info(
                    networks[0].id
                )
                print(f"📊 Network info: {network_info.name} ({network_info.driver})")

                # Analyze network config
                config_analysis = NetworkUtils.analyze_network_config(
                    network_info.config
                )
                print(f"🔍 Network type: {config_analysis['network_type']}")

                # Get network statistics
                stats = NetworkUtils.get_network_statistics(network_info.config)
                print(f"📈 Connected containers: {stats['total_containers']}")

            # Demo network utilities
            print("\n🔧 Network Utilities Demo:")

            # Validate network config
            mock_config = {
                "Driver": "bridge",
                "IPAM": {
                    "Config": [{"Subnet": "172.17.0.0/16", "Gateway": "172.17.0.1"}]
                },
            }
            validation = NetworkUtils.validate_network_config(mock_config)
            print(f"✅ Network config valid: {validation['valid']}")

            # Format network info
            formatted = NetworkUtils.format_network_info(mock_config)
            print(f"📝 Formatted info:\n{formatted}")

            self.demo_results["network_management"] = "✅ Success"

        except Exception as e:
            print(f"❌ Network management demo failed: {e}")
            self.demo_results["network_management"] = f"❌ Failed: {e}"

    async def demo_volume_management(self):
        """Demonstrate volume management capabilities."""
        print("\n💾 Volume Management Demo")
        print("=" * 50)

        try:
            # List volumes
            volumes = await self.provider.volume_manager.list_volumes()
            print(f"📋 Found {len(volumes)} volumes")

            # Get volume info for first volume (if any)
            if volumes:
                volume_info = await self.provider.volume_manager.get_volume_info(
                    volumes[0].name
                )
                print(f"📊 Volume info: {volume_info.name} ({volume_info.driver})")

                # Analyze volume config
                config_analysis = VolumeUtils.analyze_volume_config(volume_info.config)
                print(f"🔍 Volume type: {config_analysis['volume_type']}")

                # Get volume usage stats
                usage_stats = VolumeUtils.get_volume_usage_stats(volume_info.config)
                print(f"📈 Usage: {usage_stats['size_formatted']}")

            # Demo volume utilities
            print("\n🔧 Volume Utilities Demo:")

            # Validate volume config
            mock_config = {"Driver": "local", "Name": "test-volume"}
            validation = VolumeUtils.validate_volume_config(mock_config)
            print(f"✅ Volume config valid: {validation['valid']}")

            # Format volume size
            formatted_size = VolumeUtils.format_volume_size(1024 * 1024 * 100)  # 100MB
            print(f"📏 Formatted size: {formatted_size}")

            self.demo_results["volume_management"] = "✅ Success"

        except Exception as e:
            print(f"❌ Volume management demo failed: {e}")
            self.demo_results["volume_management"] = f"❌ Failed: {e}"

    async def demo_compose_management(self):
        """Demonstrate Docker Compose management capabilities."""
        print("\n🎼 Compose Management Demo")
        print("=" * 50)

        try:
            # Demo compose utilities
            print("🔧 Compose Utilities Demo:")

            # Create a mock compose config
            compose_config = ComposeConfig(
                project_name="demo-project",
                compose_file="docker-compose.yml",
                environment="development",
            )

            print(f"📋 Project: {compose_config.project_name}")
            print(f"📄 Compose file: {compose_config.compose_file}")
            print(f"🌍 Environment: {compose_config.environment}")

            # Note: Actual compose operations would require a docker-compose.yml file
            print("ℹ️  Compose operations require docker-compose.yml files")

            self.demo_results["compose_management"] = "✅ Success"

        except Exception as e:
            print(f"❌ Compose management demo failed: {e}")
            self.demo_results["compose_management"] = f"❌ Failed: {e}"

    async def demo_registry_management(self):
        """Demonstrate registry management capabilities."""
        print("\n🏪 Registry Management Demo")
        print("=" * 50)

        try:
            # Demo registry utilities
            print("🔧 Registry Utilities Demo:")

            # List registries
            registries = await self.provider.registry_manager.list_registries()
            print(f"📋 Available registries: {registries}")

            # Note: Registry operations require authentication
            print("ℹ️  Registry operations require authentication")

            self.demo_results["registry_management"] = "✅ Success"

        except Exception as e:
            print(f"❌ Registry management demo failed: {e}")
            self.demo_results["registry_management"] = f"❌ Failed: {e}"

    async def demo_monitoring(self):
        """Demonstrate monitoring capabilities."""
        print("\n📊 Monitoring Demo")
        print("=" * 50)

        try:
            # Demo monitoring utilities
            print("🔧 Monitoring Utilities Demo:")

            # Format bytes
            formatted_bytes = MonitoringUtils.format_bytes(1024 * 1024 * 500)  # 500MB
            print(f"📏 Formatted bytes: {formatted_bytes}")

            # Format percentage
            formatted_percent = MonitoringUtils.format_percentage(85.5)
            print(f"📊 Formatted percentage: {formatted_percent}")

            # Calculate average
            values = [10, 20, 30, 40, 50]
            average = MonitoringUtils.calculate_average(values)
            print(f"📈 Average of {values}: {average}")

            # Calculate percentile
            p95 = MonitoringUtils.calculate_percentile(values, 95)
            print(f"📊 95th percentile: {p95}")

            # Generate alerts
            mock_stats = {
                "cpu_usage_percent": 85,
                "memory_usage_percent": 75,
                "network_rx_bytes": 1024 * 1024 * 50,  # 50MB
            }
            thresholds = {"cpu_percent": 80, "memory_percent": 80, "network_mbps": 100}
            alerts = MonitoringUtils.generate_alerts(mock_stats, thresholds)
            print(f"🚨 Generated {len(alerts)} alerts")

            self.demo_results["monitoring"] = "✅ Success"

        except Exception as e:
            print(f"❌ Monitoring demo failed: {e}")
            self.demo_results["monitoring"] = f"❌ Failed: {e}"

    async def demo_health_checks(self):
        """Demonstrate health checking capabilities."""
        print("\n🏥 Health Checks Demo")
        print("=" * 50)

        try:
            # Demo health utilities
            print("🔧 Health Utilities Demo:")

            # Validate health check config
            health_check = {
                "Test": ["CMD", "curl", "-f", "http://localhost/health"],
                "Interval": 30,
                "Timeout": 10,
                "Retries": 3,
                "StartPeriod": 40,
            }
            validation = HealthUtils.validate_health_check_config(health_check)
            print(f"✅ Health check valid: {validation['valid']}")

            # Create health check for different service types
            web_health = HealthUtils.create_health_check_command("web", 8080)
            print(f"🌐 Web health check: {web_health['test']}")

            db_health = HealthUtils.create_health_check_command("database")
            print(f"🗄️  Database health check: {db_health['test']}")

            # Format health status (mock)
            mock_status = {
                "Status": "healthy",
                "FailingStreak": 0,
                "Log": [
                    {
                        "ExitCode": 0,
                        "Output": "OK",
                        "Start": "2024-01-01T10:00:00Z",
                        "End": "2024-01-01T10:00:01Z",
                    }
                ],
            }
            formatted_status = HealthUtils.format_health_status(mock_status)
            print(f"📝 Health status:\n{formatted_status}")

            self.demo_results["health_checks"] = "✅ Success"

        except Exception as e:
            print(f"❌ Health checks demo failed: {e}")
            self.demo_results["health_checks"] = f"❌ Failed: {e}"

    async def demo_utilities(self):
        """Demonstrate general Docker utilities."""
        print("\n🔧 General Utilities Demo")
        print("=" * 50)

        try:
            # Demo Docker utilities
            print("🔧 Docker Utilities Demo:")

            # Check Docker installation
            docker_check = DockerUtils.check_docker_installation()
            print(f"🐳 Docker installed: {docker_check['installed']}")

            # Check Docker Compose installation
            compose_check = DockerUtils.check_docker_compose_installation()
            print(f"🎼 Docker Compose installed: {compose_check['installed']}")

            # Get Docker environment
            env_vars = DockerUtils.get_docker_environment()
            print(f"🌍 Docker environment variables: {len(env_vars)} found")

            # Format bytes and duration
            formatted_bytes = DockerUtils.format_bytes(1024 * 1024 * 1024)  # 1GB
            formatted_duration = DockerUtils.format_duration(3661)  # 1h 1m 1s
            print(f"📏 1GB = {formatted_bytes}")
            print(f"⏱️  3661s = {formatted_duration}")

            # Parse and build image names
            parsed = DockerUtils.parse_docker_image_name(
                "docker.io/library/nginx:latest"
            )
            built = DockerUtils.build_docker_image_name(
                "myapp", "v1.0", "myregistry.com"
            )
            print(f"🔍 Parsed: {parsed}")
            print(f"🔨 Built: {built}")

            self.demo_results["utilities"] = "✅ Success"

        except Exception as e:
            print(f"❌ Utilities demo failed: {e}")
            self.demo_results["utilities"] = f"❌ Failed: {e}"

    async def demo_system_info(self):
        """Demonstrate system information capabilities."""
        print("\n💻 System Information Demo")
        print("=" * 50)

        try:
            # Get Docker system info
            system_info = DockerUtils.get_docker_system_info()
            print(f"📊 System info available: {system_info['success']}")

            # Get comprehensive status from provider
            status = self.provider.get_comprehensive_status()
            print(f"📈 Provider status: {status['status']}")

            # Get Docker info
            docker_info = self.provider.get_docker_info()
            print(f"🐳 Docker info available: {bool(docker_info)}")

            # List available managers
            managers = self.provider.list_managers()
            print(f"🔧 Available managers: {managers}")

            self.demo_results["system_info"] = "✅ Success"

        except Exception as e:
            print(f"❌ System info demo failed: {e}")
            self.demo_results["system_info"] = f"❌ Failed: {e}"

    async def run_all_demos(self):
        """Run all demonstration modules."""
        print("🚀 Starting OPSVI Docker Management Demo")
        print("=" * 60)

        await self.setup()

        # Run all demos
        demos = [
            self.demo_container_management,
            self.demo_image_management,
            self.demo_network_management,
            self.demo_volume_management,
            self.demo_compose_management,
            self.demo_registry_management,
            self.demo_monitoring,
            self.demo_health_checks,
            self.demo_utilities,
            self.demo_system_info,
        ]

        for demo in demos:
            try:
                await demo()
            except Exception as e:
                print(f"❌ Demo failed: {e}")

        self.print_results_summary()
        await self.cleanup()

    def print_results_summary(self):
        """Print a summary of all demo results."""
        print("\n" + "=" * 60)
        print("📊 DEMO RESULTS SUMMARY")
        print("=" * 60)

        total_demos = len(self.demo_results)
        successful_demos = sum(
            1 for result in self.demo_results.values() if result.startswith("✅")
        )

        print(f"Total demos: {total_demos}")
        print(f"Successful: {successful_demos}")
        print(f"Failed: {total_demos - successful_demos}")
        print(f"Success rate: {(successful_demos/total_demos)*100:.1f}%")

        print("\nDetailed Results:")
        for demo_name, result in self.demo_results.items():
            status_icon = "✅" if result.startswith("✅") else "❌"
            print(f"  {status_icon} {demo_name}: {result}")

        print("\n🎉 Demo completed!")

    async def cleanup(self):
        """Clean up resources."""
        if self.provider:
            await self.provider.cleanup()
            print("🧹 Cleanup completed")


async def main():
    """Main demo function."""
    demo = DockerManagementDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        sys.exit(1)
