import {
    validateManifest
} from './submission.js';
const $ = s => document.querySelector(s),
    $$ = s => [...document.querySelectorAll(s)];
const escape = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
} [c]));
const colors = {
    'Frontier API': '#77a8c8',
    'Streaming API': '#267989',
    'Open non-streaming': '#c5a853',
    'Open streaming': '#cc7950'
};
const axisNames = ['Skill', 'Trust in AI', 'Pace', 'Alert tolerance', 'Interruption'];
const levels = [
    ['Novice', 'Intermediate', 'Expert'],
    ['Low', 'Medium', 'High'],
    ['Cautious', 'Balanced', 'Fast'],
    ['Strict', 'Balanced', 'Broad'],
    ['Step-by-step', 'Balanced', 'Avoid']
];
let episode, playing = false,
    elapsed = 0,
    last = 0,
    lastTick = -1,
    lastMessages = '',
    audio = new Audio(),
    activeAudio = '',
    muted = false,
    rate = 1,
    images = new Map(),
    generation = 0,
    view = 'combined';
const canvas = $('#scene'),
    ctx = canvas.getContext('2d');

function clock(t) {
    return `${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`
}

function fallbackTimeline(e) {
    let start = 0;
    return {
        duration: (e.ticks + 1) * .6,
        segments: Array.from({
            length: e.ticks + 1
        }, (_, tick) => ({
            tick,
            start: tick * .6,
            duration: .6
        }))
    }
}
async function loadEpisode(id) {
    const request = ++generation;
    pause();
    const loaded = await fetch(`data/${id}.json`, {
        cache: 'no-cache'
    }).then(r => r.json());
    if (request !== generation) return;
    episode = loaded;
    canvas.width = id === 'mobile' ? 780 : 1320;
    canvas.height = id === 'mobile' ? 1000 : 740;
    $('.playback').classList.toggle('mobile', id === 'mobile');
    $('#presentation-note').textContent = 'Original dialogue with synthetic speech; playback is time-expanded. ' +
        (episode.presentation?.description ?? 'Visual observations follow the recorded simulation ticks.');
    episode.playback ??= fallbackTimeline(episode);
    elapsed = 0;
    lastTick = -1;
    lastMessages = '';
    images.clear();
    $('#task').textContent = episode.task;
    $('#assistant').textContent = episode.model;
    $('#persona').textContent = episode.persona;
    $('#record-link').href = `data/${id}.json`;
    $('#video-link').href = `assets/media/${id}.mp4`;
    $('#captions-link').href = `assets/media/${id}.vtt`;
    view = 'combined';
    $$('[data-view]').forEach(b => {
        b.classList.toggle('active', b.dataset.view === view);
        b.hidden = id === 'mobile';
    });
    $$('.tabs button').forEach(b => {
        b.classList.toggle('active', b.dataset.episode === id);
        b.setAttribute('aria-selected', String(b.dataset.episode === id))
    });
    $('#persona-axes').innerHTML = episode.axes.map((n, i) => `<div class="axis"><div class="axis-label">${axisNames[i]}<span>${levels[i][n-1]}</span></div><div class="axis-level">${[1,2,3].map(x=>`<i class="${x===n?'on':''}"></i>`).join('')}</div></div>`).join('');
    $('#milestones').innerHTML = episode.milestones.map(m => `<div class="milestone" data-tick="${m.tick}"><i></i>${escape(m.label)}</div>`).join('');
    $('#events').innerHTML = episode.events.map((e, i) => `<button class="event-chip" data-index="${i}" title="Scheduled at tick ${e.tick}${e.detail ? ': '+escape(e.detail):''}">${escape(e.label)}<small>Scheduled</small></button>`).join('');
    $$('#events button').forEach(b => b.onclick = () => seekTick(episode.events[+b.dataset.index].tick));
    $('#episode-score').textContent = episode.quality.overall == null ? 'Rubric details' : `${(episode.quality.overall*100).toFixed(1)} / 100 overall ↗`;
    const names = ['Factual grounding', 'Situational relevance', 'Actionable guidance', 'User intent uptake', 'Guidance conciseness'];
    $('#rubric-scores').innerHTML = Object.entries(episode.quality.categories).map(([k, v], i) => `<div class="rubric">${names[i]}<strong>${(v*100).toFixed(1)}</strong><div class="rubric-track"><i style="width:${v*100}%"></i></div></div>`).join('');
    draw();
}

