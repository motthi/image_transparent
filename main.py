from tkinterdnd2 import *
from src.canvas import ImageCanvas


def main():
    root = TkinterDnD.Tk()
    root.geometry("650x500")
    root.title('Image Transparent')
    root.state('zoomed')
    _ = ImageCanvas(root)
    root.mainloop()


if __name__ == '__main__':
    main()
