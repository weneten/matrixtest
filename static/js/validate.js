document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const MAX_FILE_SIZE = 100 * 1000 * 1000; // 100 MB

    form.addEventListener('submit', function (event) {
        const file = fileInput.files[0];
        if (file && file.size > MAX_FILE_SIZE) {
            event.preventDefault(); // Verhindert das Absenden des Formulars
            alert(`Die Datei ist zu groß. Bitte wähle eine Datei, die kleiner als ${MAX_FILE_SIZE / 1024 / 1024} MB ist.`);
        }
    });
});
