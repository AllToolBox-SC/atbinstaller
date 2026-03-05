#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from typing import List


def find_first(paths: List[str]):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def collect_include_options(base_dir: str) -> List[str]:
    opts: List[str] = []

    # include locals folder (keeps same 'locals' target name)
    locals_dir = os.path.join(base_dir, "src", "locals")
    if os.path.isdir(locals_dir):
        opts.append(f"--include-data-dir={locals_dir}=locals")

    # include LICENSE at root
    license_file = os.path.join(base_dir, "LICENSE")
    if os.path.exists(license_file):
        opts.append(f"--include-data-file={license_file}=LICENSE")

    # include api_server.txt (prefer src/api_server.txt if present)
    src_api = os.path.join(base_dir, "src", "api_server.txt")
    root_api = os.path.join(base_dir, "api_server.txt")
    if os.path.exists(src_api):
        opts.append(f"--include-data-file={src_api}=api_server.txt")
    elif os.path.exists(root_api):
        opts.append(f"--include-data-file={root_api}=api_server.txt")

    # 7z binaries - try common locations and map to root names (7z.exe / 7z.dll)
    candidates = [
        os.path.join(base_dir, "7zc", "7z.exe"),
        os.path.join(base_dir, "7zc", "7z.dll"),
        os.path.join(base_dir, "src", "7z.exe"),
        os.path.join(base_dir, "src", "7z.dll"),
        os.path.join(base_dir, "7z.exe"),
        os.path.join(base_dir, "7z.dll"),
    ]
    for p in candidates:
        if os.path.exists(p):
            dest = os.path.basename(p)
            opts.append(f"--include-data-file={p}={dest}")

    return opts


def build_nuitka(
    base_dir: str,
    nuitka_backend: str,
    target: str,
    onefile: bool,
    output_dir: str,
    extra: List[str],
):
    main_py = os.path.join(base_dir, "src", "main.py")
    if not os.path.exists(main_py):
        raise FileNotFoundError(f"main entry not found: {main_py}")

    cmd = [sys.executable, "-m", "nuitka", main_py]

    if onefile:
        cmd += ["--onefile"]
        # hide console in release builds
        if target == "release":
            cmd += ["--windows-console-mode=disable"]

    # output
    cmd += [f"--output-dir={output_dir}"]

    # compiler selection
    if nuitka_backend == "msvc":
        cmd += ["--msvc=latest"]
    elif nuitka_backend == "mingw":
        cmd += ["--mingw64"]

    # target specific options
    if target == "release":
        cmd += ["--lto=yes"]
    else:
        # debug-friendly flags
        cmd += ["--debug"]

    # Qt plugin
    cmd += ["--enable-plugin=pyqt6"]

    # include data files
    cmd += collect_include_options(base_dir)

    # extra user options
    if extra:
        cmd += extra

    print("Executing build command:")
    print(" ".join(shlex.quote(a) for a in cmd))

    # run
    subprocess.check_call(cmd)


def collect_pyinstaller_mappings(base_dir: str):
    """Return tuples for PyInstaller: (data_entries, binary_entries).
    Each entry is a pair (src, dest) where dest is the target path inside the bundle.
    """
    data_entries = []
    binary_entries = []

    locals_dir = os.path.join(base_dir, "src", "locals")
    if os.path.isdir(locals_dir):
        data_entries.append((locals_dir, "locals"))

    license_file = os.path.join(base_dir, "LICENSE")
    if os.path.exists(license_file):
        data_entries.append((license_file, "LICENSE"))

    src_api = os.path.join(base_dir, "src", "api_server.txt")
    root_api = os.path.join(base_dir, "api_server.txt")
    if os.path.exists(src_api):
        data_entries.append((src_api, "api_server.txt"))
    elif os.path.exists(root_api):
        data_entries.append((root_api, "api_server.txt"))

    # 7z binaries - include as binaries so they are available at runtime
    candidates = [
        os.path.join(base_dir, "7zc", "7z.exe"),
        os.path.join(base_dir, "7zc", "7z.dll"),
        os.path.join(base_dir, "src", "7z.exe"),
        os.path.join(base_dir, "src", "7z.dll"),
        os.path.join(base_dir, "7z.exe"),
        os.path.join(base_dir, "7z.dll"),
    ]
    for p in candidates:
        if os.path.exists(p):
            # place binaries at bundle root so relative lookups work
            binary_entries.append((p, "."))

    return data_entries, binary_entries


