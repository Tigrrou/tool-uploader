import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import webbrowser
import threading
import csv
import os


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
                rutor_results.append({'title': title, 'link': link})
                log_message(f"Rutor found: {title} -> {link}")
        return rutor_results
    except requests.RequestException as e:
        log_message(f"Erreur lors de la recherche sur Rutor: {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la recherche sur Rutor: {e}")
        return []

def search_ovagames(query):
    try:
        url = 'https://www.ovagames.com/?s=' + query
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all('a', href=True, title=True)
        ovagames_results = []
        for result in results:
            if query.lower() in result['title'].lower():
                title = result['title'].strip()
                link = result['href']
                ovagames_results.append({'title': title, 'link': link})
                log_message(f"OvaGames found: {title} -> {link}")
        return ovagames_results
    except requests.RequestException as e:
        log_message(f"Erreur lors de la recherche sur OvaGames: {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la recherche sur OvaGames: {e}")
        return []
def search_goggames(query):
    try:
        url = f'https://gog-games.to/search/{query}'
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all('a', class_='block')
        goggames_results = []
        for result in results:
            title = result.find('div', class_='info').find('span', class_='title').text.strip()
            link = 'https://gog-games.to' + result['href']
            goggames_results.append({'title': title, 'link': link})
            log_message(f"GogGames found: {title} -> {link}")
        return goggames_results
    except requests.RequestException as e:
        log_message(f"Erreur lors de la recherche sur GogGames: {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la recherche sur GogGames: {e}")
        return []

def search_steamrip(query):
    try:
        url = 'https://steamrip.com/?s=' + query
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all('a', class_='all-over-thumb-link')
        steamrip_results = []
        for result in results:
            if query.lower() in result['href']:
                title = result.find('span', class_='screen-reader-text').text.strip()
                link = url
                steamrip_results.append({'title': title, 'link': link})
                log_message(f"Steamrip found: {title} -> {link}")
        return steamrip_results
    except requests.RequestException as e:
        log_message(f"Erreur lors de la recherche sur Steamrip: {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la recherche sur Steamrip: {e}")
        return []

def run_search(query, selected_sites, results_dict):
    update_progress(0)
    progress_step = 100 / len(selected_sites)
    
    for index, search_function in enumerate(selected_sites):
        site_results = search_function(query)
        site_name = search_function.__name__.split('_')[1]
        if site_results:
            results_dict[query][site_name] = site_results
            log_message(f"Results for {site_name} added to dictionary: {site_results}")
        else:
            log_message(f"No results for {site_name} for query: {query}")
        update_progress(progress_step * (index + 1))
    
    root.after(0, lambda: display_results(results_dict))

def search_all_sites():
    query = entry.get().strip()
    if not query:
        messagebox.showwarning("Avertissement", "Veuillez entrer un terme de recherche.")
        return

    selected_sites = []
    if rutor_var.get():
        selected_sites.append(search_rutor)
    if ovagames_var.get():
        selected_sites.append(search_ovagames)
    if steamrip_var.get():
        selected_sites.append(search_steamrip)
    if goggames_var.get():
        selected_sites.append(search_goggames)

    if not selected_sites:
        messagebox.showwarning("Avertissement", "Veuillez sélectionner au moins un site.")
        return

    results_dict = {query: {'rutor': [], 'ovagames': [], 'steamrip': [], 'goggames': []}}
    threading.Thread(target=lambda: run_search(query, selected_sites, results_dict)).start()
    save_search_history(query)

