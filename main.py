import os
from tkinterdnd2 import *
from src.canvas import ImageCanvas


def main():
    root = TkinterDnD.Tk()
    root.geometry("650x500")
    root.title('Image Transparent')
    state = 'zoomed' if 'nt' in os.name else 'normal'
    root.state(state)
    _ = ImageCanvas(root)
    root.mainloop()


if __name__ == '__main__':
    main()
