import re
import os

netlist_path = r"c:\Users\Bharathi\Documents\PlatformIO\Projects\Alarm V1\hardware\kicad\alarm_clock_v1.net"
with open(netlist_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Parse components
comps_raw = re.findall(r'\(comp\s+\(ref\s+"([^"]+)".*?\(value\s+"([^"]+)".*?\(footprint\s+"([^"]+)"', text, re.DOTALL)
components = {}
for ref, val, fp in comps_raw:
    components[ref] = {"val": val, "footprint": fp}

print(f"Total components parsed: {len(components)}")
for ref, d in sorted(components.items()):
    print(f"  {ref:>6}: {d['val']:<20} -> {d['footprint']}")

# 2. Parse nets
nets_section_idx = text.find('(nets')
nets_text = text[nets_section_idx:]
net_blocks = re.findall(r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\n\t\t\(net|\n\t\)\n\))', nets_text, re.DOTALL)

nets = {}
for code, name, body in net_blocks:
    nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body)
    nets[name] = nodes

print(f"\nTotal nets parsed: {len(nets)}")
for name, nodes in sorted(nets.items()):
    print(f"  {name:<18} ({len(nodes)} nodes): {nodes[:4]}")
