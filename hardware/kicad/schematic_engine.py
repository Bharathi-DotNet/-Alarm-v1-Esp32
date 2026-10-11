import os
import uuid
import re
import subprocess
from test_gen_init import lib_symbols_s, raw_pins

def u(): return str(uuid.uuid4())

class SchematicGenerator:
    def __init__(self, title="ESP32 Anti-Cheat Smart Alarm Clock", rev="v1.0"):
        self.sheet_uuid = u()
        self.title = title
        self.rev = rev
        self.symbols = []
        self.wires = []
        self.labels = []
        self.no_connects = []
        self.texts = []

    def add_sym(self, lib_id, ref, val, footprint, x, y, rot=0):
        sym_uuid = u()
        pins_dict = raw_pins[lib_id]
        pin_uuids = {pnum: u() for pnum in pins_dict.keys()}
        pin_world = {}
        for pnum, (px, py, pang, ptype, pname) in pins_dict.items():
            if rot == 0:
                dx, dy = px, -py
            elif rot == 90:
                dx, dy = -py, -px
            elif rot == 180:
                dx, dy = -px, py
            elif rot == 270:
                dx, dy = py, px
            else:
                raise ValueError(f"Invalid rotation {rot}")
            pin_world[pnum] = (round(x + dx, 2), round(y + dy, 2))

        sym_obj = {
            "lib_id": lib_id,
            "ref": ref,
            "val": val,
            "footprint": footprint,
            "x": x,
            "y": y,
            "rot": rot,
            "uuid": sym_uuid,
            "pin_uuids": pin_uuids,
            "pin_world": pin_world,
            "is_pwr": False
        }
        self.symbols.append(sym_obj)
        return sym_obj

    def add_pwr(self, lib_id, val, x, y, rot=0):
        sym_uuid = u()
        pins_dict = raw_pins[lib_id]
        pin_uuids = {pnum: u() for pnum in pins_dict.keys()}
        pin_world = {}
        for pnum, (px, py, pang, ptype, pname) in pins_dict.items():
            pin_world[pnum] = (round(x, 2), round(y, 2))
        sym_obj = {
            "lib_id": lib_id,
            "ref": "#PWR?",
            "val": val,
            "footprint": "",
            "x": x,
            "y": y,
            "rot": rot,
            "uuid": sym_uuid,
            "pin_uuids": pin_uuids,
            "pin_world": pin_world,
            "is_pwr": True
        }
        self.symbols.append(sym_obj)
        return sym_obj

    def add_label(self, name, x, y, rot=0):
        self.labels.append({
            "name": name,
            "x": round(x, 2),
            "y": round(y, 2),
            "rot": rot,
            "uuid": u()
        })

    def add_wire(self, x1, y1, x2, y2):
        self.wires.append({
            "x1": round(x1, 2),
            "y1": round(y1, 2),
            "x2": round(x2, 2),
            "y2": round(y2, 2),
            "uuid": u()
        })

    def add_nc(self, x, y):
        self.no_connects.append({
            "x": round(x, 2),
            "y": round(y, 2),
            "uuid": u()
        })

    def add_text(self, text, x, y, size=2.54):
        self.texts.append({
            "text": text,
            "x": round(x, 2),
            "y": round(y, 2),
            "size": size,
            "uuid": u()
        })

    def connect_pin(self, sym, pin_num, net_name):
        # Place label or power symbol right on the pin
        px, py = sym["pin_world"][pin_num]
        if net_name == "GND":
            self.add_pwr("power:GND", "GND", px, py)
        elif net_name == "+3V3":
            self.add_pwr("power:+3V3", "+3V3", px, py)
        else:
            self.add_label(net_name, px, py)

    def nc_pin(self, sym, pin_num):
        px, py = sym["pin_world"][pin_num]
        self.add_nc(px, py)

    def wire_pins(self, sym1, p1, sym2, p2):
        x1, y1 = sym1["pin_world"][p1]
        x2, y2 = sym2["pin_world"][p2]
        if x1 == x2 or y1 == y2:
            self.add_wire(x1, y1, x2, y2)
        else:
            # 2 segment L-wire
            self.add_wire(x1, y1, x2, y1)
            self.add_wire(x2, y1, x2, y2)

    def export(self):
        lines = [
            "(kicad_sch",
            "\t(version 20231120)",
            '\t(generator "kicad-cli")',
            '\t(generator_version "10.0")',
            f'\t(uuid "{self.sheet_uuid}")',
            '\t(paper "A3")',
            "\t(title_block",
            f'\t\t(title "{self.title}")',
            '\t\t(date "2026-09-22")',
            f'\t\t(rev "{self.rev}")',
            '\t\t(company "Production Hardware Design")',
            "\t)",
            lib_symbols_s
        ]

        for t in self.texts:
            lines.append(f'\t(text "{t["text"]}" (at {t["x"]:.2f} {t["y"]:.2f} 0) (effects (font (size {t["size"]:.2f} {t["size"]:.2f}) (bold yes))) (uuid "{t["uuid"]}"))')

        for s in self.symbols:
            is_pwr = s.get("is_pwr", False)
            hide_fp = ' (hide yes)' if s['footprint'] == "" or not is_pwr else ''
            ref_hide = ' (hide yes)' if is_pwr else ''
            lines.append('\t(symbol')
            lines.append(f'\t\t(lib_id "{s["lib_id"]}")')
            lines.append(f'\t\t(at {s["x"]:.2f} {s["y"]:.2f} {s["rot"]})')
            lines.append('\t\t(unit 1)')
            lines.append('\t\t(exclude_from_sim no)')
            lines.append('\t\t(in_bom no)' if is_pwr else '\t\t(in_bom yes)')
            lines.append('\t\t(on_board yes)')
            lines.append('\t\t(dnp no)')
            lines.append(f'\t\t(uuid "{s["uuid"]}")')
            lines.append(f'\t\t(property "Reference" "{s["ref"]}" (at {s["x"]:.2f} {s["y"] - 2.54:.2f} 0) (effects (font (size 1.27 1.27)){ref_hide}))')
            lines.append(f'\t\t(property "Value" "{s["val"]}" (at {s["x"]:.2f} {s["y"] + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
            lines.append(f'\t\t(property "Footprint" "{s["footprint"]}" (at {s["x"]:.2f} {s["y"]:.2f} 0) (effects (font (size 1.27 1.27)){hide_fp}))')
            for pnum, pid in s["pin_uuids"].items():
                lines.append(f'\t\t(pin "{pnum}" (uuid "{pid}"))')
            lines.append('\t\t(instances')
            lines.append('\t\t\t(project "alarm_clock_v1"')
            lines.append(f'\t\t\t\t(path "/{self.sheet_uuid}/{s["uuid"]}"')
            lines.append(f'\t\t\t\t\t(reference "{s["ref"]}")')
            lines.append('\t\t\t\t\t(unit 1)')
            lines.append('\t\t\t\t)')
            lines.append('\t\t\t)')
            lines.append('\t\t)')
            lines.append('\t)')

        for w in self.wires:
            lines.append(f'\t(wire (pts (xy {w["x1"]:.2f} {w["y1"]:.2f}) (xy {w["x2"]:.2f} {w["y2"]:.2f})) (stroke (width 0) (type default)) (uuid "{w["uuid"]}"))')

        for lb in self.labels:
            lines.append(f'\t(label "{lb["name"]}" (at {lb["x"]:.2f} {lb["y"]:.2f} {lb["rot"]}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{lb["uuid"]}"))')

        for nc in self.no_connects:
            lines.append(f'\t(no_connect (at {nc["x"]:.2f} {nc["y"]:.2f}) (uuid "{nc["uuid"]}"))')

        lines.append(")")
        return "\n".join(lines)

print("SchematicGenerator class ready")
