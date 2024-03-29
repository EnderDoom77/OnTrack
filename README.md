# OnTrack

OnTrack is a time management app built with Python. It keeps track of the active time of various windows.

At the moment, OnTrack is only supported on Windows operating systems.

## Dependencies

- Python >3.12 (might work on lower versions, but 3.12 is the active development version)
- `tkinter`: usually comes bundled with modern Python installations
- Pip modules: `pygetwindow`, `pyyaml`, `keyboard`, `tkcalendar`, `pillow`, `matplotlib`, `ttkwidgets`, `requests`
- For building: The `pyinstaller` pip module

## Getting started

Once you have all of the dependencies installed, simply run `py ontrack.py` to start the application.

## Building

To build into the final distribution, run `py -m PyInstaller --noconsole ontrack.py`. Ensure you have the `pyinstaller` pip module installed.

In some cases, since this program tracks active windows, using `--noconsole` can trigger virus threat protection actions, consider omitting that option if this is the case.

Documentation on the [tkcalendar](https://tkcalendar.readthedocs.io/en/stable/index.html) module states that there may be issues with PyInstaller and the `babel.numbers` hidden import.
Refer to the [tkcalendar HowTos - PyInstaller section](https://tkcalendar.readthedocs.io/en/stable/howtos.html#pyinstaller) to fix this issue if a problem arises during building.
