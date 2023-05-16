from lxml import etree
from pathlib import Path, PurePath
from dynawo_contingencies_screening.commons import manage_files
from dynawo_contingencies_screening.prepare_basecase import create_contingencies


def get_dynawo_branches(dynawo_iidm_root, ns):
    dynawo_branches = []

    # Get all the connected branches' name
    for dynawo_branch in dynawo_iidm_root.iter("{%s}line" % ns, "{%s}twoWindingsTransformer" % ns):
        if (float(dynawo_branch.get("p1")) == 0.0 and float(dynawo_branch.get("q1")) == 0.0) or (
            float(dynawo_branch.get("p2")) == 0.0 and float(dynawo_branch.get("q2")) == 0.0
        ):
            continue
        branch_name = dynawo_branch.get("id")
        branch_tag = etree.QName(dynawo_branch).localname
        if branch_tag == "line":
            branch_type = "Line"
        elif branch_tag == "twoWindingsTransformer":
            if dynawo_branch.find("{%s}phaseTapChanger" % ns) is None:
                branch_type = "Transformer"
            else:
                branch_type = "PhaseShitfer"

        # Get the buses we need to disconnect
        bus_from = create_contingencies.get_endbus(
            dynawo_iidm_root, dynawo_branch, branch_type, "1"
        )
        bus_to = create_contingencies.get_endbus(dynawo_iidm_root, dynawo_branch, branch_type, "2")

        if bus_from is None or bus_to is None:  # skip branch
            continue

        dynawo_branches.append(branch_name)

    return dynawo_branches


def get_hades_branches(hades_root):
    hades_branches = set()  # For faster matching

    reseau = hades_root.find("./reseau", hades_root.nsmap)
    donneesQuadripoles = reseau.find("./donneesQuadripoles", hades_root.nsmap)

    # Get all the connected branches' name
    for branch in donneesQuadripoles.iterfind("./quadripole", hades_root.nsmap):
        hades_branches.add(branch.get("nom"))

    return hades_branches


def extract_matching_branches(hades_root, dynawo_iidm_root):
    # Get all the Dynawo branches
    ns = etree.QName(dynawo_iidm_root).namespace
    dynawo_branches = get_dynawo_branches(dynawo_iidm_root, ns)

    # Get all the Hades branches
    hades_branches = get_hades_branches(hades_root)

    # Get the matching branches
    matched_branches = [x for x in dynawo_branches if x in hades_branches]

    return matched_branches


def get_dynawo_generators(dynawo_iidm_root, ns):
    dynawo_generators = []

    # Get all the connected generators' name
    for gen in dynawo_iidm_root.iter("{%s}generator" % ns):
        P_val = float(gen.get("p"))
        if gen.get("q") is not None:
            Q_val = float(gen.get("q"))
        else:
            Q_val = float(gen.get("targetQ"))
        # Skip disconnected (detection via p,q to accommodate BUS_BREAKER/NODE_BREAKER)
        if P_val == 0.0 and Q_val == 0.0:
            continue
        if gen.get("bus") is None:
            continue

        gen_name = gen.get("id")

        dynawo_generators.append(gen_name)

    return dynawo_generators


def get_hades_generators(hades_root):
    hades_generators = set()  # For faster matching

    reseau = hades_root.find("./reseau", hades_root.nsmap)
    donneesGroupes = reseau.find("./donneesGroupes", hades_root.nsmap)

    # Get all the connected generators' name
    for gen in donneesGroupes.iterfind("./groupe", hades_root.nsmap):
        # Discard gens having noeud="-1"
        if gen.get("noeud") != "-1":
            hades_generators.add(gen.get("nom"))

    return hades_generators


def extract_matching_generators(hades_root, dynawo_iidm_root):
    ns = etree.QName(dynawo_iidm_root).namespace
    dynawo_generators = get_dynawo_generators(dynawo_iidm_root, ns)

    # Get all the Hades branches
    hades_generators = get_hades_generators(hades_root)

    # Get the matching branches
    matched_generators = [x for x in dynawo_generators if x in hades_generators]

    return matched_generators


