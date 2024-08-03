# MathScript Installer

This directory contains the source code for the MathScript installer. The installer is written using Python and PyQt5, and is designed to provide a user-friendly experience for installing, repairing, and uninstalling MathScript.

## Build

The build process require some dependencies:

- PyInstaller
- Pillow
- svg2png

**⚠️ In future releases, the `env.py` file will be replaced with the `pathenv` package on **PyPI**. ⚠️**

svg2png uses Inkscape to conver the SVG logo into PNG. If the PNG logo exists, it won't recreate it.

Firstly, install the dependencies using this command:

```bash
pip install -r requirements.txt
```

Then you can build the binaries for the installer by running the following command:

```bash
pyinstaller build.spec
```

This will generate a `dist` folder, containing the installer executable.

## Running the Installer

Once the installer has been built, you can run it by double-clicking the executable file. The installer will guide you through the installation process. You can also run it without building it using the following command:

```bash
python main.py
```

## Features

The installer provides the following features:

- **Installation:** Installs MathScript on the user's system, adding it to the PATH environment variable.
- **Repair:** Repairs an existing MathScript installation by reinstalling the necessary files and updating the PATH environment variable.
- **Uninstallation:** Uninstalls MathScript from the user's system, removing the installation directory and the PATH environment variable entry.

## Dependencies

The installer relies on the following Python libraries:

- **PyQt5:** For the installer's graphical user interface (GUI).
- **requests:** For downloading the MathScript installation files.
- **elevate:** For requesting administrator privileges on Windows.
- **pathvalidate:** For validating file paths.

## Contributing

Contributions to the MathScript installer are always welcome! If you find any issues or have any suggestions for improvements, please feel free to open an issue or submit a pull request.

## License

The MathScript installer is licensed under the GNU General Public License v2.0. See the [`LICENSE`](./LICENSE) file for details.