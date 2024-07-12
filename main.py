# IMPORTS
import tkinter as tk
from tkinter import ttk
import numpy as np
import spyrograph as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import threading
import math
import datetime

# VARIABLES
# Create root window
root = tk.Tk()
root.title("GuilloCNC")
root.geometry('800x600')

# Create configuration variables
R = tk.IntVar()
r = tk.IntVar()
d = tk.DoubleVar()
max_radius = tk.IntVar()
res = tk.IntVar()
selected_shape = None

text_obj = None
rotations = 0


locking = threading.Lock()

# FUNCTIONS
def get_epitrochoid(R, r, d, max_radius, res):
    global rotations
    thetamax = 0 
    
    epitrochoid = sp.Epitrochoid(R = R, r = r, d = d, thetas = np.arange(0, (1024 * np.pi) + (np.pi / res), np.pi / res).tolist())
    coords = [[round(x, 10), round(y, 10), round(z, 10)] for x, y, z in epitrochoid.coords]
    
    for i in range(1, len(coords)):
        if coords[i][0] == coords[0][0] and coords[i][1] == coords[0][1]:
            thetamax = math.ceil(((coords[i][2] - (np.pi / res)) / np.pi))
            rotations = thetamax
            break
    
    scale = max_radius / epitrochoid.max_x
    
    return sp.Epitrochoid(R = R, r = r, d = d, thetas = np.arange(0, (thetamax * np.pi) + (np.pi / res), np.pi / res).tolist()).scale(scale)

def get_hypotrochoid(R, r, d, max_radius, res):
    global rotations
    thetamax = 0
    
    hypotrochoid = sp.Hypotrochoid(R = R, r = r, d = d, thetas = np.arange(0, (1024 * np.pi) + (np.pi / res), np.pi / res).tolist())
    coords = [[round(x, 10), round(y, 10), round(z, 10)] for x, y, z in hypotrochoid.coords]
    
    for i in range(1, len(coords)):
        if coords[i][0] == coords[0][0] and coords[i][1] == coords[0][1]:
            thetamax = math.ceil(((coords[i][2] - (np.pi / res)) / np.pi))
            rotations = thetamax
            break
    
    scale = max_radius / hypotrochoid.max_x
    
    return sp.Hypotrochoid(R = R, r = r, d = d, thetas = np.arange(0, (thetamax * np.pi) + (np.pi / res), np.pi / res).tolist()).scale(scale)

def get_shape(selected_shape, R, r, d, max_radius, res):
    if selected_shape == 'Epitrochoid':
        return get_epitrochoid(R, r, d, max_radius, res)
    elif selected_shape == 'Hypotrochoid':
        return get_hypotrochoid(R, r, d, max_radius, res)

def update_plot():
    global text_obj
    global selected_shape
    
    R, r, d, max_radius, res = (slider.get() for slider in [R_slider, r_slider, d_slider, max_radius_slider, res_slider])
    
    if selected_shape.get() == 'Epitrochoid':
        shape = get_epitrochoid(R, r, d, max_radius, res)
    elif selected_shape.get() == 'Hypotrochoid':
        shape = get_hypotrochoid(R, r, d, max_radius, res)
    
    ax.clear()
    
    if text_obj is not None:
        text_obj.remove()
    
    text_obj = fig.text(0.95, 0.95, f'{selected_shape.get()}\nR: {R} | r: {r} | d: {d}\nMax Radius: {max_radius}\nResolution: {res}\nClosed: {shape.is_closed()}\n{len(shape.coords)} points, {rotations} rotations\nDiameter: {round((shape.max_x * 2),3)} mm', fontsize = 10, verticalalignment = 'top', horizontalalignment = 'right', bbox = dict(facecolor= 'white', alpha = 0.5))
    
    ax.plot(shape.x + max_radius, shape.y + max_radius)
    ax.axis('equal')
    
    canvas.draw()

def update_plot_threaded():
    def task():
        with locking:
            root.after(0, update_plot)
    threading.Thread(target=task).start()
    
    print(selected_shape.get())

def on_slider_change(val):
    update_plot_threaded()

