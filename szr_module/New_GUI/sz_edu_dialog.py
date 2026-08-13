# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SZR+
                                 A QGIS plugin
 susceptibility
                              -------------------
        begin                : 2026-04-08
        copyright            : (C) 2026 by Cristobal A. Padilla Moreno
        email                : cristobalpadilla@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

Acknowledgements:
- UI layout designed with Qt Designer in early stages.
- Code logic entirely generated and authored with the assistance of AI (Gemini, Claude).
"""

__author__ = 'Cristobal A. Padilla Moreno'
__email__ = "cristobalpadilla@gmail.com"
__date__ = '2026-04-08'
__copyright__ = '(C) 2026 by Cristobal A. Padilla Moreno'

import os
import tempfile
from osgeo import gdal
gdal.SetConfigOption('GDAL_MEM_ENABLE_OPEN', 'YES')
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QSpinBox, QPushButton, QListWidget, QListWidgetItem,
    QTreeView, QMessageBox, QProgressBar,
    QTabWidget, QAbstractItemView, QCheckBox, QScrollArea, QAbstractScrollArea,
    QFileSystemModel, QSizePolicy, QHeaderView, QFrame,
    QLineEdit, QToolButton, QMenu, QAction, QFileDialog, QApplication
)
from qgis.PyQt.QtCore import (
    Qt, QDir, QMimeData, QUrl, pyqtSignal
)
from qgis.PyQt.QtGui import QPixmap, QColor

from qgis.gui import (
    QgsFileWidget, QgsMapLayerComboBox, QgsFieldComboBox,
    QgsCheckableComboBox, QgsExtentGroupBox, QgsMessageBar,
)
from qgis.core import (
    QgsMapLayerProxyModel, QgsVectorLayer, QgsWkbTypes,
    QgsProject, QgsMessageLog, Qgis, QgsTask, QgsApplication,
)

UI_FILE = os.path.join(os.path.dirname(__file__), 'SZ_edu.ui')
FORM_CLASS, _ = uic.loadUiType(UI_FILE)

LOG_TAG = 'SZR+'

INFO_DICT = {
    'Weight of Evidence (WoE)': "<b>Weight of Evidence (WoE)</b><br><br><b>Description:</b><br>WoE is a data-driven, bivariate statistical method based on Bayes' rule. For each class of a predictive factor it computes a positive weight (W+) and a negative weight (W-) from the presence or absence of landslides: the higher the contrast, the stronger that class's association with instability.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) MUST be classified/categorical.",
    'Frequency Ratio (FR)': "<b>Frequency Ratio (FR)</b><br><br><b>Description:</b><br>FR is a bivariate statistical method that compares the percentage of landslides falling in a parameter class with the percentage of the study area occupied by that class. FR &gt; 1 means the class is more prone to landslides than average; FR &lt; 1 means less prone.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) MUST be classified/categorical.",
    'Logistic Regression (LR)': "<b>Logistic Regression (LR)</b><br><br><b>Description:</b><br>LR is a multivariate statistical method that models the probability of landslide occurrence (a value between 0 and 1) as a function of several predictive variables combined. Its coefficients show how much, and in which direction, each variable contributes to susceptibility.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical.",
    'Random Forest (RF)': "<b>Random Forest (RF)</b><br><br><b>Description:</b><br>RF is an ensemble machine learning method that builds many decision trees, each trained on a random subset of the data and variables, and averages their predictions. Combining many trees reduces the overfitting typical of a single tree and usually gives robust, accurate results.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical.",
    'Support Vector Machine (SVM)': "<b>Support Vector Machine (SVM)</b><br><br><b>Description:</b><br>SVM is a supervised machine learning method that finds the boundary separating landslide from non-landslide conditions with the widest possible margin. Kernel functions allow this boundary to be non-linear, capturing complex relationships between covariates.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical (requires normalization, handled internally).",
    'Decision Trees (DT)': "<b>Decision Trees (DT)</b><br><br><b>Description:</b><br>DT splits the dataset step by step using simple threshold rules on the predictive variables (e.g., slope &gt; 25&deg;), forming a tree of decisions that leads to a susceptibility class. It is very easy to interpret, but a single tree tends to overfit the training data.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical.",
    
    'Binomial Mode Extra': "<br><br><b>Mode: SI Binomial Sampler</b><br>The binomial sampler randomly splits the data into a training and a testing set according to a chosen percentage (e.g., 70% train / 30% test). The model is calibrated on the training set and validated on the testing set, so its performance is measured on data it has never seen.<br><br><b>Outputs:</b><br>- Output Test/Train Raster (aligned to the Raster Base): pixels used for training = 0, for testing = 1, all others NoData.<br>- Additional Output Folder contains: ROC (Receiver Operating Characteristic) and SR (Success Rate) curves (.png), ROC and SR data (.csv), and model-specific files (weights, coefficients, or feature importance). The ROC plot includes validation metrics: AUC (Area Under the Curve), DIS (Distance to the perfect (0,1) classifier), and CSI (Critical Success Index / Threat Score).",
    'KFold Mode Extra': "<br><br><b>Mode: SI K-fold</b><br>K-fold cross-validation randomly divides the data into K equal folds. The model is trained K times, each time leaving one fold out for testing and training on the other K-1, so every observation is used for validation exactly once. This gives a more robust performance estimate than a single train/test split.<br><br><b>Outputs:</b><br>- Output Test/Train Raster: Pixel values range from 1 to K representing the assigned fold for each pixel, and NoData otherwise (for Raster Base).<br>- Additional Output Folder contains K subfolders (e.g., fold_0, fold_1), each containing its respective ROC (Receiver Operating Characteristic) and SR (Success Rate) curves (.png) showing AUC (Area Under the Curve), DIS (Distance to the perfect (0,1) classifier), and CSI (Critical Success Index / Threat Score) metrics, along with ROC and SR data (.csv), and model-specific files.",
    
    'Clean Points By Raster Kernel': "<b>Clean Points By Raster Kernel</b><br><br>Filters an input point layer using a raster constraint: a point is kept only if the raster cells within a kernel (buffer) around it contain accepted, valid values.",
    'Attribute Table Statistics': "<b>Attribute Table Statistics</b><br><br>Calculate descriptive statistics based on an attribute table of a vector layer.",
    'Points Kernel Statistics': "<b>Points Kernel Statistics</b><br><br>Extracts statistics of the raster values found within a kernel (neighbourhood) around each input point, limited to a mask polygon.",
    'Points Kernel Graphs': "<b>Points Kernel Graphs</b><br><br>Generates informative graphs and plots based on the kernel statistics calculated around the input points.",
    'Points Sampler': "<b>Points Sampler</b><br><br>Splits an input point layer into two subsets (e.g., training and testing) according to a chosen percentage, using a spatial grid so the sampling stays spatially balanced.",
    'Points To Grid': "<b>Points To Grid</b><br><br>Rasterizes an input point dataset onto a grid, snapping to a reference raster and specified spatial extent.",
    'Poly To Grid': "<b>Poly To Grid</b><br><br>Rasterizes an input polygon dataset into a raster grid with a user-defined pixel width and height.",
    'Classify Field by .txt File': "<b>Classify Field by .txt File</b><br><br>Classifies (reclassifies) a continuous or categorical vector field using a set of rules defined in a plain text file.",
    'Classify Field in Quantiles': "<b>Classify Field in Quantiles</b><br><br>Classifies a continuous vector field into quantiles (e.g., quartiles, deciles) &mdash; classes containing an equal number of features &mdash; and writes the class IDs to a new field.",
    'Correlation Plot': "<b>Correlation Plot</b><br><br>Generates a correlation matrix plot for a set of continuous independent variables, useful for identifying highly correlated features before running susceptibility models.",
    
    'Classify Vector by ROC': "<b>Classify Vector by ROC</b><br><br>Reclassifies the continuous Susceptibility Index (SI) into discrete classes by selecting cutoff values along the ROC curve that maximize the discrimination between stable and unstable areas.",
    'Classify Vector by Weighted ROC': "<b>Classify Vector by Weighted ROC</b><br><br>Same as Classify by ROC, but each observation contributes to the ROC curve according to a user-defined weight field, giving more influence to selected events or areas.",
    'ROC Generator': "<b>ROC Generator</b><br><br>Calculates and outputs a standalone Receiver Operating Characteristic (ROC) curve plot and Area Under the Curve (AUC) for an existing SI prediction field against a dependent variable. The generated plot includes threshold metrics: DIS (Distance to the perfect (0,1) classifier) and CSI (Critical Success Index / Threat Score).",
    'Confusion Matrix (FP/TN Threshold)': "<b>Confusion Matrix (FP/TN Threshold)</b><br><br>Applies a cutoff percentile to the SI and counts True Positives, False Positives, True Negatives and False Negatives, producing the confusion matrix and derived metrics.",
    # Raster Classify SI tools
    # Raster Classify SI tools
    'Classify by ROC': (
        '<b>Classify by ROC</b><br><br>'
        '<b>Description:</b><br>'
        'Classifies the Susceptibility Index (SI) raster into discrete categories by optimizing class boundaries along the ROC curve results.<br><br>'
        '<b>Formula:</b><br>'
        'Youden Index J = TPR &minus; FPR<br><br>'
        '<b>Reclassification:</b><br>'
        'Uses an optimized Genetic Algorithm to find the N&minus;1 breakpoints that maximize the difference between the True Positive Rate and the False Positive Rate globally along the ROC curve.<br><br>'
        '<b>Focus:</b><br>'
        'Global discrimination and multi-class optimization.<br><br>'
        '<b>Best for:</b><br>'
        'High-precision susceptibility terrain zoning where maximizing discrimination is critical across all classes.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
    'ROC Generator (Raster)': '<b>ROC Generator</b><br>Generates the Receiver Operating Characteristic (ROC) curve directly from the given SI Raster and the Landslide Inventory Raster.<br><br><b>Output:</b><br>- A `.png` image of the ROC plot including Area Under the Curve (AUC), Distance to the perfect (0,1) classifier (DIS), and Critical Success Index (CSI / Threat Score).<br>- A `.csv` file containing False Positive Rates, True Positive Rates, and their respective thresholds.',
    'Confusion Matrix (FP/TN Threshold) (Raster)': '<b>Confusion Matrix (Raster)</b><br>Evaluates the spatial predictive performance of the model using a defined threshold (or the Youden index if 0 is provided). It calculates the confusion matrix (True Positives, True Negatives, False Positives, False Negatives) for the SI Raster against the Landslide Inventory.<br><br><b>Output:</b><br>- A `.csv` file with the performance metrics.',
    # ── New Raster Classify SI methods ───────────────────────────────────────
    'Classify by Closest Point (0,1)': (
        '<b>Classify by Closest Point (0,1)</b><br><br>'
        '<b>Description:</b><br>'
        'This is the geometric "cousin" of Youden\'s Index. It finds the threshold point on the ROC curve that is spatially closest to the "perfect" classifier (top-left corner).<br><br>'
        '<b>Formula:</b><br>'
        'd = &radic;((1 &minus; Sensitivity)&sup2; + FPR&sup2;)<br><br>'
        '<b>Reclassification:</b><br>'
        'The optimal threshold point defines the boundary of the highest susceptibility class. The remaining N&minus;1 classes are distributed using equal intervals below this threshold.<br><br>'
        '<b>Focus:</b><br>'
        'Balanced geometric trade-off in the ROC space.<br><br>'
        '<b>Best for:</b><br>'
        'When you want a mathematically neutral boundary between low and high susceptibility, based on the straight-line distance in ROC space rather than the vertical distance from the diagonal.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
    'Classify by F1-Score': (
        '<b>Classify by F1-Score</b><br><br>'
        '<b>Description:</b><br>'
        'Balances precision (how many pixels predicted as "high susceptibility" were actually landslides) and recall (how many total landslides were caught) to find the most representative class boundary.<br><br>'
        '<b>Formula:</b><br>'
        'F1 = 2&times;TP / (2&times;TP + FP + FN)<br><br>'
        '<b>Reclassification:</b><br>'
        'The threshold that maximizes the F1-score is calculated along the ROC curve and used to designate the boundary for the highest susceptibility class.<br><br>'
        '<b>Focus:</b><br>'
        'Reliable prediction quality and classification accuracy.<br><br>'
        '<b>Best for:</b><br>'
        'Imbalanced datasets (e.g., landslides covering &lt; 5% of the area) as it ensures the high-susceptibility class is trustworthy and not overpredicted.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
    'Classify by Threat Score (CSI)': (
        '<b>Classify by Threat Score (CSI)</b><br><br>'
        '<b>Description:</b><br>'
        'A hazard detection measure that ignores True Negatives. It focuses purely on correctly identifying the presence of the hazard.<br><br>'
        '<b>Formula:</b><br>'
        'CSI = TP / (TP + FP + FN)<br><br>'
        '<b>Reclassification:</b><br>'
        'The threshold that maximizes the Critical Success Index (CSI) determines the boundary of the highest class, with lower classes spaced evenly below.<br><br>'
        '<b>Focus:</b><br>'
        'Hazard detection performance, ignoring stable zones.<br><br>'
        '<b>Best for:</b><br>'
        'When "low susceptibility" areas are secondary and the primary goal is maximizing the detection of future landslide events.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _bold(widget):
    """Make a widget's font bold without touching its colours.

    Colours are left to the active QGIS theme; only the weight is overridden so
    the label still reads correctly under both the light and dark UI themes.
    """
    font = widget.font()
    font.setBold(True)
    widget.setFont(font)
    return widget


def _labeled(label_text, widget):
    """Return a QVBoxLayout with a label above the widget."""
    vbox = QVBoxLayout()
    vbox.addWidget(_bold(QLabel(label_text)))
    vbox.addWidget(widget)
    return vbox


def _accent_button(text, base_color):
    """A coloured action button that stays legible under any QGIS theme.

    The hover/pressed shades are derived from the base colour with QColor so the
    result is always a valid colour (a plain '#rrggbb' + 'cc' suffix is not a
    colour Qt style sheets accept, and silently disables the rule).
    """
    btn = QPushButton(text)
    base = QColor(base_color)
    hover = base.darker(115)
    pressed = base.darker(135)
    btn.setStyleSheet(
        "QPushButton {"
        f" background:{base.name()}; color:#ffffff; font-weight:bold;"
        " padding:8px; border:none; border-radius:4px; }"
        f"QPushButton:hover {{ background:{hover.name()}; }}"
        f"QPushButton:pressed {{ background:{pressed.name()}; }}"
        "QPushButton:disabled { background:palette(button); color:palette(mid); }"
    )
    return btn


def _open_folder(path):
    """Reveal a results folder in the system file manager."""
    from qgis.PyQt.QtGui import QDesktopServices
    if path and os.path.isdir(path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        return True
    return False


def _run_row(run_label, color):
    """A RUN button with an 'open results folder' button beneath it.

    The second button stays disabled until a run has actually produced output;
    the folder it points at is stashed on the button itself.
    """
    run_btn = _accent_button(run_label, color)
    open_btn = QPushButton("Open results folder")
    open_btn.setEnabled(False)
    open_btn.setToolTip("Enabled once a run has produced results.")
    open_btn.clicked.connect(
        lambda: _open_folder(open_btn.property('results_folder')))

    box = QVBoxLayout()
    box.setSpacing(4)
    box.addWidget(run_btn)
    box.addWidget(open_btn)
    return box, run_btn, open_btn


def _scrollable(page):
    """Wrap a page in a scroll area so tall forms stay usable in a docked panel."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setWidget(page)
    return scroll


def _file_widget(title="", filter_="All files (*)"):
    fw = QgsFileWidget()
    fw.setDialogTitle(title)
    fw.setFilter(filter_)
    return fw


def _extent_widget(title="Extent"):
    """A native QGIS extent picker (canvas / layer / draw on canvas / manual)."""
    from qgis.utils import iface
    box = QgsExtentGroupBox()
    box.setTitle(title)
    canvas = iface.mapCanvas() if iface is not None else None
    if canvas is not None:
        box.setMapCanvas(canvas)
        box.setOutputCrs(canvas.mapSettings().destinationCrs())
        box.setCurrentExtent(canvas.extent(),
                             canvas.mapSettings().destinationCrs())
        box.setOutputExtentFromCurrent()
    return box


def _extent_values(box):
    """Return [xmin, xmax, ymin, ymax] for a QgsExtentGroupBox, or None."""
    rect = box.outputExtent()
    if rect is None or rect.isEmpty():
        return None
    return [rect.xMinimum(), rect.xMaximum(), rect.yMinimum(), rect.yMaximum()]


