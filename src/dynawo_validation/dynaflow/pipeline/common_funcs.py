# Common functions for all contingency-generating scripts
import os
import sys
import glob
import subprocess
from lxml import etree
from collections import namedtuple


def check_inputfiles(input_case, dwo_paths, verbose=False):
    if not os.path.isdir(input_case):
        raise ValueError("source directory %s not found" % input_case)

    # remove trailing slash so that basename/dirname below behave consistently:
    if input_case[-1] == "/":
        input_case = input_case[:-1]
    basename = os.path.basename(input_case)
    dirname = os.path.dirname(input_case)
    # corner case: if called from the parent dir, dirname is empty
    if dirname == "":
        dirname = "."

    print("\nUsing input_case: %s" % input_case)
    print("New cases will be generated under: %s" % dirname)
    if verbose:
        print("input_case: %s" % input_case)
        print("basename: %s" % basename)
        print("dirname:  %s" % dirname)

    if not (
        os.path.isfile(input_case + "/Astre/donneesModelesEntree.xml")
        and os.path.isfile(input_case + "/" + dwo_paths.iidmFile)
        and os.path.isfile(input_case + "/" + dwo_paths.dydFile)
        and os.path.isfile(input_case + "/" + dwo_paths.parFile)
        and os.path.isfile(input_case + "/" + dwo_paths.curves_inputFile)
    ):
        raise ValueError("some expected files are missing in %s\n" % input_case)

    return input_case, basename, dirname


def copy_astdwo_basecase(base_case, dwo_paths, dest_case):
    # If the destination exists, remove it
    if os.path.exists(dest_case):
        remove_case(dest_case)
    # Make the subdirs for Astre and for the Dynawo job; and copy any non-changed
    # files (Dynawo's JOB file and the IIDM) using hard links
    iidm_dir = os.path.dirname(dwo_paths.iidmFile)
    dyd_dir = os.path.dirname(dwo_paths.dydFile)  # all these are usually the same
    par_dir = os.path.dirname(dwo_paths.parFile)  # but we allow themm to be different
    crv_dir = os.path.dirname(dwo_paths.curves_inputFile)  # just in case
    try:
        retcode = subprocess.call(
            f"mkdir -p '{dest_case}/Astre' '{dest_case}/{iidm_dir}'"
            f" '{dest_case}/{dyd_dir}' '{dest_case}/{par_dir}' '{dest_case}/{crv_dir}'"
            f" && cp -l '{dwo_paths.job_file}' '{dest_case}'"
            f" && cp -l '{base_case}/{dwo_paths.iidmFile}' '{dest_case}/{iidm_dir}'",
            shell=True,
        )
        if retcode < 0:
            raise ValueError("Copy operation was terminated by signal: %d" % -retcode)
        elif retcode > 0:
            raise ValueError("Copy operation returned error code: %d" % retcode)
    except OSError as e:
        print("Copy operation failed: ", e, file=sys.stderr)
        raise


