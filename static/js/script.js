const AGENT_SVG = `
    <svg class="agent-icon" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
            <linearGradient id="agentBody2" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#fff7f0"/>
                <stop offset="100%" stop-color="#ffe8d6"/>
            </linearGradient>
            <radialGradient id="agentGlow2" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#F37021" stop-opacity="0.35"/>
                <stop offset="100%" stop-color="#F37021" stop-opacity="0"/>
            </radialGradient>
        </defs>
        <circle class="agent-glow" cx="60" cy="68" r="48" fill="url(#agentGlow2)"/>
        <line class="agent-antenna" x1="60" y1="20" x2="60" y2="32" stroke="#F37021" stroke-width="2.5" stroke-linecap="round"/>
        <circle class="agent-antenna-dot" cx="60" cy="18" r="3.5" fill="#F37021"/>
        <rect class="agent-head" x="22" y="32" width="76" height="68" rx="22" fill="url(#agentBody2)" stroke="#F37021" stroke-width="2"/>
        <g class="agent-face">
            <path class="agent-eye left" d="M 40 64 Q 44 64 48 64" fill="none" stroke="#1a1a1a" stroke-width="3" stroke-linecap="round"/>
            <path class="agent-eye right" d="M 72 64 Q 76 64 80 64" fill="none" stroke="#1a1a1a" stroke-width="3" stroke-linecap="round"/>
            <circle class="agent-eye-open left" cx="44" cy="64" r="3.5" fill="#1a1a1a"/>
            <circle class="agent-eye-open right" cx="76" cy="64" r="3.5" fill="#1a1a1a"/>
            <path class="agent-mouth" d="M 52 80 Q 60 84 68 80" fill="none" stroke="#1a1a1a" stroke-width="2.5" stroke-linecap="round"/>
        </g>
        <circle class="agent-cheek left" cx="38" cy="76" r="4" fill="#F37021" opacity="0.35"/>
        <circle class="agent-cheek right" cx="82" cy="76" r="4" fill="#F37021" opacity="0.35"/>
    </svg>`;

function renderAgentState(state) {
    const states = {
        sleeping: {
            status: 'El asistente está descansando...',
            hint: 'Sube y procesa los documentos para despertarlo'
        },
        ready: {
            status: '¡Asistente listo!',
            hint: 'Pregúntame lo que quieras de los documentos'
        }
    };
    const cfg = states[state] || states.sleeping;
    const zzz = state === 'sleeping'
        ? '<div class="agent-zzz" aria-hidden="true"><span class="z z1">z</span><span class="z z2">z</span><span class="z z3">Z</span></div>'
        : '';
    return `<div class="chat-empty-state agent-state ${state}">
        <div class="agent-stage">${zzz}${AGENT_SVG}</div>
        <p class="agent-status">${cfg.status}</p>
        <p class="agent-hint">${cfg.hint}</p>
    </div>`;
}

function setChatEnabled(enabled, customPlaceholder) {
    const chatInput = document.getElementById('chatInput');
    const sendChat = document.getElementById('sendChat');
    if (!chatInput || !sendChat) return;
    chatInput.disabled = !enabled;
    sendChat.disabled = !enabled;
    chatInput.placeholder = customPlaceholder || (enabled
        ? "Escribe tu mensaje aquí..."
        : "Procesa los documentos primero");
    const container = document.querySelector('.chat-input-container');
    if (container) container.classList.toggle('disabled', !enabled);
    const chatBox = document.getElementById('chatBox');
    if (chatBox) chatBox.classList.toggle('locked', !enabled);
    if (!customPlaceholder) {
        setChatStatus(enabled ? 'online' : 'offline');
    }
}

function setChatStatus(state) {
    const wrap = document.getElementById('chatHeaderStatus');
    if (!wrap) return;
    const dot = wrap.querySelector('.status-dot');
    const text = wrap.querySelector('.status-text');
    dot.classList.remove('online', 'offline', 'busy');
    dot.classList.add(state);
    if (state === 'online') text.textContent = 'En línea';
    else if (state === 'busy') text.textContent = 'Procesando...';
    else text.textContent = 'Desconectado';
}

function setStep(step) {
    document.querySelectorAll('.workflow-stepper .step').forEach(el => {
        const n = parseInt(el.dataset.step, 10);
        el.classList.toggle('active', n === step);
        el.classList.toggle('completed', n < step);
    });
}

function setProcessButtonLabel(isReprocess) {
    const btn = document.getElementById('processButton');
    if (!btn) return;
    btn.innerHTML = isReprocess
        ? '<i class="fas fa-arrows-rotate me-2"></i>Reprocesar Documentos'
        : '<i class="fas fa-bolt me-2"></i>Procesar Documentos';
    btn.dataset.mode = isReprocess ? 'reprocess' : 'process';
}

