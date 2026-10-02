const form = document.querySelector("#task-form");
const tasksList = document.querySelector("#tasks");
const message = document.querySelector("#message");
const titleInput = document.querySelector("#title");
const descriptionInput = document.querySelector("#description");
const cancelButton = document.querySelector("#cancel-button");
let editingTask = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Ошибка HTTP ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}

function showError(error) {
  message.textContent = error.message || "Не удалось выполнить запрос";
}

function resetForm() {
  editingTask = null;
  form.reset();
  document.querySelector("#form-heading").textContent = "Новая задача";
  document.querySelector("#submit-button").textContent = "Добавить";
  cancelButton.hidden = true;
}

function renderTask(task) {
  const item = document.createElement("li");
  item.classList.toggle("done", task.done);

  const top = document.createElement("div");
  top.className = "task-top";
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = task.done;
  checkbox.setAttribute("aria-label", `Выполнена: ${task.title}`);
  checkbox.addEventListener("change", async () => {
    try {
      await api(`/api/tasks/${task.id}`, {
        method: "PUT",
        body: JSON.stringify({ ...task, done: checkbox.checked }),
      });
      await loadTasks();
    } catch (error) {
      checkbox.checked = task.done;
      showError(error);
    }
  });
  const title = document.createElement("span");
  title.className = "task-title";
  title.textContent = task.title;
  top.append(checkbox, title);
  item.append(top);

  if (task.description) {
    const description = document.createElement("p");
    description.className = "task-description";
    description.textContent = task.description;
    item.append(description);
  }

  const actions = document.createElement("div");
  actions.className = "task-actions";
  const edit = document.createElement("button");
  edit.className = "secondary";
  edit.textContent = "Изменить";
  edit.addEventListener("click", () => {
    editingTask = task;
    titleInput.value = task.title;
    descriptionInput.value = task.description;
    document.querySelector("#form-heading").textContent = "Изменить задачу";
    document.querySelector("#submit-button").textContent = "Сохранить";
    cancelButton.hidden = false;
    titleInput.focus();
  });
  const remove = document.createElement("button");
  remove.className = "secondary";
  remove.textContent = "Удалить";
  remove.addEventListener("click", async () => {
    if (!confirm(`Удалить задачу «${task.title}»?`)) return;
    try {
      await api(`/api/tasks/${task.id}`, { method: "DELETE" });
      if (editingTask?.id === task.id) resetForm();
      await loadTasks();
    } catch (error) {
      showError(error);
    }
  });
  actions.append(edit, remove);
  item.append(actions);
  return item;
}

async function loadTasks() {
  const tasks = await api("/api/tasks");
  tasksList.replaceChildren(...tasks.map(renderTask));
  message.textContent = tasks.length ? "" : "Задач пока нет.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const task = {
    title: titleInput.value,
    description: descriptionInput.value,
    done: editingTask?.done || false,
  };
  try {
    await api(editingTask ? `/api/tasks/${editingTask.id}` : "/api/tasks", {
      method: editingTask ? "PUT" : "POST",
      body: JSON.stringify(task),
    });
    resetForm();
    await loadTasks();
  } catch (error) {
    showError(error);
  }
});

cancelButton.addEventListener("click", resetForm);
loadTasks().catch(showError);
