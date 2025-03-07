import os
import logging
import re
from pathlib import Path

from haystack import Pipeline


logger = logging.getLogger(__name__)

def _replace_env_vars(content):
    """Replace environment variables in the content with their values."""
    pattern = r'\${([^}]+)}'
    
    def replace_var(match):
        var_name = match.group(1)
        var_value = os.environ.get(var_name, '')
        logger.debug(f"Replacing environment variable {var_name} with value {var_value}")
        return var_value
    
    return re.sub(pattern, replace_var, content)

def load_pipeline(pipelines_dir, filename):
    if not pipelines_dir or not filename:
        return None

    p = Pipeline()
    yaml_path = os.path.join(pipelines_dir, filename)

    try:
        with open(yaml_path, "r") as f:
            logger.info(f"Loading pipeline definition from {yaml_path}")
            # Read the content and replace environment variables
            content = f.read()
            content_with_env_vars = _replace_env_vars(content)
            
            # Load the pipeline from the processed content
            return p.loads(content_with_env_vars)
    except FileNotFoundError:
        logger.warning(f"Pipeline definition not found: {yaml_path}")
    except Exception as e:
        logger.error(f"Error loading pipeline: {e}")
    return None
