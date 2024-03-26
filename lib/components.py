import tkinter as tk
import ttkwidgets as ttkw
from typing import Any

from config import Config
from data import Profile, ProgramData
from lib.mathlib import get_tristate_from_selected 

class ScrollableFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, cnf: dict[str,Any] = {}, **kwargs):
        tk.Frame.__init__(self, parent, cnf, **kwargs)
        self.canvas = tk.Canvas(self, background="#ffffff")
        self.frame = tk.Frame(self.canvas, background="#ffffff")
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame, anchor="n", tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    def onFrameConfigure(self, _evt):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def onMouseWheel(self, evt):
        '''Handle mouse wheel events'''
        print(f"Mouse wheel handling from scrollable frame, {evt.delta}")
        self.canvas.yview_scroll(-evt.delta // 120, "units")

class ProgramSetSelector(tk.Frame):
    def __init__(self, parent: tk.Misc, config: Config, data: Profile, cnf: dict[str,Any] = {}, selected_programs: list[ProgramData] = [], **kwargs):
        tk.Frame.__init__(self, parent, cnf, **kwargs)
        
        self.config = config
        self.data = data
        self.programs = data.programs
        self.selectedvars: dict[str, tk.BooleanVar] = {}

        # Precalculate the number of programs per category
        selected_program_ids = {p.id for p in selected_programs}
        selected_per_category = {c: 0 for c in config.categories}
        total_per_category = {c: 0 for c in config.categories}
        for p in selected_programs:
            selected_per_category[p.category] += 1
        for p in data.programs.values():
            if not p.is_visible(): continue
            total_per_category[p.category] += 1

        self.tree = ttkw.CheckboxTreeview(self)
        self.tree.pack(fill="both", expand=True)
        self.tree.insert("", "end", "all", text="All", tags=(get_tristate_from_selected(len(selected_program_ids),sum(total_per_category.values())),))
        for cat in config.categories:
            self.tree.insert("all", "end", cat.lower(), text=cat, tags=(get_tristate_from_selected(selected_per_category[cat],total_per_category[cat]),))

        for p in sorted(data.programs.values(), key=lambda p: p.sortkey()):
            if not p.is_visible(): continue
            self.tree.insert(p.category.lower(), "end", p.id, text=p.display_name, tags=("checked" if p.id in selected_program_ids else "unckecked",))
        self.tree.selection_add([p.id for p in selected_programs])
        self.tree.expand_all()
    
    def get_checked(self) -> list[ProgramData]:
        '''Get the list of checked programs'''
        return [self.data.programs[item] for item in self.tree.get_checked() if item in self.data.programs]