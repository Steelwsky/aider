# bootstrap_streamlit.py FILE
import os
import sys
import streamlit.web.bootstrap as bootstrap

def run_streamlit():
    # Get the directory containing the executable
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        os.environ['STREAMLIT_SERVER_WATCH_DIRS'] = 'false'
        os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Point to main.py as the main script
    main_script_path = os.path.join(base_path, 'config.py')
    
    # Define flag options
    flag_options = {
        'server.address': 'localhost',
        'server.port': 8501,
        'server.headless': True,
        'server.runOnSave': False,
        'browser.serverAddress': 'localhost',
        'browser.serverPort': 8501,
        'global.developmentMode': False,
    }

    # Set environment variables
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Run the Streamlit application
    bootstrap.run(
        main_script_path,
        False,
        args=[],
        flag_options=flag_options
    )

if __name__ == '__main__':
    run_streamlit()