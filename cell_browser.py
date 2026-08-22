#!/usr/bin/env python3
"""
quilt-tui — Terminal UI for browsing the cell graph.

Like vim for cells. Use keyboard navigation to move through the cell graph,
inspect 5D addresses, see 3-coloring, and explore the topology.

The cells are loaded from a .qzt file. Without one, the TUI generates a
sample cell graph from the corrected cut-and-project construction.

Controls:
  h/j/k/l : move cursor left/down/up/right
  H/J/K/L : jump to neighbor in L
  i       : inspect current cell (show 5D address, internal coord, color)
  n       : next generation
  p       : previous generation
  g/G     : first/last cell
  /       : search by color (CREATION/ENTROPY/WITNESS)
  q       : quit
"""

import sys
import os
import math
import curses
from typing import List, Dict, Any, Tuple

# Reuse the cut-and-project module
sys.path.insert(0, '/workspace/quilt-velato')
from cut_and_project import (
    build_penrose_tiling, FiveDAddress, Window, encode_on_window, default_encoder
)


def load_sample_cells(n_iterations: int = 4, window_radius: float = 1.5) -> List[Dict]:
    """Load a sample set of cells from the cut-and-project construction."""
    tiling = build_penrose_tiling(n_iterations=n_iterations, window=Window(radius=window_radius))
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
    return cells


