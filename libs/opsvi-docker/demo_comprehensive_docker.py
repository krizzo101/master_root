#!/usr/bin/env python3
"""
Comprehensive Docker Management Demo

Demonstrates all capabilities of the opsvi-docker library:
- Docker Provider initialization and configuration
- Container lifecycle management
- Image management and optimization
- Network and volume operations
- Docker Compose orchestration
- Registry management
- Health monitoring and security scanning
- Utility functions and best practices
"""

import os
import sys
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the library to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from opsvi_docker import (
        DockerProvider,
        DockerConfig,
        ContainerConfig,
        ImageConfig,
        NetworkConfig,
        VolumeConfig,
        ComposeConfig,
        RegistryConfig,
        DockerUtils,
        ContainerUtils,
        ImageUtils,
        NetworkUtils,
        VolumeUtils,
        HealthUtils,
        MonitoringUtils,
        SecurityUtils,
        VulnerabilityScanner,
    )
    from opsvi_docker.schemas import (
        ContainerCreateRequest,
        ImageBuildRequest,
        NetworkCreateRequest,
        VolumeCreateRequest,
        ComposeUpRequest,
    )
except ImportError as e:
    print(f"❌ Failed to import opsvi-docker components: {e}")
    print("Make sure you're running from the libs/opsvi-docker directory")
    sys.exit(1)