function pause() {
    playing = false;
    audio.pause();
    $('#play').textContent = '▶';
    $('#play').setAttribute('aria-label', 'Play episode')
}

function play() {
    if (!episode) return;
    if (elapsed >= episode.playback.duration) elapsed = 0;
    playing = true;
    last = performance.now();
    $('#play').textContent = 'Ⅱ';
    $('#play').setAttribute('aria-label', 'Pause episode');
    requestAnimationFrame(loop)
}

function loop(now) {
    if (!playing) return;
    elapsed += (now - last) / 1000 * rate;
    last = now;
    if (elapsed >= episode.playback.duration) {
        elapsed = episode.playback.duration;
        pause()
    }
    draw();
    if (playing) requestAnimationFrame(loop)
}

function seekTick(t) {
    elapsed = episode.playback.segments.find(s => s.tick >= t)?.start ?? 0;
    audio.pause();
    activeAudio = '';
    draw()
}

function getImage(t) {
    const presentation = episode.presentation;
    const n = Math.min(t, (presentation?.frameCount ?? episode.frameCount ?? episode.ticks) - 1);
    let url = `${presentation?.frameRoot ?? 'assets/media/'+episode.id}/${String(n).padStart(4,'0')}.jpg`;
    const gesture = presentation?.gestures?.[String(t)];
    if (gesture) {
        const seg = episode.playback.segments.find(s => s.tick === t);
        const i = Math.max(0, Math.min(gesture.frames.length - 1, Math.floor((elapsed - seg.start) * gesture.fps)));
        url = gesture.frames[i];
        for (const next of gesture.frames.slice(i + 1, i + 6)) {
            if (!images.has(next)) {
                const im = new Image();
                im.src = next;
                images.set(next, im);
            }
        }
    }
    if (!images.has(url)) {
        const im = new Image();
        im.src = url;
        images.set(url, im)
    }
    return images.get(url)
}

function contain(im, sx, sy, sw, sh, x, y, w, h) {
    let scale = Math.min(w / sw, h / sh),
        dw = sw * scale,
        dh = sh * scale;
    ctx.drawImage(im, sx, sy, sw, sh, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)
}

function renderFrame(t) {
    const im = getImage(t),
        gen = generation;
    if (!im.complete) {
        im.onload = () => {
            if (gen === generation && t === lastTick) renderFrame(t)
        };
        return
    }
    ctx.fillStyle = '#f4f6fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let n = 1; n < 4; n++) getImage(Math.min(t + n, episode.ticks));
    if (episode.id === 'mobile') {
        const gesture = episode.presentation?.gestures?.[String(t)];
        if (gesture) contain(im, 0, 0, im.width, im.height, 144, 30, 492, 940);
        else contain(im, 0, 0, im.width, im.height, 168, 54, 412, 892);
    } else {
        const c = episode.presentation?.crops ?? episode.crops ?? (episode.id === 'cooking' ? {
            main: [521, 26, 521, 370],
            context: [0, 26, 520, 370]
        } : {
            main: [0, 24, 640, 456],
            context: [640, 24, 480, 456]
        });
        if (view !== 'combined') {
            contain(im, ...(view === 'map' ? c.context : c.main), 30, 60, 1260, 650);
            ctx.fillStyle = '#536882';
            ctx.font = '20px "DM Sans", sans-serif';
            ctx.fillText(view === 'map' ? 'Top-down view' : 'Egocentric view', 30, 36);
            return;
        }
        ctx.fillStyle = '#fff';
        ctx.fillRect(20, 90, 630, 556);
        ctx.fillRect(670, 90, 630, 556);
        contain(im, ...c.main, 26, 130, 618, 480);
        contain(im, ...c.context, 676, 130, 618, 480);
        ctx.fillStyle = '#536882';
        ctx.font = '20px "DM Sans",sans-serif';
        ctx.fillText('Egocentric view', 38, 120);
        ctx.fillText('Top-down view', 688, 120);
        ctx.strokeStyle = '#dbe2ed';
        ctx.lineWidth = 1;
        ctx.strokeRect(20, 90, 630, 556);
        ctx.strokeRect(670, 90, 630, 556);
    }
}

