// copy-link.js
function copyLink() {
    const link = document.querySelector('.download-link').href;
    navigator.clipboard.writeText(link)
        .then(() => {
            alert('Link wurde in die Zwischenablage kopiert!');
        })
        .catch(err => {
            console.error('Fehler beim Kopieren des Links: ', err);
            alert('Fehler beim Kopieren des Links.');
        });
}
