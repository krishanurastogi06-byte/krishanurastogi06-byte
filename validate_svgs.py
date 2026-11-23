import xml.etree.ElementTree as ET
from pathlib import Path

cards = sorted(Path('cards').glob('*.svg'))
print(f"Validating {len(cards)} SVG cards...")

all_valid = True
for svg_file in cards:
    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
        viewbox = root.attrib.get('viewBox', 'missing')
        width = root.attrib.get('width', 'missing')
        height = root.attrib.get('height', 'missing')
        print(f"  ✓ {svg_file.name:<15} : Valid XML | viewBox={viewbox} | w={width} h={height} | size={svg_file.stat().st_size:,}B")
    except Exception as exc:
        print(f"  ✗ {svg_file.name:<15} : FAILED -> {exc}")
        all_valid = False

if all_valid:
    print("\nAll SVG cards passed strict XML syntax validation!")
else:
    print("\nSome SVG cards failed validation.")
