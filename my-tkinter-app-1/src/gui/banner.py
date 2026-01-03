from tkinter import Toplevel, Button
from PIL import Image, ImageTk, ImageDraw
import os, webbrowser
import requests
from urllib.parse import urlparse
from io import BytesIO
import base64

class Banner:
    def __init__(self, master, links_photos):
        print(f"Banner: __init__ called with {len(links_photos)} links/photos")
        self.master = master
        self.links_photos = links_photos
        self._link_images = []

    def make_rounded_transparent(self, img, size):
        # Ne modifie plus les blancs et noirs, garde les couleurs d'origine
        img = img.convert('RGBA').resize((size, size))
        # Masque circulaire pour bords arrondis
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img

    def show(self):
        print("Banner: show() called")
        links = self.links_photos
        print(f"Banner: links_photos count = {len(links)}")
        if not links:
            return

        # Determine screen dimensions
        screen_w = self.master.winfo_screenwidth()
        w, h = 300, 100
        x = (screen_w - w) // 2
        y = 0  # Position the banner at the very top of the screen

        # Create popup window
        popup = Toplevel(self.master)
        popup.overrideredirect(1)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        import platform
        if platform.system() == "Windows":
            magenta_hex = "#FF00FF"
            popup.configure(bg=magenta_hex)
            try:
                popup.attributes('-transparentcolor', magenta_hex)
                print("[DEBUG] Transparency enabled on Windows.")
            except Exception as e:
                print(f"[WARNING] Transparency not supported: {e}")
        else:  # Linux or other systems
            popup.configure(bg="")
            popup.attributes('-alpha', 0.9)  # Semi-transparent background
            print("[DEBUG] Transparency not supported, using semi-transparent background.")

        popup.attributes('-topmost', True)
        popup.attributes('-disabled', True)  # Prevent popup from intercepting clicks

        # Add buttons or icons
        start_x = (w - len(links) * 50) // 2
        btn_y = 5
        for idx, item in enumerate(links):
            url = item.get('url', '').strip()
            photo = item.get('photo', '')
            print(f"Banner: idx={idx}, url={url}, photo={str(photo)[:40]}")
            img = None
            # Si photo est une chaîne base64 PNG
            if isinstance(photo, str) and len(photo) > 100 and not os.path.exists(photo):
                try:
                    import base64
                    from io import BytesIO
                    img_data = base64.b64decode(photo)
                    img = Image.open(BytesIO(img_data))
                    print(f"Banner: Image loaded from base64 for idx={idx}")
                except Exception as e:
                    print(f"Banner: Error decoding base64 image idx={idx}: {e}")
            elif isinstance(photo, str) and os.path.exists(photo):
                try:
                    img = Image.open(photo)
                    print(f"Banner: Image loaded from file for idx={idx}")
                except Exception as e:
                    print(f"Banner: Error loading image file idx={idx}: {e}")
            else:
                print(f"Banner: Skipping idx={idx} (no valid image)")
                continue
            try:
                if img is None:
                    continue
                if platform.system() == "Windows":
                    img = self.make_rounded_transparent(img, 35)
                    img_tk = ImageTk.PhotoImage(img)
                    self._link_images.append(img_tk)
                    from tkinter import Label
                    lbl = Label(popup, image=img_tk, bg=magenta_hex, borderwidth=0, highlightthickness=0)
                else:
                    img = img.convert('RGBA').resize((35, 35))
                    mask = Image.new('L', (35, 35), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, 35, 35), fill=255)
                    img.putalpha(mask)
                    img_tk = ImageTk.PhotoImage(img)
                    self._link_images.append(img_tk)
                    from tkinter import Label
                    lbl = Label(popup, image=img_tk, bg='white', borderwidth=0, highlightthickness=0)
                lbl.place(x=start_x + idx * (35 + 15), y=btn_y, width=35, height=35)
                lbl.bind('<Button-1>', lambda e, u=url: webbrowser.open(u))
                print(f"Banner: Image placed on label idx={idx}")
            except Exception as e:
                print(f"Banner: Error displaying image idx={idx}: {e}")
        popup._link_images = self._link_images

def fetch_favicon(url, save_dir="favicons"):
    """Télécharge le favicon d'une URL et le sauvegarde localement."""
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        favicon_url = base_url + "/favicon.ico"
        resp = requests.get(favicon_url, timeout=5)
        if resp.status_code == 200 and resp.content:
            img = Image.open(BytesIO(resp.content))
            # Convertit en PNG si besoin
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_path = os.path.join(save_dir, f"{parsed.netloc}.png")
            img.save(save_path, "PNG")
            return save_path
        # Sinon, tente de parser le HTML pour trouver le favicon
        resp_html = requests.get(url, timeout=5)
        if resp_html.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp_html.text, "html.parser")
            icon_link = soup.find("link", rel=lambda v: v and "icon" in v.lower())
            if icon_link and icon_link.get("href"):
                icon_href = icon_link["href"]
                if icon_href.startswith("//"):
                    icon_href = parsed.scheme + ":" + icon_href
                elif icon_href.startswith("/"):
                    icon_href = base_url + icon_href
                elif not icon_href.startswith("http"):
                    icon_href = base_url + "/" + icon_href
                resp_icon = requests.get(icon_href, timeout=5)
                if resp_icon.status_code == 200 and resp_icon.content:
                    img = Image.open(BytesIO(resp_icon.content))
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    save_path = os.path.join(save_dir, f"{parsed.netloc}.png")
                    img.save(save_path, "PNG")
                    return save_path
    except Exception as e:
        print(f"fetch_favicon: erreur pour {url}: {e}")
    return None

def fetch_favicon_base64(url):
    """Télécharge le favicon d'une URL et retourne l'image PNG encodée en base64."""
    try:
        from urllib.parse import urlparse
        import requests
        from PIL import Image
        from io import BytesIO
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        favicon_url = base_url + "/favicon.ico"
        resp = requests.get(favicon_url, timeout=5)
        if resp.status_code == 200 and resp.content:
            img = Image.open(BytesIO(resp.content))
            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return b64
        # Sinon, tente de parser le HTML pour trouver le favicon
        resp_html = requests.get(url, timeout=5)
        if resp_html.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp_html.text, "html.parser")
            icon_link = soup.find("link", rel=lambda v: v and "icon" in v.lower())
            if icon_link and icon_link.get("href"):
                icon_href = icon_link["href"]
                if icon_href.startswith("//"):
                    icon_href = parsed.scheme + ":" + icon_href
                elif icon_href.startswith("/"):
                    icon_href = base_url + icon_href
                elif not icon_href.startswith("http"):
                    icon_href = base_url + "/" + icon_href
                resp_icon = requests.get(icon_href, timeout=5)
                if resp_icon.status_code == 200 and resp_icon.content:
                    img = Image.open(BytesIO(resp_icon.content))
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    return b64
    except Exception as e:
        print(f"fetch_favicon_base64: erreur pour {url}: {e}")
    return None
