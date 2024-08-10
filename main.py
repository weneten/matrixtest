from flask import Flask, request, render_template, redirect, url_for, flash
import os
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Für Flash-Messages

# Basis-URL des Matrix-Servers
base_url = 'https://matrix.org'
access_token = os.environ.get('ACCESS_TOKEN')  # Zugriffstoken aus Umgebungsvariablen
max_file_size = 100 * 1024 * 1024  # 100 MB

UPLOAD_FOLDER = 'uploads'

# Verzeichnis erstellen, falls es nicht existiert
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
        print(f"Ordner '{UPLOAD_FOLDER}' erfolgreich erstellt.")
    except Exception as e:
        print(f"Fehler beim Erstellen des Ordners '{UPLOAD_FOLDER}': {e}")
        raise

def upload_file(file_data, filename, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/octet-stream'
    }

    if filename:
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'

    try:
        response = requests.post(f'{base_url}/_matrix/media/v3/upload', headers=headers, data=file_data)
        response.raise_for_status()
        response_json = response.json()
        content_uri = response_json.get('content_uri')
        if content_uri:
            return content_uri
        else:
            raise Exception("Fehlende content_uri in der Antwort")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        if response is not None:
            print("Response content:", response.text)
        return None
    except Exception as err:
        print(f"An error occurred: {err}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            try:
                # Versuche, die Datei zu speichern
                uploaded_file.save(file_path)
                
                # Prüfe die Datei auf Größe
                if os.path.getsize(file_path) > max_file_size:  # 100 MB
                    os.remove(file_path)
                    flash('Die Datei ist zu groß. Maximal erlaubte Größe ist 100 MB.')
                    return redirect(url_for('index'))
                
                # Lese die Datei und lade sie hoch
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                    media_uri = upload_file(file_data, filename, access_token)
                
                if media_uri:
                    media_link = f'https://matrix-client.matrix.org/_matrix/media/v3/download/matrix.org/{media_uri.split("/")[-1]}'
                    return render_template('result.html', filename=filename, media_link=media_link)
                else:
                    flash('Es gab ein Problem beim Hochladen der Datei. Bitte versuche es erneut.')
            except Exception as e:
                print(f'Fehler beim Speichern der Datei: {e}')
                flash('Es gab ein Problem beim Speichern der Datei. Bitte versuche es erneut.')
        else:
            flash('Es wurde keine Datei ausgewählt.')
        return redirect(url_for('index'))
    return render_template('index.html')
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
