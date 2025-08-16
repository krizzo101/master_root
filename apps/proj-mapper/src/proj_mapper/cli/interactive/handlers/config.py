"""Handle config command for the interactive shell."""


def handle_config(shell, arg):
    """Handle the config command.
    
    Args:
        shell: The InteractiveShell instance
        arg: Command arguments as a string
    """
    args = arg.split()
    
    if not args or "--list" in args:
        # Display current configuration
        from proj_mapper.cli.interactive.prompt import create_config_table
        table = create_config_table(shell.config)
        shell.console.print(table)
            
    elif args[0] == "--save" and len(args) > 1:
        # Save configuration to file
        filename = args[1]
        try:
            shell.config_manager.save_config(filename, shell.config)
            shell.console.print(f"Configuration saved to: {filename}")
        except Exception as e:
            shell.console.print(f"[bold red]Error:[/bold red] Error saving configuration: {e}")
            
    elif len(args) == 1:
        # Get specific configuration value
        key = args[0]
        keys = key.split('.')
        config = shell.config
        
        try:
            for k in keys:
                config = config[k]
                
            shell.console.print(f"{key} = {config}")
        except (KeyError, TypeError):
            shell.console.print(f"[bold red]Error:[/bold red] Configuration key not found: {key}")
            
    elif len(args) >= 2:
        # Set configuration value
        key = args[0]
        value = " ".join(args[1:])
        
        # Parse value
        if value.lower() in ["true", "yes"]:
            value = True
        elif value.lower() in ["false", "no"]:
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
            value = float(value)
            
        # Set the value
        keys = key.split('.')
        config = shell.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        shell.console.print(f"Set {key} = {value}") 