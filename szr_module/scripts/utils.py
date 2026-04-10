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
        ax.plot(x_sr, y_sr, color='blue', lw=2, label=f'Success Rate')
        ax.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('Fraction of study area classified as positive')
        ax.set_ylabel('True Positive Rate (Correctly classified landslides)')
        
        title_sr = 'Success Rate Curve' if not prefix.startswith('test') else 'Prediction Rate Curve'
        ax.set_title(f'{title_sr}')
        ax.legend(loc="lower right")
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
        label_text = 'Complete dataset (AUC = %0.2f' % r
        if best_dis is not None:
            label_text += ', min DIS = %0.2f, max CSI = %0.2f)' % (best_dis, best_csi)
        else:
            label_text += ')'

        fig=plt.figure()
        lw = 2
        plt.plot(fpr1, tpr1, color='green',lw=lw, label=label_text)
        plt.plot([0, 1], [0, 1], color='black', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC')
        plt.legend(loc="lower right")
        
        os.makedirs(parameters['OUT'], exist_ok=True)
        fig.savefig(parameters['OUT']+'/fig_fit.png', dpi=150)
        plt.close(fig)

    def stamp_cv(parameters):
        df=parameters['df']
        test_ind=parameters['test_ind']
        y_v=df['y']
        scores_v=df['SI']
        lw = 2
        ################################figure
        fig=plt.figure()
        plt.plot([0, 1], [0, 1], color='black', lw=lw, linestyle='--')
        
        base_out = parameters['OUT']
        os.makedirs(base_out, exist_ok=True)
        
        for i in range(len(test_ind)):
            fold_dir = os.path.join(base_out, f'fold_{i}')
            os.makedirs(fold_dir, exist_ok=True)
            
            fprv, tprv, treshv = roc_curve(y_v[test_ind[i]],scores_v[test_ind[i]])
            aucv=roc_auc_score(y_v[test_ind[i]],scores_v[test_ind[i]])
            
            best_dis, best_csi = SZ_utils.export_roc_and_sr(y_v[test_ind[i]], scores_v[test_ind[i]], fold_dir, prefix=f"fold_{i}_")
            
            label_text = f'ROC fold {i} (AUC = {aucv:.2f}'
            if best_dis is not None:
                label_text += f', min DIS = {best_dis:.2f}, max CSI = {best_csi:.2f})'
            else:
                label_text += ')'
                
            print(f'ROC {i} AUC=',aucv)
            plt.plot(fprv, tprv,lw=lw, alpha=0.5, label=label_text)
            
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.legend(loc="lower right", prop={'size': 6})
        #plt.show()
        print('ROC curve figure = ',base_out+'/fig_cv.png')
        fig.savefig(os.path.join(base_out, 'fig_cv.png'), dpi=150)
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

        label_test = 'Prediction performance (AUC = %0.2f' % aucv
        if dis_v is not None:
             label_test += ', min DIS = %0.2f, max CSI = %0.2f)' % (dis_v, csi_v)
        else:
             label_test += ')'
             
        label_train = 'Success performance (AUC = %0.2f' % auct
        if dis_t is not None:
             label_train += ', min DIS = %0.2f, max CSI = %0.2f)' % (dis_t, csi_t)
        else:
             label_train += ')'

        fig=plt.figure()
        plt.plot(fprv, tprv, color='green',lw=lw, label=label_test)
        plt.plot(fprt, tprt, color='red',lw=lw, label=label_train)
        plt.plot([0, 1], [0, 1], color='black', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC')
        plt.legend(loc="lower right")
        fig.savefig(os.path.join(base_out, 'fig_simple.png'), dpi=150)
        plt.close(fig)

    def save(parameters):

        df=parameters['df']
        nomi=list(df.head())
        fields = QgsFields()

        for field in nomi:
            if field=='ID':
                fields.append(QgsField(field, QVariant.Int))
            if field=='geom':
                continue
            if field=='y':
                fields.append(QgsField(field, QVariant.Int))
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
        for i, row in df.iterrows():
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromWkt(row['geom']))
            fet.setAttributes(list(map(float,list(df.loc[ i, df.columns != 'geom']))))
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
