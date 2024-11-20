# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

datas_a = copy_metadata('streamlit')
datas = [('/Users/steelewski/projects/aider-forked/aider', 'aider'), ('/Users/steelewski/projects/aider-forked/aienv/lib/python3.11/site-packages/litellm', 'litellm'), ('/Users/steelewski/projects/aider-forked/aienv/lib/python3.11/site-packages/tree_sitter_language_pack', 'tree_sitter_language_pack'), ('/Users/steelewski/projects/aider-forked/aienv/lib/python3.11/site-packages/streamlit', 'streamlit'), ('/Users/steelewski/projects/aider-forked/streamlit_error_8501.log', '.'), ('/Users/steelewski/projects/aider-forked/recent_paths.json', '.'), ('/Users/steelewski/projects/aider-forked/requirements.txt', '.'), ('/Users/steelewski/projects/aider-forked/args.json', '.'), ('/Users/steelewski/projects/aider-forked/streamlit_8501.log', '.'), ('/Users/steelewski/projects/aider-forked/LICENSE.txt', '.')]
datas += copy_metadata('streamlit')

a = Analysis(
    ['entrypoint.py'],
    pathex=[],
    binaries=[],
    datas=datas_a + [('/Users/steelewski/projects/aider-forked/recent_paths.json', '.'), ('/Users/steelewski/projects/aider-forked/args.json', '.'),],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

b = Analysis(
    ['aider/main.py', 'aider/gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['prompt-toolkit', 'tiktoken_ext', 'tiktoken_ext.openai_public', 'streamlit.web.cli', 'streamlit.runtime.scriptrunner.magic_funcs', 'tiktoken_ext.openai_public', '_yaml', 'dnspython', 'GitPython', 'fastapi_cli', 'prompt-toolkit', 'tree_sitter_embedded_template', '__editable___aider_chat_0_58_2_dev48_gfe87e4bc_finder', 'toml', 'PyQt6_Qt6', 'brotli', 'dataclasses_json', 'frozenlist', 'aiohttp', 'diskcache', 'llama_index_readers_file', 'llama_index_core', 'pycparser', 'tqdm', 'multipart', 'altgraph', 'wrapt', 'cpuinfo', 'pydantic_extra_types', 'llama_index_program_openai', 'MarkupSafe', 'marshmallow', 'llama_index_cli', 'llama_parse', 'six', 'aiodns', 'idna', 'starlette', 'aider_chat', 'referencing', 'nest_asyncio', 'pyperclip', 'json5', 'SQLAlchemy', 'vai', 'pycares', 'PyInstaller', '_sounddevice', 'tqdm_loggable', 'tree-sitter-language-pack', 'markdown-it-py', 'shellingham', 'grep_ast', 'litellm', 'PyQt6', 'pypdf', 'huggingface_hub', 'networkx', 'llama_index_question_gen_openai', 'annotated-types', 'tree_sitter_language_pack', 'llama_index_agent_openai', 'llama_index_indices_managed_llama_cloud', 'pydantic', 'python-dotenv', 'distro', 'h11', 'importlib-resources', 'fastapi', 'attrs', 'uvicorn', 'pfzy', 'gitdb', 'jsonschema', 'tree_sitter_php', 'charset-normalizer', 'mdurl', 'pyyaml', 'altair', 'packaging', 'tree_sitter_xml', 'email_validator', 'regex', 'PyNaCl', 'pydantic_settings', 'ujson', 'sniffio', 'importlib_resources', 'jiter', 'diff-match-patch', '_distutils_hack', 'llama-parse', 'blinker', 'llama_index', 'dotenv', 'pyflakes', 'pydeck', 'inquirerpy', 'tests', 'rpds', 'pydantic_core', 'tzdata', 'dirtyjson', 'greenlet', 'cx_Freeze', 'smmap', 'ds_store', 'httpx', 'pytz', 'rich', '__editable___vai_0_58_2_dev55_ga21dd651_d20241018_finder', 'macholib', 'yarl', 'pip', 'mac_alias', 'scipy', 'python_dateutil', 'tomlkit', 'markupsafe', 'llama_index_legacy', 'nltk', 'jsonschema-specifications', 'markdown_it_py', 'python_dotenv', 'pathspec', 'gitpython', 'llama_index_llms_openai', 'huggingface-hub', 'PIL', '_soundfile_data', 'tenacity', '_soundfile', 'prompt_toolkit', 'zipp', 'paramiko', 'colorama', 'striprtf', 'nacl', 'anyio', 'runpod', 'typing_extensions', 'py_cpuinfo', 'pypager', 'annotated_types', 'sqlalchemy', 'configargparse', 'pydantic-core', '_sounddevice_data', 'soundfile', 'boto3', 'Deprecated', 'tiktoken', 'tree-sitter', 'httpcore', 'fsspec', 'cryptography', 'openai', 'yaml', 'pydub', 'filelock', 'tokenizers', 'dateutil', 'jinja2', 'aiohappyeyeballs', 'pillow', 'tomli', 'mccabe', 'pycodestyle', 'dns', 'backoff', 'typer', 'dmgbuild', 'rpds-py', 'pyinstaller_hooks_contrib', 'git', 'python-dateutil', 'requests', 'importlib-metadata', 'tornado', 'PyYAML', 'ConfigArgParse', 'streamlit', 'protobuf', 'aiohttp_retry', 'certifi', 'orjson', 'uvloop', 'typing-extensions', 'watchfiles', 'httptools', 'beautifulsoup4', 'psutil', 'llama_index_embeddings_openai', 'jmespath', 'click', 'tree_sitter', 'wcwidth', 'pygments', 'numpy', 'llama_cloud', 'itsdangerous', 'bs4', 'importlib_metadata', '_pyinstaller_hooks_contrib', 'pyinstaller', 'llama_index_multi_modal_llms_openai', 'markdown_it', 'tree_sitter_languages', 'pyarrow', 'narwhals', 'charset_normalizer', 'rpds_py', 'setuptools_scm', 'tree_sitter_typescript', 'grep-ast', 'llama_index_readers_llama_parse', 'pkg_resources', 'cx-Freeze', 'pypandoc', 'botocore', 'pandas', 'soupsieve', 'deprecated', 'cffi', 'prettytable', 'jsonschema_specifications', 'aiosignal', 'pexpect', 's3transfer', 'urllib3', 'benchmarks', 'multidict', 'Brotli', 'setuptools', 'PyQt6_sip', 'tree_sitter_c_sharp', 'sounddevice', 'websockets', 'InquirerPy', 'ptyprocess', 'bcrypt', 'attr', 'python_multipart', 'joblib', 'cachetools', 'typing_inspect', 'tree_sitter_yaml', 'watchdog', 'diff_match_patch', 'flake8', 'mypy_extensions', 'PIL._imaging', 'PIL._imagingmath', 'PIL._imagingmorph', 'PIL.ImageGrab', 'PIL.PngImagePlugin', 'PIL.JpegImagePlugin', 'PIL.Image'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)

pyz_a = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
pyz_b = PYZ(b.pure, b.zipped_data, cipher=block_cipher)

# Create EXE for entrypoint
exe_a = EXE(
    pyz_a,
    a.scripts,
    [],
    exclude_binaries=True,  # Important for --onedir
    name='launch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create EXE for ai app
exe_b = EXE(
    pyz_b,
    b.scripts,
    [],
    exclude_binaries=True,  # Important for --onedir
    name='ai',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create directory-based build for entrypoint
coll_a = COLLECT(
    exe_a,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='launcher'
)

# Create directory-based build for streamlit app
coll_b = COLLECT(
    exe_b,
    b.binaries,
    b.zipfiles,
    b.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vai'
)