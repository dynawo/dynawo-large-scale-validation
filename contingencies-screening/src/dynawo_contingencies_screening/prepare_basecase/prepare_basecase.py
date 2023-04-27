from pathlib import Path, PurePath
import warnings


def check_basecase_dir(input_dir):
    # Check input has both directories
    if not Path(input_dir / "dynawo").is_dir():
        exit("Error: missing 'dynawo' directory in the input folder (name must be as shown in this message)")
    if not Path(input_dir / "hades").is_dir():
        exit("Error: missing 'hades' directory in the input folder (name must be as shown in this message)")

    for file in input_dir.iterdir():
        if PurePath(file).name != "dynawo" and PurePath(file).name != "hades":
            warnings.warn("Input directory should only contain the 'dynawo' and 'hades' folders")
            break

    # Check hades dir is not empty and has only 1 file ('donneesEntreeHADES2*.xml')
    has_next = next(Path(input_dir / "hades").iterdir(), None)
    if has_next is not None:
        for file in Path(input_dir / "hades").iterdir():
            if not (PurePath(file).name.startswith("donneesEntreeHADES2")) or (file.suffix != ".xml"):
                exit("Error: 'hades' directory in the input folder "
                     "should only contain the 'donneesEntreeHADES2*.xml' case-file")
    else:
        exit("Error: 'hades' directory in the input folder should not be empty")

    # TODO: Check dynawo directory
