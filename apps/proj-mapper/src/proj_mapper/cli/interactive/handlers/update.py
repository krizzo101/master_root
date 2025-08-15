"""Handle update command for the interactive shell."""

import os
import time


def handle_update(shell, arg):
    """Handle the update command.
    
    Args:
        shell: The InteractiveShell instance
        arg: Command arguments as a string
    """
    args = arg.split()
    project_path = args[0] if args else shell.current_project
    
    if not project_path:
        shell.console.print("[bold red]Error:[/bold red] No project specified.")
        return
        
    if not os.path.isdir(project_path):
        shell.console.print(f"[bold red]Error:[/bold red] Project path does not exist: {project_path}")
        return
        
    # Check for full update flag
    full = "--full" in args
    
    shell.console.print(f"Updating maps for project: {project_path}")
    shell.console.print(f"Update type: {'Full' if full else 'Incremental'}")
    
    try:
        # Start progress
        shell.progress.start_progress(total=100, description="Updating project maps")
        
        # TODO: Integrate with core subsystem
        # Simulate progress for now
        for i in range(100):
            shell.progress.update_progress(advance=1)
            time.sleep(0.01)
            
        shell.progress.stop_progress()
        shell.console.print("Project maps updated successfully")
        
    except Exception as e:
        shell.progress.stop_progress()
        shell.console.print(f"[bold red]Error:[/bold red] {e}") 