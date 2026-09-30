// Local-only manifest checks. Uploaded data is never transmitted.
export function validateManifest(data, catalog, full = true) {
    const errors = [], counts = {cooksim: 150, vhhome: 75, screensim: 90};
    const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
    const string = x => typeof x === 'string' && x.trim().length > 0;
    const require = (ok, message) => { if (!ok) errors.push(message); };
    if (!object(data)) return ['The manifest must be a JSON object.'];
    require(data.benchmark_version === 'ive-v1', 'benchmark_version must be ive-v1.');
    if (full) require(data.demo_only !== true, 'Demo manifests are not full benchmark submissions.');
    if (!object(data.model)) errors.push('model must be an object.');
    else {
        for (const k of ['name', 'revision']) require(string(data.model[k]), `model.${k} is required.`);
        require(['Frontier API','Streaming API','Open non-streaming','Open streaming'].includes(data.model.family), 'Unknown model family.');
    }
    if (!Array.isArray(data.runs) || !data.runs.length) return [...errors, 'runs must be a nonempty array.'];
    const seen = new Set();
    for (const [i, r] of data.runs.entries()) {
        const label = `Run ${i+1}`;
        if (!object(r)) { errors.push(`${label}: must be an object.`); continue; }
        if (!Object.keys(counts).includes(r.engine)) { errors.push(`${label}: unknown engine.`); continue; }
        if (!Number.isInteger(r.run_id) || r.run_id < 1) { errors.push(`${label}: invalid run_id.`); continue; }
        const key = `${r.engine}:${r.run_id}`;
        require(!seen.has(key), `${label}: duplicate engine/run.`); seen.add(key);
        if (!Array.isArray(r.episodes) || !r.episodes.length) { errors.push(`${label}: episodes must be a nonempty array.`); continue; }
        if (full) require(r.episodes.length === counts[r.engine], `${label}: expected ${counts[r.engine]} episodes.`);
        const pairs = new Set(), expected = new Set(catalog.engines[r.engine].map(x => JSON.stringify([x.case_id,x.persona_id])));
        for (const [j, ep] of r.episodes.entries()) {
            const at = `${label}, episode ${j+1}`;
            if (!object(ep)) { errors.push(`${at}: must be an object.`); continue; }
            const fields = ['case_id','persona_id','trace_uri','trace_sha256'];
            if (fields.some(k => !string(ep[k]))) { errors.push(`${at}: case/persona, trace path, and hash must be nonempty strings.`); continue; }
            const pair = JSON.stringify([ep.case_id,ep.persona_id]);
            require(!pairs.has(pair), `${at}: duplicate case/persona.`); pairs.add(pair);
            require(expected.has(pair), `${at}: unknown case/persona pair.`);
            require(ep.trace_sha256.length === 64 && /^[a-f0-9]{64}$/.test(ep.trace_sha256), `${at}: invalid SHA-256.`);
            require(!ep.trace_uri.startsWith('/') && !ep.trace_uri.includes('://') && !ep.trace_uri.includes('\\') && !ep.trace_uri.split('/').includes('..'), `${at}: trace path must be relative and stay inside the submission.`);
        }
        if (full) require(pairs.size === expected.size && [...pairs].every(x => expected.has(x)), `${label}: membership does not match the benchmark catalog.`);
    }
    if (full) require(seen.size === 9 && Object.keys(counts).every(e => [1,2,3].every(r => seen.has(`${e}:${r}`))), 'Full submissions require all three environments and runs 1, 2, 3.');
    return errors;
}