def get_dynawo_loads(dynawo_iidm_root, dynawo_dyd_root):
    dynawo_loads = []
    dm_loads = dict()

    # We first enumerate all loads from the DYD and keep their model type
    ns_dyd = etree.QName(dynawo_dyd_root).namespace
    for bbm in dynawo_dyd_root.iter("{%s}blackBoxModel" % ns_dyd):
        if bbm.get("lib") in create_contingencies.LOAD_MODELS:
            dm_loads[bbm.get("id")] = bbm.get("lib")

    # Get all the connected loads' name
    ns = etree.QName(dynawo_iidm_root).namespace
    for load in dynawo_iidm_root.iter("{%s}load" % ns):
        load_name = load.get("id")
        if load_name not in dm_loads:
            continue
        topo_val = load.getparent().get("topologyKind")
        if topo_val == "BUS_BREAKER":
            bus_name = load.get("bus")
            if bus_name is None:
                continue

        dynawo_loads.append(load_name)

    return dynawo_loads


def get_hades_loads(hades_root):
    hades_loads = set()  # For faster matching

    reseau = hades_root.find("./reseau", hades_root.nsmap)
    donneesConsos = reseau.find("./donneesConsos", hades_root.nsmap)
    for load in donneesConsos.iterfind("./conso", hades_root.nsmap):
        # Discard loads having noeud="-1"
        if load.get("noeud") != "-1":
            hades_loads.add(load.get("nom"))

    return hades_loads


def extract_matching_loads(hades_root, dynawo_iidm_root, dynawo_dyd_root):
    dynawo_loads = get_dynawo_loads(dynawo_iidm_root, dynawo_dyd_root)

    # Get all the Hades loads
    hades_loads = get_hades_loads(hades_root)

    # Get the matching loads
    matched_loads = [x for x in dynawo_loads if x in hades_loads]

    return matched_loads


def get_dynawo_shunts(dynawo_iidm_root, ns):
    dynawo_shunts = []

    # We enumerate all shunts and extract their properties
    for shunt in dynawo_iidm_root.iter("{%s}shunt" % ns):
        if shunt.get("bus") is not None:
            shunt_name = shunt.get("id")
            dynawo_shunts.append(shunt_name)

    return dynawo_shunts


def get_hades_shunts(hades_root):
    hades_shunts = set()  # For faster matching

    reseau = hades_root.find("./reseau", hades_root.nsmap)
    donneesShunts = reseau.find("./donneesShunts", hades_root.nsmap)
    for shunt in donneesShunts.iterfind("./shunt", hades_root.nsmap):
        # Discard shunts having noeud="-1"
        if shunt.get("noeud") != "-1":
            hades_shunts.add(shunt.get("nom"))

    return hades_shunts


def extract_matching_shunts(hades_root, dynawo_iidm_root):
    ns = etree.QName(dynawo_iidm_root).namespace
    dynawo_shunts = get_dynawo_shunts(dynawo_iidm_root, ns)

    # Get all the Hades loads
    hades_shunts = get_hades_shunts(hades_root)

    # Get the matching loads
    matched_shunts = [x for x in dynawo_shunts if x in hades_shunts]

    return matched_shunts


def matching_elements(hades_input_file, dynawo_job_file):
    # Get the needed dynawo file paths from the JOB file
    parsed_input_xml = manage_files.parse_xml_file(dynawo_job_file)
    root = parsed_input_xml.getroot()
    ns = etree.QName(root).namespace

    jobs = root.findall("{%s}job" % ns)
    last_job = jobs[-1]  # contemplate only the *last* job, in case there are several
    modeler = last_job.find("{%s}modeler" % ns)
    dynModels = modeler.findall("{%s}dynModels" % ns)
    dyd_file = dynModels[0].get("dydFile")
    network = modeler.find("{%s}network" % ns)
    iidm_file = network.get("iidmFile")

    iidm_file_path = PurePath(dynawo_job_file.absolute()).parent / iidm_file
    dyd_file_path = PurePath(dynawo_job_file.absolute()).parent / dyd_file

    # Parse the necessary files
    hades_input_file_parsed = manage_files.parse_xml_file(hades_input_file)
    hades_root = hades_input_file_parsed.getroot()
    dynawo_iidm_file_parsed = manage_files.parse_xml_file(iidm_file_path)
    dynawo_iidm_root = dynawo_iidm_file_parsed.getroot()
    dynawo_dyd_file_parsed = manage_files.parse_xml_file(dyd_file_path)
    dynawo_dyd_root = dynawo_dyd_file_parsed.getroot()

    # Extract the matching elements for each type
    matched_branches = extract_matching_branches(hades_root, dynawo_iidm_root)
    matched_generators = extract_matching_generators(hades_root, dynawo_iidm_root)
    matched_loads = extract_matching_loads(hades_root, dynawo_iidm_root, dynawo_dyd_root)
    matched_shunts = extract_matching_shunts(hades_root, dynawo_iidm_root)

    return matched_branches, matched_generators, matched_loads, matched_shunts
