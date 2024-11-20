import json
import os
import sys
import streamlit as st
from aider.main import main


def update_directory(directory):
    """Update session state and config with new directory."""
    if directory:
        if 'recent_directories' not in st.session_state:
            st.session_state.recent_directories = []

        if directory in st.session_state.recent_directories:
            st.session_state.recent_directories.remove(directory)
        st.session_state.recent_directories.insert(0, directory)

        st.session_state.recent_directories = st.session_state.recent_directories[:5]

        st.session_state.directory = directory

        save_config({
            'directory': st.session_state.directory,
            'openai_api_key': st.session_state.openai_api_key,
            'api_base': st.session_state.api_base,
            'model': st.session_state.model,
            'recent_directories': st.session_state.recent_directories
        })

        # st.rerun()


def save_config(config):
    """Save configuration to JSON file."""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        config_file = os.path.join(base_path, 'config.json')

        with open(config_file, 'w') as f:
            json.dump(config, f)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False


def load_config():
    """Load configuration from JSON file."""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        config_file = os.path.join(base_path, 'config.json')

        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
    return {}


config = load_config()


def settings_ui():
    # Initialize session state with config file values
    if 'config_loaded' not in st.session_state:
        st.session_state.directory = config.get('directory', '/Users/steelewski/projects/bpc-vh') # TODO delete default dir
        st.session_state.openai_api_key = config.get('openai_api_key', '')
        st.session_state.api_base = config.get('api_base', 'https://integrate.api.nvidia.com/v1')
        st.session_state.model = config.get('model', 'openai/nvidia/llama-3.1-nemotron-70b-instruct')
        st.session_state.recent_directories = config.get('recent_directories', [])
        st.session_state.config_loaded = True

    st.title("Configuration Settings")

    # Rest of the configuration form
    with st.form("config_form"):
        
        directory = st.text_input("Current Directory",
                      value=st.session_state.directory)

        openai_api_key = st.text_input("OpenAI API Key",
                                       value=st.session_state.openai_api_key,
                                       type="password",
                                       key="api_key_input")

        api_base = st.text_input("API Base URL",
                                 value=st.session_state.api_base,
                                 key="api_base_input")

        model = st.text_input("Model Name",
                              value=st.session_state.model,
                              key="model_input")

        submitted = st.form_submit_button("Save and start")

        if submitted:
            # Update session state
            st.session_state.directory = directory
            st.session_state.openai_api_key = openai_api_key
            st.session_state.api_base = api_base
            st.session_state.model = model

            # Save to config file
            new_config = {
                'directory': st.session_state.directory,
                'openai_api_key': openai_api_key,
                'api_base': api_base,
                'model': model,
                'recent_directories': st.session_state.recent_directories
            }

            print(f'MAIN STARTS')
            main(argv=[st.session_state.directory,
                       '--browser',
                       '--model', st.session_state.model,
                       '--map-tokens', '1024',
                       '--openai-api-key', st.session_state.openai_api_key,
                       '--openai-api-base', st.session_state.api_base,
                       ])

            if save_config(new_config):
                st.success("Configuration saved successfully! You can now proceed to the GUI page.")
            else:
                st.error("Failed to save configuration!")

    # Display current directory path
    if st.session_state.directory:
        st.info(f"Selected directory: {st.session_state.directory}")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Configuration Settings",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    settings_ui()
