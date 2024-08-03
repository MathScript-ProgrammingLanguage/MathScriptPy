import os
import subprocess
import sys

def add_to_path_win(new_path):
    new_path = new_path.strip().replace('/', '\\').removesuffix("\\")

    key = win32api.RegOpenKeyEx(
        win32con.HKEY_CURRENT_USER,
        r"Environment",
        0,
        win32con.KEY_ALL_ACCESS
    )

    current_path, _ = win32api.RegQueryValueEx(key, "Path")

    if new_path in current_path.split(os.pathsep) or \
       new_path + '\\' in current_path.split(os.pathsep):
        return

    new_path_value =  new_path + os.pathsep + current_path

    win32api.RegSetValueEx(key, "Path", 0, win32con.REG_EXPAND_SZ, new_path_value)
    win32api.RegCloseKey(key)

    refresh_path()

def edit_environment_variables_file(file_path, new_path):
    with open(file_path, 'a') as environment_variables_file:
        environment_variables_file.write(f'PATH="{new_path}{os.pathsep}$PATH"\n')

    refresh_path()

def add_to_path_bash(new_path):
    new_path = new_path.strip().replace('\\', '/').removesuffix('/')

    if os.path.exists(os.path.expanduser('~/.bash_profile')):
        file_path = os.path.expanduser('~/.bash_profile')
    elif os.path.expanduser('~/.profile'):
        file_path = os.path.expanduser('~/.profile')
    else:
        raise FileNotFoundError("Couldn't find the .bash_profile/.profile")

    edit_environment_variables_file(file_path, new_path)

def add_to_path_sh(new_path):
    new_path = new_path.strip().replace('\\', '/').removesuffix('/')

    if os.path.expanduser('~/.profile'):
        file_path = os.path.expanduser('~/.profile')
    else:
        raise FileNotFoundError("Couldn't find the .profile")

    edit_environment_variables_file(file_path, new_path)

def add_to_path_zsh(new_path):
    new_path = new_path.strip().replace('\\', '/').removesuffix('/')

    if os.path.expanduser('~/.zshenv'):
        file_path = os.path.expanduser('~/.zshenv')
    else:
        raise FileNotFoundError("Couldn't find the .zshenv")

    edit_environment_variables_file(file_path, new_path)

def add_to_path_unix(shell):
    if shell == 'bash':
        return add_to_path_bash
    elif shell == 'sh':
        return add_to_path_sh
    elif shell == 'zsh':
        return add_to_path_zsh
    
# ################################################################################

def remove_from_path_win(new_path):
    new_path = new_path.strip().replace('/', '\\').removesuffix("\\")

    key = win32api.RegOpenKeyEx(
        win32con.HKEY_CURRENT_USER,
        r"Environment",
        0,
        win32con.KEY_ALL_ACCESS
    )

    current_path, _ = win32api.RegQueryValueEx(key, "Path")
    current_path = current_path.split(os.pathsep)

    if new_path not in current_path or \
       new_path + '\\' not in current_path:
        return
    
    if new_path + '\\' in current_path:
        new_path = new_path + '\\'
    
    current_path.remove(new_path)

    win32api.RegSetValueEx(key, "Path", 0, win32con.REG_EXPAND_SZ, os.pathsep.join(current_path))
    win32api.RegCloseKey(key)

    refresh_path()

def remove_from_environment_variables_file(file_path, new_path):
    with open(file_path, 'r+') as environment_variables_file:
        content = environment_variables_file.read()
        if f'export PATH="{new_path}{os.pathsep}$PATH"\n' in content:
            content = content.replace(f'export PATH="{new_path}{os.pathsep}$PATH"\n', '')
        if f'PATH="{new_path}{os.pathsep}$PATH"\n' in content:
            content = content.replace(f'PATH="{new_path}{os.pathsep}$PATH"\n', '')

    refresh_path()

