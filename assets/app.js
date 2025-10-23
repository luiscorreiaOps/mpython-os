const fileList = document.getElementById('file-list');
const fileManagerTitle = document.getElementById('file-manager-title');
const currentPathElement = document.getElementById('current-path');
const editor = document.getElementById('editor');
const fileContent = document.getElementById('file-content');
const editorFilename = document.getElementById('editor-filename');
const termOutput = document.getElementById('terminal-output');
const termInput = document.getElementById('terminal-input');
const termPrompt = document.getElementById('terminal-prompt');
const newFilenameInput = document.getElementById('new-filename');
const wifiSsidInput = document.getElementById('wifi-ssid');
const wifiPasswordInput = document.getElementById('wifi-password');

let currentEditingFile = '';
let currentPath = '';
let pathHistory = [''];

function isFolder(name) {
    return !name.includes('.') || name === 'assets' || name === 'modules';
}

async function loadFiles(path = '') {
    try {
        currentPath = path;
        currentPathElement.textContent = path ? '/' + path : '/';
        
        const apiUrl = path ? '/api/files?path=' + encodeURIComponent(path) : '/api/files';
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error('HTTP ' + response.status);
        }
        
        const data = await response.json();
        
        fileManagerTitle.textContent = 'Gerenciador de Arquivos [' + data.path + ']';
        fileList.innerHTML = '';
        
        if (data.files && data.files.length > 0) {
            data.files.forEach(function(file) {
                const li = document.createElement('li');
                
                if (isFolder(file)) {
                    li.className = 'folder';
                    
                    const span = document.createElement('span');
                    span.textContent = '📁 ' + file;

                    const div = document.createElement('div');

                    const openButton = document.createElement('button');
                    openButton.textContent = 'Abrir';
                    openButton.addEventListener('click', function() {
                        enterFolder(file);
                    });

                    div.appendChild(openButton);

                    li.appendChild(span);
                    li.appendChild(div);
                } else {
                    li.className = 'file';

                    const span = document.createElement('span');
                    span.textContent = '📄 ' + file;

                    const div = document.createElement('div');

                    const editButton = document.createElement('button');
                    editButton.textContent = 'Editar';
                    editButton.addEventListener('click', function() {
                        editFile(file);
                    });

                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = 'Deletar';
                    deleteButton.addEventListener('click', function() {
                        deleteFile(file);
                    });

                    div.appendChild(editButton);
                    div.appendChild(deleteButton);

                    li.appendChild(span);
                    li.appendChild(div);
                }
                
                fileList.appendChild(li);
            });
        } else {
            fileList.innerHTML = '<li>Pasta vazia</li>';
        }
    } catch(e) { 
        console.error('Falha ao carregar arquivos:', e);
        fileList.innerHTML = '<li class="error">Erro ao carregar: ' + e.message + '</li>';
    }
}

function enterFolder(folderName) {
    const newPath = currentPath ? currentPath + '/' + folderName : folderName;
    pathHistory.push(newPath);
    loadFiles(newPath);
}

function goUp() {
    if (pathHistory.length > 1) {
        pathHistory.pop();
        const previousPath = pathHistory[pathHistory.length - 1];
        loadFiles(previousPath);
    } else {
        loadFiles('');
    }
}

async function editFile(filename) {
    if (!filename) { 
        alert('Nome do arquivo não pode ser vazio.'); 
        return; 
    }
    
    const fullPath = currentPath ? currentPath + '/' + filename : filename;
    
    try {
        const response = await fetch('/api/read?file=' + encodeURIComponent(fullPath));
        if (!response.ok) {
            if (response.status === 404) {
                currentEditingFile = fullPath;
                editorFilename.textContent = 'Editar: ' + fullPath;
                fileContent.value = '';
                editor.style.display = 'block';
                document.getElementById('file-manager').style.display = 'none';
                document.body.classList.add('input-active');
                fileContent.focus();
                return;
            }
            throw new Error('HTTP ' + response.status);
        }
        
        const data = await response.json();
        currentEditingFile = fullPath;
        editorFilename.textContent = 'Editar: ' + fullPath;
        fileContent.value = data.content || '';
        editor.style.display = 'block';
        document.getElementById('file-manager').style.display = 'none';
        document.body.classList.add('input-active');
        fileContent.focus();
        
    } catch(e) { 
        console.error('Falha ao ler arquivo:', e);
        alert('Erro ao ler arquivo: ' + e.message);
    }
}

function createFile() {
    const filename = newFilenameInput.value;
    if (!filename) {
        alert('Nome do arquivo não pode ser vazio.');
        newFilenameInput.focus();
        return;
    }
    editFile(filename);
}

async function deleteFile(filename) {
    const fullPath = currentPath ? currentPath + '/' + filename : filename;
    
    if (confirm('Tem certeza que deseja deletar ' + fullPath + '?')) {
        try {
            const response = await fetch('/api/delete?file=' + encodeURIComponent(fullPath));
            
            if (response.ok) {
                loadFiles(currentPath);
            } else {
                alert('Erro ao deletar arquivo.');
            }
        } catch(e) {
            console.error('Falha ao deletar:', e);
            alert('Erro ao deletar: ' + e.message);
        }
    }
}

