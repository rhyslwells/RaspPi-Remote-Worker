#!/usr/bin/env python3
"""
Main runner script - polls Config sheet and executes scripts.
Continuously monitors the Config worksheet and executes scripts
with START status, managing their complete lifecycle.
"""
import time
import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils.control_panel import ControlPanel, ScriptStatus


def run_script(script_name: str) -> tuple:
    """
    Dynamically import and execute a script.
    
    Args:
        script_name: Name of the script (e.g., "test_connection.py")
        
    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        # Remove .py extension if present
        module_name = script_name.replace('.py', '')
        script_path = Path(__file__).parent / f"{module_name}.py"
        
        if not script_path.exists():
            return (
                False,
                f"Script file not found",
                f"Expected: {script_path}"
            )
        
        # Dynamically import the script module
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            return (
                False,
                "Failed to load script module",
                f"Could not create module spec for {module_name}"
            )
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Execute the main function if it exists
        if hasattr(module, 'main'):
            result = module.main()
        elif hasattr(module, 'test_sheet_connection'):  # Special case for test_connection.py
            result = module.test_sheet_connection()
        else:
            return (
                False,
                "No main() or execution function found",
                f"Script must have a main() function that returns (success, message, details)"
            )
        
        # Ensure result is a tuple
        if not isinstance(result, tuple) or len(result) != 3:
            return (
                False,
                "Script returned invalid format",
                f"Expected (success: bool, message: str, details: str), got: {type(result)}"
            )
        
        return result
        
    except Exception as e:
        return (
            False,
            "Error executing script",
            f"{type(e).__name__}: {str(e)}"
        )


def main():
    """Main runner loop."""
    panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
    print("\n✅ Runner started - polling Config sheet for START status\n")
    
    while True:
        try:
            # Get only scripts with START status
            scripts_to_run = panel.get_scripts_to_run()
            
            for script_name in scripts_to_run:
                print(f"🚀 Executing: {script_name}")
                
                # Execute with full lifecycle management
                def execution_func():
                    return run_script(script_name)
                
                panel.execute_script_lifecycle(
                    script_name=script_name,
                    execution_func=execution_func
                )
            
            time.sleep(10)  # Poll every 10 seconds
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Runner stopped by user")
            break
        except Exception as e:
            panel.logger.error(f"Runner error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()