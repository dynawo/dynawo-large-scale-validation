from pathlib import PurePath
import warnings


def check_basecase_dir(input_dir):
    # Check input has both directories
    if not (input_dir / "dynawo").is_dir():
        exit(
            "Error: missing 'dynawo' directory in the input folder (name must be as shown in this message)"
        )
    if not (input_dir / "hades").is_dir():
        exit(
            "Error: missing 'hades' directory in the input folder (name must be as shown in this message)"
        )

    # Check for unnecessary elements in the directory
    for file in input_dir.iterdir():
        if PurePath(file).name != "dynawo" and PurePath(file).name != "hades":
            warnings.warn("Input directory should only contain the 'dynawo' and 'hades' folders")
            break

    # Check hades dir is not empty and has only 1 file ('donneesEntreeHADES2*.xml')
    has_next = next((input_dir / "hades").iterdir(), None)
    if has_next is not None:
        for file in (input_dir / "hades").iterdir():
            if not (PurePath(file).name.startswith("donneesEntreeHADES2")) or (
                file.suffix != ".xml"
            ):
                exit(
                    "Error: 'hades' directory in the input folder "
                    "should only contain the 'donneesEntreeHADES2*.xml' case-file"
                )
    else:
        exit("Error: 'hades' directory in the input folder should not be empty")

    # Check dynawo dir is not empty and contains the iidm file
    has_next = next((input_dir / "dynawo").iterdir(), None)
    if has_next is not None:
        for file in (input_dir / "dynawo").iterdir():
            iidm_file = list((input_dir / "dynawo").glob("*.*iidm"))
            if len(iidm_file) == 0:
                exit(
                    "Error: 'dynawo' directory in the input folder "
                    "does not contain the 'iidm' case-file"
                )
            if file != iidm_file[0]:
                exit(
                    "Error: 'dynawo' directory in the input folder "
                    "should only contain the 'iidm' case-file"
                )
    else:
        exit("Error: 'dynawo' directory in the input folder should not be empty")
