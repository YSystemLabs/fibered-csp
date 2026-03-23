/* ── Fibered CSP Image Generator — 前端逻辑 ── */

// ═══ 工具函数 ═══════════════════════════════════════════════

function $(id) { return document.getElementById(id); }

function fmt(v, d = 2) {
    if (typeof v === 'boolean') return v ? '✓ True' : '✗ False';
    if (typeof v === 'number') return v.toFixed(d);
    return String(v);
}

// ═══ Tab 切换 ═══════════════════════════════════════════════

function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab-bar button');
    tabs.forEach(t => t.classList.remove('active'));
    if (tab === 'generate') {
        tabs[0].classList.add('active');
        $('generate-panel').classList.remove('hidden');
        $('generate-panel').style.display = 'grid';
        $('sweep-panel').classList.remove('active');
    } else {
        tabs[1].classList.add('active');
        $('generate-panel').classList.add('hidden');
        $('generate-panel').style.display = 'none';
        $('sweep-panel').classList.add('active');
    }
}

// ═══ 参数收集 ═══════════════════════════════════════════════

const SLIDER_IDS = ['alpha', 'K', 'sigma', 'tau', 'beta', 'gamma', 'mu',
                     'dir_strength', 'dir_angle', 'epsilon', 'cooling'];

const PARAM_CONTROL_IDS = {
    seed: 'p-seed',
    max_iter: 'p-max_iter',
    T_init: 'p-T_init',
    T_min: 'p-T_min',
    cooling: 'p-cooling',
    alpha: 'p-alpha',
    K: 'p-K',
    sigma: 'p-sigma',
    tau: 'p-tau',
    beta: 'p-beta',
    gamma: 'p-gamma',
    mu: 'p-mu',
    dir_strength: 'p-dir_strength',
    dir_angle: 'p-dir_angle',
    epsilon: 'p-epsilon',
    translate_period: 'p-translate_period',
    w_pixel: 'p-w_pixel',
};

let uiDefaults = null;

