"""
    Code sourced from: https://github.com/JoseIuri/cocoTBCoverageView
    Usage: call python coverage_view.py coverage-filename.xml
    Graphically displays the coverage report from cocotb-coverage.
"""



import sys
import xml.etree.ElementTree as ET
import tkinter as tk
import tkinter.ttk as ttk
# from tkinter.filedialog import askopenfilename


def print_coverage(root, level, master):
    global counter
    if 'hits' not in root.attrib:
        value = float(root.get('cover_percentage'))
        name = root.tag

        # Create Coverage bar
        if value < 80:
            progress_bar = ttk.Progressbar(master,
                                           style="red.Horizontal.TProgressbar",
                                           orient="horizontal",
                                           length=100,
                                           mode='determinate',
                                           maximum=100,
                                           value=value)
        elif value < 100:
            progress_bar = ttk.Progressbar(
                master,
                style="yellow.Horizontal.TProgressbar",
                orient="horizontal",
                length=100,
                mode='determinate',
                maximum=100,
                value=value)
        else:
            progress_bar = ttk.Progressbar(
                master,
                style="green.Horizontal.TProgressbar",
                orient="horizontal",
                length=100,
                mode='determinate',
                maximum=100,
                value=value)

        height = 20

        # create Labels for information
        label_frame = tk.Frame(master, width=150, height=20)
        label_frame.pack_propagate(
            1)  # Stops child widgets of label_frame from resizing it
        tk.Label(label_frame,
                 fg="black",
                 text=name,
                 font=("Calibri", 10),
                 anchor="nw").pack()
        label_2 = tk.Label(master, text=str(value) + '%')

        # Place elements
        label_frame.place(x=level * 20, y=counter * 20, anchor='nw')
        progress_bar.place(x=level * 20 + 150, y=counter * 20, anchor='nw')
        label_2.place(x=level * 20 + 300, y=counter * 20, anchor='nw')

        # Resize window
        w, h = master.winfo_screenwidth(), master.winfo_screenheight()
        master.geometry("%dx%d+0+0" % (level * 20 + 400, counter * 20 + 20))

        counter += 1

    # Recursion
    for (idx, child) in enumerate(root):
        if 'hits' not in root.attrib:
            print_coverage(child, level + 1, master)
        else:
            pass


def open_file(master):
    global counter
    global filename
    counter = 0
    # filename = askopenfilename(initialdir="", title="Open file", filetypes=(
    #     ("XML files", "*.xml"), ("All files", "*.*")))

    tree = ET.parse(filename)

    counter = 0
    root = tree.getroot()

    print_coverage(root, 0, master)


def main():
    master = tk.Tk()
    master.title("Coverage Results")

    s = ttk.Style()
    s.theme_use('clam')
    s.configure("red.Horizontal.TProgressbar",
                foreground='red',
                background='red')

    w = ttk.Style()
    w.theme_use('clam')
    w.configure("green.Horizontal.TProgressbar",
                foreground='forest green',
                background='forest green')

    z = ttk.Style()
    z.theme_use('clam')
    z.configure("yellow.Horizontal.TProgressbar",
                foreground='goldenrod',
                background='goldenrod')
    open_file(master)

    tk.mainloop()


if __name__ == '__main__':
    filename = sys.argv[1]
    main()
