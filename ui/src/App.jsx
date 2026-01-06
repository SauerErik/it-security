import React, { useState, useEffect, useMemo } from "react";
import { DragDropContext, Droppable } from "react-beautiful-dnd";
import TaskCard from "./components/TaskCard.jsx";
import Task from "./components/Task.jsx";

import CreateTask from "./create/create_task.jsx";
import CreateGroup from "./create/create_group.jsx";
import JoinGroup from "./create/join_group.jsx";
import Profile from "./profile.jsx";

export default function App() {
  const userId = 1;
  const columnNames = { todo: "To Do", inProgress: "In Progress", done: "Done" };
  const columnKeys = useMemo(() => ["todo", "inProgress", "done"], []);

  const [columns, setColumns] = useState({ todo: [], inProgress: [], done: [] });
  const [selectedTask, setSelectedTask] = useState(null);
  const [showForm, setShowForm] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  // -----------------------------
  // Fetch tasks
  // -----------------------------
  const fetchTasks = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/tasks/user/${userId}`);
      const data = await res.json();
      const newColumns = { todo: [], inProgress: [], done: [] };
      data.forEach(task => {
        const status = task.status && newColumns[task.status] ? task.status : "todo";
        newColumns[status].push({ ...task, id: String(task.id) });
      });
      setColumns(newColumns);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
      setColumns({ todo: [], inProgress: [], done: [] });
      setLoading(false);
    }
  };

  // -----------------------------
  // Fetch groups
  // -----------------------------
  const fetchGroups = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/groups/user/${userId}`);
      const data = await res.json();
      setGroups(data);
    } catch (err) {
      console.error("Failed to fetch groups:", err);
    }
  };

  useEffect(() => {
    fetchTasks();
    fetchGroups();
  }, [userId]);

  // -----------------------------
  // Add task
  // -----------------------------
  const handleAddTask = async (newTask) => {
    try {
      const res = await fetch(`http://localhost:8000/api/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...newTask, user_id: userId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to create task");
      const task = { ...data.task, id: String(data.task.id) };
      setColumns(prev => ({
        ...prev,
        [task.status || "todo"]: [...prev[task.status || "todo"], task],
      }));
      setShowForm(null);
    } catch (err) {
      alert("Error creating task: " + err.message);
    }
  };

  // -----------------------------
  // Update task
  // -----------------------------
  const handleUpdateTask = async (updatedTask) => {
    try {
      const res = await fetch(`http://localhost:8000/api/tasks/${updatedTask.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedTask),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to update task");
      const task = { ...data.task, id: String(data.task.id) };
      setColumns(prev => {
        const newCols = { ...prev };
        Object.keys(newCols).forEach(col => {
          newCols[col] = newCols[col].filter(t => t.id !== task.id);
        });
        newCols[task.status || "todo"].push(task);
        return newCols;
      });
      setSelectedTask(null);
    } catch (err) {
      alert("Error updating task: " + err.message);
    }
  };

  // -----------------------------
  // Join group
  // -----------------------------
  const handleJoinGroup = async (groupId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/groups/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, group_id: groupId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to join group");
      fetchTasks();
      setShowForm(null);
    } catch (err) {
      alert("Error joining group: " + err.message);
    }
  };

  // -----------------------------
  // Drag & Drop
  // -----------------------------
  const onDragEnd = async (result) => {
    const { source, destination, draggableId } = result;
    if (!destination) return;
    if (source.droppableId === destination.droppableId && source.index === destination.index) return;

    const sourceTasks = Array.from(columns[source.droppableId]);
    const destTasks = Array.from(columns[destination.droppableId]);
    const [movedTask] = sourceTasks.splice(source.index, 1);
    movedTask.status = destination.droppableId;
    destTasks.splice(destination.index, 0, movedTask);

    const newColumns = {
      ...columns,
      [source.droppableId]: sourceTasks,
      [destination.droppableId]: destTasks,
    };

    setColumns(newColumns);

    try {
      await fetch(`http://localhost:8000/api/tasks/${draggableId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: destination.droppableId }),
      });
    } catch (err) {
      console.error("Failed to update task:", err);
      fetchTasks();
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="app-container">
      <div className="top-right-buttons">
        <button className="btn-primary" onClick={() => setShowProfile(true)}>Profile</button>
        <button className="btn-cancel" onClick={() => alert("Logged out!")}>Logout</button>
      </div>

      <h1 className="title-with-icon">
        <img src="/assets/StudyConnectLogo.png" alt="logo" className="title-icon" />
        StudyConnect
      </h1>

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="kanban-board">
          {columnKeys.map(colId => (
            <Droppable droppableId={colId} key={colId}>
              {(provided, snapshot) => (
                <div
                  className={`kanban-column ${snapshot.isDraggingOver ? "bg-indigo-100" : ""}`}
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                >
                  <h3 className="kanban-column-header">{columnNames[colId]}</h3>
                  {columns[colId].map((task, index) => (
                    <TaskCard key={task.id} task={task} index={index} onClick={setSelectedTask} />
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          ))}
        </div>
      </DragDropContext>

      <div className="button-container">
        <button className="btn-primary" onClick={() => setShowForm("task")}>Create Task</button>
        <button className="btn-primary" onClick={() => setShowForm("join")}>Join a Group</button>
        <button className="btn-primary" onClick={() => setShowForm("group")}>Create a Group</button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal-content">
            {showForm === "task" && <CreateTask userId={userId} onCancel={() => setShowForm(null)} onAddTask={handleAddTask} />}
            {showForm === "group" && <CreateGroup onCancel={() => setShowForm(null)} />}
            {showForm === "join" && <JoinGroup userId={userId} groups={groups} onCancel={() => setShowForm(null)} onJoinGroup={handleJoinGroup} />}
          </div>
        </div>
      )}

      {showProfile && (
        <div className="modal-overlay">
          <div className="modal-content">
            <Profile userId={userId} onClose={() => setShowProfile(false)} />
          </div>
        </div>
      )}

      {selectedTask && (
        <Task task={selectedTask} onSave={handleUpdateTask} onCancel={() => setSelectedTask(null)} />
      )}
    </div>
  );
}
