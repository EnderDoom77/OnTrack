# OnTrack

OnTrack is a time management app built with Python. It keeps track of the active time of various windows.

At the moment, OnTrack is only supported on Windows operating systems.

## Dependencies

- Python >3.12 (might work on lower versions, but 3.12 is the active development version)
- `tkinter`: usually comes bundled with modern Python installations
- `pygetwindow` pip module
- `pyyaml` pip module
- For building: `pyinstaller` pip module

## Getting started

Once you have all of the dependencies installed, simply run `py ontrack.py` to start the application.

## Building

To build into the final distribution, run `py -m PyInstaller --noconsole ontrack.py`. Ensure you have the `pyinstaller` pip module installed.

In some cases, since this program tracks active windows, using `--noconsole` can trigger virus threat protection actions, consider omitting that option if this is the case.
