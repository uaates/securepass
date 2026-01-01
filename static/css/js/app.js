function reveal(enc, btn) {
  fetch('/decode?val=' + encodeURIComponent(enc))
    .then(r => r.text())
    .then(p => {
      navigator.clipboard.writeText(p);
      btn.textContent = "Kopyalandı!";
      btn.classList.remove("btn-outline-light");
      btn.classList.add("btn-success");
      setTimeout(() => {
        btn.textContent = "Göster";
        btn.classList.remove("btn-success");
        btn.classList.add("btn-outline-light");
      }, 2000);
    });
}
