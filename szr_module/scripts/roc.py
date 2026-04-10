# -*- coding: utf-8 -*-

"""
/***************************************************************************
    rocAlgorithm
        begin                : 2021-11
        copyright            : (C) 2021 by Giacomo Titti,
                               Padova, November 2021
        email                : giacomotitti@gmail.com
 ***************************************************************************/

/***************************************************************************
    rocAlgorithm
    Copyright (C) 2021 by Giacomo Titti, Padova, November 2021

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
 ***************************************************************************/
"""

__author__ = 'Giacomo Titti, Cristobal A. Padilla Moreno'
__email__ = "cristobalpadilla@gmail.com"
__date__ = '2021-11-01'
__copyright__ = '(C) 2021 by Giacomo Titti, (C) 2026 by Cristobal A. Padilla Moreno'

# Acknowledgements:
# - UI layout initially designed with Qt Designer.
# - Code logic and algorithms partially authored with the assistance of AI (Gemini, Claude).

__author__ = 'Giacomo Titti, Cristobal A. Padilla Moreno'
__email__ = "cristobalpadilla@gmail.com"
__date__ = '2021-07-01'
__copyright__ = '(C) 2021 by Giacomo Titti, (C) 2026 by Cristobal A. Padilla Moreno'

# Acknowledgements:
# - UI layout initially designed with Qt Designer.
# - Code logic and algorithms partially authored with the assistance of AI (Gemini, Claude).

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsMessageLog,
                       Qgis,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterVectorLayer)
from qgis import processing
#import jenkspy
from osgeo import gdal,ogr
import numpy as np
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import roc_auc_score
import math
import operator
import matplotlib.pyplot as plt
import tempfile