def build_pyinstaller(base_dir: str, onefile: bool, output_dir: str, extra: List[str], build_type: str):
    main_py = os.path.join(base_dir, "src", "main.py")
    if not os.path.exists(main_py):
        raise FileNotFoundError(f"main entry not found: {main_py}")

    name = os.path.splitext(os.path.basename(main_py))[0] or "main"

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm"]

    if onefile:
        cmd += ["--onefile"]
        # hide console in release, show console in debug
        if build_type == "release":
            cmd += ["--windowed"]
        else:
            # enable PyInstaller debug mode for more verbose output
            cmd += ["--debug=all"]

    # output locations
    cmd += ["--name", name, "--distpath", output_dir]
    workpath = os.path.join(base_dir, "build", "pyinstaller_work")
    cmd += ["--workpath", workpath, "--clean"]

    # gather include mappings
    data_entries, binary_entries = collect_pyinstaller_mappings(base_dir)
    for src, dest in data_entries:
        mapping = f"{src}{os.pathsep}{dest}"
        cmd += ["--add-data", mapping]
    for src, dest in binary_entries:
        mapping = f"{src}{os.pathsep}{dest}"
        cmd += ["--add-binary", mapping]

    # allow user extra flags
    if extra:
        cmd += extra

    print("Executing PyInstaller command:")
    print(" ".join(shlex.quote(a) for a in cmd))

    # ensure workpath exists
    os.makedirs(workpath, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    subprocess.check_call(cmd)


def locate_executable_in_output(output_dir: str) -> str | None:
    # Try to find an .exe in output_dir (first match)
    for root, _, files in os.walk(output_dir):
        for f in files:
            if f.lower().endswith(".exe"):
                return os.path.join(root, f)
    return None


def main(argv: List[str] | None = None):
    parser = argparse.ArgumentParser(description="Build helper for atbinstaller (supports Nuitka and PyInstaller)")
    parser.add_argument("--nuitka", choices=["msvc", "mingw", "none"], default="msvc", help="Which backend to use for Nuitka (or 'none' to skip)")
    parser.add_argument("--pyinstaller", action="store_true", help="Alias flag to select PyInstaller as packager")
    parser.add_argument("-t", "--type", dest="build_type", choices=["release", "debug"], default="release", help="Build type: release or debug")
    parser.add_argument("--onefile", dest="onefile", action="store_true", default=True, help="Create onefile executable (default: True)")
    parser.add_argument("--no-onefile", dest="onefile", action="store_false", help="Do not create onefile executable")
    # Note: removed --output-dir option; default output path is build/py/dist
    parser.add_argument("--clean", action="store_true", help="Clean output dir before building")
    parser.add_argument("--run", action="store_true", help="Run produced executable after build (searches first .exe in output)")
    parser.add_argument("--extra", nargs="*", help="Extra options to pass to Nuitka (space separated)")

    args = parser.parse_args(argv)

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # helper to detect whether a flag was explicitly provided by the user in argv
    def _arg_provided(flag: str, arglist: List[str] | None):
        check = arglist if arglist is not None else sys.argv[1:]
        for tok in check:
            if tok == flag or tok.startswith(flag + "="):
                return True
        return False

    # onefile defaults to True unless overridden by --no-onefile

    # default output directory (relative build folder)
    output_dir = os.path.join(base_dir, "build", "py", "dist")
    if args.clean and os.path.isdir(output_dir):
        print(f"Cleaning output dir: {output_dir}")
        shutil.rmtree(output_dir)

    try:
        # choose packager
        extra = args.extra or []

        # Determine selected packager. Default to PyInstaller unless user explicitly requested Nuitka.
        if args.pyinstaller:
            if _arg_provided("--nuitka", argv):
                parser.error("--pyinstaller and --nuitka cannot be used together. Provide only one of these options.")
            selected_packager = "pyinstaller"
        elif _arg_provided("--nuitka", argv):
            selected_packager = "nuitka"
        else:
            selected_packager = "pyinstaller"

        if selected_packager == "pyinstaller":
            build_pyinstaller(base_dir, args.onefile, output_dir, extra, args.build_type)
        else:
            # If user explicitly asked for --nuitka with value 'none', run source directly
            if args.nuitka == "none":
                print("Running source directly (no nuitka)")
                subprocess.check_call([sys.executable, os.path.join(base_dir, "src", "main.py")])
                return
            # build with Nuitka; pass build_type as target
            build_nuitka(base_dir, args.nuitka, args.build_type, args.onefile, output_dir, extra)

        print("Build finished")

        # After build, copy main.exe and main.pdb (if present) to build/main
        try:
            exe_basename = os.path.splitext(os.path.basename(os.path.join(base_dir, "src", "main.py")))[0] + ".exe"
            pdb_basename = os.path.splitext(exe_basename)[0] + ".pdb"

            expected_exe = os.path.join(output_dir, exe_basename)
            exe_path = expected_exe if os.path.exists(expected_exe) else locate_executable_in_output(output_dir)

            pdb_path = None
            for root, _, files in os.walk(output_dir):
                if pdb_basename in files:
                    pdb_path = os.path.join(root, pdb_basename)
                    break

            target_dir = os.path.join(base_dir, "build", "main")
            os.makedirs(target_dir, exist_ok=True)

            if exe_path and os.path.exists(exe_path):
                shutil.copy2(exe_path, target_dir)
                print(f"Copied executable to {target_dir}")
            else:
                print("No executable found to copy.")

            if pdb_path and os.path.exists(pdb_path):
                shutil.copy2(pdb_path, target_dir)
                print(f"Copied pdb to {target_dir}")
            else:
                print("No pdb found to copy.")
        except Exception as e:
            print(f"Warning: failed to copy exe/pdb: {e}")

        if args.run:
            exe = locate_executable_in_output(output_dir)
            if exe:
                print(f"Running: {exe}")
                subprocess.check_call([exe])
            else:
                print("No executable found to run.")

    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code: {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
