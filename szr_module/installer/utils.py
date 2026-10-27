import glob
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from subprocess import (
    PIPE,
    STDOUT,
    Popen,
)

from qgis.core import Qgis, QgsApplication
from qgis.utils import iface

from ..utils import log, warn

if platform.system() == "Windows":
    from subprocess import (
        STARTF_USESHOWWINDOW,
        STARTF_USESTDHANDLES,
        STARTUPINFO,
        SW_HIDE,
    )


class CommandError(RuntimeError):
    """A subprocess the installer depends on did not succeed.

    run_cmd used to only warn on a non-zero exit code, so a failed venv
    creation or pip install went unnoticed and the installer reported success
    anyway. Every failure now reaches the caller as this exception.
    """

    def __init__(self, args, returncode, output):
        self.cmd = args
        self.returncode = returncode
        self.output = output
        printable = " ".join(str(a) for a in args)
        if returncode is None:
            super().__init__(f"Could not run {printable}: {output}")
        else:
            super().__init__(
                f"{printable} exited with code {returncode}.\n{output}")


def _startupinfo():
    """Keep the console window hidden on Windows."""
    if os.name != "nt":
        return None
    startupinfo = STARTUPINFO()
    startupinfo.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = SW_HIDE
    return startupinfo


def probe(args, timeout=60):
    """Run a short command only for its exit status; never raises.

    Used for the yes/no questions the installer asks about an interpreter —
    can it import ensurepip, does this environment have pip — where a failure
    is an answer rather than an error.
    """
    try:
        completed = subprocess.run(
            [str(a) for a in args], stdout=PIPE, stderr=STDOUT,
            startupinfo=_startupinfo(), timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return completed.returncode, completed.stdout.decode(errors="replace").strip()


def run_cmd(args, description="Installing....", check=True):
    """Run a command, streaming its output to the log panel.

    Returns (returncode, output). With check=True a command that cannot be
    started, or that exits non-zero, raises CommandError.
    """
    args = [str(a) for a in args]
    log(f'command:{args}')

    try:
        process = Popen(args, stdout=PIPE, stderr=STDOUT,
                        startupinfo=_startupinfo())
    except OSError as e:
        warn(f"Could not start {args}: {e}")
        if check:
            raise CommandError(args, None, str(e)) from e
        return 1, str(e)

    full_output = ""
    while True:
        QgsApplication.processEvents()
        try:
            # FIXME : this doesn't seem to timeout
            out, _ = process.communicate(timeout=0.1)
            output = out.decode(errors="replace").strip()
            full_output += output
            if output:
                log(output)
        except subprocess.TimeoutExpired:
            pass

        if process.poll() is not None:
            break

    if process.returncode != 0:
        warn(f"Command failed with exit code {process.returncode}: {full_output}")
        if check:
            raise CommandError(args, process.returncode, full_output)
        return process.returncode, full_output

    log("Command succeeded.")
    if iface is not None:
        iface.messageBar().pushMessage(
            "Success",
            f"{description.capitalize()} succeeded",
            level=Qgis.Success,
        )
    return 0, full_output


def locate_py():
        # get Python version
        str_ver_qgis = sys.version.split(" ")[0]
        try:
            # non-Linux
            path_py = os.environ["PYTHONHOME"]
        except Exception:
            # Linux / fallback
            path_py = sys.executable
        # convert to Path for easier processing
        path_py = Path(path_py)

        if platform.system() == "Windows":
            # sys.executable is always the most reliable starting point
            exe = Path(sys.executable)
            candidates = [
                # prefer pythonw.exe next to the running python.exe
                exe.with_name("pythonw.exe"),
                # OSGeo4W layout: PYTHONHOME = …\apps\Python312, binaries in …\bin\
                path_py / "../../bin/pythonw.exe",
                path_py / "../../bin/python.exe",
                # fallback: same directory as PYTHONHOME
                path_py.with_name("pythonw.exe"),
                path_py.with_name("python.exe"),
                # last resort: the running interpreter itself
                exe,
            ]
        else:
            candidates = [
                path_py / "bin" / "python3",
                path_py / "bin" / "python",
                path_py.with_name("python3"),
                path_py.with_name("python"),
                Path(sys.executable),
            ]
        for candidate_path in candidates:
            try:
                resolved = candidate_path.resolve()
                if resolved.exists():
                    log(f"Python interpreter is located in {resolved}")
                    return resolved
            except Exception:
                continue
        # absolute last resort: return the running interpreter
        fallback = Path(sys.executable)
        log(f"Python interpreter fallback: {fallback}")
        return fallback


def venv_interpreter(venv_path):
    """The interpreter inside a virtual-environment, for this platform.

    Probing for it by catching the exception from a Windows path on Linux hid
    the real errors underneath, so the layout is chosen explicitly instead.
    """
    if platform.system() == "Windows":
        scripts = os.path.join(venv_path, "Scripts")
        for name in ("pythonw.exe", "python.exe"):
            candidate = os.path.join(scripts, name)
            if os.path.exists(candidate):
                return candidate
        return os.path.join(scripts, "python.exe")
    return os.path.join(venv_path, "bin", "python")


def venv_has_pip(venv_path):
    """True when venv_path holds an environment whose pip actually runs.

    The directory existing proves nothing: when `python -m venv` fails at the
    ensurepip step it still leaves behind pyvenv.cfg, bin/ and an empty
    site-packages/.
    """
    interpreter = venv_interpreter(venv_path)
    if not os.path.exists(interpreter):
        return False
    returncode, output = probe([interpreter, "-m", "pip", "--version"])
    if returncode != 0:
        log(f"{interpreter} has no usable pip: {output}")
        return False
    return True


def venv_package_hint(interpreter):
    """Name of the distribution package that carries ensurepip."""
    returncode, output = probe(
        [interpreter, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"])
    if returncode == 0 and output.strip():
        return f"python{output.strip()}-venv"
    return "python3-venv"


def check_venv_support(interpreter):
    """Raise unless `interpreter -m venv` can produce a working environment.

    Debian and Ubuntu ship ensurepip in a separate package. Without it venv
    creation half-succeeds, which is what let the installer claim success and
    then fail to import scikit-learn.
    """
    returncode, output = probe([interpreter, "-c", "import ensurepip"])
    if returncode == 0:
        return
    if platform.system() == "Windows":
        raise RuntimeError(
            f"{interpreter} cannot create a virtual-environment: the "
            f"'ensurepip' module is missing.\n{output}")
    package = venv_package_hint(interpreter)
    raise RuntimeError(
        "Python cannot create a virtual-environment because the 'ensurepip' "
        "module is missing. On Debian/Ubuntu it ships in a separate package — "
        f"install it with:\n\n    sudo apt install {package}\n\n"
        "then restart QGIS and enable SZR+ again.")


def add_venv(prefix_path, venv_path, plugin_venv, interpreter="python"):
    """Provision the plugin's virtual-environment, reusing a working one."""
    os.makedirs(prefix_path, exist_ok=True)
    if os.path.isdir(venv_path):
        if venv_has_pip(venv_path):
            log(f"{plugin_venv} already exist in {venv_path} with {interpreter}")
            return
        # An environment left half-created by an earlier failed attempt would
        # otherwise be reused for ever, since only the folder was checked.
        warn(f"{venv_path} exists but has no working pip; recreating it.")
        shutil.rmtree(venv_path, ignore_errors=True)

    check_venv_support(interpreter)
    log(f"creating {plugin_venv} in {venv_path} with {interpreter}")
    run_cmd(
        [
            interpreter,
            "-m",
            "venv",
            venv_path,
        ],
        f"creating a dedicated virtual-environment",
    )
    if not venv_has_pip(venv_path):
        raise RuntimeError(
            f"The virtual-environment created in {venv_path} has no pip, so no "
            "dependency can be installed into it.")


def add_QGIS_env(prefix_path,plugin_venv):
    if platform.system() == 'Windows':
        site_packages_path = os.path.join(prefix_path,plugin_venv,"Lib", "site-packages")
        bin_path = os.path.join(prefix_path,plugin_venv,"Scripts")
    else:
        search_pattern = os.path.join(prefix_path,plugin_venv, "lib", "python*", "site-packages")
        matches = sorted(glob.glob(search_pattern))
        if not matches:
            raise RuntimeError(
                "No site-packages directory under "
                f"{os.path.join(prefix_path, plugin_venv)}: the "
                "virtual-environment was not created properly.")
        site_packages_path = matches[0]
        bin_path = os.path.join(prefix_path,plugin_venv,"bin")

    if site_packages_path not in sys.path:
        log(f"Adding {site_packages_path} to PYTHONPATH")
        sys.path.insert(0, site_packages_path)
        os.environ["PYTHONPATH"] = (
            site_packages_path + os.pathsep + os.environ.get("PYTHONPATH", "")
        )

    if bin_path not in os.environ.get("PATH", ""):
        log(f"Adding {bin_path} to PATH")
        os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")

    return (site_packages_path, bin_path)

def install_pip(reqs_to_install,interpreter="python"):
    """
    Installs given reqs with pip
    """
    log(f"Will install {reqs_to_install} with {interpreter}")
    cmd=[
            interpreter,
            "-m",
            *reqs_to_install
        ]
    run_cmd(cmd)#,f"installing {len(reqs_to_install)} requirements: {reqs_to_install}")
    return(cmd)

def pip_uninstall_reqs(reqs_to_uninstall, extra_args=[],interpreter="python"):
    """
    Unnstalls given deps with pip
    """
    log(f"Will pip uninstall {reqs_to_uninstall}")
    cmd=[
            interpreter,
            "-m",
            "pip",
            "uninstall",
            "-y",
            *reqs_to_uninstall,
        ]
    run_cmd(cmd,f"uninstalling {len(reqs_to_uninstall)} requirements: {reqs_to_uninstall}")
    return(cmd)

def pip_install_reqs(prefix_path,plugin_venv,reqs_to_install,interpreter="python"):
    """
    Installs given reqs with pip
    """
    log(f"Will pip install {reqs_to_install} in {os.path.join(prefix_path, plugin_venv)} with {interpreter}")
    cmd=[
            interpreter,
            "-m",
            "pip",
            "install",
            *reqs_to_install,
            #"-U",
            #"--prefer-binary",
            #"--user"
            #"--prefix",
            #prefix_path,
        ]
    run_cmd(cmd,f"installing {len(reqs_to_install)} requirements: {reqs_to_install}")
    return(cmd)

def get_package_version(qgis_python_interpreter,package_name):
        returncode, output = probe(
            [qgis_python_interpreter, '-m', 'pip', 'show', package_name])
        if returncode != 0:
            return None
        for line in output.strip().split('\n'):
            if line.startswith("Version: "):
                return line[len("Version: "):].strip()
        return None