def _colormap(name):
    """Fetch a matplotlib colormap.

    matplotlib.cm.get_cmap() is deprecated since 3.7 and scheduled for removal
    in 3.11, so prefer the modern registry and fall back for older installs.
    """
    import matplotlib
    try:
        return matplotlib.colormaps[name]
    except (AttributeError, KeyError):
        import matplotlib.cm as cm
        return cm.get_cmap(name)


def _finish_raster_style(layer, heading):
    """Anchor a freshly styled raster's symbology, once it is in the project.

    Call this *after* addMapLayer: both steps need the layer's tree node.

    Two things outlive the session here. The style is written as the raster's
    default .qml, so it comes back whenever the file is loaded on its own —
    after a broken temporary source is repaired, when the layer is re-added, or
    when the raster is opened in another project — none of which read the style
    the current project holds. And the legend heading is relabelled: QGIS heads
    a raster's legend with the band's display name, which GDAL assembles from
    the band's colour interpretation. For a single-band GeoTIFF that is always
    'Gray', whatever renderer is in use, so the panel ends up announcing 'Band 1
    (Gray)' above a colour ramp. The replacement lives on the layer-tree node
    and is written into the project file, so it survives reopening.
    """
    _save_default_style(layer)
    _set_legend_heading(layer, heading)


def _save_default_style(layer):
    """Write the layer's style as the raster's default .qml sidecar."""
    try:
        provider = layer.dataProvider()
        if provider is None or provider.name() != 'gdal':
            return                      # only file-backed rasters get a sidecar
        path = layer.source().split('|')[0]
        if not os.path.isfile(path):
            return                      # in-memory or already-gone source
        try:
            from qgis.core import QgsMapLayer
            layer.saveDefaultStyle(QgsMapLayer.AllStyleCategories)
        except TypeError:
            layer.saveDefaultStyle()    # QGIS < 3.26 has no categories overload
    except Exception as e:
        QgsMessageLog.logMessage(f"Could not save the raster's default style: {e}",
                                 LOG_TAG, Qgis.Warning)


def _set_legend_heading(layer, text):
    """Replace the band's display name at the head of the layer's legend."""
    try:
        from qgis.core import QgsMapLayerLegendUtils
        from qgis.utils import iface

        node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if node is None:
            return
        QgsMapLayerLegendUtils.setLegendNodeUserLabel(node, 0, text)
        if iface is not None:
            iface.layerTreeView().layerTreeModel().refreshLayerLegend(node)
    except Exception as e:
        QgsMessageLog.logMessage(f"Could not relabel the raster legend: {e}",
                                 LOG_TAG, Qgis.Warning)


def _style_si_raster(r_lyr):
    """Render an SI raster with an interpolated RdYlGn_r ramp over its value range."""
    try:
        from qgis.core import (QgsRasterShader, QgsColorRampShader,
                               QgsSingleBandPseudoColorRenderer, QgsRasterBandStats)
        provider = r_lyr.dataProvider()

        # Compute min/max explicitly to ensure correct values
        stats = provider.bandStatistics(
            1, QgsRasterBandStats.Min | QgsRasterBandStats.Max, r_lyr.extent(), 0)
        min_v = stats.minimumValue
        max_v = stats.maximumValue

        cmap = _colormap('RdYlGn_r')
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        lst = []
        num_c = 5
        for i in range(num_c):
            val = min_v + (max_v - min_v) * (i / (num_c - 1))
            rgba = cmap(i / (num_c - 1))
            c = QColor(int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255))
            lst.append(QgsColorRampShader.ColorRampItem(val, c, f"{val:.4f}"))

        fnc.setColorRampItemList(lst)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)

        renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
        renderer.setClassificationMin(min_v)
        renderer.setClassificationMax(max_v)

        r_lyr.setRenderer(renderer)
        r_lyr.triggerRepaint()
    except Exception as e:
        QgsMessageLog.logMessage(f"Error styling SI raster: {e}", LOG_TAG, Qgis.Warning)


def _style_si_vector(v_lyr):
    """Render an SI vector layer graduated in 5 equal-interval RdYlGn_r classes."""
    try:
        from qgis.core import (QgsGraduatedSymbolRenderer, QgsRendererRange,
                               QgsClassificationEqualInterval, QgsSymbol)
        fields = [f.name() for f in v_lyr.fields()]
        si_f = next((f for f in ['SI', 'si', 'prediction', 'Prediction',
                                 'SI_test', 'SI_train'] if f in fields), None)
        if not si_f:
            return

        cmap = _colormap('RdYlGn_r')
        method = QgsClassificationEqualInterval()
        classes = method.classes(v_lyr, si_f, 5)
        if not classes:
            return

        # classes() yields QgsClassificationRange, which carries no symbol; the
        # renderer needs QgsRendererRange built from each interval.
        ranges = []
        for i, c in enumerate(classes):
            rgba = cmap(i / max(1, len(classes) - 1))
            color = QColor(int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255))
            sym = QgsSymbol.defaultSymbol(v_lyr.geometryType())
            sym.setColor(color)
            ranges.append(QgsRendererRange(c.lowerBound(), c.upperBound(),
                                           sym, c.label()))

        v_lyr.setRenderer(QgsGraduatedSymbolRenderer(si_f, ranges))
        v_lyr.triggerRepaint()
    except Exception as e:
        QgsMessageLog.logMessage(f"Error styling SI vector: {e}", LOG_TAG, Qgis.Warning)


class SzTask(QgsTask):
    """Runs one SZR+ computation on the QGIS task manager.

    Using QgsTask instead of a bare QThread means every run shows up in the QGIS
    status-bar progress widget and can be cancelled from there, and Qt guarantees
    finished() runs on the main thread so layers can be created safely.
    """

    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, description, func, *args, **kwargs):
        super().__init__(description, QgsTask.CanCancel)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None
        self._message = ''

    def run(self):
        try:
            self._result = self._func(*self._args, **self._kwargs)
            return True
        except Exception as e:
            import traceback
            self._message = str(e)
            # The full traceback belongs in the QGIS log panel, not in a dialog.
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Critical)
            return False

    def finished(self, result):
        """Always called on the main thread once run() returns."""
        if self.isCanceled():
            return
        if result:
            self.completed.emit(self._result)
        else:
            self.failed.emit(self._message or 'Unknown error')


def load_as_memory_layer(filepath, layername_in_file, display_name):
    """Load a vector layer from file (e.g. gpkg, shp) and copy all fields/features into a RAM memory layer."""
    from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsFeature, QgsField
    import os
    if not os.path.exists(filepath):
        return None
    # Load the temporary file layer
    file_layer = QgsVectorLayer(f"{filepath}|layername={layername_in_file}" if filepath.endswith(".gpkg") else filepath, "temp_file_lyr", "ogr")
    if not file_layer.isValid():
        # Maybe it's not a gpkg layer or didn't require layername
        file_layer = QgsVectorLayer(filepath, "temp_file_lyr", "ogr")
        if not file_layer.isValid():
            return None
        
    # Get crs and geometry type
    crs_str = file_layer.crs().authid()
    geom_type = QgsWkbTypes.displayString(file_layer.wkbType())
    
    # Create memory layer
    uri = f"{geom_type}?crs={crs_str}"
    mem_layer = QgsVectorLayer(uri, display_name, "memory")
    provider = mem_layer.dataProvider()
    
    # Add fields
    provider.addAttributes(file_layer.fields())
    mem_layer.updateFields()
    
    # Add features
    features = []
    for feat in file_layer.getFeatures():
        features.append(QgsFeature(feat))
    provider.addFeatures(features)
    mem_layer.updateExtents()
    
    return mem_layer


def csv_to_memory_layer(csv_path, display_name):
    """Load a CSV file, parse header/rows, and create an in-memory geometryless scratch table layer."""
    import csv
    import os
    from qgis.core import QgsVectorLayer, QgsField, QgsFeature
    from qgis.PyQt.QtCore import QVariant
    import pandas as pd
    import numpy as np
    
    if not os.path.exists(csv_path):
        return None
        
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return None
            rows = list(reader)
    except Exception:
        return None
        
    # Create memory layer with no geometry
    uri = "None"
    layer = QgsVectorLayer(uri, display_name, "memory")
    provider = layer.dataProvider()
    
    # Add fields
    fields = []
    for col in header:
        # Check if column values look numeric
        is_num = True
        for row in rows[:10]:
            if len(row) > header.index(col):
                val = row[header.index(col)].strip()
                if not val:
                    continue
                try:
                    float(val)
                except ValueError:
                    is_num = False
                    break
        if is_num:
            fields.append(QgsField(col, QVariant.Double))
        else:
            fields.append(QgsField(col, QVariant.String))
            
    provider.addAttributes(fields)
    layer.updateFields()
    
    # Add features
    features = []
    for row in rows:
        fet = QgsFeature(layer.fields())
        attrs = []
        for col_idx, col in enumerate(header):
            if col_idx < len(row):
                val = row[col_idx].strip()
                if val == "":
                    attrs.append(None)
                else:
                    try:
                        attrs.append(float(val))
                    except ValueError:
                        attrs.append(val)
            else:
                attrs.append(None)
        fet.setAttributes(attrs)
        features.append(fet)
        
    provider.addFeatures(features)
    return layer


