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

sz_raster_utils.py
------------------
Shared raster I/O and array utilities for the raster-native SZ algorithms.

All training scripts in the 'SI raster' group import from this module.

Acknowledgements:
- Code logic and components entirely generated with the assistance of AI (Gemini, Claude) for the SZR+ release.
"""

__author__ = 'Cristobal A. Padilla Moreno'
__email__ = "cristobalpadilla@gmail.com"
__date__ = '2026-04-08'
__copyright__ = '(C) 2026 by Cristobal A. Padilla Moreno'

import os
import math
import numpy as np
from osgeo import gdal, osr
from qgis.core import QgsProcessingException

NODATA_OUT = -9999.0


# ─────────────────────────────────────────────────────────────────────────────
# 1. Alignment validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_alignment(paths):
    """
    Check that all rasters in *paths* share the same:
      • pixel size and origin (GeoTransform)
      • number of rows and columns
    Raises QgsProcessingException if any mismatch is found.
    Returns (rows, cols, geotransform, projection_wkt) of the reference raster.

    NOTE: CRS equality is NOT strictly checked here because WKT comparison can
    diverge even for identical CRS.  Users are responsible for pre-aligning.
    """
    if not paths:
        raise QgsProcessingException("No raster paths provided.")

    ref_ds = gdal.Open(paths[0])
    if ref_ds is None:
        raise QgsProcessingException(f"Cannot open raster: {paths[0]}")
    ref_gt    = ref_ds.GetGeoTransform()
    ref_rows  = ref_ds.RasterYSize
    ref_cols  = ref_ds.RasterXSize
    ref_proj  = ref_ds.GetProjection()
    ref_ds    = None   # close

    for p in paths[1:]:
        ds = gdal.Open(p)
        if ds is None:
            raise QgsProcessingException(f"Cannot open raster: {p}")
        gt   = ds.GetGeoTransform()
        rows = ds.RasterYSize
        cols = ds.RasterXSize
        ds = None

        # Check pixel size (within floating-point tolerance)
        if (abs(gt[1] - ref_gt[1]) > 1e-6 or
                abs(gt[5] - ref_gt[5]) > 1e-6):
            raise QgsProcessingException(
                f"Pixel size mismatch between:\n  {paths[0]}\n  {p}\n"
                "Please re-sample / align all rasters to the same grid before running."
            )
        # Check extent origin
        if (abs(gt[0] - ref_gt[0]) > 1e-3 or
                abs(gt[3] - ref_gt[3]) > 1e-3):
            raise QgsProcessingException(
                f"Raster origin mismatch between:\n  {paths[0]}\n  {p}\n"
                "Please clip / align all rasters to the same extent."
            )
        # Check dimensions
        if rows != ref_rows or cols != ref_cols:
            raise QgsProcessingException(
                f"Raster size mismatch between:\n  {paths[0]}\n  {p}\n"
                f"  ({ref_rows}x{ref_cols} vs {rows}x{cols})\n"
                "Please clip / align all rasters to the same extent."
            )

    return ref_rows, ref_cols, ref_gt, ref_proj


# ─────────────────────────────────────────────────────────────────────────────
# 2. Reading rasters
# ─────────────────────────────────────────────────────────────────────────────

def read_raster_band(path):
    """
    Open a single-band raster and return:
      arr     : float32 numpy 2-D array with nodata pixels -> np.nan
      nodata  : the GDAL nodata value (or NODATA_OUT if not set)
    """
    ds = gdal.Open(path)
    if ds is None:
        raise QgsProcessingException(f"Cannot open raster: {path}")
    band = ds.GetRasterBand(1)
    nodataval = band.GetNoDataValue()
    arr = band.ReadAsArray().astype(np.float32)
    ds = None   # close GDAL dataset

    if nodataval is not None:
        arr[arr == nodataval] = np.nan
    else:
        # fallback: treat very negative sentinel as nodata
        arr[arr <= NODATA_OUT] = np.nan
    return arr


def load_rasters(paths):
    """
    Load a list of single-band GeoTIFFs (already validated with
    validate_alignment) into a single 3-D stack.

    Returns
    -------
    stack   : np.ndarray, shape (N, rows, cols), float32, nodata -> nan
    georef  : dict with keys 'gt', 'proj', 'rows', 'cols'
    """
    rows, cols, gt, proj = validate_alignment(paths)
    stack = np.full((len(paths), rows, cols), np.nan, dtype=np.float32)
    for i, p in enumerate(paths):
        stack[i] = read_raster_band(p)
    georef = {'gt': gt, 'proj': proj, 'rows': rows, 'cols': cols}
    return stack, georef


# ─────────────────────────────────────────────────────────────────────────────
# 3. Building training arrays
# ─────────────────────────────────────────────────────────────────────────────

def get_training_pixels(inv_path, cov_stack, georef):
    """
    Extract pixels that are valid for training.

    Valid training pixel = inventory is 0 or 1 (not nan)
                           AND all covariate values are finite.

    Parameters
    ----------
    inv_path  : str     - path to binary inventory raster (1/0/nodata)
    cov_stack : ndarray - shape (N, rows, cols) from load_rasters()
    georef    : dict

    Returns
    -------
    X_train   : ndarray (n_train, N)   - covariate values at training pixels
    y_train   : ndarray (n_train,)     - 0 or 1
    train_idx : ndarray (n_train,)     - flat pixel indices in [0, rows*cols)
    """
    inv = read_raster_band(inv_path)

    # Valid inventory mask:  0 or 1 (not nodata/nan)
    inv_mask = np.isfinite(inv)

    # Valid covariate mask: all bands finite
    cov_mask = np.all(np.isfinite(cov_stack), axis=0)   # (rows, cols)

    combined_mask = inv_mask & cov_mask   # (rows, cols)

    flat_mask   = combined_mask.ravel()
    train_idx   = np.where(flat_mask)[0]

    inv_flat    = inv.ravel()
    cov_flat    = cov_stack.reshape(cov_stack.shape[0], -1).T   # (n_pixels, N)

    X_train = cov_flat[train_idx]
    y_train = inv_flat[train_idx]
    y_train = (y_train > 0).astype(np.float32)   # binarise (any >0 -> 1)

    if len(train_idx) == 0:
        raise QgsProcessingException(
            "No valid training pixels found. "
            "Check that the inventory and covariate rasters overlap "
            "and that there are non-nodata cells in both."
        )
    return X_train, y_train, train_idx


def get_prediction_pixels(cov_stack):
    """
    Extract all pixels where ALL covariate bands are finite (for full-area SI).

    Returns
    -------
    X_pred    : ndarray (m, N)   - covariate values
    pred_idx  : ndarray (m,)     - flat pixel indices
    """
    cov_mask = np.all(np.isfinite(cov_stack), axis=0)   # (rows, cols)
    flat_mask = cov_mask.ravel()
    pred_idx  = np.where(flat_mask)[0]
    cov_flat  = cov_stack.reshape(cov_stack.shape[0], -1).T   # (n, N)
    X_pred    = cov_flat[pred_idx]
    return X_pred, pred_idx


# ─────────────────────────────────────────────────────────────────────────────
# 4. Writing the SI raster
# ─────────────────────────────────────────────────────────────────────────────

def write_si_raster(si_flat, pred_idx, georef, out_path):
    """
    Reconstruct a full 2-D SI raster from flat predictions and write GeoTIFF.

    Parameters
    ----------
    si_flat  : ndarray (m,)    - SI values, one per prediction pixel
    pred_idx : ndarray (m,)    - flat pixel indices (from get_prediction_pixels)
    georef   : dict            - 'gt', 'proj', 'rows', 'cols'
    out_path : str             - destination .tif path
    """
    rows = georef['rows']
    cols = georef['cols']
    si_2d = np.full((rows, cols), NODATA_OUT, dtype=np.float32)
    si_2d.ravel()[pred_idx] = si_flat.astype(np.float32)

    import sys
    print(f'[SZ-DEBUG] si_flat len: {len(si_flat)}, pred_idx len: {len(pred_idx)}', file=sys.stderr)
    try:
        valid_si = si_flat[np.isfinite(si_flat)]
        print(f'[SZ-DEBUG] si_flat min: {valid_si.min()}, max: {valid_si.max()}, mean: {valid_si.mean()}', file=sys.stderr)
    except: pass

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    driver   = gdal.GetDriverByName('GTiff')
    out_ds   = driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)
    if out_ds is None:
        raise QgsProcessingException(f"Cannot create output raster: {out_path}")
    out_ds.SetGeoTransform(georef['gt'])
    out_ds.SetProjection(georef['proj'])
    band = out_ds.GetRasterBand(1)
    band.SetNoDataValue(NODATA_OUT)
    band.WriteArray(si_2d)
    band.FlushCache()
    out_ds = None   # flush and close

def write_test_raster_simple(train_idx, idx_tr, idx_te, georef, out_path):
    '''
    Reconstruct a 2-D raster mapping train and test pixels.
    Pixels from idx_tr will have value 0, and pixels from idx_te will have value 1.
    Remaining pixels have NoData.

    Parameters
    ----------
    train_idx : ndarray (n,)    - indices of all valid training pixels in flat array
    idx_tr    : ndarray (tr,)   - train indices (subset of train_idx)
    idx_te    : ndarray (te,)   - test indices (subset of train_idx)
    georef    : dict            - gt, proj, rows, cols
    out_path  : str             - destination .tif path
    '''
    rows = georef['rows']
    cols = georef['cols']
    test_2d = np.full((rows, cols), NODATA_OUT, dtype=np.float32)
    flat = test_2d.ravel()
    
    # Set train split map to 0
    flat[train_idx[idx_tr]] = 0.0
    # Set test split map to 1
    flat[train_idx[idx_te]] = 1.0

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    driver   = gdal.GetDriverByName('GTiff')
    out_ds   = driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)
    if out_ds is None:
        raise QgsProcessingException(f"Cannot create output raster: {out_path}")
    out_ds.SetGeoTransform(georef['gt'])
    out_ds.SetProjection(georef['proj'])
    band = out_ds.GetRasterBand(1)
    band.SetNoDataValue(NODATA_OUT)
    band.WriteArray(test_2d)
    band.FlushCache()
    out_ds = None   # flush and close

def write_test_raster_kfold(train_idx, test_indices_list, georef, out_path):
    '''
    Reconstruct a 2-D raster mapping k-fold splits.
    Pixels belonging to fold i will have value i + 1.
    Remaining pixels have NoData.

    Parameters
    ----------
    train_idx         : ndarray (n,)    - indices of all valid training pixels in flat array
    test_indices_list : list of ndarray - test indices for each fold (subsets of train_idx)
    georef            : dict            - gt, proj, rows, cols
    out_path          : str             - destination .tif path
    '''
    rows = georef['rows']
    cols = georef['cols']
    test_2d = np.full((rows, cols), NODATA_OUT, dtype=np.float32)
    flat = test_2d.ravel()
    
    # Set fold membership to i+1
    for i, fold_idx in enumerate(test_indices_list):
        flat[train_idx[fold_idx]] = float(i + 1)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    driver   = gdal.GetDriverByName('GTiff')
    out_ds   = driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)
    if out_ds is None:
        raise QgsProcessingException(f"Cannot create output raster: {out_path}")
    out_ds.SetGeoTransform(georef['gt'])
    out_ds.SetProjection(georef['proj'])
    band = out_ds.GetRasterBand(1)
    band.SetNoDataValue(NODATA_OUT)
    band.WriteArray(test_2d)
    band.FlushCache()
    out_ds = None   # flush and close
# 5. ROC / AUC plotting helpers
# ─────────────────────────────────────────────────────────────────────────────

def _export_roc_and_sr(y_true, scores, out_folder, prefix="", extra_stats=None):
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
    
    if extra_stats:
        stats_keys = list(extra_stats.keys())
        stats_vals = list(extra_stats.values())
        # Pad with empty strings to match DataFrame length
        padded_keys = stats_keys + [''] * (len(df_roc) - len(stats_keys)) if len(df_roc) > len(stats_keys) else stats_keys[:len(df_roc)]
        padded_vals = stats_vals + [''] * (len(df_roc) - len(stats_vals)) if len(df_roc) > len(stats_vals) else stats_vals[:len(df_roc)]
        df_roc['Stat_Name'] = padded_keys
        df_roc['Stat_Value'] = padded_vals

    df_roc.to_csv(os.path.join(out_folder, f'{prefix}ROC_data.csv'), index=False)

    x_sr = (TP + FP) / (P + N)
    y_sr = tpr
    df_sr = pd.DataFrame({
        'Threshold': thresholds,
        'Fraction_Positive_Area': x_sr,
        'TPR': y_sr
    })

    if extra_stats:
        # Pad strings again for the SR dataframe
        padded_keys_sr = stats_keys + [''] * (len(df_sr) - len(stats_keys)) if len(df_sr) > len(stats_keys) else stats_keys[:len(df_sr)]
        padded_vals_sr = stats_vals + [''] * (len(df_sr) - len(stats_vals)) if len(df_sr) > len(stats_vals) else stats_vals[:len(df_sr)]
        df_sr['Stat_Name'] = padded_keys_sr
        df_sr['Stat_Value'] = padded_vals_sr

    df_sr.to_csv(os.path.join(out_folder, f'{prefix}SR_data.csv'), index=False)

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
    fig.savefig(os.path.join(out_folder, f'{prefix}fig_SR.png'), dpi=150)
    plt.close(fig)

    best_dis_idx = np.argmin(DIS)
    best_csi_idx = np.argmax(CSI)
    return DIS[best_dis_idx], CSI[best_csi_idx]

def save_roc_fit(y_true, scores, out_folder, label='fit', method_tag='', base_stats=None):
    """Save a single ROC curve (fitting performance) to PNG.
    
    method_tag : short string prepended to every output filename,
                 e.g. 'WoE' -> 'WoE_fig_roc_fit.png'
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, roc_auc_score

    os.makedirs(out_folder, exist_ok=True)
    tag = f"{method_tag}_" if method_tag else ""
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC')

    try:
        auc_val = roc_auc_score(y_true, scores)
        fpr, tpr, _ = roc_curve(y_true, scores)
        
        best_dis, best_csi = _export_roc_and_sr(y_true, scores, out_folder, prefix=f"{tag}fit_", extra_stats=base_stats)
        label_text = f'Complete dataset (AUC = {auc_val:.2f}'
        if best_dis is not None:
            label_text += f', min DIS = {best_dis:.2f}, max CSI = {best_csi:.2f})'
        else:
            label_text += ')'
            
        ax.plot(fpr, tpr, color='green', lw=2, label=label_text)
        print(f'[SZ] Fit AUC = {auc_val:.4f}')
    except ValueError as e:
        ax.text(0.5, 0.5, f"ROC not available\n({e})", ha='center', va='center', color='red')
        print(f'[SZ] ROC Error: {e}')

    ax.legend(loc='lower right')
    fig.savefig(os.path.join(out_folder, f'{tag}fig_roc_fit.png'), dpi=150)
    plt.close(fig)