def copy_dwohds_basecase(base_case, dwo_paths, dest_case):
    # If the destination exists, remove it
    if os.path.exists(dest_case):
        remove_case(dest_case)
    # Make the subdirs for Hades and for the Dynawo job; and copy all non-changed
    # files (Dynawo's JOB, IIDM, Diagrams, solver/network par files) using hard links
    spar_dir = os.path.dirname(dwo_paths.solver_parFile)
    npar_dir = os.path.dirname(dwo_paths.network_parFile)
    iidm_dir = os.path.dirname(dwo_paths.iidmFile)
    dyd_dir = os.path.dirname(dwo_paths.dydFile)  # all these are usually the same
    dyd_dir_contg = os.path.dirname(
        dwo_paths.dydFile_contg
    )  # all these are usually the same
    par_dir_contg = os.path.dirname(
        dwo_paths.parFile_contg
    )  # all these are usually the same
    par_dir = os.path.dirname(dwo_paths.parFile)  # but we allow themm to be different
    crv_dir = os.path.dirname(dwo_paths.curves_inputFile)  # just in case
    diag_dir = glob.glob(f"{base_case}/*_Diagram")
    if len(diag_dir) != 0:
        copy_diags_command = f" && cp -al '{diag_dir[0]}' '{dest_case}'"
    else:
        copy_diags_command = ""
    try:
        retcode = subprocess.call(
            f"mkdir -p '{dest_case}/Hades' '{dest_case}/{spar_dir}'"
            f" '{dest_case}/{npar_dir}' '{dest_case}/{par_dir}'"
            f" '{dest_case}/{crv_dir}'"
            f" && cp -l '{dwo_paths.job_file}' '{dest_case}'"
            f" && cp -l '{base_case}/{dwo_paths.solver_parFile}' '{dest_case}/{spar_dir}'"
            f" && cp -l '{base_case}/{dwo_paths.network_parFile}' '{dest_case}/{npar_dir}'"
            f" && cp -l '{base_case}/{dwo_paths.parFile}' '{dest_case}/{par_dir}'"
            f" && cp '{base_case}/{dwo_paths.dydFile_contg}' '{dest_case}/{dyd_dir_contg}'"
            f" && cp '{base_case}/{dwo_paths.parFile_contg}' '{dest_case}/{par_dir_contg}'"
            + copy_diags_command,
            shell=True,
        )
        if retcode < 0:
            raise ValueError("Copy operation was terminated by signal: %d" % -retcode)
        elif retcode > 0:
            raise ValueError("Copy operation returned error code: %d" % retcode)
    except OSError as e:
        print("Copy operation failed: ", e, file=sys.stderr)
        raise


def copy_dwodwo_basecase(base_case, dwo_pathsA, dwo_pathsB, dest_case):
    # If the destination exists, remove it
    if os.path.exists(dest_case):
        remove_case(dest_case)
    # Make the subdirs for Dynawo cases A & B; and copy any non-changed
    # files (Dynawo's JOB file and the IIDM) using hard links
    spar_dirA = os.path.dirname(dwo_pathsA.solver_parFile)
    npar_dirA = os.path.dirname(dwo_pathsA.network_parFile)
    iidm_dirA = os.path.dirname(dwo_pathsA.iidmFile)
    dyd_dirA = os.path.dirname(dwo_pathsA.dydFile)  # all these are usually the same
    par_dirA = os.path.dirname(dwo_pathsA.parFile)  # but we allow themm to be different
    crv_dirA = os.path.dirname(dwo_pathsA.curves_inputFile)  # just in case
    diag_dirA = glob.glob(f"{base_case}/A/*_Diagram")
    spar_dirB = os.path.dirname(dwo_pathsB.solver_parFile)
    npar_dirB = os.path.dirname(dwo_pathsB.network_parFile)
    iidm_dirB = os.path.dirname(dwo_pathsB.iidmFile)
    dyd_dirB = os.path.dirname(dwo_pathsB.dydFile)  # all these are usually the same
    par_dirB = os.path.dirname(dwo_pathsB.parFile)  # but we allow themm to be different
    crv_dirB = os.path.dirname(dwo_pathsB.curves_inputFile)  # just in case
    diag_dirB = glob.glob(f"{base_case}/B/*_Diagram")
    dyd_dir_contgA = os.path.dirname(
        dwo_pathsA.dydFile_contg
    )  # all these are usually the same
    par_dir_contgA = os.path.dirname(
        dwo_pathsA.parFile_contg
    )  # all these are usually the same
    dyd_dir_contgB = os.path.dirname(
        dwo_pathsB.dydFile_contg
    )  # all these are usually the same
    par_dir_contgB = os.path.dirname(
        dwo_pathsB.parFile_contg
    )  # all these are usually the same
    if len(diag_dirA) != 0:
        copy_diags_commandA = f" && cp -al '{diag_dirA[0]}' '{dest_case}/A'"
    else:
        copy_diags_commandA = ""
    if len(diag_dirB) != 0:
        copy_diags_commandB = f" && cp -al '{diag_dirB[0]}' '{dest_case}/B'"
    else:
        copy_diags_commandB = ""
    try:
        retcode = subprocess.call(
            f"mkdir -p '{dest_case}/{par_dirA}' '{dest_case}/{par_dirB}'"
            f" '{dest_case}/{crv_dirA}' '{dest_case}/{crv_dirB}'"
            f" '{dest_case}/{spar_dirA}' '{dest_case}/{spar_dirB}'"
            f" '{dest_case}/{npar_dirA}' '{dest_case}/{npar_dirB}'"
            f" && cp -l '{dwo_pathsA.job_file}' '{dest_case}'"
            f" && cp -l '{dwo_pathsB.job_file}' '{dest_case}'"
            f" && cp -l '{base_case}/{dwo_pathsA.parFile}' '{dest_case}/{par_dirA}'"
            f" && cp -l '{base_case}/{dwo_pathsB.parFile}' '{dest_case}/{par_dirB}'"
            f" && cp -l '{base_case}/{dwo_pathsA.solver_parFile}' '{dest_case}/{spar_dirA}'"
            f" && cp -l '{base_case}/{dwo_pathsB.solver_parFile}' '{dest_case}/{spar_dirB}'"
            f" && cp -l '{base_case}/{dwo_pathsA.network_parFile}' '{dest_case}/{npar_dirA}'"
            f" && cp -l '{base_case}/{dwo_pathsB.network_parFile}' '{dest_case}/{npar_dirB}'"
            f" && cp '{base_case}/{dwo_pathsA.dydFile_contg}' '{dest_case}/{dyd_dir_contgA}'"
            f" && cp '{base_case}/{dwo_pathsA.parFile_contg}' '{dest_case}/{par_dir_contgA}'"
            f" && cp '{base_case}/{dwo_pathsB.dydFile_contg}' '{dest_case}/{dyd_dir_contgB}'"
            f" && cp '{base_case}/{dwo_pathsB.parFile_contg}' '{dest_case}/{par_dir_contgB}'"
            + copy_diags_commandA
            + copy_diags_commandB,
            shell=True,
        )
        if retcode < 0:
            raise ValueError("Copy operation was terminated by signal: %d" % -retcode)
        elif retcode > 0:
            raise ValueError("Copy operation returned error code: %d" % retcode)
    except OSError as e:
        print("Copy operation failed: ", e, file=sys.stderr)
        raise


