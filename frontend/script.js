document.getElementById("helloBtn").addEventListener("click", () => {
  fetch("http://127.0.0.1:5000/")
    .then(response => response.text())
    .then(data => {
      document.getElementById("output").innerText = data;
    })
    .catch(error => {
      document.getElementById("output").innerText = "Error: " + error;
    });
});
