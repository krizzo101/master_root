#!/usr/bin/env python3
"""
Autonomous Coder - Main Entry Point
Build any software from natural language descriptions using current technology.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
import json

from core.base import BuildRequest
from core.config import Config
from modules.orchestrator import Orchestrator


async def main(
    description: str,
    output_path: Optional[str] = None,
    config_file: Optional[str] = None,
    interactive: bool = False,
    force_research: bool = True
):
    """Main function to run the autonomous coder."""
    
    print("\n" + "="*60)
    print("🚀 AUTONOMOUS CODER v2.0")
    print("Building with 2024-2025 Technology")
    print("="*60 + "\n")
    
    # Load configuration
    config = None
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            config = Config(config_path)
            print(f"✅ Loaded config from {config_file}")
    
    if not config:
        config = Config()
        print("📋 Using default configuration")
    
    # Create build request
    output = Path(output_path) if output_path else Path("./output")
    request = BuildRequest(
        description=description,
        output_path=output,
        force_research=force_research,
        interactive=interactive
    )
    
    print(f"📝 Request: {description}")
    print(f"📁 Output: {output}\n")
    
    # Initialize orchestrator
    orchestrator = Orchestrator(config.config)
    
    try:
        # Execute build
        result = await orchestrator.build(request)
        
        # Save result
        result_file = output / "build_result.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        with open(result_file, 'w') as f:
            f.write(result.to_json())
        
        if result.success:
            print(f"\n✅ Build successful!")
            print(f"📁 Project created at: {result.project_path}")
            print(f"📄 {len(result.files_created)} files generated")
            print(f"⏱️  Completed in {result.execution_time:.2f} seconds")
            
            # Show next steps
            print("\n📚 Next Steps:")
            if (result.project_path / "package.json").exists():
                print("  1. cd " + str(result.project_path))
                print("  2. pnpm install (or npm install)")
                print("  3. pnpm dev (or npm run dev)")
            elif (result.project_path / "requirements.txt").exists():
                print("  1. cd " + str(result.project_path))
                print("  2. python -m venv venv")
                print("  3. source venv/bin/activate")
                print("  4. pip install -r requirements.txt")
                print("  5. python main.py")
            
            return 0
        else:
            print(f"\n❌ Build failed!")
            for error in result.errors:
                print(f"  • {error}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Build interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


def cli():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Autonomous Coder - Build any software from natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Build a TODO app with React and TypeScript"
  %(prog)s "Create a REST API for managing users" --output ./my-api
  %(prog)s "Build a CLI tool for file processing" --config custom.yaml
  
Tech Stack (2024-2025):
  • Frontend: React 19, Vue 3.5, Vite 7
  • Backend: FastAPI, Express, Django 5
  • Languages: TypeScript 5.7, Python 3.13
  • Testing: Vitest, Playwright, Pytest
  • Databases: PostgreSQL 17, MongoDB 8
        """
    )
    
    parser.add_argument(
        'description',
        help='Natural language description of what to build'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: ./output)',
        default='./output'
    )
    
    parser.add_argument(
        '-c', '--config',
        help='Configuration file (YAML or JSON)',
        default=None
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode with prompts'
    )
    
    parser.add_argument(
        '--no-research',
        action='store_true',
        help='Skip research phase (use cached data)'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear research cache before building'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    args = parser.parse_args()
    
    # Clear cache if requested
    if args.clear_cache:
        from modules.research_engine import ResearchEngine
        engine = ResearchEngine()
        engine.clear_cache()
        print("✅ Cache cleared")
    
    # Run the main function
    exit_code = asyncio.run(main(
        description=args.description,
        output_path=args.output,
        config_file=args.config,
        interactive=args.interactive,
        force_research=not args.no_research
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()