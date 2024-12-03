import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import webbrowser
import threading
import os
import time
from concurrent.futures import ThreadPoolExecutor
import rarfile
import subprocess
import re
import base64
from bs4 import BeautifulSoup

global_comment = ""

def log_message(message):
    with open("debug_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def display_download_link(download_url):
    link_popup = tk.Toplevel(root)
    link_popup.title("Lien de téléchargement")
    
    tk.Label(link_popup, text="Lien de téléchargement :").pack(pady=5)
    
    link_entry = ttk.Entry(link_popup, width=50)
    link_entry.pack(pady=5)
    link_entry.insert(0, download_url)
    link_entry.config(state='readonly')  
    tk.Button(link_popup, text="Fermer", command=link_popup.destroy).pack(pady=10)
    
    link_popup.transient(root)
    link_popup.grab_set()
    root.wait_window(link_popup)

def create_rar_archive_with_comment(folder_path):
    global global_comment 
    archive_name = f"{folder_path}.rar"
    command = [r"C:\Program Files\WinRAR\rar.exe", "a", "-r"]

    if global_comment:
        try:
            log_message("Tentative de création du fichier temp_comment.txt...")
            with open("temp_comment.txt", "w", encoding="utf-8") as temp_file:
                temp_file.write(global_comment)
            log_message("Fichier temp_comment.txt créé avec succès.")
        except Exception as e:
            log_message(f"Erreur lors de la création du fichier temp_comment.txt : {e}")
            return None
        command.extend(["-ztemp_comment.txt", f"{archive_name}", f"{folder_path}"])
    else:
        command.extend([f"{archive_name}", f"{folder_path}"])

    try:
        log_message(f"Tentative d'exécution de la commande : {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        log_message(f"Commande exécutée avec succès : {' '.join(command)}")
        log_message(f"Sortie de la commande : {result.stdout}")
    except subprocess.CalledProcessError as e:
        log_message(f"Erreur lors de l'exécution de la commande : {e}")
        log_message(f"Sortie d'erreur : {e.stderr}")
        return None

    if os.path.exists("temp_comment.txt"):
        try:
            os.remove("temp_comment.txt")
            log_message("Fichier temp_comment.txt supprimé avec succès.")
        except Exception as e:
            log_message(f"Erreur lors de la suppression du fichier temp_comment.txt : {e}")

    return archive_name

def upload_file_with_progress(file_path, progress_bar, status_label):
    api_key = 'TA CLEE API'
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
        chunk_size = 5 * 1024 * 1024  
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
            display_download_link(download_url)
            return download_url
        else:
            status_label.config(text="Échec de l'upload.")
            return None
    except requests.exceptions.JSONDecodeError:
        status_label.config(text="Échec du décodage de la réponse JSON.")
        print(response.text)
        return None

def download_file(url, progress, status_label, speed_label, game_name, version, repacker, comment):
    local_filename = url.split('/')[-1]
    local_filename = re.sub(r'[\\/*?:"<>|]', "", local_filename)

    if not local_filename.lower().endswith('.rar'):
        local_filename += '.rar'

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erreur", f"Échec de la requête GET: {e}")
        return

    chunk_size = 5 * 1024 * 1024  # 5 Mo
    downloaded_size = 0
    start_time = time.time()

    file_size = int(response.headers.get('content-length', 0))  # Taille totale du fichier en octets
    total_mb = file_size / (1024 * 1024)  # Taille totale du fichier en Mo

    def update_progress(downloaded_size):
        downloaded_mb = downloaded_size / (1024 * 1024)
        elapsed_time = time.time() - start_time
        speed = downloaded_mb / elapsed_time if elapsed_time > 0 else 0
        progress['value'] = (downloaded_size / file_size) * 100
        status_label.config(text=f"Téléchargé : {downloaded_mb:.2f} Mo / {total_mb:.2f} Mo")
        speed_label.config(text=f"Vitesse : {speed:.2f} Mo/s")
        root.update_idletasks()

    try:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    update_progress(downloaded_size)

        messagebox.showinfo("Information", f"Téléchargement terminé : {local_filename}")
        extract_and_rename(local_filename, game_name, version, repacker, comment)
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du téléchargement : {e}")

def extract_and_rename(filename, game_name, version, repacker, comment):
    dest_folder = f"{game_name} {version} - {repacker} by cFinder"
    os.makedirs(dest_folder, exist_ok=True)
    
    with rarfile.RarFile(filename) as rf:
        rf.extractall(dest_folder)
    
    global global_comment
    global_comment = comment
    
    archive_name = create_rar_archive_with_comment(dest_folder)
    if archive_name:
        messagebox.showinfo("Information", f"Réarchivage terminé : {archive_name}")

        upload_progress_bar = ttk.Progressbar(download_frame, orient='horizontal', length=400, mode='determinate')
        upload_progress_bar.pack(pady=5)

        upload_status_label = ttk.Label(download_frame, text="Prêt pour l'upload")
        upload_status_label.pack(pady=5)

        upload_url = upload_file_with_progress(archive_name, upload_progress_bar, upload_status_label)
        if upload_url:
            messagebox.showinfo("Information", f"Upload terminé : {upload_url}")
        else:
            messagebox.showerror("Erreur", "L'upload a échoué.")
    else:
        messagebox.showwarning("Avertissement", "La création de l'archive a échoué.")

def start_download():
    url = entry_url.get().strip()
    game_name = entry_game_name.get().strip()
    version = entry_version.get().strip()
    repacker = entry_repacker.get().strip()
    comment = entry_comment.get("1.0", tk.END).strip()

    if not url or not game_name or not version or not repacker:
        messagebox.showwarning("Avertissement", "Veuillez remplir tous les champs nécessaires.")
        return

    progress['value'] = 0
    threading.Thread(target=download_file, args=(url, progress, status_label, speed_label, game_name, version, repacker, comment)).start()

def run_search(query, selected_sites, results_dict):
    update_progress(0)
    total_sites = len(selected_sites)
    for index, site in enumerate(selected_sites):
        results = site(query)
        results_dict[query][site.__name__] = results
        progress_value = ((index + 1) / total_sites) * 100
        update_progress(progress_value)
    root.after(0, display_results, results_dict)

def search_ovagames(query):
    base_url = "https://ovagames.com/?s="
    search_url = base_url + query.replace(" ", "+")
    response = requests.get(search_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for article in soup.find_all('article'):
        title = article.find('h2').text.strip()
        link = article.find('a')['href']
        results.append({'title': title, 'link': link})
    return results

def search_steamrip(query):
    base_url = "https://steamrip.com/?s="
    search_url = base_url + query.replace(" ", "+")
    response = requests.get(search_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for article in soup.find_all('article'):
        title = article.find('h2').text.strip()
        link = article.find('a')['href']
        results.append({'title': title, 'link': link})
    return results

def run_search(query, selected_sites, results_dict):
    update_progress(0)
    total_sites = len(selected_sites)
    for index, site in enumerate(selected_sites):
        results = site(query)
        results_dict[query][site.__name__] = results
        progress_value = ((index + 1) / total_sites) * 100
        update_progress(progress_value)
    root.after(0, display_results, results_dict)

def update_progress(value):
    search_progress_bar['value'] = value
    root.update_idletasks()

def search_games():
    query = entry_search.get().strip()
    selected_sites = []
    results_dict = {query: {}}
    
    if var_ovagames.get():
        selected_sites.append(search_ovagames)
    if var_steamrip.get():
        selected_sites.append(search_steamrip)

    if not query or not selected_sites:
        messagebox.showwarning("Avertissement", "Veuillez entrer une recherche et sélectionner au moins un site.")
        return
    
    threading.Thread(target=run_search, args=(query, selected_sites, results_dict)).start()

def display_results(results_dict):
    results_text.delete(1.0, tk.END)
    
    for query, sites in results_dict.items():
        results_text.insert(tk.END, f"Résultats de la recherche pour '{query}':\n")
        for site, results in sites.items():
            results_text.insert(tk.END, f"Site : {site}\n")
            for result in results:
                results_text.insert(tk.END, f"  - {result['title']} : {result['link']}\n")
        results_text.insert(tk.END, "\n")

def clear_text(event):
    event.widget.delete(0, tk.END)

root = tk.Tk()
root.title("Téléchargeur de Jeux")
root.geometry("600x800")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

download_frame = ttk.Frame(notebook)
notebook.add(download_frame, text='Téléchargement')

search_frame = ttk.Frame(notebook)
notebook.add(search_frame, text='Recherche')

entry_url = ttk.Entry(download_frame, width=80)
entry_url.pack(pady=10)
entry_url.insert(0, "Entrez l'URL de téléchargement ici")
entry_url.bind("<FocusIn>", clear_text)

entry_game_name = ttk.Entry(download_frame, width=80)
entry_game_name.pack(pady=10)
entry_game_name.insert(0, "Nom du jeu")
entry_game_name.bind("<FocusIn>", clear_text)

entry_version = ttk.Entry(download_frame, width=80)
entry_version.pack(pady=10)
entry_version.insert(0, "Version")
entry_version.bind("<FocusIn>", clear_text)

entry_repacker = ttk.Entry(download_frame, width=80)
entry_repacker.pack(pady=10)
entry_repacker.insert(0, "Repacker")
entry_repacker.bind("<FocusIn>", clear_text)

entry_comment = tk.Text(download_frame, height=5, width=80)
entry_comment.pack(pady=10)
entry_comment.insert(tk.END, "Commentaire")
entry_comment.bind("<FocusIn>", lambda event: entry_comment.delete("1.0", tk.END))

progress = ttk.Progressbar(download_frame, orient='horizontal', length=400, mode='determinate')
progress.pack(pady=10)

status_label = ttk.Label(download_frame, text="Prêt")
status_label.pack(pady=5)

speed_label = ttk.Label(download_frame, text="Vitesse : 0.00 Mo/s")
speed_label.pack(pady=5)

download_button = ttk.Button(download_frame, text="Démarrer le téléchargement", command=start_download)
download_button.pack(pady=10)

entry_search = ttk.Entry(search_frame, width=80)
entry_search.pack(pady=10)
entry_search.insert(0, "Entrez la recherche de jeu ici")
entry_search.bind("<FocusIn>", clear_text)

var_ovagames = tk.BooleanVar()
check_ovagames = ttk.Checkbutton(search_frame, text='OvaGames', variable=var_ovagames)
check_ovagames.pack(anchor='w')

var_steamrip = tk.BooleanVar()
check_steamrip = ttk.Checkbutton(search_frame, text='SteamRip', variable=var_steamrip)
check_steamrip.pack(anchor='w')

search_button = ttk.Button(search_frame, text="Rechercher", command=search_games)
search_button.pack(pady=10)

search_progress_bar = ttk.Progressbar(search_frame, orient='horizontal', length=400, mode='determinate')
search_progress_bar.pack(pady=10)

results_text = tk.Text(search_frame, height=20, width=80)
results_text.pack(pady=10)

root.mainloop()
