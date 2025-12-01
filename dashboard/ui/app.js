// dashboard/ui/app.js

function showPage(page) {
    document.querySelectorAll(".page").forEach(p => {
        p.classList.remove("active");
        p.style.display = "none";
    });
    const target = document.getElementById("page-" + page);
    if (target) {
        target.classList.add("active");
        target.style.display = "block";
    }
}

// Show logs page by default
showPage("logs");

/* -----------------------------------
   LIVE LOGS 
------------------------------------ */
setInterval(() => {
    fetch("/logs")
        .then(r => r.json())
        .then(data => {
            if (data.length > 0) {
                let out = document.getElementById("log-output");
                data.forEach(l => {
                    out.textContent += l + "\n";
                });
                out.scrollTop = out.scrollHeight;
            }
        })
        .catch(err => {
            // Silently fail if logs endpoint not available
        });
}, 1000);

/* -----------------------------------
   MODEL LIST + SWITCH
------------------------------------ */
function loadModels() {
    fetch("/models")
        .then(r => r.json())
        .then(models => {
            let sel = document.getElementById("model-list");
            sel.innerHTML = "";
            models.forEach(m => {
                let opt = document.createElement("option");
                opt.textContent = m;
                opt.value = m;
                sel.appendChild(opt);
            });
        })
        .catch(err => {
            console.error("Failed to load models:", err);
        });
}

function changeModel() {
    let model = document.getElementById("model-list").value;
    if (!model) {
        document.getElementById("model-status").textContent = "Please select a model";
        return;
    }
    fetch("/set_model", {
        method: "POST",
        body: JSON.stringify({ model: model }),
        headers: {"Content-Type": "application/json"}
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("model-status").textContent = 
            "Model changed to " + data.new_model;
    })
    .catch(err => {
        document.getElementById("model-status").textContent = "Error: " + err;
    });
}

/* -----------------------------------
   MEMORY VIEWER
------------------------------------ */
function loadMemory() {
    fetch("/memory")
        .then(r => r.json())
        .then(data => {
            document.getElementById("memory-json").value =
                JSON.stringify(data, null, 2);
        })
        .catch(err => {
            console.error("Failed to load memory:", err);
        });
}

function saveMemory() {
    try {
        let mem = JSON.parse(document.getElementById("memory-json").value);
        fetch("/memory", {
            method: "POST",
            body: JSON.stringify(mem),
            headers: {"Content-Type": "application/json"}
        })
        .then(res => res.json())
        .then(data => {
            alert("Memory saved!");
        })
        .catch(err => {
            alert("Error saving memory: " + err);
        });
    } catch (err) {
        alert("Invalid JSON: " + err);
    }
}

/* -----------------------------------
   PLUGINS
------------------------------------ */
function loadPlugins() {
    fetch("/plugins")
        .then(r => r.json())
        .then(data => {
            let div = document.getElementById("plugin-list");
            div.innerHTML = "";

            if (data.length === 0) {
                div.innerHTML = "<p>No plugins installed.</p>";
                return;
            }

            data.forEach(p => {
                div.innerHTML += `
                    <div class="plugin">
                        <b>${p.name}</b><br>
                        Folder: ${p.folder}<br>
                        Behavior: ${p.behavior || "None"}<br>
                        <button onclick="reloadPlugin('${p.name}')">Reload</button>
                    </div><br>
                `;
            });
        })
        .catch(err => {
            console.error("Failed to load plugins:", err);
        });
}

function reloadPlugin(name) {
    fetch("/plugins/reload", {
        method: "POST",
        body: JSON.stringify({name: name}),
        headers: {"Content-Type": "application/json"}
    })
    .then(res => res.json())
    .then(data => {
        alert("Plugin " + name + " reloaded!");
        loadPlugins();
    })
    .catch(err => {
        alert("Error reloading plugin: " + err);
    });
}

/* -----------------------------------
   AGENTS
------------------------------------ */
function loadAgents() {
    fetch("/agents")
        .then(r => r.json())
        .then(data => {
            let out = document.getElementById("agents-output");
            if (data.length === 0) {
                out.innerHTML = "<p>No active agents.</p>";
                return;
            }
            let html = "";
            data.forEach(a => {
                html += `<p><b>${a.name}</b> - Model: ${a.model}</p>`;
            });
            out.innerHTML = html;
        })
        .catch(err => {
            console.error("Failed to load agents:", err);
        });
}

function createAgent() {
    let name = document.getElementById("agent-name").value;
    let model = document.getElementById("agent-model").value;
    if (!name || !model) {
        alert("Please provide both name and model");
        return;
    }
    fetch("/agents/create", {
        method: "POST",
        body: JSON.stringify({name: name, model: model}),
        headers: {"Content-Type": "application/json"}
    })
    .then(res => res.json())
    .then(data => {
        alert("Agent created!");
        document.getElementById("agent-name").value = "";
        document.getElementById("agent-model").value = "";
        loadAgents();
    })
    .catch(err => {
        alert("Error creating agent: " + err);
    });
}

function killAgent() {
    let name = document.getElementById("kill-agent-name").value;
    if (!name) {
        alert("Please provide agent name");
        return;
    }
    fetch("/agents/kill", {
        method: "POST",
        body: JSON.stringify({name: name}),
        headers: {"Content-Type": "application/json"}
    })
    .then(res => res.json())
    .then(data => {
        alert("Agent killed!");
        document.getElementById("kill-agent-name").value = "";
        loadAgents();
    })
    .catch(err => {
        alert("Error killing agent: " + err);
    });
}

/* -----------------------------------
   VOICE
------------------------------------ */
function loadVoiceStatus() {
    fetch("/voice/status")
        .then(r => r.json())
        .then(data => {
            let status = document.getElementById("voice-status");
            status.textContent = `Status: ${data.enabled ? "Enabled" : "Disabled"} | Listening: ${data.listening ? "Yes" : "No"}`;
        })
        .catch(err => {
            console.error("Failed to load voice status:", err);
        });
}

function voiceOn() {
    fetch("/voice/enable", {method: "POST"})
        .then(res => res.json())
        .then(data => {
            alert("Voice enabled!");
            loadVoiceStatus();
        })
        .catch(err => {
            alert("Error: " + err);
        });
}

function voiceOff() {
    fetch("/voice/disable", {method: "POST"})
        .then(res => res.json())
        .then(data => {
            alert("Voice disabled!");
            loadVoiceStatus();
        })
        .catch(err => {
            alert("Error: " + err);
        });
}

// Auto-refresh voice status
setInterval(loadVoiceStatus, 2000);

/* initial calls */
loadModels();
loadMemory();
loadPlugins();
loadAgents();
loadVoiceStatus();
