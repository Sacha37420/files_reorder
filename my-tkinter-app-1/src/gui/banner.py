from tkinter import Toplevel, Button
from PIL import Image, ImageTk, ImageDraw
import os, webbrowser

class Banner:
    def __init__(self, master, links_photos):
        print(f"Banner: __init__ called with {len(links_photos)} links/photos")
        self.master = master
        self.links_photos = links_photos
        self._link_images = []

    def make_rounded_transparent(self, img, size):
        # Utilise une couleur magenta comme couleur de transparence
        transparent_color = (255, 0, 255, 255)  # Magenta opaque
        img = img.convert('RGBA').resize((size, size))
        datas = img.getdata()
        newData = []
        for item in datas:
            # Remplace blanc ou noir par magenta
            if (item[0] > 220 and item[1] > 220 and item[2] > 220) or (item[0] < 35 and item[1] < 35 and item[2] < 35):
                newData.append(transparent_color)
            else:
                newData.append(item)
        img.putdata(newData)
        # Masque circulaire pour bords arrondis
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        # Remplace les pixels transparents par magenta (pour Tkinter)
        img_np = img.copy()
        px = img_np.load()
        for y in range(size):
            for x in range(size):
                if px[x, y][3] == 0:
                    px[x, y] = (255, 0, 255, 255)
        return img_np

    def show(self):
        print("Banner: show() called")
        links = self.links_photos
        print(f"Banner: links_photos count = {len(links)}")
        if not links:
            print("Banner: No links/photos to show.")
            return
        btn_size = 35
        btn_pad = 15
        n = len(links)
        print(f"Banner: n = {n}")
        total_btn_w = n * btn_size + (n-1) * btn_pad
        w = max(320, total_btn_w + 20)
        h = btn_size + 10
        w = max(320, total_btn_w + 20)
        screen_width = self.master.winfo_screenwidth()
        x = int((screen_width - w) / 2)
        y = 0
        magenta_hex = '#FF00FF'
        popup = Toplevel(self.master)
        popup.overrideredirect(1)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.configure(bg=magenta_hex)
        try:
            popup.attributes('-transparentcolor', magenta_hex)
        except Exception:
            pass
        popup.attributes('-topmost', True)
        start_x = (w - total_btn_w) // 2
        btn_y = 5
        for idx, item in enumerate(links):
            url = item.get('url', '').strip()
            photo = item.get('photo', '').strip()
            print(f"Banner: idx={idx}, url={url}, photo={photo}")
            if not url or not photo or not os.path.exists(photo):
                print(f"Banner: Skipping idx={idx} (missing url or photo or file does not exist)")
                continue
            try:
                img = Image.open(photo)
                print(f"Banner: Image loaded for idx={idx}")
                img = self.make_rounded_transparent(img, btn_size)
                print(f"Banner: Image processed for idx={idx}")
                img_tk = ImageTk.PhotoImage(img)
                print(f"Banner: ImageTk created for idx={idx}")
                self._link_images.append(img_tk)
                from tkinter import Label
                lbl = Label(popup, image=img_tk, bg=magenta_hex, borderwidth=0, highlightthickness=0)
                lbl.place(x=start_x + idx * (btn_size + btn_pad), y=btn_y, width=btn_size, height=btn_size)
                lbl.bind('<Button-1>', lambda e, u=url: webbrowser.open(u))
                print(f"Banner: Image placed on label idx={idx}")
            except Exception as e:
                print(f"Banner: Error loading image idx={idx}: {e}")
        popup._link_images = self._link_images
