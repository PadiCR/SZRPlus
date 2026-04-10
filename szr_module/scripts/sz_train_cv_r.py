#!/usr/bin/python
# coding=utf-8
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

sz_train_cv_r.py
-----------------
Raster-native runner: k-fold cross-validation for all methods.
Works with szr_module_provider.py Instance dispatcher (v1.1.5 architecture).
Group: 06 SI raster k-fold

Acknowledgements:
- Code logic and components entirely generated with the assistance of AI (Gemini, Claude) for the SZR+ release.
"""

__author__ = 'Cristobal A. Padilla Moreno'
__email__ = "cristobalpadilla@gmail.com"
__date__ = '2026-04-08'
__copyright__ = '(C) 2026 by Cristobal A. Padilla Moreno'

import sys, os
sys.setrecursionlimit(10000)

from qgis.core import (
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterMultipleLayers,
    QgsRasterLayer,
    QgsProcessingContext,
)
from qgis.core import *
from szr_module.scripts.sz_raster_utils import (
    write_si_raster, save_roc_kfold
)


class CoreAlgorithm_cv_r():
    """
    Raster-native runner for k-fold cross-validation mode.
    init() / process() are called by the Instance dispatcher in
    szr_module_provider.py, which injects the correct algorithm callable.
    """

    def init(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT1,
            self.tr('Inventory raster (1=landslide, 0=absence, nodata=outside)'),
            defaultValue=None))

        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.INPUT,
            self.tr('Covariate rasters (co-registered, same CRS/extent/resolution)'),
            layerType=QgsProcessing.TypeRaster,
            defaultValue=None))

        self.addParameter(QgsProcessingParameterNumber(
            self.NUMBER,
            self.tr('Number of k-folds (>=2)'),
            type=QgsProcessingParameterNumber.Integer,
            minValue=2,
            defaultValue=5))

        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT,
            self.tr('Output SI raster (average over folds)'),
            fileFilter='GeoTIFF (*.tif *.TIF)',
            defaultValue=None))

        self.addParameter(QgsProcessingParameterFileDestination(
            self.OUTPUT_TEST,
            self.tr('Output test raster [optional]'),
            fileFilter='GeoTIFF (*.tif *.TIF)',
            defaultValue=None,
            optional=True))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT3,
            self.tr('Output folder (ROC curves, weight files)'),
            defaultValue=None, createByDefault=True))

    def process(self, parameters, context, feedback, algorithm=None,
                classifier=None):
        feedback = QgsProcessingMultiStepFeedback(4, feedback)
        results  = {}

        # ── Resolve inventory raster path ──────────────────────────────
        inv_layer = self.parameterAsRasterLayer(parameters, self.INPUT1, context)
        if inv_layer is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT1))
        inv_path = inv_layer.source()

        # ── Resolve covariate raster paths ─────────────────────────────
        cov_layers = self.parameterAsLayerList(parameters, self.INPUT, context)
        if not cov_layers:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT))
        cov_paths = [lyr.source() for lyr in cov_layers]
        cov_names = [os.path.splitext(os.path.basename(p))[0]
                     for p in cov_paths]

        # ── Other parameters ───────────────────────────────────────────
        kfolds = self.parameterAsInt(parameters, self.NUMBER, context)
        si_out = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        test_out = self.parameterAsFileOutput(parameters, self.OUTPUT_TEST, context)
        folder = self.parameterAsString(parameters, self.OUTPUT3, context)
        if folder is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.OUTPUT3))
        os.makedirs(folder, exist_ok=True)

        feedback.pushInfo(f'[SZ raster] inventory: {inv_path}')
        feedback.pushInfo(f'[SZ raster] covariates: {cov_names}')
        feedback.pushInfo(f'[SZ raster] k-folds = {kfolds}')

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # ── Run algorithm ──────────────────────────────────────────────
        alg_params = {
            'inv_path':  inv_path,
            'cov_paths': cov_paths,
            'cov_names': cov_names,
            'kfolds':    kfolds,
            'folder':    folder,
        }
        feedback.pushInfo('Running k-fold algorithm …')
        out = algorithm(alg_params)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # ── Write averaged SI raster ───────────────────────────────────
        feedback.pushInfo(f'Writing averaged SI raster -> {si_out}')
        write_si_raster(out['si_pred'], out['pred_idx'],
                        out['georef'], si_out)

        # ── Write Test raster ──────────────────────────────────────────
        if test_out and 'test_indices_list' in out:
            feedback.pushInfo(f'Writing k-fold test split raster -> {test_out}')
            from szr_module.scripts.sz_raster_utils import write_test_raster_kfold
            write_test_raster_kfold(out['train_idx'], out['test_indices_list'],
                                    out['georef'], test_out)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # ── ROC curves (per fold) ──────────────────────────────────────
        import numpy as np
        y_all  = out['y_all']
        si_all = out['si_all']
        # Replace any un-predicted nan slots with 0 (safety guard)
        si_all = np.where(np.isnan(si_all), 0.0, si_all)
        save_roc_kfold(y_all, si_all, out['test_indices_list'], folder, base_stats=out.get('base_stats', None))

        feedback.setCurrentStep(4)

        # ── Load SI raster into QGIS canvas ───────────────────────────
        si_layer = QgsRasterLayer(si_out, 'SI_raster_kfold')
        if si_layer.isValid():
            context.temporaryLayerStore().addMapLayer(si_layer)
            context.addLayerToLoadOnCompletion(
                si_layer.id(),
                QgsProcessingContext.LayerDetails(
                    'SI_raster_kfold', context.project(), 'SI'))

        results['OUTPUT'] = si_out
        if test_out:
            results['OUTPUT_TEST'] = test_out
        return results
