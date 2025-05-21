"""
Configuration system for the E-commerce crawler
"""
import os
import json

# Environment-based configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Base configuration
BASE_CONFIG = {
    'max_pages': 20,
    'max_depth': 3,
    'delay_range': (2, 5),
    'timeout': 30,
    'stealth_mode': True,
    'user_agent_rotation': True,
    'proxy_rotation': False,
    'save_results': True,
    'results_dir': 'ecommerce_data',
    'analyze_robots': True,
    'analyze_sitemap': True,
    'follow_robots': True,
    'retry_attempts': 3,
    'retry_delay': 2,
    'debug': False
}

# Environment-specific configurations
CONFIGS = {
    'development': {
        **BASE_CONFIG,
        'max_pages': 10,
        'debug': True
    },
    'production': {
        **BASE_CONFIG,
        'max_pages': 50,
        'delay_range': (3, 7),
        'proxy_rotation': True,
        'debug': False
    },
    'streamlit_cloud': {
        **BASE_CONFIG,
        'max_pages': 15,
        'delay_range': (4, 8),
        'timeout': 20,
        'save_results': False,  # Don't save files on Streamlit Cloud
        'debug': False
    }
}

def load_config():
    """
    Load configuration based on environment
    
    Returns:
        dict: Configuration dictionary
    """
    # Get active configuration
    config = CONFIGS.get(ENVIRONMENT, BASE_CONFIG)
    
    # Override with environment variables if present
    for key in config:
        env_var = f'ECOMMERCE_CRAWLER_{key.upper()}'
        if env_var in os.environ:
            # Convert environment variable to appropriate type
            env_value = os.environ[env_var]
            if isinstance(config[key], bool):
                config[key] = env_value.lower() in ('true', 'yes', '1')
            elif isinstance(config[key], int):
                config[key] = int(env_value)
            elif isinstance(config[key], float):
                config[key] = float(env_value)
            elif isinstance(config[key], tuple) and ',' in env_value:
                config[key] = tuple(float(x) for x in env_value.split(','))
            else:
                config[key] = env_value
    
    # Try to load from config.json if it exists
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                # Update config with file values
                config.update(file_config)
        except Exception as e:
            print(f"Error loading config.json: {str(e)}")
    
    return config

# Get the active configuration
config = load_config()

def save_config(config_dict):
    """
    Save configuration to config.json
    
    Args:
        config_dict (dict): Configuration dictionary to save
    """
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        # Convert tuple to list for JSON serialization
        serializable_config = {}
        for key, value in config_dict.items():
            if isinstance(value, tuple):
                serializable_config[key] = list(value)
            else:
                serializable_config[key] = value
        
        with open(config_file, 'w') as f:
            json.dump(serializable_config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config.json: {str(e)}")
        return False
