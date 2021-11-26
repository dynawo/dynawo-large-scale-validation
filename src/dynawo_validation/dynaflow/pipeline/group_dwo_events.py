#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# (c) Grupo AIA
#

import pandas as pd
import sys
import argparse
from lxml import etree
import networkx as nx
import math
THRESHOLD = 50

parser = argparse.ArgumentParser()
parser.add_argument(
    "dynawoautomata",
    help="Enter Dynawo Automata csv.xz file",
)

parser.add_argument(
    "iidmfile_basecase",
    help="Enter iidm file",
)


args = parser.parse_args()

def main():
    dynawoautomata = args.dynawoautomata
    iidm_file = args.iidmfile_basecase

    # Remove a possible trailing slash
    if iidm_file[-1] == "/":
        iidm_file = iidm_file[:-1]

    df = read_aut_changes(dynawoautomata)
    aut_df = filter_dwo_events(df)
    aut_df["BUS"] = define_buses(aut_df, iidm_file)
    for i in range(len(aut_df.index)):
        if len(aut_df.loc[i, "BUS"].split("%")) != 1:
            list_bus = aut_df.loc[i, "BUS"].split("%")
            aut_df.loc[i, "BUS"] = list_bus[0]
            aut_df.loc[len(aut_df.index)] = aut_df.loc[i,:]
            aut_df.loc[len(aut_df.index) - 1, "BUS"] = list_bus[1]

    graph = create_graph(iidm_file)
    small_distance_matrix = create_distance_matrix(graph, aut_df)
    groups = group_dwo_events(aut_df, small_distance_matrix)

    print(small_distance_matrix)
    print(groups)
    for i in range(len(groups)):
        print("GROUP " + str(i) + " ----------------------")
        for j in range(len(groups[i])):
            print(list(aut_df.loc[groups[i][j], :]))
        print("\n")
        print("\n")
        print("\n")


def read_aut_changes(aut_dir):
    data = pd.read_csv(aut_dir, sep=";")
    return data


def filter_dwo_events(df):
    aut_df = df.loc[(df.DEVICE_TYPE == "Transformer") | (df.DEVICE_TYPE == "Shunt") | (df.DEVICE_TYPE == "Generator") | (df.DEVICE_TYPE == "Line") | (df.DEVICE_TYPE == "Load")]
    return aut_df


def define_buses(aut_df, iidm_file):
    iidmTree = etree.parse(iidm_file, etree.XMLParser(remove_blank_text=True))
    root = iidmTree.getroot()
    ns = etree.QName(root).namespace

    bus_names = []
    for df_i in range(len(aut_df.index)):
        if aut_df.loc[df_i, "DEVICE_TYPE"] == "Line":
            for line in root.iter("{%s}line" % ns):
                if line.get("id") == aut_df.loc[df_i, "DEVICE"]:
                    bus1 = line.get("connectableBus1")
                    if bus1 is not None:
                        bus2 = line.get("connectableBus2")
                        if bus2 is not None:
                            bus_names.append(bus1 + "%" + bus2)

        if aut_df.loc[df_i, "DEVICE_TYPE"] == "Transformer":
            for trans in root.iter("{%s}twoWindingsTransformer" % ns):
                if trans.get("id") == aut_df.loc[df_i, "DEVICE"]:
                    bus1 = trans.get("connectableBus1")
                    if bus1 is not None:
                        bus2 = trans.get("connectableBus2")
                        if bus2 is not None:
                            bus_names.append(bus1 + "%" + bus2)

        if aut_df.loc[df_i, "DEVICE_TYPE"] == "Shunt":
            for shunt in root.iter("{%s}shunt" % ns):
                if shunt.get("id") == aut_df.loc[df_i, "DEVICE"]:
                    bus = shunt.get("connectableBus")
                    if bus is not None:
                        bus_names.append(bus)

        if aut_df.loc[df_i, "DEVICE_TYPE"] == "Generator":
            for gen in root.iter("{%s}generator" % ns):
                if gen.get("id") == aut_df.loc[df_i, "DEVICE"]:
                    bus = gen.get("connectableBus")
                    if bus is not None:
                        bus_names.append(bus)

        if aut_df.loc[df_i, "DEVICE_TYPE"] == "Load":
            for load in root.iter("{%s}load" % ns):
                if load.get("id") == aut_df.loc[df_i, "DEVICE"]:
                    bus = load.get("connectableBus")
                    if bus is not None:
                        bus_names.append(bus)

    if len(bus_names) != len(aut_df.index):
        raise Exception("Some AUT IDs not found or disconnected in input file.")

    return bus_names


def create_graph(iidm_file):
    iidmTree = etree.parse(iidm_file, etree.XMLParser(remove_blank_text=True))

    # Create the graph
    G = nx.Graph()

    # Call the function that will insert all the buses as nodes of the graph
    G = insert_buses(iidmTree, G)

    # Call the function that will insert the lines as edges
    G = insert_lines(iidmTree, G)

    # Call the function that will insert the transformers as edges
    n_edges = G.number_of_edges()
    G = insert_transformers(iidmTree, G, n_edges)

    # Call the function that will insert the HVDCLines as edges
    n_edges = G.number_of_edges()
    G = insert_HVDCLines(iidmTree, G, n_edges)

    return G



