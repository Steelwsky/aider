import PyInstaller.__main__
import os
import re
import sys
import json
import shutil
import site
from pathlib import Path
import litellm
import tree_sitter_language_pack
import streamlit

# Get the absolute path to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
litellm_path = os.path.dirname(os.path.abspath(litellm.__file__))
tree_sitter_path = os.path.dirname(os.path.abspath(tree_sitter_language_pack.__file__))
streamlit_path = os.path.dirname(os.path.abspath(streamlit.__file__))


def get_requirements():
    req_file = os.path.join(script_dir, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            content = f.read()

            # Split into lines and filter out comments and empty lines
            lines = [line.strip() for line in content.split('\n')]
            lines = [line for line in lines if line and not line.startswith('#')]

            # Extract package names without versions and comments
            packages = []
            for line in lines:
                # If line contains "# via", take only the part before it
                if '#' in line:
                    line = line.split('#')[0].strip()

                # Extract package name (everything before any version specifier)
                match = re.match(r'^([a-zA-Z0-9\-._]+)', line)
                if match:
                    packages.append(match.group(1))

            return list(set(packages))
    return []


def get_venv_packages():
    """Get list of packages installed in the virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment
        venv_site_packages = Path(
            sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
        if not venv_site_packages.exists():
            # Try Windows path format
            venv_site_packages = Path(sys.prefix) / 'Lib' / 'site-packages'
    else:
        # We're not in a virtual environment, use system site-packages
        venv_site_packages = Path(site.getsitepackages()[0])

    packages = []
    if venv_site_packages.exists():
        for item in venv_site_packages.iterdir():
            if item.is_dir():
                # Handle regular packages
                if (item / '__init__.py').exists():
                    packages.append(item.name)
                # Handle dist-info directories
                elif item.name.endswith('.dist-info'):
                    packages.append(item.name.split('-')[0])
            elif item.is_file() and item.suffix == '.py':
                # Handle single-file packages
                packages.append(item.stem)

    return list(set(packages))


# Get dependencies from requirements.txt
dependencies = get_requirements()
venv_packages = get_venv_packages()
all_packages = list(set(dependencies + venv_packages))

# Collect data files from the root directory
data_files = []
for file in os.listdir(script_dir):
    if file.endswith(('.json', '.log', '.txt')):
        if file == 'history.json':
            history_path = os.path.join(script_dir, file)
            with open(history_path, 'w') as f:
                # Write an empty list to the file
                json.dump(['/Users/steelewski/projects/bpc-vh'], f)
            print(f"Cleared contents of {file}")
        data_files.append(os.path.join(script_dir, file))

# PyInstaller command
pyinstaller_command = [
    'entrypoint.py',
    '--name=vai',
    '--onedir',
    '--windowed',
    '--log-level=DEBUG',
    '--debug=all',
    '--clean',
    f'--add-data={os.path.join(script_dir, "aider")}:aider',
    f'--add-data={litellm_path}:litellm',
    f'--add-data={tree_sitter_path}:tree_sitter_language_pack',
    f'--add-data={streamlit_path}:streamlit',
    # '--hidden-import=streamlit',
    '--copy-metadata=streamlit',
    '--hidden-import=prompt-toolkit',
    '--hidden-import=tiktoken_ext',
    '--hidden-import=tiktoken_ext.openai_public',
    '--hidden-import=streamlit.web.cli',
    '--hidden-import=streamlit.runtime.scriptrunner.magic_funcs',
    '--hidden-import=tiktoken_ext.openai_public',
]

PIL_IMPORTS = [
    'PIL._imaging',
    'PIL._imagingmath',
    'PIL._imagingmorph',
    'PIL.ImageGrab',
    'PIL.PngImagePlugin',
    'PIL.JpegImagePlugin',
    'PIL.Image',
]

# Add data files
for file in data_files:
    pyinstaller_command.extend(['--add-data', f'{file}:.'])

# Add each dependency as a hidden import
for package in all_packages:
    pyinstaller_command.append(f'--hidden-import={package}')

for pil_import in PIL_IMPORTS:
    pyinstaller_command.append(f'--hidden-import={pil_import}')

print("Starting PyInstaller with command:", ' '.join(pyinstaller_command))

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_command)
