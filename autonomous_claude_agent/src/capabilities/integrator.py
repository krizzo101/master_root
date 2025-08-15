"""
Capability Integrator - Dynamically integrates new capabilities into the system
"""

import asyncio
import importlib
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import tempfile
import shutil

from src.capabilities.discovery import Capability
from src.capabilities.registry import CapabilityRegistry, CapabilityCategory
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IntegrationMethod(Enum):
    """Methods for integrating capabilities"""
    PYTHON_IMPORT = "python_import"
    PIP_INSTALL = "pip_install"
    NPM_INSTALL = "npm_install"
    SYSTEM_PACKAGE = "system_package"
    DOCKER_CONTAINER = "docker_container"
    API_ENDPOINT = "api_endpoint"
    MCP_SERVER = "mcp_server"
    CUSTOM_SCRIPT = "custom_script"


class IntegrationStatus(Enum):
    """Status of integration attempt"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    ROLLBACK = "rollback"


class CapabilityIntegrator:
    """Integrates new capabilities dynamically into the system"""
    
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.integration_history: List[Dict[str, Any]] = []
        self.rollback_stack: List[Dict[str, Any]] = []
        self.integration_cache = Path.home() / '.autonomous_claude' / 'integrations'
        self.integration_cache.mkdir(parents=True, exist_ok=True)
        self._integration_handlers: Dict[IntegrationMethod, Callable] = {
            IntegrationMethod.PYTHON_IMPORT: self._integrate_python_module,
            IntegrationMethod.PIP_INSTALL: self._integrate_pip_package,
            IntegrationMethod.NPM_INSTALL: self._integrate_npm_package,
            IntegrationMethod.SYSTEM_PACKAGE: self._integrate_system_package,
            IntegrationMethod.DOCKER_CONTAINER: self._integrate_docker_container,
            IntegrationMethod.API_ENDPOINT: self._integrate_api_endpoint,
            IntegrationMethod.MCP_SERVER: self._integrate_mcp_server,
            IntegrationMethod.CUSTOM_SCRIPT: self._integrate_custom_script
        }
        self._lock = asyncio.Lock()
    
    async def integrate_capability(self, capability: Capability, 
                                  method: Optional[IntegrationMethod] = None,
                                  force: bool = False) -> IntegrationStatus:
        """Integrate a new capability into the system"""
        
        async with self._lock:
            logger.info(f"Starting integration of capability: {capability.name}")
            
            # Check if already integrated
            if not force and self.registry.get_capability(capability.name):
                if self.registry.get_capability(capability.name).available:
                    logger.info(f"Capability {capability.name} already integrated")
                    return IntegrationStatus.SUCCESS
            
            # Determine integration method if not specified
            if method is None:
                method = self._determine_integration_method(capability)
                if method is None:
                    logger.error(f"Could not determine integration method for {capability.name}")
                    return IntegrationStatus.FAILED
            
            # Create rollback point
            rollback_point = self._create_rollback_point(capability, method)
            self.rollback_stack.append(rollback_point)
            
            # Execute integration
            try:
                handler = self._integration_handlers.get(method)
                if not handler:
                    logger.error(f"No handler for integration method: {method}")
                    return IntegrationStatus.FAILED
                
                success = await handler(capability)
                
                if success:
                    # Register the capability
                    capability.available = True
                    await self.registry.register(capability)
                    
                    # Record integration
                    self._record_integration(capability, method, IntegrationStatus.SUCCESS)
                    
                    # Test the integration
                    if await self._test_integration(capability):
                        logger.info(f"Successfully integrated capability: {capability.name}")
                        return IntegrationStatus.SUCCESS
                    else:
                        logger.warning(f"Integration test failed for {capability.name}")
                        return IntegrationStatus.PARTIAL
                else:
                    self._record_integration(capability, method, IntegrationStatus.FAILED)
                    await self._rollback_integration(rollback_point)
                    return IntegrationStatus.FAILED
                    
            except Exception as e:
                logger.error(f"Integration failed for {capability.name}: {e}")
                self._record_integration(capability, method, IntegrationStatus.FAILED, str(e))
                await self._rollback_integration(rollback_point)
                return IntegrationStatus.FAILED
    
    def _determine_integration_method(self, capability: Capability) -> Optional[IntegrationMethod]:
        """Determine the best integration method for a capability"""
        
        # Check capability type
        if capability.type == "python_module":
            # Check if it's already installed
            try:
                importlib.import_module(capability.name.replace('python_', ''))
                return IntegrationMethod.PYTHON_IMPORT
            except ImportError:
                return IntegrationMethod.PIP_INSTALL
        
        elif capability.type == "mcp_tool":
            return IntegrationMethod.MCP_SERVER
        
        elif capability.type == "cli_tool":
            return IntegrationMethod.SYSTEM_PACKAGE
        
        elif capability.type == "api":
            return IntegrationMethod.API_ENDPOINT
        
        elif capability.type == "docker":
            return IntegrationMethod.DOCKER_CONTAINER
        
        # Check requirements for hints
        if capability.requirements:
            for req in capability.requirements:
                if "pip install" in req:
                    return IntegrationMethod.PIP_INSTALL
                elif "npm install" in req:
                    return IntegrationMethod.NPM_INSTALL
                elif "apt install" in req or "brew install" in req:
                    return IntegrationMethod.SYSTEM_PACKAGE
                elif "docker" in req:
                    return IntegrationMethod.DOCKER_CONTAINER
        
        return None
    
    async def _integrate_python_module(self, capability: Capability) -> bool:
        """Integrate a Python module"""
        
        module_name = capability.name.replace('python_', '')
        
        try:
            # Try to import directly
            module = importlib.import_module(module_name)
            
            # Store module reference
            capability.metadata['module'] = module
            capability.metadata['functions'] = [
                name for name in dir(module) 
                if not name.startswith('_') and callable(getattr(module, name))
            ][:50]  # Limit to 50 functions
            
            logger.info(f"Successfully imported Python module: {module_name}")
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            
            # Try to install via pip
            if await self._integrate_pip_package(capability):
                # Try import again
                try:
                    module = importlib.import_module(module_name)
                    capability.metadata['module'] = module
                    return True
                except ImportError:
                    pass
            
            return False
    
    async def _integrate_pip_package(self, capability: Capability) -> bool:
        """Install a package via pip"""
        
        package_name = capability.name.replace('python_', '').replace('pip_', '')
        
        try:
            # Check if already installed
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Package {package_name} already installed")
                return True
            
            # Install the package
            logger.info(f"Installing package via pip: {package_name}")
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed package: {package_name}")
                
                # Update capability metadata
                capability.metadata['install_output'] = result.stdout
                capability.metadata['install_method'] = 'pip'
                
                return True
            else:
                logger.error(f"Failed to install package {package_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Installation timeout for package: {package_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to install package {package_name}: {e}")
            return False
    
    async def _integrate_npm_package(self, capability: Capability) -> bool:
        """Install a package via npm"""
        
        package_name = capability.name.replace('npm_', '')
        
        try:
            # Check if npm is available
            npm_check = subprocess.run(['which', 'npm'], capture_output=True)
            if npm_check.returncode != 0:
                logger.error("npm is not available")
                return False
            
            # Install globally
            result = subprocess.run(
                ['npm', 'install', '-g', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed npm package: {package_name}")
                capability.metadata['install_method'] = 'npm'
                return True
            else:
                logger.error(f"Failed to install npm package {package_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to install npm package {package_name}: {e}")
            return False
    
    async def _integrate_system_package(self, capability: Capability) -> bool:
        """Install a system package"""
        
        package_name = capability.name.replace('sys_', '').replace('cli_', '')
        
        try:
            # Detect package manager
            if os.path.exists('/usr/bin/apt'):
                # Debian/Ubuntu
                cmd = ['sudo', 'apt', 'install', '-y', package_name]
            elif os.path.exists('/usr/bin/yum'):
                # RedHat/CentOS
                cmd = ['sudo', 'yum', 'install', '-y', package_name]
            elif os.path.exists('/usr/local/bin/brew'):
                # macOS
                cmd = ['brew', 'install', package_name]
            else:
                logger.error("No supported package manager found")
                return False
            
            # Note: In production, this would need proper sudo handling
            logger.warning(f"System package installation would require: {' '.join(cmd)}")
            
            # For safety, we don't actually run system commands
            # In a real implementation, this would need careful security consideration
            return False
            
        except Exception as e:
            logger.error(f"Failed to install system package {package_name}: {e}")
            return False
    
    async def _integrate_docker_container(self, capability: Capability) -> bool:
        """Set up a Docker container for the capability"""
        
        container_name = capability.name.replace('docker_', '')
        
        try:
            # Check if Docker is available
            docker_check = subprocess.run(['which', 'docker'], capture_output=True)
            if docker_check.returncode != 0:
                logger.error("Docker is not available")
                return False
            
            # Pull the image if specified
            if 'image' in capability.metadata:
                image = capability.metadata['image']
                logger.info(f"Pulling Docker image: {image}")
                
                result = subprocess.run(
                    ['docker', 'pull', image],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    capability.metadata['docker_image'] = image
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to set up Docker container {container_name}: {e}")
            return False
    
    async def _integrate_api_endpoint(self, capability: Capability) -> bool:
        """Configure an API endpoint capability"""
        
        try:
            # Store API configuration
            api_config = {
                'endpoint': capability.metadata.get('endpoint'),
                'auth_type': capability.metadata.get('auth_type', 'none'),
                'headers': capability.metadata.get('headers', {}),
                'timeout': capability.metadata.get('timeout', 30)
            }
            
            # Test the endpoint if possible
            if api_config['endpoint']:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(
                            api_config['endpoint'],
                            headers=api_config['headers'],
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status < 500:
                                capability.metadata['api_config'] = api_config
                                capability.metadata['api_tested'] = True
                                return True
                    except:
                        # Endpoint might require specific parameters
                        capability.metadata['api_config'] = api_config
                        capability.metadata['api_tested'] = False
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to configure API endpoint: {e}")
            return False
    
    async def _integrate_mcp_server(self, capability: Capability) -> bool:
        """Configure an MCP server capability"""
        
        try:
            server_name = capability.name.replace('mcp_', '')
            
            # Check MCP configuration
            mcp_config_path = Path.home() / '.mcp' / 'mcp.json'
            
            if mcp_config_path.exists():
                with open(mcp_config_path) as f:
                    mcp_config = json.load(f)
                
                if server_name in mcp_config.get('servers', {}):
                    capability.metadata['mcp_configured'] = True
                    capability.metadata['server_config'] = mcp_config['servers'][server_name]
                    return True
            
            # MCP server would need to be configured
            logger.warning(f"MCP server {server_name} needs configuration")
            return False
            
        except Exception as e:
            logger.error(f"Failed to configure MCP server: {e}")
            return False
    
    async def _integrate_custom_script(self, capability: Capability) -> bool:
        """Run a custom integration script"""
        
        try:
            if 'script' not in capability.metadata:
                logger.error("No integration script provided")
                return False
            
            script = capability.metadata['script']
            
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            try:
                # Execute the script
                result = subprocess.run(
                    ['bash', script_path],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    capability.metadata['script_output'] = result.stdout
                    return True
                else:
                    logger.error(f"Integration script failed: {result.stderr}")
                    return False
                    
            finally:
                # Clean up
                os.unlink(script_path)
                
        except Exception as e:
            logger.error(f"Failed to run integration script: {e}")
            return False
    
    async def _test_integration(self, capability: Capability) -> bool:
        """Test if an integration was successful"""
        
        try:
            if capability.type == "python_module":
                module_name = capability.name.replace('python_', '')
                try:
                    importlib.import_module(module_name)
                    return True
                except ImportError:
                    return False
            
            elif capability.type == "cli_tool":
                tool_name = capability.name.replace('cli_', '')
                result = subprocess.run(['which', tool_name], capture_output=True)
                return result.returncode == 0
            
            elif capability.type == "mcp_tool":
                # Would need actual MCP testing
                return capability.metadata.get('mcp_configured', False)
            
            elif capability.type == "api":
                return capability.metadata.get('api_tested', False)
            
            # Default: assume success if we got here
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False
    
    def _create_rollback_point(self, capability: Capability, method: IntegrationMethod) -> Dict[str, Any]:
        """Create a rollback point for an integration"""
        
        return {
            'timestamp': datetime.now(),
            'capability': capability.name,
            'method': method,
            'state': {
                'installed_packages': self._get_installed_packages(),
                'environment': dict(os.environ),
                'registry_state': len(self.registry.capabilities)
            }
        }
    
    def _get_installed_packages(self) -> List[str]:
        """Get list of installed Python packages"""
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return [f"{p['name']}=={p['version']}" for p in packages]
        except:
            pass
        return []
    
    async def _rollback_integration(self, rollback_point: Dict[str, Any]) -> bool:
        """Rollback a failed integration"""
        
        logger.info(f"Rolling back integration of {rollback_point['capability']}")
        
        try:
            # Remove from registry
            await self.registry.unregister(rollback_point['capability'])
            
            # Method-specific rollback
            method = rollback_point['method']
            
            if method == IntegrationMethod.PIP_INSTALL:
                # Uninstall pip package
                package_name = rollback_point['capability'].replace('python_', '')
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'uninstall', '-y', package_name],
                    capture_output=True,
                    timeout=30
                )
            
            # Record rollback
            self._record_integration(
                Capability(name=rollback_point['capability'], type='unknown', description=''),
                method,
                IntegrationStatus.ROLLBACK
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def _record_integration(self, capability: Capability, method: IntegrationMethod,
                           status: IntegrationStatus, error: Optional[str] = None):
        """Record integration attempt in history"""
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'capability': capability.name,
            'method': method.value,
            'status': status.value,
            'error': error
        }
        
        self.integration_history.append(record)
        
        # Save to file
        history_file = self.integration_cache / 'integration_history.jsonl'
        with open(history_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
    
    async def batch_integrate(self, capabilities: List[Capability], 
                             parallel: bool = True) -> Dict[str, IntegrationStatus]:
        """Integrate multiple capabilities"""
        
        results = {}
        
        if parallel:
            # Integrate in parallel
            tasks = [
                self.integrate_capability(cap) for cap in capabilities
            ]
            statuses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for cap, status in zip(capabilities, statuses):
                if isinstance(status, Exception):
                    results[cap.name] = IntegrationStatus.FAILED
                else:
                    results[cap.name] = status
        else:
            # Integrate sequentially
            for cap in capabilities:
                results[cap.name] = await self.integrate_capability(cap)
        
        return results
    
    def get_integration_history(self, capability_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get integration history"""
        
        if capability_name:
            return [
                record for record in self.integration_history
                if record['capability'] == capability_name
            ]
        return self.integration_history
    
    async def auto_integrate_requirements(self, goal: str) -> Dict[str, IntegrationStatus]:
        """Automatically integrate capabilities needed for a goal"""
        
        from src.capabilities.discovery import CapabilityDiscovery
        
        # Discover what's needed
        discovery = CapabilityDiscovery()
        gaps = await discovery.analyze_capability_gaps(goal)
        
        results = {}
        
        for gap in gaps:
            # Try to find and integrate the capability
            cap = await discovery.discover_new_capability(gap)
            if cap:
                status = await self.integrate_capability(cap)
                results[gap] = status
            else:
                results[gap] = IntegrationStatus.FAILED
        
        return results