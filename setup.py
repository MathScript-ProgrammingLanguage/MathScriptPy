from cx_Freeze import setup, Executable
import mathscript
import subprocess

original_content = ""

with open('shell.py', 'r+') as f:
    original_content = content = f.read()

    try:
        git_release_tag = subprocess.check_output(['git', 'describe', '--tags']).decode('utf-8').strip()
        git_commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
        git_commit_date = subprocess.check_output(['git', 'show', '-s', '--format=%ci', 'HEAD']).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        git_release_tag = "latest"
        git_commit_hash = "latest"
        git_commit_date = None

    content = content.replace('git_release_tag = "latest"\ngit_commit_hash = "latest"\ngit_commit_date = None', f'git_release_tag = {repr(git_release_tag)}\ngit_commit_hash = {repr(git_commit_hash)}\ngit_commit_date = {repr(git_commit_date)}')

    f.seek(0)
    f.write(content)
    f.truncate()

build_options = {'packages': [], 'excludes': []}

base = 'console'

executables = [
    Executable('shell.py', base=base, target_name = mathscript.product_name.lower())
]

setup(name=mathscript.product_name,
      version = mathscript.version_str,
      description = mathscript.product_description,
      options = {'build_exe': build_options},
      executables = executables)

with open('shell.py', 'w') as f:
    f.write(original_content)