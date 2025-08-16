class ProjectDiscoveryStage(AnalysisStage):
    """Stage for discovering project files and structure."""

    def run(self, context: AnalysisContext) -> None:
        """Run the project discovery stage.
        
        Args:
            context: Analysis context
        """
        logger.info("Starting project discovery stage")
        logger.debug(f"Project root: {context.project_root}")
        logger.debug(f"Config: {context.config}")
        
        # Create file discovery instance
        file_discovery = FileDiscovery(
            include_patterns=context.config.include_patterns,
            exclude_patterns=context.config.exclude_patterns,
            max_file_size=context.config.max_file_size
        )
        logger.debug("Created FileDiscovery instance")
        logger.debug(f"Include patterns: {file_discovery.include_patterns}")
        logger.debug(f"Exclude patterns: {file_discovery.exclude_patterns}")
        logger.debug(f"Max file size: {file_discovery.max_file_size}")
        
        # Discover files
        try:
            discovered_files = file_discovery.discover_files(context.project_root)
            logger.debug(f"File discovery completed. Found {len(discovered_files)} files")
            
            # Add files to context
            context.discovered_files = discovered_files
            logger.debug("Added discovered files to context")
            
            # Log file types summary
            type_counts = {}
            for file in discovered_files:
                file_type = file.file_type.value
                if file_type not in type_counts:
                    type_counts[file_type] = 0
                type_counts[file_type] += 1
            logger.debug("Files by type in context:")
            for file_type, count in type_counts.items():
                logger.debug(f"  {file_type}: {count}")
                
        except Exception as e:
            logger.error(f"Error during file discovery: {e}")
            raise
            
        logger.info("Project discovery stage completed") 