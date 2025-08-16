import sys
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Store the original excepthook
original_excepthook = sys.excepthook

def detailed_excepthook(exc_type, exc_value, exc_traceback):
    """Enhanced exception hook that provides more details for attribute errors."""
    if exc_type is AttributeError and str(exc_value) == "'str' object has no attribute 'value'":
        logger.error("FOUND THE ERROR: 'str' object has no attribute 'value'")
        # Print the traceback in a more useful format
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # Print the formatted traceback
        for line in tb_lines:
            logger.error(line.rstrip())
        
        # Attempt to get more context
        frames = traceback.extract_tb(exc_traceback)
        if frames:
            last_frame = frames[-1]
            filename, lineno, funcname, line = last_frame
            logger.error(f"Error occurred in {filename} at line {lineno} in function {funcname}")
            if line:
                logger.error(f"Code: {line}")
                
            # Try to get variable values
            frame_obj = None
            for frame, _ in traceback.walk_tb(exc_traceback):
                if frame.f_code.co_filename == filename and frame.f_lineno == lineno:
                    frame_obj = frame
                    break
                    
            if frame_obj:
                logger.error("Local variables in the frame:")
                for var_name, var_value in frame_obj.f_locals.items():
                    logger.error(f"  {var_name} = {repr(var_value)}")
                    # If this is a relationship_type, inspect it further
                    if "relationship_type" in var_name.lower():
                        logger.error(f"  -> Type: {type(var_value)}")
                        logger.error(f"  -> Dir: {dir(var_value)}")
    
    # Call the original excepthook
    original_excepthook(exc_type, exc_value, exc_traceback)

# Install our custom exception hook
sys.excepthook = detailed_excepthook

# Now run the command
import os
import subprocess

print("Running relationship detection with custom exception tracer...")
cmd = [
    "python", "-m", "proj_mapper", "relationship", "detect-relationships",
    "--code-dir", "src",
    "--docs-dir", "docs",
    "--output-file", "relationships.json",
    "--include-code", "*.py",
    "--exclude-code", "__pycache__,venv"
]

# Set environment variable to ensure we can find the module
os.environ["PYTHONPATH"] = "."

try:
    # Execute the command
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"Output: {result.stdout}")
    print(f"Error: {result.stderr}")
except Exception as e:
    print(f"Error running command: {e}")
    traceback.print_exc() 