async function saveFile() {
    try {
        const response = await fetch('/api/write', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ 
                filename: currentEditingFile, 
                content: fileContent.value 
            }) 
        });
        
        if (response.ok) {
            alert('Arquivo salvo!');
            closeEditor();
            loadFiles(currentPath);
        } else { 
            alert('Erro ao salvar arquivo.'); 
        }
    } catch(e) { 
        console.error('Falha ao salvar:', e);
        alert('Erro ao salvar: ' + e.message);
    }
}

function closeEditor() {
    editor.style.display = 'none';
    newFilenameInput.value = '';
    document.getElementById('file-manager').style.display = 'block';
    document.body.classList.remove('input-active');
    
    setTimeout(function() {
        termInput.focus();
    }, 100);
}

async function loadMotd() {
    try {
        const response = await fetch('/api/motd');
        if (response.ok) {
            const data = await response.json();
            const motdDiv = document.createElement('div');
            motdDiv.innerHTML = data.motd.replace(/\n/g, '<br>');
            termOutput.appendChild(motdDiv);
        }
    } catch(e) { 
        console.error('Falha ao carregar MOTD:', e); 
        termOutput.innerHTML += '<div>Falha ao carregar mensagem inicial.</div>'; 
    }
    
    setTimeout(function() {
        termInput.focus();
    }, 500);
}

termInput.addEventListener('keydown', async function(event) {
    if (event.key === 'Enter' && termInput.value.trim() !== '') {
        const command = termInput.value;
        
        const commandDiv = document.createElement('div');
        commandDiv.innerHTML = '<span class="prompt">' + termPrompt.textContent + '</span>' + command;
        termOutput.appendChild(commandDiv);
        
        termInput.value = '';
        
        try {
            const response = await fetch('/api/exec', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ command: command }) 
            });
            
            if (response.ok) {
                const data = await response.json();
                const outputDiv = document.createElement('div');
                outputDiv.textContent = data.output;
                termOutput.appendChild(outputDiv);
            } else { 
                const errorDiv = document.createElement('div');
                errorDiv.textContent = 'Erro na comunicacao com o dispositivo.';
                errorDiv.style.color = 'red';
                termOutput.appendChild(errorDiv);
            }
        } catch(e) { 
            console.error('Falha ao executar comando:', e);
            const errorDiv = document.createElement('div');
            errorDiv.textContent = 'Erro: ' + e.message;
            errorDiv.style.color = 'red';
            termOutput.appendChild(errorDiv);
        }
        
        termOutput.scrollTop = termOutput.scrollHeight;
        termInput.focus();
    }
});

function setupInputFocus(inputElement) {
    inputElement.addEventListener('focus', function() {
        document.body.classList.add('input-active');
    });

    inputElement.addEventListener('blur', function() {
        setTimeout(function() {
            const focusedElement = document.activeElement;
            const isAnotherInput = focusedElement === newFilenameInput || 
                                  focusedElement === wifiSsidInput || 
                                  focusedElement === wifiPasswordInput || 
                                  focusedElement === fileContent;
            
            if (!isAnotherInput) {
                document.body.classList.remove('input-active');
            }
        }, 10);
    });
}

setupInputFocus(newFilenameInput);
setupInputFocus(wifiSsidInput);
setupInputFocus(wifiPasswordInput);
setupInputFocus(fileContent);

document.addEventListener('click', function(event) {
    const clickedElement = event.target;
    const isInput = clickedElement.tagName === 'INPUT' || 
                   clickedElement.tagName === 'TEXTAREA';
    
    if (!isInput && !(editor.style.display === 'block')) {
        document.body.classList.remove('input-active');
        termInput.focus();
    }
});

newFilenameInput.addEventListener('click', function(event) {
    event.stopPropagation();
    newFilenameInput.focus();
});

wifiSsidInput.addEventListener('click', function(event) {
    event.stopPropagation();
    wifiSsidInput.focus();
});

wifiPasswordInput.addEventListener('click', function(event) {
    event.stopPropagation();
    wifiPasswordInput.focus();
});

async function saveWifi() {
    const ssid = wifiSsidInput.value;
    const password = wifiPasswordInput.value;

    if (!ssid) {
        alert('O nome da rede (SSID) e obrigatorio.');
        wifiSsidInput.focus();
        return;
    }

    const confirmation = confirm(
        'ATENÇÃO:\n\n' +
        'O dispositivo ira salvar a nova rede e reiniciar.\n' +
        'Voce perdera a conexão com esta página e precisara encontrar o novo endereço IP do dispositivo na sua rede Wifi.\n\n' +
        'Deseja continuar?'
    );

    if (confirmation) {
        try {
            await fetch('/api/setwifi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: ssid, password: password })
            });
            alert('Configuracao enviada. O dispositivo esta reiniciando...');
        } catch (e) {
            alert('Erro ao enviar configuracao. Tente novamente.');
        }
    }
}

loadFiles('');
loadMotd();