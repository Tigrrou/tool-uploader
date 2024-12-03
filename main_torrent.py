import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import requests
from bs4 import BeautifulSoup
import webbrowser
import threading
import os
import base64
import time

def log_message(message):
    with open("debug_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

def search_rutor(query):
    try:
        url = f'https://rutor.info/search/{query}/0/0/0'
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all('a', href=True)
        rutor_results = []
        for result in results:
            if query.lower() in result.text.lower():
                title = result.text.strip()
                link = 'https://rutor.info' + result['href']
                download_link = get_download_link(link)
                rutor_results.append({'title': title, 'link': link, 'download_link': download_link})
                log_message(f"Rutor found: {title} -> {link} -> {download_link}")
        return rutor_results
    except requests.RequestException as e:
        log_message(f"Erreur lors de la recherche sur Rutor: {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la recherche sur Rutor: {e}")
        return []

def get_download_link(result_link):
    try:
        response = requests.get(result_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        download_tag = soup.select_one('a[href^="//d.rutor.info/download/"]')
        if download_tag:
            return 'https:' + download_tag['href']
    except requests.RequestException as e:
        log_message(f"Erreur lors de la récupération du lien de téléchargement: {e}")
    return None

def run_search(query, results_dict):
    update_progress(0)
    
    site_results = search_rutor(query)
    if site_results:
        results_dict[query]['rutor'] = site_results
        log_message(f"Results for rutor added to dictionary: {site_results}")
    else:
        log_message(f"No results for rutor for query: {query}")
    update_progress(100)
    
    root.after(0, lambda: display_results(results_dict))

def search_all_sites():
    query = entry.get().strip()
    if not query:
        messagebox.showwarning("Avertissement", "Veuillez entrer un terme de recherche.")
        return

    results_dict = {query: {'rutor': []}}
    threading.Thread(target=lambda: run_search(query, results_dict)).start()

def search_multiple_games(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        queries = [line.strip() for line in file.readlines()]

    if not queries:
        messagebox.showwarning("Avertissement", "Le fichier est vide.")
        return

    results_dict = {query: {'rutor': []} for query in queries}
    threading.Thread(target=lambda: [run_search(query, results_dict) for query in queries]).start()

def display_results(results_dict):
    for tree in [tree_rutor]:
        for item in tree.get_children():
            tree.delete(item)

    for game, results in results_dict.items():
        log_message(f"Displaying results for {game}: {results}")
        if results['rutor']:
            parent = tree_rutor.insert("", tk.END, text=game, values=(f"{game} (Rutor)", "", ""))
            for result in results['rutor']:
                tree_rutor.insert(parent, tk.END, values=(result['title'], result['link'], result['download_link']))
        else:
            parent = tree_rutor.insert("", tk.END, text=game, values=(f"{game} (Rutor) - Aucun résultat", "", ""))

    global latest_results
    latest_results = results_dict

def open_link(event, tree):
    item = tree.selection()[0]
    url = tree.item(item, 'values')[1]
    if url:
        webbrowser.open(url)

def upload_file_with_progress(file_path, progress_bar, status_label):
    api_key = 'db333321-1c7c-4826-bea8-a64962e15312'
    encoded_key = base64.b64encode(f':{api_key}'.encode()).decode()
    url = "https://pixeldrain.com/api/file"
    headers = {
        "Authorization": f"Basic {encoded_key}",
    }

    file_size = os.path.getsize(file_path)

    def update_progress(uploaded_size, total_size):
        progress_value = (uploaded_size / total_size) * 100
        progress_bar['value'] = progress_value
        uploaded_mb = uploaded_size / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        elapsed_time = time.time() - start_time
        speed = uploaded_mb / elapsed_time if elapsed_time > 0 else 0
        status_label.config(text=f"Upload : {uploaded_mb:.2f} Mo / {total_mb:.2f} Mo à {speed:.2f} Mo/s")
        root.update_idletasks()

    with open(file_path, 'rb') as f:
        session = requests.Session()
        uploaded_size = 0
        start_time = time.time()
        chunk_size = 5 * 1024 * 1024  # 5 Mo
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            files = {'file': (os.path.basename(file_path), chunk)}
            response = session.post(url, headers=headers, files=files, stream=True)
            if response.status_code >= 400:
                status_label.config(text=f"Erreur d'upload : {response.status_code}")
                print(response.text)
                return None
            uploaded_size += len(chunk)
            update_progress(uploaded_size, file_size)

    try:
        result = response.json()
        if result.get('success'):
            file_id = result.get('id')
            download_url = f"https://pixeldrain.com/u/{file_id}"
            print(f"File uploaded successfully! Download URL: {download_url}")
            show_download_link(download_url) 
            return download_url
        else:
            status_label.config(text="Échec de l'upload.")
            return None
    except requests.exceptions.JSONDecodeError:
        status_label.config(text="Échec du décodage de la réponse JSON.")
        print(response.text)
        return None

def download_and_upload_file(url, filename):
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        upload_link = upload_file_with_progress(filename, progress, status_bar)
        if upload_link:
            show_download_link(upload_link)
        else:
            messagebox.showerror("Erreur", "Erreur lors de l'upload du fichier sur PixelDrain.")
    except requests.RequestException as e:
        log_message(f"Erreur lors du téléchargement du fichier: {e}")
        messagebox.showerror("Erreur", f"Erreur lors du téléchargement du fichier: {e}")

def upload_to_pixeldrain(file_path):
    url = 'https://pixeldrain.com/api/file'
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files)
            response.raise_for_status()
            json_response = response.json()
            if 'success' in json_response and json_response['success']:
                file_id = json_response['id']
                download_link = f"https://pixeldrain.com/u/{file_id}"
                log_message(f"Fichier uploadé sur PixelDrain avec succès. Lien de téléchargement : {download_link}")
                return download_link
            else:
                log_message(f"Erreur : Aucun identifiant de fichier trouvé dans la réponse de Pixeldrain. Réponse : {json_response}")
    except requests.RequestException as e:
        log_message(f"Erreur lors de l'upload du fichier sur PixelDrain: {e}")
    except Exception as e:
        log_message(f"Erreur lors de l'upload du fichier sur PixelDrain : {e}")
    return None

def show_download_link(download_link):
    link_popup = tk.Toplevel(root)
    link_popup.title("Lien de téléchargement")
    link_popup.geometry("400x100")

    label = ttk.Label(link_popup, text="Lien de téléchargement :")
    label.pack(pady=10)

    link_entry = ttk.Entry(link_popup, width=50)
    link_entry.insert(0, download_link)
    link_entry.config(state='readonly')
    link_entry.pack(pady=5)

    def open_link_event(event):
        webbrowser.open(download_link)

    link_entry.bind("<Double-1>", open_link_event)

    link_popup.mainloop()

def download_and_upload_specific_file():
    selected_item = tree_rutor.selection()
    if not selected_item:
        messagebox.showwarning("Avertissement", "Veuillez sélectionner un fichier à télécharger et uploader.")
        return
    
    item = tree_rutor.item(selected_item[0])
    url = item['values'][2]
    if url:
        dialog = DownloadDialog(root)
        root.wait_window(dialog.top)
        
        if dialog.result:
            nom_du_jeu, version, cracker = dialog.result
            if not (nom_du_jeu and version and cracker):
                messagebox.showwarning("Avertissement", "Toutes les informations doivent être renseignées.")
                return

            local_filename = f"[cfinder.xyz] {nom_du_jeu} {version} - {cracker}.torrent"
            
            download_and_upload_file(url, local_filename)

class DownloadDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Informations pour le téléchargement et l'upload")
        self.top.geometry("300x150")
        self.result = None
        
        self.label1 = ttk.Label(self.top, text="Nom du jeu :")
        self.label1.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry1 = ttk.Entry(self.top)
        self.entry1.grid(row=0, column=1, padx=5, pady=5)
        
        self.label2 = ttk.Label(self.top, text="Version :")
        self.label2.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry2 = ttk.Entry(self.top)
        self.entry2.grid(row=1, column=1, padx=5, pady=5)
        
        self.label3 = ttk.Label(self.top, text="Cracker :")
        self.label3.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry3 = ttk.Entry(self.top)
        self.entry3.grid(row=2, column=1, padx=5, pady=5)
        
        self.button = ttk.Button(self.top, text="Valider", command=self.ok)
        self.button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def ok(self):
        nom_du_jeu = self.entry1.get().strip()
        version = self.entry2.get().strip()
        cracker = self.entry3.get().strip()
        
        self.result = (nom_du_jeu, version, cracker)
        self.top.destroy()

def update_progress(value):
    progress['value'] = value
    root.update_idletasks()

def show_about():
    about_text = """Cette application de recherche est actuellement en version bêta et a été développée par Tigrrou_. \nDes bugs et des problèmes peuvent survenir, n'hésitez pas à me dm pour les reports ainsi que pour d'éventuelles suggestions."""
    messagebox.showinfo("À propos", about_text)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Fichiers texte", "*.txt")])
    if file_path:
        search_multiple_games(file_path)

root = tk.Tk()
root.title("Recherche Multi-Sites")
root.geometry("800x600")

main_bg_color = "#f0f0f0"
button_bg_color = "#005f5f"
button_hover_color = "#004d4d"
label_bg_color = "#e6e6e6"
label_fg_color = "#000000"
progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
status_bar = ttk.Label(root, text="Prêt", relief=tk.SUNKEN, anchor=tk.W)
style = ttk.Style()
style.theme_use("clam")

style.configure("TButton", padding=6, relief="flat", background=button_bg_color, foreground="#ffffff", font=("Helvetica", 10, "bold"))
style.map("TButton", background=[("active", button_hover_color)])
style.configure("TLabel", background=label_bg_color, foreground=label_fg_color, font=("Helvetica", 12))
root.configure(bg=main_bg_color)

entry_label = ttk.Label(root, text="Entrez votre recherche:")
entry_label.pack(pady=10)

entry = ttk.Entry(root, width=50)
entry.pack(pady=5)

button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

rutor_var = tk.BooleanVar(value=True)

search_button = ttk.Button(root, text="Rechercher", command=search_all_sites)
search_button.pack(pady=10)

file_button = ttk.Button(root, text="Rechercher depuis un fichier", command=select_file)
file_button.pack(pady=5)

progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress.pack(pady=5)

notebook = ttk.Notebook(root)
notebook.pack(padx=10, pady=10, fill='both', expand=True)

tree_frame_rutor = ttk.Frame(notebook)

tree_rutor = ttk.Treeview(tree_frame_rutor, columns=("Title", "Link", "Download"), show='headings')
tree_rutor.heading("Title", text="Titre")
tree_rutor.heading("Link", text="Lien")
tree_rutor.heading("Download", text="Lien de Téléchargement")
tree_rutor.column("Download", width=200, anchor='center')
tree_rutor.pack(fill='both', expand=True)

download_button = ttk.Button(root, text="Télécharger et Upload le fichier sélectionné", command=download_and_upload_specific_file)
download_button.pack(pady=5)

notebook.add(tree_frame_rutor, text='Rutor')

tree_rutor.bind("<Double-1>", lambda event: open_link(event, tree_rutor))

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

about_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="À propos", menu=about_menu)
about_menu.add_command(label="À propos", command=show_about)

status_bar = ttk.Label(root, text="Prêt", relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

root.mainloop()
