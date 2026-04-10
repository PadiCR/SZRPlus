import os

filepath = os.path.join(os.path.dirname(__file__), 'New_GUI', 'sz_edu_dialog.py')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace _build_dataprep_tab
old_build_dataprep = '''    def _build_dataprep_tab(self):
        cb_stats_lyr = self._vl_combo()
        cb_stats_fld = QgsFieldComboBox()
        cb_stats_lyr.layerChanged.connect(cb_stats_fld.setLayer)

        csv_stats_out = _file_widget("Output csv", "CSV (*.csv)")
        csv_stats_out.setStorageMode(QgsFileWidget.SaveFile)

        pages_cfg = [
            ("Clean Points By Raster Kernel", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Output Folder", _folder_widget()),
            ]),
            ("Attribute Table Statistics", [
                ("Input Layer (vector)", cb_stats_lyr),
                ("ID Field", cb_stats_fld),
                ("Output CSV", csv_stats_out),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points Kernel Statistics", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points Kernel Graphs", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points Sampler", [
                ("Landslide Inventory (raster)", _file_widget("Inventory", "GeoTIFF (*.tif *.tiff)")),
                ("Mask Polygon Layer (vector)", self._vl_combo()),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points To Grid", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Reference Raster", _file_widget("Reference raster", "GeoTIFF (*.tif *.tiff)")),
                ("Output Folder", _folder_widget()),
            ]),
            ("Poly To Grid", [
                ("Input Polygon Layer (vector)", self._vl_combo()),
                ("Reference Raster", _file_widget("Reference raster", "GeoTIFF (*.tif *.tiff)")),
                ("Output Folder", _folder_widget()),
            ]),
            ("Classify Field by .txt File", [
                ("Input Layer (vector)", self._vl_combo()),
                ("Classification .txt File", _file_widget("Classes txt", "Text (*.txt)")),
                ("Output Folder", _folder_widget()),
            ]),
            ("Classify Field in Quantiles", [
                ("Input Layer (vector)", self._vl_combo()),
                ("Number of Quantiles", self._spinbox(2, 20, 4)),
                ("Output Folder", _folder_widget()),
            ]),
            ("Correlation Plot", [
                ("Input Layer (vector)", self._vl_combo()),
                ("Output Folder", _folder_widget()),
            ]),
        ]'''

new_build_dataprep = '''    def _build_dataprep_tab(self):
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

        csv_stats_out = _file_widget("Output csv", "CSV (*.csv)")
        csv_stats_out.setStorageMode(QgsFileWidget.SaveFile)

        from qgis.PyQt.QtWidgets import QLineEdit
        def _line_edit(placeholder):
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            return le

        def _shp_out(title):
            fw = _file_widget(title, "ESRI Shapefile (*.shp)")
            fw.setStorageMode(QgsFileWidget.SaveFile)
            return fw
            
        def _tif_out(title):
            fw = _file_widget(title, "GeoTIFF (*.tif *.tiff)")
            fw.setStorageMode(QgsFileWidget.SaveFile)
            return fw

        pages_cfg = [
            ("Clean Points By Raster Kernel", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Extent Coordinates (xmin,xmax,ymin,ymax)", _line_edit("e.g. 10.0, 20.0, 30.0, 40.0")),
                ("Buffer Radius (pixels)", self._spinbox(1, 100, 4)),
                ("Min Value Acceptable", self._spinbox(-9999, 9999, 3)),
                ("Output Vector Layer", _shp_out("Output shapefile")),
            ]),
            ("Attribute Table Statistics", [
                ("Input Layer (vector)", cb_stats_lyr),
                ("ID Field", cb_stats_fld),
                ("Output CSV", csv_stats_out),
                ("Output Folder", _folder_widget()),
            ]),
            ("Points Kernel Statistics", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Raster Kernel Layer", _file_widget("Raster", "GeoTIFF (*.tif *.tiff)")),
                ("Mask Polygon Layer (vector)", self._vl_combo()),
                ("Buffer Radius (pixels)", self._spinbox(1, 100, 4)),
                ("Output Vector Layer", _shp_out("Output shapefile")),
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
                ("Output Layer Sample", _shp_out("Output shapefile")),
                ("Output Layer 1-Sample", _shp_out("Output shapefile")),
            ]),
            ("Points To Grid", [
                ("Input Points Layer (vector)", self._vl_combo()),
                ("Reference Raster", _file_widget("Reference raster", "GeoTIFF (*.tif *.tiff)")),
                ("Extent Coordinates (xmin,xmax,ymin,ymax)", _line_edit("e.g. 10.0, 20.0, 30.0, 40.0")),
                ("Output Raster", _tif_out("Output raster")),
            ]),
            ("Poly To Grid", [
                ("Input Polygon Layer (vector)", self._vl_combo()),
                ("Pixel Width", self._spinbox(1, 10000, 10)),
                ("Pixel Height", self._spinbox(1, 10000, 10)),
                ("Output Raster", _tif_out("Output raster")),
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
        ]'''

