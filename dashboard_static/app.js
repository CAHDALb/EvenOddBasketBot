(() => {
    "use strict";

    const state = {
        data: null,
        loading: false,
        signalFilter: "all",
        activeView: "dashboard",
        refreshTimer: null,
    };

    const viewMeta = {
        dashboard: ["REAL-TIME ANALYTICS", "Панель стратегии"],
        signals: ["SIGNAL JOURNAL", "Журнал сигналов"],
        analytics: ["PERFORMANCE BREAKDOWN", "Аналитика результатов"],
        strategies: ["STRATEGY ENGINE", "Стратегия"],
        matches: ["MATCH CONTROL", "Матчи и результаты"],
        bankroll: ["ROI & BANKROLL", "Динамика банка"],
        alerts: ["SYSTEM STATE", "Текущее состояние"],
        settings: ["PUBLIC DASHBOARD", "О панели"],
    };

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function number(value, digits = 0) {
        const parsed = Number(value || 0);
        return new Intl.NumberFormat("ru-RU", {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
        }).format(parsed);
    }

    function signed(value, suffix = "", digits = 2) {
        const parsed = Number(value || 0);
        const sign = parsed > 0 ? "+" : "";
        return `${sign}${number(parsed, digits)}${suffix}`;
    }

    function dateObject(value) {
        const parsed = new Date(value);
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    }

    function formatTime(value) {
        const parsed = dateObject(value);
        return parsed ? parsed.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }) : "—";
    }

    function formatDate(value, withYear = false) {
        const parsed = dateObject(value);
        if (!parsed) return "—";
        return parsed.toLocaleDateString("ru-RU", withYear
            ? { day: "2-digit", month: "2-digit", year: "numeric" }
            : { day: "2-digit", month: "2-digit" });
    }

    function setText(selector, value) {
        const element = $(selector);
        if (element) element.textContent = value;
    }

    function roiClass(value) {
        return Number(value || 0) >= 0 ? "roi-positive" : "roi-negative";
    }

    function resultLabel(signal) {
        if (signal.status === "waiting") return ["waiting", "ОЖИДАЕТ"];
        if (signal.result === "win") return ["win", "WIN"];
        if (signal.result === "lose") return ["lose", "LOSE"];
        return ["", "—"];
    }

    function predictionLabel(value) {
        const prediction = String(value || "odd").toLowerCase();
        return prediction === "even" ? "EVEN" : "ODD";
    }

    function setLoading(isLoading, initial = false) {
        state.loading = isLoading;
        const refresh = $("#refresh-button");
        const overlay = $("#loading-overlay");
        refresh?.classList.toggle("is-loading", isLoading);
        if (initial) overlay?.classList.toggle("is-hidden", !isLoading);
    }

    async function loadData({ initial = false } = {}) {
        if (state.loading) return;
        setLoading(true, initial);

        try {
            const response = await fetch(`/api/dashboard?_=${Date.now()}`, {
                cache: "no-store",
                headers: { Accept: "application/json" },
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            state.data = data;
            renderAll(data);
            scheduleRefresh(data.refresh_seconds);
        } catch (error) {
            console.error("Dashboard data error:", error);
            showNotice("Не удалось обновить данные. Панель повторит попытку автоматически.");
            setSystemState(false, "OFFLINE");
        } finally {
            setLoading(false, initial);
        }
    }

    function scheduleRefresh(seconds) {
        if (state.refreshTimer) clearTimeout(state.refreshTimer);
        const interval = Math.max(15, Number(seconds || window.EOB_CONFIG?.refreshSeconds || 60));
        state.refreshTimer = setTimeout(() => loadData(), interval * 1000);
    }

    function showNotice(message = "") {
        const notice = $("#system-notice");
        if (!notice) return;
        notice.textContent = message;
        notice.classList.toggle("is-hidden", !message);
    }

    function setSystemState(online, source = "") {
        const engine = $("#engine-state");
        const pill = $("#live-pill");
        if (engine) {
            engine.textContent = online ? "ACTIVE" : "OFFLINE";
            engine.className = online ? "online" : "offline";
        }
        if (pill) {
            pill.classList.toggle("offline", !online);
            const label = $("b", pill);
            if (label) label.textContent = online ? "LIVE" : "OFFLINE";
        }
        setText("#status-source", source || "—");
    }

    function renderAll(data) {
        const summary = data.summary || {};
        const system = data.system || {};
        const strategy = data.strategy || {};

        setSystemState(Boolean(system.online), system.source);
        showNotice(system.online ? "" : (system.message || "Источник данных недоступен"));
        setText("#last-updated", formatTime(data.generated_at));
        setText("#status-sync", `${formatDate(data.generated_at, true)} ${formatTime(data.generated_at)}`);
        setText("#status-waiting", number(summary.waiting));
        setText("#about-version", `v${data.version || window.EOB_CONFIG?.version || "—"}`);
        setText("#about-refresh", `${number(data.refresh_seconds)} сек.`);
        setText("#about-timezone", data.timezone || "—");
        setText("#footer-version", `v${data.version || "—"}`);

        renderSummary(summary, strategy);
        renderLineChart($("#roi-chart"), data.roi_history || [], { compact: true });
        renderLineChart($("#strategy-roi-chart"), data.roi_history || [], { compact: false });
        renderLineChart($("#bankroll-roi-chart"), data.roi_history || [], { compact: false });
        renderBarChart($("#bank-chart"), data.bank_daily || [], { compact: true });
        renderBarChart($("#bankroll-bar-chart"), data.bank_daily || [], { compact: false });
        renderHistory(data.recent_signals || []);
        renderMatchTypes(data.match_types || []);
        renderSignalsTable(data.signals || []);
        renderBreakdownTable("#countries-table", data.countries || [], "country");
        renderBreakdownTable("#leagues-table", data.leagues || [], "league");
        renderStrategy(strategy);
        renderWaiting(data.waiting_signals || []);
        renderRecentResults(data.recent_signals || []);
        renderRisk(data.risk || {});
    }

    function renderSummary(summary, strategy) {
        const total = Number(summary.total || 0);
        const wins = Number(summary.wins || 0);
        const loses = Number(summary.loses || 0);
        const finished = wins + loses;
        const winPercent = finished ? (wins / finished) * 100 : 0;
        const losePercent = finished ? (loses / finished) * 100 : 0;
        const roi = Number(summary.roi || 0);

        setText("#total-signals", number(total));
        setText("#total-wins", number(wins));
        setText("#total-loses", number(loses));
        setText("#win-percent", `${number(winPercent, 2)}%`);
        setText("#lose-percent", `${number(losePercent, 2)}%`);
        const winProgress = $("#win-progress");
        const loseProgress = $("#lose-progress");
        if (winProgress) winProgress.style.width = `${winPercent}%`;
        if (loseProgress) loseProgress.style.width = `${losePercent}%`;

        setText("#current-roi", signed(roi, "%"));
        setText("#roi-head", signed(roi, "%"));
        setText("#roi-sample", `${number(finished)} сигналов`);
        ["#current-roi", "#roi-head"].forEach(selector => {
            const element = $(selector);
            if (element) element.className = roi >= 0 ? "roi-positive" : "roi-negative";
        });

        setText("#metric-total", number(total));
        setText("#metric-rate", `${number(strategy.win_rate || 0, 2)}%`);
        setText("#metric-roi", signed(roi, "%"));
        setText("#metric-waiting", number(summary.waiting || 0));
        const metricRoi = $("#metric-roi");
        if (metricRoi) metricRoi.className = roiClass(roi);

        setText("#strategy-rate", `${number(strategy.win_rate || 0, 2)}%`);
        setText("#strategy-name", strategy.name || "Стратегия");
        setText("#strategy-sample", `${number(strategy.sample || 0)} завершено`);
        const donut = $("#strategy-donut");
        if (donut) donut.style.setProperty("--value", `${Math.max(0, Math.min(100, Number(strategy.win_rate || 0))) * 3.6}deg`);

        $("#alert-dot")?.classList.toggle("is-active", Number(summary.waiting || 0) > 0);
    }

    function renderLineChart(container, points, options = {}) {
        if (!container) return;
        container.innerHTML = "";
        const values = points.map(point => Number(point.roi || 0));
        if (!values.length) {
            container.innerHTML = '<div class="chart-empty">Пока нет завершённых сигналов</div>';
            return;
        }

        const compact = Boolean(options.compact);
        const width = compact ? 760 : 1100;
        const height = compact ? 210 : 330;
        const margin = compact
            ? { top: 12, right: 16, bottom: 28, left: 45 }
            : { top: 18, right: 24, bottom: 40, left: 56 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        let min = Math.min(0, ...values);
        let max = Math.max(0, ...values);
        const range = max - min || 1;
        min -= range * 0.14;
        max += range * 0.14;

        const x = index => margin.left + (values.length === 1 ? innerWidth / 2 : index / (values.length - 1) * innerWidth);
        const y = value => margin.top + (max - value) / (max - min) * innerHeight;
        const coords = values.map((value, index) => [x(index), y(value)]);
        const linePath = coords.map(([cx, cy], index) => `${index ? "L" : "M"}${cx.toFixed(2)},${cy.toFixed(2)}`).join(" ");
        const areaPath = `${linePath} L${x(values.length - 1)},${margin.top + innerHeight} L${x(0)},${margin.top + innerHeight} Z`;
        const gradientId = `roiAreaGradient-${container.id}`;

        const grids = Array.from({ length: 5 }, (_, index) => {
            const value = max - (index / 4) * (max - min);
            const gy = y(value);
            return `<line class="chart-grid-line" x1="${margin.left}" x2="${width - margin.right}" y1="${gy}" y2="${gy}"/><text class="chart-label" x="${margin.left - 8}" y="${gy + 3}" text-anchor="end">${signed(value, "%", 0)}</text>`;
        }).join("");

        const dateIndexes = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])];
        const dateLabels = dateIndexes.map(index => `<text class="chart-label" x="${x(index)}" y="${height - 5}" text-anchor="${index === 0 ? "start" : index === points.length - 1 ? "end" : "middle"}">${formatDate(points[index].datetime)}</text>`).join("");
        const last = coords[coords.length - 1];

        container.innerHTML = `
            <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Изменение ROI">
                <defs>
                    <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#10d6e8" stop-opacity="0.34"/>
                        <stop offset="100%" stop-color="#10d6e8" stop-opacity="0.01"/>
                    </linearGradient>
                </defs>
                ${grids}
                <line class="chart-axis-line" x1="${margin.left}" x2="${width - margin.right}" y1="${y(0)}" y2="${y(0)}"/>
                <path d="${areaPath}" fill="url(#${gradientId})"/>
                <path class="chart-line" d="${linePath}"/>
                <circle class="chart-point" cx="${last[0]}" cy="${last[1]}" r="5"><title>${signed(values.at(-1), "%")} · ${formatDate(points.at(-1).datetime, true)}</title></circle>
                ${dateLabels}
            </svg>`;
    }

    function renderBarChart(container, points, options = {}) {
        if (!container) return;
        container.innerHTML = "";
        if (!points.length) {
            container.innerHTML = '<div class="chart-empty">Пока нет данных за 30 дней</div>';
            return;
        }

        const compact = Boolean(options.compact);
        const width = compact ? 900 : 1180;
        const height = compact ? 245 : 360;
        const margin = compact
            ? { top: 12, right: 14, bottom: 38, left: 45 }
            : { top: 18, right: 20, bottom: 47, left: 58 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        const values = points.map(point => Number(point.value || 0));
        const absolute = Math.max(1, ...values.map(Math.abs));
        const max = absolute * 1.18;
        const min = -max;
        const y = value => margin.top + (max - value) / (max - min) * innerHeight;
        const zeroY = y(0);
        const step = innerWidth / points.length;
        const barWidth = Math.max(4, step * 0.60);
        const gradientSuffix = container.id;

        const grids = [-1, -.5, 0, .5, 1].map(multiplier => {
            const value = max * multiplier;
            const gy = y(value);
            return `<line class="chart-grid-line" x1="${margin.left}" x2="${width - margin.right}" y1="${gy}" y2="${gy}"/><text class="chart-label" x="${margin.left - 8}" y="${gy + 3}" text-anchor="end">${signed(value, "", 0)}</text>`;
        }).join("");

        const bars = points.map((point, index) => {
            const value = Number(point.value || 0);
            const bx = margin.left + index * step + (step - barWidth) / 2;
            const by = value >= 0 ? y(value) : zeroY;
            const bh = Math.max(1, Math.abs(y(value) - zeroY));
            const className = value >= 0 ? "bar-positive" : "bar-negative";
            const gradient = value >= 0 ? `positiveBar-${gradientSuffix}` : `negativeBar-${gradientSuffix}`;
            const showLabel = index % 5 === 0 || index === points.length - 1;
            const label = showLabel ? `<text class="chart-label" x="${bx + barWidth / 2}" y="${height - 9}" text-anchor="middle">${formatDate(point.date)}</text>` : "";
            return `<rect class="${className}" style="fill:url(#${gradient})" x="${bx}" y="${by}" width="${barWidth}" height="${bh}" rx="2"><title>${formatDate(point.date, true)}: ${signed(value, "%")}</title></rect>${label}`;
        }).join("");

        container.innerHTML = `
            <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Изменение банка за 30 дней">
                <defs>
                    <linearGradient id="positiveBar-${gradientSuffix}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#38f2f2"/><stop offset="100%" stop-color="#067b98"/></linearGradient>
                    <linearGradient id="negativeBar-${gradientSuffix}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ff9714"/><stop offset="100%" stop-color="#c94300"/></linearGradient>
                </defs>
                <style>.bar-positive{fill:url(#positiveBar-${gradientSuffix})}.bar-negative{fill:url(#negativeBar-${gradientSuffix})}</style>
                ${grids}
                <line class="chart-axis-line" x1="${margin.left}" x2="${width - margin.right}" y1="${zeroY}" y2="${zeroY}"/>
                ${bars}
            </svg>`;
    }

    function renderHistory(signals) {
        const container = $("#history-list");
        if (!container) return;
        if (!signals.length) {
            container.innerHTML = '<div class="empty-state">История появится после завершения первого сигнала</div>';
            return;
        }
        container.innerHTML = signals.slice(0, 10).map(signal => {
            const [resultClass, resultText] = resultLabel(signal);
            const pick = predictionLabel(signal.prediction);
            return `<div class="history-row">
                <span class="history-time">${formatTime(signal.datetime)}</span>
                <strong class="history-pick ${pick === "ODD" ? "odd" : ""}">${pick}</strong>
                <span class="history-match" title="${escapeHtml(signal.match)}">${escapeHtml(signal.match)}</span>
                <span class="result-badge ${resultClass}">${resultClass === "win" ? "✓" : "×"} ${resultText}</span>
            </div>`;
        }).join("");
    }

    function typeIcon(key) {
        if (key === "women") return "♀";
        if (key === "youth") return "♙";
        return "♟";
    }

    function typeCards(items) {
        return items.map(item => `<article class="type-card">
            <div class="type-title"><span class="type-icon">${typeIcon(item.key)}</span>${escapeHtml(item.label)}</div>
            <div class="type-values">
                <div><span>Сигналов</span><strong>${number(item.total)}</strong></div>
                <div><span>WIN / LOSE</span><strong><i class="win-number">${number(item.wins)}</i> / <i class="lose-number">${number(item.loses)}</i></strong></div>
                <div><span>Проходимость</span><strong>${number(item.win_rate, 2)}%</strong></div>
                <div><span>ROI</span><strong class="${roiClass(item.roi)}">${signed(item.roi)}</strong></div>
            </div>
        </article>`).join("");
    }

    function renderMatchTypes(items) {
        const content = items.length ? typeCards(items) : '<div class="empty-state">Нет завершённых сигналов</div>';
        const main = $("#match-types-grid");
        const analytics = $("#analytics-types");
        if (main) main.innerHTML = content;
        if (analytics) analytics.innerHTML = content;
    }

    function renderSignalsTable(signals) {
        const tbody = $("#signals-table");
        if (!tbody) return;
        const filtered = signals.filter(signal => {
            if (state.signalFilter === "all") return true;
            if (state.signalFilter === "waiting") return signal.status === "waiting";
            return signal.result === state.signalFilter;
        });

        if (!filtered.length) {
            tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state">Нет сигналов в выбранном разделе</div></td></tr>';
            return;
        }

        tbody.innerHTML = filtered.map(signal => {
            const [resultClass, resultText] = resultLabel(signal);
            const link = signal.match_url ? `<a href="${escapeHtml(signal.match_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(signal.match)}</a>` : escapeHtml(signal.match);
            return `<tr>
                <td>${formatDate(signal.signal_datetime, true)}<br><span class="history-time">${formatTime(signal.signal_datetime)}</span></td>
                <td class="match-cell"><strong>${link}</strong><span>${escapeHtml(signal.country)} · ${escapeHtml(signal.league)}</span></td>
                <td>${escapeHtml(signal.match_type_label)}</td>
                <td><strong class="history-pick ${predictionLabel(signal.prediction) === "ODD" ? "odd" : ""}">${predictionLabel(signal.prediction)}</strong></td>
                <td><span class="status-chip ${resultClass}">${resultText}</span></td>
                <td class="${roiClass(signal.roi)}">${signal.status === "finished" ? signed(signal.roi) : "—"}</td>
            </tr>`;
        }).join("");
    }

    function renderBreakdownTable(selector, items, field) {
        const tbody = $(selector);
        if (!tbody) return;
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state">Нет завершённых сигналов</div></td></tr>';
            return;
        }
        tbody.innerHTML = items.map(item => `<tr>
            <td title="${escapeHtml(item.key)}">${escapeHtml(item.key)}</td>
            <td>${number(item.total)}</td>
            <td><span class="win-number">${number(item.wins)}</span> / <span class="lose-number">${number(item.loses)}</span></td>
            <td>${number(item.win_rate, 2)}%</td>
            <td class="${roiClass(item.roi)}">${signed(item.roi)}</td>
        </tr>`).join("");
    }

    function renderStrategy(strategy) {
        setText("#detail-strategy-name", strategy.name || "Стратегия");
        setText("#detail-sample", number(strategy.sample || 0));
        setText("#detail-wl", `${number(strategy.wins || 0)} / ${number(strategy.loses || 0)}`);
        setText("#detail-rate", `${number(strategy.win_rate || 0, 2)}%`);
        setText("#detail-roi", signed(strategy.roi || 0));
        const detailRoi = $("#detail-roi");
        if (detailRoi) detailRoi.className = roiClass(strategy.roi);
        const streak = strategy.streak || {};
        setText("#detail-streak", streak.length ? `${streak.length} ${String(streak.result || "").toUpperCase()}` : "Нет серии");
    }

    function renderWaiting(signals) {
        const container = $("#waiting-grid");
        if (!container) return;
        if (!signals.length) {
            container.innerHTML = '<div class="empty-state">Сейчас нет матчей в ожидании результата</div>';
            return;
        }
        container.innerHTML = signals.map(signal => `<article class="waiting-card">
            <strong>${escapeHtml(signal.match)}</strong>
            <span>${escapeHtml(signal.country)} · ${escapeHtml(signal.league)}</span>
            <span>Сигнал: ${formatDate(signal.signal_datetime, true)} ${formatTime(signal.signal_datetime)}</span>
            ${signal.match_url ? `<a href="${escapeHtml(signal.match_url)}" target="_blank" rel="noopener noreferrer">Открыть матч ↗</a>` : ""}
        </article>`).join("");
    }

    function renderRecentResults(signals) {
        const tbody = $("#matches-results-table");
        if (!tbody) return;
        if (!signals.length) {
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state">Пока нет завершённых результатов</div></td></tr>';
            return;
        }
        tbody.innerHTML = signals.map(signal => {
            const [resultClass, resultText] = resultLabel(signal);
            return `<tr><td>${formatDate(signal.datetime, true)} ${formatTime(signal.datetime)}</td><td>${escapeHtml(signal.match)}</td><td><span class="status-chip ${resultClass}">${resultText}</span></td><td>${signal.final_total ?? "—"}</td><td class="${roiClass(signal.roi)}">${signed(signal.roi)}</td></tr>`;
        }).join("");
    }

    function renderRisk(risk) {
        setText("#risk-title", risk.title || "Оценка формы");
        setText("#risk-message", risk.message || "Нет данных");
        const card = $("#risk-card");
        if (card) {
            card.classList.remove("positive", "warning", "danger", "neutral");
            card.classList.add(risk.level || "neutral");
        }
    }

    function switchView(view, updateHash = true) {
        if (!viewMeta[view]) view = "dashboard";
        state.activeView = view;
        $$(".nav-item").forEach(button => button.classList.toggle("is-active", button.dataset.view === view));
        $$("[data-view-panel]").forEach(panel => panel.classList.toggle("is-active", panel.dataset.viewPanel === view));
        setText("#section-eyebrow", viewMeta[view][0]);
        setText("#section-title", viewMeta[view][1]);
        $("#sidebar")?.classList.remove("is-open");
        if (updateHash && location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
        requestAnimationFrame(() => {
            if (!state.data) return;
            if (["dashboard", "strategies", "bankroll"].includes(view)) {
                renderLineChart($("#roi-chart"), state.data.roi_history || [], { compact: true });
                renderLineChart($("#strategy-roi-chart"), state.data.roi_history || [], { compact: false });
                renderLineChart($("#bankroll-roi-chart"), state.data.roi_history || [], { compact: false });
                renderBarChart($("#bank-chart"), state.data.bank_daily || [], { compact: true });
                renderBarChart($("#bankroll-bar-chart"), state.data.bank_daily || [], { compact: false });
            }
        });
    }

    function updateClock() {
        const now = new Date();
        setText("#clock", now.toLocaleTimeString("ru-RU"));
        setText("#clock-date", now.toLocaleDateString("ru-RU", { day: "2-digit", month: "long", year: "numeric", weekday: "long" }));
    }

    function bindEvents() {
        $$(".nav-item").forEach(button => button.addEventListener("click", () => switchView(button.dataset.view)));
        $("#refresh-button")?.addEventListener("click", () => loadData());
        $("#menu-toggle")?.addEventListener("click", () => $("#sidebar")?.classList.toggle("is-open"));
        $$("[data-signal-filter]").forEach(button => button.addEventListener("click", () => {
            state.signalFilter = button.dataset.signalFilter;
            $$("[data-signal-filter]").forEach(item => item.classList.toggle("is-active", item === button));
            renderSignalsTable(state.data?.signals || []);
        }));
        window.addEventListener("hashchange", () => switchView(location.hash.slice(1), false));
        window.addEventListener("resize", debounce(() => {
            if (!state.data) return;
            renderLineChart($("#roi-chart"), state.data.roi_history || [], { compact: true });
            renderLineChart($("#strategy-roi-chart"), state.data.roi_history || [], { compact: false });
            renderLineChart($("#bankroll-roi-chart"), state.data.roi_history || [], { compact: false });
            renderBarChart($("#bank-chart"), state.data.bank_daily || [], { compact: true });
            renderBarChart($("#bankroll-bar-chart"), state.data.bank_daily || [], { compact: false });
        }, 180));
        document.addEventListener("keydown", event => {
            if (event.key === "Escape") $("#sidebar")?.classList.remove("is-open");
        });
    }

    function debounce(fn, delay) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    }

    function init() {
        bindEvents();
        updateClock();
        setInterval(updateClock, 1000);
        switchView(location.hash.slice(1) || "dashboard", false);
        loadData({ initial: true });
    }

    document.addEventListener("DOMContentLoaded", init);
})();
