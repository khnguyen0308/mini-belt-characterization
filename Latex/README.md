# Project Lab of Embedded Systems

This repository contains the LaTeX source for the report "Project Lab of Embedded Systems".

## What is in the repo

- `main.tex` is the root file for the document.
- `overview.tex`, `literature_review.tex`, `code_understanding.tex`, and `Hardware_setup.tex` are included from `main.tex`.
- `references.bib` contains the bibliography entries.
- Image files such as `AD8421.jpg`, `dac_output.jpeg`, and `TU_Chemnitz_Logo_gruen.png` are used in the report.

## Requirements

To build the PDF, you need a LaTeX distribution with these tools installed:

- `latexmk`
- `pdflatex`
- `biber`

On Windows, MiKTeX works well. This repository also contains installers that can be used offline if needed:

- `basic-miktex-25.12-x64.exe`
- `strawberry-perl-5.42.2.1-64bit.msi`

## Recommended VS Code setup

If you want to work in VS Code, install these extensions:

- LaTeX Workshop
- PDF Viewer or the built-in PDF preview is enough for reading the generated PDF

Recommended LaTeX Workshop settings are simple and do not require a custom `.vscode` folder for this project. The document is built from `main.tex`, and the default LaTeX Workshop recipe can use `latexmk` directly.

## Build instructions

From the project root, run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

If you want to force a full rebuild, use:

```bash
latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex
```

## Clean build files

LaTeX creates temporary files such as `.aux`, `.bcf`, `.bbl`, `.blg`, `.fdb_latexmk`, `.fls`, `.log`, `.out`, `.run.xml`, `.synctex.gz`, and `.toc`.

If you want a clean rebuild, delete those generated files and run `latexmk` again.

## Notes for contributors

- Keep `main.tex` as the single root entry point.
- Add new sections as separate `.tex` files and include them from `main.tex`.
- Put bibliography entries in `references.bib`.
- Keep image files in the repository so the document can be built without extra setup.

If you add a new figure or citation, run the build command once more so the references and table of contents update correctly.