# 2. Replace _run_dataprep
old_run_dataprep = '''    def _run_dataprep(self, title: str):
        if title == "Attribute Table Statistics":
            refs = self._dp_refs[title]
            layer = refs["Input Layer (vector)"].currentLayer()
            if not layer or not layer.isValid():
                QMessageBox.warning(self, "Missing input", "Please select a valid Input Layer.")
                return
            
            field = refs["ID Field"].currentField()
            if not field:
                QMessageBox.warning(self, "Missing input", "Please select an ID Field.")
                return
                
            out_csv = refs["Output CSV"].filePath()
            out_folder = refs["Output Folder"].filePath()
            if not out_csv or not out_folder:
                QMessageBox.warning(self, "Missing input", "Please specify output CSV and Folder.")
                return
                
            from ..scripts.lsdanalysis import statistic
            alg_params = {
                'OUTPUT': out_csv,
                'ID': field,
                'INPUT2': layer.source(),
                'PATH': out_folder
            }
            try:
                stat_alg = statistic()
                stat_alg.input(alg_params)
                QMessageBox.information(self, "Success", f"Attribute Table Statistics completed successfully.\\nSaved to:\\n{out_folder}")
            except Exception as e:
                import traceback
                QMessageBox.critical(self, "Error", f"{str(e)}\\n{traceback.format_exc()}")
            return
            
        QMessageBox.information(self, "Not yet implemented",
            f"The backend for '{title}' will be wired in the next implementation phase.\\n"
            "Parameters have been collected successfully.")'''

