# Build and release

## Build the Windows installer

Use x64 Python 3.13 on Windows and the official [Inno Setup 6 compiler](https://jrsoftware.org/isdl.php). Install the application dependencies first, then:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller==6.16.0
.\packaging\build.ps1 -Compiler "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

The build stops on errors. Its output is `dist/Prism-0.1.3-Setup-x64.exe`. For local distribution, copy that one installer into the project root. Do not copy the internal runtime folder alongside it.

The installer bundles Python, Qt, image/PDF libraries and offline OCR models. It installs per user, creates a Start-menu shortcut, optionally adds desktop/Explorer shortcuts, and supports Windows uninstall. Word/LibreOffice are separate dependencies.

## Publish on GitHub

1. Commit the source, README and cleanup deletions. `.gitignore` excludes virtual environments, caches, build output and installer binaries.
2. Create a GitHub Release for the version being shipped.
3. Attach `Prism-0.1.3-Setup-x64.exe` as a **release asset**.
4. Publish the release and verify that the README's Releases link offers the download.

The installer is approximately 128 MiB. [GitHub blocks regular Git files above 100 MiB](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github); upload it as a Release asset, not as a repository file. The ignored root installer stays available locally.

Before public distribution, review bundled dependency/model licenses, current Inno Setup licensing, signing and clean-machine installation/update/uninstall tests. The current build is unsigned. Nothing is published by the build script.

## Runtime diagnostics

Optional, for developers: run the installed executable with `--verify-installation <samples-folder> <new-output-folder>`. The output folder must not already exist. This tests the available sample conversions and writes results outside the source inputs. The four included inputs cover the base image/PDF/text/OCR checks. Word-specific fixtures and generated proof galleries are intentionally not distributed with the source samples.
