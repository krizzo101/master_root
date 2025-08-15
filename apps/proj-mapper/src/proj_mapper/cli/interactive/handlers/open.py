"""Handle open command for the interactive shell."""

import os


def handle_open(shell, arg):
    """Handle the open command.
    
    Args:
        shell: The InteractiveShell instance
        arg: Command arguments as a string
    """
    if not arg:
        shell.console.print("[bold red]Error:[/bold red] Project path is required.")
        return
        
    project_path = arg
    if not os.path.isdir(project_path):
        shell.console.print(f"[bold red]Error:[/bold red] Project path does not exist: {project_path}")
        return
        
    shell.current_project = project_path
    shell.console.print(f"Current project set to: {project_path}")
    
    # Check for existing maps
    maps_dir = os.path.join(project_path, ".maps")
    map_file = os.path.join(maps_dir, "project_map.json")
    
    if os.path.exists(map_file):
        shell.console.print("Project maps found. Use 'info' command to view details.")
    else:
        shell.console.print("No project maps found. Use 'analyze' command to create maps.") 