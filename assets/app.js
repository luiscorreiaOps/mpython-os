var curPath = "";
var curFile = "";
var chartD = [];
var monInt = null;
var cmdHis = [];
var hisIdx = -1;

for (var k = 0; k < 50; k++) { chartD.push(0); }

window.onload = function() {
    setupEvents();
    loadFiles("");
    loadMotd();
    loadCron();
    loadWifiStatus();
};

function setupEvents() {
    document.getElementById("btn-up").onclick = goUp;
    document.getElementById("btn-upload-trigger").onclick = function() { document.getElementById("file-upload").click(); };
    document.getElementById("file-upload").onchange = function() { uploadFile(this); };
    document.getElementById("btn-create").onclick = createFile;
    document.getElementById("btn-save").onclick = saveFile;
    document.getElementById("btn-close").onclick = closeEditor;
    document.getElementById("btn-cron-add").onclick = addCron;
    document.getElementById("btn-monitor").onclick = toggleMon;
    document.getElementById("btn-wifi-save").onclick = saveWifi;
    document.getElementById("terminal-input").onkeydown = function(e) { 
        if (e.key === "Enter") {
            handleTerminal(this);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            if (cmdHis.length > 0) {
                if (hisIdx === -1) hisIdx = cmdHis.length;
                if (hisIdx > 0) { hisIdx--; this.value = cmdHis[hisIdx]; }
            }
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            if (hisIdx !== -1) {
                if (hisIdx < cmdHis.length - 1) { hisIdx++; this.value = cmdHis[hisIdx]; }
                else { hisIdx = -1; this.value = ""; }
            }
        }
    };
}

function loadWifiStatus() {
    fetch("/api/wifi/status").then(function(r) { return r.json(); }).then(function(d) {
        var el = document.getElementById("wifi-status");
        if (d.ssid) { el.textContent = d.mode + ": " + d.ssid; }
        else { el.textContent = d.mode; }
    }).catch(function() { document.getElementById("wifi-status").textContent = "Erro status."; });
}

function loadFiles(p) {
    curPath = p || "";
    var displayPath = curPath;
    if (displayPath.indexOf("/") !== 0) { displayPath = "/" + displayPath; }
    document.getElementById("current-path").textContent = displayPath;
    var u = "/api/files" + (curPath ? "?path=" + encodeURIComponent(curPath) : "");
    fetch(u).then(function(r) { return r.json(); }).then(function(d) {
        var l = document.getElementById("file-list");
        l.innerHTML = "";
        if (d.files) {
            for (var i = 0; i < d.files.length; i++) {
                var f = d.files[i];
                var isDir = f.indexOf(".") === -1 || f === "assets" || f === "modules";
                var li = document.createElement("li");
                li.className = "file-item";
                var s = document.createElement("span");
                s.textContent = f;
                li.appendChild(s);
                var div = document.createElement("div");
                if (isDir) {
                    var b = document.createElement("button"); b.textContent = "Abrir";
                    b.onclick = (function(n) { return function() { enterFolder(n); }; })(f);
                    div.appendChild(b);
                    
                    var bd = document.createElement("button"); bd.textContent = "X";
                    bd.style.background = "#111"; // Cinza escuro
                    bd.style.marginLeft = "5px";
                    bd.onclick = (function(n) { return function() { deleteFile(n); }; })(f);
                    div.appendChild(bd);
                } else {
                    var be = document.createElement("button"); be.textContent = "Edit";
                    be.onclick = (function(n) { return function() { editFile(n); }; })(f);
                    div.appendChild(be);
                    var bd = document.createElement("button"); bd.textContent = "X";
                    bd.style.background = "#111"; // Cinza escuro
                    bd.style.marginLeft = "5px";
                    bd.onclick = (function(n) { return function() { deleteFile(n); }; })(f);
                    div.appendChild(bd);
                }
                li.appendChild(div);
                l.appendChild(li);
            }
        }
    });
}

function enterFolder(n) { curPath = curPath ? curPath + "/" + n : n; loadFiles(curPath); }

function goUp() {
    if (!curPath) return;
    var parts = curPath.split("/"); parts.pop();
    loadFiles(parts.join("/"));
}

function editFile(n) {
    var p = curPath ? curPath + "/" + n : n;
    fetch("/api/read?file=" + encodeURIComponent(p)).then(function(r) { return r.json(); }).then(function(d) {
        curFile = p;
        document.getElementById("editor-title").textContent = p;
        document.getElementById("file-cont").value = d.content || "";
        document.getElementById("editor").style.display = "block";
        document.getElementById("file-manager").style.display = "none";
    });
}

function saveFile() {
    var c = document.getElementById("file-cont").value;
    fetch("/api/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: curFile, content: c })
    }).then(function() { alert("Salvo"); closeEditor(); });
}

