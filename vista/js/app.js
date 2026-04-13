/* ===================================================
   APP.JS - Estado global y lógica de la aplicación
   Usa Alpine.js para reactividad y estado compartido
   =================================================== */

// URL base de la API (vacío porque el frontend se sirve desde el mismo servidor FastAPI)
const API_BASE = '';

/**
 * Estado global de la aplicación Alpine.js
 * Controla la navegación, autenticación, datos del contrato,
 * dashboard y comunicación con la API.
 */
function appState() {
    return {
        // --- Utilidades ---
        formatDate(dateString) {
            if (!dateString) return '___/___/______';
            const [year, month, day] = dateString.split('-');
            return `${day}/${month}/${year}`;
        },

        // ========================
        // NAVEGACIÓN
        // ========================
        currentView: 'landing', // 'landing' | 'selector' | 'editor' | 'dashboard'
        scrolled: false,

        // ========================
        // USUARIO / AUTENTICACIÓN
        // ========================
        user: {
            loggedIn: false,
            nombre: '',
            email: '',
            id: null
        },
        showAuthModal: false,
        authMode: 'login', // 'login' | 'signup' | 'forgot' | 'reset'
        authLoading: false,
        authError: '',
        authSuccess: '',
        loginData: { email: '', password: '' },
        signupData: { nombre: '', email: '', password: '' },
        forgotEmail: '',
        resetData: { nueva_password: '', confirmar_password: '' },
        resetToken: '',
        showUserMenu: false,

        // ========================
        // NOTIFICACIONES
        // ========================
        notifications: [],
        showNotifications: false,

        // ========================
        // CONTRATO (Estado Alpine.js según AGENT.md)
        // ========================
        currentContractId: null, // Para saber si estamos editando uno existente
        contrato: {
            titulo: 'Contrato sin título',
            tipo: '',
            vendedores: [{ id: Math.random().toString(36).substr(2, 9), nombre: '', dni: '', domicilio: '' }],
            compradores: [{ id: Math.random().toString(36).substr(2, 9), nombre: '', dni: '', domicilio: '' }],
            finca: {
                direccion: '',
                precio: '',
                arras: '',
                referencia_catastral: '',
                ciudad: '',
                ciudad_juzgados: ''
            },
            fechas: { firma: '', limite: '' },
            clausulas: [],
            // Campos específicos por tipo
            extra: {
                descripcion_carga: '',      // arras_con_cargas
                resto_escritura: '',        // arras_sin_cargas
                duracion_anos: '',          // alquiler
                fecha_entrada: '',          // alquiler
                renta_anual: '',            // alquiler
                renta_mensual: '',          // alquiler
                iban_arrendador: '',        // alquiler
                fianza_euros: '',           // alquiler
                pagador_ibi: 'ARRENDADOR'  // alquiler
            }
        },

        // ========================
        // EDITOR / UPLOAD
        // ========================
        dragOver: false,
        uploading: false,
        uploadSuccess: false,

        // ========================
        // DASHBOARD
        // ========================
        dashboardStats: {
            activos: 0,
            espera: 0,
            finalizados: 0
        },
        alerts: [],
        recentContracts: [],

        // ========================
        // TOAST
        // ========================
        toast: { show: false, message: '', type: 'info', icon: 'info' },

        // ========================
        // INICIALIZACIÓN
        // ========================
        init() {
            // Detectar scroll para cambiar estilo del header
            window.addEventListener('scroll', () => {
                this.scrolled = window.scrollY > 10;
            });

            // Comprobar si hay sesión guardada en localStorage
            const savedUser = localStorage.getItem('arraspro_user');
            if (savedUser) {
                try {
                    this.user = JSON.parse(savedUser);
                    this.fetchUserContracts();
                } catch (e) {
                    localStorage.removeItem('arraspro_user');
                }
            }

            // Detectar token de restablecimiento en la URL (?reset_token=XXX)
            const urlParams = new URLSearchParams(window.location.search);
            const resetToken = urlParams.get('reset_token');
            if (resetToken) {
                this.resetToken = resetToken;
                this.authMode = 'reset';
                this.showAuthModal = true;
                // Limpiar el token de la URL para que no se reutilice
                window.history.replaceState({}, document.title, window.location.pathname);
                this.$nextTick(() => lucide.createIcons());
            }
        },

        async fetchUserContracts() {
            if (!this.user.id) return;
            try {
                const response = await fetch(`${API_BASE}/contratos/?user_id=${this.user.id}`);
                if (response.ok) {
                    const rawContracts = await response.json();
                    
                    let activos = 0, espera = 0, finalizados = 0;
                    
                    this.recentContracts = rawContracts.map(c => {
                        const d = c.datos_json || {};
                        const fecha = new Date(c.fecha_creacion).toLocaleDateString();
                        const comprador = d.compradores && d.compradores[0] && d.compradores[0].nombre ? d.compradores[0].nombre : 'Sin comprador';
                        const direccion = d.finca && d.finca.direccion ? d.finca.direccion : 'Sin dirección';
                        const precio = d.finca && d.finca.precio ? '€' + d.finca.precio : '€0';
                        const titulo = d.titulo || `Contrato #${c.id}`;
                        const isAlquiler = d.tipo && d.tipo.includes('alquiler');
                        
                        if (c.estado === 'activo') activos++;
                        else if (c.estado === 'vencido') finalizados++;
                        else espera++;

                        return {
                            ...c,
                            direccion,
                            comprador,
                            fecha,
                            precio,
                            titulo,
                            estadoLabel: c.estado.toUpperCase(),
                            icon: isAlquiler ? 'key' : 'home',
                            iconClass: isAlquiler ? 'icon-building' : 'icon-home'
                        };
                    });
                    
                    this.dashboardStats = { activos, espera, finalizados };
                    this.$nextTick(() => lucide.createIcons());
                }
            } catch (error) {
                console.error('Error cargando contratos:', error);
            }
        },

        openContract(contract) {
            this.currentContractId = contract.id;
            this.contrato = JSON.parse(JSON.stringify(contract.datos_json));
            if (!this.contrato.titulo) this.contrato.titulo = contract.titulo || "Contrato sin título";
            this.navigateTo('editor');
            this.showToast('Contrato cargado', 'info', 'file-text');
        },

        async renameContract(contract) {
            const newTitle = prompt('Nuevo nombre para el contrato:', contract.titulo);
            if (newTitle && newTitle.trim() !== '') {
                // Actualizar localmente primero
                const updatedData = { ...contract.datos_json };
                updatedData.titulo = newTitle.trim();
                
                try {
                    const response = await fetch(`${API_BASE}/contratos/${contract.id}?user_id=${this.user.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(updatedData)
                    });
                    
                    if (response.ok) {
                        this.showToast('Contrato renombrado', 'success', 'check');
                        this.fetchUserContracts();
                    }
                } catch (e) {
                    this.showToast('Error al renombrar', 'error', 'alert');
                }
            }
        },

        // ========================
        // NAVEGACIÓN
        // ========================
        navigateTo(view) {
            // Si vamos al selector, reseteamos el contrato para empezar uno nuevo
            if (view === 'selector') {
                this.resetContract();
            }
            this.currentView = view;
            this.showUserMenu = false;
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // Re-crear iconos de Lucide para la nueva vista
            this.$nextTick(() => {
                lucide.createIcons();
            });
        },

        resetContract() {
            this.currentContractId = null;
            this.contrato = {
                titulo: 'Contrato sin título',
                tipo: '',
                vendedores: [{ id: Math.random().toString(36).substr(2, 9), nombre: '', dni: '', domicilio: '' }],
                compradores: [{ id: Math.random().toString(36).substr(2, 9), nombre: '', dni: '', domicilio: '' }],
                finca: {
                    direccion: '',
                    precio: '',
                    arras: '',
                    referencia_catastral: '',
                    ciudad: '',
                    ciudad_juzgados: ''
                },
                fechas: { firma: '', limite: '' },
                clausulas: [],
                extra: {
                    descripcion_carga: '',
                    resto_escritura: '',
                    duracion_anos: '',
                    fecha_entrada: '',
                    renta_anual: '',
                    renta_mensual: '',
                    iban_arrendador: '',
                    fianza_euros: '',
                    pagador_ibi: 'ARRENDADOR'
                }
            };
        },

        scrollToFeatures() {
            const el = document.getElementById('features');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
        },

        // ========================
        // AUTENTICACIÓN
        // ========================
        openAuthModal(mode) {
            this.authMode = mode;
            this.showAuthModal = true;
            this.authError = '';
            
            // Inicializar el botón oficial de Google cada vez que se abre el modal
            this.$nextTick(() => {
                lucide.createIcons();
                this.initGoogleSignIn();
            });
        },

        initGoogleSignIn() {
            // Solo si la librería de Google ha cargado
            if (typeof google !== 'undefined') {
                google.accounts.id.initialize({
                    client_id: "641197400675-ga0jsgi5ivl5qntr2824lbpuuvqlt1o3.apps.googleusercontent.com",
                    callback: (response) => this.handleGoogleCredentialResponse(response)
                });
                
                // Renderizar botón centrado y con ancho completo del contenedor (si es posible)
                google.accounts.id.renderButton(
                    document.getElementById("g_id_signin"),
                    { 
                        theme: "outline", 
                        size: "large", 
                        width: "100%", // Intentamos ancho completo del div contenedor
                        text: "continue_with",
                        shape: "pill"
                    }
                );
            }
        },

        async handleGoogleCredentialResponse(response) {
            this.authLoading = true;
            try {
                // 'response.credential' es el JWT firmado por Google
                const res = await fetch(`${API_BASE}/auth/google`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ credential: response.credential })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    this.setUserSession(data);
                } else {
                    const err = await res.json();
                    this.authError = err.detail || 'Error verificando identidad con Google.';
                }
            } catch (e) {
                this.authError = 'Error de conexión con el servidor.';
            }
            this.authLoading = false;
        },


        async handleLogin() {
            this.authLoading = true;
            this.authError = '';

            try {
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.loginData)
                });

                if (response.ok) {
                    const data = await response.json();
                    this.setUserSession(data);
                } else {
                    const err = await response.json();
                    this.authError = err.detail || 'Error en las credenciales.';
                }
            } catch (error) {
                this.authError = 'Fallo de conexión. ¿Está la API funcionando?';
            }

            this.authLoading = false;
        },

        async handleSignup() {
            this.authError = '';
            const p = this.signupData.password;
            
            // Validación frontend rápida
            const hasUpper = /[A-Z]/.test(p);
            const hasLower = /[a-z]/.test(p);
            const hasNumber = /\d/.test(p);
            const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(p);
            const isLongEnough = p.length >= 8;

            if (!isLongEnough || !hasUpper || !hasLower || !hasNumber || !hasSpecial) {
                this.authError = 'La contraseña debe tener: 8+ caracteres, mayúscula, minúscula, número y símbolo.';
                return;
            }

            this.authLoading = true;
            try {
                const response = await fetch(`${API_BASE}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.signupData)
                });

                if (response.ok) {
                    const data = await response.json();
                    this.setUserSession(data);
                } else {
                    const err = await response.json();
                    // Si el backend devuelve un error de validación (422), extraer el mensaje
                    if (err.detail && Array.isArray(err.detail)) {
                        this.authError = err.detail[0].msg;
                    } else {
                        this.authError = err.detail || 'No se pudo crear la cuenta.';
                    }
                }
            } catch (error) {
                this.authError = 'Fallo de conexión. ¿Está la API funcionando?';
            }

            this.authLoading = false;
        },

        async handleForgotPassword() {
            this.authLoading = true;
            this.authError = '';
            this.authSuccess = '';
            console.log("Solicitando recuperación para:", this.forgotEmail);

            try {
                const response = await fetch(`${API_BASE}/auth/forgot-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: this.forgotEmail })
                });

                const data = await response.json();
                console.log("Respuesta backend recovery:", data);

                if (response.ok) {
                    this.authSuccess = data.mensaje;
                    this.forgotEmail = '';
                } else {
                    this.authError = data.detail || 'No se pudo procesar la solicitud.';
                }
            } catch (error) {
                console.error("Error en forgotPassword:", error);
                this.authError = 'Error de conexión. Comprueba que el servidor está activo.';
            } finally {
                this.authLoading = false;
            }
        },

        async handleResetPassword() {
            if (this.resetData.nueva_password !== this.resetData.confirmar_password) {
                this.authError = 'Las contraseñas no coinciden.';
                return;
            }

            this.authLoading = true;
            this.authError = '';

            try {
                const response = await fetch(`${API_BASE}/auth/reset-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        token: this.resetToken,
                        nueva_password: this.resetData.nueva_password
                    })
                });

                if (response.ok) {
                    this.showToast('Contraseña actualizada con éxito', 'success', 'check-circle');
                    this.authMode = 'login';
                    this.resetData = { nueva_password: '', confirmar_password: '' };
                } else {
                    const err = await response.json();
                    this.authError = err.detail || 'Error al restablecer la contraseña.';
                }
            } catch (error) {
                console.error("Error en resetPassword:", error);
                this.authError = 'Fallo de conexión.';
            } finally {
                this.authLoading = false;
            }
        },

        setUserSession(data) {
            this.user = {
                loggedIn: true,
                nombre: data.nombre,
                email: data.email,
                id: data.id
            };
            localStorage.setItem('arraspro_user', JSON.stringify(this.user));
            this.showAuthModal = false;
            this.showToast('¡Bienvenido, ' + this.user.nombre + '!', 'success', 'check-circle');

            // Si venía de intentar descargar, ir al dashboard
            if (this.currentView === 'editor') {
                this.downloadPDF();
            } else {
                this.navigateTo('dashboard');
                this.fetchUserContracts();
            }
        },

        logout() {
            this.user = { loggedIn: false, nombre: '', email: '', id: null };
            localStorage.removeItem('arraspro_user');
            this.showUserMenu = false;
            this.navigateTo('landing');
            this.showToast('Sesión cerrada correctamente', 'info', 'log-out');
        },

        toggleUserMenu() {
            this.showUserMenu = !this.showUserMenu;
        },

        toggleNotifications() {
            this.showNotifications = !this.showNotifications;
        },

        // ========================
        // SELECTOR DE CONTRATO
        // ========================
        selectContractType(type) {
            this.contrato.tipo = type;
        },

        getContractTypeLabel() {
            const labels = {
                'arras_sin_cargas': 'Compraventa sin cargas',
                'arras_con_cargas': 'Compraventa con cargas',
                'alquiler': 'Alquiler'
            };
            return labels[this.contrato.tipo] || 'Sin definir';
        },

        /**
         * Genera el HTML de la vista previa del contrato
         * aplicando la plantilla correcta según el tipo seleccionado.
         */
        getContractPreview() {
            const c = this.contrato;
            const tipo = c.tipo;

            // Helper: formatear fecha DD/MM/AAAA
            const fmt = (d) => { if (!d) return '___/___/______'; const [y,m,day] = d.split('-'); return `${day}/${m}/${y}`; };
            const blank = (v, placeholder) => v || placeholder;

            // --- Bloque de personas ---
            const bloqueVendedores = (c.vendedores || []).map((v, i) => {
                const nombre = blank(v.nombre, '____________________');
                const dni    = blank(v.dni,    '___________');
                const dom    = blank(v.domicilio, '____________________________');
                return `<p class="paper-text">D./Dña. <strong>${nombre}</strong>, con DNI/NIE <strong>${dni}</strong>, con domicilio en <strong>${dom}</strong>.</p>`;
            }).join('');

            const bloqueCompradores = (c.compradores || []).map((v, i) => {
                const nombre = blank(v.nombre, '____________________');
                const dni    = blank(v.dni,    '___________');
                const dom    = blank(v.domicilio, '____________________________');
                return `<p class="paper-text">D./Dña. <strong>${nombre}</strong>, con DNI/NIE <strong>${dni}</strong>, con domicilio en <strong>${dom}</strong>.</p>`;
            }).join('');

            const ciudad    = blank(c.finca.ciudad, 'Madrid');
            const fechaFirma = fmt(c.fechas.firma);
            const fechaLimite = fmt(c.fechas.limite);
            const direccion  = blank(c.finca.direccion, '________________________________');
            const refCatastral = blank(c.finca.referencia_catastral, '________________');
            const ciudadJuzgados = blank(c.finca.ciudad_juzgados, ciudad);
            const precio     = blank(c.finca.precio, '________');
            const arras      = blank(c.finca.arras,  '________');

            // Cláusulas adicionales
            const numNames = ['PRIMERA', 'SEGUNDA', 'TERCERA', 'CUARTA', 'QUINTA', 'SEXTA', 'SÉPTIMA', 'OCTAVA', 'NOVENA', 'DÉCIMA'];

            if (tipo === 'arras_sin_cargas') {
                const resto = blank((c.extra || {}).resto_escritura, '________');
                const clausulasBase = [
                    `<p class="paper-text"><strong>PRIMERA. - OBJETO.</strong><br>La parte VENDEDORA vende a la parte COMPRADORA, que compra, el inmueble descrito en el Manifiesto I como cuerpo cierto y en el estado actual de conservación que el comprador declara conocer.</p>`,
                    `<p class="paper-text"><strong>SEGUNDA. - PRECIO.</strong><br>El precio total de la compraventa se fija en <strong>${precio} EUROS</strong>, que se abonará de la siguiente forma:<br>1. La cantidad de <strong>${arras} EUROS</strong>, entregada previamente en concepto de arras.<br>2. La cantidad de <strong>${resto} EUROS</strong>, que se abonará mediante cheque bancario en el acto de otorgamiento de la escritura pública.</p>`,
                    `<p class="paper-text"><strong>TERCERA. - ESCRITURACIÓN Y POSESIÓN.</strong><br>La entrega de llaves y de la posesión se realizará en el momento de la firma de la escritura pública. La parte COMPRADORA elegirá Notaría, debiendo formalizarse la escritura antes del día <strong>${fechaLimite}</strong>.</p>`,
                    `<p class="paper-text"><strong>CUARTA. - GASTOS.</strong><br>Los gastos e impuestos derivados de la escritura se abonarán conforme a Ley: la parte VENDEDORA abonará la Plusvalía Municipal y la parte COMPRADORA abonará el ITP, Notaría, Gestión y Registro.</p>`,
                    `<p class="paper-text"><strong>QUINTA. - INCUMPLIMIENTO.</strong><br>Si la parte COMPRADORA incumpliera su obligación de pago, perderá las cantidades entregadas. Si el incumplimiento fuera de la parte VENDEDORA, deberá devolver el doble de las cantidades recibidas, conforme al artículo 1.454 del Código Civil.</p>`,
                    `<p class="paper-text"><strong>SEXTA. - JURISDICCIÓN.</strong><br>Para cualquier controversia, las partes se someten a los Juzgados y Tribunales de <strong>${ciudadJuzgados}</strong>.</p>`
                ];
                const clausulasExtra = (c.clausulas || []).map((cl, i) => {
                    const num = numNames[clausulasBase.length + i] || (clausulasBase.length + i + 1) + 'ª';
                    return `<p class="paper-text"><strong>${num}.</strong> – ${cl.texto || '__________________________________________________________________________________________'}</p>`;
                }).join('');

                return `
                    <h2 class="paper-title">CONTRATO PRIVADO DE COMPRAVENTA</h2>
                    <p class="paper-text">En <strong>${ciudad}</strong>, a fecha de <strong>${fechaFirma}</strong>.</p>
                    <h3 class="paper-subtitle">REUNIDOS</h3>
                    <p class="paper-text"><em>De una parte, como la parte COMPRADORA:</em></p>
                    ${bloqueCompradores}
                    <p class="paper-text"><em>De otra parte, como la parte VENDEDORA:</em></p>
                    ${bloqueVendedores}
                    <h3 class="paper-subtitle">MANIFIESTAN</h3>
                    <p class="paper-text">I.- Que la parte VENDEDORA es propietaria del inmueble sito en <strong>${direccion}</strong>, con Referencia Catastral <strong>${refCatastral}</strong>.</p>
                    <p class="paper-text">II.- Que dicho inmueble se encuentra libre de cargas, gravámenes, arrendatarios y al corriente en el pago de impuestos y gastos de comunidad.</p>
                    <p class="paper-text">III.- Que ambas partes han convenido la compraventa del inmueble conforme a las siguientes:</p>
                    <h3 class="paper-subtitle">ESTIPULACIONES</h3>
                    ${clausulasBase.join('')}
                    ${clausulasExtra}
                    <div class="paper-signatures">
                        <div class="signature-block"><div class="signature-line"></div><p>LA PARTE COMPRADORA</p></div>
                        <div class="signature-block"><div class="signature-line"></div><p>LA PARTE VENDEDORA</p></div>
                    </div>`;

            } else if (tipo === 'arras_con_cargas') {
                const carga = blank((c.extra || {}).descripcion_carga, 'Hipoteca con la entidad Banco X');
                const clausulasBase = [
                    `<p class="paper-text"><strong>PRIMERA. - OBJETO.</strong><br>La parte VENDEDORA vende a la parte COMPRADORA, que compra, el inmueble descrito en el Manifiesto I.</p>`,
                    `<p class="paper-text"><strong>SEGUNDA. - PRECIO Y RETENCIÓN POR CARGAS.</strong><br>El precio total de la compraventa se fija en <strong>${precio} EUROS</strong>.<br>Debido a la existencia de la carga mencionada en el Manifiesto II, las partes acuerdan:<br>1. La parte COMPRADORA retendrá del precio final la cantidad necesaria para la cancelación económica de dicha carga en el momento de la escritura pública.<br>2. El resto del precio, deducidas las arras de <strong>${arras} EUROS</strong> y la retención por carga, se entregará a la parte VENDEDORA mediante cheque bancario.</p>`,
                    `<p class="paper-text"><strong>TERCERA. - CANCELACIÓN DE CARGAS.</strong><br>La parte VENDEDORA se obliga a entregar la finca libre de cargas y gravámenes al momento de la firma de la escritura pública, siendo de su exclusivo cargo todos los gastos e impuestos que se devenguen por la cancelación (gastos notariales, registrales y de gestión).</p>`,
                    `<p class="paper-text"><strong>CUARTA. - ESCRITURACIÓN.</strong><br>La formalización de la escritura pública se realizará antes del día <strong>${fechaLimite}</strong>. La parte COMPRADORA elegirá la Notaría.</p>`,
                    `<p class="paper-text"><strong>QUINTA. - GASTOS E IMPUESTOS.</strong><br>Los gastos e impuestos derivados de la transmisión se abonarán conforme a Ley (Vendedor: Plusvalía; Comprador: ITP, Notaría y Registro).</p>`,
                    `<p class="paper-text"><strong>SEXTA. - JURISDICCIÓN.</strong><br>Las partes se someten a los Juzgados y Tribunales de <strong>${ciudadJuzgados}</strong>.</p>`
                ];
                const clausulasExtra = (c.clausulas || []).map((cl, i) => {
                    const num = numNames[clausulasBase.length + i] || (clausulasBase.length + i + 1) + 'ª';
                    return `<p class="paper-text"><strong>${num}.</strong> – ${cl.texto || '__________________________________________________________________________________________'}</p>`;
                }).join('');

                return `
                    <h2 class="paper-title">CONTRATO PRIVADO DE COMPRAVENTA<br><small style="font-size:0.65em;">(FINCA CON CARGAS)</small></h2>
                    <p class="paper-text">En <strong>${ciudad}</strong>, a fecha de <strong>${fechaFirma}</strong>.</p>
                    <h3 class="paper-subtitle">REUNIDOS</h3>
                    <p class="paper-text"><em>De una parte, como la parte COMPRADORA:</em></p>
                    ${bloqueCompradores}
                    <p class="paper-text"><em>De otra parte, como la parte VENDEDORA:</em></p>
                    ${bloqueVendedores}
                    <h3 class="paper-subtitle">MANIFIESTAN</h3>
                    <p class="paper-text">I.- Que la parte VENDEDORA es propietaria del inmueble sito en <strong>${direccion}</strong>, con Referencia Catastral <strong>${refCatastral}</strong>.</p>
                    <p class="paper-text">II.- Que dicho inmueble se encuentra gravado con la siguiente carga: <strong>${carga}</strong>.</p>
                    <p class="paper-text">III.- Que ambas partes han convenido la compraventa del inmueble conforme a las siguientes:</p>
                    <h3 class="paper-subtitle">ESTIPULACIONES</h3>
                    ${clausulasBase.join('')}
                    ${clausulasExtra}
                    <div class="paper-signatures">
                        <div class="signature-block"><div class="signature-line"></div><p>LA PARTE COMPRADORA</p></div>
                        <div class="signature-block"><div class="signature-line"></div><p>LA PARTE VENDEDORA</p></div>
                    </div>`;

            } else if (tipo === 'alquiler') {
                const ex = c.extra || {};
                const duracion   = blank(ex.duracion_anos, '__');
                const fEntrada   = ex.fecha_entrada ? fmt(ex.fecha_entrada) : '___/___/______';
                const rentaAnual = blank(ex.renta_anual, '________');
                const rentaMens  = blank(ex.renta_mensual, '________');
                const iban       = blank(ex.iban_arrendador, 'ES__ ____ ____ ____ ____ ____');
                const fianza     = blank(ex.fianza_euros, '________');
                const pagadorIBI = blank(ex.pagador_ibi, 'ARRENDADOR');

                const clausulasBase = [
                    `<p class="paper-text"><strong>PRIMERA. - DURACIÓN.</strong><br>El arrendamiento se pacta por un plazo de <strong>${duracion}</strong> año/s, a contar desde el día <strong>${fEntrada}</strong>. El contrato se prorrogará obligatoriamente por plazos anuales hasta alcanzar una duración mínima de 5 años (o 7 si el arrendador es persona jurídica), conforme a la LAU.</p>`,
                    `<p class="paper-text"><strong>SEGUNDA. - RENTA.</strong><br>La renta anual fijada es de <strong>${rentaAnual} EUROS</strong>, a pagar en mensualidades anticipadas de <strong>${rentaMens} EUROS</strong>, dentro de los siete primeros días de cada mes.<br>El pago se realizará mediante transferencia bancaria a la cuenta: <strong>${iban}</strong>.</p>`,
                    `<p class="paper-text"><strong>TERCERA. - FIANZA.</strong><br>La parte arrendataria hace entrega en este acto de la suma de <strong>${fianza} EUROS</strong>, equivalente a una mensualidad de renta, en concepto de fianza legal.</p>`,
                    `<p class="paper-text"><strong>CUARTA. - GASTOS.</strong><br>Los gastos de suministros (luz, agua, gas) serán de cuenta exclusiva del ARRENDATARIO. Los gastos de comunidad e IBI serán por cuenta del <strong>${pagadorIBI}</strong>.</p>`,
                    `<p class="paper-text"><strong>QUINTA. - DESTINO.</strong><br>La vivienda se alquila exclusivamente para satisfacer la necesidad permanente de vivienda del arrendatario, prohibiéndose el subarriendo total o parcial.</p>`,
                    `<p class="paper-text"><strong>SEXTA. - JURISDICCIÓN.</strong><br>Para cualquier controversia que pudiera surgir, las partes se someten a los Juzgados y Tribunales de <strong>${ciudadJuzgados}</strong>.</p>`
                ];
                const clausulasExtra = (c.clausulas || []).map((cl, i) => {
                    const num = numNames[clausulasBase.length + i] || (clausulasBase.length + i + 1) + 'ª';
                    return `<p class="paper-text"><strong>${num}.</strong> – ${cl.texto || '__________________________________________________________________________________________'}</p>`;
                }).join('');

                return `
                    <h2 class="paper-title">CONTRATO DE ARRENDAMIENTO DE VIVIENDA</h2>
                    <p class="paper-text">En <strong>${ciudad}</strong>, a fecha de <strong>${fechaFirma}</strong>.</p>
                    <h3 class="paper-subtitle">REUNIDOS</h3>
                    <p class="paper-text"><em>De una parte, como ARRENDADOR/ES:</em></p>
                    ${bloqueVendedores}
                    <p class="paper-text"><em>De otra parte, como ARRENDATARIO/S:</em></p>
                    ${bloqueCompradores}
                    <p class="paper-text">Ambas partes se reconocen capacidad legal suficiente para el otorgamiento del presente contrato de arrendamiento.</p>
                    <h3 class="paper-subtitle">EXPONEN</h3>
                    <p class="paper-text">I. Que la parte arrendadora es propietaria de la vivienda situada en:<br><strong>Dirección:</strong> ${direccion}<br><strong>Referencia Catastral:</strong> ${refCatastral}</p>
                    <p class="paper-text">II. Que la parte arrendataria está interesada en el alquiler de dicha vivienda para su uso exclusivo de residencia habitual.</p>
                    <h3 class="paper-subtitle">CLÁUSULAS</h3>
                    ${clausulasBase.join('')}
                    ${clausulasExtra}
                    <div class="paper-signatures">
                        <div class="signature-block"><div class="signature-line"></div><p>EL ARRENDADOR</p></div>
                        <div class="signature-block"><div class="signature-line"></div><p>EL ARRENDATARIO</p></div>
                    </div>`;
            }

            // Fallback si no hay tipo seleccionado
            return `<div style="text-align:center; padding: 3rem; color: var(--text-tertiary);"><p style="font-size:1.1rem;">Selecciona un tipo de contrato para ver la vista previa.</p></div>`;
        },

        // ========================
        // VENDEDORES / COMPRADORES
        // ========================
        addVendedor() {
            this.contrato.vendedores.push({ id: Math.random().toString(36).substr(2, 9), nombre: '', dni: '', domicilio: '' });
        },

        removeVendedor(index) {
            this.contrato.vendedores.splice(index, 1);
        },

        addComprador() {
            this.contrato.compradores.push({ id: Math.random().toString(36).substr(2, 9), nombre: '', dni: '', domicilio: '' });
        },

        removeComprador(index) {
            this.contrato.compradores.splice(index, 1);
        },
        
        // --- Gestión de cláusulas extra ---
        addClausula() {
            this.contrato.clausulas.push({ id: Math.random().toString(36).substr(2, 9), texto: "" });
        },
        
        removeClausula(index) {
            this.contrato.clausulas.splice(index, 1);
        },

        // ========================
        // SUBIDA DE ARCHIVOS / IA
        // ========================
        handleFileDrop(event) {
            this.dragOver = false;
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        },

        handleFileUpload(event) {
            const files = event.target.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        },

        async processFile(file) {
            this.uploading = true;
            this.uploadSuccess = false;

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${API_BASE}/documentos/upload`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();
                    const datos = result.datos;

                    // Rellenar los campos del formulario con los datos extraídos
                    if (datos) {
                        if (datos.NOMBRE_VENDEDOR) this.contrato.vendedores[0].nombre = datos.NOMBRE_VENDEDOR;
                        if (datos.DNI_VENDEDOR) this.contrato.vendedores[0].dni = datos.DNI_VENDEDOR;
                        if (datos.DOMICILIO_VENDEDOR) this.contrato.vendedores[0].domicilio = datos.DOMICILIO_VENDEDOR;
                        if (datos.DIRECCION_FINCA) this.contrato.finca.direccion = datos.DIRECCION_FINCA;
                        if (datos.CUOTA_PARTICIPACION) {
                             this.showToast('Nota Simple detectada con éxito', 'success', 'sparkles');
                        }
                    }

                    this.uploadSuccess = true;
                    this.showToast('Datos extraídos correctamente por la IA', 'success', 'sparkles');
                } else {
                    throw new Error('Error en la respuesta del servidor');
                }
            } catch (error) {
                // Simulación si la API no está disponible
                await this.simulateAIExtraction();
            }

            this.uploading = false;
            this.$nextTick(() => lucide.createIcons());
        },

        async processDni(file) {
            this.uploading = true;
            try {
                const formData = new FormData();
                formData.append('file', file);
                const response = await fetch(`${API_BASE}/documentos/upload-dni`, {
                    method: 'POST',
                    body: formData
                });
                if (response.ok) {
                    const result = await response.json();
                    const d = result.datos;
                    // Rellenar en el primer vendedor por defecto
                    if (d.NOMBRE) this.contrato.vendedores[0].nombre = d.NOMBRE;
                    if (d.DNI) this.contrato.vendedores[0].dni = d.DNI;
                    if (d.DOMICILIO) this.contrato.vendedores[0].domicilio = d.DOMICILIO;
                    this.showToast('DNI procesado con éxito', 'success', 'user-check');
                }
            } catch (e) {
                this.showToast('Error procesando DNI', 'error', 'alert-circle');
            }
            this.uploading = false;
        },

        async simulateAIExtraction() {
            // Simulamos un delay de la IA
            await new Promise(resolve => setTimeout(resolve, 2000));

            this.contrato.vendedores[0].nombre = 'Juan Pérez García';
            this.contrato.vendedores[0].dni = '12345678A';
            this.contrato.vendedores[0].domicilio = 'Calle Mayor 15, Madrid';
            this.contrato.finca.direccion = 'Calle Velázquez 42, 3ºB, Madrid';

            this.uploadSuccess = true;
            this.showToast('Datos extraídos correctamente (demo)', 'success', 'sparkles');
        },

        // ========================
        // DESCARGA PDF
        // ========================
        handleDownload() {
            // Comprobar campos vacíos clave
            let c = this.contrato;
            let isComplete = true;
            if (!c.finca.direccion || !c.fechas.firma || !c.fechas.limite || !c.finca.precio || !c.vendedores[0].nombre || !c.compradores[0].nombre) {
                isComplete = false;
            }

            if (!isComplete) {
                if(!window.confirm("Faltan cosas importantes por rellenar. ¿Estás seguro que quieres descargar?")) {
                    return;
                }
            }

            if (!this.user.loggedIn) {
                this.openAuthModal('signup');
                return;
            }
            this.downloadPDF();
        },

        async downloadPDF() {
            this.showToast('Generando tu contrato PDF...', 'info', 'file-text');

            try {
                const response = await fetch(`${API_BASE}/contratos/generar-pdf`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.contrato)
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'Contrato_ArrasPro.pdf';
                    a.click();
                    window.URL.revokeObjectURL(url);

                    // --- GUARDAR EN BD AUTOMÁTICAMENTE ---
                    try {
                        let endpoint = `${API_BASE}/contratos/?user_id=${this.user.id}`;
                        let method = 'POST';
                        
                        if (this.currentContractId) {
                            endpoint = `${API_BASE}/contratos/${this.currentContractId}?user_id=${this.user.id}`;
                            method = 'PUT';
                        }
                        
                        await fetch(endpoint, {
                            method: method,
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.contrato)
                        });
                    } catch (e) { console.error("Error guardando en BD"); }

                    this.showToast('¡Contrato descargado y guardado!', 'success', 'check-circle');
                    this.navigateTo('dashboard');
                    this.fetchUserContracts();
                } else {
                    throw new Error('Error generando el PDF');
                }
            } catch (error) {
                this.showToast('PDF generado (demo - conecta la API para descarga real)', 'info', 'info');
                // Redirigir al dashboard igualmente para mostrar la funcionalidad
                setTimeout(() => this.navigateTo('dashboard'), 1500);
            }
        },

        // ========================
        // DASHBOARD
        // ========================
        dismissAlert(index) {
            this.alerts.splice(index, 1);
        },

        openContract(contract) {
            this.showToast('Abriendo contrato: ' + contract.direccion, 'info', 'file-text');
        },

        // ========================
        // TOAST / NOTIFICACIONES
        // ========================
        showToast(message, type = 'info', icon = 'info') {
            this.toast = { show: true, message, type, icon };
            this.$nextTick(() => lucide.createIcons());
            setTimeout(() => {
                this.toast.show = false;
            }, 3500);
        }
    };
}