function resetExtractionCardsToSkeleton() {
    document.querySelectorAll('.extracted-section .card-body').forEach(el => {
        el.innerHTML = SKELETON_BLOCK;
    });
}

const TOAST_ICONS = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    info: 'fa-circle-info',
    warning: 'fa-triangle-exclamation'
};

function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
        <i class="fas ${TOAST_ICONS[type] || TOAST_ICONS.info}"></i>
        <span class="toast-text">${message}</span>
    `;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 350);
    }, duration);
}

function getInitials(name) {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
}

function avatarColor(seed) {
    const palette = ['#F37021', '#E5494D', '#7C3AED', '#0EA5E9', '#10B981', '#F59E0B', '#EC4899', '#6366F1'];
    let hash = 0;
    for (let i = 0; i < (seed || '').length; i++) hash = (hash * 31 + seed.charCodeAt(i)) | 0;
    return palette[Math.abs(hash) % palette.length];
}

const SKELETON_BLOCK = '<div class="skeleton-block"><div class="skeleton-line w90"></div><div class="skeleton-line w70"></div><div class="skeleton-line w80"></div></div>';

function formatBudget(value) {
    // Normaliza el campo "Presupuesto" cuando el modelo devuelve un número pelado.
    // Si ya viene con moneda explícita o texto, lo deja tal cual.
    if (!value) return value;
    const trimmed = String(value).trim();
    if (!trimmed) return trimmed;

    // Ya menciona moneda → no tocar
    if (/\b(COP|USD|EUR|MXN|CLP|PEN|ARS|BRL|GBP|JPY|CAD)\b/i.test(trimmed)) return trimmed;
    if (/peso|d[oó]lar|euro/i.test(trimmed)) return trimmed;

    // Si es solo un número (con o sin separadores/símbolo $), formatea en COP
    const onlyNumber = /^[\$\s]*\d[\d.,\s]*$/.test(trimmed);
    if (onlyNumber) {
        const digits = trimmed.replace(/[^\d]/g, '');
        if (digits.length > 0) {
            const num = Number(digits);
            if (!isNaN(num)) {
                return '$' + num.toLocaleString('es-CO') + ' COP';
            }
        }
    }
    return trimmed;
}

function renderFileItem(filename) {
    const ext = (filename.split('.').pop() || '').toUpperCase();
    const safe = filename.replace(/"/g, '&quot;');
    return `<li data-filename="${safe}">
        <div class="file-icon"><i class="fas fa-file-lines"></i></div>
        <div class="file-info">
            <div class="file-name" title="${safe}">${safe}</div>
            <div class="file-meta">${ext}</div>
        </div>
        <button type="button" class="file-delete" title="Quitar archivo"><i class="fas fa-xmark"></i></button>
    </li>`;
}

function deleteUploadedFile(filename, liEl) {
    if (!window.currentSessionId) return;
    fetch(`/upload/${window.currentSessionId}/${encodeURIComponent(filename)}`, { method: 'DELETE' })
        .then(r => r.json().then(d => ({ ok: r.ok, body: d })))
        .then(({ ok, body }) => {
            if (ok && body.status === 'deleted') {
                liEl.style.opacity = '0';
                liEl.style.transform = 'translateX(-8px)';
                setTimeout(() => liEl.remove(), 200);
                showToast('Archivo eliminado', 'info');
            } else {
                showToast(body.error || 'No se pudo eliminar', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error al eliminar archivo', 'error');
        });
}

document.addEventListener('DOMContentLoaded', function () {
    setChatEnabled(false);
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
            fileListElem.innerHTML = data.files.map(renderFileItem).join('');
            const newCount = (data.uploaded || data.files || []).length;
            if (newCount > 0) {
                showToast(`${newCount} archivo(s) subido(s) correctamente`, 'success');
                setStep(2);
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error al subir archivos', 'error');
        });
        fileInput.value = "";
    }

    document.getElementById('fileList').addEventListener('click', (e) => {
        const btn = e.target.closest('.file-delete');
        if (!btn) return;
        const li = btn.closest('li');
        if (!li || !li.dataset.filename) return;
        deleteUploadedFile(li.dataset.filename, li);
    });
    
    
    
    

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
    
        const isReprocess = processButton.dataset.mode === 'reprocess';
        processStatus.innerHTML = `<span class="status-pill processing"><span class="status-pill-dot"></span>${isReprocess ? 'Reprocesando' : 'Procesando'} documentos...</span>`;
        processButton.disabled = true;
        setStep(2);
        setChatEnabled(false, isReprocess ? 'Reprocesando documentos...' : 'Procesando documentos...');
        setChatStatus('busy');
        resetExtractionCardsToSkeleton();
        if (isReprocess) showToast('Reprocesando documentos...', 'info', 2500);

        const eventSource = new EventSource(`/process/${window.currentSessionId}`);
        eventSource.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.section === 'status' && data.value === 'completed') {
                processStatus.innerHTML = '<span class="status-pill success"><i class="fas fa-circle-check"></i>Procesamiento completado</span>';
                eventSource.close();
                setStep(3);
                setChatEnabled(true);
                processButton.disabled = false;
                setProcessButtonLabel(true);
                showToast(isReprocess ? '¡Reprocesado completo!' : '¡Documentos procesados! Ya puedes chatear', 'success');
                const existingAgent = document.querySelector('#chatBox .agent-state');
                if (existingAgent) {
                    existingAgent.classList.remove('sleeping');
                    existingAgent.classList.add('waking');
                    setTimeout(() => {
                        loadSessionDetails(window.currentSessionId);
                    }, 1300);
                } else {
                    loadSessionDetails(window.currentSessionId);
                }
                return;
            }
            if (data.section === 'general') {
                let element = document.getElementById(data.field);
                if (!element) {
                    document.getElementById('infoGeneral').innerHTML = `
                        <div class="info-row"><div class="info-label">Entidad contratante</div><div id="entidad" class="info-value pending"><span class="skeleton-line inline w60"></span></div></div>
                        <div class="info-row"><div class="info-label">Objeto de convocatoria</div><div id="objeto" class="info-value pending"><span class="skeleton-line inline w80"></span></div></div>
                        <div class="info-row"><div class="info-label">Presupuesto</div><div id="presupuesto" class="info-value pending"><span class="skeleton-line inline w50"></span></div></div>`;
                    element = document.getElementById(data.field);
                }
                if (element) {
                    const value = (data.field === 'presupuesto' || data.field === 'budget')
                        ? formatBudget(data.value)
                        : data.value;
                    element.innerHTML = marked.parse(value);
                    element.classList.remove('pending');
                }
            } else {
                const sectionBody = document.getElementById(data.section);
                if (sectionBody) {
                    sectionBody.innerHTML = marked.parse(data.value);
                    sectionBody.classList.add('extracted-content');
                }
            }
        };
        eventSource.onerror = function (error) {
            console.error('Error en el EventSource:', error);
            processStatus.innerHTML = '<span class="status-pill error"><i class="fas fa-circle-exclamation"></i>Error en el procesamiento</span>';
            processButton.disabled = false;
            // Restaurar estado del chat al previo (si era reprocess, vuelve habilitado)
            setChatEnabled(isReprocess);
            showToast('Error al procesar documentos', 'error');
            eventSource.close();
        };

        document.querySelectorAll('.extracted-section .card-body').forEach(el => {
            el.innerHTML = SKELETON_BLOCK;
        });
    });
    

    // CHAT: Enviar mensaje
    const chatBox = document.getElementById('chatBox');
    const chatInput = document.getElementById('chatInput');
    const sendChat = document.getElementById('sendChat');

    function sendMessage() {
        const message = chatInput.value.trim();
        if (message === "" || chatInput.disabled) return;

        const emptyState = chatBox.querySelector('.chat-empty-state');
        if (emptyState) emptyState.remove();

        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('message', 'user-message');
        userMessageDiv.innerHTML = marked.parse(message);
        chatBox.appendChild(userMessageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        chatInput.value = "";
    
        // Indicador "escribiendo..." (3 dots animados)
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'assistant-message', 'typing-message');
        typingDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        chatBox.appendChild(typingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    
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
    // No se borran los archivos del disco al cargar — son necesarios para reprocesar.
    // La limpieza de disco se hace al eliminar la sesión (cascade en /session/<id> DELETE).
    document.getElementById('fileList').innerHTML = "";
    document.getElementById('dropzone').style.display = "block";
    document.getElementById('processButton').disabled = false;
    document.getElementById('processStatus').textContent = "";


    document.getElementById('infoGeneral').innerHTML = `
        <div class="info-row"><div class="info-label">Entidad contratante</div><div id="entidad" class="info-value pending">Pendiente</div></div>
        <div class="info-row"><div class="info-label">Objeto de convocatoria</div><div id="objeto" class="info-value pending">Pendiente</div></div>
        <div class="info-row"><div class="info-label">Presupuesto</div><div id="presupuesto" class="info-value pending">Pendiente</div></div>`;
    document.getElementById('cronograma').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('presentacion').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('perfiles').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('evaluacion').innerHTML = `<p><span class="info-value pending">Pendiente</span></p>`;
    document.getElementById('chatBox').innerHTML = renderAgentState('sleeping');
    
    setChatEnabled(false);
    fetch(`/session/${session_id}/details`)
        .then(response => response.json())
        .then(data => {
            const chatBoxEl = document.getElementById('chatBox');
            const isProcessed = data.extracted_info && data.extracted_info.length > 0;
            if (isProcessed) {
                setChatEnabled(true);
                if (data.chat_messages && data.chat_messages.length === 0) {
                    chatBoxEl.innerHTML = renderAgentState('ready');
                }
            }
            const fillField = (id, value) => {
                const el = document.getElementById(id);
                if (!el) return;
                el.innerHTML = marked.parse(value);
                el.classList.remove('pending');
            };
            data.extracted_info.forEach(item => {
                if (item.section === "general") {
                    if (item.field === "contracting_entity" || item.field === "entidad") {
                        fillField('entidad', item.value);
                    } else if (item.field === "objective" || item.field === "objeto") {
                        fillField('objeto', item.value);
                    } else if (item.field === "budget" || item.field === "presupuesto") {
                        fillField('presupuesto', formatBudget(item.value));
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
            const fileListEl = document.getElementById('fileList');
            const dropzoneEl = document.getElementById('dropzone');
            const processBtn = document.getElementById('processButton');
            // Dropzone, file deletes y botón siempre disponibles — la UX permite
            // agregar/quitar archivos también después de procesar y luego reprocesar.
            fileListEl.classList.remove('processed');
            dropzoneEl.style.display = "";
            processBtn.disabled = false;
            if (data.files && data.files.length > 0) {
                fileListEl.innerHTML = data.files.map(f => renderFileItem(f.filename)).join('');
            }
            setProcessButtonLabel(isProcessed);
            if (isProcessed) setStep(3);
            if (data.chat_messages && data.chat_messages.length > 0) {
                chatBoxEl.innerHTML = "";
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
                sessionPanel.innerHTML = `
                    <div class="sessions-empty">
                        <div class="sessions-empty-icon">
                            <i class="fas fa-folder-open"></i>
                        </div>
                        <div class="sessions-empty-title">Sin sesiones aún</div>
                        <div class="sessions-empty-hint">Crea tu primera sesión para empezar a analizar pliegos</div>
                        <button type="button" class="sessions-empty-cta" id="sessionsEmptyCta">
                            <i class="fas fa-plus"></i>
                            <span>Nueva sesión</span>
                        </button>
                    </div>`;
                const cta = document.getElementById('sessionsEmptyCta');
                if (cta) cta.addEventListener('click', createNewSession);
                window.currentSessionId = null;
                updateMainContentVisibility(false);
            } else {
                updateMainContentVisibility(true);
                sessions.forEach(session => {
                    const sessionDiv = document.createElement('div');
                    sessionDiv.classList.add('session-item');
                    const displayName = session.name || `Sesión ${session.session_id.substring(0, 6)}`;
                    const initials = getInitials(displayName);
                    const color = avatarColor(session.session_id);
                    const dateStr = new Date(session.created_at).toLocaleDateString('es', { day: 'numeric', month: 'short' });
                    sessionDiv.innerHTML = `
                        <div class="session-avatar" style="background:${color}">${initials}</div>
                        <div class="session-meta">
                            <div class="session-name" title="${displayName}">${displayName}</div>
                            <div class="session-date">${dateStr}</div>
                        </div>
                        <button class="session-delete" title="Eliminar sesión"><i class="fas fa-xmark"></i></button>
                    `;
                    const deleteBtn = sessionDiv.querySelector('.session-delete');
                    deleteBtn.onclick = (e) => {
                        e.stopPropagation();
                        deleteSession(session.session_id);
                    };
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
    const modalEl = document.getElementById('confirmDeleteModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const confirmBtn = document.getElementById('confirmDeleteButton');

    const handler = () => {
        confirmBtn.removeEventListener('click', handler);
        modal.hide();
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
                        setChatEnabled(false);
                    }
                    loadSessions();
                } else {
                    console.error("Error al eliminar la sesión");
                }
            })
            .catch(err => console.error("Error al eliminar la sesión:", err));
    };
    confirmBtn.addEventListener('click', handler);
    modalEl.addEventListener('hidden.bs.modal', () => {
        confirmBtn.removeEventListener('click', handler);
    }, { once: true });
    modal.show();
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