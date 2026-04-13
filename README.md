# SZR+ (Susceptibility Zoning + Raster)

[![QGIS](https://img.shields.io/badge/QGIS-3.28+-blue.svg)](https://www.qgis.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Introduction

**SZR+** is an advanced QGIS plugin for susceptibility mapping and spatial analysis. It is a major evolution based on the original **SZ-plugin version 1.1.5**. 

> [!NOTE]
> While the original SZ-plugin project has recently released a version 2.0 with new features, **SZR+** is independently developed based on the 1.x codebase, introducing native raster capabilities and a completely redesigned GUI.

While primarily developed for landslide susceptibility, SZR+ is a versatile tool applicable to various natural hazards and inter-disciplinary spatial modeling tasks.

### Key Features
*   **Modern GUI**: A redesigned, user-friendly interface based on QGIS processing standards.
*   **Vector Base Mode**: Retains all the original vector-based analysis functions from the SZ-plugin version 1.1.5, fully integrated into the redesigned UI.
*   **Raster Base Mode**:
    *   **Native Raster Support**: Direct processing of raster datasets for faster and more scalable analysis.
        *   **Requirement**: All input rasters must be aligned and have the exact same spatial resolution.
        *   **Requirement (Landslide Inventory)**: The landslide inventory must be a binary raster (1 for landslide occurrence, 0 for no landslide).
    *   **Statistical Models**:
        *   Weight of Evidence (WoE)
        *   Frequency Ratio (FR)
        *   Logistic Regression (LR)
        *   Decision Tree (DT)
        *   Support Vector Machine (SVM)
        *   Random Forest (RF)
    *   **Validation**:
        *   Random Test/Train split.
        *   K-Fold Cross-Validation.
        *   ROC Curve and AUC generation.
    *   **Classification**: Advanced SI classification methods (ROC maximization, F1-Score, Threat Score).

## Installation

SZR+ can be installed manually into QGIS.

### Minimum Requirements
*   **QGIS**: 3.28+
*   **Dependencies**: `scikit-learn`, `libpysal` (Usually handled by the built-in installer).

### Install from ZIP (Recommended)
1.  Download this repository as a ZIP file and extract it.
2.  Locate the `szr_module` folder.
3.  **Important**: Create a new ZIP file that contains *only* the `szr_module` folder itself.
4.  In QGIS, go to **Plugins** > **Manage and Install Plugins...**
5.  Select **Install from ZIP** on the left sidebar.
6.  Select your new `szr_module.zip` and click **Install Plugin**.

### Manual Install (Copy/Paste)
1.  Download this repository as a ZIP file and extract it.
2.  Locate the folder named `szr_module`.
3.  Copy the `szr_module` folder to your QGIS plugins directory:
    *   **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
    *   **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
    *   **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
4.  Open QGIS and enable **SZR+** in the **Plugin Manager**.

## How to Cite

If you use SZR+ in your research, please acknowledge both the original work and the current version:

**Original SZ-Plugin Citation:**
> Titti G, Sarretta A, Lombardo L, Crema S, Pasuto A and Borgatti L (2022). Mapping Susceptibility With Open-Source Tools: A New Plugin for QGIS. *Front. Earth Sci.* 10:842425. doi: [10.3389/feart.2022.842425](https://doi.org/10.3389/feart.2022.842425)

**SZR+ Development:**
> This version (SZR+) was developed by **Cristobal Padilla** (2026), building upon the core logic by **Giacomo Titti**.

## Development and Credits

*   **Main Author**: Cristobal Padilla
*   **Original Author**: Giacomo Titti (CNR-IRPI-Padova)
*   **Contributors**: Alessandro Sarretta, Luigi Lombardo, Alessandro Corsini, Cecilia Fabbiani.
*   **Acknowledgments**: UI redesigned with Qt Designer. Code logic and algorithms refined with the assistance of AI tools (Gemini, Claude).

## Contact and Support
For issues, bug reports, or feature requests, please visit the [Issues page](https://github.com/PadiCR/SZRPlus/issues).

---
*Created and maintained by Cristobal Padilla (cristobalpadilla@gmail.com)*
