import importlib
import importlib.util
import os
import sys
sys.setrecursionlimit(10000)
from qgis.core import *
from qgis import *
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsMessageLog,QgsApplication
import traceback
import platform
import shutil
import glob
from ..utils import log,warn
from .utils import (
    locate_py,
    add_venv,
    install_pip,
    pip_install_reqs,
    get_package_version,
    add_QGIS_env,
)


class installer():
    # pip name -> import name, for the packages listed in requirements.txt.
    REQUIRED_MODULES = {
        "scikit-learn": "sklearn",
        "libpysal": "libpysal",
        "seaborn": "seaborn",
        "geopandas": "geopandas",
    }

    def __init__(self,version):
        self.plugin_module = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))
        self.plugin_venv = "."+self.plugin_module+version.replace('.', '')
        self._defered_packages = []
        self.plugins_path = os.path.join(
            QgsApplication.qgisSettingsDirPath(), "python", "plugins"
        )
        self.prefix_path = os.path.join(
            QgsApplication.qgisSettingsDirPath().replace("/", os.path.sep),
            "python",
            "dependencies",
        )
        self.qgis_python_interpreter = locate_py()
        self.venv_path = os.path.join(self.prefix_path,self.plugin_venv)
        self.site_packages_path = None
        self.bin_path = None

    def activate_env(self):
        """Fast path for an environment that has already been provisioned.

        Only puts the existing virtual-environment on sys.path/PATH and checks
        that every requirement is importable. Unlike preliminay_req() +
        requirements() this spawns no subprocess, so QGIS start-up costs a few
        milliseconds instead of several seconds. Returns False when anything is
        missing, so the caller can fall back to the full installation path.
        """
        if not os.path.isdir(self.venv_path):
            return False
        try:
            self.site_packages_path, self.bin_path = add_QGIS_env(
                self.prefix_path, self.plugin_venv)
        except Exception as e:
            log(f"Could not activate the existing environment: {e}")
            return False

        # sys.path was just modified, so the import machinery must re-scan it.
        importlib.invalidate_caches()
        for module in self.REQUIRED_MODULES.values():
            try:
                found = importlib.util.find_spec(module) is not None
            except (ImportError, ValueError):
                found = False
            if not found:
                log(f"'{module}' is missing from {self.venv_path}; "
                    "running the full dependency check.")
                return False
        return True

    def preliminay_req(self):
        try:
            add_venv(self.prefix_path,self.venv_path,self.plugin_venv,self.qgis_python_interpreter)
        except Exception as e:
            log(f"An error occurred: {e}")
            return False
        try:
            self.site_packages_path, self.bin_path=add_QGIS_env(self.prefix_path,self.plugin_venv)
        except Exception as e:
            log(f"An error occurred: {e}")
            return False
        try:
            try:
                #windows
                #self.uninstall_pip(['pip'],os.path.join(self.venv_path,"Scripts","python"))
                command=install_pip(['ensurepip'],os.path.join(self.venv_path,"Scripts","pythonw.exe"))
            except Exception as e:
                log(f"An error occurred: {e}")
                #linux and macos
                #self.uninstall_pip(['pip'],os.path.join(self.venv_path,"bin","python"))
                print(self.venv_path)
                command=install_pip(['ensurepip'],os.path.join(self.venv_path,"bin","python")) 
        except Exception as e:
            log(f"An error occurred: {e}")
            return False
           

    def requirements(self):
        dir=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
        log(f"verify requirements")
        with open(os.path.join(dir,"requirements.txt"), "r") as file:
            list_libraries={}
            for line in file:
                    parts=line.split("==")
                    try:
                        library=parts[0]
                        version=parts[1][:-1]
                    except:
                        library=parts[0][:-1]
                        version=None
                    installed_version=get_package_version(self.qgis_python_interpreter,library)
                    if installed_version is None:
                        list_libraries[library]=version
                    else:
                        if str(installed_version)==str(version) or version==None:
                            # iface.messageBar().pushMessage("SZ:",f'{library} is already installed!',Qgis.Success)
                            log(f'{library} is already installed!')
                        else:
                            log(f'{library} is already installed but the actual version '+f'({installed_version}) is different than the required ({version}). It may cause errors!')
                            # iface.messageBar().pushMessage("SZ:",f'{library} is already installed but the actual version '+f'({installed_version}) is different than the required ({version}). It may cause errors!',Qgis.Warning)
        return self.install(list_libraries)

    def install(self,list_libraries):
            if len(list_libraries.keys())>0:
                reqs_to_install = [f"{library}=={version}" if version else library for library, version in list_libraries.items()]
                if QMessageBox.question(None, "SZ for Processing Python dependencies not installed",
                    f"Do you automatically want install missing python modules {reqs_to_install}? \r\n"
                    "QGIS will be non-responsive for a couple of minutes.",
                    QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
                    try:
                        log(f"Will install selected dependencies : {reqs_to_install}")
                        try:
                            #windows
                            command=pip_install_reqs(self.prefix_path,self.plugin_venv,reqs_to_install,os.path.join(self.venv_path,"Scripts","pythonw.exe"))
                        except:
                            #linux and macos
                            command=pip_install_reqs(self.prefix_path,self.plugin_venv,reqs_to_install,os.path.join(self.venv_path,"bin","python"))
                        QMessageBox.information(None, "Packages successfully installed",
                                                #"To make all parts of the plugin work it is recommended to restart your QGIS-session.")
                                                "You can find the SZ-plugin in the Processing-toolbox")
                    except Exception as e:
                        QgsMessageLog.logMessage(traceback.format_exc(), level=Qgis.Warning)
                        QMessageBox.information(None, "An error occurred",
                                                "SZR+ couldn't install Python packages!\n"
                                                "See 'General' tab in 'Log Messages' panel for details.\n"
                                                "Report any errors to https://github.com/PadiCR/SZRPlus/issues")
                        log(f"An error occurred:{e}")
                        return False
                else:
                    QMessageBox.information(None,"Information", "Packages not installed. Some SZ tools will not be fully operational.")
                    sys.path_importer_cache.clear()
                    log("Packages not installed. Some SZ tools will not be fully operational.")
                    return False
                
                sys.path_importer_cache.clear()
                importlib.invalidate_caches()

    def unload(self):
            # Remove path alterations
            if self.site_packages_path and self.site_packages_path in sys.path:
                sys.path.remove(self.site_packages_path)
                os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"].replace(
                    self.bin_path + os.pathsep, ""
                )
                os.environ["PATH"] = os.environ["PATH"].replace(self.bin_path + os.pathsep, "")
            try:
                # Attempt to delete the folder and its contents using shutil
                import stat
                def remove_readonly(func, path, excinfo):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(self.venv_path, onerror=remove_readonly)
                print(f"Folder '{self.venv_path}' and its contents deleted successfully.")
                log(f"Folder '{self.venv_path}' and its contents deleted successfully.")
            except Exception as e:
                print(f"Error deleting folder '{self.venv_path}': {e}")
                log(f"Error deleting folder '{self.venv_path}': {e}")

        
        
    

