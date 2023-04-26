from pathlib import Path, PurePath


def check_basecase_dir(input_dir):
    # Check input has both directories
    if not Path(input_dir / "dynawo").is_dir():
        print("Error: missing 'dynawo' directory in the input folder (name must be as shown in this message)")
        exit()
    if not Path(input_dir / "hades").is_dir():
        print("Error: missing 'hades' directory in the input folder (name must be as shown in this message)")
        exit()

    # Check hades dir is not empty and has only 1 file ('donneesEntreeHADES2*.xml')
    has_next = next(Path(input_dir / "hades").iterdir(), None)
    if has_next is not None:
        for file in Path(input_dir / "hades").iterdir():
            if not (PurePath(file).name.startswith("donneesEntreeHADES2")) or (file.suffix != ".xml"):
                print("Error: 'hades' directory in the input folder "
                      "should only contain the 'donneesEntreeHADES2*.xml' case-file")
                exit()
    else:
        print("Error: 'hades' directory in the input folder should not be empty")
        exit()

    # TODO: Check dynawo directory