def save_roc_cv(y_train, scores_train, y_test, scores_test, out_folder, method_tag='', base_stats=None):
    """Save train+test ROC curves (cross-validation) to PNG.
    
    method_tag : short string prepended to every output filename,
                 e.g. 'RF' -> 'RF_fig_roc_cv.png', 'RF_test_ROC_data.csv', ...
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, roc_auc_score

    os.makedirs(out_folder, exist_ok=True)
    tag = f"{method_tag}_" if method_tag else ""
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC')

    try:
        aucv = roc_auc_score(y_test,  scores_test)
        fprv, tprv, _ = roc_curve(y_test,  scores_test)
        
        test_stats = base_stats.copy() if base_stats else {}
        test_stats['Test Split Landslides'] = int(np.sum(y_test == 1))
        test_stats['Test Split Non-Landslides'] = int(np.sum(y_test == 0))
        dis_v, csi_v = _export_roc_and_sr(y_test, scores_test, out_folder, prefix=f"{tag}test_", extra_stats=test_stats)
        label_test = f'Prediction performance (AUC = {aucv:.2f}'
        if dis_v is not None:
             label_test += f', min DIS = {dis_v:.2f}, max CSI = {csi_v:.2f})'
        else:
             label_test += ')'

        ax.plot(fprv, tprv, color='green', lw=2, label=label_test)
        print(f'[SZ] Test AUC = {aucv:.4f}')
    except ValueError as e:
        print(f'[SZ] Test ROC Error: {e}')

    try:
        auct = roc_auc_score(y_train, scores_train)
        fprt, tprt, _ = roc_curve(y_train, scores_train)
        
        train_stats = base_stats.copy() if base_stats else {}
        train_stats['Train Split Landslides'] = int(np.sum(y_train == 1))
        train_stats['Train Split Non-Landslides'] = int(np.sum(y_train == 0))
        dis_t, csi_t = _export_roc_and_sr(y_train, scores_train, out_folder, prefix=f"{tag}train_", extra_stats=train_stats)
        label_train = f'Success performance (AUC = {auct:.2f}'
        if dis_t is not None:
             label_train += f', min DIS = {dis_t:.2f}, max CSI = {csi_t:.2f})'
        else:
             label_train += ')'
             
        ax.plot(fprt, tprt, color='red', lw=2, label=label_train)
        print(f'[SZ] Train AUC = {auct:.4f}')
    except ValueError as e:
        print(f'[SZ] Train ROC Error: {e}')
        if "aucv" not in locals(): # both failed
             ax.text(0.5, 0.5, f"ROC not available\n({e})", ha='center', va='center', color='red')

    ax.legend(loc='lower right')
    fig.savefig(os.path.join(out_folder, f'{tag}fig_roc_cv.png'), dpi=150)
    plt.close(fig)


def save_roc_kfold(y_all, si_all, test_indices_list, out_folder, method_tag='', base_stats=None):
    """Save per-fold ROC curves (k-fold cross-validation) to PNG.
    
    method_tag : short string prepended to every output filename,
                 e.g. 'LR' -> 'LR_fig_roc_kfold.png', 'LR_fold_0_ROC_data.csv', ...
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, roc_auc_score

    os.makedirs(out_folder, exist_ok=True)
    tag = f"{method_tag}_" if method_tag else ""
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
    for i, test_idx in enumerate(test_indices_list):
        yt = y_all[test_idx]
        st = si_all[test_idx]
        
        fold_dir = os.path.join(out_folder, f'fold_{i}')
        os.makedirs(fold_dir, exist_ok=True)
        
        try:
            aucv = roc_auc_score(yt, st)
        except Exception:
            continue
            
        fpr, tpr, _ = roc_curve(yt, st)
        fold_stats = base_stats.copy() if base_stats else {}
        fold_stats[f'Fold {i} Landslides'] = int(np.sum(yt == 1))
        fold_stats[f'Fold {i} Non-Landslides'] = int(np.sum(yt == 0))
        best_dis, best_csi = _export_roc_and_sr(yt, st, fold_dir, prefix=f"{tag}fold_{i}_", extra_stats=fold_stats)
        
        label_text = f'Fold {i} (AUC = {aucv:.2f}'
        if best_dis is not None:
             label_text += f', min DIS = {best_dis:.2f}, max CSI = {best_csi:.2f})'
        else:
             label_text += ')'
             
        ax.plot(fpr, tpr, lw=2, alpha=0.7, label=label_text)
        print(f'[SZ] Fold {i} AUC = {aucv:.4f}')
        
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(loc='lower right', prop={'size': 6})
    fig.savefig(os.path.join(out_folder, f'{tag}fig_roc_kfold.png'), dpi=150)
    plt.close(fig)