function draw() {
    if (!episode) return;
    const segments = episode.playback.segments;
    let seg = segments.find(s => elapsed >= s.start && elapsed < s.start + s.duration) ?? segments.at(-1),
        t = seg.tick;
    $('#seek').value = elapsed / episode.playback.duration * 100;
    $('#time').textContent = `${clock(elapsed)} / ${clock(episode.playback.duration)}`;
    $('#clock').textContent = `TICK ${String(t).padStart(3,'0')}`;
    if (t !== lastTick) {
        renderFrame(t);
        lastTick = t;
        const a = episode.actions.filter(a => a.start <= t).at(-1);
        $('#action').textContent = a?.text ?? 'Observing the environment';
        $$('.milestone').forEach(x => x.classList.toggle('done', t >= +x.dataset.tick));
        $$('.event-chip').forEach((x, i) => {
            const e = episode.events[i];
            x.classList.toggle('fired', t >= e.tick);
            let status = t < e.tick ? 'Scheduled' : 'Triggered';
            if (e.kind === 'error' && e.detected && t >= (e.detectedAt ?? e.end)) status = 'Flag credited';
            if (e.answeredAt != null && t >= e.answeredAt) status = 'Answered';
            if (e.alertAt != null && t >= e.alertAt) status = 'Alert delivered';
            if (e.kind === 'plan_change' && t >= e.end) status = 'Goal revised';
            x.classList.toggle('resolved', !['Scheduled', 'Triggered'].includes(status));
            x.querySelector('small').textContent = status;
        });
        const ev = episode.events.filter(e => t >= e.tick && t < e.tick + 4).at(-1);
        $('#event-overlay').innerHTML = ev ? `<div class="event-flash">◆ &nbsp; Scheduled event: ${escape(ev.label)}</div>` : '';
    }
    if (episode.id === 'mobile' && t === lastTick) renderFrame(t);
    const ds = episode.dialogue.filter(d => d.start != null ? d.start <= elapsed : d.tick <= t),
        key = ds.length + ':' + (ds.at(-1)?.start ?? '');
    if (key !== lastMessages) {
        $('#dialogue').innerHTML = ds.length ? ds.map(d => `<div class="message ${d.speaker}"><small>${d.speaker==='assistant'?escape(episode.model):'Simulated user'} · tick ${d.tick}</small>${escape(d.text)}</div>`).join('') : '<div class="waiting">No utterances yet.</div>';
        $('#dialogue').scrollTop = $('#dialogue').scrollHeight;
        lastMessages = key;
    }
    const lastResponseTick = ds.filter(d => d.speaker === 'assistant').at(-1)?.tick ?? -1;
    const round = episode.quality.rounds.filter(r => r.tick <= lastResponseTick).at(-1),
        shorts = ['Grounding', 'Relevance', 'Guidance', 'Intent', 'Conciseness'];
    $('#turn-dimensions').innerHTML = round ? Object.entries(round.categories).map(([k, v], i) => `<span class="verdict ${v==null?'na':v===1?'pass':v===0?'fail':'mixed'}" title="${v==null?'Not applicable':v===1?'All applicable rubric items pass':v===0?'At least one applicable item fails':'Judges differ'}">${v==null?'—':v===1?'✓':v===0?'×':'◐'} ${shorts[i]}</span>`).join('') : 'Evaluation appears as the assistant responds.';
    $('#inspect-grade').disabled = !round;
    const speaking = ds.find(d => d.audio && elapsed >= d.start && elapsed < d.start + d.duration);
    if (speaking && playing && !muted) {
        if (activeAudio !== speaking.audio) {
            audio.src = speaking.audio;
            audio.currentTime = Math.max(0, elapsed - speaking.start);
            audio.playbackRate = rate;
            audio.play().catch(() => {});
            activeAudio = speaking.audio
        } else if (audio.paused) {
            audio.currentTime = Math.max(0, elapsed - speaking.start);
            audio.play().catch(() => {})
        }
    } else {
        audio.pause();
        activeAudio = ''
    }
}
$('#inspect-grade').onclick = () => {
    pause();
    const lastResponseTick = episode.dialogue.filter(d => d.speaker === 'assistant' && d.start <= elapsed).at(-1)?.tick ?? -1;
    const r = episode.quality.rounds.filter(r => r.tick <= lastResponseTick).at(-1);
    if (!r) return;
    $('#grade-evidence').innerHTML = `<p>Tick ${r.tick} · Round score ${(r.score*100).toFixed(1)}/100. These are stored judge assessments, not human annotations.</p>` + r.evidence.map(x => `<article><b>${escape(x.id)} · ${x.pass===true?'Pass':x.pass===false?'Fail':'Not applicable'}${x.judgeIndex!=null?' · Judge '+(x.judgeIndex+1):''}</b><p>${escape(x.reason)}</p></article>`).join('');
    $('#grade-dialog').showModal()
};
$('#close-grade').onclick = () => $('#grade-dialog').close();
$$('[data-view]').forEach(b => b.onclick = () => {
    view = b.dataset.view;
    $$('[data-view]').forEach(x => x.classList.toggle('active', x === b));
    renderFrame(Math.max(0, lastTick));
});
$('#watch-film').onclick = () => {
    pause();
    const film = $('#film');
    film.src = episode.media + '?v=20261001';
    film.poster = episode.poster + '?v=20261001';
    film.innerHTML = `<track kind="captions" src="assets/media/${episode.id}.vtt" srclang="en" label="English transcript">`;
    $('#film-title').textContent = `${episode.engine} · ${episode.model}`;
    $('#film-dialog').showModal();
    film.play().catch(() => {});
};
$('#close-film').onclick = () => {
    $('#film').pause();
    $('#film-dialog').close();
};
$('#film-dialog').onclose = () => $('#film').pause();
$('#share-moment').onclick = async () => {
    const url = new URL(location.href);
    url.search = '';
    url.searchParams.set('episode', episode.id);
    url.searchParams.set('tick', Math.max(0, lastTick));
    url.hash = 'experience';
    try {
        await navigator.clipboard.writeText(url.href);
        $('#share-moment').textContent = 'Link copied ✓';
        setTimeout(() => {
            $('#share-moment').textContent = 'Copy moment link';
        }, 2200);
    } catch {
        $('#share-fallback').hidden = false;
        $('#share-fallback').value = url.href;
        $('#share-fallback').select();
    }
};
document.addEventListener('visibilitychange', () => {
    if (document.hidden) pause();
});
$('#play').onclick = () => playing ? pause() : play();
$('#seek').oninput = e => {
    elapsed = +e.target.value / 100 * episode.playback.duration;
    audio.pause();
    activeAudio = '';
    draw()
};
$('#mute').onclick = () => {
    muted = !muted;
    audio.muted = muted;
    $('#mute').textContent = muted ? 'Sound off' : 'Sound on'
};
$('#speed').onchange = e => {
    rate = +e.target.value;
    audio.playbackRate = rate
};
$$('[data-episode]').forEach(b => b.onclick = () => loadEpisode(b.dataset.episode));
$$('[data-jump]').forEach(b => b.onclick = async () => {
    if (episode.id !== 'cooking') await loadEpisode('cooking');
    seekTick(+b.dataset.jump);
    $('#experience').scrollIntoView({
        behavior: 'smooth'
    });
    play()
});
let board, engine = 'overall',
    sort = 'success',
    family = null,
    search = '',
    selected = '';

