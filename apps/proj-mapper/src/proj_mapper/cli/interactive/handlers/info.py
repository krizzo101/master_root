"""Handle info command for the interactive shell."""

import os
import json


def handle_info(shell, arg):
    """Handle the info command.
    
    Args:
        shell: The InteractiveShell instance
        arg: Command arguments as a string
    """
    project_path = arg or shell.current_project
    
    if not project_path:
        shell.console.print("[bold red]Error:[/bold red] No project specified.")
        return
        
    if not os.path.isdir(project_path):
        shell.console.print(f"[bold red]Error:[/bold red] Project path does not exist: {project_path}")
        return
        
    # Check for existing maps
    maps_dir = os.path.join(project_path, ".maps")
    map_file = os.path.join(maps_dir, "project_map.json")
    
    if not os.path.exists(map_file):
        shell.console.print(f"[bold red]Error:[/bold red] No maps found for project: {project_path}")
        shell.console.print("Run 'analyze' command first.")
        return
        
    # Load the map file
    try:
        with open(map_file, 'r') as f:
            project_map = json.load(f)
            
        # Display project information
        from proj_mapper.cli.interactive.prompt import create_project_info_table
        table = create_project_info_table(project_map)
        shell.console.print(table)
        
    except Exception as e:
        shell.console.print(f"[bold red]Error:[/bold red] Error loading project map: {e}") 