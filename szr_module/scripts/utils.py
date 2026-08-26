import matplotlib.pyplot as plt
from processing.algs.gdal.GdalUtils import GdalUtils
import plotly.graph_objs as go
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import pearsonr
import csv

#from pygam import LogisticGAM, s, f, terms

from qgis.core import (QgsVectorLayer,
                       QgsFields,
                       QgsField,
                       QgsProject,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsGeometry,
                       QgsProcessingContext
)
import numpy as np
import pandas as pd
from qgis.PyQt.QtCore import QVariant
import os
from collections import OrderedDict


class SZ_utils():

    def load_simple(directory,parameters):
        layer = QgsVectorLayer(parameters['INPUT_VECTOR_LAYER'], '', 'ogr')
        crs=layer.crs()
        campi=[]
        for field in layer.fields():
            campi.append(field.name())
        campi.append('geom')
        gdp=pd.DataFrame(columns=campi,dtype=float)
        features = layer.getFeatures()
        count=0
        feat=[]
        for feature in features:
            attr=feature.attributes()
            geom = feature.geometry()
            feat=attr+[geom.asWkt()]
            gdp.loc[len(gdp)] = feat
            count=+ 1
        gdp.to_csv(directory+'/file.csv')
        del gdp
        gdp=pd.read_csv(directory+'/file.csv')
        gdp['ID']=np.arange(1,len(gdp.iloc[:,0])+1)
        df=gdp[parameters['field1']]
        nomi=list(df.head())
        lsd=gdp[parameters['lsd']]
        print(parameters,'printalo')
        if parameters.get('family') == 'gaussian':
            lsd[lsd>0]=np.log(lsd[lsd>0])
            print('lsd',lsd,'lsd')
        else:
            lsd[lsd>0]=1
        df['y']=lsd#.astype(int)
        df['ID']=gdp['ID']
        df['geom']=gdp['geom']
        df=df.dropna(how='any',axis=0)
        X=[parameters['field1']]
        if parameters['testN']==0:
            train=df
            test=pd.DataFrame(columns=nomi,dtype=float)
        else:
            # split the data into train and test set
            per=int(np.ceil(df.shape[0]*parameters['testN']/100))
            train, test = train_test_split(df, test_size=per, random_state=42, shuffle=True)
        return train, test, nomi,crs,df
    
    def load_cv(directory,parameters):
        layer = QgsVectorLayer(parameters['INPUT_VECTOR_LAYER'], '', 'ogr')
        crs=layer.crs()
        campi=[]
        for field in layer.fields():
            campi.append(field.name())
        campi.append('geom')
        gdp=pd.DataFrame(columns=campi,dtype=float)
        features = layer.getFeatures()
        count=0
        feat=[]
        for feature in features:
            attr=feature.attributes()
            geom = feature.geometry()
            feat=attr+[geom.asWkt()]
            gdp.loc[len(gdp)] = feat
            count=+ 1
        gdp.to_csv(directory+'/file.csv')
        del gdp
        gdp=pd.read_csv(directory+'/file.csv')
        gdp['ID']=np.arange(1,len(gdp.iloc[:,0])+1)
        df=gdp[parameters['field1']]
        nomi=list(df.head())
        lsd=gdp[parameters['lsd']]
        lsd[lsd>0]=1
        df['y']=lsd#.astype(int)
        df['ID']=gdp['ID']
        df['geom']=gdp['geom']
        df=df.dropna(how='any',axis=0)
        return(df,nomi,crs)
    

    @staticmethod
    def export_roc_and_sr(y_true, scores, out_folder, prefix=""):
        from sklearn.metrics import roc_curve
        import numpy as np
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import os

        os.makedirs(out_folder, exist_ok=True)
        fpr, tpr, thresholds = roc_curve(y_true, scores)
        P = np.sum(y_true == 1)
        N = np.sum(y_true == 0)

        if P == 0 or N == 0:
            return None, None

        TP = tpr * P
        FN = P - TP
        FP = fpr * N
        TN = N - FP

        DIS = np.sqrt((1 - tpr)**2 + fpr**2)
        
        CSI = np.zeros_like(TP, dtype=float)
        valid = (TP + FP + FN) > 0
        CSI[valid] = TP[valid] / (TP[valid] + FP[valid] + FN[valid])

        df_roc = pd.DataFrame({
            'Threshold': thresholds,
            'TPR': tpr,
            'FPR': fpr,
            'TP': TP,
            'FP': FP,
            'TN': TN,
            'FN': FN,
            'DIS': DIS,
            'CSI': CSI
        })
        df_roc.to_csv(os.path.join(out_folder, f'{prefix}ROC_data.csv'), index=False)

        x_sr = (TP + FP) / (P + N)
        y_sr = tpr
        df_sr = pd.DataFrame({
            'Threshold': thresholds,
            'Fraction_Positive_Area': x_sr,
            'TPR': y_sr
        })
        df_sr.to_csv(os.path.join(out_folder, f'{prefix}SuccessRate_data.csv'), index=False)

        fig, ax = plt.subplots()
        line_sr, = ax.plot(x_sr, y_sr, color='blue', lw=2)
        ax.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('Fraction of study area classified as positive')
        ax.set_ylabel('True Positive Rate (Correctly classified landslides)')
        
        title_sr = 'Success Rate Curve' if not prefix.startswith('test') else 'Prediction Rate Curve'
        ax.set_title(f'{title_sr}')
        leg = ax.legend(
            [line_sr], ['Success Rate'],
            loc='lower right',
            bbox_to_anchor=(0.99, 0.03),
            bbox_transform=ax.transAxes,
            fontsize=8.5, framealpha=0.92, edgecolor='gray',
        )
        leg.set_clip_on(False)
        fig.savefig(os.path.join(out_folder, f'{prefix}fig_success_rate.png'), dpi=150)
        plt.close(fig)

        best_dis_idx = np.argmin(DIS)
        best_csi_idx = np.argmax(CSI)
        return DIS[best_dis_idx], CSI[best_csi_idx]

    def stampfit(parameters):
        df=parameters['df']
        y_true=df['y']
        scores=df['SI']
        ################################figure
        fpr1, tpr1, tresh1 = roc_curve(y_true,scores)
        norm=(scores-scores.min())/(scores.max()-scores.min())
        r=roc_auc_score(y_true, scores)
        
        best_dis, best_csi = SZ_utils.export_roc_and_sr(y_true, scores, parameters['OUT'], prefix="fit_")
        if best_dis is not None:
            label_text = 'Complete: AUC=%.2f, DIS=%.2f, CSI=%.2f' % (r, best_dis, best_csi)
        else:
            label_text = 'Complete: AUC=%.2f' % r

        fig, ax = plt.subplots()
        lw = 2
        line1, = ax.plot(fpr1, tpr1, color='green', lw=lw)
        ax.plot([0, 1], [0, 1], color='black', lw=lw, linestyle='--')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC')
        ax.legend(
            [line1], [label_text],
            loc='lower right',
            fontsize=8.5, framealpha=0.92, edgecolor='gray'
        )
        
        os.makedirs(parameters['OUT'], exist_ok=True)
        fig.savefig(parameters['OUT']+'/fig_fit.png', dpi=150, bbox_inches='tight')
        plt.close(fig)

    def stamp_cv(parameters):
        df=parameters['df']
        test_ind=parameters['test_ind']
        y_v=df['y']
        scores_v=df['SI']
        lw = 2
        ################################figure
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color='black', lw=lw, linestyle='--')
        
        base_out = parameters['OUT']
        os.makedirs(base_out, exist_ok=True)
        
        lines = []
        labels = []
        for i in range(len(test_ind)):
            fold_dir = os.path.join(base_out, f'fold_{i}')
            os.makedirs(fold_dir, exist_ok=True)
            
            fprv, tprv, treshv = roc_curve(y_v[test_ind[i]],scores_v[test_ind[i]])
            aucv=roc_auc_score(y_v[test_ind[i]],scores_v[test_ind[i]])
            
            best_dis, best_csi = SZ_utils.export_roc_and_sr(y_v[test_ind[i]], scores_v[test_ind[i]], fold_dir, prefix=f"fold_{i}_")
            
            if best_dis is not None:
                label_text = 'Fold %d: AUC=%.2f, DIS=%.2f, CSI=%.2f' % (i, aucv, best_dis, best_csi)
            else:
                label_text = 'Fold %d: AUC=%.2f' % (i, aucv)
                
            print(f'ROC {i} AUC=',aucv)
            line, = ax.plot(fprv, tprv, lw=lw, alpha=0.5)
            lines.append(line)
            labels.append(label_text)
            
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        if lines:
            ax.legend(lines, labels, loc='lower right', fontsize=7, framealpha=0.92, edgecolor='gray')
        print('ROC curve figure = ',base_out+'/fig_cv.png')
        fig.savefig(os.path.join(base_out, 'fig_cv.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    
    def stamp_simple(parameters):
        train=parameters['train']
        y_t=train['y']
        scores_t=train['SI']

        test=parameters['test']
        y_v=test['y']
        scores_v=test['SI']
        lw = 2
        
        fprv, tprv, treshv = roc_curve(y_v,scores_v)
        fprt, tprt, tresht = roc_curve(y_t,scores_t)

        aucv=roc_auc_score(y_v, scores_v)
        auct=roc_auc_score(y_t, scores_t)
        normt=(scores_t-scores_t.min())/(scores_t.max()-scores_t.min())
        normv=(scores_v-scores_v.min())/(scores_v.max()-scores_v.min())
        
        base_out = parameters['OUT']
        os.makedirs(base_out, exist_ok=True)
        
        dis_v, csi_v = SZ_utils.export_roc_and_sr(y_v, scores_v, base_out, prefix="test_")
        dis_t, csi_t = SZ_utils.export_roc_and_sr(y_t, scores_t, base_out, prefix="train_")

        if dis_v is not None:
            label_test = 'Prediction: AUC=%.2f, DIS=%.2f, CSI=%.2f' % (aucv, dis_v, csi_v)
        else:
            label_test = 'Prediction: AUC=%.2f' % aucv
             
        if dis_t is not None:
            label_train = 'Success:    AUC=%.2f, DIS=%.2f, CSI=%.2f' % (auct, dis_t, csi_t)
        else:
            label_train = 'Success:    AUC=%.2f' % auct

        fig, ax = plt.subplots()
        line_v, = ax.plot(fprv, tprv, color='green', lw=lw)
        line_t, = ax.plot(fprt, tprt, color='red',   lw=lw)
        ax.plot([0, 1], [0, 1], color='black', lw=lw, linestyle='--')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC')
        ax.legend(
            [line_v, line_t], [label_test, label_train],
            loc='lower right',
            fontsize=8.5, framealpha=0.92, edgecolor='gray'
        )
        fig.savefig(os.path.join(base_out, 'fig_simple.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    def save(parameters):

        df=parameters['df']
        nomi=list(df.head())
        fields = QgsFields()

        for field in nomi:
            if field=='geom':
                continue
            if field=='ID' or field=='y':
                fields.append(QgsField(field, QVariant.Int))
            elif df[field].dtype==object:
                fields.append(QgsField(field, QVariant.String))
            else:
                fields.append(QgsField(field, QVariant.Double))

        transform_context = QgsProject.instance().transformContext()
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = 'GPKG'
        save_options.fileEncoding = 'UTF-8'

        writer = QgsVectorFileWriter.create(
          parameters['OUT'],
          fields,
          QgsWkbTypes.Polygon,
          parameters['crs'],
          transform_context,
          save_options
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ",  writer.errorMessage())
        cols=[c for c in df.columns if c!='geom']
        for i, row in df.iterrows():
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromWkt(row['geom']))
            fet.setAttributes([row[c] if isinstance(row[c],str) else float(row[c]) for c in cols])
            writer.addFeature(fet)

        del writer

    def addmap(parameters):
        context=parameters()
        fileName = parameters['trainout']
        layer = QgsVectorLayer(fileName,"train","ogr")
        subLayers =layer.dataProvider().subLayers()

        for subLayer in subLayers:
            name = subLayer.split('!!::!!')[1]
            uri = "%s|layername=%s" % (fileName, name,)
            # Create layer
            sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
            if not sub_vlayer.isValid():
                print('layer failed to load')
            # Add layer to map
            context.temporaryLayerStore().addMapLayer(sub_vlayer)
            context.addLayerToLoadOnCompletion(sub_vlayer.id(), QgsProcessingContext.LayerDetails('layer', context.project(),'LAYER'))


    def errors(parameters):
        df=parameters['df']
        nomi=list(df.head())
        y=df['y']
        predic=df['SI']
        min_absolute_error = np.min(np.abs(y - predic))
        rmse = np.sqrt(mean_squared_error(y, predic))
        r_squared = r2_score(y, predic)
        pearson_coefficient, _ = pearsonr(y, predic)
        errors=[min_absolute_error,rmse,r_squared,pearson_coefficient]

        output_file = parameters['file']

        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(["Metric", "Value"])
            # Write data
            writer.writerow(["Minimum Absolute Error", min_absolute_error])
            writer.writerow(["RMSE", rmse])
            writer.writerow(["R-squared", r_squared])
            writer.writerow(["Pearson Coefficient", pearson_coefficient])
        return(errors)
