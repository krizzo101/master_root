#!/usr/bin/env python3
"""Test script for MCP Research Engine integration."""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# For testing without actual MCP services
import sys
sys.path.insert(0, '.')

from modules.mcp_research_engine import MCPResearchEngine


class TestMCPIntegration:
    """Test the MCP research engine integration."""
    
    def __init__(self):
        self.engine = MCPResearchEngine()
        self.results = {}
    
    async def test_version_discovery(self):
        """Test version discovery for popular packages."""
        print("\n" + "="*60)
        print("TESTING VERSION DISCOVERY")
        print("="*60)
        
        packages = ["react", "nextjs", "vite", "typescript", "python"]
        
        for package in packages:
            print(f"\nResearching {package}...")
            tech_info = await self.engine.research_technology(package)
            
            print(f"  Name: {tech_info.name}")
            print(f"  Version: {tech_info.version}")
            print(f"  Release Date: {tech_info.release_date}")
            print(f"  Documentation: {tech_info.documentation_url}")
            
            self.results[f"version_{package}"] = {
                "name": tech_info.name,
                "version": tech_info.version,
                "source": "mcp" if tech_info.version != "latest" else "fallback"
            }
    
    async def test_best_practices(self):
        """Test best practices discovery."""
        print("\n" + "="*60)
        print("TESTING BEST PRACTICES DISCOVERY")
        print("="*60)
        
        topics = ["react hooks", "nextjs app router", "python async"]
        
        for topic in topics:
            print(f"\nFinding best practices for: {topic}")
            tech_info = await self.engine.research_technology(topic.split()[0])
            
            if tech_info.best_practices:
                print("  Best Practices:")
                for i, practice in enumerate(tech_info.best_practices[:3], 1):
                    print(f"    {i}. {practice}")
            
            self.results[f"practices_{topic.replace(' ', '_')}"] = tech_info.best_practices[:3]
    
    async def test_deprecation_check(self):
        """Test deprecation checking."""
        print("\n" + "="*60)
        print("TESTING DEPRECATION CHECKING")
        print("="*60)
        
        packages = ["react", "angular"]
        
        for package in packages:
            print(f"\nChecking deprecations for {package}...")
            tech_info = await self.engine.research_technology(package)
            
            if tech_info.deprecations:
                print("  Deprecation Warnings:")
                for warning in tech_info.deprecations[:2]:
                    print(f"    - {warning[:100]}...")
            else:
                print("  No deprecations found")
            
            self.results[f"deprecations_{package}"] = len(tech_info.deprecations)
    
    async def test_parallel_execution(self):
        """Test parallel research execution."""
        print("\n" + "="*60)
        print("TESTING PARALLEL EXECUTION")
        print("="*60)
        
        packages = ["vue", "svelte", "solid", "qwik", "preact"]
        
        print(f"\nResearching {len(packages)} packages in parallel...")
        start = datetime.now()
        
        versions = await self.engine.get_current_versions(packages)
        
        elapsed = (datetime.now() - start).total_seconds()
        
        print(f"\nCompleted in {elapsed:.2f} seconds")
        print("Results:")
        for pkg, version in versions.items():
            print(f"  {pkg}: {version}")
        
        self.results["parallel_execution"] = {
            "packages": len(packages),
            "time_seconds": elapsed,
            "avg_per_package": elapsed / len(packages)
        }
    
    async def test_cache_performance(self):
        """Test cache hit performance."""
        print("\n" + "="*60)
        print("TESTING CACHE PERFORMANCE")
        print("="*60)
        
        package = "react"
        
        # First call - cache miss
        print(f"\nFirst call for {package} (cache miss)...")
        start = datetime.now()
        result1 = await self.engine.research_technology(package)
        time1 = (datetime.now() - start).total_seconds()
        print(f"  Time: {time1:.3f}s")
        print(f"  Version: {result1.version}")
        
        # Second call - cache hit
        print(f"\nSecond call for {package} (cache hit)...")
        start = datetime.now()
        result2 = await self.engine.research_technology(package)
        time2 = (datetime.now() - start).total_seconds()
        print(f"  Time: {time2:.3f}s")
        print(f"  Version: {result2.version}")
        
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"\nCache speedup: {speedup:.1f}x faster")
        
        self.results["cache_performance"] = {
            "cache_miss_time": time1,
            "cache_hit_time": time2,
            "speedup_factor": speedup
        }
    
    async def test_circuit_breaker(self):
        """Test circuit breaker behavior."""
        print("\n" + "="*60)
        print("TESTING CIRCUIT BREAKER")
        print("="*60)
        
        # Get current status
        summary = self.engine.get_research_summary()
        
        print("\nService Status:")
        print(f"  Brave Search: {summary['brave_status']}")
        print(f"  Firecrawl: {summary['firecrawl_status']}")
        print(f"  Context7: {summary['context7_status']}")
        print(f"  Cache Size: {summary['cache_size']} items")
        print(f"  Fallback Packages: {summary['fallback_packages']}")
        
        self.results["circuit_breaker"] = summary
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "#"*60)
        print("# MCP RESEARCH ENGINE INTEGRATION TESTS")
        print("#"*60)
        
        tests = [
            self.test_version_discovery(),
            self.test_best_practices(),
            self.test_deprecation_check(),
            self.test_parallel_execution(),
            self.test_cache_performance(),
            self.test_circuit_breaker()
        ]
        
        for test in tests:
            try:
                await test
            except Exception as e:
                print(f"\nTest failed: {e}")
        
        # Save results
        self.save_results()
        
        print("\n" + "#"*60)
        print("# TESTS COMPLETED")
        print("#"*60)
    
    def save_results(self):
        """Save test results to file."""
        results_file = "mcp_test_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults saved to {results_file}")


async def main():
    """Main test runner."""
    tester = TestMCPIntegration()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())