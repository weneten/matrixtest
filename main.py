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
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Stelle sicher, dass der Upload-Ordner existiert

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

def split_and_upload(file_path, access_token):
    media_uris = []
    filename = os.path.basename(file_path)
    
    with open(file_path, 'rb') as file:
        file_data = file.read()
        content_uri = upload_file(file_data, filename, access_token)
        if content_uri:
            media_uris.append(content_uri)

    return media_uris


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename != '':
            file_size = len(uploaded_file.read())
            uploaded_file.seek(0)  # Zurück zum Anfang der Datei
            if file_size > max_file_size:
                flash(f'Die Datei ist zu groß. Bitte wähle eine Datei, die kleiner als {max_file_size / 1024 / 1024} MB ist.')
                return redirect(url_for('index'))
            
            filename = uploaded_file.filename
            if filename:
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    uploaded_file.save(file_path)
                except Exception as e:
                    flash(f'Fehler beim Speichern der Datei: {e}')
                    return redirect(url_for('index'))

                try:
                    with open(file_path, 'rb') as file:
                        media_uri = upload_file(file.read(), access_token, filename)
                        if media_uri:
                            os.remove(file_path)  # Optional: Entferne die Datei nach dem Upload
                            return render_template('result.html', media_uris=[media_uri])
                        else:
                            flash('Es gab ein Problem beim Hochladen der Datei. Bitte versuche es erneut.')
                except Exception as e:
                    flash(f'Fehler beim Hochladen der Datei: {e}')
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)  # Sicherstellen, dass die Datei gelöscht wird
            else:
                flash('Ungültiger Dateiname. Bitte wähle eine andere Datei.')
        else:
            flash('Es wurde keine Datei ausgewählt.')
        return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
