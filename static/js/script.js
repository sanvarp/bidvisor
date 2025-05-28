document.addEventListener('DOMContentLoaded', function () {
    loadSessions();
    document.getElementById('newSessionButton').addEventListener('click', createNewSession);
    document.getElementById('createSessionFromEmpty').addEventListener('click', createNewSession);

    // ELEMENTOS DE CARGA DE ARCHIVOS Y PROCESAMIENTO
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const processButton = document.getElementById('processButton');
    const processStatus = document.getElementById('processStatus');

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.backgroundColor = "#e9ecef";
    });
    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.style.backgroundColor = "";
    });
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.backgroundColor = "";
        handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
    });

    function handleFiles(files) {
        if (!window.currentSessionId) {
            alert("No hay sesión activa. Por favor, crea o selecciona una sesión.");
            return;
        }
    
        const fileListElem = document.getElementById('fileList');
        fileListElem.innerHTML = ""; // Limpiar la lista
    
        const validFiles = [];
        const rejectedFiles = [];
    
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const ext = file.name.split('.').pop().toLowerCase();
    
            if (ext === 'xls' || ext === 'xlsx') {
                rejectedFiles.push(file.name);
            } else {
                validFiles.push(file);
                const li = document.createElement('li');
                li.textContent = file.name;
                fileListElem.appendChild(li);
            }
        }
    
        // ✅ Mostrar modal si hay rechazados, sin importar si hay válidos o no
        if (rejectedFiles.length > 0) {
            const modalBody = document.getElementById('rejectedFilesModalBody');
            modalBody.innerHTML = `
                <p>Los siguientes archivos fueron rechazados por tener un formato no permitido:</p>
                <ul>
                    ${rejectedFiles.map(file => `<li>${file}</li>`).join('')}
                </ul>
                <p class="mt-2 mb-0">Solo se permiten archivos <strong>PDF</strong>, <strong>DOCX</strong> y <strong>TXT</strong>.</p>
            `;
            const modal = new bootstrap.Modal(document.getElementById('rejectedFilesModal'));
            modal.show();
        }
    
        // ❌ Si no hay válidos, NO subir nada
        if (validFiles.length === 0) return;
    
        const formData = new FormData();
        validFiles.forEach(file => {
            formData.append('files[]', file);
        });
    
        fetch(`/upload?session_id=${window.currentSessionId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            fileListElem.innerHTML = "";
            data.files.forEach(filename => {
                const li = document.createElement('li');
                li.textContent = filename;
                fileListElem.appendChild(li);
            });
        })
        .catch(err => console.error(err));
        fileInput.value = "";
    }
    
    
    
    

    processButton.addEventListener('click', () => {
        processStatus.textContent = "";
    
        if (!window.currentSessionId) {
            processStatus.textContent = "No hay session_id activo. Crea o selecciona una sesión primero.";
            return;
        }
    
        const fileListElem = document.getElementById('fileList');
        const fileItems = fileListElem.querySelectorAll('li');
    
        if (fileItems.length === 0) {
            processStatus.textContent = "No hay archivos válidos cargados para procesar.";
            return;
        }
    
        processStatus.textContent = "Procesando documentos...";
    
        const eventSource = new EventSource(`/process/${window.currentSessionId}`);
        eventSource.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.section === 'status' && data.value === 'completed') {
                processStatus.textContent = "Procesamiento completado.";
                eventSource.close();
                loadSessionDetails(window.currentSessionId);
                return;
            }
            if (data.section === 'general') {
                const element = document.getElementById(data.field);
                if (element) {
                    element.innerHTML = marked.parse(data.value);
                    element.classList.remove('pending');
                }
            } else {
                const infoValue = document.querySelector(`#${data.section} .info-value`);
                if (infoValue) {
                    infoValue.innerHTML = marked.parse(data.value);
                    infoValue.classList.remove('pending');
                }
            }
        };
        eventSource.onerror = function (error) {
            console.error('Error en el EventSource:', error);
            processStatus.textContent = "Error en el procesamiento.";
            eventSource.close();
        };
    
        document.querySelectorAll('.info-value').forEach(el => {
            el.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Procesando...';
        });
    });
    

    // CHAT: Enviar mensaje
    const chatBox = document.getElementById('chatBox');
    const chatInput = document.getElementById('chatInput');
    const sendChat = document.getElementById('sendChat');

    function sendMessage() {
        const message = chatInput.value.trim();
        if (message === "") return;
    
        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('message', 'user-message');
        userMessageDiv.innerHTML = marked.parse(message);
        chatBox.appendChild(userMessageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        chatInput.value = "";
    
        // Mostrar animación "escribiendo..."
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.classList.add('message', 'assistant-message');
        typingDiv.innerHTML = `
            <div id="typingAnimation" style="width: 60px; height: 40px; margin-left: 10px;"></div>
        `;
        chatBox.appendChild(typingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    
        lottie.loadAnimation({
            container: document.getElementById('typingAnimation'),
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets6.lottiefiles.com/packages/lf20_usmfx6bp.json' // Animación de puntos
        });
    
        fetch(`/ask/${window.currentSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        })
            .then(response => response.json())
            .then(data => {
                typingDiv.remove();
    
                const botMessageDiv = document.createElement('div');
                botMessageDiv.classList.add('message', 'assistant-message');
                botMessageDiv.innerHTML = marked.parse(data.answer);
                chatBox.appendChild(botMessageDiv);
                chatBox.scrollTop = chatBox.scrollHeight;
            })
            .catch(err => {
                typingDiv.remove();
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('message', 'assistant-message');
                errorDiv.textContent = "Error al obtener respuesta del asistente.";
                chatBox.appendChild(errorDiv);
                chatBox.scrollTop = chatBox.scrollHeight;
            });
    }
    

    sendChat.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
    const chatBoxObserver = new MutationObserver(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    });
    chatBoxObserver.observe(chatBox, { childList: true, subtree: true });
    const fontAwesome = document.createElement('link');
    fontAwesome.rel = 'stylesheet';
    fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
    document.head.appendChild(fontAwesome);

    var modalEl = document.getElementById('createSessionModal');
    modalEl.addEventListener('hide.bs.modal', function () {
        if (document.activeElement && modalEl.contains(document.activeElement)) {
            document.activeElement.blur();
        }
    });
});

// Funciones globales

function loadSessionDetails(session_id) {
    // Llamada a /clear_folder para limpiar la carpeta del usuario
    fetch('/clear_folder', { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta de clear_folder:', data.message);
        })
        .catch(error => console.error('Error al limpiar la carpeta:', error));

    // Resto del código para cargar los detalles de la sesión
    document.getElementById('fileList').innerHTML = "";
    document.getElementById('dropzone').style.display = "block";
    document.getElementById('processButton').disabled = false;
    document.getElementById('processStatus').textContent = "";


    document.getElementById('infoGeneral').innerHTML = `
        <p><strong>Entidad contratante:</strong> <span id="entidad" class="info-value pending">Pendiente</span></p>
        <p><strong>Objeto de convocatoria:</strong> <span id="objeto" class="info-value pending">Pendiente</span></p>
        <p><strong>Presupuesto:</strong> <span id="presupuesto" class="info-value pending">Pendiente</span></p>`;
    document.getElementById('cronograma').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('presentacion').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('perfiles').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('evaluacion').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('chatBox').innerHTML = "";
    
    fetch(`/session/${session_id}/details`)
        .then(response => response.json())
        .then(data => {
            data.extracted_info.forEach(item => {
                if (item.section === "general") {
                    if (item.field === "contracting_entity" || item.field === "entidad") {
                        document.getElementById('entidad').innerHTML = marked.parse(item.value);
                    } else if (item.field === "objective" || item.field === "objeto") {
                        document.getElementById('objeto').innerHTML = marked.parse(item.value);
                    } else if (item.field === "budget" || item.field === "presupuesto") {
                        document.getElementById('presupuesto').innerHTML = marked.parse(item.value);
                    }
                } else if (item.section === "cronograma") {
                    document.getElementById('cronograma').innerHTML = marked.parse(item.value);
                } else if (item.section === "presentacion") {
                    document.getElementById('presentacion').innerHTML = marked.parse(item.value);
                } else if (item.section === "perfiles") {
                    document.getElementById('perfiles').innerHTML = marked.parse(item.value);
                } else if (item.section === "evaluacion") {
                    document.getElementById('evaluacion').innerHTML = marked.parse(item.value);
                }
            });
            if (data.files && data.files.length > 0) {
                const filesHTML = data.files.map(file => `<li>${file.filename}</li>`).join("");
                document.getElementById('fileList').innerHTML = filesHTML;
                document.getElementById('dropzone').style.display = "none";
                document.getElementById('processButton').disabled = true;
            }
            data.chat_messages.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.classList.add('message');
                if (msg.role === "user") {
                    msgDiv.classList.add('user-message');
                } else {
                    msgDiv.classList.add('assistant-message');
                }
                msgDiv.innerHTML = marked.parse(msg.content);
                document.getElementById('chatBox').appendChild(msgDiv);
            });
        })
        .catch(error => {
            console.error("Error al cargar los detalles de la sesión:", error);
        });
}

function loadSessions() {
    fetch('/sessions')
        .then(response => response.json())
        .then(sessions => {
            console.log("Sesiones cargadas:", sessions);
            sessions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            const sessionPanel = document.getElementById('sessionPanel');
            sessionPanel.innerHTML = "";
            if (sessions.length === 0) {
                sessionPanel.innerHTML = "<p>No hay sesiones. Crea una nueva.</p>";
                window.currentSessionId = null;
                updateMainContentVisibility(false);
            } else {
                updateMainContentVisibility(true);
                sessions.forEach(session => {
                    const sessionDiv = document.createElement('div');
                    sessionDiv.classList.add('session-item');
                    sessionDiv.innerHTML = `<div>
    <strong>${session.name ? session.name : session.session_id.substring(0, 8)}</strong><br>
    <small>${new Date(session.created_at).toLocaleString()}</small>
  </div>`;
                    const deleteBtn = document.createElement('button');
                    deleteBtn.classList.add('session-delete');
                    deleteBtn.innerHTML = '&times;';
                    deleteBtn.onclick = (e) => {
                        e.stopPropagation();
                        deleteSession(session.session_id);
                    };
                    sessionDiv.appendChild(deleteBtn);
                    sessionDiv.onclick = () => {
                        window.currentSessionId = session.session_id;
                        document.querySelectorAll(".session-item").forEach(el => el.classList.remove("active"));
                        sessionDiv.classList.add("active");
                        loadSessionDetails(session.session_id);
                    };
                    if (session.session_id === window.currentSessionId) {
                        sessionDiv.classList.add("active");
                        loadSessionDetails(session.session_id);
                    }
                    sessionPanel.appendChild(sessionDiv);
                });

                if (!window.currentSessionId && sessions.length > 0) {
                    window.currentSessionId = sessions[0].session_id;
                    sessionPanel.firstChild.classList.add("active");
                    loadSessionDetails(window.currentSessionId);
                }
            }
        })
        .catch(err => {
            console.error("Error al cargar sesiones:", err);
            document.getElementById('sessionPanel').innerHTML = "<p>Error al cargar las sesiones.</p>";
        });
}

function createNewSession() {
    const createSessionModal = new bootstrap.Modal(document.getElementById('createSessionModal'));
    createSessionModal.show();

    document.getElementById('saveSessionButton').onclick = () => {
        const sessionName = document.getElementById('sessionNameInput').value.trim();
        if (!sessionName) return;
        document.getElementById('sessionNameInput').value = "";
        fetch('/session/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: sessionName })
        })
            .then(response => response.json())
            .then(data => {
                window.currentSessionId = data.session_id;
                loadSessions();
                createSessionModal.hide();
            })
            .catch(err => {
                console.error("Error al crear sesión:", err);
                createSessionModal.hide();
            });
    };
}

function deleteSession(session_id) {
    if (!confirm("¿Está seguro de eliminar esta sesión?")) return;
    fetch(`/session/${session_id}`, { method: 'DELETE' })
        .then(response => {
            if (response.ok) {
                if (session_id === window.currentSessionId) {
                    window.currentSessionId = null;
                    document.getElementById('infoGeneral').innerHTML = "";
                    document.getElementById('cronograma').innerHTML = "";
                    document.getElementById('presentacion').innerHTML = "";
                    document.getElementById('perfiles').innerHTML = "";
                    document.getElementById('evaluacion').innerHTML = "";
                    document.getElementById('fileList').innerHTML = "";
                    document.getElementById('chatBox').innerHTML = "";
                    document.getElementById('dropzone').style.display = "block";
                    document.getElementById('processButton').disabled = false;
                }
                loadSessions();
            } else {
                console.error("Error al eliminar la sesión");
            }
        })
        .catch(err => console.error("Error al eliminar la sesión:", err));
}

function updateMainContentVisibility(hasSession) {
    const mainContentColumn = document.getElementById('mainContentColumn');
    if (hasSession) {
        document.getElementById('mainContent').classList.remove('d-none');
        document.getElementById('emptyState').classList.add('d-none');
        document.getElementById('chatColumn').classList.remove('d-none');
        mainContentColumn.className = 'col-md-6';
    } else {
        document.getElementById('mainContent').classList.add('d-none');
        document.getElementById('emptyState').classList.remove('d-none');
        document.getElementById('chatColumn').classList.add('d-none');
        mainContentColumn.className = 'col-md-10';
    }
}