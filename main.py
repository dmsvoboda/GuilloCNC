# Imports
import tkinter as tk
from tkinter import ttk
import numpy as np
import spyrograph as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import threading

text_obj = None
rotations = 0

locking = threading.Lock()

# Function to draw the spirograph pattern on the canvas
def get_epitrochoid(R, r, d, max_radius, res):
    global rotations
    thetamax = 0 
    
    epitrochoid = sp.Epitrochoid(R = R, r = r, d = d, thetas = np.arange(0, (1024 * np.pi) + (np.pi / res), np.pi / res).tolist())
    coords = [[round(x,10),round(y,10),round(z,10)] for x, y, z in epitrochoid.coords]
    
    for i in range(1, len(coords)):
        if coords[i][0] == coords[0][0] and coords[i][1] == coords[0][1]:
            thetamax = round(((coords[i][2] - (np.pi / res)) / np.pi))
            rotations = thetamax
            break
    
    scale = max_radius / epitrochoid.max_x
    
    return sp.Epitrochoid(R = R, r = r, d = d, thetas = np.arange(0, (thetamax * np.pi) + (np.pi / res), np.pi / res).tolist()).scale(scale)

def update_plot():
    global text_obj
    
    R, r, d, max_radius, res = (slider.get() for slider in [R_slider, r_slider, d_slider, max_radius_slider, res_slider])
    
    epitrochoid = get_epitrochoid(R, r, d, max_radius, res)
    
    ax.clear()
    
    if text_obj is not None:
        text_obj.remove()
    
    text_obj = fig.text(0.95, 0.95, f'R: {R} | r: {r} | d: {d}\nMax Radius: {max_radius}\nResolution: {res}\nClosed: {epitrochoid.is_closed()}\n{len(epitrochoid.coords)} points, {rotations} rotations\nDiameter: {round((epitrochoid.max_x * 2),3)} mm', fontsize = 10, verticalalignment = 'top', horizontalalignment = 'right', bbox = dict(facecolor= 'white', alpha = 0.5))
    
    ax.plot(epitrochoid.x + max_radius, epitrochoid.y + max_radius)
    ax.axis('equal')
    
    canvas.draw()

def update_plot_threaded():
    def task():
        with locking:
            root.after(0, update_plot)
    threading.Thread(target=task).start()

def on_slider_change(val):
    update_plot_threaded()

def randomize_sliders():
    R_slider.set(random.randint(1, 100))
    r_slider.set(random.randint(1, 100))
    d_slider.set(random.randint(1, 100))
    #max_radius_slider.set(random.randint(1, 100))
    res_slider.set(random.randint(1, 50))

def on_closing():
    root.quit()
    root.destroy()

# Create root window
root = tk.Tk()
root.title("GuilloCNC")
root.geometry('800x600')

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

# Create sliders for R, r, d, max_radius, and res
R_slider = tk.Scale(slider_frame, label='Radius of fixed circle', from_=1, to=100, resolution=1, orient=tk.HORIZONTAL, command=on_slider_change)
R_slider.set(50)
R_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

r_slider = tk.Scale(slider_frame, label='Radius of rollng circle', from_=1, to=100, resolution=1, orient=tk.HORIZONTAL, command=on_slider_change)
r_slider.set(30)
r_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

d_slider = tk.Scale(slider_frame, label='Trace point distance from rolling circle', from_=1, to=100, resolution=1, orient=tk.HORIZONTAL, command=on_slider_change)
d_slider.set(20)
d_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

max_radius_slider = tk.Scale(slider_frame, label='Max overall radius', from_=1, to=100, resolution=1, orient=tk.HORIZONTAL, command=on_slider_change)
max_radius_slider.set(22)
max_radius_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

res_slider = tk.Scale(slider_frame, label='Resolution', from_=1, to=50, resolution=1, orient=tk.HORIZONTAL, command=on_slider_change)
res_slider.set(25)
res_slider.pack(side=tk.TOP, fill=tk.X, expand=1)

# Create randomize button
randomize_button = ttk.Button(slider_frame, text="Randomize", command=randomize_sliders)
randomize_button.pack(side=tk.BOTTOM, fill=tk.X, expand=1)

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