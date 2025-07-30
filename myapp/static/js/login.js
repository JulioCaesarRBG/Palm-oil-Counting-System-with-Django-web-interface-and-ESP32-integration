document
  .getElementById("loginForm")
  .addEventListener("submit", async (event) => {
    event.preventDefault(); // Mencegah form reload halaman

    // Mengambil nilai username dan password dari input
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      // Mengirim data ke endpoint login
      const response = await fetch("http://localhost:3000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      // Memeriksa status respons server
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Error: ${errorData.message}`);
        return;
      }

      // Berhasil login
      const data = await response.json();
      alert(`Login successful! Welcome, ${data.user.username}`);

      // Redirect ke halaman utama (contoh: dashboard)
      window.location.href = "./dashboard.html";
    } catch (error) {
      console.error("Login error:", error);
      alert("An error occurred. Please try again.");
    }
  });
