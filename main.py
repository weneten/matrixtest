from flask import Flask, request, render_template, redirect, url_for, flash
import os
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Für Flash-Messages

# Basis-URL des Matrix-Servers
base_url = 'https://matrix.org'
access_token = os.environ['access_token']
chunk_size = 100 * 1000 * 1000  # 100 MB

def upload_chunk(chunk_data, access_token, filename=None):
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/octet-stream'
            }

            if filename:
                headers['Content-Disposition'] = f'attachment; filename="{filename}"'

            response = None  # Initialisiere die Variable `response` vor dem `try`-Block

            try:
                response = requests.post(f'{base_url}/_matrix/media/v3/upload', headers=headers, data=chunk_data)
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


def split_and_upload(file_path, access_token, chunk_size):
    file_size = os.path.getsize(file_path)
    num_chunks = (file_size + chunk_size - 1) // chunk_size

    media_uris = []
    chunk_filenames = []

    for i in range(num_chunks):
        chunk_filename = f'{file_path}_chunk_{i + 1}.part'
        chunk_filenames.append(chunk_filename)

    with open(file_path, 'rb') as file:
        for i in range(num_chunks):
            start_byte = i * chunk_size
            end_byte = min(start_byte + chunk_size, file_size)
            file.seek(start_byte)
            chunk_data = file.read(end_byte - start_byte)

            with open(chunk_filenames[i], 'wb') as chunk_file:
                chunk_file.write(chunk_data)

    for i, chunk_filename in enumerate(chunk_filenames):
        with open(chunk_filename, 'rb') as chunk_file:
            chunk_data = chunk_file.read()
            filename = None
            if i == 0:
                filename = os.path.basename(file_path)
            content_uri = upload_chunk(chunk_data, access_token, filename)
            if content_uri:
                media_uris.append(content_uri)
            else:
                return None  # Fehler beim Upload, brich ab

    for chunk_filename in chunk_filenames:
        os.remove(chunk_filename)

    return media_uris

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename != '':
            # Ensure filename is not None and handle it properly
            filename = uploaded_file.filename
            if filename:
                file_path = os.path.join('uploads', filename)
                uploaded_file.save(file_path)
                media_uris = split_and_upload(file_path, access_token, chunk_size)
                if media_uris:
                    return render_template('result.html', media_uris=media_uris)
                else:
                    flash('Es gab ein Problem beim Hochladen der Datei. Bitte versuche es erneut.')
            else:
                flash('Ungültiger Dateiname. Bitte wähle eine andere Datei.')
        else:
            flash('Es wurde keine Datei ausgewählt.')
        return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)