(function () {
    'use strict';
    var consent = window.CookieConsent;
    if (!consent) return;

    function allowed(category) {
        return consent.acceptedCategory(category);
    }

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () {
        var command = arguments[0];
        var name = arguments[1];
        var options = arguments[2] || {};
        if (command === 'config' || command === 'event') {
            var destination = command === 'config' ? name : options.send_to || '';
            var category = /^(AW|DC)-/.test(destination) || name === 'conversion' ? 'marketing' : 'analytics';
            if (!allowed(category)) return;
        }
        window.dataLayer.push(arguments);
    };
    window.gtag('consent', 'default', {
        analytics_storage: 'denied', ad_storage: 'denied',
        ad_user_data: 'denied', ad_personalization: 'denied'
    });

    function updateGoogleConsent() {
        var analytics = allowed('analytics');
        var marketing = allowed('marketing');
        window['ga-disable-G-LYDBN7KGBN'] = !analytics;
        window.gtag('consent', 'update', {
            analytics_storage: analytics ? 'granted' : 'denied',
            ad_storage: marketing ? 'granted' : 'denied',
            ad_user_data: marketing ? 'granted' : 'denied',
            ad_personalization: marketing ? 'granted' : 'denied'
        });
        if (!marketing) {
            try {
                localStorage.removeItem('bv_ft');
                sessionStorage.removeItem('bvg_ft');
            } catch (error) { /* Storage may be disabled. */ }
        }
        if (allowed('external')) {
            document.querySelectorAll('iframe[data-sbs-map-src]').forEach(function (frame) {
                if (!frame.src) frame.src = frame.dataset.sbsMapSrc;
                frame.hidden = false;
                if (frame.previousElementSibling && frame.previousElementSibling.classList.contains('sbs-map-placeholder')) {
                    frame.previousElementSibling.hidden = true;
                }
            });
        }
    }

    function cookieRules(pattern) {
        return [
            { name: pattern },
            { name: pattern, domain: '.sheabusinesssolutions.com' },
            { name: pattern, domain: 'sheabusinesssolutions.com' }
        ];
    }

    var spanish = document.documentElement.lang.toLowerCase().indexOf('es') === 0;
    document.querySelectorAll('iframe[data-sbs-map-src]').forEach(function (frame) {
        var placeholder = document.createElement('div');
        placeholder.className = 'sbs-map-placeholder';
        var description = document.createElement('p');
        description.textContent = spanish ? 'Google proporciona este mapa. Puede cargarlo sin permitir analítica ni publicidad.' : 'This map is provided by Google. You can load it separately from analytics and advertising.';
        var load = document.createElement('button');
        load.type = 'button';
        load.textContent = spanish ? 'Cargar mapa de Google' : 'Load Google map';
        load.addEventListener('click', function () {
            var categories = ['external'];
            ['analytics', 'marketing'].forEach(function (category) { if (allowed(category)) categories.push(category); });
            consent.acceptCategory(categories);
            consent.hide();
        });
        placeholder.append(description, load);
        frame.before(placeholder);
    });
    var settings = document.createElement('button');
    settings.type = 'button';
    settings.className = 'sbs-cookie-settings';
    settings.textContent = spanish ? 'Preferencias de cookies' : 'Cookie settings';
    settings.addEventListener('click', function () { consent.showPreferences(); });
    var footer = document.querySelector('.footer-legal') || document.querySelector('footer');
    if (footer) footer.appendChild(settings);

    consent.run({
        mode: 'opt-in',
        revision: 1,
        disablePageInteraction: false,
        cookie: { name: 'sbs_cookie_consent', domain: '', expiresAfterDays: 182, sameSite: 'Lax' },
        guiOptions: {
            consentModal: { layout: 'bar inline', position: 'bottom', equalWeightButtons: true },
            preferencesModal: { layout: 'box', equalWeightButtons: true }
        },
        onConsent: updateGoogleConsent,
        onChange: function (event) {
            updateGoogleConsent();
            if (event.changedCategories.some(function (category) { return !allowed(category); })) {
                // Reload after saving a withdrawal to unload previously enabled trackers.
                window.location.reload();
            }
        },
        categories: {
            necessary: { enabled: true, readOnly: true },
            analytics: { autoClear: { cookies: cookieRules(/^(_ga|_gid|_gat)/) } },
            marketing: { autoClear: { cookies: cookieRules(/^(_gcl|_fbp|_fbc|_oai|oaiq|calltrk|callrail)/) } },
            external: {}
        },
        language: {
            default: spanish ? 'es' : 'en',
            translations: {
                en: {
                    consentModal: {
                        title: 'Your privacy choices',
                        description: 'We use necessary storage to make this site work. You can also allow analytics and advertising tools. Your choice does not affect contacting us.',
                        acceptAllBtn: 'Accept all',
                        acceptNecessaryBtn: 'Necessary only',
                        showPreferencesBtn: 'Preferences'
                    },
                    preferencesModal: {
                        title: 'Cookie preferences',
                        acceptAllBtn: 'Accept all',
                        acceptNecessaryBtn: 'Necessary only',
                        savePreferencesBtn: 'Save preferences',
                        closeIconLabel: 'Close preferences',
                        sections: [
                            { title: 'Your choice', description: 'Choose which optional tools may run. Change your choice any time using Cookie settings in the footer.' },
                            { title: 'Necessary', description: 'Remembers your privacy choice and supports website features such as sending a consultation request.', linkedCategory: 'necessary' },
                            { title: 'Analytics', description: 'Allows Google Analytics to measure visits and interactions so we can improve this website.', linkedCategory: 'analytics' },
                            { title: 'Advertising', description: 'Allows Google Ads, OpenAI advertising measurement, CallRail, and marketing attribution tools to measure advertising and inquiries.', linkedCategory: 'marketing' },
                            { title: 'External content', description: 'Allows embedded Google Maps to load. You can use maps separately from analytics and advertising.', linkedCategory: 'external' }
                        ]
                    }
                },
                es: {
                    consentModal: {
                        title: 'Sus opciones de privacidad',
                        description: 'Usamos almacenamiento necesario para que este sitio funcione. Puede permitir herramientas de análisis y publicidad. Su elección no afecta la posibilidad de contactarnos.',
                        acceptAllBtn: 'Aceptar todo',
                        acceptNecessaryBtn: 'Solo necesarias',
                        showPreferencesBtn: 'Preferencias'
                    },
                    preferencesModal: {
                        title: 'Preferencias de cookies',
                        acceptAllBtn: 'Aceptar todo',
                        acceptNecessaryBtn: 'Solo necesarias',
                        savePreferencesBtn: 'Guardar preferencias',
                        closeIconLabel: 'Cerrar preferencias',
                        sections: [
                            { title: 'Su elección', description: 'Elija qué herramientas opcionales pueden funcionar. Puede cambiar su elección con el botón de preferencias en el pie de página.' },
                            { title: 'Necesarias', description: 'Recuerda su elección de privacidad y permite funciones como enviar una solicitud de consulta.', linkedCategory: 'necessary' },
                            { title: 'Análisis', description: 'Permite que Google Analytics mida visitas e interacciones para mejorar este sitio.', linkedCategory: 'analytics' },
                            { title: 'Publicidad', description: 'Permite que Google Ads, OpenAI, CallRail y las herramientas de atribución midan la publicidad y las consultas.', linkedCategory: 'marketing' },
                            { title: 'Contenido externo', description: 'Permite cargar Google Maps sin permitir análisis ni publicidad.', linkedCategory: 'external' }
                        ]
                    }
                }
            }
        }
    });
})();