class rocAlgorithm(QgsProcessingAlgorithm):
    INPUT1 = 'lsi'
    INPUT2 = 'lsd'
    NUMBER = 'classes'
    OUTPUT1 = 'OUTPUT1'
    OUTPUT2 = 'OUTPUT2'
    OUTPUT3 = 'OUTPUT3'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return rocAlgorithm()

    def name(self):
        return 'classy raster'

    def displayName(self):
        return self.tr('02 Classify Raster')

    def group(self):
        return self.tr('Raster analysis')

    def groupId(self):
        return 'Raster analysis'

    def shortHelpString(self):
        return self.tr("Apply different kind of classificator to raster: Jenks Natural Breaks, Equal Interval")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT1, self.tr('LSI'), defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT1, 'edgesJenks', '*.txt', defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT2, 'edgesEqual', '*.txt', defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT3, 'edgesGA', '*.txt', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber(self.NUMBER, self.tr('number of classes'), type=QgsProcessingParameterNumber.Integer, defaultValue = None,  minValue=0))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT2, self.tr('Landslides'), types=[QgsProcessing.TypeVectorPoint], defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        self.f=tempfile.gettempdir()
        #parameters['classes']=5
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        parameters['lsi'] = self.parameterAsRasterLayer(parameters, self.INPUT1, context).source()
        if parameters['lsi'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT1))

        source= self.parameterAsVectorLayer(parameters, self.INPUT2, context)
        parameters['lsd']=source.source()
        if parameters['lsd'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT2))

        parameters['edgesJenks'] = self.parameterAsFileOutput(parameters, self.OUTPUT1, context)
        if parameters['edgesJenks'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT1))

        parameters['edgesEqual'] = self.parameterAsFileOutput(parameters, self.OUTPUT2, context)
        if parameters['edgesEqual'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT2))

        parameters['edgesGA'] = self.parameterAsFileOutput(parameters, self.OUTPUT3, context)
        if parameters['edgesGA'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT3))

        parameters['classes'] = self.parameterAsEnum(parameters, self.NUMBER, context)
        if parameters['classes'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.NUMBER))


        #QgsMessageLog.logMessage(parameters['lsi'], 'MyPlugin', level=Qgis.Info)
        #QgsMessageLog.logMessage(parameters['lsi'], 'MyPlugin', level=Qgis.Info)
        # Input
        alg_params = {
            'INPUT': parameters['lsi']
        }
        outputs['open']=self.raster2array(alg_params)
        #list_of_values=list(np.arange(10))
        self.list_of_values=outputs['open'][outputs['open']>-9999].reshape(-1)
        QgsMessageLog.logMessage(str(len(self.list_of_values)), 'MyPlugin', level=Qgis.Info)

        alg_params = {
            'OUTPUT': parameters['edgesEqual'],
            'NUMBER': parameters['classes']
        }
        #outputs['equal']=self.equal(alg_params)

        alg_params = {
            'INPUT': parameters['lsd']
        }
        b=self.vector2array(alg_params)
        outputs['inv'] = b.astype(int)

        alg_params = {
            'INPUT1': outputs['open'],
            'INPUT2': outputs['inv'],
            'NUMBER': parameters['classes'],
            'OUTPUT': parameters['edgesGA']
        }
        outputs['ga']=self.classy(alg_params)

        alg_params = {
            'OUTPUT': parameters['edgesJenks'],
            'NUMBER': parameters['classes']
        }
        #outputs['jenk']=self.jenk(alg_params)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        return results

    def raster2array(self,parameters):
        self.ds22 = gdal.Open(parameters['INPUT'])
        if self.ds22 is None:#####################verify empty row input
            #QgsMessageLog.logMessage("ERROR: can't open raster input", tag="WoE")
            raise ValueError  # can't open raster input, see 'WoE' Log Messages Panel
        self.gt=self.ds22.GetGeoTransform()
        self.xsize = self.ds22.RasterXSize
        self.ysize = self.ds22.RasterYSize
        #print(w,h,xmin,xmax,ymin,ymax,self.xsize,self.ysize)
        band = self.ds22.GetRasterBand(1)
        matrix = band.ReadAsArray()
        self.ds22 = None # Close dataset
        return matrix

    def jenk(self,parameters):
        breaks = jenkspy.jenks_breaks(self.list_of_values, nb_class=parameters['NUMBER'])
        QgsMessageLog.logMessage(str(breaks), 'ClassyLSI', level=Qgis.Info)
        np.savetxt(parameters['OUTPUT'], breaks, delimiter=",")

    def equal(self,parameters):
        interval=(np.max(self.list_of_values)-np.min(self.list_of_values))/parameters['NUMBER']
        QgsMessageLog.logMessage(str(interval), 'ClassyLSI', level=Qgis.Info)
        edges=[]
        for i in range(parameters['NUMBER']):
            QgsMessageLog.logMessage(str(i), 'ClassyLSI', level=Qgis.Info)
            edges=np.append(edges,np.min(self.list_of_values)+(i*interval))
        edges=np.append(edges,np.max(self.list_of_values))
        np.savetxt(parameters['OUTPUT'], edges, delimiter=",")


    def classy(self,parameters):
        """
        Optimized version using histograms to speed up the GA optimization.
        Instead of millions of pixels, we optimize over 2000 bins.
        """
        self.numOff = 50 
        self.Off = 50
        
        self.matrix = np.reshape(parameters['INPUT1'], -1).astype(np.float32)
        self.inventory = np.reshape(parameters['INPUT2'], -1).astype(np.int8)
        
        # Single pass for valid indices
        idx = np.where((self.matrix != -9999.) & (~np.isnan(self.matrix)))[0]
        self.y_scores = self.matrix[idx]
        self.y_true = np.where(self.inventory[idx] > 0, 1, 0)
        
        nclasses = parameters['NUMBER']
        M = np.max(self.y_scores)
        m = np.min(self.y_scores)
        
        # --- Pre-summarize data into bins ---
        num_bins = 2000
        hist_p, edges = np.histogram(self.y_scores[self.y_true == 1], bins=num_bins, range=(m, M))
        hist_n, _ = np.histogram(self.y_scores[self.y_true == 0], bins=num_bins, range=(m, M))
        
        total_p = float(np.sum(hist_p))
        total_n = float(np.sum(hist_n))
        
        # Cumulative distributions (count of pixels < edge)
        cum_p = np.concatenate(([0], np.cumsum(hist_p)))
        cum_n = np.concatenate(([0], np.cumsum(hist_n)))
        
        def calc_auc_bins(C):
            # C: list of cutoff values [m, c1, c2, ..., M+1]
            # bin_idx: indices in 'edges' array
            bin_idx = np.searchsorted(edges, C, side='left')
            bin_idx = np.clip(bin_idx, 0, num_bins)
            
            # P(score >= C) = total - P(score < C)
            tp_counts = total_p - cum_p[bin_idx]
            fp_counts = total_n - cum_n[bin_idx]
            
            # Rates (cumulative from top class down)
            # tpr array: [1.0, ..., 0.0] as C goes from m to M+1
            tpr_c = tp_counts / total_p if total_p > 0 else tp_counts * 0
            fpr_c = fp_counts / total_n if total_n > 0 else fp_counts * 0
            
            # trapz expects x to be sorted
            # Reversed arrays to go from 0.0 to 1.0 (cutoff M+1 to m)
            return np.trapz(tpr_c[::-1], fpr_c[::-1])

        # --- GA Optimization loop ---
        fitness = 0
        best_cutoffs = []
        
        population = {}
        for pop in range(self.numOff):
            ran = np.sort(np.random.random_sample(nclasses-1) * (M-m))
            population[pop] = np.hstack((m, m + ran, M + 1))
            
        for gen in range(self.Off):
            roc_auc = {}
            for k in range(self.numOff):
                roc_auc[k] = calc_auc_bins(population[k])
            
            # Identify best
            current_best_idx = max(roc_auc, key=roc_auc.get)
            if roc_auc[current_best_idx] > fitness:
                fitness = roc_auc[current_best_idx]
                best_cutoffs = population[current_best_idx]
                
            # Selection and Mutation (Tournament-style per block of 5)
            new_population = {}
            for block_start in range(0, self.numOff, 5):
                # 1. Selection
                block_items = list(roc_auc.items())[block_start : block_start+5]
                sorted_block = sorted(block_items, key=lambda x: x[1], reverse=True)
                
                parent = population[sorted_block[0][0]]
                new_population[block_start] = parent
                
                # 2. Mutation for offspring
                for off_idx in range(1, 5):
                    # Pick a random boundary to mutate (everything except first/last)
                    mut_idx = np.random.randint(1, nclasses) 
                    
                    offspring = parent.copy()
                    # Boundary values
                    limit_low = offspring[mut_idx - 1]
                    limit_high = offspring[mut_idx + 1]
                    
                    # Randomly move within constraints
                    offspring[mut_idx] = limit_low + np.random.random() * (limit_high - limit_low)
                    new_population[block_start + off_idx] = offspring
            
            population = new_population

        self.classes = best_cutoffs
        np.savetxt(parameters['OUTPUT'], self.classes, delimiter=',')
        
        # Cleanup
        self.matrix = None
        self.inventory = None
        self.y_scores = None
        self.y_true = None

    def vector2array(self,parameters):
        inn=parameters['INPUT']
        w=self.gt[1]
        h=self.gt[5]
        xmin=self.gt[0]
        ymax=self.gt[3]
        xmax=xmin+(self.xsize*w)
        ymin=ymax+(self.ysize*h)

        pxlw=w
        pxlh=h
        xm=xmin
        ym=ymin
        xM=xmax
        yM=ymax
        sizex=self.xsize
        sizey=self.ysize

        driverd = ogr.GetDriverByName('ESRI Shapefile')
        ds9 = driverd.Open(inn)
        layer = ds9.GetLayer()
        count=0
        for feature in layer:
            count+=1
            geom = feature.GetGeometryRef()
            xy=np.array([geom.GetX(),geom.GetY()])
            try:
                XY=np.vstack((XY,xy))
            except:
                XY=xy
        size=np.array([pxlw,pxlh])
        OS=np.array([xm,yM])
        NumPxl=(np.ceil(abs((XY-OS)/size)-1))#from 0 first cell
        valuess=np.zeros((sizey,sizex),dtype='int16')
        try:
            for i in range(count):
                #print(i,'i')
                if XY[i,1]<yM and XY[i,1]>ym and XY[i,0]<xM and XY[i,0]>xm:
                    valuess[NumPxl[i,1].astype(int),NumPxl[i,0].astype(int)]=1
        except:#only 1 feature
            if XY[1]<yM and XY[1]>ym and XY[0]<xM and XY[0]>xm:
                valuess[NumPxl[1].astype(int),NumPxl[0].astype(int)]=1
        fuori = valuess.astype('float32')
        ds9 = None # Close OR dataset
        return fuori