class ChartsDialog(QDialog):
    def __init__(self, folder, algo_name, is_temp, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.algo_name = algo_name
        self.is_temp = is_temp
        self.saved_charts = set()
        self.pngs = []
        
        self.setWindowTitle(f"Results Charts - {algo_name}")
        self.resize(850, 700)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for charts
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Find all pngs in folder
        import glob
        self.png_paths = sorted(glob.glob(os.path.join(folder, "*.png")))
        
        # Friendly name mapping
        friendly_names = {
            "fig_simple.png": "ROC Curve",
            "fig_fit.png": "ROC Curve (Fit)",
            "fig_cv.png": "K-Fold ROC Curve",
            "test_fig_success_rate.png": "Success Rate (Test)",
            "train_fig_success_rate.png": "Success Rate (Train)",
            "fit_fig_success_rate.png": "Success Rate (Fit)",
            "fig_success_rate.png": "Success Rate Curve"
        }
        
        for p in self.png_paths:
            base = os.path.basename(p)
            # Support prepended tag (e.g. RF_fig_roc_cv.png)
            stripped_base = base
            for tag in ["WoE_", "FR_", "LR_", "RF_", "SVM_", "DT_", "ROC_Gen_"]:
                if stripped_base.startswith(tag):
                    stripped_base = stripped_base[len(tag):]
                    break
            
            title = friendly_names.get(stripped_base, base)
            
            # Create a scroll area for the image
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            
            lbl = QLabel()
            pix = QPixmap(p)
            lbl.setPixmap(pix)
            lbl.setAlignment(Qt.AlignCenter)
            scroll.setWidget(lbl)
            
            self.tabs.addTab(scroll, title)
            self.pngs.append((p, title))
            
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("Save Current Chart...")
        self.btn_save.clicked.connect(self.save_current)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
    def save_current(self):
        idx = self.tabs.currentIndex()
        if idx < 0 or idx >= len(self.pngs):
            return
        p, title = self.pngs[idx]
        
        default_name = os.path.basename(p)
        dest, _ = QFileDialog.getSaveFileName(self, f"Save {title}", default_name, "PNG Image (*.png)")
        if dest:
            import shutil
            try:
                shutil.copy(p, dest)
                self.saved_charts.add(p)
                QMessageBox.information(self, "Success", f"Chart saved to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save chart: {e}")
                
    def closeEvent(self, event):
        # Check if there are unsaved charts and if the folder is temporary
        if self.is_temp and len(self.saved_charts) < len(self.png_paths):
            # Check if the panel has "don't ask again" set for this session
            panel = self.parent()
            if getattr(panel, '_dont_ask_save_png', False):
                super().closeEvent(event)
                return

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setText("The charts will be lost if you close this window without saving. Do you want to save them?")
            msg.setWindowTitle("Unsaved Charts")

            save_btn = msg.addButton("Save Active Chart...", QMessageBox.AcceptRole)
            msg.addButton("Don't Save", QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton(QMessageBox.Cancel)

            cb = QCheckBox("Do not ask me again during this session")
            msg.setCheckBox(cb)

            msg.exec_()
            clicked = msg.clickedButton()

            if cb.isChecked() and panel is not None:
                panel._dont_ask_save_png = True

            if clicked == save_btn:
                event.ignore()
                self.save_current()
                return
            if clicked == cancel_btn:
                event.ignore()
                return

        super().closeEvent(event)


class ProcessingOutputWidget(QWidget):
    fileChanged = pyqtSignal(str)

    def __init__(self, title, is_folder=False, filter="All files (*)", default_text=None, is_optional=False, force_physical=False):
        super().__init__()
        self.is_folder = is_folder
        self.title = title
        self.filter = filter
        self.is_optional = is_optional
        self.force_physical = force_physical
        self.is_temp = not is_optional and not force_physical
        self._filepath = ""
        self.default_text = default_text
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        # The "no path chosen yet" hint is a placeholder rather than real text, so
        # Qt greys it out using the active theme's palette instead of a hardcoded
        # colour that only looks right on a light background.
        self.line_edit.setPlaceholderText(
            "[Optional]" if self.is_optional else self._hint_text())
        layout.addWidget(self.line_edit)
        
        self.tool_btn = QToolButton()
        self.tool_btn.setText("...")
        self.tool_btn.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(self.tool_btn)
        
        self.menu = QMenu(self)
        self.action_temp = QAction("Save to a Temporary File", self) if not is_folder else QAction("Save to a Temporary Folder", self)
        self.action_save = QAction("Save to File...", self) if not is_folder else QAction("Save to Directory...", self)
        
        if not self.force_physical:
            self.menu.addAction(self.action_temp)
        self.menu.addAction(self.action_save)
        
        if self.is_optional:
            self.action_optional = QAction("Optional (No Output)", self)
            self.menu.addAction(self.action_optional)
            self.action_optional.triggered.connect(self.set_optional)
            
        self.tool_btn.setMenu(self.menu)
        
        self.action_temp.triggered.connect(self.set_temporary)
        self.action_save.triggered.connect(self.prompt_save)
        
    def _hint_text(self):
        """Placeholder describing what happens when no explicit path is set."""
        if self.force_physical:
            return "[Specify output folder…]" if self.is_folder else "[Specify output file…]"
        if self.default_text:
            return self.default_text
        return "[Save to temporary folder]" if self.is_folder else "[Save to temporary file]"

    def set_temporary(self):
        self.is_temp = not self.force_physical
        self._filepath = ""
        self.line_edit.clear()
        self.line_edit.setPlaceholderText(self._hint_text())
        self.fileChanged.emit("")

    def set_optional(self):
        self.is_temp = False
        self._filepath = ""
        self.line_edit.clear()
        self.line_edit.setPlaceholderText("[Optional]")
        self.fileChanged.emit("")

    def prompt_save(self):
        from qgis.PyQt.QtWidgets import QFileDialog
        if self.is_folder:
            path = QFileDialog.getExistingDirectory(self, self.title)
        else:
            path, _ = QFileDialog.getSaveFileName(self, self.title, "", self.filter)
            
        if path:
            self.setFilePath(path)
            
    def filePath(self):
        return self._filepath
        
    def setFilePath(self, path):
        if path:
            self.is_temp = False
            self._filepath = path
            self.line_edit.setText(path)
            self.line_edit.setToolTip(path)
            self.fileChanged.emit(path)
        else:
            if self.is_optional:
                self.set_optional()
            else:
                self.set_temporary()
 
 
def _folder_widget(title="Output folder", default_text=None, force_physical=False):
    return ProcessingOutputWidget(title, is_folder=True, default_text=default_text, force_physical=force_physical)
 
 
def _file_widget_temp(title="", filter_="All files (*)", is_optional=False, force_physical=False):
    w = ProcessingOutputWidget(title, is_folder=False, filter=filter_, is_optional=is_optional, force_physical=force_physical)
    class DummyCheck:
        def __init__(self, w): self.w = w
        def isChecked(self): return self.w.is_temp
    return w, {'fw': w, 'chk': DummyCheck(w)}



# ─────────────────────────────────────────────────────────────────────────────
# Drag-and-drop QListWidget (accept drops from QTreeView)
# ─────────────────────────────────────────────────────────────────────────────

class DropListWidget(QListWidget):
    """QListWidget that accepts file paths dropped from a QTreeView."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def _add_path(self, path):
        if path not in self._paths():
            import os
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            self.addItem(item)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.tif', '.tiff')):
                    self._add_path(path)
            event.acceptProposedAction()
        elif mime.hasText():
            path = mime.text()
            if path.lower().endswith(('.tif', '.tiff')):
                self._add_path(path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _paths(self):
        paths = []
        for i in range(self.count()):
            data = self.item(i).data(Qt.UserRole)
            if data:
                paths.append(str(data))
        return paths


class FileDragTreeView(QTreeView):
    """QTreeView backed by QFileSystemModel that allows dragging .tif files."""
    def __init__(self, parent=None):
        super().__init__(parent)
        model = QFileSystemModel()
        home_path = QgsProject.instance().homePath() or QDir.homePath()
        model.setRootPath(home_path)
        model.setNameFilters(["*.tif", "*.tiff"])
        model.setNameFilterDisables(False)
        self.setModel(model)
        self.setRootIndex(model.index(home_path))
        # Hide unnecessary columns (size, type, date)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._model = model

    def mimeData(self, indexes):
        """Override to expose the full file path as URL + text."""
        mime = QMimeData()
        paths = []
        for idx in indexes:
            path = self._model.filePath(idx)
            if os.path.isfile(path):
                paths.append(path)
        if paths:
            mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
            mime.setText(paths[0])
        return mime


# ─────────────────────────────────────────────────────────────────────────────
# Raster covariate selector widget (dropdown + browse + list)
# ─────────────────────────────────────────────────────────────────────────────

def _make_covariate_selector():
    """
    Returns (outer_widget, drop_list, combo_layer) where outer_widget is a QSplitter
    with the layer selector on the left and the selected-rasters list on the right.
    """
    from qgis.gui import QgsMapLayerComboBox
    from qgis.core import QgsMapLayerProxyModel
    from qgis.PyQt.QtWidgets import QFileDialog

    splitter = QSplitter(Qt.Horizontal)

    # Left: Layer Selection
    left = QWidget()
    lv = QVBoxLayout(left)
    lv.setContentsMargins(0, 0, 0, 0)
    lv.addWidget(_bold(QLabel("Add Independent Variable Raster")))

    layer_combo = QgsMapLayerComboBox()
    layer_combo.setFilters(QgsMapLayerProxyModel.RasterLayer)
    lv.addWidget(layer_combo)

    btn_add = QPushButton("Add Selected Layer")
    lv.addWidget(btn_add)

    btn_browse = QPushButton("Browse Multiple Files…")
    lv.addWidget(btn_browse)

    lv.addStretch()
    splitter.addWidget(left)

    # Right: selected rasters
    right = QWidget()
    rv = QVBoxLayout(right)
    rv.setContentsMargins(0, 0, 0, 0)
    rv.addWidget(_bold(QLabel("Selected Rasters")))
    drop_list = DropListWidget()
    rv.addWidget(drop_list)
    # Remove button
    btn_remove = QPushButton("Remove selected")

    def _remove_selected():
        for item in drop_list.selectedItems():
            drop_list.takeItem(drop_list.row(item))
    btn_remove.clicked.connect(_remove_selected)
    rv.addWidget(btn_remove)
    splitter.addWidget(right)

    # Add button logic
    def _add_layer():
        layer = layer_combo.currentLayer()
        if layer:
            drop_list._add_path(layer.source())
    btn_add.clicked.connect(_add_layer)
    
    # Browse logic
    def _browse_files():
        files, _ = QFileDialog.getOpenFileNames(
            left, "Select Raster Covariates", "", "GeoTIFF (*.tif *.tiff)"
        )
        for f in files:
            from qgis.core import QgsRasterLayer, QgsProject
            lyr = QgsRasterLayer(f, os.path.basename(f))
            if lyr.isValid():
                QgsProject.instance().addMapLayer(lyr)
            drop_list._add_path(f)
    btn_browse.clicked.connect(_browse_files)

    splitter.setSizes([300, 400])
    return splitter, drop_list, layer_combo


# ─────────────────────────────────────────────────────────────────────────────
# Build a raster algorithm page  (2 sub-tabs: Binomial / k-fold)
# ─────────────────────────────────────────────────────────────────────────────

def _make_raster_page(algo_name: str):
    """
    Returns (page_widget, refs) where refs is a dict of widget references for
    both sub-tabs, used by the dialog to read values and trigger runs.
    """
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)

    # The selected method is already named by the list on the left and by the
    # info panel, so the page itself carries no redundant heading.
    sub_tabs = QTabWidget()
    page_layout.addWidget(sub_tabs)

    refs = {}

    for mode in ("binomial", "kfold"):
        sub_page = QWidget()
        sp_layout = QVBoxLayout(sub_page)

        # Landslide raster (now a combo box)
        sp_layout.addWidget(_bold(QLabel("Landslide Raster Inventory")))

        inv_layout = QHBoxLayout()
        inv_combo = QgsMapLayerComboBox()
        inv_combo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        inv_layout.addWidget(inv_combo)

        btn_inv_browse = QPushButton("Browse…")
        def _browse_inv(*args, c=inv_combo):
            from qgis.PyQt.QtWidgets import QFileDialog
            f, _ = QFileDialog.getOpenFileName(sub_page, "Select Landslide Raster Inventory", "", "GeoTIFF (*.tif *.tiff)")
            if f:
                from qgis.core import QgsRasterLayer, QgsProject
                lyr = QgsRasterLayer(f, os.path.basename(f))
                if lyr.isValid():
                    QgsProject.instance().addMapLayer(lyr)
                c.setLayer(lyr)
        btn_inv_browse.clicked.connect(_browse_inv)
        inv_layout.addWidget(btn_inv_browse)
        
        sp_layout.addLayout(inv_layout)

        # Covariate selector
        cov_splitter, drop_list, _ = _make_covariate_selector()
        sp_layout.addWidget(_bold(QLabel("Independent Variables rasters")))
        sp_layout.addWidget(cov_splitter)

        # SpinBox label
        if mode == "binomial":
            spin_lbl = "Percentage of test sample  (0 = fit only, >0 = train/test)"
        else:
            spin_lbl = "Number of k-folds  (≥ 2)"
        spin = QSpinBox()
        spin.setRange(0, 99) if mode == "binomial" else spin.setRange(2, 50)
        spin.setValue(30) if mode == "binomial" else spin.setValue(5)
        sp_layout.addLayout(_labeled(spin_lbl, spin))

        # Output SI raster
        out_raster_widget, out_raster_refs = _file_widget_temp("Output Susceptibility Index (SI) Raster", "GeoTIFF (*.tif *.tiff)", force_physical=True)
        sp_layout.addLayout(_labeled("Output Susceptibility Index (SI) Raster", out_raster_widget))

        out_test_widget, out_test_refs = _file_widget_temp("Output Test/Train Raster", "GeoTIFF (*.tif *.tiff)", is_optional=True, force_physical=True)
        sp_layout.addLayout(_labeled("Output Test/Train Raster (optional)", out_test_widget))

        # Output folder
        if mode == "kfold":
            if 'WoE' in algo_name or 'FR' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR + Weights for each k-fold)"
            elif 'LR' in algo_name or 'SVM' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR + Coefficients for each k-fold)"
            elif 'RF' in algo_name or 'DT' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR + Feature Importance for each k-fold)"
            else:
                folder_lbl = "Additional outputs folder (ROC, SR + etc for each k-fold)"
        else:
            if 'WoE' in algo_name or 'FR' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR, Weights)"
            elif 'LR' in algo_name or 'SVM' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR, Coefficients)"
            elif 'RF' in algo_name or 'DT' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR, Feature Importance)"
            else:
                folder_lbl = "Additional outputs folder (ROC, SR, etc)"
            
        out_folder = _folder_widget(folder_lbl, force_physical=True)
        sp_layout.addLayout(_labeled(folder_lbl, out_folder))
        
        # Auto-fill output folder if empty
        out_raster_refs['fw'].fileChanged.connect(lambda path, f=out_folder: f.setFilePath(os.path.dirname(path)) if path and not f.filePath() else None)

        # RUN button (+ open results folder)
        run_box, run_btn, open_btn = _run_row(f"RUN  —  {algo_name}", "#2d7dd2")
        sp_layout.addLayout(run_box)
        sp_layout.addStretch()

        refs[mode] = {
            'inventory': inv_combo,
            'covariates': drop_list,
            'spin': spin,
            'output': out_raster_refs,
            'out_test': out_test_refs,
            'folder': out_folder,
            'run_btn': run_btn,
            'open_btn': open_btn,
        }

        tab_title = "SI Binomial Sampler" if mode == "binomial" else "SI k-fold"
        sub_tabs.addTab(_scrollable(sub_page), tab_title)

    refs['sub_tabs'] = sub_tabs
    return page, refs


# ─────────────────────────────────────────────────────────────────────────────
# Build a vector algorithm page  (2 sub-tabs: Binomial / k-fold)
# ─────────────────────────────────────────────────────────────────────────────

def _make_vector_page(algo_name: str):
    """
    Returns (page_widget, refs).  refs[mode]['layer_combo'] is the slope-unit combo,
    refs[mode]['dep_combo'] the dependent-variable field and refs[mode]['indep_combo']
    the checkable list of covariate fields.
    """
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)

    sub_tabs = QTabWidget()
    page_layout.addWidget(sub_tabs)

    refs = {}

    for mode in ("binomial", "kfold"):
        sub_page = QWidget()
        sp_layout = QVBoxLayout(sub_page)

        # Slope unit vector layer selector
        layer_combo = QgsMapLayerComboBox()
        layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        layer_combo.setAllowEmptyLayer(True)
        sp_layout.addLayout(_labeled("Slope Unit Vector Layer  (input layer)", layer_combo))

        # ── Dependent Variable (Combo Box) ────────────────────────────────────
        dep_combo = QgsFieldComboBox()
        sp_layout.addLayout(_labeled("Dependent Variable Field (0 for absence, >0 for presence)", dep_combo))

        # ── Independent variables ─────────────────────────────────────────────
        # QgsCheckableComboBox is the native QGIS control for picking several
        # fields at once; it replaces the old checklist + read-only mirror panel
        # and shows the current selection in its own line.
        indep_combo = QgsCheckableComboBox()
        indep_combo.setToolTip("Fields to use as covariates")
        indep_combo.setDefaultText("Select the covariate fields…")
        sp_layout.addLayout(_labeled("Independent Variable Fields", indep_combo))

        # SpinBox
        if mode == "binomial":
            spin_lbl = "Percentage of test sample  (0 = fit only)"
        else:
            spin_lbl = "Number of k-folds  (1 = fit only, >1 = cross-validate)"
        spin = QSpinBox()
        spin.setRange(0, 99) if mode == "binomial" else spin.setRange(1, 50)
        spin.setValue(30) if mode == "binomial" else spin.setValue(5)
        sp_layout.addLayout(_labeled(spin_lbl, spin))

        # Output vector
        if mode == "binomial":
            out_vec_test_widget, out_vec_test_refs = _file_widget_temp("Output Test GeoPackage", "GeoPackage (*.gpkg)", is_optional=True)
            sp_layout.addLayout(_labeled("Output Test GeoPackage", out_vec_test_widget))

            out_vec_train_widget, out_vec_train_refs = _file_widget_temp("Output Train/Fit GeoPackage", "GeoPackage (*.gpkg)", is_optional=True)
            sp_layout.addLayout(_labeled("Output Train/Fit GeoPackage", out_vec_train_widget))
        else:
            # kfold mode
            out_vec_test_widget, out_vec_test_refs = _file_widget_temp("Output test/fit", "GeoPackage (*.gpkg)", is_optional=True)
            sp_layout.addLayout(_labeled("Output test/fit", out_vec_test_widget))
            out_vec_train_widget = None
            out_vec_train_refs = None

        if mode == "kfold":
            if 'WoE' in algo_name or 'FR' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR + Weights for each k-fold)"
            elif 'LR' in algo_name or 'SVM' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR + Coefficients for each k-fold)"
            elif 'RF' in algo_name or 'DT' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR + Feature Importance for each k-fold)"
            else:
                folder_lbl = "Additional outputs folder (ROC, SR + etc for each k-fold)"
        else:
            if 'WoE' in algo_name or 'FR' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR, Weights)"
            elif 'LR' in algo_name or 'SVM' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR, Coefficients)"
            elif 'RF' in algo_name or 'DT' in algo_name:
                folder_lbl = "Additional outputs folder (ROC, SR, Feature Importance)"
            else:
                folder_lbl = "Additional outputs folder (ROC, SR, etc)"
            
        out_folder = _folder_widget(folder_lbl, default_text="[only ROC will be saved as temporary file]" if mode == "kfold" else None)
        sp_layout.addLayout(_labeled(folder_lbl, out_folder))
        
        # Link outputs to folder autocomplete
        def auto_populate_folder():
            if out_folder.filePath():
                return
            if mode == "binomial":
                pct = spin.value()
                if pct > 0:
                    test_path = out_vec_test_refs['fw'].filePath()
                    if test_path:
                        out_folder.setFilePath(os.path.dirname(test_path))
                else:
                    train_path = out_vec_train_refs['fw'].filePath()
                    if train_path:
                        out_folder.setFilePath(os.path.dirname(train_path))
            else:
                test_path = out_vec_test_refs['fw'].filePath()
                if test_path:
                    out_folder.setFilePath(os.path.dirname(test_path))

        out_vec_test_refs['fw'].fileChanged.connect(lambda path: auto_populate_folder() if path else None)
        if out_vec_train_refs is not None:
            out_vec_train_refs['fw'].fileChanged.connect(lambda path: auto_populate_folder() if path else None)
        spin.valueChanged.connect(lambda val: auto_populate_folder())

        run_box, run_btn, open_btn = _run_row(f"RUN  —  {algo_name}", "#27ae60")
        sp_layout.addLayout(run_box)
        sp_layout.addStretch()

        refs[mode] = {
            'layer_combo': layer_combo,
            'dep_combo': dep_combo,
            'indep_combo': indep_combo,
            'spin': spin,
            'out_test': out_vec_test_refs,
            'out_train': out_vec_train_refs,
            'folder': out_folder,
            'run_btn': run_btn,
            'open_btn': open_btn,
        }

        tab_title = "SI Binomial Sampler" if mode == "binomial" else "SI k-fold"
        sub_tabs.addTab(_scrollable(sub_page), tab_title)

    refs['sub_tabs'] = sub_tabs
    return page, refs


# ─────────────────────────────────────────────────────────────────────────────
# Simple parameter-form pages (Data Preparation / Classify SI)
# ─────────────────────────────────────────────────────────────────────────────

def _simple_page(title: str, params: list, run_label: str, btn_color: str = "#8e44ad"):
    """
    params = list of ('label', widget) tuples.
    Returns (scrollable page, {key: widget, 'run_btn': QPushButton}).
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    refs = {}
    for row in params:
        label_text = row[0]
        if len(row) == 3:
            # Contains refs dictionary and widget explicitly defined
            refs[label_text] = row[1]
            widget = row[2]
        else:
            refs[label_text] = row[1]
            widget = row[1]
        if isinstance(widget, QgsExtentGroupBox):
            # Already a titled group box — a separate caption would just repeat it.
            layout.addWidget(widget)
        else:
            layout.addLayout(_labeled(label_text, widget))

    run_box, run_btn, open_btn = _run_row(run_label, btn_color)
    layout.addLayout(run_box)
    layout.addStretch()
    refs['run_btn'] = run_btn
    refs['open_btn'] = open_btn
    return _scrollable(page), refs


# ─────────────────────────────────────────────────────────────────────────────
# Main Dialog
# ─────────────────────────────────────────────────────────────────────────────

class SzEduPanel(QWidget, FORM_CLASS):
    """The SZR+ panel. Hosted inside a QDialog by the plugin entry point."""

    ALGO_KEYS_R = ['woe', 'fr', 'lr', 'rf', 'svm', 'dt']
    ALGO_NAMES  = [
        'Weight of Evidence (WoE)',
        'Frequency Ratio (FR)',
        'Logistic Regression (LR)',
        'Random Forest (RF)',
        'Support Vector Machine (SVM)',
        'Decision Trees (DT)',
    ]

    # Where each list's pages start inside its QStackedWidget.
    DP_PAGE_OFFSET   = 6    # Data Preparation, in stackedWidget_v
    CL_V_PAGE_OFFSET = 16   # Classify SI (vector), in stackedWidget_v
    CL_R_PAGE_OFFSET = 6    # Classify SI (raster), in stackedWidget_r

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.lbl_cl_r_title.setText("Classify SI Raster")

        self._is_running = False
        self._task = None
        self._mem_datasets = {}
        self._child_dialogs = []
        self._dont_ask_save_png = False

        # Storage for widget references
        self._raster_refs = {}   # key: algo key str -> {'binomial':…, 'kfold':…}
        self._vector_refs = {}   # key: algo key str
        self._dp_refs     = {}   # key: function label
        self._cl_refs     = {}   # key: function label
        self._cl_r_refs   = {}   # key: function label

        # Pages are built the first time they are shown. Constructing all 26 of
        # them up front instantiated dozens of layer/field combos — each one a
        # live listener on the project — for pages the user may never open.
        self._lazy_r = {}   # stacked index -> builder callable
        self._lazy_v = {}

        # Register first: it rewrites classify_list_r, whose (longer) entries
        # must be present before the lists are measured and sized.
        self._register_page_builders()
        self._init_lists()
        self._init_navigation()
        self._init_status_area()
        self._init_info_panel()

        # Default selections (this builds only the two visible pages)
        self.SIfunct_r.setCurrentRow(0)
        self.SIfunct_v.setCurrentRow(0)
        self.dataprep_list.setCurrentRow(-1)
        self.classify_list.setCurrentRow(-1)
        self.classify_list_r.setCurrentRow(-1)

        # As a child widget rather than a window of its own, the panel gets no
        # closeEvent when QGIS exits, so the teardown guard is hooked to the
        # application shutdown instead. PyQt drops the connection automatically
        # if this panel is destroyed first.
        app = QgsApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._mute_layer_widgets)

        self._update_info()

    # ── Construction helpers ─────────────────────────────────────────────────

    def _init_lists(self):
        """Apply the per-method icons, then size the navigation lists to fit."""
        from qgis.PyQt.QtGui import QIcon
        from qgis.PyQt.QtWidgets import QStyle

        lists_to_adjust = (self.SIfunct_r, self.SIfunct_v, self.dataprep_list,
                           self.classify_list, self.classify_list_r)

        # Icons first: they widen their rows, and sizeHintForColumn() has to see
        # them. (Measuring before they were set is why the old code needed a
        # blanket +80 px, which left a wide empty gutter beside every label.)
        icon_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
        for idx, key in enumerate(self.ALGO_KEYS_R):
            icon_path = os.path.join(icon_dir, f"{key}_icon.png")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                for lw in (self.SIfunct_r, self.SIfunct_v):
                    item = lw.item(idx)
                    if item:
                        item.setIcon(icon)

        # Room for the frame plus a scrollbar, so the widest label is never
        # clipped once a list starts scrolling.
        style = self.style()
        scrollbar = style.pixelMetric(QStyle.PM_ScrollBarExtent)

        max_width = 0
        for lw in lists_to_adjust:
            lw.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            width = lw.sizeHintForColumn(0) + 2 * lw.frameWidth() + scrollbar + 4
            max_width = max(max_width, width)

        for lw in lists_to_adjust:
            # One shared width keeps the stacked lists aligned in their column.
            lw.setFixedWidth(max_width)
            lw.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)

            if lw in (self.SIfunct_r, self.SIfunct_v):
                lw.setMinimumHeight(170)
            elif lw == self.dataprep_list:
                lw.setMinimumHeight(240)
                lw.setMaximumHeight(260)
            elif lw == self.classify_list:
                lw.setMinimumHeight(100)
                lw.setMaximumHeight(150)
            elif lw == self.classify_list_r:
                lw.setMaximumHeight(150)

    def _ensure_page(self, stack, lazy, index):
        """Build the page at `index` if it has not been constructed yet."""
        builder = lazy.pop(index, None)
        if builder is None:
            return
        page = builder()
        placeholder = stack.widget(index)
        if placeholder is not None:
            stack.removeWidget(placeholder)
            placeholder.deleteLater()
        stack.insertWidget(index, page)

    def _init_navigation(self):
        """Wire each navigation list to its stacked widget, building on demand."""

        def _select(stack, lazy, index, others):
            self._ensure_page(stack, lazy, index)
            stack.setCurrentIndex(index)
            for lw in others:
                lw.clearSelection()
                lw.setCurrentRow(-1)

        def set_r_page(idx):
            if idx >= 0:
                _select(self.stackedWidget_r, self._lazy_r, idx,
                        (self.classify_list_r,))

        def set_cl_r_page(idx):
            if idx >= 0:
                _select(self.stackedWidget_r, self._lazy_r,
                        self.CL_R_PAGE_OFFSET + idx, (self.SIfunct_r,))

        def set_v_page(idx):
            if idx >= 0:
                _select(self.stackedWidget_v, self._lazy_v, idx,
                        (self.dataprep_list, self.classify_list))

        def set_dp_page(idx):
            if idx >= 0:
                _select(self.stackedWidget_v, self._lazy_v,
                        self.DP_PAGE_OFFSET + idx,
                        (self.SIfunct_v, self.classify_list))

        def set_cl_page(idx):
            if idx >= 0:
                _select(self.stackedWidget_v, self._lazy_v,
                        self.CL_V_PAGE_OFFSET + idx,
                        (self.SIfunct_v, self.dataprep_list))

        self.SIfunct_r.currentRowChanged.connect(set_r_page)
        self.classify_list_r.currentRowChanged.connect(set_cl_r_page)
        self.SIfunct_v.currentRowChanged.connect(set_v_page)
        self.dataprep_list.currentRowChanged.connect(set_dp_page)
        self.classify_list.currentRowChanged.connect(set_cl_page)

    def _init_status_area(self):
        """Message bar, status label, progress bar and the Cancel button."""
        # An in-panel QgsMessageBar is what QGIS' own Processing dialogs use for
        # validation and result feedback; it keeps the panel usable while it
        # reports, unlike the chain of modal dialogs this replaces.
        self.message_bar = QgsMessageBar()
        self.message_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.mainLayout.insertWidget(0, self.message_bar)

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setToolTip("Stop waiting on the current run and unlock the panel.")
        self.btn_cancel.setVisible(False)   # Only shown while a task is running
        self.btn_cancel.clicked.connect(self._cancel_run)

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.btn_cancel)
        self.mainLayout.addLayout(status_layout)

    def _init_info_panel(self):
        """The method description pane, styled from the active theme's palette."""
        from qgis.PyQt.QtWidgets import QTextEdit

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumWidth(280)
        # Only size and padding are overridden — 13px matches the comfortable
        # reading size v1.9 used. Colours, font family and scrollbars are left to
        # QGIS so the panel follows the light and dark UI themes (the previous
        # hardcoded near-white background and 'Segoe UI' family did neither).
        self.info_text.setStyleSheet("QTextEdit { padding: 8px; font-size: 13px; }")
        self.info_text.document().setDefaultStyleSheet(
            "b { font-weight: 600; }")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.mainTabWidget)
        splitter.addWidget(self.info_text)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        self.mainLayout.insertWidget(1, splitter)

        self.mainTabWidget.currentChanged.connect(self._update_info)
        self.SIfunct_r.currentRowChanged.connect(self._update_info)
        self.classify_list_r.currentRowChanged.connect(self._update_info)
        self.SIfunct_v.currentRowChanged.connect(self._update_info)
        self.dataprep_list.currentRowChanged.connect(self._update_info)
        self.classify_list.currentRowChanged.connect(self._update_info)

    # ── Feedback helpers ─────────────────────────────────────────────────────

    def _info(self, text, title='SZR+'):
        self.message_bar.pushMessage(title, text, Qgis.Success, 8)

    def _warn(self, text, title='Missing input'):
        self.message_bar.pushMessage(title, text, Qgis.Warning, 8)

    def _error(self, text, title='Error'):
        # No timeout: an error stays until the user dismisses it. The traceback
        # goes to the QGIS log panel rather than into a modal dialog.
        self.message_bar.pushMessage(title, text, Qgis.Critical)

    def _log(self, text, level=Qgis.Info):
        QgsMessageLog.logMessage(text, LOG_TAG, level)

    def _set_results_folder(self, refs, folder):
        """Point a page's 'Open results folder' button at the run's output."""
        btn = refs.get('open_btn') if isinstance(refs, dict) else refs
        if btn is None or not folder:
            return
        folder = folder if os.path.isdir(folder) else os.path.dirname(folder)
        if not folder or not os.path.isdir(folder):
            return
        btn.setProperty('results_folder', folder)
        btn.setEnabled(True)
        btn.setToolTip(folder)

    def _show_charts(self, folder, algo_name, is_temp):
        """Open the results charts without blocking the panel or the canvas."""
        import glob
        from qgis.PyQt import sip
        if not glob.glob(os.path.join(folder, "*.png")):
            return
        # Drop references to windows the user has already closed.
        self._child_dialogs = [d for d in self._child_dialogs
                               if not sip.isdeleted(d) and d.isVisible()]
        dlg = ChartsDialog(folder, algo_name, is_temp=is_temp, parent=self)
        self._child_dialogs.append(dlg)
        dlg.show()
        dlg.raise_()

    def _mute_layer_widgets(self):
        """Defense-in-depth against the QGIS-shutdown access violation.

        Mutes every layer/field combo so that the layer removal happening during
        teardown can't fire a slot against a widget whose C++ side is already
        gone. (The slots are also guarded individually, since the project clear
        during fileExit runs before this.) As a child widget never receives
        closeEvent on shutdown, this is also wired to the application's
        aboutToQuit signal.
        """
        try:
            for widget_type in (QgsMapLayerComboBox, QgsFieldComboBox,
                                QgsCheckableComboBox):
                for cb in self.findChildren(widget_type):
                    cb.blockSignals(True)
        except Exception:
            pass

    def closeEvent(self, event):
        self._mute_layer_widgets()
        super().closeEvent(event)

    def _mode_info(self, algo_refs):
        """Description of the active Binomial/k-fold sub-tab for a built page."""
        if not algo_refs:
            return ''
        sub_tabs = algo_refs.get('sub_tabs')
        if sub_tabs is None:
            return ''
        # Refresh the info panel when the user switches sub-tab, once per page.
        if not getattr(sub_tabs, '_info_connected', False):
            sub_tabs.currentChanged.connect(self._update_info)
            sub_tabs._info_connected = True
        key = 'Binomial Mode Extra' if sub_tabs.currentIndex() == 0 else 'KFold Mode Extra'
        return INFO_DICT.get(key, '')

    def _update_info(self, *args):
        tab_idx = self.mainTabWidget.currentIndex()
        text_name = ""
        extra_text = ""
        
        try:
            if tab_idx == 0:
                if self.SIfunct_r.currentItem() and self.SIfunct_r.hasFocus() or \
                   (self.SIfunct_r.currentRow() != -1 and self.classify_list_r.currentRow() == -1):
                    name = self.SIfunct_r.currentItem().text()
                    text_name = INFO_DICT.get(name, name)
                    if text_name:
                        text_name = text_name.replace("- Dependent Variable (Landslide inventory).", "- Dependent Variable (Landslide Raster Inventory): Binary raster with value 1 for presence and 0 for absence of landslide.")
                    curr_stack_idx = self.stackedWidget_r.currentIndex()
                    if 0 <= curr_stack_idx < len(self.ALGO_KEYS_R):
                        algo_key = self.ALGO_KEYS_R[curr_stack_idx]
                        extra_text = self._mode_info(self._raster_refs.get(algo_key))

                elif self.classify_list_r.currentItem() and self.classify_list_r.currentRow() != -1:
                    name = self.classify_list_r.currentItem().text()
                    text_name = INFO_DICT.get(name, name)

            elif tab_idx == 1:
                if self.SIfunct_v.currentItem() and self.SIfunct_v.hasFocus() or \
                   (self.SIfunct_v.currentRow() != -1 and self.dataprep_list.currentRow() == -1 and self.classify_list.currentRow() == -1):
                    name = self.SIfunct_v.currentItem().text()
                    text_name = INFO_DICT.get(name, name)
                    if text_name:
                        if "<b>Inputs Required:</b><br>" in text_name:
                            parts = text_name.split("<b>Inputs Required:</b><br>")
                            if "Weight of Evidence (WoE)" in name or "Frequency Ratio (FR)" in name:
                                indep_text = "- Independent Variables: Fields values must be classified/categorical."
                            else:
                                indep_text = "- Independent Variables: Fields values can be both continuous and categorical."
                            
                            vector_inputs = (
                                "Slope Units Vector layer: layer that contains the dependent variable and independent variables as fields in the attribute table:<br>"
                                "- Dependent Variable: Field with number of landslides in the slope unit<br>"
                                + indep_text
                            )
                            text_name = parts[0] + "<b>Inputs Required:</b><br>" + vector_inputs
                        else:
                            text_name = text_name.replace("- Dependent Variable (Landslide inventory).", "- Slope Units Vector layer which contains the dependent variables and independent variables as fields in the attribute table.")
                    curr_stack_idx = self.stackedWidget_v.currentIndex()
                    if 0 <= curr_stack_idx < len(self.ALGO_KEYS_R):
                        algo_key = self.ALGO_KEYS_R[curr_stack_idx]
                        extra_text = self._mode_info(self._vector_refs.get(algo_key))

                elif self.dataprep_list.currentItem() and self.dataprep_list.currentRow() != -1:
                    name = self.dataprep_list.currentItem().text()
                    text_name = INFO_DICT.get(name, name)

                elif self.classify_list.currentItem() and self.classify_list.currentRow() != -1:
                    name = self.classify_list.currentItem().text()
                    text_name = INFO_DICT.get(name, name)

            if not text_name:
                self.info_text.setText("Select an algorithm or tool on the left to see its description and inputs.")
            else:
                self.info_text.setText(f"{text_name}\n{extra_text}")
        except Exception:
            self.info_text.setText("Method info unavailable.")

    def _set_inputs_enabled(self, enabled):
        for w in (self.stackedWidget_r, self.stackedWidget_v,
                  self.SIfunct_r, self.SIfunct_v,
                  self.dataprep_list, self.classify_list, self.classify_list_r):
            w.setEnabled(enabled)

    def _set_running(self, text):
        self._is_running = True
        self.status_label.setText(text)
        self.progress_bar.setRange(0, 0)   # Indeterminate
        self.btn_cancel.setVisible(True)
        self._set_inputs_enabled(False)
        QApplication.processEvents()

    def _set_finished(self, status="Finished run", progress=100):
        self._is_running = False
        self._task = None
        self.status_label.setText(status)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)
        self.btn_cancel.setVisible(False)
        self._set_inputs_enabled(True)

    def _cancel_run(self):
        """Stop waiting on the current task and hand the panel back to the user."""
        task = self._task
        if task is not None:
            try:
                task.cancel()
            except RuntimeError:
                pass   # already finished and deleted on the C++ side
            self._log("Run cancelled by the user.", Qgis.Warning)
        self._set_finished(status="Cancelled", progress=0)

    def _start_task(self, description, func, *args, on_success=None, on_error=None):
        """Run `func` on the QGIS task manager and unlock the panel when it ends."""
        task = SzTask(description, func, *args)

        def _handle_error(message):
            self._set_finished(status="Error during run", progress=0)
            self._error(f"{description} failed: {message}. "
                        "See the SZR+ tab of the Log Messages panel for details.")

        if on_success is not None:
            task.completed.connect(on_success)
        task.failed.connect(on_error if on_error is not None else _handle_error)

        self._task = task
        self._set_running(description)
        QgsApplication.taskManager().addTask(task)
        return task

    def load_raster_as_memory_layer(self, disk_path, display_name):
        """Copy a temporary raster file from disk into GDAL's MEM driver,
        load it into QGIS as a RAM-resident layer, and clean up the disk file.
        Keeps the MEM dataset alive in self._mem_datasets.
        """
        from osgeo import gdal
        from qgis.core import QgsRasterLayer, QgsProject
        from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
        import os
        import uuid

        if not os.path.exists(disk_path):
            return None

        # 1. Open the source dataset
        src_ds = gdal.Open(disk_path)
        if not src_ds:
            return None

        # 2. Check available RAM
        width = src_ds.RasterXSize
        height = src_ds.RasterYSize
        bands = src_ds.RasterCount
        datatype = src_ds.GetRasterBand(1).DataType
        
        # Calculate size in bytes
        type_sizes = {
            gdal.GDT_Byte: 1,
            gdal.GDT_UInt16: 2,
            gdal.GDT_Int16: 2,
            gdal.GDT_UInt32: 4,
            gdal.GDT_Int32: 4,
            gdal.GDT_Float32: 4,
            gdal.GDT_Float64: 8
        }
        bytes_per_pixel = type_sizes.get(datatype, 4)
        size_bytes = width * height * bands * bytes_per_pixel
        
        # Get available memory
        avail_bytes = 1024 * 1024 * 1024 # default fallback 1GB
        try:
            import psutil
            avail_bytes = psutil.virtual_memory().available
        except:
            try:
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                avail_bytes = stat.ullAvailPhys
            except:
                pass

        # 3. Verify if it fits in RAM (threshold: 70% of available RAM)
        if size_bytes > 0.7 * avail_bytes:
            size_mb = size_bytes / (1024 * 1024)
            avail_mb = avail_bytes / (1024 * 1024)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Low Memory Warning")
            msg.setText(
                f"The generated raster is too big to fit in the available RAM space.\n\n"
                f"Required: {size_mb:.1f} MB\n"
                f"Available RAM: {avail_mb:.1f} MB\n\n"
                f"Would you like to save it to your local drive instead?"
            )
            save_btn = msg.addButton("Save to Local Drive...", QMessageBox.YesRole)
            load_temp_btn = msg.addButton("Keep as Temporary File on Disk", QMessageBox.NoRole)
            cancel_btn = msg.addButton(QMessageBox.Cancel)
            msg.exec_()

            if msg.clickedButton() == save_btn:
                dest_path, _ = QFileDialog.getSaveFileName(self, "Save Raster", "", "GeoTIFF (*.tif *.tiff)")
                if dest_path:
                    # Copy to local drive path
                    src_ds = None
                    import shutil
                    try:
                        shutil.copy(disk_path, dest_path)
                        os.remove(disk_path)
                    except:
                        pass
                    rlayer = QgsRasterLayer(dest_path, display_name)
                    return rlayer
                else:
                    # User canceled file dialog, default to temporary file on disk
                    src_ds = None
                    rlayer = QgsRasterLayer(disk_path, display_name)
                    return rlayer
            elif msg.clickedButton() == load_temp_btn:
                # Load temporary file from disk directly, do not convert to RAM and do not delete
                src_ds = None
                rlayer = QgsRasterLayer(disk_path, display_name)
                return rlayer
            else:
                # Cancel
                src_ds = None
                return "CANCELLED"

        # 4. Copy to GDAL MEM driver
        gdal.SetConfigOption('GDAL_MEM_ENABLE_OPEN', 'YES')
        mem_driver = gdal.GetDriverByName('MEM')
        
        unique_id = uuid.uuid4().hex
        unique_name = f"SZ_mem_raster_{unique_id}"
        
        mem_ds = mem_driver.CreateCopy(unique_name, src_ds)
        src_ds = None  # close source dataset

        if not mem_ds:
            # Fallback to loading temporary disk file
            rlayer = QgsRasterLayer(disk_path, display_name)
            return rlayer

        # 5. Load in QGIS
        uri = f"MEM:::{unique_name}"
        rlayer = QgsRasterLayer(uri, display_name, "gdal")
        if not rlayer.isValid():
            mem_ds = None
            rlayer = QgsRasterLayer(disk_path, display_name)
            return rlayer

        # 6. Delete disk file
        try:
            os.remove(disk_path)
        except:
            pass

        # 7. Keep MEM dataset reference alive
        if not hasattr(self, '_mem_datasets'):
            self._mem_datasets = {}
        self._mem_datasets[rlayer.id()] = mem_ds

        # Clean up reference when layer is destroyed
        rlayer.destroyed.connect(lambda: self._mem_datasets.pop(rlayer.id(), None))

        return rlayer

    def _get_out_path(self, refs_dict, suffix=None, prefix=None, is_folder=False):
        if is_folder:
            w = refs_dict
            if getattr(w, 'is_temp', False):
                return tempfile.mkdtemp(prefix=prefix or "SZ_folder_")
            return w.filePath()
        else:
            w = refs_dict['fw']
            if getattr(w, 'is_temp', False):
                return tempfile.mktemp(suffix=suffix or "", prefix=prefix or "SZ_temp_")
            return w.filePath()

    # ── Lazy page registration ───────────────────────────────────────────────

    def _register_page_builders(self):
        """Record how to build each page, without building any of them yet."""
        for i, (key, name) in enumerate(zip(self.ALGO_KEYS_R, self.ALGO_NAMES)):
            self._lazy_r[i] = (lambda k=key, n=name: self._build_raster_page(k, n))
            self._lazy_v[i] = (lambda k=key, n=name: self._build_vector_page(k, n))

        self._register_dataprep_builders()
        self._register_classify_builders()
        self._register_classify_raster_builders()

    def _build_raster_page(self, key, name):
        page, refs = _make_raster_page(name)
        self._raster_refs[key] = refs
        refs['binomial']['run_btn'].clicked.connect(
            lambda checked=False, k=key: self._run_raster(k, 'binomial'))
        refs['kfold']['run_btn'].clicked.connect(
            lambda checked=False, k=key: self._run_raster(k, 'kfold'))
        return page

    def _build_vector_page(self, key, name):
        page, refs = _make_vector_page(name)
        self._vector_refs[key] = refs
        for mode in ('binomial', 'kfold'):
            layer_combo = refs[mode]['layer_combo']
            layer_combo.layerChanged.connect(
                lambda lyr, k=key, m=mode: self._populate_vector_fields(k, m, lyr))
            # The combo pre-selects a layer when the project already has one, so
            # layerChanged never fires for it. Populate once up front, otherwise
            # the field selectors stay empty until the user re-picks the layer.
            self._populate_vector_fields(key, mode, layer_combo.currentLayer())
        refs['binomial']['run_btn'].clicked.connect(
            lambda checked=False, k=key: self._run_vector(k, 'binomial'))
        refs['kfold']['run_btn'].clicked.connect(
            lambda checked=False, k=key: self._run_vector(k, 'kfold'))
        return page

    def _populate_vector_fields(self, key: str, mode: str, layer):
        """Populate the dependent/independent field selectors from the chosen layer."""
        from qgis.PyQt import sip

        refs = self._vector_refs.get(key)
        if not refs:
            return
        dep_combo   = refs[mode]['dep_combo']
        indep_combo = refs[mode]['indep_combo']

        # During QGIS shutdown the project is cleared and every layer removed,
        # which fires layerChanged while the C++ widgets are mid-teardown.
        if sip.isdeleted(dep_combo) or sip.isdeleted(indep_combo):
            return
        try:
            valid = layer is not None and not sip.isdeleted(layer) and layer.isValid()
        except (RuntimeError, AttributeError):
            valid = False

        dep_combo.setLayer(layer if valid else None)

        indep_combo.blockSignals(True)
        indep_combo.clear()
        if valid:
            indep_combo.addItems([f.name() for f in layer.fields()])
        indep_combo.blockSignals(False)

    # ── Data Preparation ─────────────────────────────────────────────────────

    def _register_dataprep_builders(self):
        cb_stats_lyr = self._vl_combo()
        cb_stats_fld = QgsFieldComboBox()
        """Register the Data Preparation pages (built on first display)."""

        def _shp_out(title):
            return _file_widget_temp(title, "ESRI Shapefile (*.shp)")

        def _tif_out(title):
            return _file_widget_temp(title, "GeoTIFF (*.tif *.tiff)")

        def _clean_points():
            out_w, out_refs = _shp_out("Output shapefile")
            return [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Extent", _extent_widget("Extent (optional)")),
                ("Buffer Radius (pixels)", self._spinbox(1, 100, 4)),
                ("Min Value Acceptable", self._spinbox(-9999, 9999, 3)),
                ("Output Vector Layer", out_refs, out_w),
            ]

        def _attr_stats():
            lyr, fld = self._layer_field_pair()
            csv_w, csv_refs = _file_widget_temp("Output csv", "CSV (*.csv)")
            return [
                ("Input Layer (vector)", lyr),
                ("ID Field", fld),
                ("Output CSV", csv_refs, csv_w),
                ("Output Folder", _folder_widget()),
            ]

        def _kernel_stats():
            out_w, out_refs = _shp_out("Output shapefile")
            return [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Mask Polygon Layer (vector)", self._vl_combo()),
                ("Buffer Radius (pixels)", self._spinbox(1, 100, 4)),
                ("Output Vector Layer", out_refs, out_w),
            ]

        def _kernel_graphs():
            lyr, fld = self._layer_field_pair()
            return [
                ("Input Points Layer (vector)", lyr),
                ("ID Field", fld),
                ("Output Folder", _folder_widget()),
            ]

        def _points_sampler():
            out1_w, out1_refs = _shp_out("Output Layer Sample")
            out2_w, out2_refs = _shp_out("Output Layer 1-Sample")
            return [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Mask Polygon Layer (vector)", self._vl_combo()),
                ("Pixel Width", self._spinbox(1, 10000, 10)),
                ("Pixel Height", self._spinbox(1, 10000, 10)),
                ("Sample (%)", self._spinbox(1, 100, 70)),
                ("Output Layer Sample", out1_refs, out1_w),
                ("Output Layer 1-Sample", out2_refs, out2_w),
            ]

        def _points_to_grid():
            out_w, out_refs = _tif_out("Output raster")
            return [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Reference Raster", _file_widget("Reference raster", "GeoTIFF (*.tif *.tiff)")),
                ("Extent", _extent_widget("Extent")),
                ("Output Raster", out_refs, out_w),
            ]

        def _poly_to_grid():
            out_w, out_refs = _tif_out("Output raster")
            return [
                ("Input Polygon Layer (vector)", self._vl_combo()),
                ("Pixel Width", self._spinbox(1, 10000, 10)),
                ("Pixel Height", self._spinbox(1, 10000, 10)),
                ("Output Raster", out_refs, out_w),
            ]

        def _classify_txt():
            lyr, fld = self._layer_field_pair()
            return [
                ("Input Layer (vector)", lyr),
                ("Classification .txt File", _file_widget("Classes txt", "Text (*.txt)")),
                ("Field to Classify", fld),
                ("New Field Name", self._line_edit("e.g. class_id")),
            ]

        def _classify_quantiles():
            lyr, fld = self._layer_field_pair()
            return [
                ("Input Layer (vector)", lyr),
                ("Field to Classify", fld),
                ("New Field Name", self._line_edit("e.g. class_id")),
                ("Number of Quantiles (4=quartiles, 10=deciles)", self._spinbox(2, 100, 10)),
            ]

        def _corr_plot():
            lyr, fields = self._layer_fields_pair()
            return [
                ("Input Layer (vector)", lyr),
                ("Continuous Independent Variables", fields),
                ("Output Folder", _folder_widget()),
            ]

        pages_cfg = [
            ("Clean Points By Raster Kernel", _clean_points),
            ("Attribute Table Statistics", _attr_stats),
            ("Points Kernel Statistics", _kernel_stats),
            ("Points Kernel Graphs", _kernel_graphs),
            ("Points Sampler", _points_sampler),
            ("Points To Grid", _points_to_grid),
            ("Poly To Grid", _poly_to_grid),
            ("Classify Field by .txt File", _classify_txt),
            ("Classify Field in Quantiles", _classify_quantiles),
            ("Correlation Plot", _corr_plot),
        ]

        for i, (title, params_fn) in enumerate(pages_cfg):
            self._lazy_v[self.DP_PAGE_OFFSET + i] = (
                lambda t=title, fn=params_fn: self._make_simple_page(
                    t, fn(), self._dp_refs, self._run_dataprep, "#8e44ad"))

    def _make_simple_page(self, title, params, store, handler, color):
        """Build one parameter-form page and remember its widget references."""
        page, refs = _simple_page(title, params, f"RUN  —  {title}", color)
        store[title] = refs
        refs['run_btn'].clicked.connect(
            lambda checked=False, t=title: handler(t))
        return page

    # ── Classify SI ──────────────────────────────────────────────────────────

    def _register_classify_builders(self):
        """Register the vector Classify SI pages (built on first display)."""

        def _classify_roc():
            lyr, si, dep = self._layer_field_pair(2)
            return [
                ("Input Layer (vector)", lyr),
                ("SI Field", si),
                ("Dependent Variable Field", dep),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder", _folder_widget()),
            ]

        def _classify_rocw():
            lyr, si, dep, weight = self._layer_field_pair(3)
            return [
                ("Input Layer (vector)", lyr),
                ("SI Field", si),
                ("Dependent Variable Field", dep),
                ("Weight Field", weight),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder", _folder_widget()),
            ]

        def _roc_generator():
            lyr, si, dep = self._layer_field_pair(2)
            return [
                ("Input Layer (vector)", lyr),
                ("SI Field", si),
                ("Dependent Variable Field", dep),
                ("Output Folder", _folder_widget()),
            ]

        def _confusion_matrix():
            lyr, si, dep = self._layer_field_pair(2)
            out_w, out_refs = _file_widget_temp("Output GeoPackage", "GeoPackage (*.gpkg)")
            return [
                ("Input Layer (vector)", lyr),
                ("SI Field", si),
                ("Dependent Variable Field", dep),
                ("Cutoff percentile (0 = Youden)", self._spinbox(0, 100, 0)),
                ("Output GeoPackage", out_refs, out_w),
            ]

        pages_cfg = [
            ("Classify Vector by ROC", _classify_roc),
            ("Classify Vector by Weighted ROC", _classify_rocw),
            ("ROC Generator", _roc_generator),
            ("Confusion Matrix (FP/TN Threshold)", _confusion_matrix),
        ]

        for i, (title, params_fn) in enumerate(pages_cfg):
            self._lazy_v[self.CL_V_PAGE_OFFSET + i] = (
                lambda t=title, fn=params_fn: self._make_simple_page(
                    t, fn(), self._cl_refs, self._run_classify, "#c0392b"))

    def _register_classify_raster_builders(self):
        """Register the raster Classify SI pages (built on first display)."""

        def _classified_params():
            return [
                ("Landslide Inventory Raster", self._rl_combo()),
                ("SI Raster", self._rl_combo()),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder (Cutoffs & Raster)", _folder_widget(force_physical=True)),
            ]

        def _roc_generator_params():
            return [
                ("Landslide Inventory Raster", self._rl_combo()),
                ("SI Raster", self._rl_combo()),
                ("Output Folder", _folder_widget(force_physical=True)),
            ]

        def _confusion_matrix_params():
            return [
                ("Landslide Inventory Raster", self._rl_combo()),
                ("SI Raster", self._rl_combo()),
                ("Cutoff percentile (0 = Youden)", self._spinbox(0, 100, 0)),
                ("Output Folder (Metrics)", _folder_widget(force_physical=True)),
            ]

        pages_cfg = [
            ("Classify by ROC", _classified_params),
            ("Classify by Closest Point (0,1)", _classified_params),
            ("Classify by F1-Score", _classified_params),
            ("Classify by Threat Score (CSI)", _classified_params),
            ("ROC Generator", _roc_generator_params),
            ("Confusion Matrix (FP/TN Threshold)", _confusion_matrix_params),
        ]

        # stackedWidget_r only declares the six algorithm pages in the .ui, so
        # these need placeholders to occupy indices 6..11 until first shown.
        for _ in pages_cfg:
            self.stackedWidget_r.addWidget(QWidget())

        for i, (title, params_fn) in enumerate(pages_cfg):
            self._lazy_r[self.CL_R_PAGE_OFFSET + i] = (
                lambda t=title, fn=params_fn: self._make_simple_page(
                    t, fn(), self._cl_r_refs, self._run_classify_raster, "#c0392b"))

        # Rebuild the classify_list_r in the correct order.
        # The .ui file has 3 hardcoded items (ROC, ROC Generator, CM). 
        # We clear and re-add all 6 in the desired order to match the stacked widget index.
        self.classify_list_r.clear()
        for title, _ in pages_cfg:
            self.classify_list_r.addItem(title)





    # ── Small widget factories ───────────────────────────────────────────────

    @staticmethod
    def _vl_combo():
        cb = QgsMapLayerComboBox()
        cb.setFilters(QgsMapLayerProxyModel.VectorLayer)
        cb.setAllowEmptyLayer(True)
        return cb

    @staticmethod
    def _rl_combo():
        cb = QgsMapLayerComboBox()
        cb.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb.setAllowEmptyLayer(True)
        return cb

    @staticmethod
    def _spinbox(min_v, max_v, default):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(default)
        return sb

    @staticmethod
    def _line_edit(placeholder):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        return le

    @classmethod
    def _layer_field_pair(cls, n_fields=1):
        """A vector-layer combo plus `n_fields` field combos kept in sync with it."""
        layer_combo = cls._vl_combo()
        field_combos = []
        for _ in range(n_fields):
            fc = QgsFieldComboBox()
            layer_combo.layerChanged.connect(fc.setLayer)
            # The combo pre-selects a layer when the project already has one, so
            # layerChanged never fires for it — seed the field list up front.
            fc.setLayer(layer_combo.currentLayer())
            field_combos.append(fc)
        return (layer_combo, *field_combos)

    @classmethod
    def _layer_fields_pair(cls):
        """A vector-layer combo plus a checkable multi-field combo bound to it."""
        from qgis.PyQt import sip

        layer_combo = cls._vl_combo()
        fields_combo = QgsCheckableComboBox()
        fields_combo.setDefaultText("Select the fields…")

        def _populate(layer):
            # During QGIS shutdown the project is cleared and every layer is
            # removed, which makes the combo emit layerChanged while the C++
            # widgets/layers are mid-teardown. Touching a deleted object here
            # is an access violation (not a catchable Python exception), so bail
            # out if anything we need has already been deleted.
            if sip.isdeleted(fields_combo):
                return
            try:
                valid = layer is not None and not sip.isdeleted(layer) and layer.isValid()
            except (RuntimeError, AttributeError):
                valid = False
            fields_combo.clear()
            if valid:
                fields_combo.addItems([f.name() for f in layer.fields()])

        layer_combo.layerChanged.connect(_populate)
        # The combo pre-selects a layer when the project already has one, so
        # layerChanged never fires for it — seed the field list up front.
        _populate(layer_combo.currentLayer())
        return layer_combo, fields_combo

    # ── RUN slots ────────────────────────────────────────────────────────────

    def _run_raster(self, key: str, mode: str):
        """Extract values and call backend."""
        if self._is_running:
            return

        m_refs = self._raster_refs[key][mode]

        inv_layer = m_refs['inventory'].currentLayer()
        if not inv_layer or not inv_layer.isValid():
            self._warn("Please select a valid Landslide Raster Inventory.")
            return
        inventory = inv_layer.source()

        covariates = m_refs['covariates']._paths()
        if not covariates:
            self._warn("Please add at least one covariate raster.")
            return
        spin_val = m_refs['spin'].value()

        if m_refs['output']['fw'].is_temp:
            self._warn("Please specify a file path for the Output Susceptibility Index Raster.")
            return
        if m_refs['folder'].is_temp:
            self._warn("Please specify a directory path for the Additional Outputs Folder.")
            return

        if m_refs['out_test']['fw'].is_temp or not m_refs['out_test']['fw'].filePath():
            out_test = None
        else:
            out_test = self._get_out_path(m_refs['out_test'], suffix=".tif", prefix="Test_raster_")

        out_raster = self._get_out_path(m_refs['output'], suffix=".tif", prefix="SI_raster_")
        out_folder = self._get_out_path(m_refs['folder'], is_folder=True)

        if not out_folder:
            self._warn("Please select an output folder.")
            return

        algo_display = self.ALGO_NAMES[self.ALGO_KEYS_R.index(key)]

        # Method tags for files
        METHOD_TAGS = {
            'woe': 'WoE',
            'fr':  'FR',
            'lr':  'LR',
            'rf':  'RF',
            'svm': 'SVM',
            'dt':  'DT',
        }
        method_tag = METHOD_TAGS.get(key, key.upper())

        def on_finished(_):
            is_raster_temp = m_refs['output']['fw'].is_temp
            # Auto-load SI
            if out_raster and os.path.exists(out_raster):
                lyr_name = os.path.splitext(os.path.basename(out_raster))[0]
                if is_raster_temp:
                    lyr = self.load_raster_as_memory_layer(out_raster, lyr_name)
                    if lyr == "CANCELLED":
                        lyr = None
                else:
                    from qgis.core import QgsRasterLayer
                    lyr = QgsRasterLayer(out_raster, lyr_name)
                if lyr and lyr.isValid():
                    _style_si_raster(lyr)
                    QgsProject.instance().addMapLayer(lyr)
                    _finish_raster_style(lyr, "Susceptibility Index")

            is_folder_temp = m_refs['folder'].is_temp

            # Load Test ROC CSV as geometryless memory layer if temporary
            if is_folder_temp:
                import glob
                csv_files = glob.glob(os.path.join(out_folder, f"{method_tag}_test_ROC_data.csv"))
                if csv_files:
                    csv_lyr = csv_to_memory_layer(csv_files[0], f"{algo_display} ({mode}) Test ROC Data")
                    if csv_lyr and csv_lyr.isValid():
                        QgsProject.instance().addMapLayer(csv_lyr)

            self._set_finished()
            self._set_results_folder(m_refs, out_folder)
            self._info(f"{algo_display} ({mode}) completed. Results in {out_folder}")
            self._show_charts(out_folder, algo_display, is_folder_temp)

        self._start_task(f"{algo_display} ({mode})", self._call_raster_backend,
                         key, mode, inventory, covariates, spin_val,
                         out_raster, out_test, out_folder,
                         on_success=on_finished)

    def _call_raster_backend(self, key, mode, inventory, covariates,
                              spin_val, out_raster, out_test, out_folder):
        """
        Import and call the raster-native backend algorithm.
        Uses Raster_Algorithms from algorithms.py and the raster runner scripts.
        """
        from ..scripts.algorithms import Raster_Algorithms
        from ..scripts.sz_raster_utils import (
            write_si_raster, save_roc_fit, save_roc_kfold, save_roc_cv
        )

        algo_fn_map = {
            'woe': (Raster_Algorithms.woe_simple_r, Raster_Algorithms.woe_cv_r),
            'fr':  (Raster_Algorithms.fr_simple_r,  Raster_Algorithms.fr_cv_r),
            'lr':  (Raster_Algorithms.LR_simple_r,  Raster_Algorithms.LR_cv_r),
            'rf':  (Raster_Algorithms.RF_simple_r,  Raster_Algorithms.RF_cv_r),
            'svm': (Raster_Algorithms.SVC_simple_r, Raster_Algorithms.SVC_cv_r),
            'dt':  (Raster_Algorithms.DT_simple_r,  Raster_Algorithms.DT_cv_r),
        }
        # Short labels prefixed to every output file (PNG, CSV)
        METHOD_TAGS = {
            'woe': 'WoE',
            'fr':  'FR',
            'lr':  'LR',
            'rf':  'RF',
            'svm': 'SVM',
            'dt':  'DT',
        }
        fn_simple, fn_cv = algo_fn_map[key]
        method_tag = METHOD_TAGS.get(key, key.upper())

        import os
        cov_names = [os.path.basename(p).replace('.tif', '').replace('.tiff', '') for p in covariates]
        params = {
            'inv_path':   inventory,
            'cov_paths':  covariates,
            'cov_names':  cov_names,
            'folder':      out_folder,
            'out':         out_raster,
        }
        
        if not os.path.exists(out_folder):
            os.makedirs(out_folder, exist_ok=True)

        if mode == 'binomial':
            params['testN'] = spin_val
            out_data = fn_simple(params)
            
            # Write SI raster
            write_si_raster(out_data['si_pred'], out_data['pred_idx'], out_data['georef'], out_raster)

            # Write test split raster
            if out_test and spin_val > 0 and 'idx_tr' in out_data:
                from ..scripts.sz_raster_utils import write_test_raster_simple
                write_test_raster_simple(out_data['train_idx'], out_data['idx_tr'], out_data['idx_te'], out_data['georef'], out_test)
            
            # ROC curve — prefixed with method tag
            if spin_val > 0:
                save_roc_cv(out_data['y_train'], out_data['si_train'],
                            out_data['y_test'],  out_data['si_test'], out_folder,
                            method_tag=method_tag, base_stats=out_data.get('base_stats'))
            else:
                save_roc_fit(out_data['y_train'], out_data['si_train'], out_folder,
                             method_tag=method_tag, base_stats=out_data.get('base_stats'))

        else:
            params['kfolds'] = spin_val
            out_data = fn_cv(params)
            
            # Write SI raster
            write_si_raster(out_data['si_pred'], out_data['pred_idx'], out_data['georef'], out_raster)

            # Write test split raster
            if out_test and 'test_indices_list' in out_data:
                from ..scripts.sz_raster_utils import write_test_raster_kfold
                write_test_raster_kfold(out_data['train_idx'], out_data['test_indices_list'], out_data['georef'], out_test)
            
            # ROC curves (per fold) — prefixed with method tag
            import numpy as np
            y_all  = out_data['y_all']
            si_all = out_data['si_all']
            si_all = np.where(np.isnan(si_all), 0.0, si_all)
            save_roc_kfold(y_all, si_all, out_data['test_indices_list'], out_folder,
                           method_tag=method_tag, base_stats=out_data.get('base_stats'))

    def _run_vector(self, key: str, mode: str):
        if self._is_running:
            return

        refs   = self._vector_refs[key]
        m_refs = refs[mode]
        layer  = m_refs['layer_combo'].currentLayer()

        if not layer or not layer.isValid():
            self._warn("Please select a valid Slope Unit Vector layer.")
            return

        dep_field = m_refs['dep_combo'].currentField()
        if not dep_field:
            self._warn("Please select a Dependent Variable field.")
            return

        indep_fields = list(m_refs['indep_combo'].checkedItems())
        if not indep_fields:
            self._warn("Please check at least one Independent Variable field.")
            return

        # Percentage of test sample (binomial) or number of k-folds (kfold).
        spin_val = m_refs['spin'].value()

        out_folder = self._get_out_path(m_refs['folder'], is_folder=True)
        if not out_folder:
            self._warn("Please select an output folder.")
            return

        out_test = self._get_out_path(m_refs['out_test'], suffix=".gpkg", prefix="Test_vector_")
        if m_refs['out_train'] is not None:
            out_train = self._get_out_path(m_refs['out_train'], suffix=".gpkg", prefix="Train_vector_")
        else:
            out_train = None

        algo_display = self.ALGO_NAMES[self.ALGO_KEYS_R.index(key)]

        def on_finished(_):
            is_folder_temp = m_refs['folder'].is_temp
            
            # Load Test layer
            test_path = m_refs['out_test']['fw'].filePath()
            is_test_temp = m_refs['out_test']['fw'].is_temp
            if test_path:
                from qgis.core import QgsVectorLayer
                lyr = QgsVectorLayer(f"{test_path}|layername=test", f"{algo_display} Vector Test SI" if mode == "binomial" else f"{algo_display} Vector test/fit", "ogr")
                if not lyr.isValid():
                    lyr = QgsVectorLayer(test_path, f"{algo_display} Vector Test SI" if mode == "binomial" else f"{algo_display} Vector test/fit", "ogr")
                if lyr.isValid():
                    _style_si_vector(lyr)
                    QgsProject.instance().addMapLayer(lyr)
            elif is_test_temp:
                if os.path.exists(out_test):
                    lyr = load_as_memory_layer(out_test, "test", f"{algo_display} Vector Test SI" if mode == "binomial" else f"{algo_display} Vector test/fit")
                    if lyr and lyr.isValid():
                        _style_si_vector(lyr)
                        QgsProject.instance().addMapLayer(lyr)
                    try: os.remove(out_test)
                    except: pass
            else:
                if os.path.exists(out_test):
                    try: os.remove(out_test)
                    except: pass

            # Load Train/Fit layer (only in binomial mode)
            if mode == 'binomial':
                train_path = m_refs['out_train']['fw'].filePath()
                is_train_temp = m_refs['out_train']['fw'].is_temp
                if train_path:
                    from qgis.core import QgsVectorLayer
                    lyr = QgsVectorLayer(f"{train_path}|layername=train", f"{algo_display} Vector Train SI", "ogr")
                    if not lyr.isValid():
                        lyr = QgsVectorLayer(train_path, f"{algo_display} Vector Train SI", "ogr")
                    if lyr.isValid():
                        _style_si_vector(lyr)
                        QgsProject.instance().addMapLayer(lyr)
                elif is_train_temp:
                    if os.path.exists(out_train):
                        lyr = load_as_memory_layer(out_train, "train", f"{algo_display} Vector Train SI")
                        if lyr and lyr.isValid():
                            _style_si_vector(lyr)
                            QgsProject.instance().addMapLayer(lyr)
                        try: os.remove(out_train)
                        except: pass
                else:
                    if os.path.exists(out_train):
                        try: os.remove(out_train)
                        except: pass

            # Load Test ROC CSV as geometryless memory layer if folder is temporary
            if is_folder_temp:
                import glob
                csv_files = glob.glob(os.path.join(out_folder, "*test_ROC_data.csv"))
                if csv_files:
                    csv_lyr = csv_to_memory_layer(csv_files[0], f"{algo_display} ({mode}) Test ROC Data")
                    if csv_lyr and csv_lyr.isValid():
                        QgsProject.instance().addMapLayer(csv_lyr)

            self._set_finished()
            self._set_results_folder(m_refs, out_folder)
            self._info(f"{algo_display} ({mode}) completed. Results in {out_folder}")
            self._show_charts(out_folder, algo_display, is_folder_temp)

        self._start_task(f"{algo_display} ({mode})", self._call_vector_backend,
                         key, mode, layer.source(), dep_field, indep_fields,
                         spin_val, out_test, out_train, out_folder,
                         on_success=on_finished)

    def _call_vector_backend(self, key, mode, layer_path,
                              dep_field, indep_fields,
                              spin_val, out_test, out_train, out_folder):
        """Call the vector-based (slope-unit) algorithm backend."""
        from ..scripts.algorithms import Algorithms
        from ..scripts.sz_train_simple import CoreAlgorithm
        from ..scripts.sz_train_cv import CoreAlgorithm_cv

        algo_map = {
            'woe': (Algorithms.woe_simple, Algorithms.woe_cv),
            'fr':  (Algorithms.fr_simple,  Algorithms.fr_cv),
            'lr':  (Algorithms.LR_simple,  Algorithms.LR_cv),
            'rf':  (Algorithms.RF_simple,  Algorithms.RF_cv),
            'svm': (Algorithms.SVC_simple, Algorithms.SVC_cv),
            'dt':  (Algorithms.DT_simple,  Algorithms.DT_cv),
        }
        fn_simple, fn_cv = algo_map[key]

        import os
        import tempfile
        from ..scripts.utils import SZ_utils
        from ..scripts.utils_cv import CV_utils

        if not os.path.exists(out_folder):
            os.makedirs(out_folder, exist_ok=True)

        if mode == 'binomial':
            alg_params = {
                'INPUT_VECTOR_LAYER': layer_path,
                'field1': indep_fields,
                'lsd' : dep_field,
                'testN': spin_val,
            }
            tmpdir = tempfile.gettempdir()
            train, testy, nomi, crs, df = SZ_utils.load_simple(tmpdir, alg_params)

            alg_in = {
                'train': train,
                'testy': testy,
                'nomi': nomi,
                'testN': spin_val,
                'fold': out_folder
            }
            trainsi, testsi = fn_simple(alg_in)
            
            if spin_val > 0:
                SZ_utils.save({
                    'df': testsi,
                    'crs': crs,
                    'OUT': out_test or os.path.join(out_folder, 'test.gpkg')
                })
            
            SZ_utils.save({
                'df': trainsi,
                'crs': crs,
                'OUT': out_train or os.path.join(out_folder, 'train.gpkg')
            })

            if spin_val == 0:
                SZ_utils.stampfit({
                    'nomi': nomi,
                    'df': trainsi,
                    'OUT': out_folder
                })
            else:
                SZ_utils.stamp_simple({
                    'nomi': nomi,
                    'df': trainsi,
                    'df1': testsi,
                    'OUT': out_folder
                })

        else:
            alg_params = {
                'INPUT_VECTOR_LAYER': layer_path,
                'field1': indep_fields,
                'lsd' : dep_field,
            }
            tmpdir = tempfile.gettempdir()
            df, nomi, crs = SZ_utils.load_cv(tmpdir, alg_params)

            alg_in = {
                'field1': indep_fields,
                'testN': spin_val,
                'fold': out_folder,
                'nomi': nomi,
                'df': df
            }

            from ..scripts.algorithms import Algorithms
            classifier_map = {
                'woe': Algorithms.c_woe,
                'fr':  Algorithms.c_fr,
                'lr':  Algorithms.c_LR,
                'rf':  Algorithms.c_MRF,
                'svm': Algorithms.c_MSVC,
                'dt':  Algorithms.c_MDT,
            }
            classifier = classifier_map[key]
            
            prob, test_ind = CV_utils.cross_validation(alg_in, fn_cv, classifier)

            if spin_val > 0:
                SZ_utils.save({
                    'df': df,
                    'crs': crs,
                    'OUT': out_test or os.path.join(out_folder, 'test.gpkg')
                })

            SZ_utils.stamp_cv({
                'test_ind': test_ind,
                'df': df,
                'OUT': out_folder
            })

    def _auto_add_vector(self, path, name=None):
        """Add a vector result written to disk into the current project."""
        if not path or not os.path.exists(path):
            return None
        layer = QgsVectorLayer(path, name or os.path.splitext(os.path.basename(path))[0], "ogr")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            return layer
        self._log(f"Could not load the result as a vector layer: {path}", Qgis.Warning)
        return None

    def _auto_add_raster(self, path, name=None):
        """Add a raster result written to disk into the current project."""
        from qgis.core import QgsRasterLayer
        if not path or not os.path.exists(path):
            return None
        layer = QgsRasterLayer(path, name or os.path.splitext(os.path.basename(path))[0])
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            return layer
        self._log(f"Could not load the result as a raster layer: {path}", Qgis.Warning)
        return None

    def _run_dataprep(self, title: str):
        if self._is_running:
            return
        refs = self._dp_refs[title]
        result_dir = None   # where this tool's output landed, for the Open button
        try:
            if title == "Clean Points By Raster Kernel":
                v_layer = refs["Input Points Layer (vector)"].currentLayer()
                r_path  = refs["Raster Kernel Layer"].filePath()
                extent  = _extent_values(refs["Extent"])
                buf     = refs["Buffer Radius (pixels)"].value()
                min_val = refs["Min Value Acceptable"].value()

                out_shp = self._get_out_path(refs["Output Vector Layer"], suffix=".shp", prefix="Clean_points_")
                result_dir = out_shp

                if not (v_layer and r_path and out_shp):
                    self._warn("Ensure points, raster, and output are set.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.cleaning import cleankernelAlgorithm
                algo_mod = cleankernelAlgorithm()
                params = {
                    'INPUT_VECTOR_LAYER': v_layer.source(),
                    'MASK': r_path,
                    'min': min_val,
                    'radius': buf,
                    'OUT': out_shp
                }
                if extent:
                    params['exst'] = extent
                algo_mod.processAlgorithm_edu(params)
                if refs["Output Vector Layer"]["fw"].is_temp:
                    lyr = load_as_memory_layer(out_shp, "clean", "Cleaned Points")
                    if lyr and lyr.isValid():
                        QgsProject.instance().addMapLayer(lyr)
                    try:
                        import glob
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                            p = out_shp.replace('.shp', ext)
                            if os.path.exists(p): os.remove(p)
                    except: pass
                else:
                    self._auto_add_vector(out_shp)

            elif title == "Attribute Table Statistics":
                v_layer  = refs["Input Layer (vector)"].currentLayer()
                id_field = refs["ID Field"].currentField()

                out_csv = self._get_out_path(refs["Output CSV"], suffix=".csv", prefix="Attr_stats_")
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                result_dir = out_folder

                if not (v_layer and id_field and out_csv and out_folder):
                    self._warn("All fields required.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.lsdanalysis import statistic
                alg = statistic()
                alg_params = { 'OUTPUT': out_csv, 'ID': id_field, 'INPUT2': v_layer.source(), 'PATH': out_folder }
                alg.input(alg_params)
                if refs["Output CSV"]["fw"].is_temp:
                    lyr = csv_to_memory_layer(out_csv, "Attribute Table Statistics")
                    if lyr and lyr.isValid():
                        QgsProject.instance().addMapLayer(lyr)
                    try: os.remove(out_csv)
                    except: pass

            elif title == "Points Kernel Statistics":
                v_layer = refs["Input Points Layer (vector)"].currentLayer()
                r_path  = refs["Raster Kernel Layer"].filePath()
                m_layer = refs["Mask Polygon Layer (vector)"].currentLayer()
                buf     = refs["Buffer Radius (pixels)"].value()

                out_shp = self._get_out_path(refs["Output Vector Layer"], suffix=".shp", prefix="Kernel_stats_")
                result_dir = out_shp

                if not (v_layer and r_path and m_layer and out_shp):
                    self._warn("Please provide all required inputs.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.stat31 import rasterstatkernelAlgorithm
                alg = rasterstatkernelAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT': m_layer.source(), 'INPUT2': r_path, 'INPUT3': v_layer.source() }
                ras, ds1, XY, crs = alg.importing(alg_params)
                alg_params2 = { 'INPUT': buf, 'INPUT3': ras, 'INPUT2': XY, 'INPUT1': ds1, 'CRS': crs }
                XYcoord, attributi = alg.indexing(alg_params2)
                alg_params3 = { 'OUTPUT': out_shp, 'INPUT2': XYcoord, 'INPUT': ds1, 'INPUT3': attributi, 'CRS': crs }
                alg.saveV(alg_params3)
                if refs["Output Vector Layer"]["fw"].is_temp:
                    lyr = load_as_memory_layer(out_shp, "kernel_stats", "Points Kernel Statistics")
                    if lyr and lyr.isValid():
                        QgsProject.instance().addMapLayer(lyr)
                    try:
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                            p = out_shp.replace('.shp', ext)
                            if os.path.exists(p): os.remove(p)
                    except: pass
                else:
                    self._auto_add_vector(out_shp)

            elif title == "Points Kernel Graphs":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                field = refs["ID Field"].currentField()
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                result_dir = out_folder
                if not layer or not field or not out_folder:
                    self._warn("Please provide all parameters.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.graphs_lsdstats_kernel import statistickernel
                alg = statistickernel()
                alg_params = { 'ID': field, 'INPUT2': layer.source(), 'OUT': out_folder }
                alg.input(alg_params)

            elif title == "Points Sampler":
                v_pts  = refs["Input Points Layer (vector)"].currentLayer()
                v_poly = refs["Mask Polygon Layer (vector)"].currentLayer()
                pw     = refs["Pixel Width"].value()
                ph     = refs["Pixel Height"].value()
                samp   = refs["Sample (%)"].value()

                out1 = self._get_out_path(refs["Output Layer Sample"], suffix=".shp", prefix="Sample_")
                out2 = self._get_out_path(refs["Output Layer 1-Sample"], suffix=".shp", prefix="1_Sample_")
                result_dir = out1

                if not (v_pts and out1 and out2):
                    self._warn("Points layer and both outputs required.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.randomsampler3 import samplerAlgorithm
                alg = samplerAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT': v_pts.source(), 'INPUT1': v_poly.source(), 'w': pw, 'h': ph, 'train': samp }
                v, t, xy = alg.resampler(alg_params)
                alg.save({ 'INPUT1': out1, 'INPUT2': v, 'INPUT3': xy })
                alg.save({ 'INPUT1': out2, 'INPUT2': t, 'INPUT3': xy })
                
                if refs["Output Layer Sample"]["fw"].is_temp:
                    lyr1 = load_as_memory_layer(out1, "sample", "Output Layer Sample")
                    if lyr1 and lyr1.isValid():
                        QgsProject.instance().addMapLayer(lyr1)
                    try:
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                            p = out1.replace('.shp', ext)
                            if os.path.exists(p): os.remove(p)
                    except: pass
                else:
                    self._auto_add_vector(out1)
                    
                if refs["Output Layer 1-Sample"]["fw"].is_temp:
                    lyr2 = load_as_memory_layer(out2, "1_sample", "Output Layer 1-Sample")
                    if lyr2 and lyr2.isValid():
                        QgsProject.instance().addMapLayer(lyr2)
                    try:
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                            p = out2.replace('.shp', ext)
                            if os.path.exists(p): os.remove(p)
                    except: pass
                else:
                    self._auto_add_vector(out2)

            elif title == "Points To Grid":
                v_layer = refs["Input Points Layer (vector)"].currentLayer()
                r_path  = refs["Reference Raster"].filePath()
                coords  = _extent_values(refs["Extent"])

                out_tif = self._get_out_path(refs["Output Raster"], suffix=".tif", prefix="Pts_to_grid_")
                result_dir = out_tif

                if not (v_layer and r_path and out_tif):
                    self._warn("Layer, Reference raster, output required.")
                    return
                if not coords:
                    self._warn("Please define the output extent.")
                    return
                self._set_running(f"Running {title}...")
                from qgis.core import QgsRectangle
                from ..scripts.pointtogrid import pointtogridAlgorithm
                alg = pointtogridAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                rect = QgsRectangle(coords[0], coords[2], coords[1], coords[3])
                alg_params = { 'STRING': '', 'INPUT_RASTER_LAYER': r_path, 'INPUT_EXTENT': rect, 'INPUT_VECTOR_LAYER': v_layer.source(), 'OUTPUT': out_tif }
                alg.extent(alg_params)
                alg.importingandcounting(alg_params)
                self._auto_add_raster(out_tif)

            elif title == "Poly To Grid":
                v_layer = refs["Input Polygon Layer (vector)"].currentLayer()
                pw      = refs["Pixel Width"].value()
                ph      = refs["Pixel Height"].value()

                out_tif = self._get_out_path(refs["Output Raster"], suffix=".tif", prefix="Poly_to_grid_")
                result_dir = out_tif

                if not (v_layer and out_tif):
                    self._warn("Polygon layer and output required.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.polytogrid import polytogridAlgorithm
                alg = polytogridAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT_VECTOR_LAYER': v_layer.source(), 'OUTPUT': out_tif, 'W': pw, 'H': ph }
                alg.importingandcounting(alg_params)
                self._auto_add_raster(out_tif)

            elif title == "Classify Field by .txt File":
                layer = refs["Input Layer (vector)"].currentLayer()
                txt = refs["Classification .txt File"].filePath()
                field = refs["Field to Classify"].currentField()
                new_f = refs["New Field Name"].text()
                if not layer or not txt or not field or not new_f:
                    self._warn("Please provide all parameters.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.classcovtxt import classcovtxtAlgorithm
                alg = classcovtxtAlgorithm()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'field': field, 'txt': txt, 'nome': new_f }
                alg.classify(alg_params)

            elif title == "Classify Field in Quantiles":
                layer = refs["Input Layer (vector)"].currentLayer()
                field = refs["Field to Classify"].currentField()
                new_f = refs["New Field Name"].text()
                num = refs["Number of Quantiles (4=quartiles, 10=deciles)"].value()
                if not layer or not field or not new_f:
                    self._warn("Please provide all parameters.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.classcovdeciles import classcovdecAlgorithm
                alg = classcovdecAlgorithm()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'field': field, 'nome': new_f, 'num': num }
                alg.classify(alg_params)

            elif title == "Correlation Plot":
                layer = refs["Input Layer (vector)"].currentLayer()
                fields = list(refs["Continuous Independent Variables"].checkedItems())
                out = self._get_out_path(refs["Output Folder"], is_folder=True)
                result_dir = out
                if not layer or not fields or not out:
                    self._warn("Please provide all parameters.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.corrplot import CorrAlgorithm
                alg = CorrAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'field1': fields }
                df, nomi, crs = alg.load(alg_params)
                alg_params2 = { 'INPUT_VECTOR_LAYER': layer.source(), 'field1': fields, 'df': df, 'nomi': nomi, 'OUT': out }
                alg.corr(alg_params2)

            self._set_finished()
            if result_dir:
                self._set_results_folder(refs, result_dir)
            self._info(f"{title} completed successfully.")
        except Exception as e:
            import traceback
            # The panel must never stay locked because a step raised.
            self._set_finished(status="Error during run", progress=0)
            self._log(traceback.format_exc(), Qgis.Critical)
            self._error(f"{title} failed: {e}. "
                        "See the SZR+ tab of the Log Messages panel for details.")

    def _run_classify(self, title: str):
        refs = self._cl_refs[title]
        layer = refs["Input Layer (vector)"].currentLayer()

        if not layer or not layer.isValid():
            self._warn("Please select a valid Input Layer.")
            return

        si_field = refs["SI Field"].currentField()
        dep_field = refs["Dependent Variable Field"].currentField()

        if not si_field or not dep_field:
            self._warn("Please select both SI and Dependent Variable Fields.")
            return

        try:
            if title == "Classify Vector by ROC":
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not out_folder:
                    self._warn("Please specify an Output Folder.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.classvector import classvAlgorithm
                alg_params = {
                    'INPUT_VECTOR_LAYER': layer.source(),
                    'field1': si_field,
                    'lsd': dep_field
                }
                alg = classvAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                df, crs = alg.load(alg_params)
                alg.classy({
                    'df': df,
                    'NUMBER': refs["Number of Classes (from 2 to 10)"].value(),
                    'OUTPUT': out_folder
                })
                
                is_folder_temp = refs["Output Folder"].is_temp
                if is_folder_temp:
                    import os
                    csv_path = os.path.join(out_folder, "plotROC.csv")
                    if os.path.exists(csv_path):
                        csv_lyr = csv_to_memory_layer(csv_path, "Classify Vector by ROC (plotROC)")
                        if csv_lyr and csv_lyr.isValid():
                            QgsProject.instance().addMapLayer(csv_lyr)
                            
                self._set_finished()
                self._set_results_folder(refs, out_folder)
                self._info(f"Classify Vector by ROC completed. Saved to {out_folder}")
                
            elif title == "Classify Vector by Weighted ROC":
                w_field = refs["Weight Field"].currentField()
                if not w_field:
                    self._warn("Please select a Weight Field.")
                    return
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not out_folder:
                    self._warn("Please specify an Output Folder.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.classvectorw import classvAlgorithmW
                alg_params = {
                    'INPUT_VECTOR_LAYER': layer.source(),
                    'field1': si_field,
                    'lsd': dep_field,
                    'W': w_field
                }
                alg = classvAlgorithmW()
                alg.f = __import__('tempfile').gettempdir()
                df, crs = alg.load(alg_params)
                alg.classy({
                    'df': df,
                    'NUMBER': refs["Number of Classes (from 2 to 10)"].value(),
                    'OUTPUT': out_folder
                })
                
                is_folder_temp = refs["Output Folder"].is_temp
                if is_folder_temp:
                    import os
                    csv_path = os.path.join(out_folder, "plotROCW.csv")
                    if os.path.exists(csv_path):
                        csv_lyr = csv_to_memory_layer(csv_path, "Classify Vector by Weighted ROC (plotROCW)")
                        if csv_lyr and csv_lyr.isValid():
                            QgsProject.instance().addMapLayer(csv_lyr)
                            
                self._set_finished()
                self._set_results_folder(refs, out_folder)
                self._info(f"Classify Vector by Weighted ROC completed. Saved to {out_folder}")

            elif title == "ROC Generator":
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not out_folder:
                    self._warn("Please specify an Output Folder.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.selfroc import rocGenerator
                alg_params = {
                    'INPUT_VECTOR_LAYER': layer.source(),
                    'field1': si_field,
                    'lsd': dep_field
                }
                alg = rocGenerator()
                alg.f = __import__('tempfile').gettempdir()
                df, crs = alg.load(alg_params)
                alg.roc({
                    'df': df,
                    'OUT': out_folder
                })
                self._set_finished()
                self._set_results_folder(refs, out_folder)
                self._info(f"ROC Generator completed. Saved to {out_folder}")
                self._show_charts(out_folder, "ROC Generator",
                                  refs["Output Folder"].is_temp)

            elif title == "Confusion Matrix (FP/TN Threshold)":
                out_gpkg = self._get_out_path(refs["Output GeoPackage"], suffix=".gpkg", prefix="Conf_matrix_")

                if not out_gpkg:
                    self._warn("Please specify an Output GeoPackage.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.tptn import FPAlgorithm
                alg_params = {
                    'INPUT_VECTOR_LAYER': layer.source(),
                    'field1': si_field,
                    'lsd': dep_field,
                    'testN': refs["Cutoff percentile (0 = Youden)"].value()
                }
                alg = FPAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                df, nomi, crs = alg.load(alg_params)
                alg.save({
                    'df': df,
                    'crs': crs,
                    'OUT': out_gpkg
                })
                
                is_gpkg_temp = refs["Output GeoPackage"]["fw"].is_temp
                if is_gpkg_temp:
                    if os.path.exists(out_gpkg):
                        lyr = load_as_memory_layer(out_gpkg, "confusion_matrix", "Confusion Matrix Output")
                        if lyr and lyr.isValid():
                            QgsProject.instance().addMapLayer(lyr)
                        try: os.remove(out_gpkg)
                        except: pass
                else:
                    if os.path.exists(out_gpkg):
                        from qgis.core import QgsVectorLayer
                        v_lyr = QgsVectorLayer(f"{out_gpkg}|layername=confusion_matrix", "Confusion Matrix Output", "ogr")
                        if v_lyr.isValid():
                            QgsProject.instance().addMapLayer(v_lyr)

                self._set_finished()
                self._set_results_folder(refs, out_gpkg)
                self._info(f"Confusion Matrix calculated. Saved to {out_gpkg}")

        except Exception as e:
            import traceback
            # The panel must never stay locked because a step raised.
            self._set_finished(status="Error during run", progress=0)
            self._log(traceback.format_exc(), Qgis.Critical)
            self._error(f"{title} failed: {e}. "
                        "See the SZR+ tab of the Log Messages panel for details.")

    def _run_classify_raster(self, algo_name: str):
        if self._is_running:
            return

        refs = self._cl_r_refs[algo_name]

        inv_layer = refs["Landslide Inventory Raster"].currentLayer()
        si_layer  = refs["SI Raster"].currentLayer()
        num_classes = None
        cutoff = None

        if algo_name == "ROC Generator":
            folder_widget = refs["Output Folder"]
        elif algo_name == "Confusion Matrix (FP/TN Threshold)":
            folder_widget = refs["Output Folder (Metrics)"]
            cutoff = refs["Cutoff percentile (0 = Youden)"].value()
        else:
            folder_widget = refs["Output Folder (Cutoffs & Raster)"]
            num_classes = refs["Number of Classes (from 2 to 10)"].value()

        out_folder = self._get_out_path(folder_widget, is_folder=True)

        if not inv_layer or not si_layer:
            self._warn("Please select both Inventory and SI Rasters.")
            return

        if not out_folder:
            self._warn("Please select an output folder.")
            return

        is_folder_temp = folder_widget.is_temp
        if is_folder_temp:
            self._warn("Please specify a directory path for the Output Folder.")
            return

        # Capture plain strings only – NO QGIS layer objects inside the thread closure.
        si_path  = si_layer.source()
        inv_path = inv_layer.source()
        # Freeze the values that were resolved on the main thread.
        _num_classes = num_classes
        _cutoff      = cutoff
        _out_folder  = out_folder
        _algo_name   = algo_name
        _is_folder_temp = is_folder_temp

        def _call_classify_raster():
            """
            Pure computation, run on the task manager's worker thread.
            Returns a plain dict – NEVER creates QgsRasterLayer or calls QgsProject.
            """
            from osgeo import gdal
            import numpy as np
            import os
            import tempfile

            ds_si  = None
            ds_inv = None
            ds_out = None

            try:
                # ── Open input rasters ────────────────────────────────────────────
                ds_si  = gdal.Open(si_path)
                ds_inv = gdal.Open(inv_path)

                if ds_si is None or ds_inv is None:
                    raise Exception("Failed to open raster using GDAL.")

                gt    = ds_si.GetGeoTransform()
                proj  = ds_si.GetProjection()
                xsize = ds_si.RasterXSize
                ysize = ds_si.RasterYSize

                si_band  = ds_si.GetRasterBand(1)
                inv_band = ds_inv.GetRasterBand(1)

                si_ndv  = si_band.GetNoDataValue()
                inv_ndv = inv_band.GetNoDataValue()
                if si_ndv  is None: si_ndv  = -9999
                if inv_ndv is None: inv_ndv = -9999

                y_scores_raw = si_band.ReadAsArray().flatten()
                y_true_raw   = inv_band.ReadAsArray().flatten()

                # Release bands and input datasets — arrays are in memory now.
                si_band  = None
                inv_band = None
                ds_si    = None
                ds_inv   = None

                valid_idx = np.where(
                    (y_scores_raw != si_ndv) & (y_true_raw != inv_ndv) &
                    (~np.isnan(y_scores_raw)) & (~np.isnan(y_true_raw))
                )[0]

                y_scores = y_scores_raw[valid_idx]
                y_true   = y_true_raw[valid_idx]
                y_true   = np.where(y_true > 0, 1, 0)

                from sklearn.metrics import roc_curve, roc_auc_score

                # ── Classify by ROC (GA optimisation) ─────────────────────────────
                if _algo_name == "Classify by ROC":
                    from ..scripts.roc import rocAlgorithm

                    alg_params = {
                        'INPUT1': y_scores_raw.reshape(ysize, xsize),
                        'INPUT2': y_true_raw.reshape(ysize, xsize),
                        'NUMBER': _num_classes,
                        'OUTPUT': os.path.join(_out_folder, "classification_cutoffs_ROC.csv")
                    }

                    alg = rocAlgorithm()
                    alg.xsize = xsize
                    alg.ysize = ysize
                    alg.f = tempfile.gettempdir()
                    alg.classy(alg_params)
                        
                    # Reclassify raster
                    cutoffs = np.loadtxt(alg_params['OUTPUT'], delimiter=',')
                    if cutoffs.ndim == 0:
                        cutoffs = list(cutoffs.reshape(-1))
                    else:
                        cutoffs = list(cutoffs)

                    # cutoffs from GA: [m, c1, c2, ..., M+1]
                    reclassified_raw = np.digitize(y_scores_raw, cutoffs[1:-1]) + 1
                    reclassified_raw = reclassified_raw.astype(np.float32)
                    reclassified_raw[y_scores_raw == si_ndv] = si_ndv

                    # Overwrite the raw np.savetxt file with the unified 3-column format
                    # (Class, Lower Bound, Upper Bound) — same layout as the other methods.
                    import csv
                    with open(alg_params['OUTPUT'], 'w', newline='') as f_csv:
                        writer = csv.writer(f_csv)
                        writer.writerow(['Class', 'Lower Bound', 'Upper Bound'])
                        for i in range(_num_classes):
                            writer.writerow([i + 1, cutoffs[i], cutoffs[i + 1]])

                    out_tif = os.path.join(_out_folder, "reclassified_SI_ROC.tif")
                    driver  = gdal.GetDriverByName('GTiff')
                    ds_out  = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
                    ds_out.SetGeoTransform(gt)
                    ds_out.SetProjection(proj)
                    ds_out.GetRasterBand(1).SetNoDataValue(si_ndv)
                    ds_out.GetRasterBand(1).WriteArray(reclassified_raw.reshape(ysize, xsize))
                    ds_out.FlushCache()
                    ds_out = None   # ← close file handle on disk NOW, before returning

                    return {
                        'out_tif':     out_tif,
                        'layer_name':  "Reclassified SI (ROC)",
                        'num_classes': _num_classes,
                        'out_folder':  _out_folder,
                        'is_temp':     _is_folder_temp,
                        'algo_name':   _algo_name,
                        'method_label': "ROC",
                    }

                # ── ROC Generator (no raster output) ─────────────────────────────
                elif _algo_name == "ROC Generator":
                    from ..scripts import sz_raster_utils
                    sz_raster_utils.save_roc_fit(y_true, y_scores, _out_folder, method_tag='ROC_Gen')
                    return {
                        'out_tif':     None,
                        'out_folder':  _out_folder,
                        'is_temp':     _is_folder_temp,
                        'algo_name':   _algo_name,
                    }

                # ── Confusion Matrix (no raster output) ──────────────────────────
                elif _algo_name == "Confusion Matrix (FP/TN Threshold)":
                    import pandas as pd
                    from sklearn.metrics import confusion_matrix as sk_cm

                    if _cutoff == 0:
                        fpr_a, tpr_a, thresh = roc_curve(y_true, y_scores)
                        idx = np.argmax(tpr_a - fpr_a)   # Youden Index
                        cutoff_val = thresh[idx]
                    else:
                        cutoff_val = np.percentile(y_scores, _cutoff)

                    y_pred = np.where(y_scores > cutoff_val, 1, 0)
                    tn, fp, fn, tp = sk_cm(y_true, y_pred).ravel()

                    df = pd.DataFrame([{
                        'Cutoff Percentile':  _cutoff,
                        'SI Cutoff Value':    cutoff_val,
                        'True Positives':     tp,
                        'True Negatives':     tn,
                        'False Positives':    fp,
                        'False Negatives':    fn
                    }])
                    df.to_csv(os.path.join(_out_folder, "confusion_matrix_metrics.csv"), index=False)
                    return {
                        'out_tif':     None,
                        'out_folder':  _out_folder,
                        'is_temp':     _is_folder_temp,
                        'algo_name':   _algo_name,
                    }

                # ── Closest Point / F1-Score / Threat Score (CSI) ────────────────
                elif _algo_name in ("Classify by Closest Point (0,1)", "Classify by F1-Score", "Classify by Threat Score (CSI)"):
                    fpr_arr, tpr_arr, thresholds_arr = roc_curve(y_true, y_scores)

                    if _algo_name == "Classify by Closest Point (0,1)":
                        distances    = np.sqrt((1 - tpr_arr) ** 2 + fpr_arr ** 2)
                        best_idx     = np.argmin(distances)
                        method_label = "ClosestPoint"
                    elif _algo_name == "Classify by F1-Score":
                        P = float(np.sum(y_true == 1))
                        N = float(np.sum(y_true == 0))
                        tp_arr = tpr_arr * P
                        fp_arr = fpr_arr * N
                        fn_arr = P - tp_arr
                        denom  = 2 * tp_arr + fp_arr + fn_arr
                        f1_arr = np.where(denom > 0, 2 * tp_arr / denom, 0)
                        best_idx     = np.argmax(f1_arr)
                        method_label = "F1Score"
                    elif _algo_name == "Classify by Threat Score (CSI)":
                        P = float(np.sum(y_true == 1))
                        N = float(np.sum(y_true == 0))
                        tp_arr  = tpr_arr * P
                        fp_arr  = fpr_arr * N
                        fn_arr  = P - tp_arr
                        denom   = tp_arr + fp_arr + fn_arr
                        csi_arr = np.where(denom > 0, tp_arr / denom, 0)
                        best_idx     = np.argmax(csi_arr)
                        method_label = "ThreatScore_CSI"

                    opt_threshold = thresholds_arr[best_idx]
                    si_min = np.nanmin(y_scores)
                    si_max = np.nanmax(y_scores)

                    if _num_classes > 1:
                        lower_breaks = np.linspace(si_min, opt_threshold, num=_num_classes)
                        cutoff_edges = np.append(lower_breaks, si_max + 1)
                    else:
                        cutoff_edges = [si_min, si_max + 1]

                    reclassified_raw = np.digitize(y_scores_raw, cutoff_edges[1:-1]) + 1
                    reclassified_raw = reclassified_raw.astype(np.float32)
                    reclassified_raw[y_scores_raw == si_ndv] = si_ndv

                    # Save cutoff CSV
                    import csv
                    csv_path = os.path.join(_out_folder, f"classification_cutoffs_{method_label}.csv")
                    with open(csv_path, 'w', newline='') as f_csv:
                        writer = csv.writer(f_csv)
                        writer.writerow(['Class', 'Lower Bound', 'Upper Bound'])
                        for i in range(_num_classes):
                            writer.writerow([i + 1, cutoff_edges[i], cutoff_edges[i + 1]])

                    # Write reclassified raster
                    out_tif = os.path.join(_out_folder, f"reclassified_SI_{method_label}.tif")
                    driver  = gdal.GetDriverByName('GTiff')
                    ds_out  = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
                    ds_out.SetGeoTransform(gt)
                    ds_out.SetProjection(proj)
                    ds_out.GetRasterBand(1).SetNoDataValue(si_ndv)
                    ds_out.GetRasterBand(1).WriteArray(reclassified_raw.reshape(ysize, xsize))
                    ds_out.FlushCache()
                    ds_out = None   # ← close file handle on disk NOW, before returning

                    return {
                        'out_tif':     out_tif,
                        'layer_name':  f"Reclassified SI ({method_label})",
                        'num_classes': _num_classes,
                        'out_folder':  _out_folder,
                        'is_temp':     _is_folder_temp,
                        'algo_name':   _algo_name,
                        'method_label': method_label,
                    }

            except Exception as e:
                import traceback
                raise Exception(f"Classification failed:\n{e}\n\n{traceback.format_exc()}")

            finally:
                # Belt-and-suspenders: release every GDAL handle even on error.
                try:
                    del si_band
                except Exception:
                    pass
                try:
                    del inv_band
                except Exception:
                    pass
                ds_si  = None
                ds_inv = None
                ds_out = None

        # _on_classify_raster_done runs on the main thread via Qt signal/slot.
        self._start_task(algo_name, _call_classify_raster,
                         on_success=self._on_classify_raster_done)

    def _on_classify_raster_done(self, result):
        """
        Slot – always invoked on the main (GUI) thread by Qt's signal/slot mechanism.
        Creates and registers the QgsRasterLayer here so that QGIS holds a clean,
        thread-safe file handle.  The worker thread already closed every GDAL handle
        before emitting finished_ok, so there is no double-open race on Windows.
        """
        self._set_finished()

        if not isinstance(result, dict):
            return

        is_temp = result.get('is_temp', False)
        out_folder = result.get('out_folder')
        algo_name = result.get('algo_name')
        method_label = result.get('method_label')

        if algo_name and out_folder:
            self._set_results_folder(self._cl_r_refs.get(algo_name, {}), out_folder)

        # Load cutoffs/metrics CSV if temporary
        if is_temp and out_folder:
            import os
            from qgis.core import QgsProject
            if algo_name == "Classify by ROC":
                csv_path = os.path.join(out_folder, "classification_cutoffs_ROC.csv")
                csv_lyr = csv_to_memory_layer(csv_path, "Classify by ROC Cutoffs")
                if csv_lyr and csv_lyr.isValid():
                    QgsProject.instance().addMapLayer(csv_lyr)
            elif algo_name == "ROC Generator":
                csv_path = os.path.join(out_folder, "ROC_Gen_fit_ROC_data.csv")
                csv_lyr = csv_to_memory_layer(csv_path, "ROC Generator Fit ROC Data")
                if csv_lyr and csv_lyr.isValid():
                    QgsProject.instance().addMapLayer(csv_lyr)
            elif algo_name == "Confusion Matrix (FP/TN Threshold)":
                csv_path = os.path.join(out_folder, "confusion_matrix_metrics.csv")
                csv_lyr = csv_to_memory_layer(csv_path, "Confusion Matrix Metrics")
                if csv_lyr and csv_lyr.isValid():
                    QgsProject.instance().addMapLayer(csv_lyr)
            elif method_label:
                csv_path = os.path.join(out_folder, f"classification_cutoffs_{method_label}.csv")
                csv_lyr = csv_to_memory_layer(csv_path, f"{algo_name} Cutoffs")
                if csv_lyr and csv_lyr.isValid():
                    QgsProject.instance().addMapLayer(csv_lyr)

            self._show_charts(out_folder, algo_name or "Classify Raster", True)

        out_tif = result.get('out_tif')
        if not out_tif:
            # Algorithms that produce no raster (ROC Generator, Confusion Matrix)
            return

        num_classes = result.get('num_classes', 5)
        layer_name  = result.get('layer_name', "Reclassified SI")

        from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer

        if is_temp:
            rlayer = self.load_raster_as_memory_layer(out_tif, layer_name)
            if rlayer == "CANCELLED":
                return
        else:
            rlayer = QgsRasterLayer(out_tif, layer_name)

        if not rlayer or not rlayer.isValid():
            self._error(f"The reclassified raster could not be loaded: {out_tif}",
                        title="Layer error")
            return

        # Build colour palette (main thread – safe to use Qt colour types here)
        cmap = _colormap('RdYlGn_r')

        if num_classes == 2:
            class_names = {1: "Low", 2: "High"}
        elif num_classes == 3:
            class_names = {1: "Low", 2: "Moderate", 3: "High"}
        elif num_classes == 5:
            class_names = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
        else:
            class_names = {i: f"Class {i}" for i in range(1, num_classes + 1)}

        classes = []
        for i in range(1, num_classes + 1):
            norm_val = (i - 1) / max(1, num_classes - 1)
            rgba  = cmap(norm_val)
            color = QColor(int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255))
            lbl   = class_names.get(i, f"Class {i}")
            classes.append(QgsPalettedRasterRenderer.Class(i, color, lbl))

        renderer = QgsPalettedRasterRenderer(rlayer.dataProvider(), 1, classes)
        rlayer.setRenderer(renderer)
        QgsProject.instance().addMapLayer(rlayer)
        _finish_raster_style(rlayer, "Susceptibility Class")
        rlayer.triggerRepaint()

