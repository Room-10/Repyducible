
import os
import sys
import signal
import glob
import re
import importlib
import subprocess
import threading
import queue
import tkinter as tk
import tkinter.ttk as ttk

from repyducible.demo import modules_demo
from repyducible.util import get_params, args_from_logs

class ArgChooser(object):
    def __init__(self, master, argname=""):
        self.argname = argname
        self.active = tk.IntVar()
        self.active_cb = tk.Checkbutton(master, variable=self.active)
        self.active.set(True)
        self.label = tk.Label(master, text=self.argname)
        self.content = ttk.Frame(master)
        self.val = tk.StringVar()
        self.val.trace("w", self._change_cb)

    def _change_cb(self, *args):
        if self.val.get() != "":
            self.active.set(True)
        else:
            self.active.set(False)

    def set(self, val):
        self.val.set(val)
        self.active.set(True)

    def reset(self):
        self.val.set("")
        self.active.set(False)

    def grid(self, row):
        if self.argname[0] == "-":
            self.active_cb.grid(row=row, column=0)
            self.active.set(False)
        self.label.grid(row=row, column=1, sticky=tk.E, pady=2)
        self.content.grid(row=row, column=2, sticky=(tk.N, tk.E, tk.S, tk.W),
                          padx=3, pady=1)

    def get_arg(self):
        result = []
        if self.argname[0] == "-":
            if not self.active.get():
                return result
            result.append(self.argname)
        result += self._state()
        return result

    def _state(self):
        return [self.val.get()]

class OptionArgChooser(ArgChooser):
    def __init__(self, *args, options=[], **kwargs):
        ArgChooser.__init__(self, *args, **kwargs)
        self.options = options
        w = tk.OptionMenu(self.content, self.val, *self.options)
        w.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.content.grid_columnconfigure(0, weight=1)
        self.reset()

    def reset(self):
        self.val.set(self.options[0])
        self.active.set(False)

class StringArgChooser(ArgChooser):
    def __init__(self, *args, options=[], **kwargs):
        ArgChooser.__init__(self, *args, **kwargs)
        if len(options) == 0:
            w = ttk.Entry(self.content, textvariable=self.val)
        else:
            w = ttk.Combobox(self.content, textvariable=self.val,
                                           values=options,
                                           height=min(20,len(options)))
        w.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.content.grid_columnconfigure(0, weight=1)

class DictArgChooser(ArgChooser):
    def __init__(self, *args, keys=[], **kwargs):
        ArgChooser.__init__(self, *args, **kwargs)
        self.content.config(borderwidth=3, relief=tk.GROOVE)
        self.vals = []
        for i,k in enumerate(keys):
            active = tk.IntVar()
            cb = tk.Checkbutton(self.content, variable=active,
                                command=self._change_cb)
            cb.grid(row=i, column=0)
            l = tk.Label(self.content, text="%s=" % k)
            l.grid(row=i, column=1, sticky=tk.E)
            val = tk.StringVar()
            val.trace("w", lambda *args, i=i: self._sub_change_cb(i))
            e = tk.Entry(self.content, textvariable=val)
            e.grid(row=i, column=2, sticky=(tk.W, tk.E))
            self.vals.append({ 'active': active, 'val': val, 'key': k })
        self.content.grid_columnconfigure(2, weight=1)

    def set(self, val):
        if val == "":
            self.reset()
            return
        val += ","
        regex = r"^(([a-z0-9]+)=([^=]+),)+$"
        setvals = {}
        while val != "":
            m = re.match(regex, val)
            setvals[m.group(2)] = m.group(3)
            val = val[:-len(m.group(1))]
        for v in self.vals:
            if v['key'] in setvals:
                v['val'].set(setvals[v['key']])
        self.active.set(True)

    def reset(self):
        for v in self.vals:
            v['val'].set("")
            v['active'].set(False)
        self.active.set(False)

    def _sub_change_cb(self, *args):
        for v in self.vals:
            if v['val'].get() == "":
                v['active'].set(False)

        if len(args) > 0:
            val = self.vals[args[0]]
            if val['val'].get() != "":
                val['active'].set(True)
                self.active.set(True)

        if len(list(filter(lambda v: v['active'].get(), self.vals))) == 0:
            self.active.set(False)

    def _state(self):
        vals = []
        for v in self.vals:
            if v['active'].get():
                vals.append("%s=%s" % (v['key'], v['val'].get()))
        result = ",".join(vals).replace('"', "'")
        return ['%s' % result]

