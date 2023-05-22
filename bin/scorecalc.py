#!/usr/bin/env python3

#__________________________________________________
# ScoreCulculator
# author: NAKADA Yoshiyuki
# December 6, 2022
# Licence: MIT License
#__________________________________________________

import os
import sys
import PySimpleGUI as sg
import json
import pyperclip

#__________________________________________________
# GUI configuration

sg.theme("SystemDefault")
# Window = sg.Window("score calculator", return_keyboard_events=True)
Window = sg.Window("score calculator")

TextFont1  = ("Arial", 15)
TextFont2  = ("Arial", 12)
TextFont3  = ("Menlo", 15)
ButtonFont = ("Arial", 11)

#__________________________________________________
# global variables

ConfigPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../conf/default.json")
Keys = {"Spn": [], "Sldr": [], "BtnMin": [], "BtnMax": []}
Cont = list()
MaxScore = 0
NormFactor = 100

#__________________________________________________
# main function

def main():

    """
    main function to control the events
    """

    global ConfigPath

    if 2 == len(sys.argv):
        ConfigPath = sys.argv[1]

    if os.path.isfile(ConfigPath):
        configure(ConfigPath)
    else:
        sys.stderr.write(F"ERROR: invalid file path > {ConfigPath}\n")
        sys.exit(1)

    while True:
        event, values = Window.read()

        # closing window or exit button
        if event == sg.WIN_CLOSED or event == "-BtnExit-":
            break

        # calculating score
        elif event == "-BtnCalc-":
            update_sum()

        # filling default values
        elif event == "-BtnClr-":
            clear_form()

        # copying contents to clipboard
        elif event == "-BtnCpy-":
            copy_to_clipboard()

        # spiner events
        elif event in Keys["Spn"]:
            i = Keys["Spn"].index(event)
            try:
                val = int(values[event])
            except ValueError:
                update_value(i, Cont[i]["default"])
            else:
                if val < Cont[i]["min"] or val > Cont[i]["max"]:
                    update_value(i, Cont[i]["default"])
                else:
                    update_value(i, val)
            update_sum()

        # slider events
        elif event in Keys["Sldr"]:
            i   = Keys["Sldr"].index(event)
            val = values[event]
            update_value(i, int(val))
            update_sum()

        # events with the button to fill minimum value
        elif event in Keys["BtnMin"]:
            i   = Keys["BtnMin"].index(event)
            val = Cont[i]["min"]
            update_value(i, val)
            update_sum()

        # events with the button to fill maximum value
        elif event in Keys["BtnMax"]:
            i   = Keys["BtnMax"].index(event)
            val = Cont[i]["max"]
            update_value(i, val)
            update_sum()

        # # spiner events with return key (doesn't work)
        # elif '\r' == event:
        #     print("return key detected")
        #     for i in range(len(Keys["Spn"])):
        #         try:
        #             val = int(values[event])
        #         except ValueError:
        #             update_value(i, Cont[i]["default"])
        #         else:
        #             if val < Cont[i]["min"] or val > Cont[i]["max"]:
        #                 update_value(i, Cont[i]["default"])
        #             else:
        #                 update_value(i, val)
        #     update_sum()


    Window.close()

    return

#__________________________________________________