def export_gcode():
    coords = []
    shape = get_epitrochoid(R_slider.get(), r_slider.get(), d_slider.get(), max_radius_slider.get(), res_slider.get())
    last_x = -999
    last_y = -999
    omitted = 0
    
    # Clean the coordinates, convert them from millimeters to inches, and omit duplicates
    for coord in shape.coords:
        coords.append((round(coord[0] * 0.0393701, 3), round(coord[1] * 0.0393701, 3)))
    
    currdatetime = datetime.datetime.now()
    date_time = currdatetime.strftime("%Y-%m-%d_%H-%M-%S")
    
    with open(f'.output\\guilloche_{date_time}.gcode', 'w') as f:
        f.write('%\n')
        f.write('o42069\n')
        f.write('G90\n')    # Use absolute coordinates
        f.write('G20\n')    # Use inches
        f.write('G17\n')    # Use XY plane
        f.write('G40\n')    # Cancel cutter radius compensation
        f.write('G49\n')    # Cancel tool length offset
        f.write('G80\n\n')  # Cancel canned cycles
        f.write('G00 G54 X0 Y0\n\n')    # Rapid move to origin
        f.write('N100 M05 T01\n')   # Tool
        f.write('S7000 M03\n')
        f.write('G00 G43 Z1.0 H01 M08\n')
        f.write(f'G01 X{coords[0][0]} Y{coords[0][1]} F20.\n')
        f.write('G01 Z-0.005 F8.\n\n')
        f.write('(start chewing)\n\n')
        
        for coord in coords:
            # Do not write the same coordinates twice
            if coord[0] != last_x or coord[1] != last_y:
                f.write(f'G01 X{coord[0]} Y{coord[1]} F20.\n')
                last_x = coord[0]
                last_y = coord[1]
            else:
                omitted += 1
        
        f.write('\n\nG01 Z1.0 F20.\n')
        f.write('G00 G53 Z0 M09\n')
        f.write('G00 G53 Y0 M05\n')
        f.write('\n\nM30\n%')
    
    print(f'{omitted} points omitted')

def randomize_sliders():
    R_slider.set(random.randint(1, 100))
    r_slider.set(random.randint(1, 100))
    d_slider.set(random.randint(1, 100))
    #max_radius_slider.set(random.randint(1, 100))
    res_slider.set(random.randint(1, 50))

def on_closing():
    root.quit()
    root.destroy()

# GUI
# Create sliders frame
slider_frame = ttk.Frame(root)
slider_frame.grid(row=0, column=0, sticky='nsew')

# Create plot frame
plot_frame = ttk.Frame(root)
plot_frame.grid(row=0, column=1, sticky='nsew')

# Configure grid layout
root.grid_columnconfigure(0, weight=2)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Create shape dropdown menu
selected_shape = tk.StringVar()
shape_combobox = ttk.Combobox(slider_frame, textvariable=selected_shape, state='readonly', values=['Epitrochoid', 'Hypotrochoid'], postcommand=update_plot_threaded)
shape_combobox.set('Epitrochoid')
shape_combobox.pack(side=tk.TOP, fill=tk.X, expand=1)

# Create sliders for R, r, d, max_radius, and res
R_slider = tk.Scale(slider_frame, label='Radius of fixed circle', from_=1, to=100, resolution=1, variable=R, orient=tk.HORIZONTAL, command=on_slider_change)
R_slider.set(50)
R_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

r_slider = tk.Scale(slider_frame, label='Radius of rollng circle', from_=1, to=100, resolution=1, variable=r, orient=tk.HORIZONTAL, command=on_slider_change)
r_slider.set(30)
r_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

d_slider = tk.Scale(slider_frame, label='Trace point distance from rolling circle', from_=1, to=100, resolution=0.1, variable=d, orient=tk.HORIZONTAL, command=on_slider_change)
d_slider.set(20)
d_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

max_radius_slider = tk.Scale(slider_frame, label='Max overall radius', from_=1, to=100, resolution=1, variable=max_radius, orient=tk.HORIZONTAL, command=on_slider_change)
max_radius_slider.set(22)
max_radius_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

res_slider = tk.Scale(slider_frame, label='Resolution', from_=1, to=50, resolution=1, variable=res, orient=tk.HORIZONTAL, command=on_slider_change)
res_slider.set(25)
res_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

# Create button frame
button_frame = ttk.Frame(slider_frame)
button_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=1)

# Create randomize button
randomize_button = ttk.Button(slider_frame, text="Randomize", command=randomize_sliders)
randomize_button.pack(side=tk.LEFT, fill=tk.X, expand=0)

# Create export button
export_button = ttk.Button(button_frame, text="Export", command=export_gcode)
export_button.pack(side=tk.RIGHT, fill=tk.X, expand=0)

# Create a MPL figure and axes
fig, ax = plt.subplots()

# Create a canvas for the plot
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Initial plot
update_plot()

# Bind the window close even to the on_closing function
root.protocol("WM_DELETE_WINDOW", on_closing)

# Execute main loop
root.mainloop()