def args_gui(Experiment, data_modules, model_modules):
    def destroy_cb(*args):
        root.quit()
        root.destroy()
        sys.exit()

    def dataset_change_cb(*args):
        rowi = 5
        dval = choosers[0].val.get()
        DataClass = importlib.import_module(data_modules[dval]).Data
        params = get_params(DataClass)
        choosers[rowi].content.grid_forget()
        choosers[rowi] = DictArgChooser(fr, argname="--data-params", keys=params)
        choosers[rowi].grid(2*rowi)

    def model_change_cb(*args):
        rowi = 6
        mval = choosers[1].val.get()
        ModelClass = importlib.import_module(model_modules[mval]).Model
        params = get_params(ModelClass)
        params.remove("data")
        choosers[rowi].content.grid_forget()
        choosers[rowi] = DictArgChooser(fr, argname="--model-params", keys=params)
        choosers[rowi].grid(2*rowi)

    def output_change_cb(*args):
        for c in choosers[3:]:
            c.reset()
        output_dir = choosers[2].val.get()
        dataset, model, params = args_from_logs(output_dir)
        if dataset is not None:
            choosers[0].set(dataset)
        if model is not None:
            choosers[1].set(model)
        root.after_idle(lambda a=params: set_params(a))

    def set_params(args):
        arglist = [
            (3, "--resume"),
            (4, "--plot"),
            (5, "--data-params"),
            (6, "--model-params"),
            (7, "--solver"),
            (8, "--solver-params"),
            (9, "--snapshots"),
        ]
        for i,n in arglist:
            if n in args:
                idx = args.index(n)
                if idx+1 < len(args) and args[idx+1][0] != "-":
                    choosers[i].set(args[idx+1])
                else:
                    choosers[i].set(True)
        b_prev_cb()

    def parse_commandline():
        return sum([c.get_arg() for c in choosers], [])

    def b_prev_cb():
        preview.delete("1.0", tk.END)
        preview.insert(tk.END, " ".join(parse_commandline()))

    def b_go_cb():
        cmd = ["python", "demo.py"] + parse_commandline()
        root.after_idle(lambda root=root, cmd=cmd: popen_with_stdout(root, cmd))

    def b_reset_cb():
        for c in choosers:
            c.reset()

    root = tk.Tk()
    root.wm_title("Setup arguments")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.protocol("WM_DELETE_WINDOW", destroy_cb)
    root.bind('<Control-q>', destroy_cb)

    fr = ttk.Frame(root, padding=(5, 5, 12, 12))
    fr.grid(column=0, row=0, sticky=(tk.N, tk.E, tk.S, tk.W))

    output_dirs = sorted(glob.glob("./results/*"))
    datasets = sorted(list(data_modules.keys()))
    models = sorted(list(model_modules.keys()))
    choosers = [
        OptionArgChooser(fr, argname="DATASET", options=datasets),
        OptionArgChooser(fr, argname="MODEL", options=models),
        StringArgChooser(fr, argname="--output", options=output_dirs),
        ArgChooser(fr, argname="--resume"),
        OptionArgChooser(fr, argname="--plot", options=['show','hide','no']),
        DictArgChooser(fr, argname="--data-params", keys=[]),
        DictArgChooser(fr, argname="--model-params", keys=[]),
        OptionArgChooser(fr, argname="--solver", options=['pdhg','cvx']),
        StringArgChooser(fr, argname="--solver-params"),
        ArgChooser(fr, argname="--snapshots"),
    ]

    choosers[0].val.trace("w", dataset_change_cb)
    choosers[1].val.trace("w", model_change_cb)
    choosers[2].val.trace("w", output_change_cb)

    for i,c in enumerate(choosers):
        c.grid(2*i)
        s = ttk.Separator(fr, orient=tk.HORIZONTAL)
        s.grid(row=2*i+1, columnspan=3, sticky=(tk.E, tk.W), pady=8)
    preview = tk.Text(fr, height=4)
    preview.grid(row=2*len(choosers), column=2, sticky=(tk.E, tk.W))
    bfr = ttk.Frame(fr)
    bfr.grid(row=2*len(choosers), column=0, columnspan=2, sticky=(tk.N, tk.E, tk.S, tk.W))
    b_prev = tk.Button(bfr, text="Preview")
    b_prev.grid(row=0, column=0, sticky=(tk.E, tk.W), columnspan=2)
    b_prev.config(command=b_prev_cb)
    b_reset = tk.Button(bfr, text="Reset")
    b_reset.grid(row=1, column=0, sticky=(tk.E, tk.W))
    b_reset.config(command=b_reset_cb)
    b_go = tk.Button(bfr, text="Go!")
    b_go.grid(row=1, column=1, sticky=(tk.E, tk.W))
    b_go.config(command=b_go_cb)

    fr.grid_columnconfigure(2, weight=1)
    dataset_change_cb()
    model_change_cb()
    tk.mainloop()

class popen_with_stdout(object):
    def __init__(self, master, cmd):
        self.cmd = cmd
        self.window = tk.Toplevel(master)
        self.window.wm_title("Console output")
        self.window.bind('<Control-c>', self.interrupt)

        self.textfield = tk.Text(self.window,
                                 font=("monospace", 10),
                                 background='black',
                                 foreground='white',
                                 width=120,
                                 height=40)
        self.textfield.grid(row=0, column=0, sticky="nsew")
        scrollb = tk.Scrollbar(self.window, command=self.textfield.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.textfield['yscrollcommand'] = scrollb.set
        self.textfield.insert(tk.END, "$ " + " ".join(cmd) + "\n")
        self.textfield.insert(tk.END, "BEGIN OUTPUT (stdout and stderr)\n")
        self.textfield.see(tk.END)

        self.queue = queue.Queue()
        self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        bufsize=1)
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        self.periodiccall()

    def periodiccall(self):
        self.checkqueue()
        if self.thread.is_alive():
            self.window.after(100, self.periodiccall)
        else:
            self.textfield.insert(tk.END, "PROCESS TERMINATED")
            self.textfield.see(tk.END)
            self.textfield.update()

    def checkqueue(self):
        while self.queue.qsize():
            try:
                output = self.queue.get(0)
                self.textfield.insert(tk.END, output)
                self.textfield.see(tk.END)
                self.textfield.update()
            except queue.Queue.Empty:
                pass

    def run(self):
        for output in iter(self.process.stdout.readline, b''):
            self.queue.put(output)
        self.process.stdout.flush()
        self.process.stdout.close()
        self.process.wait()

    def interrupt(self, *args):
        self.process.send_signal(signal.SIGINT)