def remove_from_path_bash(new_path):
    new_path = new_path.strip().replace('\\', '/').removesuffix('/')

    if os.path.exists(os.path.expanduser('~/.bash_profile')):
        file_path = os.path.expanduser('~/.bash_profile')
    elif os.path.expanduser('~/.profile'):
        file_path = os.path.expanduser('~/.profile')
    else:
        raise FileNotFoundError("Couldn't find the .bash_profile/.profile")

    remove_from_environment_variables_file(file_path, new_path)

def remove_from_path_sh(new_path):
    new_path = new_path.strip().replace('\\', '/').removesuffix('/')

    if os.path.expanduser('~/.profile'):
        file_path = os.path.expanduser('~/.profile')
    else:
        raise FileNotFoundError("Couldn't find the .profile")

    remove_from_environment_variables_file(file_path, new_path)

def remove_from_path_zsh(new_path):
    new_path = new_path.strip().replace('\\', '/').removesuffix('/')

    if os.path.expanduser('~/.zshenv'):
        file_path = os.path.expanduser('~/.zshenv')
    else:
        raise FileNotFoundError("Couldn't find the .zshenv")

    remove_from_environment_variables_file(file_path, new_path)

def remove_from_path_unix(shell):
    if shell == 'bash':
        return remove_from_path_bash
    elif shell == 'sh':
        return remove_from_path_sh
    elif shell == 'zsh':
        return remove_from_path_zsh

# ################################################################################

def refresh_path_win():
    key = win32api.RegOpenKeyEx(
        win32con.HKEY_CURRENT_USER,
        r"Environment",
        0,
        win32con.KEY_ALL_ACCESS
    )

    current_path, _ = win32api.RegQueryValueEx(key, "Path")

    os.environ['PATH'] = current_path

    win32api.RegCloseKey(key)

def refresh_from_environment_variables_file(shell, file_path):
    proc = subprocess.Popen(
        [shell],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    proc.stdin.write(f"source {file_path}\n")
    proc.stdin.write(f"echo $PATH\n")

    path, _ = proc.communicate()

    os.environ['PATH'] = path

def refresh_path_bash():
    if os.path.exists(os.path.expanduser('~/.bash_profile')):
        file_path = '~/.bash_profile'
    elif os.path.expanduser('~/.profile'):
        file_path = '~/.profile'
    else:
        raise FileNotFoundError("Couldn't find the .bash_profile/.profile")

    refresh_from_environment_variables_file(shell, file_path)

def refresh_path_sh():
    if os.path.expanduser('~/.profile'):
        file_path = '~/.profile'
    else:
        raise FileNotFoundError("Couldn't find the .profile")

    refresh_from_environment_variables_file(shell, file_path)

def refresh_path_zsh():
    if os.path.expanduser('~/.zshenv'):
        file_path = '~/.zshenv'
    else:
        raise FileNotFoundError("Couldn't find the .zshenv")

    refresh_from_environment_variables_file(shell, file_path)

def refresh_path_unix(shell):
    if shell == 'bash':
        return refresh_path_bash
    elif shell == 'sh':
        return refresh_path_sh
    elif shell == 'zsh':
        return refresh_path_zsh

if sys.platform in ("win32", 'cygwin'):
    import win32api
    import win32con

    add_to_path = add_to_path_win
    remove_from_path = remove_from_path_win
    refresh_path = refresh_path_win
elif sys.platform.startswith("linux") or sys.platform == "darwin":
    shell = os.environ['SHELL'].removeprefix('/bin/')

    if shell in ('bash', 'sh', 'zsh'):
        add_to_path = add_to_path_unix(shell)
        remove_from_path = remove_from_path_unix(shell)
        refresh_path = refresh_path_unix(shell)
    else:
        raise NotImplementedError(f"Unsupported shell: {shell}")
else:
    raise NotImplementedError(f"Unsupported platform: {sys.platform}")