import os
import pandas as pd
import matplotlib.pyplot as plt
import tqdm
import numpy as np
import seaborn as sns
from datetime import datetime
import statistics
import plotly.graph_objects as go
from lxml import etree
from pathlib import Path


def load_df(path):
    path = Path(path)
    first_df = True
    for year_dir in path.iterdir():
        if year_dir.is_file():
            continue
        for month_dir in year_dir.iterdir():
            if month_dir.is_file():
                continue
            for day_dir in month_dir.iterdir():
                if day_dir.is_file():
                    continue
                for time_dir in day_dir.iterdir():
                    if first_df:
                        first_df = False
                        df_contg = pd.read_csv(time_dir / "contg_df.csv", sep=";", index_col="NAME")
                        time_str = (time_dir.stem).replace("recollement-auto-", "").replace("-enrichi", "")
                        df_contg["DATE"] = time_str + "00"
                        df_contg["DATE"] = pd.to_datetime(df_contg["DATE"], format="%Y%m%d-%H%M%S")
                    else:
                        df_new = pd.read_csv(time_dir / "contg_df.csv", sep=";", index_col="NAME")
                        time_str = (time_dir.stem).replace("recollement-auto-", "").replace("-enrichi", "")
                        df_new["DATE"] = time_str + "00"
                        df_new["DATE"] = pd.to_datetime(df_new["DATE"], format="%Y%m%d-%H%M%S")
                        df_contg = pd.concat([df_contg, df_new], axis=0, ignore_index=False)
    
    return df_contg.dropna()


def all_time_top(df_filtered):
    dict_cont = {}

    list_index = list(df_filtered.index)

    for i in range(len(list_index)):
        row_i = df_filtered.iloc[i]
        index_i = list_index[i]
        # Choose border contingencies
        """
        if index_i[0] == ".":
            if index_i not in dict_cont:
                dict_cont[index_i] = [row_i["REAL_SCORE"]]
            else:
                dict_cont[index_i].append(row_i["REAL_SCORE"])
        """
        if index_i not in dict_cont:
            dict_cont[index_i] = [row_i["REAL_SCORE"]]
        else:
            dict_cont[index_i].append(row_i["REAL_SCORE"])

    for i in list(dict_cont.keys()):
        dict_cont[i] = statistics.median(dict_cont[i])

    dict_cont = dict(sorted(dict_cont.items(), key=lambda item: item[1], reverse=True))

    j = 1
    for i in list(dict_cont.items())[:10]:
        print(j, ":", i[0], "-", i[1])
        j += 1


def week_day_top(df_filtered):
    day_list = []
    for i in range(len(df_filtered.index)):
        row_i = df_filtered.iloc[i]

        day_list.append(datetime.strptime(str(row_i["DATE"]), "%Y-%m-%d %H:%M:%S").weekday())

    df_filtered["W_DAY"] = day_list

    df_list = []

    for i in range(7):
        df_list.append(df_filtered.groupby(df_filtered["W_DAY"] == i).get_group(True))

    list_dicts = []
    for df_i in df_list:
        dict_cont = {}
        list_index = list(df_i.index)
        for i in range(len(df_i.index)):
            row_i = df_i.iloc[i]
            index_i = list_index[i]
            if index_i not in dict_cont:
                dict_cont[index_i] = [row_i["REAL_SCORE"]]
            else:
                dict_cont[index_i].append(row_i["REAL_SCORE"])
        for i in list(dict_cont.keys()):
            dict_cont[i] = statistics.median(dict_cont[i])

        dict_cont = dict(sorted(dict_cont.items(), key=lambda item: item[1], reverse=True))
        list_dicts.append(list(dict_cont.keys())[:14])

    for i in range(len(list_dicts)):
        print()
        print(i)
        print()
        if i == 0:
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[i + 1]:
                    if pos_i not in list_dicts[(len(list_dicts) - 1)]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[(len(list_dicts) - 1)]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)
        elif i == (len(list_dicts) - 1):
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[0]:
                    if pos_i not in list_dicts[i - 1]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[i - 1]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)
        else:
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[i + 1]:
                    if pos_i not in list_dicts[i - 1]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[i - 1]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)


def month_top(df_filtered):
    month_list = []
    for i in range(len(df_filtered.index)):
        row_i = df_filtered.iloc[i]

        month_list.append(datetime.strptime(str(row_i["DATE"]), "%Y-%m-%d %H:%M:%S").month)

    df_filtered["MONTH"] = month_list

    df_list = []

    for i in [1, 2, 6]:
        df_list.append(df_filtered.groupby(df_filtered["MONTH"] == i).get_group(True))

    list_dicts = []
    for df_i in df_list:
        dict_cont = {}
        list_index = list(df_i.index)
        for i in range(len(df_i.index)):
            row_i = df_i.iloc[i]
            index_i = list_index[i]
            if index_i not in dict_cont:
                dict_cont[index_i] = [row_i["REAL_SCORE"]]
            else:
                dict_cont[index_i].append(row_i["REAL_SCORE"])
        for i in list(dict_cont.keys()):
            dict_cont[i] = statistics.median(dict_cont[i])

        dict_cont = dict(sorted(dict_cont.items(), key=lambda item: item[1], reverse=True))
        list_dicts.append(list(dict_cont.keys())[:14])

    for i in range(len(list_dicts)):
        print()
        print(i)
        print()
        if i == 0:
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[i + 1]:
                    if pos_i not in list_dicts[(len(list_dicts) - 1)]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[(len(list_dicts) - 1)]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)
        elif i == (len(list_dicts) - 1):
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[0]:
                    if pos_i not in list_dicts[i - 1]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[i - 1]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)
        else:
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[i + 1]:
                    if pos_i not in list_dicts[i - 1]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[i - 1]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)


