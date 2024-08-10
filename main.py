from flask import Flask, request, render_template, redirect, url_for, flash
import os
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Für Flash-Messages

# Basis-URL des Matrix-Servers
base_url = 'https://matrix.org'
access_token = os.environ['ACCESS_TOKEN']  # Umgebungsvariable für Access Token
chunk_size = 100 * 1000 * 1000  # 100 MB

def upload_chunk(chunk_data, access_token, filename=None):
    """
    Lädt einen Chunk der Datei hoch.

    :param chunk_data: Die Chunk-Daten im Speicher.
    :param access_token: Zugriffstoken für die Authentifizierung.
    :param filename: Optionaler Dateiname, der im Content-Disposition-Header angegeben wird.
    :return: Die URI des hochgeladenen Chunks.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/octet-stream'
    }
    if filename:
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'

    try:
        response = requests.post(f'{base_url}/_matrix/media/v3/upload', headers=headers, data=chunk_data)
        response.raise_for_status()  # Check for HTTP errors
        response_json = response.json()
        content_uri = response_json.get('content_uri')
        if content_uri:
            return content_uri
        else:
            raise Exception("Fehlende content_uri in der Antwort")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print("Response content:", response.text)
        return None
    except Exception as err:
        print(f"An error occurred: {err}")
        return None

def split_and_upload(file, access_token, chunk_size):
    """
    Teilt eine Datei in Chunks auf, benennt die Chunks und lädt sie hoch.
    :param file: Die Dateiobjekt im Speicher.
    :param access_token: Zugriffstoken für die Authentifizierung.
    :param chunk_size: Größe der Chunks in Byte.
    :return: Liste von URIs der hochgeladenen Chunks.
    """
    file_size = len(file.read())
    file.seek(0)  # Setzt den Lesezeiger zurück, um die Datei erneut lesen zu können
    num_chunks = (file_size + chunk_size - 1) // chunk_size

    media_uris = []
    for i in range(num_chunks):
        start_byte = i * chunk_size
        end_byte = min(start_byte + chunk_size, file_size)

        file.seek(start_byte)
        chunk_data = file.read(end_byte - start_byte)

        filename = None
        if i == 0:
            filename = os.path.basename('uploaded_file')  # Nutze einen temporären Namen für den ersten Chunk

        content_uri = upload_chunk(chunk_data, access_token, filename)
        if content_uri:
            media_uris.append(content_uri)
        else:
            return None  # Fehler beim Upload, brich ab

    return media_uris

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename != '':
            media_uris = split_and_upload(uploaded_file, access_token, chunk_size)
            if media_uris:
                return render_template('result.html', media_uris=media_uris)
            else:
                flash('Es gab ein Problem beim Hochladen der Datei. Bitte versuche es erneut.')
        else:
            flash('Es wurde keine Datei ausgewählt.')
        return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
