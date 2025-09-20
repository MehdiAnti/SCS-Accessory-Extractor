# SCS Accessory Extractor

**SCS Accessory Extractor** is a Python-based tool for processing and extracting some folders from `.scs` files used in Euro Truck Simulator 2 (ETS2) and American Truck Simulator (ATS). It allows you to safely backup, clean, and package the result.


## Features

- Process `.scs` files for ETS2 and ATS.
- Automatically backup required accessory folders.
- Clean unwanted files while keeping necessary assets.
- Extract game version from `version.scs`.
- Zip processed files for easy storage or distribution.
- User-friendly GUI with progress bar.
- Logging support (`log.txt`) for tracking processing steps.
- Runs safely on Windows (requires `converter_pix.exe`).

## Requirements

- **Python 3.10+**
- **Windows OS** (tested)
- `tkinter` (usually included with Python)
- `converter_pix.exe` (included in `data/` folder)
- SCS files list configuration (`data/scs_files.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MehdiAnti/SCS-Accessory-Extractor.git
cd scs-accessory-extractor
```
2. Ensure **Python 3.10+** is installed.
3. Make sure `converter_pix.exe` and `scs_files.txt` are in the data/ folder.


## Usage

1. Run the program:
```bash
python main.py
```
2. Click “Select Folder” to choose the directory containing your .scs files.
3. The program will process the files, clean unnecessary folders, and zip the results.
4. View progress on the progress bar and check log.txt for detailed logs.

      ⚠️ Only run one instance at a time to avoid conflicts in temporary folders and log files.


## Thanks to

[**mwl4**](https://github.com/mwl4) - [Converter PIX](https://github.com/mwl4/ConverterPIX) project

## License

This project is licensed under the **MIT License**.

## Contributing

Contributions are welcome! Please submit bug reports, feature requests, or pull requests via GitHub.

## Disclaimer

This tool is provided as-is. The author is not responsible for any damage or data loss resulting from its use. Always backup your files before processing.