class DockerDemo:
    """Comprehensive Docker management demonstration."""

    def __init__(self):
        self.docker_provider = None
        self.demo_containers = []
        self.demo_images = []
        self.demo_networks = []
        self.demo_volumes = []

    async def initialize(self) -> bool:
        """Initialize Docker provider and check prerequisites."""
        print("🔄 Initializing Docker Demo...")

        try:
            # Check Docker installation
            docker_check = DockerUtils.check_docker_installation()
            if not docker_check["installed"]:
                print(f"❌ Docker not installed: {docker_check['error']}")
                return False

            print(f"✅ Docker installed: {docker_check['version']}")

            # Check Docker daemon
            daemon_health = HealthUtils.check_docker_daemon()
            if daemon_health.status != "healthy":
                print(f"❌ Docker daemon unhealthy: {daemon_health.message}")
                return False

            print("✅ Docker daemon is healthy")

            # Initialize Docker provider
            config = DockerConfig(base_url="unix://var/run/docker.sock", timeout=30)

            self.docker_provider = DockerProvider(config)
            await self.docker_provider.initialize()

            print("✅ Docker provider initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize Docker demo: {e}")
            return False

    def demo_docker_utils(self) -> None:
        """Demonstrate Docker utility functions."""
        print("\n" + "=" * 50)
        print("📋 Docker Utilities Demo")
        print("=" * 50)

        try:
            # Check installations
            docker_check = DockerUtils.check_docker_installation()
            compose_check = DockerUtils.check_docker_compose_installation()

            print(f"Docker installed: {docker_check['installed']}")
            print(f"Docker Compose installed: {compose_check['installed']}")

            # Get system info
            system_info = DockerUtils.get_docker_system_info()
            if system_info["success"]:
                print("✅ Docker system info retrieved")
            else:
                print(f"❌ Failed to get system info: {system_info.get('error')}")

            # Get environment variables
            docker_env = DockerUtils.get_docker_environment()
            print(f"Docker environment variables: {len(docker_env)} found")

            # Test image name parsing
            test_image = "registry.example.com/myorg/myapp:v1.2.3"
            parsed = DockerUtils.parse_docker_image_name(test_image)
            print(f"Parsed image '{test_image}':")
            for key, value in parsed.items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"❌ Docker utils demo failed: {e}")

    async def demo_container_management(self) -> None:
        """Demonstrate container lifecycle management."""
        print("\n" + "=" * 50)
        print("🐳 Container Management Demo")
        print("=" * 50)

        try:
            container_manager = self.docker_provider.container_manager

            # Create a test container
            print("📦 Creating test container...")

            container_config = ContainerConfig(
                image="nginx:alpine",
                name="opsvi-demo-nginx",
                ports={"80/tcp": 8080},
                environment={"NGINX_HOST": "localhost"},
                restart_policy="unless-stopped",
            )

            container_info = await container_manager.create_container(container_config)
            if container_info:
                self.demo_containers.append(container_info.id)
                print(f"✅ Container created: {container_info.id[:12]}")

                # Start container
                print("▶️  Starting container...")
                started = await container_manager.start_container(container_info.id)
                if started:
                    print("✅ Container started successfully")

                    # Wait a moment for container to be fully running
                    await asyncio.sleep(2)

                    # Get container info
                    info = await container_manager.get_container_info(container_info.id)
                    print(f"📋 Container status: {info.status}")

                    # Get container stats
                    stats = await container_manager.get_container_stats(
                        container_info.id
                    )
                    print(f"📊 Memory usage: {stats.memory_usage_mb:.1f} MB")
                    print(f"📊 CPU usage: {stats.cpu_usage_percent:.2f}%")

                    # Get logs
                    logs = await container_manager.get_container_logs(
                        container_info.id, tail=5
                    )
                    print(f"📝 Recent logs (first 200 chars): {logs[:200]}...")

                    # Execute command in container
                    result = await container_manager.execute_command(
                        container_info.id, ["nginx", "-v"]
                    )
                    if result["success"]:
                        print(f"🔧 Command result: {result['output'].strip()}")

                    # Demonstrate container utilities
                    print("\n🔍 Container Analysis...")

                    # Analyze container config
                    container_raw = container_manager._get_container(container_info.id)
                    container_config_dict = container_raw.attrs

                    analysis = ContainerUtils.analyze_container_config(
                        container_config_dict
                    )
                    print(f"Security score: {analysis['security_score']}/100")
                    if analysis["warnings"]:
                        print(f"Warnings: {len(analysis['warnings'])}")
                    if analysis["recommendations"]:
                        print(f"Recommendations: {len(analysis['recommendations'])}")

                    # Security scan
                    security_findings = SecurityUtils.scan_container_security(
                        container_config_dict
                    )
                    print(f"Security findings: {len(security_findings)}")
                    for finding in security_findings[:3]:  # Show first 3
                        print(f"  • {finding.title} ({finding.severity.value})")

                else:
                    print("❌ Failed to start container")
            else:
                print("❌ Failed to create container")

        except Exception as e:
            print(f"❌ Container management demo failed: {e}")

    async def demo_image_management(self) -> None:
        """Demonstrate image management operations."""
        print("\n" + "=" * 50)
        print("🖼️  Image Management Demo")
        print("=" * 50)

        try:
            image_manager = self.docker_provider.image_manager

            # Pull a test image
            print("⬇️  Pulling test image...")

            image_config = ImageConfig(name="hello-world", tag="latest")

            image_info = await image_manager.pull_image(image_config)
            if image_info:
                self.demo_images.append(image_info.id)
                print(f"✅ Image pulled: {image_info.id[:12]}")
                print(f"📏 Size: {ImageUtils.format_image_size(image_info.size)}")

                # Get image details
                detailed_info = await image_manager.get_image_info(image_info.id)
                print(f"📅 Created: {detailed_info.created}")

                # Analyze image
                print("\n🔍 Image Analysis...")

                # Get raw image data for analysis
                image_raw = image_manager._get_image_by_id_or_name(image_info.id)
                image_data = image_raw.attrs

                # Image metadata
                metadata = ImageUtils.get_image_metadata(image_data)
                print(f"Architecture: {metadata['architecture']}")
                print(f"OS: {metadata['os']}")
                if metadata["age_days"] is not None:
                    print(f"Age: {metadata['age_days']} days")

                # Security analysis
                security_analysis = ImageUtils.analyze_image_security(image_data)
                print(f"Base image: {security_analysis['base_image']}")
                print(f"Exposed ports: {len(security_analysis['exposed_ports'])}")
                print(f"Security issues: {len(security_analysis['security_issues'])}")

                # Size analysis
                size_info = ImageUtils.calculate_image_size(image_data)
                print(
                    f"Virtual size: {size_info['size_breakdown']['virtual_size_formatted']}"
                )

                # Search for similar images
                print("\n🔍 Searching for similar images...")
                search_results = await image_manager.search_images("hello", limit=3)
                print(f"Found {len(search_results)} similar images")
                for result in search_results[:2]:
                    print(
                        f"  • {result.get('name', 'unknown')}: {result.get('description', 'No description')[:50]}..."
                    )

            else:
                print("❌ Failed to pull image")

        except Exception as e:
            print(f"❌ Image management demo failed: {e}")

    async def demo_network_management(self) -> None:
        """Demonstrate network management operations."""
        print("\n" + "=" * 50)
        print("🌐 Network Management Demo")
        print("=" * 50)

        try:
            network_manager = self.docker_provider.network_manager

            # Create a custom network
            print("🔗 Creating custom network...")

            network_config = NetworkConfig(
                name="opsvi-demo-network",
                driver="bridge",
                options={"com.docker.network.bridge.enable_icc": "true"},
                labels={"demo": "opsvi-docker"},
            )

            network_info = await network_manager.create_network(network_config)
            if network_info:
                self.demo_networks.append(network_info.id)
                print(f"✅ Network created: {network_info.id[:12]}")
                print(f"📛 Name: {network_info.name}")
                print(f"🚗 Driver: {network_info.driver}")

                # List networks
                networks = await network_manager.list_networks()
                print(f"📋 Total networks: {len(networks)}")

                # Get network details
                details = await network_manager.inspect_network(network_info.id)
                print(f"🔍 Network details retrieved: {bool(details)}")

                # Connect container to network (if we have one)
                if self.demo_containers:
                    container_id = self.demo_containers[0]
                    print(f"🔌 Connecting container to network...")

                    connected = await network_manager.connect_container(
                        network_info.id, container_id
                    )
                    if connected:
                        print("✅ Container connected to network")

                        # Get network containers
                        containers = await network_manager.get_network_containers(
                            network_info.id
                        )
                        print(f"📦 Containers in network: {len(containers)}")

                    else:
                        print("❌ Failed to connect container to network")

            else:
                print("❌ Failed to create network")

        except Exception as e:
            print(f"❌ Network management demo failed: {e}")

    async def demo_volume_management(self) -> None:
        """Demonstrate volume management operations."""
        print("\n" + "=" * 50)
        print("💾 Volume Management Demo")
        print("=" * 50)

        try:
            volume_manager = self.docker_provider.volume_manager

            # Create a volume
            print("📁 Creating volume...")

            volume_config = VolumeConfig(
                name="opsvi-demo-volume",
                driver="local",
                labels={"demo": "opsvi-docker", "purpose": "testing"},
            )

            volume_info = await volume_manager.create_volume(volume_config)
            if volume_info:
                self.demo_volumes.append(volume_info.name)
                print(f"✅ Volume created: {volume_info.name}")
                print(f"🚗 Driver: {volume_info.driver}")
                print(f"📍 Mount point: {volume_info.mount_point}")

                # List volumes
                volumes = await volume_manager.list_volumes()
                print(f"📋 Total volumes: {len(volumes)}")

                # Get volume details
                details = await volume_manager.inspect_volume(volume_info.name)
                print(f"🔍 Volume details retrieved: {bool(details)}")

                # Get volume usage (simulated)
                usage = await volume_manager.get_volume_usage(volume_info.name)
                print(f"📊 Volume usage info: {bool(usage)}")

            else:
                print("❌ Failed to create volume")

        except Exception as e:
            print(f"❌ Volume management demo failed: {e}")

    async def demo_monitoring_and_health(self) -> None:
        """Demonstrate monitoring and health checking."""
        print("\n" + "=" * 50)
        print("📊 Monitoring & Health Demo")
        print("=" * 50)

        try:
            # Check Docker daemon health
            daemon_health = HealthUtils.check_docker_daemon()
            print(f"🏥 Docker daemon: {daemon_health.status}")
            print(f"   Message: {daemon_health.message}")
            print(f"   Duration: {daemon_health.duration_ms:.1f}ms")

            # Collect system metrics
            print("\n📈 Collecting system metrics...")
            system_metrics = MonitoringUtils.collect_system_metrics()
            print(f"Collected {len(system_metrics)} system metrics")

            for metric in system_metrics[:3]:  # Show first 3
                print(f"  • {metric.name}: {metric.value} {metric.unit}")

            # Health checks for running containers
            if self.demo_containers:
                print("\n🔍 Checking container health...")
                container_manager = self.docker_provider.container_manager

                for container_id in self.demo_containers[:2]:  # Check first 2
                    try:
                        container_raw = container_manager._get_container(container_id)
                        container_info = container_raw.attrs

                        health_result = HealthUtils.check_container_health(
                            container_info
                        )
                        print(
                            f"🐳 Container {container_id[:12]}: {health_result.status}"
                        )
                        print(f"   {health_result.message}")

                        # Get container stats for monitoring
                        stats_data = container_raw.stats(stream=False)
                        metrics = MonitoringUtils.collect_container_metrics(stats_data)
                        print(f"   Collected {len(metrics)} container metrics")

                    except Exception as e:
                        print(
                            f"   ❌ Failed to check container {container_id[:12]}: {e}"
                        )

            # Aggregate health results
            all_health_results = [daemon_health]

            if self.demo_containers:
                container_manager = self.docker_provider.container_manager
                for container_id in self.demo_containers:
                    try:
                        container_raw = container_manager._get_container(container_id)
                        container_info = container_raw.attrs
                        health_result = HealthUtils.check_container_health(
                            container_info
                        )
                        all_health_results.append(health_result)
                    except:
                        pass

            # Generate health report
            print("\n📋 Health Report:")
            health_report = HealthUtils.create_health_report(all_health_results)
            print(health_report)

        except Exception as e:
            print(f"❌ Monitoring demo failed: {e}")

    async def demo_security_scanning(self) -> None:
        """Demonstrate security scanning capabilities."""
        print("\n" + "=" * 50)
        print("🔒 Security Scanning Demo")
        print("=" * 50)

        try:
            # Check if vulnerability scanner is available
            scanner = VulnerabilityScanner("trivy")
            if scanner.is_available():
                print("✅ Trivy vulnerability scanner available")

                # Scan an image for vulnerabilities
                if self.demo_images:
                    print(f"\n🔍 Scanning image for vulnerabilities...")
                    image_id = self.demo_images[0]

                    # Get image name for scanning
                    image_manager = self.docker_provider.image_manager
                    image_raw = image_manager._get_image_by_id_or_name(image_id)
                    image_tags = image_raw.tags

                    if image_tags:
                        image_name = image_tags[0]
                        print(f"   Scanning: {image_name}")

                        vuln_report = scanner.scan_image(image_name)
                        if vuln_report:
                            print(
                                f"   ✅ Scan completed in {vuln_report.scan_duration_ms:.0f}ms"
                            )
                            print(
                                f"   📊 Total vulnerabilities: {vuln_report.total_findings}"
                            )

                            for (
                                severity,
                                count,
                            ) in vuln_report.findings_by_severity.items():
                                if count > 0:
                                    print(f"   {severity.capitalize()}: {count}")
                        else:
                            print("   ❌ Vulnerability scan failed")
                    else:
                        print("   ⚠️  No image tags found for scanning")
                else:
                    print("⚠️  No images available for vulnerability scanning")
            else:
                print("⚠️  Trivy vulnerability scanner not available")
                print(
                    "   Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
                )

            # Security scan of containers
            if self.demo_containers:
                print(f"\n🔍 Security scanning containers...")
                container_manager = self.docker_provider.container_manager

                for container_id in self.demo_containers[:1]:  # Scan first container
                    try:
                        container_raw = container_manager._get_container(container_id)
                        container_info = container_raw.attrs

                        findings = scanner.scan_container(container_info)
                        print(
                            f"   🐳 Container {container_id[:12]}: {len(findings)} security findings"
                        )

                        # Show findings by severity
                        by_severity = {}
                        for finding in findings:
                            severity = finding.severity.value
                            by_severity[severity] = by_severity.get(severity, 0) + 1

                        for severity in ["critical", "high", "medium", "low"]:
                            count = by_severity.get(severity, 0)
                            if count > 0:
                                print(f"     {severity.capitalize()}: {count}")

                        # Show top findings
                        critical_findings = [
                            f for f in findings if f.severity.value == "critical"
                        ]
                        high_findings = [
                            f for f in findings if f.severity.value == "high"
                        ]

                        for finding in (critical_findings + high_findings)[:2]:
                            print(f"     • {finding.title}")

                    except Exception as e:
                        print(f"   ❌ Failed to scan container {container_id[:12]}: {e}")

        except Exception as e:
            print(f"❌ Security scanning demo failed: {e}")

    async def cleanup_demo_resources(self) -> None:
        """Clean up all demo resources."""
        print("\n" + "=" * 50)
        print("🧹 Cleaning Up Demo Resources")
        print("=" * 50)

        try:
            # Stop and remove containers
            if self.demo_containers:
                container_manager = self.docker_provider.container_manager

                for container_id in self.demo_containers:
                    try:
                        print(f"🛑 Stopping container {container_id[:12]}...")
                        await container_manager.stop_container(container_id)

                        print(f"🗑️  Removing container {container_id[:12]}...")
                        await container_manager.remove_container(
                            container_id, force=True
                        )

                    except Exception as e:
                        print(
                            f"   ⚠️  Failed to cleanup container {container_id[:12]}: {e}"
                        )

            # Remove networks
            if self.demo_networks:
                network_manager = self.docker_provider.network_manager

                for network_id in self.demo_networks:
                    try:
                        print(f"🗑️  Removing network {network_id[:12]}...")
                        await network_manager.remove_network(network_id)

                    except Exception as e:
                        print(
                            f"   ⚠️  Failed to cleanup network {network_id[:12]}: {e}"
                        )

            # Remove volumes
            if self.demo_volumes:
                volume_manager = self.docker_provider.volume_manager

                for volume_name in self.demo_volumes:
                    try:
                        print(f"🗑️  Removing volume {volume_name}...")
                        await volume_manager.remove_volume(volume_name)

                    except Exception as e:
                        print(f"   ⚠️  Failed to cleanup volume {volume_name}: {e}")

            # Clean up provider
            if self.docker_provider:
                await self.docker_provider.cleanup()

            print("✅ Cleanup completed")

        except Exception as e:
            print(f"❌ Cleanup failed: {e}")


async def main():
    """Run the comprehensive Docker demo."""
    print("🐳 OPSVI Docker Management - Comprehensive Demo")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    demo = DockerDemo()

    try:
        # Initialize
        if not await demo.initialize():
            return False

        # Run all demonstrations
        demo.demo_docker_utils()
        await demo.demo_container_management()
        await demo.demo_image_management()
        await demo.demo_network_management()
        await demo.demo_volume_management()
        await demo.demo_monitoring_and_health()
        await demo.demo_security_scanning()

        print("\n" + "=" * 60)
        print("🎉 All demonstrations completed successfully!")

        return True

    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
        return False

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        return False

    finally:
        # Always cleanup
        await demo.cleanup_demo_resources()
        print(f"\n📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