new_run_dataprep = '''    def _run_dataprep(self, title: str):
        refs = self._dp_refs[title]
        try:
            if title == "Clean Points By Raster Kernel":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                raster = refs["Raster Kernel Layer"].filePath()
                extent = refs["Extent Coordinates (xmin,xmax,ymin,ymax)"].text()
                radius = refs["Buffer Radius (pixels)"].value()
                min_val = refs["Min Value Acceptable"].value()
                out = refs["Output Vector Layer"].filePath()
                if not layer or not raster or not extent or not out:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.cleaning import cleankernelAlgorithm
                alg = cleankernelAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT_RASTER_LAYER': raster, 'INPUT_EXTENT': extent, 'INPUT_VECTOR_LAYER': layer.source(), 'INPUT_INT': radius, 'INPUT_INT_1': min_val, 'OUTPUT': out }
                alg.extent(alg_params)
                alg.importingandcounting(alg_params)
                alg.indexing(alg_params)
                alg.vector()
                alg.saveV(alg_params)

            elif title == "Attribute Table Statistics":
                layer = refs["Input Layer (vector)"].currentLayer()
                field = refs["ID Field"].currentField()
                out_csv = refs["Output CSV"].filePath()
                out_folder = refs["Output Folder"].filePath()
                if not layer or not field or not out_csv or not out_folder:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.lsdanalysis import statistic
                alg = statistic()
                alg_params = { 'OUTPUT': out_csv, 'ID': field, 'INPUT2': layer.source(), 'PATH': out_folder }
                alg.input(alg_params)

            elif title == "Points Kernel Statistics":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                raster = refs["Raster Kernel Layer"].filePath()
                mask = refs["Mask Polygon Layer (vector)"].currentLayer()
                radius = refs["Buffer Radius (pixels)"].value()
                out = refs["Output Vector Layer"].filePath()
                if not layer or not raster or not mask or not out:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.stat31 import rasterstatkernelAlgorithm
                alg = rasterstatkernelAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT': mask.source(), 'INPUT2': raster, 'INPUT3': layer.source() }
                ras, ds1, XY, crs = alg.importing(alg_params)
                alg_params2 = { 'INPUT': radius, 'INPUT3': ras, 'INPUT2': XY, 'INPUT1': ds1, 'CRS': crs }
                XYcoord, attributi = alg.indexing(alg_params2)
                alg_params3 = { 'OUTPUT': out, 'INPUT2': XYcoord, 'INPUT': ds1, 'INPUT3': attributi, 'CRS': crs }
                alg.saveV(alg_params3)

            elif title == "Points Kernel Graphs":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                field = refs["ID Field"].currentField()
                out_folder = refs["Output Folder"].filePath()
                if not layer or not field or not out_folder:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.graphs_lsdstats_kernel import statistickernel
                alg = statistickernel()
                alg_params = { 'ID': field, 'INPUT2': layer.source(), 'OUT': out_folder }
                alg.input(alg_params)

            elif title == "Points Sampler":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                mask = refs["Mask Polygon Layer (vector)"].currentLayer()
                w = refs["Pixel Width"].value()
                h = refs["Pixel Height"].value()
                trainN = refs["Sample (%)"].value()
                out1 = refs["Output Layer Sample"].filePath()
                out2 = refs["Output Layer 1-Sample"].filePath()
                if not layer or not mask or not out1 or not out2:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.randomsampler3 import samplerAlgorithm
                alg = samplerAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT': layer.source(), 'INPUT1': mask.source(), 'w': w, 'h': h, 'train': trainN }
                v, t, xy = alg.resampler(alg_params)
                alg.save({ 'INPUT1': out1, 'INPUT2': v, 'INPUT3': xy })
                alg.save({ 'INPUT1': out2, 'INPUT2': t, 'INPUT3': xy })

            elif title == "Points To Grid":
                layer = refs["Input Points Layer (vector)"].currentLayer()
                raster = refs["Reference Raster"].filePath()
                ext_str = refs["Extent Coordinates (xmin,xmax,ymin,ymax)"].text()
                out = refs["Output Raster"].filePath()
                if not layer or not raster or not ext_str or not out:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from qgis.core import QgsRectangle
                coords = [float(x.strip()) for x in ext_str.split(',')]
                from ..scripts.pointtogrid import pointtogridAlgorithm
                alg = pointtogridAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                rect = QgsRectangle(coords[0], coords[2], coords[1], coords[3])
                alg_params = { 'STRING': '', 'INPUT_RASTER_LAYER': raster, 'INPUT_EXTENT': rect, 'INPUT_VECTOR_LAYER': layer.source(), 'OUTPUT': out }
                alg.extent(alg_params)
                alg.importingandcounting(alg_params)

            elif title == "Poly To Grid":
                layer = refs["Input Polygon Layer (vector)"].currentLayer()
                w = refs["Pixel Width"].value()
                h = refs["Pixel Height"].value()
                out = refs["Output Raster"].filePath()
                if not layer or not out:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.polytogrid import polytogridAlgorithm
                alg = polytogridAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'OUTPUT': out, 'W': w, 'H': h }
                alg.importingandcounting(alg_params)

            elif title == "Classify Field by .txt File":
                layer = refs["Input Layer (vector)"].currentLayer()
                txt = refs["Classification .txt File"].filePath()
                field = refs["Field to Classify"].currentField()
                new_f = refs["New Field Name"].text()
                if not layer or not txt or not field or not new_f:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
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
                from ..scripts.classcovdeciles import classcovdecAlgorithm
                alg = classcovdecAlgorithm()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'field': field, 'nome': new_f, 'num': num }
                alg.classify(alg_params)

            elif title == "Correlation Plot":
                layer = refs["Input Layer (vector)"].currentLayer()
                lw = refs["Continuous Independent Variables"]
                fields = [lw.item(i).text() for i in range(lw.count()) if lw.item(i).checkState() == Qt.Checked]
                out = refs["Output Folder"].filePath()
                if not layer or not fields or not out:
                    QMessageBox.warning(self, "Missing input", "Please provide all parameters.")
                    return
                from ..scripts.corrplot import CorrAlgorithm
                alg = CorrAlgorithm()
                alg.f = __import__('tempfile').gettempdir()
                alg_params = { 'INPUT_VECTOR_LAYER': layer.source(), 'field1': fields }
                df, nomi, crs = alg.load(alg_params)
                alg_params2 = { 'INPUT_VECTOR_LAYER': layer.source(), 'field1': fields, 'df': df, 'nomi': nomi, 'OUT': out }
                alg.corr(alg_params2)

            QMessageBox.information(self, "Success", f"{title} completed successfully.")
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", f"{str(e)}\\n{traceback.format_exc()}")'''

if old_build_dataprep in content:
    content = content.replace(old_build_dataprep, new_build_dataprep)
    print("Replaced _build_dataprep_tab")
else:
    print("_build_dataprep_tab not found")

if old_run_dataprep in content:
    content = content.replace(old_run_dataprep, new_run_dataprep)
    print("Replaced _run_dataprep")
else:
    print("_run_dataprep not found")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