def hour_top(df_filtered):
    hour_list = []
    for i in range(len(df_filtered.index)):
        row_i = df_filtered.iloc[i]
        hour_list.append(datetime.strptime(str(row_i["DATE"]), "%Y-%m-%d %H:%M:%S").hour)

    df_filtered["HOUR"] = hour_list

    df_list = []

    for i in range(24):
        df_list.append(df_filtered.groupby(df_filtered["HOUR"] == i).get_group(True))

    list_dicts = []
    for df_i in df_list:
        dict_cont = {}
        list_index = list(df_i.index)
        for i in range(len(df_i.index)):
            row_i = df_i.iloc[i]
            index_i = list_index[i]
            if index_i not in dict_cont:
                dict_cont[index_i] = [row_i["REAL_SCORE"]]
            else:
                dict_cont[index_i].append(row_i["REAL_SCORE"])
        for i in list(dict_cont.keys()):
            dict_cont[i] = statistics.median(dict_cont[i])

        dict_cont = dict(sorted(dict_cont.items(), key=lambda item: item[1], reverse=True))
        list_dicts.append(list(dict_cont.keys())[:14])

    for i in range(len(list_dicts)):
        print()
        print(i)
        print()
        if i == 0:
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[i + 1]:
                    if pos_i not in list_dicts[(len(list_dicts) - 1)]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[(len(list_dicts) - 1)]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)
        elif i == (len(list_dicts) - 1):
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[0]:
                    if pos_i not in list_dicts[i - 1]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[i - 1]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)
        else:
            for pos_i in list_dicts[i]:
                if pos_i not in list_dicts[i + 1]:
                    if pos_i not in list_dicts[i - 1]:
                        print("-+", pos_i)
                    else:
                        print("- ", pos_i)
                elif pos_i not in list_dicts[i - 1]:
                    print(" +", pos_i)
                else:
                    print("  ", pos_i)


def hour_boxplot(df_contg, str_score):
    str_date_1 = "2023-06-22 00:00:00"
    str_date_2 = "2023-06-22 23:59:59"
    df_contg = df_contg.sort_values(by="DATE", ascending=True)

    mask = (df_contg["DATE"] > datetime.strptime(str_date_1, "%Y-%m-%d %H:%M:%S")) & (
        df_contg["DATE"] <= datetime.strptime(str_date_2, "%Y-%m-%d %H:%M:%S")
    )

    df_filtered = df_contg.loc[mask]

    df_filtered = df_filtered[df_filtered["STATUS"] == "BOTH"]

    # Creating dataset
    ax = plt.axes()
    ax.set_facecolor("white")
    sns.boxplot(
        x=df_filtered["DATE"].dt.strftime("%Y/%m/%d, %H:%M"),
        y=pd.to_numeric(df_filtered[str_score]),
    ).set(xlabel="DATE", ylabel=str_score)

    plt.xticks(rotation=90)
    plt.ylim(2000, 14000)
    plt.grid(color="grey", linewidth=0.5)


def day_boxplot(df_contg, str_score):
    str_date_1 = "2023-01-01 00:00:00"
    str_date_2 = "2023-01-31 23:59:59"
    df_contg = df_contg.sort_values(by="DATE", ascending=True)

    mask = (df_contg["DATE"] > datetime.strptime(str_date_1, '%Y-%m-%d %H:%M:%S')) & (df_contg["DATE"] <= datetime.strptime(str_date_2, '%Y-%m-%d %H:%M:%S'))

    df_filtered = df_contg.loc[mask]

    df_filtered = df_filtered[df_filtered["STATUS"] == "BOTH"]

    df_filtered['DATE'] = pd.to_datetime(df_filtered['DATE'], format='%Y-%m-%d %H:%M:%S').dt.date

    # Creating dataset
    sns.set(rc={"figure.figsize":(10, 3)})
    ax = plt.axes()
    ax.set_facecolor("white")
    sns.boxplot(x=df_filtered["DATE"], y=pd.to_numeric(df_filtered[str_score])).set(
                xlabel='DATE', 
                ylabel=str_score)
    plt.xticks(rotation=90)
    plt.ylim(2000, 14000)
    plt.grid(color='grey', linewidth=0.5)


def score_histogram(df_contg, column_name):
    def convertable_to_float(string):
        try:
            result = float(string)
            return result
        except ValueError:
            return 100000

    df_filtered = df_contg

    df_filtered[column_name] = df_filtered[column_name].apply(convertable_to_float)

    df_filtered = df_filtered[df_filtered[column_name] < 20000]

    column_data = df_filtered[column_name]

    # Create the histogram using matplotlib
    ax = plt.axes()
    ax.set_facecolor("white")
    ax.spines["left"].set_color("black")
    ax.spines["bottom"].set_color("black")
    ax.spines["top"].set_color("black")
    ax.spines["right"].set_color("black")
    plt.hist(column_data, bins=50)  # Adjust the number of bins as per your preference

    # Customize the plot (optional)
    plt.xlabel(column_name)
    plt.ylabel("FREQUENCY")

    # Display the histogram
    plt.grid(color="grey", linewidth=0.5)