def render(stdscr, cells: List[Dict], cursor: int, message: str = ""):
    """Render the cell browser."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # Header
    title = "𝕋 — Quilt TUI: Cell Browser"
    stdscr.addstr(0, 0, title[:w-1], curses.A_BOLD | curses.color_pair(1))
    stdscr.addstr(1, 0, "─" * min(w-1, 60))
    
    if not cells:
        stdscr.addstr(3, 0, "No cells loaded.")
        stdscr.addstr(h-2, 0, "Press 'q' to quit.")
        stdscr.refresh()
        return
    
    # Left panel: cell list
    list_w = min(40, w // 3)
    stdscr.addstr(3, 0, "CELLS", curses.A_BOLD)
    visible_cells = min(h - 6, len(cells))
    start = max(0, cursor - visible_cells // 2)
    for i in range(start, min(start + visible_cells, len(cells))):
        cell = cells[i]
        marker = "→ " if i == cursor else "  "
        line = f"{marker}{cell['id']:10s} {cell['color']:10s}"
        attr = curses.A_REVERSE if i == cursor else 0
        if cell['color'] == 'CREATION':
            attr |= curses.color_pair(2)
        elif cell['color'] == 'ENTROPY':
            attr |= curses.color_pair(3)
        elif cell['color'] == 'WITNESS':
            attr |= curses.color_pair(4)
        stdscr.addstr(4 + (i - start), 0, line[:list_w-1], attr)
    
    # Right panel: cell details
    if cursor < len(cells):
        cell = cells[cursor]
        x = list_w + 2
        y = 3
        stdscr.addstr(y, x, "CELL DETAILS", curses.A_BOLD)
        y += 1
        stdscr.addstr(y, x, f"id:        {cell['id']}")
        y += 1
        stdscr.addstr(y, x, f"5D addr:   ({', '.join(str(c) for c in cell['address_5d'])})")
        y += 1
        # Verify in L
        in_l = sum(cell['address_5d']) == 0
        stdscr.addstr(y, x, f"in L:      {'YES' if in_l else 'NO (gauge redundancy!)'}")
        y += 1
        stdscr.addstr(y, x, f"physical:  ({cell['physical'][0]:.3f}, {cell['physical'][1]:.3f})")
        y += 1
        stdscr.addstr(y, x, f"internal:  ({cell['internal'][0]:.3f}, {cell['internal'][1]:.3f}, {cell['internal'][2]:.3f})")
        y += 1
        stdscr.addstr(y, x, f"color:     {cell['color']}")
        y += 1
        stdscr.addstr(y, x, f"# of cells: {len(cells)}")
        y += 1
        stdscr.addstr(y, x, f"position:  {cursor + 1}/{len(cells)}")
        y += 2
        stdscr.addstr(y, x, "─" * 20)
        y += 1
        stdscr.addstr(y, x, "8 Quilt Primitives:", curses.A_BOLD)
        y += 1
        primitives = ['Z_in', 'Z_out', 'JEPA', 'DoubleEntry', 'Vibe', 'GC', 'Murmur', 'Graph']
        for p in primitives:
            stdscr.addstr(y, x, f"  • {p}")
            y += 1
    
    # Footer
    footer = "h/j/k/l move | H/J/K/L jump | i inspect | n/p next/prev | g/G first/last | / search | q quit"
    stdscr.addstr(h-2, 0, footer[:w-1])
    
    # Message
    if message:
        stdscr.addstr(h-1, 0, message[:w-1], curses.A_BOLD | curses.color_pair(1))
    
    stdscr.refresh()


def main(stdscr):
    # Init colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.curs_set(0)
    
    # Load sample cells
    cells = load_sample_cells(n_iterations=4, window_radius=1.5)
    cursor = 0
    message = f"Loaded {len(cells)} cells from cut-and-project"
    
    while True:
        render(stdscr, cells, cursor, message)
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break
        
        if key == ord('q'):
            break
        elif key == ord('h') or key == curses.KEY_LEFT:
            cursor = max(0, cursor - 1)
            message = ""
        elif key == ord('l') or key == curses.KEY_RIGHT:
            cursor = min(len(cells) - 1, cursor + 1)
            message = ""
        elif key == ord('j') or key == curses.KEY_DOWN:
            cursor = min(len(cells) - 1, cursor + 10)
            message = ""
        elif key == ord('k') or key == curses.KEY_UP:
            cursor = max(0, cursor - 10)
            message = ""
        elif key == ord('g'):
            cursor = 0
            message = ""
        elif key == ord('G'):
            cursor = len(cells) - 1
            message = ""
        elif key == ord('n'):
            cursor = min(len(cells) - 1, cursor + 50)
            message = f"Jumped forward 50 cells to {cursor + 1}"
        elif key == ord('p'):
            cursor = max(0, cursor - 50)
            message = f"Jumped back 50 cells to {cursor + 1}"
        elif key == ord('i'):
            if cursor < len(cells):
                cell = cells[cursor]
                in_l = sum(cell['address_5d']) == 0
                message = f"id={cell['id']} | in_L={in_l} | color={cell['color']}"
        elif key == ord('H'):
            # Find a neighbor in L: subtract 1 from coords[1:], add 1 to coords[0]
            if cursor < len(cells):
                cell = cells[cursor]
                new_coords = list(cell['address_5d'])
                new_coords[1] += 1
                new_coords[0] -= 1
                # Find a cell with matching coords
                for i, c in enumerate(cells):
                    if c['address_5d'] == new_coords:
                        cursor = i
                        message = f"Jumped to neighbor in L"
                        break
        elif key == ord('L'):
            if cursor < len(cells):
                cell = cells[cursor]
                new_coords = list(cell['address_5d'])
                new_coords[1] -= 1
                new_coords[0] += 1
                for i, c in enumerate(cells):
                    if c['address_5d'] == new_coords:
                        cursor = i
                        message = f"Jumped to neighbor in L"
                        break
        elif key == ord('/'):
            # Search by color
            stdscr.addstr(curses.LINES - 1, 0, "Search color (c/e/w): ")
            stdscr.refresh()
            ch = stdscr.getch()
            target = None
            if ch == ord('c'):
                target = 'CREATION'
            elif ch == ord('e'):
                target = 'ENTROPY'
            elif ch == ord('w'):
                target = 'WITNESS'
            if target:
                for i, c in enumerate(cells):
                    if c['color'] == target:
                        cursor = i
                        message = f"Found first {target} cell at {i + 1}"
                        break


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("Quilt TUI: bye")
        sys.exit(0)
