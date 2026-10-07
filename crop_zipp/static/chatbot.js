/**
 * Crop Advisor Chatbot - Hindi + English, soil report flow, weather, ML prediction
 */
(function() {
    const panel = document.getElementById('chatbotPanel');
    const toggle = document.getElementById('chatbotToggle');
    const messagesEl = document.getElementById('chatbotMessages');
    const inputWrap = document.getElementById('chatInputWrap');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');

    if (!panel || !messagesEl) return;

    let state = 'greeting';
    let soilData = null;  // { N, P, K, ph } from area or manual
    let weatherFetched = false;
    let userCity = '';
    let userLat = null;
    let userLon = null;

    const STATES = {
        greeting: 'greeting',
        soil_has_report: 'soil_has_report',
        soil_no_area: 'soil_no_area',
        soil_manual: 'soil_manual',
        weather_ask: 'weather_ask',
        predicting: 'predicting',
        done: 'done'
    };

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addMessage(text, type) {
        type = type || 'bot';
        const div = document.createElement('div');
        div.className = 'chat-msg ' + type;
        div.textContent = text;
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function addHtmlMessage(html, type) {
        type = type || 'bot';
        const div = document.createElement('div');
        div.className = 'chat-msg ' + type;
        div.innerHTML = html;
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function addOptions(labels, values) {
        const wrap = document.createElement('div');
        wrap.className = 'chat-options';
        labels.forEach((label, i) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'chat-option-btn';
            btn.textContent = label;
            btn.dataset.value = values[i] !== undefined ? String(values[i]) : label;
            wrap.appendChild(btn);
        });
        messagesEl.appendChild(wrap);
        scrollToBottom();
        return wrap;
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'chat-msg bot chatbot-typing';
        div.id = 'chatbotTyping';
        div.innerHTML = '<i class="fas fa-circle"></i> <i class="fas fa-circle"></i> <i class="fas fa-circle"></i>';
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function hideTyping() {
        const el = document.getElementById('chatbotTyping');
        if (el) el.remove();
    }

    function showInput(show) {
        inputWrap.style.display = show ? 'flex' : 'none';
        if (show) chatInput.focus();
    }

    function startChat() {
        state = STATES.greeting;
        soilData = null;
        weatherFetched = false;
        userCity = '';
        userLat = null;
        userLon = null;
        messagesEl.innerHTML = '';

        addMessage('नमस्ते! Hello! 👋 I\'m your Crop Assistant. Kya aapke paas soil testing report hai?', 'bot');
        const opts = addOptions(['Haan (Yes)', 'Nahi (No)'], ['yes', 'no']);
        opts.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', function() {
                opts.remove();
                if (this.dataset.value === 'yes') {
                    state = STATES.soil_has_report;
                    addMessage('Haan, mere paas report hai.', 'user');
                    addMessage('Please enter your soil values: N, P, K, and pH. You can type them like: 40 45 35 6.5 (space separated) or one by one.', 'bot');
                    showInput(true);
                } else {
                    state = STATES.soil_no_area;
                    addMessage('Nahi, mere paas report nahi hai.', 'user');
                    addMessage('Aapka district / state / area kaunsa hai? (e.g. Bihar, Punjab, Maharashtra)', 'bot');
                    showInput(true);
                }
            });
        });
    }

    function handleAreaInput(area) {
        if (!area || !area.trim()) return;
        addMessage(area.trim(), 'user');
        showTyping();
        fetch('/get_soil?state=' + encodeURIComponent(area.trim()))
            .then(r => r.json())
            .then(data => {
                hideTyping();
                const N = data.Nitrogen != null ? data.Nitrogen : data.N;
                const P = data.Phosphorus != null ? data.Phosphorus : data.P;
                const K = data.Potassium != null ? data.Potassium : data.K;
                const ph = data.pH != null ? data.pH : data.ph;
                soilData = { N: N || 45, P: P || 42, K: K || 40, ph: ph || 6.5 };
                addMessage('Aapke area ke hisaab se average soil values use kar rahe hain: N=' + soilData.N + ', P=' + soilData.P + ', K=' + soilData.K + ', pH=' + soilData.ph + '. Ab weather ke liye apna sheher bataiye ya "location" likhein taaki aapki location use ho.', 'bot');
                state = STATES.weather_ask;
                showInput(true);
            })
            .catch(function() {
                hideTyping();
                soilData = { N: 45, P: 42, K: 40, ph: 6.5 };
                addMessage('Default values use kar rahe hain. Ab city naam bataiye ya "location" likhein.', 'bot');
                state = STATES.weather_ask;
                showInput(true);
            });
    }

    function handleManualSoilInput(text) {
        const parts = text.trim().split(/[\s,]+/).map(function(p) { return parseFloat(p); }).filter(function(n) { return !isNaN(n); });
        if (parts.length >= 4) {
            soilData = { N: Math.round(parts[0]), P: Math.round(parts[1]), K: Math.round(parts[2]), ph: Math.min(14, Math.max(0, parts[3])) };
            addMessage('N=' + soilData.N + ', P=' + soilData.P + ', K=' + soilData.K + ', pH=' + soilData.ph, 'user');
            addMessage('Ab weather ke liye apna sheher bataiye ya "location" likhein.', 'bot');
            state = STATES.weather_ask;
            showInput(true);
            return true;
        }
        if (parts.length > 0) {
            addMessage('Please enter all 4 values: N, P, K, pH (e.g. 40 45 35 6.5)', 'bot');
        }
        return false;
    }

    function fetchWeatherAndPredict() {
        if (!soilData) return;
        state = STATES.predicting;
        showInput(false);
        showTyping();

        const payload = {
            N: soilData.N,
            P: soilData.P,
            K: soilData.K,
            ph: soilData.ph
        };
        if (userCity) payload.city = userCity;
        else if (userLat != null && userLon != null) {
            payload.lat = userLat;
            payload.lon = userLon;
        }

        fetch('/chat_predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(function(r) { return r.json().then(function(data) { return { ok: r.ok, data }; }); })
        .then(function(result) {
            hideTyping();
            if (result.ok && result.data.crop) {
                addHtmlMessage('🌾 <strong>Recommended crop: ' + result.data.crop + '</strong><br>Temperature: ' + result.data.temperature + '°C, Humidity: ' + result.data.humidity + '%', 'crop-result');
                addMessage('Koi aur sawal ho to poochhiye, ya form se bhi prediction le sakte hain.', 'bot');
            } else {
                addMessage('Sorry, prediction nahi ho payi. Error: ' + (result.data.error || 'Unknown'), 'bot');
            }
            state = STATES.done;
            showInput(true);
        })
        .catch(function(err) {
            hideTyping();
            addMessage('Network error. Please try again.', 'bot');
            state = STATES.weather_ask;
            showInput(true);
        });
    }

    function handleWeatherInput(text) {
        const t = text.trim().toLowerCase();
        if (t === 'location' || t === 'my location' || t === 'geolocation') {
            addMessage('Use my location', 'user');
            function useCoords(lat, lon) {
                userLat = lat;
                userLon = lon;
                userCity = '';
                hideTyping();
                addMessage('Location mil gayi. Recommendation bana rahe hain...', 'bot');
                fetchWeatherAndPredict();
            }
            function tryIPLocation() {
                addMessage('Network location try kar rahe hain...', 'bot');
                fetch('/get_location_ip')
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.lat != null && data.lon != null) {
                            if (data.city) userCity = data.city;
                            useCoords(data.lat, data.lon);
                        } else {
                            hideTyping();
                            addMessage('Location detect nahi hui. Apna sheher likhein (jaise Mumbai, Delhi).', 'bot');
                        }
                    })
                    .catch(function() {
                        hideTyping();
                        addMessage('Apna sheher likhein (jaise Mumbai, Delhi).', 'bot');
                    });
            }
            if (!navigator.geolocation) {
                showTyping();
                tryIPLocation();
                return;
            }
            showTyping();
            navigator.geolocation.getCurrentPosition(
                function(pos) { useCoords(pos.coords.latitude, pos.coords.longitude); },
                function() {
                    hideTyping();
                    addMessage('GPS access nahi mila. Network location try kar rahe hain...', 'bot');
                    showTyping();
                    tryIPLocation();
                },
                { enableHighAccuracy: false, timeout: 20000, maximumAge: 300000 }
            );
            return;
        }
        if (t.length > 0) {
            userCity = text.trim();
            addMessage(userCity, 'user');
            addMessage('Weather fetch karke recommendation bana rahe hain...', 'bot');
            fetchWeatherAndPredict();
        }
    }

    function onSend() {
        const text = (chatInput.value || '').trim();
        if (!text) return;
        chatInput.value = '';

        if (state === STATES.soil_no_area) {
            handleAreaInput(text);
            return;
        }
        if (state === STATES.soil_has_report) {
            if (handleManualSoilInput(text)) return;
            return;
        }
        if (state === STATES.weather_ask) {
            handleWeatherInput(text);
            return;
        }
        if (state === STATES.done) {
            addMessage(text, 'user');
            addMessage('Nayi recommendation ke liye page reload karein ya form use karein.', 'bot');
        }
    }

    toggle.addEventListener('click', function() {
        const isOpen = panel.classList.toggle('open');
        if (isOpen && messagesEl.children.length === 0) startChat();
    });

    chatSend.addEventListener('click', onSend);
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') onSend();
    });
})();
