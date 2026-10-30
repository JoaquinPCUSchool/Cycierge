import tkinter as tk
from tkVideoPlayer import TkinterVideo
root = tk.Tk()
root.title("Video Player")

# scaled=False ? plays at native resolution (no stretching)
videoplayer = TkinterVideo(master=root, scaled=False)
videoplayer.load("video.avi")
videoplayer.pack(expand=True, fill="both")

# Label to show the resolution
info_label = tk.Label(root, text="Loading...")
info_label.pack()


videoplayer.play()
root.mainloop()