def clone_base_case(input_case, dest_case):
    # If the destination exists, remove it (it's temporary anyway)
    if os.path.exists(dest_case):
        remove_case(dest_case)

    try:
        retcode = subprocess.call(
            "rsync -aq --exclude 't0/' '%s/' '%s'" % (input_case, dest_case), shell=True
        )
        if retcode < 0:
            raise ValueError("Copy operation was terminated by signal: %d" % -retcode)
        elif retcode > 0:
            raise ValueError("Copy operation returned error code: %d" % retcode)
    except OSError as e:
        print("Copy operation failed: ", e, file=sys.stderr)
        raise


def remove_case(dest_case):
    try:
        retcode = subprocess.call("rm -rf '%s'" % dest_case, shell=True)
        if retcode < 0:
            raise ValueError("rm of bad case was terminated by signal: %d" % -retcode)
        elif retcode > 0:
            raise ValueError("rm of bad case returned error code: %d" % retcode)
    except OSError as e:
        print("call to rm failed: ", e, file=sys.stderr)
        raise


def dedup_save(basename, edited_case, deduped_case):
    # If the destination exists, warn and rename it to OLD
    if os.path.exists(deduped_case):
        print(
            "   WARNING: destination %s exists! -- renaming it to *__OLD__"
            % deduped_case
        )
        os.rename(deduped_case, deduped_case + "__OLD__")

    # Save it using "deduplication" (actually, hard links)
    dedup_cmd = "rsync -a --delete --link-dest='../%s' '%s/' '%s'" % (
        basename,
        edited_case,
        deduped_case,
    )
    try:
        retcode = subprocess.call(dedup_cmd, shell=True)
        if retcode < 0:
            raise ValueError("Copy operation was terminated by signal: %d" % -retcode)
        elif retcode > 0:
            raise ValueError("Copy operation returned error code: %d" % retcode)
    except OSError as e:
        print("Copy operation failed: ", e, file=sys.stderr)
        raise


