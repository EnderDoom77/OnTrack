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

To build into the final distribution, run `py -m PyInstaller --onefile --noconsole ontrack.py`. Ensure you have the `pyinstaller` pip module installed.

In some cases, since this program tracks active windows, using `--noconsole` can trigger virus threat protection actions, consider omitting that option if this is the case.

Documentation on the [tkcalendar](https://tkcalendar.readthedocs.io/en/stable/index.html) module states that there may be issues with PyInstaller and the `babel.numbers` hidden import.
Refer to the [tkcalendar HowTos - PyInstaller section](https://tkcalendar.readthedocs.io/en/stable/howtos.html#pyinstaller) to fix this issue if a problem arises during building.

The recommended safe command is: `py -m PyInstaller --onefile --hidden-import babel.numbers ontrack.py`

For the purpose of **auto updates**, the build must not have a `_internal` folder, as this would poorly interact with the `_internal` folder required by the auto-updating script. This could be solved by allowing the auto-updater to have a different internal folder name.

## Auto updating

The self_update executable should fetch the `latest_stable` data from VERSION_DATA and update the ontrack executable with anything it needs.

To build the `self_update.py` script, use `py -m PyInstaller self_update.py`

Similarly to the `--noconsole` option for `ontrack.py`, attempting to build this with `--onefile` causes it to be flagged as a virus. This seems to be caused by the requests to github it makes internally. If compiled with a separate `_internal` folder, this will contain a certificate which prevents it from being false-flagged.
