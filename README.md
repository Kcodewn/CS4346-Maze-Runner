<h1>CS4346 Maze Runner</h1>

Real-time maze visualizer with fog-of-war, line-of-sight, and an autopilot planner. Built with Pygame and your CS4346 grid/astar code.

<h1>Features</h1>

Random maze/world generation (or load from file)

Live agent animation (manual control or A* autopilot with re-planning)

Dynamic fog-of-war with true line-of-sight (Bresenham)

Fullscreen toggle (F11 or Option ⌥ + Enter on macOS)

Adjustable vision radius and optional grid overlay

<h1>Controls (during runtime)</h1>

Space:	Toggle autopilot (A* re-plans as it discovers blocks)

Arrow keys / WASD:	Manual movement

'[': Load previous maze in env folder
  
']': Load next maze in env folder

T: Switches Tie-breaking strategy between smaller_g and larger_g

G:	Generate a fresh random world (same size --n)

R:	Reset to start

'+' or '-': Increase or decrease vision radius
  
H:	Toggle grid overlay

F11 or Option ⌥ + Enter:	Toggle fullscreen

Esc:	Quit

<h1>Command-line Options</h1>

--n INT           Grid size when generating random maps (default: 31)

--p FLOAT         Block probability for random maps (default: 0.30)

--load PATH       Load a saved world (.txt) instead of generating random

--cell INT        Cell size in pixels (default: 28)

--fps INT         Frames per second (default: 60)

--vision INT      Vision radius in tiles (default: 6)

--fullscreen      Start in fullscreen (you can still toggle in-app)

<h1>Examples:</h1>

Bigger grid:

python run_viewer.py --n 51 --cell 24 --fullscreen

Load a specific world file:

python run_viewer.py --load path/to/world.txt --vision 8

MIT © 2025 Khanh Nguyen
