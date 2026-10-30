import tkinter as tk
from tkVideoPlayer import TkinterVideo

root = tk.Tk()

# Create video player instance
videoplayer = TkinterVideo(master=root, scaled=True)
videoplayer.load("/home/pi/Desktop/2026-10-22 13:43:45.avi")  # Load the .avi file
videoplayer.pack(expand=True, fill="both")

# Start playback
videoplayer.play()

root.mainloop()
