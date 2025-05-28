#!/usr/bin/env python3
"""
Setup script for installing twagent dependencies.

This script clones the twagent repository and installs its dependencies
to enable Twitter automation capabilities in XAgent.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("twagent-setup")


def run_command(command, cwd=None):
    """Run a shell command and return its output."""
    logger.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            cwd=cwd,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        raise


def clone_twagent(target_dir, force=False):
    """Clone the twagent repository."""
    if os.path.exists(target_dir):
        if force:
            logger.info(f"Removing existing directory: {target_dir}")
            shutil.rmtree(target_dir)
        else:
            logger.info(f"Directory already exists: {target_dir}")
            return False

    logger.info(f"Cloning twagent repository to {target_dir}")
    run_command(f"git clone https://github.com/lord-dubious/twagent {target_dir}")
    return True


def install_dependencies(twagent_dir):
    """Install twagent dependencies."""
    logger.info("Installing twagent dependencies")
    
    # Create a requirements.txt file with twagent dependencies
    requirements = [
        "playwright>=1.40.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "tqdm>=4.66.1",
        "elevenlabs>=0.2.26",
        "langchain>=0.0.335",
        "langchain-openai>=0.0.2",
        "openai>=1.3.7",
        "pydantic>=2.5.2",
    ]
    
    requirements_path = os.path.join(twagent_dir, "requirements.txt")
    with open(requirements_path, "w") as f:
        f.write("\n".join(requirements))
    
    # Install dependencies
    run_command(f"pip install -r {requirements_path}")
    
    # Install playwright browsers
    run_command("playwright install chromium")
    
    return True


def create_symlinks(twagent_dir, xv_ui_dir):
    """Create symlinks to make twagent accessible to XAgent."""
    logger.info("Creating symlinks for twagent integration")
    
    # Create browser_use symlink in the Python path
    site_packages = run_command("python -c 'import site; print(site.getsitepackages()[0])'")
    browser_use_target = os.path.join(site_packages, "browser_use")
    
    if os.path.exists(browser_use_target) or os.path.islink(browser_use_target):
        logger.info(f"Removing existing symlink: {browser_use_target}")
        if os.path.islink(browser_use_target):
            os.unlink(browser_use_target)
        else:
            shutil.rmtree(browser_use_target)
    
    browser_use_source = os.path.join(twagent_dir, "browser-use")
    logger.info(f"Creating symlink: {browser_use_source} -> {browser_use_target}")
    os.symlink(browser_use_source, browser_use_target)
    
    # Create data directories
    os.makedirs(os.path.join(xv_ui_dir, "personas"), exist_ok=True)
    os.makedirs(os.path.join(xv_ui_dir, "data"), exist_ok=True)
    
    # Copy example config and cookies files
    shutil.copy(
        os.path.join(twagent_dir, "config.json"),
        os.path.join(xv_ui_dir, "config.json"),
    )
    shutil.copy(
        os.path.join(twagent_dir, "cookies.example.json"),
        os.path.join(xv_ui_dir, "cookies.example.json"),
    )
    
    # Copy example personas
    personas_source = os.path.join(twagent_dir, "personas")
    personas_target = os.path.join(xv_ui_dir, "personas")
    
    for item in os.listdir(personas_source):
        source_item = os.path.join(personas_source, item)
        target_item = os.path.join(personas_target, item)
        
        if os.path.isfile(source_item):
            shutil.copy(source_item, target_item)
    
    return True


def main():
    """Main function to set up twagent."""
    parser = argparse.ArgumentParser(description="Set up twagent for XAgent integration")
    parser.add_argument(
        "--twagent-dir",
        default="/tmp/twagent",
        help="Directory to clone twagent repository to",
    )
    parser.add_argument(
        "--xv-ui-dir",
        default=".",
        help="Directory of the xv-ui repository",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstallation even if directories exist",
    )
    args = parser.parse_args()
    
    logger.info("Starting twagent setup")
    
    try:
        # Clone twagent repository
        clone_success = clone_twagent(args.twagent_dir, args.force)
        if not clone_success and not args.force:
            logger.info("Using existing twagent repository")
        
        # Install dependencies
        install_dependencies(args.twagent_dir)
        
        # Create symlinks
        create_symlinks(args.twagent_dir, args.xv_ui_dir)
        
        logger.info("✅ twagent setup completed successfully!")
        logger.info(f"Twitter agent is now available in XAgent")
        logger.info(f"Example config file: {os.path.join(args.xv_ui_dir, 'config.json')}")
        logger.info(f"Example cookies file: {os.path.join(args.xv_ui_dir, 'cookies.example.json')}")
        logger.info(f"Personas directory: {os.path.join(args.xv_ui_dir, 'personas')}")
        
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