def configure(path):
    """
    function to decoede config file and construct GUI
    """

    data = None

    with open(path) as f:
        data = json.load(f)

    global MaxScore
    global NormFactor
    index    = 0
    defScore = 0
    layout = [[sg.Text(F"config file: {path}", font=TextFont2)]]
    bodylayout = list()

    try:
        NormFactor = int(data["norm"]) if "norm" in data.keys() else 100
    except ValueError:
        dump_value_error("norm", data["norm"], ["root"])
        sys.exit(1)

    for item in data["items"]:

        if not "tag" in item.keys():
            sys.stderr.write("ERROR: No element with \"tag\" key was found in root branch.\n")
            sys.exit(1)

        tag = item["tag"]

        submax = 0
        sublayout = list()

        for subitem in item["items"]:

            if not "tag" in subitem.keys():
                sys.stderr.write(F"ERROR: No element with \"tag\" key was found.\n")
                sys.exit(1)

            elemtag = subitem["tag"]

            try:
                default = int(subitem["default"]) if "default" in subitem.keys() else 0
            except ValueError:
                dump_value_error("default", subitem["default"], [tag, elemtag])
                sys.exit(1)

            try:
                step   = subitem["step"] if "step" in subitem.keys() else 1
            except ValueError:
                dump_value_error("step", subitem["step"], [tag, elemtag])
                sys.exit(1)

            try:
                alloc = subitem["alloc"] if "alloc" in subitem.keys() else 1
            except ValueError:
                dump_value_error("alloc", subitem["alloc"], [tag, elemtag])
                sys.exit(1)

            valmax = max(0, alloc)
            valmin = min(0, alloc)
            vals   = [i for i in range(valmin, valmax + 1, step)] # range for spiner
            submax   += alloc
            defScore += default
            MaxScore += valmax

            sublayout.append([
                sg.Text(F"{elemtag} ({alloc})",
                        size=(20, 1), pad=((4,0), (19,0)), font=TextFont1),
                sg.Button("min", key=F"-BtnMin{index}-",
                          pad=((0,0), (19,0)), font=ButtonFont),
                sg.Slider(range=(valmin, valmax), default_value=default, resolution=step, orientation='h',
                          key=F"-Sldr{index}-", enable_events=True,
                          font=TextFont2),
                sg.Button("max", key=F"-BtnMax{index}-",
                          pad=((0,0), (19,0)), font=ButtonFont),
                sg.Spin(values=vals, initial_value=default,
                        key=F"-Spn{index}-", enable_events=True, bind_return_key=True,
                        size=(3, 1), pad=((4,4), (19,0)), font=TextFont1),
                ])

            Cont.append({"tag": F"{tag}/{elemtag}", "default": default, "value": default, "min": valmin, "max": valmax})

            for ikey in Keys.keys():
                Keys[ikey].append(F"-{ikey}{index}-")

            index += 1

        bodylayout.append([sg.Frame(F"{tag} ({submax})", sublayout, font=TextFont2)])

    normval = defScore / MaxScore * NormFactor
    ratio   = defScore / MaxScore * 100

    bodylayout.extend([
        [sg.Text("TOTAL SCORE", font=TextFont1), sg.Push(),
         sg.Text(F"{defScore} / {MaxScore}", key="-TxtSum-", font=TextFont3)],
        # size=(13, 1), pad=((265, 0), (0, 0)), font=TextFont3, justification='r')],
        [sg.Text("SCORING RATE", font=TextFont1), sg.Push(),
         sg.Text(F"{ratio:.2f} %", key="-TxtRatio-", font=TextFont3)],
        #size=(7, 1), pad=((310, 0), (0, 0)), font=TextFont3, justification='r')],
        [sg.Text("NORMALIZED SCORE", font=TextFont1), sg.Push(),
         sg.Text(F"{normval:.2f} / {NormFactor}", key="-TxtNorm-", font=TextFont3)]
        # size=(13, 1), pad=((215, 0), (0, 0)), font=TextFont3, justification='r')]
        ])

    layout.extend([
        [sg.Frame("", bodylayout)],
        [# sg.Button("calculate", key="-BtnCalc-", bind_return_key=True),
         sg.Button("COPY TO CLIPBOARD", key="-BtnCpy-", font=ButtonFont),
         sg.Button("CLEAR", key="-BtnClr-", font=ButtonFont),
         sg.Push(),
         sg.Button("EXIT", key="-BtnExit-", font=ButtonFont)]
        ])

    Window.layout(layout)

    return

#__________________________________________________

def clear_form():
    """
    function to fill default values
    """

    for i, elem in enumerate(Cont):
        update_value(i, elem["default"])
    update_sum()
    return

#__________________________________________________

def update_value(index, value):
    """
    function to fill updated values to elements
    index: index of element in the list "Key"
    value: new value
    """

    for key in Keys.keys():
        if "BtnMin" == key or "BtnMax" == key: continue
        Window[Keys[key][index]].update(value)
    Cont[index]["value"] = value
    return

#__________________________________________________

def sum_score():
    """
    function to calculate score and others
    """

    s = 0
    for elem in Cont:
        s += elem["value"]
    return s

#__________________________________________________

def update_sum():
    """
    function to fill updated values to the result box
    """

    s = sum_score()
    r = s / MaxScore * 100
    n = s / MaxScore * NormFactor
    Window["-TxtSum-"].update(F"{s} / {MaxScore}")
    Window["-TxtRatio-"].update(F"{r:.2f} %")
    Window["-TxtNorm-"].update(F"{n:.2f} / {NormFactor}")
    return

#__________________________________________________

def dump_value_error(key, value, tags):
    """
    function to dump a value error in the config file
    key: key in which the error arose
    value: value with the error
    tags: tag keys in which the error arose
    """

    path = '/'.join(tags)
    sys.stderr.write(F"ERROR: invalid value in {path} > \"{key}\": {value}\n")
    return

#__________________________________________________

def copy_to_clipboard():
    """
    function to paste the result to the system clipboard
    """

    s = sum_score()
    r = s / MaxScore * 100
    n = s / MaxScore * NormFactor

    buff = ""
    for item in Cont:
        buff += item["tag"] + " (" + str(item["min"]) + '--' + str(item["max"]) + "): " + str(item["value"]) + '\n'

    tag = "合計"
    buff += F"{tag}: {s} / {MaxScore}\n"

    tag = "得点率"
    buff += F"{tag}: {r:.2f}%\n"

    tag = "規格化得点"
    buff += F"{tag}: {n:.2f} / {NormFactor}\n"

    pyperclip.copy(buff)

    return

#__________________________________________________
# executing the main function

main()
