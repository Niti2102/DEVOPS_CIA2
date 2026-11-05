import os

from flask import Flask, jsonify, request

app = Flask(__name__)
tasks = [
    {"id": 1, "title": "Learn Docker", "done": False},
    {"id": 2, "title": "Deploy to Azure", "done": False},
]


@app.get("/")
def home():
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Task Manager</title>
        <style>
          body { font-family: Arial, sans-serif; background: #eef4ff; margin: 0; }
          main { max-width: 620px; margin: 60px auto; padding: 28px; background: white;
                  border-radius: 12px; box-shadow: 0 4px 16px #0002; }
          h1 { color: #155e9b; }
          form { display: flex; gap: 8px; }
          input { flex: 1; padding: 10px; border: 1px solid #bbb; border-radius: 5px; }
          button { padding: 10px 14px; border: 0; border-radius: 5px;
                   background: #155e9b; color: white; cursor: pointer; }
          li { display: flex; align-items: center; gap: 10px; padding: 12px 0;
               border-bottom: 1px solid #ddd; }
          li span { flex: 1; }
          .done { text-decoration: line-through; color: #777; }
          .delete { background: #c0392b; }
        </style>
      </head>
      <body>
        <main>
          <h1>Task Manager</h1>
          <p>Add tasks and track your progress.</p>
          <form id="task-form">
            <input id="task-title" placeholder="Enter a task" required>
            <button type="submit">Add</button>
          </form>
          <ul id="task-list"></ul>
        </main>
        <script>
          const list = document.getElementById("task-list");
          async function loadTasks() {
            const response = await fetch("/api/tasks");
            const taskItems = await response.json();
            list.innerHTML = taskItems.map(task => `
              <li>
                <input type="checkbox" ${task.done ? "checked" : ""}
                       onchange="completeTask(${task.id}, this.checked)">
                <span class="${task.done ? "done" : ""}">${task.title}</span>
                <button class="delete" onclick="deleteTask(${task.id})">Delete</button>
              </li>`).join("");
          }
          async function completeTask(id, done) {
            await fetch("/api/tasks/" + id, {
              method: "PUT", headers: {"Content-Type": "application/json"},
              body: JSON.stringify({done})
            });
            loadTasks();
          }
          async function deleteTask(id) {
            await fetch("/api/tasks/" + id, {method: "DELETE"});
            loadTasks();
          }
          document.getElementById("task-form").onsubmit = async event => {
            event.preventDefault();
            const input = document.getElementById("task-title");
            await fetch("/api/tasks", {
              method: "POST", headers: {"Content-Type": "application/json"},
              body: JSON.stringify({title: input.value})
            });
            input.value = "";
            loadTasks();
          };
          loadTasks();
        </script>
      </body>
    </html>
    """


@app.get("/health")
def health():
    return jsonify(status="UP", service="cicd-demo")


@app.get("/api/tasks")
def get_tasks():
    return jsonify(tasks)


@app.post("/api/tasks")
def add_task():
    title = request.json.get("title", "").strip()
    if not title:
        return jsonify(error="Task title is required"), 400
    task = {"id": max([task["id"] for task in tasks], default=0) + 1,
            "title": title, "done": False}
    tasks.append(task)
    return jsonify(task), 201


@app.put("/api/tasks/<int:task_id>")
def update_task(task_id):
    task = next((item for item in tasks if item["id"] == task_id), None)
    if task is None:
        return jsonify(error="Task not found"), 404
    task["done"] = bool(request.json.get("done", False))
    return jsonify(task)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    task = next((item for item in tasks if item["id"] == task_id), None)
    if task is None:
        return jsonify(error="Task not found"), 404
    tasks.remove(task)
    return "", 204


@app.get("/api/version")
def version():
    return jsonify({
        "app": "cicd-demo",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "message": "Simple task manager deployed to Azure"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8081")))