def parse_basecase(base_case, dwo_paths, asthds_path, dwo_pathsA, dwo_pathsB):
    Parsed_case = namedtuple(
        "Parsed_case",
        "asthdsTree iidmTree parTree dydTree crvTree parTree_contg dydTree_contg",
    )
    Parsed_dwodwo_case = namedtuple("Parsed_dwodwo_case", "A B")

    if dwo_pathsA is None and dwo_pathsB is None:
        asthdsTree = etree.parse(
            base_case + asthds_path, etree.XMLParser(remove_blank_text=True)
        )
        iidmTree = etree.parse(
            base_case + "/" + dwo_paths.iidmFile,
            etree.XMLParser(remove_blank_text=True),
        )
        parTree = etree.parse(
            base_case + "/" + dwo_paths.parFile, etree.XMLParser(remove_blank_text=True)
        )
        dydTree = etree.parse(
            base_case + "/" + dwo_paths.dydFile, etree.XMLParser(remove_blank_text=True)
        )
        crvTree = etree.parse(
            base_case + "/" + dwo_paths.curves_inputFile,
            etree.XMLParser(remove_blank_text=True),
        )
        parTree_contg = etree.parse(
            base_case + "/" + dwo_paths.parFile_contg,
            etree.XMLParser(remove_blank_text=True),
        )
        dydTree_contg = etree.parse(
            base_case + "/" + dwo_paths.dydFile_contg,
            etree.XMLParser(remove_blank_text=True),
        )
        return Parsed_case(
            asthdsTree=asthdsTree,
            iidmTree=iidmTree,
            parTree=parTree,
            dydTree=dydTree,
            crvTree=crvTree,
            parTree_contg=parTree_contg,
            dydTree_contg=dydTree_contg,
        )
    else:
        iidmTreeA = etree.parse(
            base_case + "/" + dwo_pathsA.iidmFile,
            etree.XMLParser(remove_blank_text=True),
        )
        parTreeA = etree.parse(
            base_case + "/" + dwo_pathsA.parFile,
            etree.XMLParser(remove_blank_text=True),
        )
        dydTreeA = etree.parse(
            base_case + "/" + dwo_pathsA.dydFile,
            etree.XMLParser(remove_blank_text=True),
        )
        crvTreeA = etree.parse(
            base_case + "/" + dwo_pathsA.curves_inputFile,
            etree.XMLParser(remove_blank_text=True),
        )
        parTreeA_contg = etree.parse(
            base_case + "/" + dwo_pathsA.parFile_contg,
            etree.XMLParser(remove_blank_text=True),
        )
        dydTreeA_contg = etree.parse(
            base_case + "/" + dwo_pathsA.dydFile_contg,
            etree.XMLParser(remove_blank_text=True),
        )
        parsed_caseA = Parsed_case(
            asthdsTree=None,
            iidmTree=iidmTreeA,
            parTree=parTreeA,
            dydTree=dydTreeA,
            crvTree=crvTreeA,
            parTree_contg=parTreeA_contg,
            dydTree_contg=dydTreeA_contg,
        )

        iidmTreeB = etree.parse(
            base_case + "/" + dwo_pathsB.iidmFile,
            etree.XMLParser(remove_blank_text=True),
        )
        parTreeB = etree.parse(
            base_case + "/" + dwo_pathsB.parFile,
            etree.XMLParser(remove_blank_text=True),
        )
        dydTreeB = etree.parse(
            base_case + "/" + dwo_pathsB.dydFile,
            etree.XMLParser(remove_blank_text=True),
        )
        crvTreeB = etree.parse(
            base_case + "/" + dwo_pathsB.curves_inputFile,
            etree.XMLParser(remove_blank_text=True),
        )
        parTreeB_contg = etree.parse(
            base_case + "/" + dwo_pathsB.parFile_contg,
            etree.XMLParser(remove_blank_text=True),
        )
        dydTreeB_contg = etree.parse(
            base_case + "/" + dwo_pathsB.dydFile_contg,
            etree.XMLParser(remove_blank_text=True),
        )
        parsed_caseB = Parsed_case(
            asthdsTree=None,
            iidmTree=iidmTreeB,
            parTree=parTreeB,
            dydTree=dydTreeB,
            crvTree=crvTreeB,
            parTree_contg=parTreeB_contg,
            dydTree_contg=dydTreeB_contg,
        )

        return Parsed_dwodwo_case(A=parsed_caseA, B=parsed_caseB)