function metrics(m) {
    return engine === 'overall' ? m.overall : m.engines[engine]
}

function models() {
    return board.models.filter(m => (!family || family === m.family) && m.model.toLowerCase().includes(search.toLowerCase())).sort((a, b) => metrics(b)[sort] - metrics(a)[sort])
}

function drawBoard() {
    const ms = models();
    $('#leaderboard-table tbody').innerHTML = ms.map(m => {
        const s = metrics(m);
        return `<tr class="${selected===m.model?'selected':''}" data-model="${escape(m.model)}"><td>${escape(m.model)}<small><span style="color:${colors[m.family]}">●</span> ${m.family}</small></td><td>${s.success.toFixed(1)}</td><td>${s.recall.toFixed(1)}</td><td class="quality">${s.quality.toFixed(1)}</td><td><span class="profile" title="${Object.entries(s.rubrics).map(([k,v])=>`${board.categories[k]}: ${v.toFixed(1)}`).join('; ')}">${Object.entries(s.rubrics).map(([k,v])=>`<i style="height:${Math.max(2,v*.23)}px" title="${board.categories[k]}: ${v.toFixed(1)}"></i>`).join('')}</span></td></tr>`
    }).join('');
    const svg = $('#scatter'),
        xmax = Math.max(60, Math.ceil(Math.max(...board.models.map(m => metrics(m).success)) / 20) * 20),
        xs = 685 / xmax;
    let html = '';
    for (let n = 0; n <= 100; n += 20) {
        const y = 385 - n * 3.35;
        html += `<line x1="65" x2="750" y1="${y}" y2="${y}" stroke="#dce2dc"/><text x="50" y="${y+4}" text-anchor="end">${n}</text>`
    }
    for (let n = 0; n <= xmax; n += 10) html += `<text x="${65+n*xs}" y="408" text-anchor="middle">${n}</text>`;
    html += '<text x="410" y="436" text-anchor="middle">In-time task success (%) →</text><text transform="translate(17 230) rotate(-90)" text-anchor="middle">Interaction quality (%) →</text>';
    // Collision-aware labels; every model remains named in the table and accessible on focus.
    const occupied = [],
        pts = ms.map(m => ({
            x: 65 + metrics(m).success * xs,
            y: 385 - metrics(m).quality * 3.35
        }));
    for (const m of ms) {
        const s = metrics(m),
            x = 65 + s.success * xs,
            y = 385 - s.quality * 3.35;
        const short = m.model.replace('-Thinking', '').replace('Qwen3-Omni-30B', 'Qwen3-Omni'),
            w = short.length * 5.4;
        const candidates = [];
        for (const dy of [-10, 18, -28, 36, -46, 54])
            for (const dx of [10, -w - 10]) {
                const b = {
                    x: x + dx,
                    y: y + dy,
                    w,
                    h: 14
                };
                let cost = Math.abs(dy) * .3 + (dx < 0 ? 1 : 0);
                for (const p of occupied) {
                    let iw = Math.max(0, Math.min(b.x + w, p.x + p.w) - Math.max(b.x, p.x)),
                        ih = Math.max(0, Math.min(b.y + 3, p.y + 3) - Math.max(b.y - 14, p.y - 14));
                    cost += iw * ih * 10
                }
                for (const p of pts)
                    if (p.x > b.x - 7 && p.x < b.x + w + 7 && p.y > b.y - 16 && p.y < b.y + 7) cost += 2000;
                if (b.x < 65 || b.x + w > 757 || b.y < 20 || b.y > 382) cost += 100000;
                candidates.push({
                    ...b,
                    cost
                })
            }
        candidates.sort((a, b) => a.cost - b.cost);
        const pos = candidates[0];
        occupied.push(pos);
        html += `<g class="point" tabindex="0" data-model="${escape(m.model)}" aria-label="${escape(m.model)}, success ${s.success.toFixed(1)}, quality ${s.quality.toFixed(1)}"><line x1="${x}" y1="${y}" x2="${pos.x>x?pos.x:pos.x+w}" y2="${pos.y-4}" stroke="${colors[m.family]}" opacity=".4"/><circle cx="${x}" cy="${y}" r="6" fill="${colors[m.family]}" stroke="white" stroke-width="1.5"/><text x="${pos.x}" y="${pos.y}">${escape(short)}</text></g>`
    }
    svg.innerHTML = html;
    $$('#scatter .point').forEach(p => {
        const show = () => {
            const m = board.models.find(m => m.model === p.dataset.model),
                s = metrics(m);
            $('#chart-tip').textContent = `${m.model} — Success ${s.success.toFixed(1)}% · Quality ${s.quality.toFixed(1)}% · Recall ${s.recall.toFixed(1)}%`
        };
        p.onmouseenter = show;
        p.onfocus = show;
        p.onclick = () => {
            selected = p.dataset.model;
            drawBoard()
        };
        p.onkeydown = e => {
            if (e.key === 'Enter') {
                selected = p.dataset.model;
                drawBoard()
            }
        }
    });
}
async function initBoard() {
    board = await fetch('data/leaderboard.json').then(r => r.json());
    $('#aggregation').textContent = board.aggregation + ' Rubric profiles follow the five dimensions shown above; hover for values.';
    $('#legend').innerHTML = board.families.map(f => `<button data-family="${f}"><i style="background:${colors[f]}"></i>${f}</button>`).join('');
    $$('#legend button').forEach(b => b.onclick = () => {
        family = family === b.dataset.family ? null : b.dataset.family;
        $$('#legend button').forEach(x => x.classList.toggle('inactive', family && x.dataset.family !== family));
        drawBoard()
    });
    drawBoard()
}
$$('[data-engine]').forEach(b => b.onclick = () => {
    engine = b.dataset.engine;
    $$('[data-engine]').forEach(x => x.classList.toggle('active', x === b));
    drawBoard()
});
$$('[data-sort]').forEach(b => b.onclick = () => {
    sort = b.dataset.sort;
    drawBoard()
});
$('#model-search').oninput = e => {
    search = e.target.value;
    drawBoard()
};
$('#submission-file').onchange = async e => {
    const file = e.target.files[0];
    if (!file) return;
    try {
        if (file.size > 10e6) throw Error('Please select a JSON file smaller than 10 MB.');
        const d = JSON.parse(await file.text());
        const catalog = await fetch('data/benchmark-catalog.json').then(r => r.json());
        const demo = d?.demo_only === true;
        const errors = validateManifest(d, catalog, !demo);
        $('#validation-result').textContent = errors.length ? 'Needs attention:\n' + errors.slice(0, 20).join('\n') + (errors.length > 20 ? `\n… ${errors.length-20} more issues.` : '') : demo ? 'Valid single-episode demo manifest—not a full benchmark submission. Use the local validator to verify its trace hash.' : 'Structure and benchmark membership passed. Trace hashes and scores still require verification; this does not publish a leaderboard entry.'
    } catch (err) {
        $('#validation-result').textContent = err.message
    }
};
const initialParams = new URLSearchParams(location.search);
const initialEpisode = ['cooking', 'household', 'mobile'].includes(initialParams.get('episode')) ? initialParams.get('episode') : 'cooking';
Promise.all([loadEpisode(initialEpisode), initBoard()]).then(() => {
    const tick = Number(initialParams.get('tick'));
    if (initialParams.has('tick') && Number.isFinite(tick) && tick >= 0) {
        seekTick(Math.min(Math.floor(tick), episode.ticks));
        $('#experience').scrollIntoView({
            behavior: 'instant'
        });
    }
}).catch(e => {
    $('#task').textContent = 'The preview data could not be loaded. Please reload the page.';
    console.error(e)
});