def search_multiple_games(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        queries = [line.strip() for line in file.readlines()]

    if not queries:
        messagebox.showwarning("Avertissement", "Le fichier est vide.")
        return

    selected_sites = []
    if rutor_var.get():
        selected_sites.append(search_rutor)
    if ovagames_var.get():
        selected_sites.append(search_ovagames)
    if steamrip_var.get():
        selected_sites.append(search_steamrip)
    if goggames_var.get():
        selected_sites.append(search_goggames)

    if not selected_sites:
        messagebox.showwarning("Avertissement", "Veuillez sélectionner au moins un site.")
        return

    results_dict = {query: {'rutor': [], 'ovagames': [], 'steamrip': [], 'goggames': []} for query in queries}
    threading.Thread(target=lambda: [run_search(query, selected_sites, results_dict) for query in queries]).start()


def display_results(results_dict):
    for tree in [tree_rutor, tree_ovagames, tree_steamrip, tree_goggames]:
        for item in tree.get_children():
            tree.delete(item)

    for game, results in results_dict.items():
        log_message(f"Displaying results for {game}: {results}")
        if results['rutor']:
            parent = tree_rutor.insert("", tk.END, text=game, values=(f"{game} (Rutor)", ""))
            for result in results['rutor']:
                tree_rutor.insert(parent, tk.END, values=(result['title'], result['link']))
        else:
            parent = tree_rutor.insert("", tk.END, text=game, values=(f"{game} (Rutor) - Aucun résultat", ""))

        if results['ovagames']:
            parent = tree_ovagames.insert("", tk.END, text=game, values=(f"{game} (OvaGames)", ""))
            for result in results['ovagames']:
                tree_ovagames.insert(parent, tk.END, values=(result['title'], result['link']))
        else:
            parent = tree_ovagames.insert("", tk.END, text=game, values=(f"{game} (OvaGames) - Aucun résultat", ""))

        if results['steamrip']:
            parent = tree_steamrip.insert("", tk.END, text=game, values=(f"{game} (Steamrip)", ""))
            for result in results['steamrip']:
                tree_steamrip.insert(parent, tk.END, values=(result['title'], result['link']))
        else:
            parent = tree_steamrip.insert("", tk.END, text=game, values=(f"{game} (Steamrip) - Aucun résultat", ""))

        if results['goggames']:
            parent = tree_goggames.insert("", tk.END, text=game, values=(f"{game} (GogGames)", ""))
            for result in results['goggames']:
                tree_goggames.insert(parent, tk.END, values=(result['title'], result['link']))
        else:
            parent = tree_goggames.insert("", tk.END, text=game, values=(f"{game} (GogGames) - Aucun résultat", ""))

    global latest_results
    latest_results = results_dict


def open_link(event, tree):
    item = tree.selection()[0]
    url = tree.item(item, 'values')[1]
    if url:
        webbrowser.open(url)

def save_results():
    with open('search_results.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Jeu", "Site", "Titre", "Lien"])
        for game, results in latest_results.items():
            for site, site_results in results.items():
                for result in site_results:
                    writer.writerow([game, site, result['title'], result['link']])
    messagebox.showinfo("Information", "Résultats sauvegardés dans search_results.csv")



def update_progress(value):
    progress['value'] = value
    root.update_idletasks()

def save_search_history(query):
    with open("search_history.txt", "a", encoding="utf-8") as history_file:
        history_file.write(query + "\n")

def show_search_history():
    history_file = "search_history.txt"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as file:
            history = file.read()
        messagebox.showinfo("Historique des recherches", history)
    else:
        messagebox.showinfo("Historique des recherches", "Aucun historique trouvé.")

def on_select(event):
    item = tree_rutor.selection()[0]
    link = tree_rutor.item(item, "values")[1]
    if link:
        webbrowser.open(link)

def update_status(message):
    status_bar.config(text=message)
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

rutor_var = tk.BooleanVar()
ovagames_var = tk.BooleanVar()
steamrip_var = tk.BooleanVar()
goggames_var = tk.BooleanVar()

rutor_check = ttk.Checkbutton(button_frame, text="Rutor", variable=rutor_var)
rutor_check.grid(row=0, column=0, padx=10)
ovagames_check = ttk.Checkbutton(button_frame, text="OvaGames", variable=ovagames_var)
ovagames_check.grid(row=0, column=1, padx=10)
steamrip_check = ttk.Checkbutton(button_frame, text="Steamrip", variable=steamrip_var)
steamrip_check.grid(row=0, column=2, padx=10)
goggames_check = ttk.Checkbutton(button_frame, text="GogGames", variable=goggames_var)
goggames_check.grid(row=0, column=4, padx=10)


search_button = ttk.Button(root, text="Rechercher", command=search_all_sites)
search_button.pack(pady=10)

file_button = ttk.Button(root, text="Rechercher depuis un fichier", command=select_file)
file_button.pack(pady=5)

progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress.pack(pady=5)

notebook = ttk.Notebook(root)
notebook.pack(padx=10, pady=10, fill='both', expand=True)

tree_frame_rutor = ttk.Frame(notebook)
tree_frame_ovagames = ttk.Frame(notebook)
tree_frame_steamrip = ttk.Frame(notebook)

tree_rutor = ttk.Treeview(tree_frame_rutor, columns=("Title", "Link"), show='headings')
tree_rutor.heading("Title", text="Titre")
tree_rutor.heading("Link", text="Lien")
tree_rutor.pack(fill='both', expand=True)

tree_ovagames = ttk.Treeview(tree_frame_ovagames, columns=("Title", "Link"), show='headings')
tree_ovagames.heading("Title", text="Titre")
tree_ovagames.heading("Link", text="Lien")
tree_ovagames.pack(fill='both', expand=True)

tree_steamrip = ttk.Treeview(tree_frame_steamrip, columns=("Title", "Link"), show='headings')
tree_steamrip.heading("Title", text="Titre")
tree_steamrip.heading("Link", text="Lien")
tree_steamrip.pack(fill='both', expand=True)
tree_frame_goggames = ttk.Frame(notebook)

tree_goggames = ttk.Treeview(tree_frame_goggames, columns=("Title", "Link"), show='headings')
tree_goggames.heading("Title", text="Titre")
tree_goggames.heading("Link", text="Lien")
tree_goggames.pack(fill='both', expand=True)

notebook.add(tree_frame_rutor, text='Rutor')
notebook.add(tree_frame_ovagames, text='OvaGames')
notebook.add(tree_frame_steamrip, text='Steamrip')
notebook.add(tree_frame_goggames, text='GogGames')

tree_rutor.bind("<Double-1>", lambda event: open_link(event, tree_rutor))
tree_ovagames.bind("<Double-1>", lambda event: open_link(event, tree_ovagames))
tree_steamrip.bind("<Double-1>", lambda event: open_link(event, tree_steamrip))
tree_goggames.bind("<Double-1>", lambda event: open_link(event, tree_goggames))

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Fichier", menu=file_menu)
file_menu.add_command(label="Sauvegarder les résultats", command=save_results)


history_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Historique", menu=history_menu)
history_menu.add_command(label="Afficher l'historique des recherches", command=show_search_history)

about_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="À propos", menu=about_menu)
about_menu.add_command(label="À propos", command=show_about)

status_bar = ttk.Label(root, text="Prêt", relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

root.mainloop()
