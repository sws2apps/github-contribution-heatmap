from bs4 import BeautifulSoup

input_path = '/tmp/ahuseyn-index.html'
output_path = '/Users/Vlad/Dev/Organized-Dev/GH-Heatmap-Widget/api/static/ahuseyn-world-map.svg'

with open(input_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

svgs = soup.find_all('svg')

print(f"Found {len(svgs)} SVGs")

best_svg = None
max_paths = 0

for i, svg in enumerate(svgs):
    paths = svg.find_all('path')
    print(f"SVG {i}: {len(paths)} paths, attrs: {svg.attrs}")
    if len(paths) > max_paths:
        max_paths = len(paths)
        best_svg = svg

if best_svg:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(best_svg))
    print(f"Successfully extracted SVG with {max_paths} paths to {output_path}")
else:
    print("No suitable SVG found.")
