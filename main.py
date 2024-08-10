from flask import Flask, request, render_template, redirect, url_for, flash, abort
import os
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Für Flash-Messages
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

# Basis-URL des Matrix-Servers
base_url = 'https://matrix.org'
access_token = os.environ['access_token']

def upload_file(file_data, access_token, filename=None):
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
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename != '':
            filename = uploaded_file.filename
            if filename:
                file_data = uploaded_file.read()
                content_uri = upload_file(file_data, access_token, filename)
                if content_uri:
                    media_uri = f"https://matrix-client.matrix.org/_matrix/media/v3/download/matrix.org/{content_uri.split('/')[-1]}"
                    return render_template('result.html', media_uri=media_uri, filename=filename)
                else:
                    flash('Es gab ein Problem beim Hochladen der Datei. Bitte versuche es erneut.')
            else:
                flash('Ungültiger Dateiname. Bitte wähle eine andere Datei.')
        else:
            flash('Es wurde keine Datei ausgewählt.')
        return redirect(url_for('index'))
    return render_template('index.html')

@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template('error.html', message="Die hochgeladene Datei ist zu groß. Bitte lade eine kleinere Datei hoch."), 413

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
