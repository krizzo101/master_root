
import os, sys, argparse
from genfilemap.config import DEFAULT_CONFIG, save_config

def create_project_config(config_path):
    """Create a project-specific configuration"""
    project_config = {
        "output_dirs": {
            "maps": ".genfilemap/maps",
            "logs": ".genfilemap/logs",
            "cache": ".genfilemap/cache",
            "reports": ".genfilemap/reports"
        },
        "project_map_output": ".genfilemap/maps/PROJECT_FILE_MAP.md",
        "output": {
            "template": "standard",
            "template_dir": ".genfilemap/templates",
            "schema_path": ".genfilemap/schemas/schema.json",
            "report_path": ".genfilemap/reports/filemap_report.json"
        }
    }
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    save_config(project_config, config_path)
    return project_config

def create_global_config(config_path):
    """Create the global configuration"""
    # Define the base directory for all global files
    base_dir = os.path.expanduser("~/.genfilemap")
    
    global_config = {
        "output_dirs": {
            "maps": os.path.join(base_dir, ".local/share/maps"),
            "logs": os.path.join(base_dir, ".local/share/logs"),
            "cache": os.path.join(base_dir, ".cache"),
            "config": os.path.join(base_dir, ".config"),
            "templates": os.path.join(base_dir, ".local/share/templates"),
            "schemas": os.path.join(base_dir, ".local/share/schemas")
        },
        "project_map_output": os.path.join(base_dir, ".local/share/maps/PROJECT_FILE_MAP.md"),
        "output": {
            "template": "standard",
            "template_dir": os.path.join(base_dir, ".local/share/templates"),
            "schema_path": os.path.join(base_dir, ".local/share/schemas/schema.json"),
            "report_path": os.path.join(base_dir, ".local/share/reports/filemap_report.json")
        }
    }
    
    # Create all necessary directories
    for dir_path in global_config["output_dirs"].values():
        os.makedirs(dir_path, exist_ok=True)
    
    os.makedirs(os.path.dirname(global_config["project_map_output"]), exist_ok=True)
    os.makedirs(os.path.dirname(global_config["output"]["schema_path"]), exist_ok=True)
    os.makedirs(global_config["output"]["template_dir"], exist_ok=True)
    os.makedirs(os.path.dirname(global_config["output"]["report_path"]), exist_ok=True)
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    save_config(global_config, config_path)
    return global_config

parser = argparse.ArgumentParser(description="Initialize GenFileMap configuration")
parser.add_argument("--global-config", default=os.path.expanduser("~/.genfilemap/.config/config.json"),
                    help="Path to create global configuration file")
parser.add_argument("--project-config", default=".genfilemap.json",
                    help="Path to create project-specific configuration file")
parser.add_argument("--init-type", choices=["global", "project", "both"], default="both",
                    help="Type of configuration to initialize")
args = parser.parse_args()

if args.init_type in ["global", "both"]:
    global_config = create_global_config(args.global_config)
    print(f"\nCreated global configuration at: {args.global_config}")
    print("\nGlobal directory structure:")
    print(f"  Config: {os.path.dirname(args.global_config)}")
    for name, path in global_config["output_dirs"].items():
        print(f"  {name.capitalize()}: {path}")
    print(f"  Templates: {global_config['output']['template_dir']}")
    print(f"  Project Maps: {os.path.dirname(global_config['project_map_output'])}")
    print(f"  Schemas: {os.path.dirname(global_config['output']['schema_path'])}")
    print(f"  Reports: {os.path.dirname(global_config['output']['report_path'])}")

if args.init_type in ["project", "both"]:
    project_config = create_project_config(args.project_config)
    print(f"\nCreated project configuration at: {args.project_config}")
    print("\nProject directory structure:")
    print(f"  Config: {os.path.dirname(args.project_config)}")
    for name, path in project_config["output_dirs"].items():
        print(f"  {name.capitalize()}: {path}")
    print(f"  Templates: {project_config['output']['template_dir']}")
    print(f"  Project Maps: {os.path.dirname(project_config['project_map_output'])}")
    print(f"  Schemas: {os.path.dirname(project_config['output']['schema_path'])}")
    print(f"  Reports: {os.path.dirname(project_config['output']['report_path'])}") 