const PRESETS = {
    rgb_soft_sym: {
        label: 'RGB 柔和彩色镜像',
        size: 24,
        color_mode: 'rgb',
        levels: 16,
        seed: 101,
        target_mode: 'random_smooth',
        symmetry: ['lr'],
        alpha: 0.82,
        K: 255,
        sigma: 0.18,
        tau: 0.28,
        beta: 4.5,
        gamma: 11.0,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.12,
        max_iter: 4500,
        T_init: 10.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    rgb_center_quad: {
        label: 'RGB 四象限花窗',
        size: 24,
        color_mode: 'rgb',
        levels: 16,
        seed: 202,
        target_mode: 'center_blob',
        symmetry: ['quad'],
        alpha: 0.78,
        K: 255,
        sigma: 0.16,
        tau: 0.34,
        beta: 4.0,
        gamma: 12.0,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.10,
        max_iter: 5000,
        T_init: 10.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    rgb_kaleido_c4: {
        label: 'RGB C4 万花筒',
        size: 24,
        color_mode: 'rgb',
        levels: 16,
        seed: 404,
        target_mode: 'center_blob',
        symmetry: ['c4'],
        alpha: 0.80,
        K: 255,
        sigma: 0.16,
        tau: 0.30,
        beta: 4.2,
        gamma: 12.0,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.10,
        max_iter: 5200,
        T_init: 10.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    rgb_neon_strata: {
        label: 'RGB 霓虹层纹',
        size: 24,
        color_mode: 'rgb',
        levels: 16,
        seed: 505,
        target_mode: 'gradient_v',
        symmetry: ['none'],
        alpha: 0.72,
        K: 255,
        sigma: 0.14,
        tau: 0.26,
        beta: 7.0,
        gamma: 9.0,
        mu: 0.0,
        dir_strength: 0.9,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.10,
        max_iter: 4200,
        T_init: 10.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    rgb_sunset_ud: {
        label: 'RGB 日落横渐变',
        size: 24,
        color_mode: 'rgb',
        levels: 16,
        seed: 606,
        target_mode: 'gradient_h',
        symmetry: ['ud'],
        alpha: 0.84,
        K: 255,
        sigma: 0.15,
        tau: 0.28,
        beta: 4.6,
        gamma: 11.5,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.11,
        max_iter: 4600,
        T_init: 10.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    rgb_checker_pop: {
        label: 'RGB 波普棋盘',
        size: 24,
        color_mode: 'rgb',
        levels: 16,
        seed: 808,
        target_mode: 'checkerboard',
        symmetry: ['none'],
        alpha: 0.62,
        K: 255,
        sigma: 0.30,
        tau: 0.50,
        beta: 2.2,
        gamma: 8.0,
        mu: 6.5,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.08,
        max_iter: 5200,
        T_init: 12.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    grayscale_mirror_blob: {
        label: '灰度镜像团块',
        size: 24,
        color_mode: 'grayscale',
        levels: 8,
        seed: 707,
        target_mode: 'center_blob',
        symmetry: ['lr'],
        alpha: 0.76,
        K: 255,
        sigma: 0.18,
        tau: 0.33,
        beta: 4.2,
        gamma: 10.5,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.10,
        max_iter: 4200,
        T_init: 10.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    grayscale_texture: {
        label: '灰度高对比纹理',
        size: 24,
        color_mode: 'grayscale',
        levels: 8,
        seed: 303,
        target_mode: 'checkerboard',
        symmetry: ['none'],
        alpha: 0.58,
        K: 255,
        sigma: 0.28,
        tau: 0.52,
        beta: 2.0,
        gamma: 8.0,
        mu: 9.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 0.08,
        max_iter: 5000,
        T_init: 12.0,
        T_min: 0.01,
        cooling: 0.9992,
    },
    lowalpha_smooth_alive: {
        label: '低 α 存活：平滑噪声',
        size: 8,
        color_mode: 'grayscale',
        levels: 8,
        seed: 11,
        target_mode: 'random_smooth',
        symmetry: ['none'],
        alpha: 0.08,
        K: 0.25,
        sigma: 2.0,
        tau: 0.40,
        beta: 1.0,
        gamma: 2.0,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 2.0,
        max_iter: 800,
        T_init: 6.0,
        T_min: 0.01,
        cooling: 0.998,
    },
    lowalpha_blob_lr: {
        label: '低 α 存活：镜像团块',
        size: 8,
        color_mode: 'grayscale',
        levels: 8,
        seed: 23,
        target_mode: 'center_blob',
        symmetry: ['lr'],
        alpha: 0.06,
        K: 0.25,
        sigma: 2.0,
        tau: 0.40,
        beta: 1.0,
        gamma: 2.0,
        mu: 0.0,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 2.0,
        max_iter: 800,
        T_init: 6.0,
        T_min: 0.01,
        cooling: 0.998,
    },
    lowalpha_checker_alive: {
        label: '低 α 存活：棋盘纹理',
        size: 8,
        color_mode: 'grayscale',
        levels: 8,
        seed: 37,
        target_mode: 'checkerboard',
        symmetry: ['none'],
        alpha: 0.04,
        K: 0.25,
        sigma: 2.0,
        tau: 0.50,
        beta: 1.0,
        gamma: 2.0,
        mu: 2.5,
        dir_strength: 0.0,
        dir_angle: 0,
        epsilon: 0,
        translate_period: 4,
        w_pixel: 2.0,
        max_iter: 800,
        T_init: 6.0,
        T_min: 0.01,
        cooling: 0.998,
    },
};

// 联动 slider → value display
SLIDER_IDS.forEach(id => {
    const el = $('p-' + id);
    if (!el) return;
    el.addEventListener('input', () => {
        const v = $('v-' + id);
        if (v) v.textContent = parseFloat(el.value).toFixed(
            id === 'cooling' ? 4 : (id === 'dir_angle' || id === 'epsilon' || id === 'K') ? 0 : (id === 'w_pixel') ? 3 : 2
        );
    });
});

function updateAlpha(val) {
    $('alpha-display').textContent = 'α = ' + parseFloat(val).toFixed(2);
    $('v-alpha').textContent = parseFloat(val).toFixed(2);
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}

function formatControlValue(value, step) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return String(value);
    const stepStr = String(step ?? '1');
    if (!stepStr.includes('.')) return String(Math.round(value));
    return value.toFixed(stepStr.split('.')[1].length);
}

function applyNumericSpec(el, spec) {
    if (!el || !spec) return;
    if (spec.min != null) el.min = spec.min;
    if (spec.max != null) el.max = spec.max;
    if (spec.step != null) el.step = spec.step;

    const min = spec.min != null ? Number(spec.min) : -Infinity;
    const max = spec.max != null ? Number(spec.max) : Infinity;
    let value = Number(el.value);
    if (!Number.isFinite(value)) value = Number(spec.value ?? 0);
    value = clamp(value, min, max);
    el.value = formatControlValue(value, spec.step);
}

function applyUiDefaults(defaults) {
    uiDefaults = defaults;
    for (const [key, controlId] of Object.entries(PARAM_CONTROL_IDS)) {
        const el = $(controlId);
        const spec = defaults[key];
        if (!el || !spec) continue;
        applyNumericSpec(el, spec);
    }

    if (defaults.seed) {
        $('p-seed').value = defaults.seed.value;
    }

    for (const id of SLIDER_IDS) {
        const el = $('p-' + id);
        if (el) el.dispatchEvent(new Event('input'));
    }

    updateSweepAxisInputs('x');
    updateSweepAxisInputs('y');
}

function updateSweepAxisInputs(axis) {
    if (!uiDefaults) return;
    const param = $('sw-' + axis + '-param').value;
    const minEl = $('sw-' + axis + '-min');
    const maxEl = $('sw-' + axis + '-max');
    if (!minEl || !maxEl) return;

    const fallback = {min: 0, max: 1, step: 0.01, value: 0};
    const spec = uiDefaults[param] || fallback;
    const step = spec.step ?? fallback.step;
    const min = spec.min ?? fallback.min;
    const max = spec.max ?? fallback.max;

    minEl.min = min;
    minEl.max = max;
    minEl.step = step;
    maxEl.min = min;
    maxEl.max = max;
    maxEl.step = step;

    let curMin = Number(minEl.value);
    let curMax = Number(maxEl.value);
    if (!Number.isFinite(curMin) || curMin < min || curMin > max) curMin = min;
    if (!Number.isFinite(curMax) || curMax < min || curMax > max) curMax = max;
    if (curMin > curMax) {
        curMin = min;
        curMax = max;
    }

    minEl.value = formatControlValue(curMin, step);
    maxEl.value = formatControlValue(curMax, step);
}

async function initializeUiDefaults() {
    try {
        const resp = await fetch('/api/defaults');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const defaults = await resp.json();
        applyUiDefaults(defaults);
    } catch (e) {
        console.warn('加载默认参数失败，继续使用前端静态默认值', e);
        updateSweepAxisInputs('x');
        updateSweepAxisInputs('y');
    }
}

function getSelectedSymmetry() {
    const cbs = document.querySelectorAll('#sym-checkboxes input[type="checkbox"]');
    const sel = [];
    cbs.forEach(cb => { if (cb.checked) sel.push(cb.value); });
    // 如果选了 none 以外的，去掉 none
    if (sel.length > 1 && sel.includes('none')) {
        return sel.filter(s => s !== 'none');
    }
    return sel.length ? sel : ['none'];
}

function setSelectedSymmetry(values) {
    const selected = new Set(values && values.length ? values : ['none']);
    document.querySelectorAll('#sym-checkboxes input[type="checkbox"]').forEach(cb => {
        cb.checked = selected.has(cb.value);
    });

    if (selected.has('none') && selected.size > 1) {
        document.querySelector('#sym-checkboxes input[value="none"]').checked = false;
    }
    if (selected.has('quad')) {
        document.querySelector('#sym-checkboxes input[value="lr"]').checked = true;
        document.querySelector('#sym-checkboxes input[value="ud"]').checked = true;
        document.querySelector('#sym-checkboxes input[value="none"]').checked = false;
    }
}

function setControlValue(controlId, value) {
    const el = $(controlId);
    if (!el) return;

    if (el.type === 'number' || el.type === 'range') {
        const step = el.step || '1';
        const min = el.min !== '' ? Number(el.min) : -Infinity;
        const max = el.max !== '' ? Number(el.max) : Infinity;
        const num = clamp(Number(value), min, max);
        el.value = formatControlValue(num, step);
    } else {
        el.value = String(value);
    }

    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
}

function loadPreset(presetKey) {
    const preset = PRESETS[presetKey];
    if (!preset) return;

    setControlValue('p-size', preset.size);
    setControlValue('p-color_mode', preset.color_mode);
    setControlValue('p-levels', preset.levels);
    setControlValue('p-seed', preset.seed);
    setControlValue('p-target_mode', preset.target_mode);

    setControlValue('p-alpha', preset.alpha);
    setControlValue('p-K', preset.K);
    setControlValue('p-sigma', preset.sigma);
    setControlValue('p-tau', preset.tau);
    setControlValue('p-beta', preset.beta);
    setControlValue('p-gamma', preset.gamma);
    setControlValue('p-mu', preset.mu);
    setControlValue('p-dir_strength', preset.dir_strength);
    setControlValue('p-dir_angle', preset.dir_angle);
    setControlValue('p-epsilon', preset.epsilon);
    setControlValue('p-translate_period', preset.translate_period);
    setControlValue('p-w_pixel', preset.w_pixel);
    setControlValue('p-max_iter', preset.max_iter);
    setControlValue('p-T_init', preset.T_init);
    setControlValue('p-T_min', preset.T_min);
    setControlValue('p-cooling', preset.cooling);

    setSelectedSymmetry(preset.symmetry);
    updateAlpha($('p-alpha').value);
    $('status-msg').textContent = `已加载预设：${preset.label}，可直接点击 Generate。`;
}

function applySelectedPreset() {
    const presetKey = $('preset-select').value;
    if (!presetKey) {
        $('status-msg').textContent = '当前为自定义参数。';
        return;
    }
    loadPreset(presetKey);
}

// §5.2 交互约束
document.querySelectorAll('#sym-checkboxes input').forEach(cb => {
    cb.addEventListener('change', () => {
        const val = cb.value;
        if (val === 'none' && cb.checked) {
            document.querySelectorAll('#sym-checkboxes input').forEach(c => {
                if (c.value !== 'none') c.checked = false;
            });
        } else if (val !== 'none' && cb.checked) {
            document.querySelector('#sym-checkboxes input[value="none"]').checked = false;
        }
        if (val === 'quad' && cb.checked) {
            document.querySelector('#sym-checkboxes input[value="lr"]').checked = true;
            document.querySelector('#sym-checkboxes input[value="ud"]').checked = true;
        }
        if (val === 'c4' && cb.checked) {
            // C4 需要方形，现在已是方形下拉框，无需额外处理
        }
    });
});

['x', 'y'].forEach(axis => {
    const el = $('sw-' + axis + '-param');
    if (el) el.addEventListener('change', () => updateSweepAxisInputs(axis));
});

function collectParams() {
    return {
        width:      parseInt($('p-size').value),
        height:     parseInt($('p-size').value),
        color_mode: $('p-color_mode').value,
        levels:     parseInt($('p-levels').value),
        seed:       parseInt($('p-seed').value),
        target_mode: $('p-target_mode').value,
        max_iter:   parseInt($('p-max_iter').value),
        alpha:      parseFloat($('p-alpha').value),
        K:          parseFloat($('p-K').value),
        sigma:      parseFloat($('p-sigma').value),
        tau:        parseFloat($('p-tau').value),
        beta:       parseFloat($('p-beta').value),
        gamma:      parseFloat($('p-gamma').value),
        mu:         parseFloat($('p-mu').value),
        dir_strength: parseFloat($('p-dir_strength').value),
        dir_angle:  parseFloat($('p-dir_angle').value),
        symmetry:   getSelectedSymmetry(),
        epsilon:    parseFloat($('p-epsilon').value),
        translate_period: parseInt($('p-translate_period').value),
        w_pixel:    parseFloat($('p-w_pixel').value),
        T_init:     parseFloat($('p-T_init').value),
        T_min:      parseFloat($('p-T_min').value),
        cooling:    parseFloat($('p-cooling').value),
    };
}

// ═══ Canvas 渲染 ═══════════════════════════════════════════

function renderGrayscale(canvasId, data2d, colormap) {
    const canvas = $(canvasId);
    if (!data2d || !data2d.length) return;
    const H = data2d.length, W = data2d[0].length;

    // 检测 RGB：data2d[i][j] 为 [r,g,b] 三元组
    const isRGB = Array.isArray(data2d[0][0]);

    const scale = Math.max(1, Math.floor(256 / Math.max(H, W)));
    canvas.width = W * scale;
    canvas.height = H * scale;
    const ctx = canvas.getContext('2d');
    const imgData = ctx.createImageData(W * scale, H * scale);

    if (isRGB && colormap !== 'heat') {
        // ── RGB 渲染 ──
        // 找到每通道的 min/max 用于归一化
        let mn = [Infinity, Infinity, Infinity];
        let mx = [-Infinity, -Infinity, -Infinity];
        for (let i = 0; i < H; i++)
            for (let j = 0; j < W; j++)
                for (let c = 0; c < 3; c++) {
                    mn[c] = Math.min(mn[c], data2d[i][j][c]);
                    mx[c] = Math.max(mx[c], data2d[i][j][c]);
                }
        const rng3 = [mx[0]-mn[0]||1, mx[1]-mn[1]||1, mx[2]-mn[2]||1];

        for (let i = 0; i < H; i++) {
            for (let j = 0; j < W; j++) {
                const r = Math.floor(((data2d[i][j][0] - mn[0]) / rng3[0]) * 255);
                const g = Math.floor(((data2d[i][j][1] - mn[1]) / rng3[1]) * 255);
                const b = Math.floor(((data2d[i][j][2] - mn[2]) / rng3[2]) * 255);
                for (let si = 0; si < scale; si++) {
                    for (let sj = 0; sj < scale; sj++) {
                        const idx = ((i * scale + si) * W * scale + j * scale + sj) * 4;
                        imgData.data[idx] = r;
                        imgData.data[idx + 1] = g;
                        imgData.data[idx + 2] = b;
                        imgData.data[idx + 3] = 255;
                    }
                }
            }
        }
    } else {
        // ── 灰度/热力图渲染 ──
        // 如果是 RGB 数据但需要热力图模式，取亮度
        let flat2d = data2d;
        if (isRGB) {
            flat2d = data2d.map(row => row.map(px => (px[0] + px[1] + px[2]) / 3));
        }

        let mn = Infinity, mx = -Infinity;
        for (let i = 0; i < H; i++)
            for (let j = 0; j < W; j++) {
                mn = Math.min(mn, flat2d[i][j]);
                mx = Math.max(mx, flat2d[i][j]);
            }
        const rng = mx - mn || 1;

        for (let i = 0; i < H; i++) {
            for (let j = 0; j < W; j++) {
                const t = (flat2d[i][j] - mn) / rng;
                let r, g, b;
                if (colormap === 'heat') {
                    r = Math.floor(t * 255);
                    g = Math.floor((t < 0.5 ? t * 2 : (1 - t) * 2) * 255);
                    b = Math.floor((1 - t) * 255);
                } else {
                    const v = Math.floor(t * 255);
                    r = g = b = v;
                }
                for (let si = 0; si < scale; si++) {
                    for (let sj = 0; sj < scale; sj++) {
                        const idx = ((i * scale + si) * W * scale + j * scale + sj) * 4;
                        imgData.data[idx] = r;
                        imgData.data[idx + 1] = g;
                        imgData.data[idx + 2] = b;
                        imgData.data[idx + 3] = 255;
                    }
                }
            }
        }
    }
    ctx.putImageData(imgData, 0, 0);
}

// ═══ /api/generate 调用 ═══════════════════════════════════

let lastResult = null;
let sweepAbortController = null;

async function doGenerate() {
    const btn = $('btn-generate');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    $('status-msg').textContent = '搜索中...';

    try {
        const params = collectParams();
        const resp = await fetch('/api/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params),
        });
        const data = await resp.json();
        lastResult = data;

        // 渲染 4 张图
        renderGrayscale('c-result', data.image, 'gray');
        renderGrayscale('c-target', data.targets, 'gray');
        if (data.region_heatmap) {
            renderGrayscale('c-heatmap', data.region_heatmap, 'heat');
        }

        const H = data.image.length, W = data.image[0].length;
        const closureViz = data.closure_map || Array.from({length: H}, () => Array(W).fill(
            Math.abs(data.scores.closure_correction_pixel)
        ));
        renderGrayscale('c-closure', closureViz, 'heat');

        // 更新仪表盘
        updateDashboard(data.scores, data.metadata);
        $('status-msg').textContent = `完成 (${data.metadata.time_seconds}s)`;

    } catch (e) {
        $('status-msg').textContent = '错误: ' + e.message;
        console.error(e);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate';
    }
}

function updateDashboard(scores, meta) {
    $('s-dir_pixel').textContent = fmt(scores.dir_pixel_log);
    $('s-dir_region').textContent = fmt(scores.dir_region);
    $('s-dir_sym').textContent = fmt(scores.dir_sym);
    $('s-em_region').textContent = fmt(scores.em_region);
    $('s-score_pixel').textContent = fmt(scores.score_pixel_log);
    $('s-score_region').textContent = fmt(scores.score_region);
    $('s-score_sym').textContent = fmt(scores.score_sym);
    $('s-cl_pixel').textContent = fmt(scores.cl_pixel_log);
    $('s-cl_region').textContent = fmt(scores.cl_region);
    $('s-cl_sym').textContent = fmt(scores.cl_sym);
    $('s-correction_pixel').textContent = fmt(scores.closure_correction_pixel, 3);
    $('s-correction_region').textContent = fmt(scores.closure_correction_region);

    const colEl = $('s-collapsed');
    if (scores.is_collapsed) {
        colEl.innerHTML = '<span class="status-light red"></span>Yes';
        colEl.className = 'value collapsed';
    } else {
        colEl.innerHTML = '<span class="status-light green"></span>No';
        colEl.className = 'value ok';
    }

    $('meta-info').innerHTML = `
        耗时 ${meta.time_seconds}s · ${meta.iterations_used} iter<br>
        自由像素 ${meta.free_pixels} / ${meta.total_pixels}
    `;
}

// ═══ /api/sweep 调用 ═══════════════════════════════════════

let sweepResult = null;

async function doSweep() {
    if (sweepAbortController) {
        sweepAbortController.abort();
        sweepAbortController = null;
        $('btn-sweep').textContent = 'Sweep';
        $('btn-sweep').disabled = false;
        $('sweep-status').textContent = '已取消';
        return;
    }

    const btn = $('btn-sweep');
    btn.disabled = true;
    btn.textContent = 'Cancel';
    $('sweep-status').textContent = '扫描中...';
    $('sweep-progress').style.width = '0%';
    sweepAbortController = new AbortController();

    try {
        const baseParams = collectParams();
        const xParam = $('sw-x-param').value;
        const yParam = $('sw-y-param').value;

        const sweepBody = {
            base_params: baseParams,
            stream: true,
            sweep: {
                axis_x: {
                    param: xParam,
                    min: parseFloat($('sw-x-min').value),
                    max: parseFloat($('sw-x-max').value),
                    steps: parseInt($('sw-x-steps').value),
                },
            },
            order_params: getSelectedOrderParams(),
        };
        if (yParam) {
            sweepBody.sweep.axis_y = {
                param: yParam,
                min: parseFloat($('sw-y-min').value),
                max: parseFloat($('sw-y-max').value),
                steps: parseInt($('sw-y-steps').value),
            };
        }

        const resp = await fetch('/api/sweep', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(sweepBody),
            signal: sweepAbortController.signal,
        });
        if (!resp.ok) {
            const err = await resp.text();
            throw new Error(err || ('HTTP ' + resp.status));
        }
        await consumeSweepStream(resp);

        if (!sweepResult) {
            throw new Error('扫描未返回结果');
        }

        // 填充序参量选择器
        const sel = $('sw-display');
        sel.innerHTML = '';
        for (const k of Object.keys(sweepResult.results)) {
            const opt = document.createElement('option');
            opt.value = k;
            opt.textContent = k;
            sel.appendChild(opt);
        }

        $('sweep-progress').style.width = '100%';
        renderSweepHeatmap();
        renderSweep1D();

        $('sweep-status').textContent =
            `完成: ${sweepResult.metadata.total_runs} 次, ${sweepResult.metadata.time_seconds}s` +
            (sweepResult.metadata.estimated_alpha_c != null
                ? `, α_c ≈ ${sweepResult.metadata.estimated_alpha_c.toFixed(3)}`
                : '');

    } catch (e) {
        if (e.name === 'AbortError') {
            $('sweep-status').textContent = '已取消';
        } else {
            $('sweep-status').textContent = '错误: ' + e.message;
            console.error(e);
        }
    } finally {
        sweepAbortController = null;
        btn.disabled = false;
        btn.textContent = 'Sweep';
    }
}

async function consumeSweepStream(resp) {
    const reader = resp.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, {stream: true});

        let splitIndex;
        while ((splitIndex = buffer.indexOf('\n\n')) >= 0) {
            const chunk = buffer.slice(0, splitIndex);
            buffer = buffer.slice(splitIndex + 2);
            handleSseChunk(chunk);
        }
    }
}

function handleSseChunk(chunk) {
    if (!chunk.trim()) return;
    let eventName = 'message';
    let dataLines = [];
    for (const line of chunk.split('\n')) {
        if (line.startsWith('event:')) {
            eventName = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
            dataLines.push(line.slice(5).trim());
        }
    }
    const payloadText = dataLines.join('\n');
    const payload = payloadText ? JSON.parse(payloadText) : {};

    if (eventName === 'progress') {
        const completed = payload.completed || 0;
        const total = payload.total || 1;
        const pct = Math.max(0, Math.min(100, (completed / total) * 100));
        $('sweep-progress').style.width = pct.toFixed(1) + '%';
        $('sweep-status').textContent = `扫描中... ${completed}/${total}`;
    } else if (eventName === 'done') {
        sweepResult = payload;
        $('sweep-progress').style.width = '100%';
    } else if (eventName === 'error') {
        throw new Error(payload.message || '扫描失败');
    }
}

function getSelectedOrderParams() {
    const cbs = document.querySelectorAll('#sw-order-params input:checked');
    return Array.from(cbs).map(c => c.value);
}

// ── 相图热力图 ──

function renderSweepHeatmap() {
    if (!sweepResult) return;
    const key = $('sw-display').value;
    const data = sweepResult.results[key];
    if (!data) return;

    const canvas = $('c-sweep');
    const H = data.length, W = data[0].length;
    const cellW = Math.max(1, Math.floor(480 / W));
    const cellH = Math.max(1, Math.floor(360 / H));
    canvas.width = W * cellW + 60;
    canvas.height = H * cellH + 40;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 数据范围
    let mn = Infinity, mx = -Infinity;
    for (const row of data)
        for (const v of row) { mn = Math.min(mn, v); mx = Math.max(mx, v); }
    const rng = mx - mn || 1;

    // 绘制 cells (viridis-like)
    for (let yi = 0; yi < H; yi++) {
        for (let xi = 0; xi < W; xi++) {
            const t = (data[yi][xi] - mn) / rng;
            ctx.fillStyle = viridis(t);
            ctx.fillRect(50 + xi * cellW, 5 + yi * cellH, cellW - 1, cellH - 1);
        }
    }

    // 轴标签
    ctx.fillStyle = '#999';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    const xVals = sweepResult.axis_x.values;
    for (let xi = 0; xi < W; xi += Math.max(1, Math.floor(W / 8))) {
        ctx.fillText(xVals[xi].toFixed(2), 50 + xi * cellW + cellW / 2, H * cellH + 20);
    }
    ctx.textAlign = 'right';
    const yVals = sweepResult.axis_y.values;
    if (yVals && yVals.length > 1) {
        for (let yi = 0; yi < H; yi += Math.max(1, Math.floor(H / 6))) {
            ctx.fillText(yVals[yi].toFixed(2), 46, 5 + yi * cellH + cellH / 2 + 4);
        }
    }

    // 色标
    const barX = canvas.width - 8;
    for (let i = 0; i < H * cellH; i++) {
        const t = 1 - i / (H * cellH - 1);
        ctx.fillStyle = viridis(t);
        ctx.fillRect(barX, 5 + i, 6, 1);
    }
}

// ── 1D 曲线 ──

function renderSweep1D() {
    if (!sweepResult) return;
    const canvas = $('c-sweep-1d');
    const ctx = canvas.getContext('2d');
    canvas.width = 500;
    canvas.height = 250;
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, 500, 250);

    const xVals = sweepResult.axis_x.values;
    const keys = Object.keys(sweepResult.results);
    const colors = ['#e94560', '#00cfe8', '#28c76f', '#ff9f43', '#7367f0'];
    const padL = 50, padR = 20, padT = 20, padB = 30;
    const plotW = 500 - padL - padR;
    const plotH = 250 - padT - padB;

    // X 轴
    ctx.strokeStyle = '#444';
    ctx.beginPath();
    ctx.moveTo(padL, padT + plotH);
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.stroke();

    // X 轴标签
    ctx.fillStyle = '#999';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    for (let i = 0; i < xVals.length; i += Math.max(1, Math.floor(xVals.length / 8))) {
        const x = padL + (i / (xVals.length - 1)) * plotW;
        ctx.fillText(xVals[i].toFixed(2), x, padT + plotH + 16);
    }

    // 绘制每个序参量（取 y=0 行）
    keys.forEach((key, ki) => {
        const row = sweepResult.results[key][0];
        let mn = Math.min(...row), mx = Math.max(...row);
        const rng = mx - mn || 1;

        ctx.strokeStyle = colors[ki % colors.length];
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < row.length; i++) {
            const x = padL + (i / (row.length - 1)) * plotW;
            const y = padT + plotH - ((row[i] - mn) / rng) * plotH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // 图例
        ctx.fillStyle = colors[ki % colors.length];
        ctx.textAlign = 'left';
        ctx.fillText(key, padL + 8, padT + 14 + ki * 14);
    });

    // α_c 竖线
    if (sweepResult.metadata.estimated_alpha_c != null) {
        const ac = sweepResult.metadata.estimated_alpha_c;
        const xMin = xVals[0], xMax = xVals[xVals.length - 1];
        const acX = padL + ((ac - xMin) / (xMax - xMin)) * plotW;
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(acX, padT);
        ctx.lineTo(acX, padT + plotH);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = '#fff';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('α_c≈' + ac.toFixed(2), acX, padT - 4);
    }
}

// ── Viridis 近似色标 ──

function viridis(t) {
    t = Math.max(0, Math.min(1, t));
    // Simplified viridis approximation
    const r = Math.floor(Math.max(0, Math.min(255, (t < 0.5 ? 68 + t * 2 * 30 : 68 + 30 + (t - 0.5) * 2 * 157))));
    const g = Math.floor(Math.max(0, Math.min(255, (t < 0.25 ? 1 + t * 4 * 83 : (t < 0.75 ? 84 + (t - 0.25) * 2 * 100 : 184 + (t - 0.75) * 4 * 71)))));
    const b = Math.floor(Math.max(0, Math.min(255, (t < 0.5 ? 84 + t * 2 * 84 : 252 - (t - 0.5) * 2 * 200))));
    return `rgb(${r},${g},${b})`;
}

// ═══ 初始化 ═══════════════════════════════════════════════

// 确保初始值显示正确
SLIDER_IDS.forEach(id => {
    const el = $('p-' + id);
    if (el) el.dispatchEvent(new Event('input'));
});

initializeUiDefaults();
