import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import *
from PIL import Image, ImageTk
from src.history import History, Log

SCALE_MAX = 5.0
SCALE_MIN = 0.3


class ImageCanvas:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.img: np.ndarray = None
        self.img_tk: ImageTk.PhotoImage = None
        self.history = History()
        self.scale = 1.0

        # Canvas
        self.canvas = tk.Canvas(
            master=self.root,
            width=self.root.winfo_screenwidth(),
            height=self.root.winfo_screenheight(),
            scrollregion=(0, 0, self.root.winfo_screenwidth() * 2, self.root.winfo_screenheight() * 2),
            bg="white",
        )

        # Scrollbar
        vscrollbar = tk.Scrollbar(
            self.root, orient=tk.VERTICAL, command=self.canvas.yview
        )
        hscrollbar = tk.Scrollbar(
            self.root, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=hscrollbar.set)
        self.canvas.configure(yscrollcommand=vscrollbar.set)
        self.canvas.place(x=0, y=0)

        # Background
        self.bkg_img = cv2.imread("./imgs/background.png")
        self.bkg_img_tk = ImageTk.PhotoImage(Image.fromarray(self.bkg_img))
        self.canvas.config(scrollregion=(0, 0, self.bkg_img_tk.width(), self.bkg_img_tk.height()))
        self.canvas.create_image(0, 0, image=self.bkg_img_tk, anchor="nw", tag="background")

        # Keybind
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.callbackDrop)
        self.root.bind("<Control-n>", self.callbackReset)
        self.root.bind("<ButtonPress-1>", self.callbackButtonPress)
        self.root.bind("<MouseWheel>", self.callbackVerticalScroll)
        self.root.bind("<Control-MouseWheel>", self.callbackZoom)
        self.root.bind("<Shift-MouseWheel>", self.callbackHorizontalScroll)
        self.root.bind('<Control-s>', self.callbackSaveImage)
        self.root.bind("<Control-y>", self.callbackRedo)
        self.root.bind("<Control-z>", self.callbackUndo)
        self.root.bind("<Control-semicolon>", self.callbackEnlarge)
        self.root.bind("<Control-minus>", self.callbackShrink)
        self.root.bind("<Control-0>", self.callbackZoomDefault)

    def depict_img(self):
        self.canvas.delete("image")
        img = cv2.resize(self.img, None, fx=self.scale, fy=self.scale)
        self.img_tk = ImageTk.PhotoImage(Image.fromarray(img))
        self.canvas.config(scrollregion=(0, 0, self.img_tk.width(), self.img_tk.height()))
        if img.shape[0] > self.bkg_img.shape[0] or img.shape[1] > self.bkg_img.shape[1]:
            self.canvas.delete("background")
            hnum = int(np.ceil(img.shape[0] / self.bkg_img.shape[0]))
            wnum = int(np.ceil(img.shape[1] / self.bkg_img.shape[1]))
            bkg_img = np.tile(self.bkg_img, (hnum, wnum, 1))
            self.bkg_img_tk = ImageTk.PhotoImage(Image.fromarray(bkg_img))
            self.canvas.create_image(0, 0, image=self.bkg_img_tk, anchor="nw", tag="background")
        self.canvas.create_image(0, 0, image=self.img_tk, anchor="nw", tag="image")

    def callbackReset(self, event):
        self.img = None
        self.img_tk = None
        self.history = History()
        self.scale = 1.0
        self.canvas.delete("image")
        self.canvas.delete("background")
        self.canvas.config(scrollregion=(0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.canvas.create_image(0, 0, image=self.bkg_img_tk, anchor="nw", tag="background")

    def callbackVerticalScroll(self, event):
        if event.delta > 0:
            self.canvas.yview_scroll(-1, 'units')
        elif event.delta < 0:
            self.canvas.yview_scroll(1, 'units')

    def callbackHorizontalScroll(self, event):
        if event.delta > 0:
            self.canvas.xview_scroll(-1, 'units')
        elif event.delta < 0:
            self.canvas.xview_scroll(1, 'units')

    def callbackSaveImage(self, event):
        filename = filedialog.asksaveasfilename(initialdir=os.getcwd(), title="Save image file", filetypes=[("PNG file", "*.png")])
        if not filename or len(filename) == 0:
            return
        filebasenm, _ = os.path.splitext(filename)
        img = cv2.cvtColor(self.img, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(f"{filebasenm}.png", img)

    def callbackDrop(self, event):
        files = event.data.split()
        if len(files) > 1:
            tk.messagebox.showwarning("Warning", "Please drop only one image file")
            return

        self.imf = files[0]
        if not self.imf.endswith('.jpg') and not self.imf.endswith('.png'):
            tk.messagebox.showwarning("Warning", "Please drop only jpg or png file")
            return

        self.scale = 1.0
        self.img = cv2.imread(files[0], -1)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGBA)
        self.depict_img()

    def callbackButtonPress(self, event):
        if self.img_tk is None:
            return
        if event.x < 0 or event.x > self.img_tk.width() or event.y < 0 or event.y > self.img_tk.height():
            return

        canvas = event.widget
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        pix_x = int(x / self.scale)
        pix_y = int(y / self.scale)

        prev_img = self.img.copy()
        trans_area = self.img[:, :, 3] == 0     # Store transparent area (this area is disappeared at the next line)
        img = self.img[:, :, :3].copy()         # Without copy(), the error occures "Layout of the output array image is incompatible with cv::Mat"
        h, w = img.shape[:2]
        mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        _, img, mask, _ = cv2.floodFill(img, mask, (pix_x, pix_y), (0, 0, 0), flags=4 | 255 << 8 | cv2.FLOODFILL_MASK_ONLY)
        prev_value = prev_img[pix_y, pix_x]

        mask = mask[1:-1, 1:-1]
        self.img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        self.img[trans_area, 3] = 0
        self.img[mask == 255, 3] = 0
        self.depict_img()

        # Register history
        log = Log(
            idx=mask == 255,
            prev_value=prev_value,
            new_value=(0, 0, 0, 0)
        )
        self.history.add_log(log)

    def callbackUndo(self, event):
        log = self.history.undo()
        if log is None:
            return

        self.img[log.idx] = log.prev_value
        self.depict_img()

    def callbackRedo(self, event):
        log = self.history.redo()
        if log is None:
            return

        self.img[log.idx] = log.new_value
        self.depict_img()

    def callbackZoom(self, event):
        if self.img is None:
            return
        if event.delta > 0:
            if self.scale > SCALE_MAX:
                return
            self.scale *= 1.25
        elif event.delta < 0:
            if self.scale < SCALE_MIN:
                return
            self.scale *= 0.8
        if np.abs(self.scale - 1.0) < 1e-5:
            self.scale = 1.0

        self.depict_img()

    def callbackEnlarge(self, event):
        if self.img is None:
            return
        if self.scale > SCALE_MAX:
            return
        self.scale *= 1.25
        if np.abs(self.scale - 1.0) < 1e-5:
            self.scale = 1.0
        self.depict_img()

    def callbackShrink(self, event):
        if self.img is None:
            return
        if self.scale < SCALE_MIN:
            return
        self.scale *= 0.8
        if np.abs(self.scale - 1.0) < 1e-5:
            self.scale = 1.0
        self.depict_img()

    def callbackZoomDefault(self, event):
        if self.img is None:
            return
        self.scale = 1.0
        self.depict_img()
