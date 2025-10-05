
/* Index DashBoard */
async function loadMessages() {
      const res = await fetch("/api/messages/");
      const data = await res.json();
      const list = document.getElementById("messages");
      list.innerHTML = "";
      data.forEach(m => {
        const li = document.createElement("li");
        li.textContent = `${m.user}: ${m.content}`;
        list.appendChild(li);
      });
    }

async function addMessage() {
      const user = document.getElementById("user").value;
      const content = document.getElementById("content").value;

      const res = await fetch("/api/messages/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({user, content})
      });

      const data = await res.json();
      alert(data.message);
      document.getElementById("content").value = "";
      loadMessages();
    }

    window.onload = loadMessages;


    /* Customer DataBase */
async function loadCustomers() {
      const res = await fetch("/api/customers/");
      const data = await res.json();
      const list = document.getElementById("customerList");
      if (list) {
          list.innerHTML = "";
        }
      data.forEach(c => {
        const li = document.createElement("li");
        li.textContent = `${c.username} (${c.email})`;
        list.appendChild(li);
      });
    }

    window.onload = loadCustomers;

