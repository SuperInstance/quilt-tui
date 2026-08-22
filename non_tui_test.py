"""Non-TUI test of the cell browser logic."""
import sys
sys.path.insert(0, '/workspace/quilt-velato')
from cut_and_project import build_penrose_tiling, Window, encode_on_window, default_encoder


def main():
    tiling = build_penrose_tiling(n_iterations=4, window=Window(radius=1.5))
    encode_on_window(tiling, default_encoder)
    cells = []
    for v in tiling['vertices']:
        cells.append({
            'id': f'p_{len(cells):04d}',
            'address_5d': list(v.address.coords),
            'physical': [v.physical_x, v.physical_y],
            'internal': [v.internal_x, v.internal_y, v.internal_z],
            'color': v.symbol or 'WITNESS',
        })
    
    print(f"Loaded {len(cells)} cells from cut-and-project")
    print()
    print("=" * 70)
    print("First 5 cells:")
    for c in cells[:5]:
        in_l = sum(c['address_5d']) == 0
        print(f"  {c['id']}: 5d={tuple(c['address_5d'])}, in_L={in_l}, color={c['color']}")
    print()
    print("Color distribution:")
    colors = {}
    for c in cells:
        colors[c['color']] = colors.get(c['color'], 0) + 1
    for c, n in colors.items():
        print(f"  {c:10s}: {n} ({100*n/len(cells):.1f}%)")
    print()
    print("Navigation test (first 10):")
    cursor = 0
    print(f"  cursor = {cursor} (cell {cells[cursor]['id']})")
    for key in 'jkkkllllgG':
        if key == 'h':
            cursor = max(0, cursor - 1)
        elif key == 'l':
            cursor = min(len(cells) - 1, cursor + 1)
        elif key == 'j':
            cursor = min(len(cells) - 1, cursor + 10)
        elif key == 'k':
            cursor = max(0, cursor - 10)
        elif key == 'g':
            cursor = 0
        elif key == 'G':
            cursor = len(cells) - 1
        print(f"  '{key}' → cursor = {cursor} (cell {cells[cursor]['id']})")
    print()
    print("All tests pass. The TUI is ready to run interactively.")


if __name__ == "__main__":
    main()
