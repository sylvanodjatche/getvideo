// =============================================================
// GetVideo 2.0 - Core Frontend Engine (Live Task Tracking & Pure JS)
// =============================================================

function renderSimpleQRCode(canvas, text) {
    const ctx = canvas.getContext('2d');
    canvas.width = 200;
    canvas.height = 200;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
        ctx.drawImage(img, 0, 0, 200, 200);
    };
    img.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(text)}`;
}

document.addEventListener('DOMContentLoaded', () => {
    // ---------------------------------------------------------
    // 1. MULTILINGUAL DICTIONARY (i18n)
    // ---------------------------------------------------------
    const I18N = {
        fr: {
            hero_title_1: "Téléchargez vos vidéos en",
            hero_title_2: "Haute Qualité",
            hero_subtitle: "YouTube, TikTok sans filigrane, Instagram, Twitter/X, SoundCloud. Rapide, gratuit, sécurisé et sans pub.",
            input_placeholder: "Collez le lien de la vidéo ou musique ici...",
            paste_btn: "Coller",
            analyze_btn: "Analyser",
            loading_text: "Analyse et extraction des formats HD...",
            tab_video: "Vidéo MP4",
            tab_audio: "Audio MP3",
            tab_subtitles: "Sous-Titres",
            qr_mobile_btn: "Télécharger sur Mobile (QR)",
            install_app: "Installer l'App",
            download_btn: "Télécharger",
            cancel_btn: "Annuler le téléchargement",
            progress_modal_title: "Téléchargement en cours...",
            progress_connecting: "Connexion et initialisation du flux...",
            progress_downloading: "Téléchargement depuis la plateforme...",
            progress_converting: "Conversion et assemblage audio/vidéo...",
            progress_done: "Téléchargement terminé !",
            qr_title: "Télécharger sur Smartphone",
            qr_desc: "Scannez ce QR Code avec l'appareil photo de votre mobile pour télécharger directement.",
            qr_tip: "Fonctionne sur iPhone (iOS) et Android sans aucune application requise.",
            footer_text: "Moteur de Téléchargement HD Sécurisé • Zero-Storage & Zero-Cost",
            no_video: "Aucun format vidéo disponible pour ce lien.",
            no_audio: "Aucun format audio disponible.",
            no_subs: "Aucun sous-titre disponible pour cette vidéo."
        },
        en: {
            hero_title_1: "Download your videos in",
            hero_title_2: "High Quality",
            hero_subtitle: "YouTube, TikTok without watermark, Instagram, Twitter/X, SoundCloud. Fast, free, secure and ad-free.",
            input_placeholder: "Paste video or music link here...",
            paste_btn: "Paste",
            analyze_btn: "Analyze",
            loading_text: "Analyzing and extracting HD formats...",
            tab_video: "Video MP4",
            tab_audio: "Audio MP3",
            tab_subtitles: "Subtitles",
            qr_mobile_btn: "Download on Mobile (QR)",
            install_app: "Install App",
            download_btn: "Download",
            cancel_btn: "Cancel Download",
            progress_modal_title: "Downloading in progress...",
            progress_connecting: "Connecting and initializing stream...",
            progress_downloading: "Downloading from platform...",
            progress_converting: "Converting and merging audio/video...",
            progress_done: "Download complete!",
            qr_title: "Download on Smartphone",
            qr_desc: "Scan this QR Code with your phone camera to download directly.",
            qr_tip: "Works on iPhone (iOS) and Android without any app required.",
            footer_text: "Secure HD Download Engine • Zero-Storage & Zero-Cost",
            no_video: "No video format available for this link.",
            no_audio: "No audio format available.",
            no_subs: "No subtitles available for this video."
        },
        es: {
            hero_title_1: "Descarga tus videos en",
            hero_title_2: "Alta Calidad",
            hero_subtitle: "YouTube, TikTok sin marca de agua, Instagram, Twitter/X. Rápido, gratis, seguro y sin publicidad.",
            input_placeholder: "Pega el enlace del video o música aquí...",
            paste_btn: "Pegar",
            analyze_btn: "Analizar",
            loading_text: "Analizando formatos HD...",
            tab_video: "Video MP4",
            tab_audio: "Audio MP3",
            tab_subtitles: "Subtítulos",
            qr_mobile_btn: "Descargar en Móvil (QR)",
            install_app: "Instalar App",
            download_btn: "Descargar",
            cancel_btn: "Cancelar descarga",
            progress_modal_title: "Descarga en curso...",
            progress_connecting: "Conectando al flujo...",
            progress_downloading: "Descargando desde la plataforma...",
            progress_converting: "Convirtiendo y uniendo audio/video...",
            progress_done: "¡Descarga completada!",
            qr_title: "Descargar en Smartphone",
            qr_desc: "Escanea este código QR con tu móvil para descargar directamente.",
            qr_tip: "Funciona en iPhone y Android.",
            footer_text: "Motor de Descarga HD Seguro • Zero-Storage & Zero-Cost",
            no_video: "No hay formato de video disponible.",
            no_audio: "No hay formato de audio disponible.",
            no_subs: "No hay subtítulos disponibles."
        },
        ar: {
            hero_title_1: "قم بتنزيل مقاطع الفيديو بـ",
            hero_title_2: "أعلى جودة HD",
            hero_subtitle: "يوتيوب، تيك توك بدون علامة مائية، انستغرام، تويتر. سريع ومجاني وآمن بدون إعلانات.",
            input_placeholder: "الصق رابط الفيديو أو الموسيقى هنا...",
            paste_btn: "لصق",
            analyze_btn: "تحليل",
            loading_text: "جاري تحليل واستخراج جودات الفيديو...",
            tab_video: "فيديو MP4",
            tab_audio: "صوت MP3",
            tab_subtitles: "الترجمة",
            qr_mobile_btn: "تنزيل على الهاتف (QR)",
            install_app: "تثبيت التطبيق",
            download_btn: "تنزيل",
            cancel_btn: "إلغاء التنزيل",
            progress_modal_title: "جاري التنزيل...",
            progress_connecting: "جاري الاتصال بالبث...",
            progress_downloading: "جاري التنزيل من المنصة...",
            progress_converting: "جاري دمج ومعالجة الصوت والصورة...",
            progress_done: "تم التنزيل بنجاح!",
            qr_title: "تنزيل على الهاتف الذكي",
            qr_desc: "امسح رمز QR بكاميرا الهاتف للتنزيل مباشرة.",
            qr_tip: "يعمل على أجهزة آيفون وأندرويد.",
            footer_text: "محرك تنزيل HD آمن وسريع • مجاني تماماً",
            no_video: "لا توجد جودة فيديو متاحة.",
            no_audio: "لا توجد صيغة صوتية متاحة.",
            no_subs: "لا توجد ترجمات متاحة."
        },
        de: {
            hero_title_1: "Laden Sie Videos herunter in",
            hero_title_2: "Höchster Qualität",
            hero_subtitle: "YouTube, TikTok ohne Wasserzeichen, Instagram, Twitter/X. Schnell, kostenlos und sicher.",
            input_placeholder: "Video- oder Musiklink hier einfügen...",
            paste_btn: "Einfügen",
            analyze_btn: "Analysieren",
            loading_text: "Formate werden analysiert...",
            tab_video: "Video MP4",
            tab_audio: "Audio MP3",
            tab_subtitles: "Untertitel",
            qr_mobile_btn: "Auf Handy laden (QR)",
            install_app: "App installieren",
            download_btn: "Herunterladen",
            cancel_btn: "Download abbrechen",
            progress_modal_title: "Download läuft...",
            progress_connecting: "Stream wird verbunden...",
            progress_downloading: "Wird heruntergeladen...",
            progress_converting: "Konvertierung und Zusammenführung...",
            progress_done: "Download abgeschlossen!",
            qr_title: "Auf Smartphone laden",
            qr_desc: "Scannen Sie diesen QR-Code mit Ihrem Smartphone.",
            qr_tip: "Funktioniert auf iOS und Android.",
            footer_text: "Sichere HD-Download-Engine • Zero-Cost",
            no_video: "Kein Videoformat verfügbar.",
            no_audio: "Kein Audioformat verfügbar.",
            no_subs: "Keine Untertitel verfügbar."
        },
        pt: {
            hero_title_1: "Baixe seus vídeos em",
            hero_title_2: "Alta Qualidade",
            hero_subtitle: "YouTube, TikTok sem marca d'água, Instagram, Twitter/X. Rápido, gratuito, seguro e sem anúncios.",
            input_placeholder: "Cole o link do vídeo ou música aqui...",
            paste_btn: "Colar",
            analyze_btn: "Analisar",
            loading_text: "Analisando formatos HD...",
            tab_video: "Vídeo MP4",
            tab_audio: "Áudio MP3",
            tab_subtitles: "Legendas",
            qr_mobile_btn: "Baixar no Celular (QR)",
            install_app: "Instalar App",
            download_btn: "Baixar",
            cancel_btn: "Cancelar download",
            progress_modal_title: "Baixando...",
            progress_connecting: "Conectando ao fluxo...",
            progress_downloading: "Baixando da plataforma...",
            progress_converting: "Convertendo e mesclando áudio/vídeo...",
            progress_done: "Download concluído!",
            qr_title: "Baixar no Smartphone",
            qr_desc: "Escaneie este QR Code com seu celular.",
            qr_tip: "Funciona no iPhone e Android.",
            footer_text: "Motor de Download HD Seguro • Zero-Storage",
            no_video: "Nenhum formato de vídeo disponível.",
            no_audio: "Nenhum formato de áudio disponível.",
            no_subs: "Nenhuma legenda disponível."
        }
    };

    let currentLang = localStorage.getItem('getvideo_lang') || (navigator.language.slice(0, 2) in I18N ? navigator.language.slice(0, 2) : 'fr');

    function applyLanguage(lang) {
        if (!I18N[lang]) lang = 'fr';
        currentLang = lang;
        localStorage.setItem('getvideo_lang', lang);

        document.documentElement.lang = lang;
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';

        const label = document.getElementById('current-lang-label');
        if (label) label.textContent = lang.toUpperCase();

        document.querySelectorAll('[data-i18n]').forEach((el) => {
            const key = el.getAttribute('data-i18n');
            if (I18N[lang][key]) {
                el.textContent = I18N[lang][key];
            }
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (I18N[lang][key]) {
                el.placeholder = I18N[lang][key];
            }
        });
    }

    applyLanguage(currentLang);

    // Language Dropdown Toggle
    const langMenuBtn = document.getElementById('lang-menu-btn');
    const langDropdown = document.getElementById('lang-dropdown');
    if (langMenuBtn && langDropdown) {
        langMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            langDropdown.classList.toggle('hidden');
        });
        document.addEventListener('click', () => langDropdown.classList.add('hidden'));
        document.querySelectorAll('.lang-option').forEach((opt) => {
            opt.addEventListener('click', () => {
                const selected = opt.getAttribute('data-lang');
                applyLanguage(selected);
                langDropdown.classList.add('hidden');
            });
        });
    }

    // ---------------------------------------------------------
    // 2. THEME TOGGLE (DARK / LIGHT)
    // ---------------------------------------------------------
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIconSun = document.getElementById('theme-icon-sun');
    const themeIconMoon = document.getElementById('theme-icon-moon');

    function applyTheme(isDark) {
        if (isDark) {
            document.documentElement.classList.add('dark');
            if (themeIconSun) themeIconSun.classList.add('hidden');
            if (themeIconMoon) themeIconMoon.classList.remove('hidden');
            localStorage.setItem('getvideo_theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            if (themeIconSun) themeIconSun.classList.remove('hidden');
            if (themeIconMoon) themeIconMoon.classList.add('hidden');
            localStorage.setItem('getvideo_theme', 'light');
        }
        if (window.lucide) lucide.createIcons();
    }

    const savedTheme = localStorage.getItem('getvideo_theme');
    if (savedTheme) {
        applyTheme(savedTheme === 'dark');
    } else {
        // Thème sombre PAR DÉFAUT pour tous les nouveaux utilisateurs
        applyTheme(true);
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.classList.contains('dark');
            applyTheme(!isDark);
        });
    }

    if (window.lucide) {
        lucide.createIcons();
    }

    // ---------------------------------------------------------
    // 3. RESPONSIVE CONTROLS (Mobile vs Desktop)
    // ---------------------------------------------------------
    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 768;
    const pwaInstallBtn = document.getElementById('pwa-install-btn');
    const openQrBtn = document.getElementById('open-qr-btn');

    if (isMobileDevice && openQrBtn) {
        openQrBtn.classList.add('hidden');
    }

    let deferredPrompt = null;
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        if (pwaInstallBtn && isMobileDevice) {
            pwaInstallBtn.classList.remove('hidden');
            pwaInstallBtn.classList.add('inline-flex');
        }
    });

    if (pwaInstallBtn) {
        pwaInstallBtn.addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    pwaInstallBtn.classList.add('hidden');
                }
                deferredPrompt = null;
            }
        });
    }

    // ---------------------------------------------------------
    // 4. CORE EXTRACTION & UI LOGIC
    // ---------------------------------------------------------
    const form = document.getElementById('download-form');
    const urlInput = document.getElementById('url-input');
    const pasteBtn = document.getElementById('paste-btn');
    const submitBtn = document.getElementById('submit-btn');
    const loadingState = document.getElementById('loading-state');
    const errorBox = document.getElementById('error-box');
    const errorMessage = document.getElementById('error-message');
    const resultCard = document.getElementById('result-card');

    const tabVideo = document.getElementById('tab-video');
    const tabAudio = document.getElementById('tab-audio');
    const tabSubtitles = document.getElementById('tab-subtitles');
    const videoOptions = document.getElementById('video-options');
    const audioOptions = document.getElementById('audio-options');
    const subtitlesOptions = document.getElementById('subtitles-options');

    const mediaThumb = document.getElementById('media-thumb');
    const mediaDuration = document.getElementById('media-duration');
    const mediaPlatformBadge = document.getElementById('media-platform-badge');
    const mediaTitle = document.getElementById('media-title');
    const mediaUploader = document.getElementById('media-uploader');

    // QR Modal Elements
    const qrModal = document.getElementById('qr-modal');
    const closeQrBtn = document.getElementById('close-qr-btn');
    const qrCanvas = document.getElementById('qr-canvas');
    let currentAnalyzedUrl = "";

    // Progress Modal Elements
    const progressModal = document.getElementById('progress-modal');
    const progressFilename = document.getElementById('progress-filename');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressStatusText = document.getElementById('progress-status-text');
    const progressPercent = document.getElementById('progress-percent');
    const progressTransferred = document.getElementById('progress-transferred');
    const progressSpeed = document.getElementById('progress-speed');
    const cancelDownloadBtn = document.getElementById('cancel-download-btn');
    
    let currentActiveTaskId = null;
    let progressPollInterval = null;

    if (pasteBtn) {
        pasteBtn.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    urlInput.value = text.trim();
                    urlInput.focus();
                }
            } catch (err) {
                console.warn('Presse-papier non accessible:', err);
            }
        });
    }

    function setTabActive(activeBtn, activeGrid) {
        [tabVideo, tabAudio, tabSubtitles].forEach((btn) => {
            btn.className = 'px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center gap-2 transition-all';
        });
        [videoOptions, audioOptions, subtitlesOptions].forEach((grid) => grid.classList.add('hidden'));

        activeBtn.className = 'px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-indigo-600 text-white flex items-center gap-2 transition-all shadow-md';
        activeGrid.classList.remove('hidden');
    }

    tabVideo.addEventListener('click', () => setTabActive(tabVideo, videoOptions));
    tabAudio.addEventListener('click', () => setTabActive(tabAudio, audioOptions));
    tabSubtitles.addEventListener('click', () => setTabActive(tabSubtitles, subtitlesOptions));

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) return;
        analyzeUrl(url);
    });

    async function analyzeUrl(url) {
        currentAnalyzedUrl = url;
        errorBox.classList.add('hidden');
        resultCard.classList.add('hidden');
        loadingState.classList.remove('hidden');
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-70', 'cursor-not-allowed');

        try {
            const apiUrl = `/api/info?url=${encodeURIComponent(url)}`;
            const response = await fetch(apiUrl);
            const resData = await response.json();

            if (!response.ok || resData.status !== 'success') {
                throw new Error(resData.detail || "Échec de l'analyse du lien.");
            }

            renderMedia(resData.data);
        } catch (err) {
            errorMessage.textContent = err.message || "Impossible d'extraire le média. Vérifiez le lien.";
            errorBox.classList.remove('hidden');
        } finally {
            loadingState.classList.add('hidden');
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-70', 'cursor-not-allowed');
        }
    }

    // Auto-analyze URL if in query params (?url=...)
    const urlParams = new URLSearchParams(window.location.search);
    const initialUrl = urlParams.get('url');
    if (initialUrl) {
        urlInput.value = initialUrl;
        analyzeUrl(initialUrl);
    }

    function renderMedia(data) {
        mediaThumb.src = data.thumbnail || 'https://via.placeholder.com/640x360?text=Apercu+Indisponible';
        mediaDuration.textContent = data.duration_formatted || '00:00';
        mediaPlatformBadge.textContent = data.platform.toUpperCase();
        mediaTitle.textContent = data.title || 'Média sans titre';
        mediaUploader.textContent = data.uploader || 'Auteur inconnu';

        // Render Video Formats (Clean: NO BADGES)
        videoOptions.innerHTML = '';
        if (data.videos && data.videos.length > 0) {
            data.videos.forEach((vid) => {
                const item = createCleanFormatCard({
                    title: `${vid.quality}`,
                    ext: vid.ext.toUpperCase(),
                    size: vid.filesize_formatted,
                    url: vid.url,
                    mediaUrl: vid.media_url,
                    formatId: vid.format_id,
                    safeTitle: data.safe_title,
                    fileExt: vid.ext,
                    isDirect: vid.is_direct_cdn
                });
                videoOptions.appendChild(item);
            });
        } else {
            videoOptions.innerHTML = `<p class="col-span-2 text-sm text-slate-400 py-4 text-center">${I18N[currentLang].no_video}</p>`;
        }

        // Render Audio Formats (Clean: NO BADGES)
        audioOptions.innerHTML = '';
        if (data.audios && data.audios.length > 0) {
            data.audios.forEach((aud) => {
                const item = createCleanFormatCard({
                    title: `${aud.quality}`,
                    ext: aud.ext.toUpperCase(),
                    size: aud.filesize_formatted,
                    url: aud.url,
                    mediaUrl: aud.media_url,
                    formatId: aud.format_id,
                    safeTitle: data.safe_title,
                    fileExt: aud.ext,
                    isDirect: aud.is_direct_cdn
                });
                audioOptions.appendChild(item);
            });
        } else {
            audioOptions.innerHTML = `<p class="col-span-2 text-sm text-slate-400 py-4 text-center">${I18N[currentLang].no_audio}</p>`;
        }

        // Render Subtitles
        subtitlesOptions.innerHTML = '';
        if (data.subtitles && data.subtitles.length > 0) {
            tabSubtitles.classList.remove('hidden');
            data.subtitles.forEach((sub) => {
                const item = document.createElement('div');
                item.className = 'flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 transition-all';
                item.innerHTML = `
                    <div class="flex items-center space-x-3">
                        <div class="w-8 h-8 rounded-lg bg-indigo-600/10 text-indigo-400 flex items-center justify-center font-bold text-xs uppercase">${sub.lang}</div>
                        <div>
                            <p class="text-sm font-semibold text-slate-200">${sub.name}</p>
                            <span class="text-xs text-slate-400">.${sub.ext.toUpperCase()}</span>
                        </div>
                    </div>
                    <a href="/api/subtitle?url=${encodeURIComponent(sub.url)}" download="${data.safe_title}_${sub.lang}.${sub.ext}" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i>
                        <span>${I18N[currentLang].download_btn}</span>
                    </a>
                `;
                subtitlesOptions.appendChild(item);
            });
        } else {
            tabSubtitles.classList.add('hidden');
        }

        resultCard.classList.remove('hidden');
        setTabActive(tabVideo, videoOptions);
        if (window.lucide) lucide.createIcons();
    }

    // ---------------------------------------------------------
    // 5. CLEAN FORMAT CARD CREATOR
    // ---------------------------------------------------------
    function createCleanFormatCard({ title, ext, size, url, mediaUrl, formatId, safeTitle, fileExt, isDirect }) {
        const card = document.createElement('div');
        card.className = 'flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/40 transition-all group';

        const downloadFileName = `${safeTitle}.${fileExt}`;

        card.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300 group-hover:text-indigo-400 group-hover:border-indigo-500/30 transition-colors">
                    <i data-lucide="download" class="w-4 h-4"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-slate-200">${title}</h4>
                    <span class="text-xs text-slate-400">${size} • .${ext}</span>
                </div>
            </div>
            <button 
                type="button"
                class="download-trigger-btn px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all active:scale-95"
            >
                <span>${I18N[currentLang].download_btn}</span>
                <i data-lucide="arrow-down" class="w-3.5 h-3.5"></i>
            </button>
        `;

        const triggerBtn = card.querySelector('.download-trigger-btn');
        triggerBtn.addEventListener('click', () => {
            startRealTimeDownload({
                isDirect,
                url,
                mediaUrl,
                formatId,
                title: safeTitle,
                ext: fileExt,
                filename: downloadFileName
            });
        });

        return card;
    }

    // ---------------------------------------------------------
    // 6. REAL-TIME SYNCHRONIZED PROGRESS HANDLER (0% -> 100%)
    // ---------------------------------------------------------
    async function startRealTimeDownload({ isDirect, url, mediaUrl, formatId, title, ext, filename }) {
        // Reset and Open Modal
        progressModal.classList.remove('hidden');
        progressFilename.textContent = filename;
        progressBarFill.style.width = '0%';
        progressPercent.textContent = '0%';
        progressStatusText.textContent = I18N[currentLang].progress_connecting;
        progressTransferred.textContent = '0 Mo / ...';
        progressSpeed.textContent = 'Calcul vitesse...';

        if (progressPollInterval) {
            clearInterval(progressPollInterval);
        }

        // Direct CDN Download (TikTok, Instagram, etc.)
        if (isDirect && url) {
            window.open(url, '_blank');
            setTimeout(() => progressModal.classList.add('hidden'), 800);
            return;
        }

        // Start Backend Task
        try {
            const startApiUrl = `/api/start_download?media_url=${encodeURIComponent(mediaUrl)}&format_id=${encodeURIComponent(formatId || '')}&title=${encodeURIComponent(title)}&ext=${ext}`;
            const startResp = await fetch(startApiUrl, { method: 'POST' });
            const startData = await startResp.json();

            if (!startResp.ok || startData.status !== 'started') {
                throw new Error(startData.detail || "Erreur de démarrage du téléchargement.");
            }

            currentActiveTaskId = startData.task_id;

            // Poll progress every 350ms
            progressPollInterval = setInterval(async () => {
                try {
                    const progResp = await fetch(`/api/progress/${currentActiveTaskId}`);
                    if (!progResp.ok) return;

                    const progData = await progResp.json();
                    
                    const percent = Math.min(100, Math.max(0, progData.percent || 0));
                    progressBarFill.style.width = `${percent}%`;
                    progressPercent.textContent = `${percent}%`;

                    if (progData.status === 'downloading') {
                        progressStatusText.textContent = I18N[currentLang].progress_downloading;
                        progressTransferred.textContent = `${progData.downloaded_mb || '0 Mo'} / ${progData.total_mb || '...'}`;
                        progressSpeed.textContent = `${progData.speed || '...'} (ETA: ${progData.eta || '...'})`;
                    } else if (progData.status === 'converting') {
                        progressStatusText.textContent = I18N[currentLang].progress_converting;
                        progressBarFill.style.width = '95%';
                        progressPercent.textContent = '95%';
                        progressSpeed.textContent = 'Traitement audio/vidéo...';
                    } else if (progData.status === 'ready') {
                        clearInterval(progressPollInterval);
                        progressBarFill.style.width = '100%';
                        progressPercent.textContent = '100%';
                        progressStatusText.textContent = I18N[currentLang].progress_done;
                        progressTransferred.textContent = progData.total_mb || 'Fichier complet';
                        progressSpeed.textContent = 'Prêt !';

                        // Trigger download
                        const downloadUrl = `/api/download_file/${currentActiveTaskId}`;
                        const link = document.createElement('a');
                        link.href = downloadUrl;
                        link.download = filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                        setTimeout(() => {
                            progressModal.classList.add('hidden');
                        }, 1500);

                    } else if (progData.status === 'error') {
                        clearInterval(progressPollInterval);
                        progressStatusText.textContent = 'Erreur : ' + (progData.error || 'Échec du traitement');
                        setTimeout(() => progressModal.classList.add('hidden'), 3000);
                    } else if (progData.status === 'cancelled') {
                        clearInterval(progressPollInterval);
                        progressStatusText.textContent = 'Téléchargement annulé.';
                        setTimeout(() => progressModal.classList.add('hidden'), 1500);
                    }
                } catch (err) {
                    console.error('Erreur polling:', err);
                }
            }, 350);

        } catch (err) {
            progressStatusText.textContent = 'Erreur : ' + err.message;
            setTimeout(() => progressModal.classList.add('hidden'), 2500);
        }
    }

    // Cancel Button Click Handler
    if (cancelDownloadBtn) {
        cancelDownloadBtn.addEventListener('click', async () => {
            if (progressPollInterval) {
                clearInterval(progressPollInterval);
            }
            if (currentActiveTaskId) {
                try {
                    await fetch(`/api/cancel_download/${currentActiveTaskId}`, { method: 'POST' });
                } catch (e) {}
            }
            progressStatusText.textContent = 'Téléchargement annulé.';
            setTimeout(() => progressModal.classList.add('hidden'), 500);
        });
    }

    // ---------------------------------------------------------
    // 7. QR CODE MODAL FOR MOBILE
    // ---------------------------------------------------------
    if (openQrBtn && qrModal && closeQrBtn && qrCanvas) {
        openQrBtn.addEventListener('click', () => {
            const currentHost = window.location.origin;
            const mobileUrl = `${currentHost}/?url=${encodeURIComponent(currentAnalyzedUrl)}`;

            renderSimpleQRCode(qrCanvas, mobileUrl);
            qrModal.classList.remove('hidden');
        });

        closeQrBtn.addEventListener('click', () => qrModal.classList.add('hidden'));
        qrModal.addEventListener('click', (e) => {
            if (e.target === qrModal) qrModal.classList.add('hidden');
        });
    }
});
