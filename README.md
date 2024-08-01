<div align="center">

<h1 style="display: flex; justify-content: center; align-items: center; gap: 0.2em;"><img src="./logo.svg" width="30"> MathScript</h1>

[![GitHub Releases](https://img.shields.io/github/downloads/foxypiratecove37350/MathScript/total?labelColor=0c0d10&color=ee3333&style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyLjI1IDM4LjVIMzUuNzVDMzYuNzE2NSAzOC41IDM3LjUgMzkuMjgzNSAzNy41IDQwLjI1QzM3LjUgNDEuMTY4MiAzNi43OTI5IDQxLjkyMTIgMzUuODkzNSA0MS45OTQyTDM1Ljc1IDQySDEyLjI1QzExLjI4MzUgNDIgMTAuNSA0MS4yMTY1IDEwLjUgNDAuMjVDMTAuNSAzOS4zMzE4IDExLjIwNzEgMzguNTc4OCAxMi4xMDY1IDM4LjUwNThMMTIuMjUgMzguNUgzNS43NUgxMi4yNVpNMjMuNjA2NSA2LjI1NThMMjMuNzUgNi4yNUMyNC42NjgyIDYuMjUgMjUuNDIxMiA2Ljk1NzExIDI1LjQ5NDIgNy44NTY0N0wyNS41IDhWMjkuMzMzTDMwLjI5MzEgMjQuNTQwN0MzMC45NzY1IDIzLjg1NzMgMzIuMDg0NiAyMy44NTczIDMyLjc2OCAyNC41NDA3QzMzLjQ1MTQgMjUuMjI0MiAzMy40NTE0IDI2LjMzMjIgMzIuNzY4IDI3LjAxNTZMMjQuOTg5OCAzNC43OTM4QzI0LjMwNjQgMzUuNDc3MiAyMy4xOTg0IDM1LjQ3NzIgMjIuNTE1IDM0Ljc5MzhMMTQuNzM2OCAyNy4wMTU2QzE0LjA1MzQgMjYuMzMyMiAxNC4wNTM0IDI1LjIyNDIgMTQuNzM2OCAyNC41NDA3QzE1LjQyMDIgMjMuODU3MyAxNi41MjgyIDIzLjg1NzMgMTcuMjExNyAyNC41NDA3TDIyIDI5LjMyOVY4QzIyIDcuMDgxODMgMjIuNzA3MSA2LjMyODgxIDIzLjYwNjUgNi4yNTU4TDIzLjc1IDYuMjVMMjMuNjA2NSA2LjI1NThaIiBmaWxsPSIjZWUzMzMzIi8+Cjwvc3ZnPg==)](https://github.com/foxypiratecove37350/MathScript/releases)

<p>A Math programming language, by foxypiratecove37350</p>


</div>

## What is MathScript?

MathScript is a simple, yet powerful, programming language designed with mathematics in mind. It offers a clean and intuitive syntax, making it ideal for:

* **Mathematical calculations:** Perform complex operations, and work with maths effortlessly.
* **Data analysis:** Analyze and visualize data, perform statistical calculations, and build data models.
* **Algorithm development:** Develop algorithms, solve equations, and create simulations.

## Features

* **Intuitive Syntax:**  Inspired by mathematical notation, MathScript's syntax feels natural and easy to learn.
* **Data Structures:** Supports integers, decimals, complex numbers, strings, lists, and functions.
* **Control Flow:** Includes `if`, `elif`, `else`, `for`, `while`, and `func` statements for structured programming.
* **Built-in Functions:** Provides a collection of useful built-in functions for mathematical operations, input/output, and more.
* **Extensibility:**  The language is designed to be extensible with user-defined functions.
* **Cross-Platform:**  Runs on Windows, Linux, macOS and other platforms.

## Getting Started

1. **Install MathScript**:
    - From the GitHub release
    - Or fork the repsitory and then [build](#build)
2. **Run a program**:
   ```bash
   mathscript <your_program.mscr>
   ```
   Or **start an interractive shell**:
   ```bash
   mathscript
   ```

## Build

MathScript uses `cx_Freeze` for building the binaries.

You can build the binaries by running the following command in the root directory of the repository:
```bash
python setup.py build
```

This will create a `build/` directory containing the binaries for your platform in a subdirectory. The MathScript executable will be in the subdirectory of your platform and will be named `mathscript`.
   
## Example

Here's a simple MathScript program to calculate the area of a circle:

```mathscript
func circle_area(radius) => pi * radius ^ 2
print(circle_area(5))
```

## Documentation

<!-- You can find the full documentation of MathScript here: [Docs link](Docs link) -->

## Contributing

Contributions to MathScript are always welcome! Feel free to submit issues, pull requests, or suggest new features.

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Make your changes.
4. Test your changes thoroughly.
5. Submit a pull request.

## License

MathScript is licensed under the GNU General Public License v2.0. See the [`LICENSE`](./LICENSE) file for details.