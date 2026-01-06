import React, { useState, useEffect } from "react";

export default function JoinGroup({ userId, onCancel }) {
  const [allGroups, setAllGroups] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);

  // -----------------------------
  // Fetch all groups from backend
  // -----------------------------
  useEffect(() => {
    async function fetchGroups() {
      const token = localStorage.getItem("access_token");
      if (!token) {
        alert("You must be logged in to view groups.");
        return;
      }

      setLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/groups", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to fetch groups");

        setAllGroups(data);
      } catch (err) {
        console.error("❌ Failed to fetch groups:", err);
        alert("Error fetching groups: " + err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchGroups();
  }, []);

  // -----------------------------
  // Filter groups by name or number
  // -----------------------------
  const filteredGroups = allGroups.filter(
    (group) =>
      group.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (group.groupNumber &&
        group.groupNumber.toString().includes(searchTerm.trim()))
  );

  // -----------------------------
  // Handle joining a group
  // -----------------------------
  const handleJoin = async (group) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("You must be logged in to join a group.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/groups/join", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_id: userId, group_id: group.id }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to join group");

      // Update UI after joining
      setAllGroups((prev) =>
        prev.map((g) =>
          g.id === group.id
            ? {
                ...g,
                members: [...g.members, userId],
                memberCount: (g.memberCount || g.members.length) + 1,
              }
            : g
        )
      );

      alert(`✅ Joined group: ${data.group.name}`);
    } catch (err) {
      console.error("❌ Error joining group:", err);
      alert("Error joining group: " + err.message);
    }
  };

  // -----------------------------
  // Render UI
  // -----------------------------
  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4 text-center">Join a Group</h2>

      {/* Search bar */}
      <div className="group-search mb-4">
        <input
          type="text"
          placeholder="Search by name or #"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-2 border rounded-md"
        />
      </div>

      {/* Groups Table */}
      {loading ? (
        <div className="text-center p-4 text-gray-500">Loading groups...</div>
      ) : (
        <table className="join-group-table w-full border-collapse">
          <thead>
            <tr className="border-b bg-gray-100">
              <th className="text-left p-2">Group Name</th>
              <th className="text-left p-2">Members</th>
              <th className="text-left p-2">#Number</th>
              <th className="text-left p-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredGroups.length > 0 ? (
              filteredGroups.map((group) => {
                const isMember =
                  group.members.includes(userId) ||
                  group.members.includes(String(userId));

                return (
                  <tr key={group.id} className="border-b hover:bg-gray-50">
                    <td className="p-2">{group.name}</td>
                    <td className="p-2">
                      {group.memberCount ?? group.members.length}
                    </td>
                    <td className="p-2">
                      {group.groupNumber || group.inviteLink || "-"}
                    </td>
                    <td className="p-2">
                      <button
                        className={`px-3 py-1 rounded text-white transition ${
                          isMember
                            ? "bg-gray-400 cursor-not-allowed"
                            : "bg-blue-500 hover:bg-blue-600"
                        }`}
                        onClick={() => !isMember && handleJoin(group)}
                        disabled={isMember}
                      >
                        {isMember ? "Joined" : "Join"}
                      </button>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="4" className="text-center p-4 text-gray-500">
                  No groups found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {/* Cancel Button */}
      <div className="form-buttons mt-4">
        <button
          type="button"
          className="w-full p-2 bg-gray-300 rounded hover:bg-gray-400 transition"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