def insert_buses(iidm_tree, G):
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    # We enumerate all buses and put them in the graph
    for bus in root.iter("{%s}bus" % ns):
        idb = bus.get("id")
        if idb is not None:
            G.add_node(idb)

    return G


def insert_lines(iidm_tree, G):
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    # We enumerate all lines and put them in the graph
    for line in root.iter("{%s}line" % ns):
        bus1 = line.get("bus1")
        if bus1 is not None:
            bus2 = line.get("bus2")
            if bus2 is not None:
                imp = complex(float(line.get("r")), float(line.get("x")))
                adm = 1 / (math.sqrt(pow(imp.real, 2) + pow(imp.imag, 2)))
                p1 = abs(float(line.get("p1")))
                line_id = line.get("id")
                if (bus1, bus2) not in G.edges:
                    G.add_edge(bus1, bus2, value=adm, id=line_id, pa=p1, imp=1 / adm)
                else:
                    prev_dict = G.get_edge_data(bus1, bus2)
                    G.add_edge(
                        bus1,
                        bus2,
                        value=adm + prev_dict["value"],
                        id=prev_dict["id"] + "__" + line_id,
                        pa=p1 + prev_dict["pa"],
                        imp=1 / (adm + prev_dict["value"]),
                    )

    return G


def insert_transformers(iidm_tree, G, n_edges):
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    # We enumerate all transformers and put them in the graph
    for trans in root.iter("{%s}twoWindingsTransformer" % ns):
        bus1 = trans.get("bus1")
        if bus1 is not None:
            bus2 = trans.get("bus2")
            if bus2 is not None:
                imp = complex(float(trans.get("r")), float(trans.get("x")))
                adm = 1 / (math.sqrt(pow(imp.real, 2) + pow(imp.imag, 2)))
                trans_id = trans.get("id")
                p1 = abs(float(trans.get("p1")))
                if (bus1, bus2) not in G.edges:
                    G.add_edge(bus1, bus2, value=adm, id=trans_id, pa=p1, imp=1 / adm)
                else:
                    prev_dict = G.get_edge_data(bus1, bus2)
                    G.add_edge(
                        bus1,
                        bus2,
                        value=adm + prev_dict["value"],
                        id=prev_dict["id"] + "__" + trans_id,
                        pa=p1 + prev_dict["pa"],
                        imp=1 / (adm + prev_dict["value"]),
                    )

    return G


def insert_HVDCLines(iidm_tree, G, n_edges):
    root = iidm_tree.getroot()
    ns = etree.QName(root).namespace

    # We enumerate all HVDCLines and put them in the graph
    for hvdc in root.iter("{%s}hvdcLine" % ns):
        converterStation1 = hvdc.get("converterStation1")
        if converterStation1 is not None:
            connected = False
            for converterStation in root.iter("{%s}vscConverterStation" % ns):
                if converterStation1 == converterStation.get("id"):
                    bus1 = converterStation.get("bus")
                    if bus1 is not None:
                        p1 = abs(float(converterStation.get("p")))
                        connected = True

            if connected:
                converterStation2 = hvdc.get("converterStation2")
                if converterStation2 is not None:
                    connected = False
                    for converterStation in root.iter("{%s}vscConverterStation" % ns):
                        if converterStation2 == converterStation.get("id"):
                            bus2 = converterStation.get("bus")
                            if bus2 is not None:
                                connected = True

                    if connected:
                        adm = 1 / float(hvdc.get("r"))
                        hvdc_id = hvdc.get("id")
                        if (bus1, bus2) not in G.edges:
                            G.add_edge(
                                bus1, bus2, value=adm, id=hvdc_id, pa=p1, imp=1 / adm
                            )
                        else:
                            prev_dict = G.get_edge_data(bus1, bus2)
                            G.add_edge(
                                bus1,
                                bus2,
                                value=adm + prev_dict["value"],
                                id=prev_dict["id"] + "__" + hvdc_id,
                                pa=p1 + prev_dict["pa"],
                                imp=1 / (adm + prev_dict["value"]),
                            )

    return G


def create_distance_matrix(graph, aut_df):
    distance_matrix = []
    for df_i in range(len(aut_df.index)):
        distance_matrix.append([])
        for df_j in range(len(aut_df.index)):
            shortest_path = nx.shortest_path_length(
                graph, source=aut_df.loc[df_i, "BUS"], target=aut_df.loc[df_j, "BUS"], weight="imp"
            )
            distance_matrix[df_i].append(shortest_path)

    return distance_matrix


def group_dwo_events(aut_df, small_distance_matrix):
    temp_list = list(range(len(aut_df.index)))
    fix_list = list(range(len(aut_df.index)))
    groups = []
    n_groups = 0
    for i in range(len(temp_list)):
        if temp_list[i] != "x":
            groups.append([])
            for j in range(len(aut_df.index)):
                if small_distance_matrix[fix_list[i]][j] < THRESHOLD:
                    temp_list[j] = "x"
                    groups[n_groups].append(j)
            n_groups += 1

    return groups


if __name__ == "__main__":
    sys.exit(main())