function closeEditor() {
    document.getElementById("editor").style.display = "none";
    document.getElementById("file-manager").style.display = "block";
    loadFiles(curPath);
}

function deleteFile(n) {
    if (confirm("Apagar?")) {
        var p = curPath ? curPath + "/" + n : n;
        fetch("/api/delete?file=" + encodeURIComponent(p)).then(function() { loadFiles(curPath); });
    }
}

function createFile() {
    var n = document.getElementById("new-name").value;
    if (n) editFile(n);
}

function uploadFile(i) {
    var f = i.files[0]; if (!f) return;
    var p = curPath ? curPath + "/" + f.name : f.name;
    var url = "/api/upload?file=" + encodeURIComponent(p);
    fetch(url, { method: "POST", body: f }).then(function(r) {
        if (r.ok) { alert("Upload OK"); loadFiles(curPath); }
        else { alert("Erro upload"); }
    }).catch(function(e) { alert("Erro: " + e.message); });
}

function loadMotd() {
    fetch("/api/motd").then(function(r) { return r.json(); }).then(function(d) {
        var o = document.getElementById("terminal-output");
        var div = document.createElement("div");
        div.innerHTML = d.motd.replace(/\n/g, "<br>");
        o.appendChild(div);
        o.scrollTop = o.scrollHeight;
    });
}

function logTerm(m) {
    var o = document.getElementById("terminal-output");
    var d = document.createElement("div");
    d.innerHTML = m.replace(/\n/g, "<br>");
    o.appendChild(d);
    o.scrollTop = o.scrollHeight;
}

function handleTerminal(inp) {
    var c = inp.value; if (!c) return;
    cmdHis.push(c); if (cmdHis.length > 50) cmdHis.shift();
    hisIdx = -1; inp.value = "";
    if (c === "clear") { document.getElementById("terminal-output").innerHTML = ""; loadMotd(); return; }
    logTerm("<span style='color:#0f0'>/> " + c + "</span>");
    fetch("/api/exec", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: c })
    }).then(function(r) { return r.json(); }).then(function(d) {
        logTerm(d.output);
        if (c.indexOf("cd ") === 0) loadFiles(curPath);
    }).catch(function(e) { logTerm("Erro: " + e.message); });
}

function toggleMon() {
    var b = document.getElementById("btn-monitor");
    if (monInt) { clearInterval(monInt); monInt = null; b.textContent = "Iniciar"; }
    else { monInt = setInterval(updateChart, 1000); b.textContent = "Parar"; }
}

function updateChart() {
    var p = document.getElementById("adc-pin-select").value;
    fetch("/api/gpio/" + p).then(function(r) { return r.json(); }).then(function(d) {
        var v = d.analog || 0;
        document.getElementById("sensor-val").textContent = v;
        chartD.push(v); chartD.shift(); drawChart();
    });
}

function drawChart() {
    var c = document.getElementById("sensorChart"); if (!c) return;
    var ctx = c.getContext("2d");
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.strokeStyle = "#0f0"; ctx.beginPath();
    var s = c.width / 49;
    for (var i = 0; i < 50; i++) {
        var y = c.height - (chartD[i] / 4095 * c.height);
        if (i === 0) ctx.moveTo(0, y); else ctx.lineTo(i * s, y);
    }
    ctx.stroke();
}

function loadCron() {
    fetch("/api/cron/list").then(function(r) { return r.json(); }).then(function(d) {
        var b = document.getElementById("cron-tbody"); b.innerHTML = "";
        if (d.tasks) {
            for (var i = 0; i < d.tasks.length; i++) {
                var t = d.tasks[i];
                var tr = document.createElement("tr");
                tr.innerHTML = "<td>" + t.interval + "s</td><td>" + t.command + "</td>";
                var td = document.createElement("td");
                var btn = document.createElement("button"); btn.textContent = "X"; btn.className = "btn-red";
                btn.onclick = (function(id) { return function() { fetch("/api/cron/delete?id=" + id).then(loadCron); }; })(t.id);
                td.appendChild(btn); tr.appendChild(td); b.appendChild(tr);
            }
        }
    });
}

function addCron() {
    var i = document.getElementById("cron-int").value;
    var c = document.getElementById("cron-cmd").value;
    if (!i || !c) return;
    fetch("/api/cron/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval: parseInt(i), command: c })
    }).then(loadCron);
}

function saveWifi() {
    var s = document.getElementById("wifi-ssid").value;
    var p = document.getElementById("wifi-pass").value;
    fetch("/api/setwifi", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ssid: s, password: p })
    }).then(function() { alert("OK! Reiniciando..."); });
}
