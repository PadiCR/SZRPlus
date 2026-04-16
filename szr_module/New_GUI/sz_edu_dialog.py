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
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QSpinBox, QPushButton, QListWidget, QListWidgetItem,
    QTreeView, QMessageBox, QProgressBar, QGroupBox, QFormLayout,
    QTabWidget, QAbstractItemView, QCheckBox, QScrollArea, QAbstractScrollArea,
    QFileSystemModel, QSizePolicy, QHeaderView,
    QLineEdit, QToolButton, QMenu, QAction, QFileDialog, QApplication
)
from qgis.PyQt.QtCore import (
    Qt, QDir, QMimeData, QUrl, pyqtSignal, QThread
)
from qgis.PyQt.QtGui import QDragEnterEvent, QDropEvent, QPixmap

from qgis.gui import QgsFileWidget, QgsMapLayerComboBox, QgsFieldComboBox
from qgis.core import (
    QgsMapLayerProxyModel, QgsVectorLayer, QgsWkbTypes,
    QgsProject, QgsMessageLog, Qgis,
)

UI_FILE = os.path.join(os.path.dirname(__file__), 'SZ_edu.ui')
FORM_CLASS, _ = uic.loadUiType(UI_FILE)

INFO_DICT = {
    'Weight of Evidence (WoE)': "<b>Weight of Evidence (WoE)</b><br><br><b>Description:</b><br>WoE is a data-driven, bivariate statistical method based on Bayes' rule. It calculates positive and negative weights (W+ and W-) for each predictive factor class based on the presence or absence of landslides.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) MUST be classified/categorical.",
    'Frequency Ratio (FR)': "<b>Frequency Ratio (FR)</b><br><br><b>Description:</b><br>FR is a bivariate statistical method that calculates a ratio between the percentage of landslides occurring in a given parameter class and the percent area of that class in the study region.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) MUST be classified/categorical.",
    'Logistic Regression (LR)': "<b>Logistic Regression (LR)</b><br><br><b>Description:</b><br>LR is a multivariate statistical method that models the probability of landslide occurrence as a logistic function of multiple independent variables. It handles both continuous and categorical variables naturally.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical.",
    'Random Forest (RF)': "<b>Random Forest (RF)</b><br><br><b>Description:</b><br>RF is an ensemble machine learning method that operates by constructing a multitude of decision trees at training time and outputting the class that is the mode of the classes or mean prediction.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical.",
    'Support Vector Machine (SVM)': "<b>Support Vector Machine (SVM)</b><br><br><b>Description:</b><br>SVM is a powerful supervised learning model that analyzes data and recognizes patterns. It constructs a hyperplane or set of hyperplanes in a high-dimensional space for classification.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical (requires normalization, handled internally).",
    'Decision Trees (DT)': "<b>Decision Trees (DT)</b><br><br><b>Description:</b><br>DT uses a tree-like model of decisions and their possible consequences. It breaks down a dataset into smaller subsets while at the same time an associated decision tree is incrementally developed.<br><br><b>Inputs Required:</b><br>- Dependent Variable (Landslide inventory).<br>- Independent Variables (Covariates) can be both continuous and categorical.",
    
    'Binomial Mode Extra': "<br><br><b>Mode: SI Binomial Sampler</b><br>The binomial sampler divides the data into training and testing datasets based on a specified percentage (e.g., 70% train, 30% test). It calibrates the model on the train set and evaluates it on the test set.<br><br><b>Outputs:</b><br>- Output Test/Train Raster: Pixel values will be 0 for Training data, 1 for Testing data, and NoData otherwise (for Raster Base).<br>- Additional Output Folder contains: ROC and SR curves (.png), ROC and SR data (.csv) and model-specific files (weights, coefficients, or feature importance).",
    'KFold Mode Extra': "<br><br><b>Mode: SI K-fold</b><br>K-fold cross-validation divides the data randomly into K equal-sized folds. The model is trained K times, each time using K-1 folds for training and evaluating on the remaining 1 fold. This reduces bias in performance estimation.<br><br><b>Outputs:</b><br>- Output Test/Train Raster: Pixel values range from 1 to K representing the assigned fold for each pixel, and NoData otherwise (for Raster Base).<br>- Additional Output Folder contains K subfolders (e.g., fold_0, fold_1), each containing its respective ROC and SR curves (.png), ROC and SR data (.csv), and model-specific files.",
    
    'Clean Points By Raster Kernel': "<b>Clean Points By Raster Kernel</b><br><br>Filter and clean vector points using a raster constraint. Only points whose surrounding kernel (buffer) contains acceptable valid raster values will be retained.",
    'Attribute Table Statistics': "<b>Attribute Table Statistics</b><br><br>Calculate descriptive statistics based on an attribute table of a vector layer.",
    'Points Kernel Statistics': "<b>Points Kernel Statistics</b><br><br>Performs a statistical extraction around points acting as kernels against a raster grid, constrained by a mask polygon.",
    'Points Kernel Graphs': "<b>Points Kernel Graphs</b><br><br>Generates informative graphs and plots based on the kernel statistics calculated around the input points.",
    'Points Sampler': "<b>Points Sampler</b><br><br>Divides an input point layer into two distinct samples (for example, training and testing subsets) based on a specified percentage, applying a grid-based spatial sampling mechanism.",
    'Points To Grid': "<b>Points To Grid</b><br><br>Rasterizes an input point dataset onto a grid, snapping to a reference raster and specified spatial extent.",
    'Poly To Grid': "<b>Poly To Grid</b><br><br>Rasterizes an input polygon dataset into a raster grid with a user-defined pixel width and height.",
    'Classify Field by .txt File': "<b>Classify Field by .txt File</b><br><br>Classifies (reclassifies) a continuous or categorical vector field using a set of rules defined in a plain text file.",
    'Classify Field in Quantiles': "<b>Classify Field in Quantiles</b><br><br>Classifies a continuous vector field into equal-sized quantiles (e.g., quartiles, deciles) and creates a new field with the corresponding classification IDs.",
    'Correlation Plot': "<b>Correlation Plot</b><br><br>Generates a correlation matrix plot for a set of continuous independent variables, useful for identifying highly correlated features before running susceptibility models.",

    'Classify Vector by ROC': "<b>Classify Vector by ROC</b><br><br>Reclassifies the continuous Susceptibility Index (SI) into discrete classes based on points of the ROC curve, maximizing standard metrics.",
    'Classify Vector by Weighted ROC': "<b>Classify Vector by Weighted ROC</b><br><br>Reclassifies the SI into discrete classes using a weighted ROC approach, incorporating a custom weight field.",
    'ROC Generator': "<b>ROC Generator</b><br><br>Calculates and outputs a standalone Receiver Operating Characteristic (ROC) curve and Area Under the Curve (AUC) for an existing SI prediction field against a dependent variable.",
    'Confusion Matrix (FP/TN Threshold)': "<b>Confusion Matrix (FP/TN Threshold)</b><br><br>Calculates true positives, false positives, true negatives, and false negatives metrics based on a specified cutoff percentile to generate a confusion matrix package.",
    # Raster Classify SI tools
    # Raster Classify SI tools
    'Classify by ROC': (
        '<b>Classify by ROC</b><br><br>'
        '<b>Description:</b><br>'
        'Classifies the Susceptibility Index (SI) raster into discrete categories by optimizing class boundaries along the ROC curve results.<br><br>'
        '<b>Formula:</b><br>'
        'Youden Index J = TPR &minus; FPR<br><br>'
        '<b>Reclassification:</b><br>'
        'Uses an optimized Genetic Algorithm to find the N&minus;1 breakpoints that maximize the difference between True Positives and False Positives globally along the ROC curve.<br><br>'
        '<b>Focus:</b><br>'
        'Global discrimination and multi-class optimization.<br><br>'
        '<b>Best for:</b><br>'
        'High-precision susceptibility terrain zoning where maximizing discrimination is critical across all classes.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
    'ROC Generator (Raster)': '<b>ROC Generator</b><br>Generates the Receiver Operating Characteristic (ROC) curve directly from the given SI Raster and the Landslide Inventory Raster.<br><br><b>Output:</b><br>- A `.png` image of the ROC plot including Area Under Curve (AUC), Distance (DIS), and Critical Success Index (CSI).<br>- A `.csv` file containing False Positive Rates, True Positive Rates, and their respective thresholds.',
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
        'When you want a mathematically neutral boundary between Low and High risk zones, defined spatially rather than vertically.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
    'Classify by F1-Score': (
        '<b>Classify by F1-Score</b><br><br>'
        '<b>Description:</b><br>'
        'Balance Precision (how many predicted "High Risk" were actually landslides) and Recall (how many total landslides were caught) to find the most representative class boundary.<br><br>'
        '<b>Formula:</b><br>'
        'F1 = 2&times;TP / (2&times;TP + FP + FN)<br><br>'
        '<b>Reclassification:</b><br>'
        'The threshold that maximizes the F1-score is calculated along the ROC curve and used to designate the boundary for the highest susceptibility class.<br><br>'
        '<b>Focus:</b><br>'
        'Reliable prediction quality and classification accuracy.<br><br>'
        '<b>Best for:</b><br>'
        'Imbalanced datasets (e.g., landslides covering &lt; 5% of the area) as it ensures the high-risk class is trustworthy and not overpredicted.<br><br>'
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
        'When "Low Risk" areas are secondary and the primary goal is maximizing the detection of future landslide events.<br><br>'
        '<b>Output:</b><br>'
        '- A CSV file with the calculated cutoff values.<br>'
        '- A reclassified GeoTIFF raster (N classes, RdYlGn color ramp) added to QGIS.'
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _labeled(label_text, widget):
    """Return a QVBoxLayout with a label above the widget."""
    vbox = QVBoxLayout()
    lbl = QLabel(label_text)
    lbl.setStyleSheet("font-weight: bold;")
    vbox.addWidget(lbl)
    vbox.addWidget(widget)
    return vbox


def _file_widget(title="", filter_="All files (*)"):
    fw = QgsFileWidget()
    fw.setDialogTitle(title)
    fw.setFilter(filter_)
    return fw


class WorkerThread(QThread):
    finished_ok = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished_ok.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(e)


class ProcessingOutputWidget(QWidget):
    fileChanged = pyqtSignal(str)

    def __init__(self, title, is_folder=False, filter="All files (*)"):
        super().__init__()
        self.is_folder = is_folder
        self.title = title
        self.filter = filter
        self.is_temp = True
        self._filepath = ""
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setStyleSheet("color: gray; font-style: italic;")
        self.line_edit.setText("[Save to temporary folder]" if is_folder else "[Save to temporary file]")
        layout.addWidget(self.line_edit)
        
        self.tool_btn = QToolButton()
        self.tool_btn.setText("...")
        self.tool_btn.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(self.tool_btn)
        
        self.menu = QMenu(self)
        self.action_temp = QAction("Save to a Temporary File", self) if not is_folder else QAction("Save to a Temporary Folder", self)
        self.action_save = QAction("Save to File...", self) if not is_folder else QAction("Save to Directory...", self)
        
        self.menu.addAction(self.action_temp)
        self.menu.addAction(self.action_save)
        self.tool_btn.setMenu(self.menu)
        
        self.action_temp.triggered.connect(self.set_temporary)
        self.action_save.triggered.connect(self.prompt_save)
        
    def set_temporary(self):
        self.is_temp = True
        self._filepath = ""
        self.line_edit.setStyleSheet("color: gray; font-style: italic;")
        self.line_edit.setText("[Save to temporary folder]" if self.is_folder else "[Save to temporary file]")
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
            self.line_edit.setStyleSheet("")
            self.line_edit.setText(path)
            self.fileChanged.emit(path)
        else:
            self.set_temporary()


def _folder_widget(title="Output folder"):
    return ProcessingOutputWidget(title, is_folder=True)


def _file_widget_temp(title="", filter_="All files (*)"):
    w = ProcessingOutputWidget(title, is_folder=False, filter=filter_)
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
    lbl_left = QLabel("Add Independent Variable Raster")
    lbl_left.setStyleSheet("font-weight: bold;")
    lv.addWidget(lbl_left)
    
    layer_combo = QgsMapLayerComboBox()
    layer_combo.setFilters(QgsMapLayerProxyModel.RasterLayer)
    lv.addWidget(layer_combo)
    
    btn_add = QPushButton("Add Selected Layer")
    lv.addWidget(btn_add)
    
    btn_browse = QPushButton("Browse Multiple Files...")
    lv.addWidget(btn_browse)
    
    lv.addStretch()
    splitter.addWidget(left)

    # Right: selected rasters
    right = QWidget()
    rv = QVBoxLayout(right)
    lbl_right = QLabel("Selected Rasters")
    lbl_right.setStyleSheet("font-weight: bold;")
    rv.addWidget(lbl_right)
    drop_list = DropListWidget()
    rv.addWidget(drop_list)
    # Remove button
    btn_remove = QPushButton("Remove selected")
    btn_remove.clicked.connect(lambda: [drop_list.takeItem(drop_list.currentRow())
                                        for _ in range(1) if drop_list.currentItem()])
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

    # Title
    title = QLabel(algo_name)
    title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
    page_layout.addWidget(title)

    # Sub-tabs
    sub_tabs = QTabWidget()
    page_layout.addWidget(sub_tabs)

    refs = {}

    for mode in ("binomial", "kfold"):
        sub_page = QWidget()
        sp_layout = QVBoxLayout(sub_page)

        # Landslide raster (now a combo box)
        inv_lbl = QLabel("Landslide Raster Inventory")
        inv_lbl.setStyleSheet("font-weight: bold;")
        sp_layout.addWidget(inv_lbl)
        
        inv_layout = QHBoxLayout()
        inv_combo = QgsMapLayerComboBox()
        inv_combo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        inv_layout.addWidget(inv_combo)
        
        btn_inv_browse = QPushButton("Browse...")
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
        lbl_cov = QLabel("Independent Variables rasters")
        lbl_cov.setStyleSheet("font-weight: bold;")
        sp_layout.addWidget(lbl_cov)
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
        out_raster_widget, out_raster_refs = _file_widget_temp("Output Susceptibility Index (SI) Raster", "GeoTIFF (*.tif *.tiff)")
        sp_layout.addLayout(_labeled("Output Susceptibility Index (SI) Raster", out_raster_widget))

        out_test_widget, out_test_refs = _file_widget_temp("Output Test/Train Raster", "GeoTIFF (*.tif *.tiff)")
        sp_layout.addLayout(_labeled("Output Test/Train Raster (optional)", out_test_widget))

        # Output folder
        if 'WoE' in algo_name or 'FR' in algo_name:
            folder_lbl = "Additional outputs folder (ROC, AUC, Weights)"
        elif 'LR' in algo_name or 'SVM' in algo_name:
            folder_lbl = "Additional outputs folder (ROC, AUC, Coefficients)"
        elif 'RF' in algo_name or 'DT' in algo_name:
            folder_lbl = "Additional outputs folder (ROC, AUC, Feature Importance)"
        else:
            folder_lbl = "Additional outputs folder (ROC, AUC, etc)"
            
        out_folder = _folder_widget(folder_lbl)
        sp_layout.addLayout(_labeled(folder_lbl, out_folder))
        
        # Auto-fill output folder if empty
        out_raster_refs['fw'].fileChanged.connect(lambda path, f=out_folder: f.setFilePath(os.path.dirname(path)) if path and not f.filePath() else None)

        # RUN button
        run_btn = QPushButton(f"RUN  —  {algo_name}")
        run_btn.setStyleSheet(
            "QPushButton { background:#2d7dd2; color:white; font-weight:bold;"
            " padding:8px; border-radius:4px; }"
            "QPushButton:hover { background:#1a5fa3; }"
        )
        sp_layout.addWidget(run_btn)
        sp_layout.addStretch()

        refs[mode] = {
            'inventory': inv_combo,
            'covariates': drop_list,
            'spin': spin,
            'output': out_raster_refs,
            'out_test': out_test_refs,
            'folder': out_folder,
            'run_btn': run_btn,
        }

        tab_title = "SI Binomial Sampler" if mode == "binomial" else "SI k-fold"
        sub_tabs.addTab(sub_page, tab_title)

    refs['sub_tabs'] = sub_tabs
    return page, refs


# ─────────────────────────────────────────────────────────────────────────────
# Build a vector algorithm page  (2 sub-tabs: Binomial / k-fold)
# ─────────────────────────────────────────────────────────────────────────────

def _make_vector_page(algo_name: str):
    """
    Returns (page_widget, refs).  refs['layer_combo'] is the slope-unit combo.
    refs[mode]['dep_list'], refs[mode]['dep_selected'], refs[mode]['indep_list']
    are the field selector widgets.
    """
    page = QWidget()
    page_layout = QVBoxLayout(page)

    title = QLabel(algo_name)
    title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
    page_layout.addWidget(title)

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

        # ── Independent variables (multi-select checklist + mirror panel) ─────
        field_splitter = QSplitter(Qt.Horizontal)

        # Left: checklist of all fields
        left = QWidget()
        lv = QVBoxLayout(left)
        lbl_indep = QLabel("Independent Variable Fields\n(check all that apply)")
        lbl_indep.setStyleSheet("font-weight: bold;")
        lv.addWidget(lbl_indep)
        indep_list = QListWidget()
        indep_list.setToolTip("Fields to use as covariates")
        lv.addWidget(indep_list)
        field_splitter.addWidget(left)

        # Right: selected independent-variable fields
        right = QWidget()
        rv = QVBoxLayout(right)
        lbl_indep_sel = QLabel("Selected Independent Fields")
        lbl_indep_sel.setStyleSheet("font-weight: bold;")
        rv.addWidget(lbl_indep_sel)
        indep_selected = QListWidget()
        indep_selected.setEnabled(False)
        rv.addWidget(indep_selected)
        field_splitter.addWidget(right)

        field_splitter.setSizes([280, 280])
        sp_layout.addWidget(field_splitter)

        # SpinBox
        if mode == "binomial":
            spin_lbl = "Percentage of test sample  (0 = fit only)"
        else:
            spin_lbl = "Number of k-folds  (≥ 2)"
        spin = QSpinBox()
        spin.setRange(0, 99) if mode == "binomial" else spin.setRange(2, 50)
        spin.setValue(30) if mode == "binomial" else spin.setValue(5)
        sp_layout.addLayout(_labeled(spin_lbl, spin))

        # Output vector
        out_vec_test_widget, out_vec_test_refs = _file_widget_temp("Output Test GeoPackage", "GeoPackage (*.gpkg)")
        sp_layout.addLayout(_labeled("Output Test GeoPackage", out_vec_test_widget))

        out_vec_train_widget, out_vec_train_refs = _file_widget_temp("Output Train/Fit GeoPackage", "GeoPackage (*.gpkg)")
        sp_layout.addLayout(_labeled("Output Train/Fit GeoPackage", out_vec_train_widget))

        if 'WoE' in algo_name or 'FR' in algo_name:
            folder_lbl = "Additional outputs folder (ROC, AUC, Weights)"
        elif 'LR' in algo_name or 'SVM' in algo_name:
            folder_lbl = "Additional outputs folder (ROC, AUC, Coefficients)"
        elif 'RF' in algo_name or 'DT' in algo_name:
            folder_lbl = "Additional outputs folder (ROC, AUC, Feature Importance)"
        else:
            folder_lbl = "Additional outputs folder (ROC, AUC, etc)"
            
        out_folder = _folder_widget(folder_lbl)
        sp_layout.addLayout(_labeled(folder_lbl, out_folder))
        
        # Link Train GeoPackage folder to output folder if empty
        out_vec_train_refs['fw'].fileChanged.connect(lambda path, f=out_folder: f.setFilePath(os.path.dirname(path)) if path and not f.filePath() else None)

        run_btn = QPushButton(f"RUN  —  {algo_name}")
        run_btn.setStyleSheet(
            "QPushButton { background:#27ae60; color:white; font-weight:bold;"
            " padding:8px; border-radius:4px; }"
            "QPushButton:hover { background:#1a7d43; }"
        )
        sp_layout.addWidget(run_btn)
        sp_layout.addStretch()

        refs[mode] = {
            'layer_combo': layer_combo,
            'dep_combo': dep_combo,
            'indep_list': indep_list,
            'indep_selected': indep_selected,
            'spin': spin,
            'out_test': out_vec_test_refs,
            'out_train': out_vec_train_refs,
            'folder': out_folder,
            'run_btn': run_btn,
        }

        tab_title = "SI Binomial Sampler" if mode == "binomial" else "SI k-fold"
        sub_tabs.addTab(sub_page, tab_title)

    refs['sub_tabs'] = sub_tabs
    return page, refs


# ─────────────────────────────────────────────────────────────────────────────
# Simple parameter-form pages (Data Preparation / Classify SI)
# ─────────────────────────────────────────────────────────────────────────────

def _simple_page(title: str, params: list, run_label: str, btn_color: str = "#8e44ad"):
    """
    params = list of ('label', widget) tuples.
    Returns (page, {key: widget, 'run_btn': QPushButton}).
    """
    page = QWidget()
    layout = QVBoxLayout(page)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-size:13px; font-weight:bold; padding:4px;")
    layout.addWidget(lbl)

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
        layout.addLayout(_labeled(label_text, widget))

    run_btn = QPushButton(run_label)
    run_btn.setStyleSheet(
        f"QPushButton {{ background:{btn_color}; color:white; font-weight:bold;"
        " padding:8px; border-radius:4px; }"
        f"QPushButton:hover {{ background:{btn_color}cc; }}"
    )
    layout.addWidget(run_btn)
    layout.addStretch()
    refs['run_btn'] = run_btn
    return page, refs


# ─────────────────────────────────────────────────────────────────────────────
# Main Dialog
# ─────────────────────────────────────────────────────────────────────────────

class SzEduDialog(QDialog, FORM_CLASS):

    ALGO_KEYS_R = ['woe', 'fr', 'lr', 'rf', 'svm', 'dt']
    ALGO_NAMES  = [
        'Weight of Evidence (WoE)',
        'Frequency Ratio (FR)',
        'Logistic Regression (LR)',
        'Random Forest (RF)',
        'Support Vector Machine (SVM)',
        'Decision Trees (DT)',
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("SZR+ (Susceptibility Zoning + Raster capabilities)")
        self.lbl_cl_r_title.setText("Classify SI Raster")

        self._is_running = False
        self._workers = []

        # Storage for widget references
        self._raster_refs = {}   # key: algo_name str -> {'binomial':…, 'kfold':…}
        self._vector_refs = {}   # key: algo_name str
        self._dp_refs     = {}   # key: function label
        self._cl_refs     = {}   # key: function label
        self._cl_r_refs   = {}   # key: function label

        # Move Classify Vector list under Data Prep list in Vector tab layout
        if hasattr(self, 'dataprep_list') and hasattr(self, 'classify_list'):
            # The Vector Base Tab layout uses horizontal layouts to separate the 3 columns
            # Column 2 has Data Prep. Column 3 has Classify SI + Stacked Widget
            # Let's dynamically find their parent layouts and move Classify SI under Data Prep
            
            # Find the label for Classify SI
            cl_label = None
            parent_widget = self.classify_list.parentWidget()
            if parent_widget:
                for child in parent_widget.findChildren(QLabel):
                    if child.text() == "Classify SI":
                        cl_label = child
                        break
            
            # Find the layout containing dataprep_list
            dp_layout = None
            parent_widget = self.dataprep_list.parentWidget()
            if parent_widget:
                # Find the direct layout managing dataprep_list
                for child in parent_widget.children():
                    if isinstance(child, QVBoxLayout):
                        for i in range(child.count()):
                            item = child.itemAt(i)
                            if item and item.widget() == self.dataprep_list:
                                dp_layout = child
                                break
                    if dp_layout: break
            
            if dp_layout and cl_label:
                # Add spacing, then the Classify Label, then the Classify List below Data Prep List
                dp_layout.addSpacing(20)
                dp_layout.addWidget(cl_label)
                dp_layout.addWidget(self.classify_list)

        # Auto-adjust list widths uniformly
        max_width = 0
        lists_to_adjust = [lw for lw in (self.SIfunct_r, self.SIfunct_v, self.dataprep_list, self.classify_list, self.classify_list_r) if hasattr(self, lw.objectName())]
        
        # 1. measure max width
        for lw in lists_to_adjust:
            lw.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            w = lw.sizeHintForColumn(0) + 80 # +80 for icons and scrollbar safety
            if w > max_width:
                max_width = w
                
        # 2. apply uniform width and height
        for lw in lists_to_adjust:
            lw.setFixedWidth(max_width)
            lw.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
            
            if lw in (self.SIfunct_r, self.SIfunct_v):
                lw.setMinimumHeight(170)
            elif lw == self.dataprep_list:
                lw.setMinimumHeight(240) # Shortened as requested
                lw.setMaximumHeight(260)
            elif lw == self.classify_list:
                lw.setMinimumHeight(100)
                lw.setMaximumHeight(150)
            elif lw == self.classify_list_r:
                lw.setMaximumHeight(150)


        from qgis.PyQt.QtGui import QIcon
        icon_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
        for idx, key in enumerate(self.ALGO_KEYS_R):
            icon_path = os.path.join(icon_dir, f"{key}_icon.png")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                item_r = self.SIfunct_r.item(idx)
                if item_r:
                    item_r.setIcon(icon)
                item_v = self.SIfunct_v.item(idx)
                if item_v:
                    item_v.setIcon(icon)

        self._build_raster_tab()
        self._build_vector_tab()
        self._build_dataprep_tab()
        self._build_classify_tab()
        self._build_classify_raster_tab()

        # Wire list → stacked widget navigation
        def set_r_page(idx):
            if idx >= 0:
                self.stackedWidget_r.setCurrentIndex(idx)
                self.classify_list_r.clearSelection()
                self.classify_list_r.setCurrentRow(-1)


        def set_cl_r_page(idx):
            if idx >= 0:
                # Assuming the first 6 pages are the main raster algos
                self.stackedWidget_r.setCurrentIndex(6 + idx)
                self.SIfunct_r.clearSelection()
                self.SIfunct_r.setCurrentRow(-1)

        self.SIfunct_r.currentRowChanged.connect(set_r_page)
        self.classify_list_r.currentRowChanged.connect(set_cl_r_page)
        
        def set_v_page(idx):
            if idx >= 0:
                self.stackedWidget_v.setCurrentIndex(idx)
                self.dataprep_list.clearSelection()
                self.dataprep_list.setCurrentRow(-1)
                self.classify_list.clearSelection()
                self.classify_list.setCurrentRow(-1)

        def set_dp_page(idx):
            if idx >= 0:
                self.stackedWidget_v.setCurrentIndex(6 + idx)
                self.SIfunct_v.clearSelection()
                self.SIfunct_v.setCurrentRow(-1)
                self.classify_list.clearSelection()
                self.classify_list.setCurrentRow(-1)

        def set_cl_page(idx):
            if idx >= 0:
                self.stackedWidget_v.setCurrentIndex(16 + idx)
                self.SIfunct_v.clearSelection()
                self.SIfunct_v.setCurrentRow(-1)
                self.dataprep_list.clearSelection()
                self.dataprep_list.setCurrentRow(-1)

        self.SIfunct_v.currentRowChanged.connect(set_v_page)
        self.dataprep_list.currentRowChanged.connect(set_dp_page)
        self.classify_list.currentRowChanged.connect(set_cl_page)

        # Default selections
        self.SIfunct_r.setCurrentRow(0)
        self.SIfunct_v.setCurrentRow(0)
        self.dataprep_list.setCurrentRow(-1)
        self.classify_list.setCurrentRow(-1)
        self.classify_list_r.setCurrentRow(-1)

        # Status and Progress bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Reset GUI Button
        self.btn_reset_gui = QPushButton("Reset GUI")
        self.btn_reset_gui.setStyleSheet(
            "QPushButton { background:#e74c3c; color:white; font-weight:bold; padding:2px 8px; border-radius:3px; }"
            "QPushButton:hover { background:#c0392b; }"
        )
        self.btn_reset_gui.setToolTip("Force unlock the GUI if a process gets stuck or errors out silently.")
        self.btn_reset_gui.setVisible(False)  # Only show when running
        self.btn_reset_gui.clicked.connect(self._reset_gui)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.btn_reset_gui)
        self.mainLayout.addLayout(status_layout)
        
        from qgis.PyQt.QtWidgets import QTextEdit, QSplitter
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumWidth(300)
        self.info_text.setStyleSheet("background-color: #f7f9fc; color: #2c3e50; font-size: 13px; font-family: 'Segoe UI'; padding: 10px; border: 1px solid #ccc; border-radius: 4px;")
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.mainTabWidget)
        splitter.addWidget(self.info_text)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        self.mainLayout.insertWidget(0, splitter)
        
        self.mainTabWidget.currentChanged.connect(self._update_info)
        self.SIfunct_r.currentRowChanged.connect(self._update_info)
        self.classify_list_r.currentRowChanged.connect(self._update_info)
        self.SIfunct_v.currentRowChanged.connect(self._update_info)
        self.dataprep_list.currentRowChanged.connect(self._update_info)
        self.classify_list.currentRowChanged.connect(self._update_info)
        
        self.adjustSize()
        self._update_info()

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
                    if curr_stack_idx >= 0 and curr_stack_idx < len(self.ALGO_KEYS_R):
                        algo_key = self.ALGO_KEYS_R[curr_stack_idx]
                        sub_tabs = self._raster_refs[algo_key]['sub_tabs']
                        extra_text = INFO_DICT.get('Binomial Mode Extra', '') if sub_tabs.currentIndex() == 0 else INFO_DICT.get('KFold Mode Extra', '')
                        if not hasattr(sub_tabs, '_info_connected'):
                            sub_tabs.currentChanged.connect(self._update_info)
                            sub_tabs._info_connected = True

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
                    if curr_stack_idx >= 0 and curr_stack_idx < len(self.ALGO_KEYS_R):
                        algo_key = self.ALGO_KEYS_R[curr_stack_idx]
                        sub_tabs = self._vector_refs[algo_key]['sub_tabs']
                        extra_text = INFO_DICT.get('Binomial Mode Extra', '') if sub_tabs.currentIndex() == 0 else INFO_DICT.get('KFold Mode Extra', '')
                        if not hasattr(sub_tabs, '_info_connected'):
                            sub_tabs.currentChanged.connect(self._update_info)
                            sub_tabs._info_connected = True

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

    def _set_running(self, text):
        self._is_running = True
        self.status_label.setText(text)
        self.progress_bar.setRange(0, 0) # Indeterminate
        if hasattr(self, 'btn_reset_gui'):
            self.btn_reset_gui.setVisible(True)
        for w in (self.stackedWidget_r, self.stackedWidget_v, self.SIfunct_r, self.SIfunct_v, self.dataprep_list, self.classify_list):
            w.setEnabled(False)
        QApplication.processEvents()

    def _set_finished(self):
        self._is_running = False
        self.status_label.setText("Finished run")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        if hasattr(self, 'btn_reset_gui'):
            self.btn_reset_gui.setVisible(False)
        for w in (self.stackedWidget_r, self.stackedWidget_v, self.SIfunct_r, self.SIfunct_v, self.dataprep_list, self.classify_list):
            w.setEnabled(True)

    def _reset_gui(self):
        """Force unlock the GUI if a process gets stuck or errors out silently."""
        self._is_running = False
        self.status_label.setText("GUI Reset (Ready)")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        if hasattr(self, 'btn_reset_gui'):
            self.btn_reset_gui.setVisible(False)
        for w in (self.stackedWidget_r, self.stackedWidget_v, self.SIfunct_r, self.SIfunct_v, self.dataprep_list, self.classify_list):
            w.setEnabled(True)
        # Terminate any stranded worker threads
        for worker in self._workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self._workers.clear()

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

    # ── Raster Base ──────────────────────────────────────────────────────────

    def _build_raster_tab(self):
        for i, (key, name) in enumerate(zip(self.ALGO_KEYS_R, self.ALGO_NAMES)):
            page, refs = _make_raster_page(name)
            self._raster_refs[key] = refs

            # Replace the empty placeholder page in the stacked widget
            stacked = self.stackedWidget_r
            stacked.removeWidget(stacked.widget(i))
            stacked.insertWidget(i, page)

            # Connect RUN buttons
            refs['binomial']['run_btn'].clicked.connect(
                lambda checked=False, k=key: self._run_raster(k, 'binomial'))
            refs['kfold']['run_btn'].clicked.connect(
                lambda checked=False, k=key: self._run_raster(k, 'kfold'))

    # ── Vector Base ──────────────────────────────────────────────────────────

    def _build_vector_tab(self):
        for i, (key, name) in enumerate(zip(self.ALGO_KEYS_R, self.ALGO_NAMES)):
            page, refs = _make_vector_page(name)
            self._vector_refs[key] = refs

            stacked = self.stackedWidget_v
            stacked.removeWidget(stacked.widget(i))
            stacked.insertWidget(i, page)

            for mode in ('binomial', 'kfold'):
                # Connect layer combo → field population
                refs[mode]['layer_combo'].layerChanged.connect(
                    lambda lyr, k=key, m=mode: self._populate_vector_fields(k, m, lyr))
                refs[mode]['indep_list'].itemChanged.connect(
                    lambda item, k=key, m=mode: self._sync_indep_selected(k, m))

            # Connect RUN buttons
            refs['binomial']['run_btn'].clicked.connect(
                lambda checked=False, k=key: self._run_vector(k, 'binomial'))
            refs['kfold']['run_btn'].clicked.connect(
                lambda checked=False, k=key: self._run_vector(k, 'kfold'))

    def _populate_vector_fields(self, key: str, mode: str, layer):
        """Populate indep_list and dep_combo with fields from the chosen layer."""
        refs = self._vector_refs[key]
        fields = []
        if layer and layer.isValid():
            fields = [f.name() for f in layer.fields()]

        dep_combo   = refs[mode]['dep_combo']
        indep_list  = refs[mode]['indep_list']
        indep_sel   = refs[mode]['indep_selected']

        dep_combo.setLayer(layer)
        
        indep_list.blockSignals(True)
        indep_list.clear()
        indep_sel.clear()

        for fname in fields:
            item = QListWidgetItem(fname)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            indep_list.addItem(item)

        indep_list.blockSignals(False)

    def _sync_indep_selected(self, key: str, mode: str):
        """Mirror checked items from indep_list into indep_selected."""
        refs   = self._vector_refs[key][mode]
        indep_list = refs['indep_list']
        indep_sel  = refs['indep_selected']
        indep_sel.clear()
        for i in range(indep_list.count()):
            item = indep_list.item(i)
            if item.checkState() == Qt.Checked:
                indep_sel.addItem(item.text())

    # ── Data Preparation ─────────────────────────────────────────────────────

    def _build_dataprep_tab(self):
        cb_stats_lyr = self._vl_combo()
        cb_stats_fld = QgsFieldComboBox()
        cb_stats_lyr.layerChanged.connect(cb_stats_fld.setLayer)

        cb_graphs_lyr = self._vl_combo()
        cb_graphs_fld = QgsFieldComboBox()
        cb_graphs_lyr.layerChanged.connect(cb_graphs_fld.setLayer)

        cb_txt_lyr = self._vl_combo()
        cb_txt_fld = QgsFieldComboBox()
        cb_txt_lyr.layerChanged.connect(cb_txt_fld.setLayer)

        cb_quant_lyr = self._vl_combo()
        cb_quant_fld = QgsFieldComboBox()
        cb_quant_lyr.layerChanged.connect(cb_quant_fld.setLayer)
        
        cb_corr_lyr = self._vl_combo()
        corr_list = QListWidget()
        def _pop_corr_fields(lyr):
            corr_list.clear()
            if lyr and lyr.isValid():
                from qgis.PyQt.QtWidgets import QListWidgetItem
                for f in lyr.fields():
                    item = QListWidgetItem(f.name())
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    corr_list.addItem(item)
        cb_corr_lyr.layerChanged.connect(_pop_corr_fields)

        csv_stats_out_widget, csv_stats_out_refs = _file_widget_temp("Output csv", "CSV (*.csv)")

        from qgis.PyQt.QtWidgets import QLineEdit
        def _line_edit(placeholder):
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            return le

        def _shp_out(title):
            return _file_widget_temp(title, "ESRI Shapefile (*.shp)")
            
        def _tif_out(title):
            return _file_widget_temp(title, "GeoTIFF (*.tif *.tiff)")

        # Generate widgets once so we can capture their refs
        clean_pts_out_widget, clean_pts_out_refs = _shp_out("Output shapefile")
        pkstat_out_widget, pkstat_out_refs = _shp_out("Output shapefile")
        psamp1_out_widget, psamp1_out_refs = _shp_out("Output Layer Sample")
        psamp2_out_widget, psamp2_out_refs = _shp_out("Output Layer 1-Sample")
        p2grid_out_widget, p2grid_out_refs = _tif_out("Output raster")
        poly2grid_out_widget, poly2grid_out_refs = _tif_out("Output raster")

        pages_cfg = [
            ("Clean Points By Raster Kernel", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Extent Coordinates (xmin,xmax,ymin,ymax)", _line_edit("e.g. 10.0, 20.0, 30.0, 40.0")),
                ("Buffer Radius (pixels)", self._spinbox(1, 100, 4)),
                ("Min Value Acceptable", self._spinbox(-9999, 9999, 3)),
                ("Output Vector Layer", clean_pts_out_refs, clean_pts_out_widget),
            ]),
            ("Attribute Table Statistics", [
                ("Input Layer (vector)", cb_stats_lyr),
                ("ID Field", cb_stats_fld),
                ("Output CSV", csv_stats_out_refs, csv_stats_out_widget),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points Kernel Statistics", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Mask Polygon Layer (vector)", self._vl_combo()),
                ("Buffer Radius (pixels)", self._spinbox(1, 100, 4)),
                ("Output Vector Layer", pkstat_out_refs, pkstat_out_widget),
            ]),
            ("Points Kernel Graphs", [
                ("Input Points Layer (vector)", cb_graphs_lyr),
                ("ID Field", cb_graphs_fld),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points Sampler", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Mask Polygon Layer (vector)", self._vl_combo()),
                ("Pixel Width", self._spinbox(1, 10000, 10)),
                ("Pixel Height", self._spinbox(1, 10000, 10)),
                ("Sample (%)", self._spinbox(1, 100, 70)),
                ("Output Layer Sample", psamp1_out_refs, psamp1_out_widget),
                ("Output Layer 1-Sample", psamp2_out_refs, psamp2_out_widget),
            ]),
            ("Points To Grid", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Reference Raster", _file_widget("Reference raster", "GeoTIFF (*.tif *.tiff)")),
                ("Extent Coordinates (xmin,xmax,ymin,ymax)", _line_edit("e.g. 10.0, 20.0, 30.0, 40.0")),
                ("Output Raster", p2grid_out_refs, p2grid_out_widget),
            ]),
            ("Poly To Grid", [
                ("Input Polygon Layer (vector)", self._vl_combo()),
                ("Pixel Width", self._spinbox(1, 10000, 10)),
                ("Pixel Height", self._spinbox(1, 10000, 10)),
                ("Output Raster", poly2grid_out_refs, poly2grid_out_widget),
            ]),
            ("Classify Field by .txt File", [
                ("Input Layer (vector)", cb_txt_lyr),
                ("Classification .txt File", _file_widget("Classes txt", "Text (*.txt)")),
                ("Field to Classify", cb_txt_fld),
                ("New Field Name", _line_edit("e.g. class_id")),
            ]),
            ("Classify Field in Quantiles", [
                ("Input Layer (vector)", cb_quant_lyr),
                ("Field to Classify", cb_quant_fld),
                ("New Field Name", _line_edit("e.g. class_id")),
                ("Number of Quantiles (4=quartiles, 10=deciles)", self._spinbox(2, 100, 10)),
            ]),
            ("Correlation Plot", [
                ("Input Layer (vector)", cb_corr_lyr),
                ("Continuous Independent Variables", corr_list),
                ("Output Folder", _folder_widget()),
            ]),
        ]

        stacked = self.stackedWidget_v
        for i, (title, params) in enumerate(pages_cfg):
            page, refs = _simple_page(title, params, f"RUN  —  {title}", "#8e44ad")
            self._dp_refs[title] = refs
            stacked.removeWidget(stacked.widget(i + 6))
            stacked.insertWidget(i + 6, page)
            refs['run_btn'].clicked.connect(
                lambda checked=False, t=title: self._run_dataprep(t))

    # ── Classify SI ──────────────────────────────────────────────────────────

    def _build_classify_tab(self):
        cb_roc_lyr = self._vl_combo()
        cb_roc_si = QgsFieldComboBox()
        cb_roc_dep = QgsFieldComboBox()
        cb_roc_lyr.layerChanged.connect(cb_roc_si.setLayer)
        cb_roc_lyr.layerChanged.connect(cb_roc_dep.setLayer)

        cb_rocw_lyr = self._vl_combo()
        cb_rocw_si = QgsFieldComboBox()
        cb_rocw_dep = QgsFieldComboBox()
        cb_rocw_w = QgsFieldComboBox()
        cb_rocw_lyr.layerChanged.connect(cb_rocw_si.setLayer)
        cb_rocw_lyr.layerChanged.connect(cb_rocw_dep.setLayer)
        cb_rocw_lyr.layerChanged.connect(cb_rocw_w.setLayer)

        cb_gen_lyr = self._vl_combo()
        cb_gen_si = QgsFieldComboBox()
        cb_gen_dep = QgsFieldComboBox()
        cb_gen_lyr.layerChanged.connect(cb_gen_si.setLayer)
        cb_gen_lyr.layerChanged.connect(cb_gen_dep.setLayer)

        cb_cm_lyr = self._vl_combo()
        cb_cm_si = QgsFieldComboBox()
        cb_cm_dep = QgsFieldComboBox()
        cb_cm_lyr.layerChanged.connect(cb_cm_si.setLayer)
        cb_cm_lyr.layerChanged.connect(cb_cm_dep.setLayer)
        
        cm_out_widget, cm_out_refs = _file_widget_temp("Output GeoPackage", "GeoPackage (*.gpkg)")

        pages_cfg = [
            ("Classify Vector by ROC", [
                ("Input Layer (vector)", cb_roc_lyr),
                ("SI Field", cb_roc_si),
                ("Dependent Variable Field", cb_roc_dep),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder", _folder_widget()),
            ]),
            ("Classify Vector by Weighted ROC", [
                ("Input Layer (vector)", cb_rocw_lyr),
                ("SI Field", cb_rocw_si),
                ("Dependent Variable Field", cb_rocw_dep),
                ("Weight Field", cb_rocw_w),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder", _folder_widget()),
            ]),
            ("ROC Generator", [
                ("Input Layer (vector)", cb_gen_lyr),
                ("SI Field", cb_gen_si),
                ("Dependent Variable Field", cb_gen_dep),
                ("Output Folder", _folder_widget()),
            ]),
            ("Confusion Matrix (FP/TN Threshold)", [
                ("Input Layer (vector)", cb_cm_lyr),
                ("SI Field", cb_cm_si),
                ("Dependent Variable Field", cb_cm_dep),
                ("Cutoff percentile (0 = Youden)", self._spinbox(0, 100, 0)),
                ("Output GeoPackage", cm_out_refs, cm_out_widget),
            ]),
        ]

        stacked = self.stackedWidget_v
        for i, (title, params) in enumerate(pages_cfg):
            page, refs = _simple_page(title, params, f"RUN  —  {title}", "#c0392b")
            self._cl_refs[title] = refs
            stacked.removeWidget(stacked.widget(i + 16))
            stacked.insertWidget(i + 16, page)
            refs['run_btn'].clicked.connect(
                lambda checked=False, t=title: self._run_classify(t))

    def _build_classify_raster_tab(self):
        cb_roc_inv = QgsMapLayerComboBox()
        cb_roc_inv.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_roc_inv.setAllowEmptyLayer(True)
        cb_roc_si = QgsMapLayerComboBox()
        cb_roc_si.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_roc_si.setAllowEmptyLayer(True)

        cb_gen_inv = QgsMapLayerComboBox()
        cb_gen_inv.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_gen_inv.setAllowEmptyLayer(True)
        cb_gen_si = QgsMapLayerComboBox()
        cb_gen_si.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_gen_si.setAllowEmptyLayer(True)

        cb_cm_inv = QgsMapLayerComboBox()
        cb_cm_inv.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_cm_inv.setAllowEmptyLayer(True)
        cb_cm_si = QgsMapLayerComboBox()
        cb_cm_si.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_cm_si.setAllowEmptyLayer(True)

        # New: Closest Point (0,1) widget pairs
        cb_cp_inv = QgsMapLayerComboBox()
        cb_cp_inv.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_cp_inv.setAllowEmptyLayer(True)
        cb_cp_si = QgsMapLayerComboBox()
        cb_cp_si.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_cp_si.setAllowEmptyLayer(True)

        # New: F1-Score widget pairs
        cb_f1_inv = QgsMapLayerComboBox()
        cb_f1_inv.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_f1_inv.setAllowEmptyLayer(True)
        cb_f1_si = QgsMapLayerComboBox()
        cb_f1_si.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_f1_si.setAllowEmptyLayer(True)

        # New: Threat Score (CSI) widget pairs
        cb_ts_inv = QgsMapLayerComboBox()
        cb_ts_inv.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_ts_inv.setAllowEmptyLayer(True)
        cb_ts_si = QgsMapLayerComboBox()
        cb_ts_si.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb_ts_si.setAllowEmptyLayer(True)

        pages_cfg = [
            ("Classify by ROC", [
                ("Landslide Inventory Raster", cb_roc_inv),
                ("SI Raster", cb_roc_si),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder (Cutoffs & Raster)", _folder_widget()),
            ]),
            ("Classify by Closest Point (0,1)", [
                ("Landslide Inventory Raster", cb_cp_inv),
                ("SI Raster", cb_cp_si),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder (Cutoffs & Raster)", _folder_widget()),
            ]),
            ("Classify by F1-Score", [
                ("Landslide Inventory Raster", cb_f1_inv),
                ("SI Raster", cb_f1_si),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder (Cutoffs & Raster)", _folder_widget()),
            ]),
            ("Classify by Threat Score (CSI)", [
                ("Landslide Inventory Raster", cb_ts_inv),
                ("SI Raster", cb_ts_si),
                ("Number of Classes (from 2 to 10)", self._spinbox(2, 10, 5)),
                ("Output Folder (Cutoffs & Raster)", _folder_widget()),
            ]),
            ("ROC Generator", [
                ("Landslide Inventory Raster", cb_gen_inv),
                ("SI Raster", cb_gen_si),
                ("Output Folder", _folder_widget()),
            ]),
            ("Confusion Matrix (FP/TN Threshold)", [
                ("Landslide Inventory Raster", cb_cm_inv),
                ("SI Raster", cb_cm_si),
                ("Cutoff percentile (0 = Youden)", self._spinbox(0, 100, 0)),
                ("Output Folder (Metrics)", _folder_widget()),
            ]),
        ]

        stacked = self.stackedWidget_r
        for i, (title, params) in enumerate(pages_cfg):
            page, refs = _simple_page(title, params, f"RUN  —  {title}", "#c0392b")
            self._cl_r_refs[title] = refs
            stacked.insertWidget(i + 6, page)
            refs['run_btn'].clicked.connect(
                lambda checked=False, t=title: self._run_classify_raster(t))

        # Rebuild the classify_list_r in the correct order.
        # The .ui file has 3 hardcoded items (ROC, ROC Generator, CM). 
        # We clear and re-add all 6 in the desired order to match the stacked widget index.
        self.classify_list_r.clear()
        for title, _ in pages_cfg:
            self.classify_list_r.addItem(title)





    def _build_classify_raster_tab2(self):
        # NOTE: This second copy was originally a duplicate. Merged into single version above (_build_classify_raster_tab).
        pass


    # ── Small widget factories ───────────────────────────────────────────────

    @staticmethod
    def _vl_combo():
        cb = QgsMapLayerComboBox()
        cb.setFilters(QgsMapLayerProxyModel.VectorLayer)
        cb.setAllowEmptyLayer(True)
        return cb

    @staticmethod
    def _spinbox(min_v, max_v, default):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(default)
        return sb

    # ── RUN slots ────────────────────────────────────────────────────────────

    def _run_raster(self, key: str, mode: str):
        """Extract values and call backend."""
        if hasattr(self, '_is_running') and self._is_running:
            return
            
        m_refs = self._raster_refs[key][mode]
        
        inv_layer = m_refs['inventory'].currentLayer()
        if not inv_layer or not inv_layer.isValid():
            QMessageBox.warning(self, "Missing input", "Please select a valid Landslide Raster Inventory.")
            return
        inventory = inv_layer.source()
        
        covariates = m_refs['covariates']._paths()
        if not covariates:
            QMessageBox.warning(self, "Missing input", "Please add at least one covariate raster.")
            return
        spin_val   = m_refs['spin'].value()

        out_raster = self._get_out_path(m_refs['output'], suffix=".tif", prefix="SI_raster_")
        out_test = self._get_out_path(m_refs['out_test'], suffix=".tif", prefix="Test_raster_")
        out_folder = self._get_out_path(m_refs['folder'], is_folder=True)

        if not out_folder:
            QMessageBox.warning(self, "Missing input", "Please select an output folder.")
            return

        algo_display = self.ALGO_NAMES[self.ALGO_KEYS_R.index(key)]
        self._set_running(f"Running {algo_display} ({mode})...")
        
        def on_finished(_):
            # Auto-load SI
            if out_raster and os.path.exists(out_raster):
                from qgis.core import QgsRasterLayer
                lyr_name = os.path.splitext(os.path.basename(out_raster))[0]
                lyr = QgsRasterLayer(out_raster, lyr_name)
                if lyr.isValid():
                    QgsProject.instance().addMapLayer(lyr)

            self._set_finished()
            QMessageBox.information(self, "Done",
                                    f"{algo_display} ({mode}) completed successfully.\n"
                                    f"Results saved to:\n{out_folder}")
            self._show_latest_roc_plot(out_folder, algo_display)
            if worker in self._workers:
                self._workers.remove(worker)

        def on_error(exc):
            self._set_finished()
            self.status_label.setText("Error during run")
            self.progress_bar.setValue(0)
            import traceback
            QMessageBox.critical(self, "Error", f"{str(exc)}")
            if worker in self._workers:
                self._workers.remove(worker)

        worker = WorkerThread(self._call_raster_backend, key, mode, inventory, covariates,
                              spin_val, out_raster, out_test, out_folder)
        worker.finished_ok.connect(on_finished)
        worker.error.connect(on_error)
        self._workers.append(worker)
        worker.start()

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
        if hasattr(self, '_is_running') and self._is_running:
            return
            
        refs   = self._vector_refs[key]
        m_refs = refs[mode]
        layer  = m_refs['layer_combo'].currentLayer()

        if not layer or not layer.isValid():
            QMessageBox.warning(self, "Missing input",
                "Please select a valid Slope Unit Vector layer.")
            return

        dep_field = m_refs['dep_combo'].currentField()
        if not dep_field:
            QMessageBox.warning(self, "Missing input",
                "Please select a Dependent Variable field.")
            return

        indep_fields = [m_refs['indep_list'].item(i).text()
                        for i in range(m_refs['indep_list'].count())
                        if m_refs['indep_list'].item(i).checkState() == Qt.Checked]
        if not indep_fields:
            QMessageBox.warning(self, "Missing input",
                "Please check at least one Independent Variable field.")
            return

        out_folder = self._get_out_path(m_refs['folder'], is_folder=True)
        if not out_folder:
            QMessageBox.warning(self, "Missing input", "Please select an output folder.")
            return

        out_test = self._get_out_path(m_refs['out_test'], suffix=".gpkg", prefix="Test_vector_")
        out_train = self._get_out_path(m_refs['out_train'], suffix=".gpkg", prefix="Train_vector_")

        algo_display = self.ALGO_NAMES[self.ALGO_KEYS_R.index(key)]
        self._set_running(f"Running {algo_display} ({mode})...")
        
        def on_finished(_):
            # Auto-load SI
            test_path = m_refs['out_test'].filePath()
            if not test_path:
                import os
                test_path = os.path.join(out_folder, 'test.gpkg')
            if os.path.exists(test_path):
                from qgis.core import QgsVectorLayer
                lyr = QgsVectorLayer(f"{test_path}|layername=test", f"{algo_display} Vector Test SI", "ogr")
                if lyr.isValid():
                    QgsProject.instance().addMapLayer(lyr)

            self._set_finished()
            QMessageBox.information(self, "Done",
                f"{algo_display} ({mode}) completed.\nResults in:\n{out_folder}")
            
            self._show_latest_roc_plot(out_folder, algo_display)
            if worker in self._workers:
                self._workers.remove(worker)

        def on_error(exc):
            self._set_finished()
            self.status_label.setText("Error during run")
            self.progress_bar.setValue(0)
            import traceback
            QMessageBox.critical(self, "Error", f"{str(exc)}")
            if worker in self._workers:
                self._workers.remove(worker)

        worker = WorkerThread(self._call_vector_backend, key, mode, layer.source(), dep_field, indep_fields, spin_val, out_test, out_train, out_folder)
        worker.finished_ok.connect(on_finished)
        worker.error.connect(on_error)
        self._workers.append(worker)
        worker.start()

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

    def _run_dataprep(self, title: str):
        refs = self._dp_refs[title]
        try:
            if title == "Clean Points By Raster Kernel":
                v_layer = refs["Input Points Layer (vector)"].currentLayer()
                r_path  = refs["Raster Kernel Layer"].filePath()
                ext_str = refs["Extent Coordinates (xmin,xmax,ymin,ymax)"].text()
                buf     = refs["Buffer Radius (pixels)"].value()
                min_val = refs["Min Value Acceptable"].value()

                out_shp = self._get_out_path(refs["Output Vector Layer"], suffix=".shp", prefix="Clean_points_")

                if not (v_layer and r_path and out_shp):
                    QMessageBox.warning(self, "Missing input", "Ensure points, raster, and output are set.")
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
                if ext_str:
                    params['exst'] = [float(x.strip()) for x in ext_str.split(',')]
                algo_mod.processAlgorithm_edu(params)
                self._auto_add_vector(out_shp)

            elif title == "Attribute Table Statistics":
                v_layer  = refs["Input Layer (vector)"].currentLayer()
                id_field = refs["ID Field"].currentField()

                out_csv = self._get_out_path(refs["Output CSV"], suffix=".csv", prefix="Attr_stats_")
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                
                if not (v_layer and id_field and out_csv and out_folder):
                    QMessageBox.warning(self, "Missing input", "All fields required.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.lsdanalysis import statistic
                alg = statistic()
                alg_params = { 'OUTPUT': out_csv, 'ID': id_field, 'INPUT2': v_layer.source(), 'PATH': out_folder }
                alg.input(alg_params)

            elif title == "Points Kernel Statistics":
                v_layer = refs["Input Points Layer (vector)"].currentLayer()
                r_path  = refs["Raster Kernel Layer"].filePath()
                m_layer = refs["Mask Polygon Layer (vector)"].currentLayer()
                buf     = refs["Buffer Radius (pixels)"].value()

                out_shp = self._get_out_path(refs["Output Vector Layer"], suffix=".shp", prefix="Kernel_stats_")

                if not (v_layer and r_path and m_layer and out_shp):
                    QMessageBox.warning(self, "Missing input", "Please provide all required inputs.")
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
                self._auto_add_vector(out_shp)

            elif title == "Points Kernel Graphs":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                field = refs["ID Field"].currentField()
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not layer or not field or not out_folder:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
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

                if not (v_pts and out1 and out2):
                    QMessageBox.warning(self, "Missing input", "Points layer and both outputs required.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.randomsampler3 import samplerAlgorithm
                alg = samplerAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT': v_pts.source(), 'INPUT1': v_poly.source(), 'w': pw, 'h': ph, 'train': samp }
                v, t, xy = alg.resampler(alg_params)
                alg.save({ 'INPUT1': out1, 'INPUT2': v, 'INPUT3': xy })
                alg.save({ 'INPUT1': out2, 'INPUT2': t, 'INPUT3': xy })
                self._auto_add_vector(out1)
                self._auto_add_vector(out2)

            elif title == "Points To Grid":
                v_layer = refs["Input Points Layer (vector)"].currentLayer()
                r_path  = refs["Reference Raster"].filePath()
                ext_str = refs["Extent Coordinates (xmin,xmax,ymin,ymax)"].text()

                out_tif = self._get_out_path(refs["Output Raster"], suffix=".tif", prefix="Pts_to_grid_")

                if not (v_layer and r_path and out_tif):
                    QMessageBox.warning(self, "Missing input", "Layer, Reference raster, output required.")
                    return
                self._set_running(f"Running {title}...")
                from qgis.core import QgsRectangle
                coords = [float(x.strip()) for x in ext_str.split(',')]
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

                if not (v_layer and out_tif):
                    QMessageBox.warning(self, "Missing input", "Polygon layer and output required.")
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
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
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
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                self._set_running(f"Running {title}...")
                from ..scripts.classcovdeciles import classcovdecAlgorithm
                alg = classcovdecAlgorithm()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'field': field, 'nome': new_f, 'num': num }
                alg.classify(alg_params)

            elif title == "Correlation Plot":
                layer = refs["Input Layer (vector)"].currentLayer()
                lw = refs["Continuous Independent Variables"]
                from qgis.PyQt.QtCore import Qt
                fields = [lw.item(i).text() for i in range(lw.count()) if lw.item(i).checkState() == Qt.Checked]
                out = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not layer or not fields or not out:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
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
            QMessageBox.information(self, "Success", f"{title} completed successfully.")
        except Exception as e:
            self.status_label.setText("Error during run")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            import traceback
            QMessageBox.critical(self, "Error", f"{str(e)}\\n{traceback.format_exc()}")

    def _run_classify(self, title: str):
        refs = self._cl_refs[title]
        layer = refs["Input Layer (vector)"].currentLayer()

        if not layer or not layer.isValid():
            QMessageBox.warning(self, "Missing input", "Please select a valid Input Layer.")
            return

        si_field = refs["SI Field"].currentField()
        dep_field = refs["Dependent Variable Field"].currentField()

        if not si_field or not dep_field:
            QMessageBox.warning(self, "Missing input", "Please select both SI and Dependent Variable Fields.")
            return

        try:
            if title == "Classify Vector by ROC":
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not out_folder:
                    QMessageBox.warning(self, "Missing input", "Please specify an Output Folder.")
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
                    'NUMBER': refs["Number of Classes"].value(),
                    'OUTPUT': out_folder
                })
                self._set_finished()
                QMessageBox.information(self, "Success", f"Classify Vector by ROC completed.\\nSaved to:\\n{out_folder}")
                
            elif title == "Classify Vector by Weighted ROC":
                w_field = refs["Weight Field"].currentField()
                if not w_field:
                    QMessageBox.warning(self, "Missing input", "Please select a Weight Field.")
                    return
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not out_folder:
                    QMessageBox.warning(self, "Missing input", "Please specify an Output Folder.")
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
                    'NUMBER': refs["Number of Classes"].value(),
                    'OUTPUT': out_folder
                })
                self._set_finished()
                QMessageBox.information(self, "Success", f"Classify Vector by Weighted ROC completed.\\nSaved to:\\n{out_folder}")

            elif title == "ROC Generator":
                out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
                if not out_folder:
                    QMessageBox.warning(self, "Missing input", "Please specify an Output Folder.")
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
                QMessageBox.information(self, "Success", f"ROC Generator completed.\\nSaved to:\\n{out_folder}")

            elif title == "Confusion Matrix (FP/TN Threshold)":
                out_gpkg = self._get_out_path(refs["Output GeoPackage"], suffix=".gpkg", prefix="Conf_matrix_")

                if not out_gpkg:
                    QMessageBox.warning(self, "Missing input", "Please specify an Output GeoPackage.")
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
                
                # Auto-load the GeoPackage
                if os.path.exists(out_gpkg):
                    from qgis.core import QgsVectorLayer
                    v_lyr = QgsVectorLayer(f"{out_gpkg}|layername=confusion_matrix", "Confusion Matrix Output", "ogr")
                    if v_lyr.isValid():
                        QgsProject.instance().addMapLayer(v_lyr)

                self._set_finished()
                QMessageBox.information(self, "Success", f"Confusion Matrix calculated.\\nSaved to:\\n{out_gpkg}")

        except Exception as e:
            self.status_label.setText("Error during run")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            import traceback
            QMessageBox.critical(self, "Error", f"{str(e)}\\n{traceback.format_exc()}")

    def _run_classify_raster(self, algo_name: str):
        if hasattr(self, '_is_running') and self._is_running:
            return

        refs = self._cl_r_refs[algo_name]
        
        inv_layer = None
        si_layer = None
        num_classes = None
        cutoff = None
        out_folder = None
        
        if algo_name == "Classify by ROC":
            inv_layer = refs["Landslide Inventory Raster"].currentLayer()
            si_layer = refs["SI Raster"].currentLayer()
            num_classes = refs["Number of Classes (from 2 to 10)"].value()
            out_folder = self._get_out_path(refs["Output Folder (Cutoffs & Raster)"], is_folder=True)
        elif algo_name == "ROC Generator":
            inv_layer = refs["Landslide Inventory Raster"].currentLayer()
            si_layer = refs["SI Raster"].currentLayer()
            out_folder = self._get_out_path(refs["Output Folder"], is_folder=True)
        elif algo_name == "Confusion Matrix (FP/TN Threshold)":
            inv_layer = refs["Landslide Inventory Raster"].currentLayer()
            si_layer = refs["SI Raster"].currentLayer()
            cutoff = refs["Cutoff percentile (0 = Youden)"].value()
            out_folder = self._get_out_path(refs["Output Folder (Metrics)"], is_folder=True)
        elif algo_name in ("Classify by Closest Point (0,1)", "Classify by F1-Score", "Classify by Threat Score (CSI)"):
            inv_layer = refs["Landslide Inventory Raster"].currentLayer()
            si_layer = refs["SI Raster"].currentLayer()
            num_classes = refs["Number of Classes (from 2 to 10)"].value()
            out_folder = self._get_out_path(refs["Output Folder (Cutoffs & Raster)"], is_folder=True)

            
        if not inv_layer or not si_layer:
            QMessageBox.warning(self, "Missing input", "Please select both Inventory and SI Rasters.")
            return
            
        if not out_folder:
            QMessageBox.warning(self, "Missing output", "Please select an output folder.")
            return

        self._set_running(f"Running {algo_name} ...")

        # Capture plain strings only – NO QGIS layer objects inside the thread closure.
        si_path  = si_layer.source()
        inv_path = inv_layer.source()
        # Freeze the values that were resolved on the main thread.
        _num_classes = num_classes
        _cutoff      = cutoff
        _out_folder  = out_folder
        _algo_name   = algo_name

        def _call_classify_raster():
            """
            Pure computation in the WorkerThread.
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
                    }

                # ── ROC Generator (no raster output) ─────────────────────────────
                elif _algo_name == "ROC Generator":
                    from ..scripts import sz_raster_utils
                    sz_raster_utils.save_roc_fit(y_true, y_scores, _out_folder, method_tag='ROC_Gen')
                    return {'out_tif': None}

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
                    return {'out_tif': None}

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

        worker = WorkerThread(_call_classify_raster)
        self._workers.append(worker)
        # _on_classify_raster_done runs on the main thread via Qt signal/slot.
        worker.finished_ok.connect(self._on_classify_raster_done)
        worker.error.connect(lambda msg: (self._set_finished(), QMessageBox.critical(self, "Error", str(msg))))
        worker.start()

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

        out_tif = result.get('out_tif')
        if not out_tif:
            # Algorithms that produce no raster (ROC Generator, Confusion Matrix)
            return

        num_classes = result.get('num_classes', 5)
        layer_name  = result.get('layer_name', "Reclassified SI")

        from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer
        from qgis.PyQt.QtGui import QColor
        import matplotlib.cm as cm

        rlayer = QgsRasterLayer(out_tif, layer_name)
        if not rlayer.isValid():
            QMessageBox.warning(self, "Layer error",
                                f"The reclassified raster could not be loaded:\n{out_tif}")
            return

        # Build colour palette (main thread – safe to use Qt colour types here)
        try:
            cmap = cm.get_cmap('RdYlGn_r')
        except Exception:
            cmap = cm.get_cmap('RdYlGn')

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
        rlayer.triggerRepaint()

    def _show_latest_roc_plot(self, folder, algo_name):
        """Find the latest modified .png in the folder and display it in a popup."""
        import glob
        pngs = glob.glob(os.path.join(folder, "*.png"))
        if not pngs:
            return
            
        latest_png = max(pngs, key=os.path.getmtime)
        
        dlg = QDialog(self)
        dlg.setWindowTitle(f"ROC Plot - {algo_name}")
        vbox = QVBoxLayout(dlg)
        
        lbl = QLabel()
        from qgis.PyQt.QtGui import QPixmap
        pix = QPixmap(latest_png)
        if pix.width() > 800 or pix.height() > 800:
            pix = pix.scaled(800, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl.setPixmap(pix)
        lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(lbl)
        
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.accept)
        vbox.addWidget(btn)
        
        dlg.exec_()
