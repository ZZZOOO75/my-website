# -*- coding: utf-8 -*-
"""
乏燃料运输容器智能运维系统 · 威布尔可靠性评估（桌面版）
两参数威布尔分布建模：可靠度 / 失效概率密度 / 故障率曲线自动拟合
零第三方运行时依赖（仅 Python 标准库 + Tkinter）
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import random
import csv

# ============================ 数学基础 ============================
def gamma(z):
    if z < 0.5:
        return math.pi / (math.sin(math.pi * z) * gamma(1 - z))
    z -= 1.0
    C = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
         -176.61502916214059, 12.507343278686905, -0.13857109526572012,
         9.9843695780195716e-6, 1.5056327351493116e-7]
    g = 7
    x = C[0]
    for i in range(1, g + 2):
        x += C[i] / (z + i)
    t = z + g + 0.5
    return math.sqrt(2 * math.pi) * t ** (z + 0.5) * math.exp(-t) * x


def linreg(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0, 0.0, 0.0
    sx = sy = sxx = syy = sxy = 0.0
    for i in range(n):
        sx += xs[i]; sy += ys[i]
        sxx += xs[i] * xs[i]; syy += ys[i] * ys[i]; sxy += xs[i] * ys[i]
    den = n * sxx - sx * sx
    slope = 0.0 if den == 0 else (n * sxy - sx * sy) / den
    intercept = (sy - slope * sx) / n
    r = (n * sxy - sx * sy) / math.sqrt((n * sxx - sx * sx) * (n * syy - sy * sy) or 1)
    return slope, intercept, r


def weibull_mle(data):
    """极大似然估计（数值稳定：w=t/tmax 归一化）"""
    n = len(data)
    tmax = max(data)
    w = [t / tmax for t in data]
    lnT = [math.log(t) for t in data]
    mean_ln = sum(lnT) / n

    def g(b):
        s1 = s2 = 0.0
        for i in range(n):
            wb = w[i] ** b
            s1 += wb * lnT[i]
            s2 += wb
        return s1 / s2 - 1.0 / b - mean_ln

    lo, hi = 0.02, 1.0
    while g(hi) <= 0 and hi < 1e9:
        hi *= 2
    while g(lo) >= 0 and lo > 1e-9:
        lo /= 2
    for _ in range(90):
        mid = (lo + hi) / 2
        if g(mid) < 0:
            lo = mid
        else:
            hi = mid
    beta = (lo + hi) / 2
    s2 = sum((t / tmax) ** beta for t in data)
    eta = tmax * (s2 / n) ** (1.0 / beta)
    return beta, eta


def weibull_rank(data):
    """概率纸回归（最小二乘，Benard 中位秩）"""
    n = len(data)
    s = sorted(data)
    xs, ys = [], []
    for i in range(n):
        F = (i + 1 - 0.3) / (n + 0.4)
        xs.append(math.log(s[i]))
        ys.append(math.log(-math.log(1 - F)))
    slope, intercept, r = linreg(xs, ys)
    return slope, math.exp(-intercept / slope), r


def weibull_stats(beta, eta):
    mttf = eta * gamma(1 + 1 / beta)
    median = eta * math.log(2) ** (1 / beta)
    b10 = eta * (-math.log(0.9)) ** (1 / beta)
    var = eta * eta * (gamma(1 + 2 / beta) - gamma(1 + 1 / beta) ** 2)
    sd = math.sqrt(max(0.0, var))
    return mttf, median, b10, sd


def sample_weibull(n, beta, eta):
    return [eta * (-math.log(1 - random.random())) ** (1 / beta) for _ in range(n)]


def quantile(sorted_data, p):
    n = len(sorted_data)
    if n == 0:
        return float('nan')
    idx = (n - 1) * p
    lo, hi = int(idx), math.ceil(idx)
    if lo == hi:
        return sorted_data[lo]
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def histogram(data, nbins):
    s = sorted(data)
    lo, hi = s[0], s[-1]
    nbins = max(5, min(30, int(nbins)))
    w = (hi - lo) / nbins if nbins > 0 else 1.0
    bins = [(lo + i * w, lo + (i + 1) * w, 0) for i in range(nbins)]
    for v in data:
        i = min(nbins - 1, int((v - lo) / w))
        x0, x1, c = bins[i]
        bins[i] = (x0, x1, c + 1)
    return bins, w


# ============================ 常量 ============================
PARAM_UNIT = {'acc': 'g', 'strain': 'με', 'temp': '℃'}
PARAM_NAME = {'acc': '加速度', 'strain': '应变', 'temp': '温度'}
PRESETS = {'acc': (2.6, 3.1, 60), 'strain': (2.2, 820.0, 70), 'temp': (4.2, 68.0, 60)}
CONDITIONS = ['吊装', '公路运输', '铁路运输', '水路运输', '贮存静置', '全工况']

# 配色
BG = '#0f1720'; PANEL = '#172231'; PANEL2 = '#1d2c3e'; LINE = '#2a3b50'
TEXT = '#e6edf5'; MUTED = '#8fa3bb'; ACCENT = '#22d3ee'; BLUE = '#3b82f6'
C_R = '#22d3ee'; C_F = '#34d399'; C_L = '#fbbf24'; C_FF = '#a78bfa'; C_PT = '#f472b6'

# 图表尺寸
CW, CH = 500, 300
ML, MR, MT, MB = 52, 14, 20, 36
PLOT_W = CW - ML - MR
PLOT_H = CH - MT - MB


def fmt(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return '—'
    if v == 0:
        return '0'
    a = abs(v)
    if a >= 100000 or a < 0.001:
        return '%.2e' % v
    if a >= 100:
        return '%.0f' % v
    if a >= 1:
        return '%.2f' % v
    return '%.4g' % v


def lnln(F):
    return math.log(-math.log(1 - F))


def nice_ticks(mn, mx, n=5):
    if mn == mx:
        return [mn]
    span = mx - mn
    step = 10 ** math.floor(math.log10(span / n))
    err = span / n / step
    f = 10 if err >= 7.5 else 5 if err >= 3.5 else 2 if err >= 1.5 else 1
    s = step * f
    start = math.ceil(mn / s) * s
    out = []
    v = start
    while v <= mx + 1e-9:
        out.append(v)
        v += s
    return out


def log_ticks(mn, mx):
    out = []
    k0 = math.floor(math.log10(mn)); k1 = math.ceil(math.log10(mx))
    for k in range(k0, k1 + 1):
        for m in (1, 2, 5):
            v = m * 10 ** k
            if mn * 0.999 <= v <= mx * 1.001:
                out.append(v)
    return out


# ============================ 绘图 ============================
def draw_chart(cv, cfg):
    cv.delete('all')
    x0, x1 = cfg['x_range']
    y0, y1 = cfg['y_range']
    x_scale = cfg.get('x_scale', 'linear')
    y_scale = cfg.get('y_scale', 'linear')

    def px(x):
        if x_scale == 'log':
            return ML + (math.log(x) - math.log(x0)) / (math.log(x1) - math.log(x0)) * PLOT_W
        return ML + (x - x0) / (x1 - x0) * PLOT_W

    def py(y):
        if y_scale == 'weibull':
            return MT + (1 - (lnln(y) - y0) / (y1 - y0)) * PLOT_H
        return MT + (1 - (y - y0) / (y1 - y0)) * PLOT_H

    cv.create_rectangle(0, 0, CW, CH, fill=PANEL, outline=PANEL)
    # 网格与刻度
    if y_scale == 'weibull':
        Fs = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.632, 0.7, 0.8, 0.9, 0.95, 0.99]
        yt = [(F, ('%.0f%%' % (F * 100)) if F >= 0.1 else ('%.1f%%' % (F * 100))) for F in Fs if y0 <= lnln(F) <= y1]
    else:
        yt = [(v, fmt(v)) for v in nice_ticks(y0, y1, 5)]
    xt = [(v, fmt(v)) for v in (log_ticks(x0, x1) if x_scale == 'log' else nice_ticks(x0, x1, 6))]

    for v, lab in yt:
        yy = py(v)
        cv.create_line(ML, yy, CW - MR, yy, fill='#253548')
        cv.create_text(ML - 6, yy, text=lab, fill=MUTED, anchor='e', font=('Consolas', 8))
    for v, lab in xt:
        xx = px(v)
        cv.create_line(xx, MT, xx, CH - MB, fill='#253548')
        cv.create_text(xx, CH - MB + 12, text=lab, fill=MUTED, anchor='n', font=('Consolas', 8))
    cv.create_rectangle(ML, MT, CW - MR, CH - MB, outline=LINE)

    # 直方图（密度，与 y 轴同尺度）
    if cfg.get('hist'):
        for x0b, x1b, c in cfg['hist']:
            xx0, xx1 = px(x0b), px(x1b)
            ytop, ybot = py(c), py(y0)
            cv.create_rectangle(xx0 + 1, ytop, xx1 - 1, ybot, fill='#244059', outline='')

    # 曲线
    for ln in cfg.get('lines', []):
        pts = []
        for t, v in ln['data']:
            pts.append((px(t), py(v)))
        if len(pts) >= 2:
            cv.create_line(pts, fill=ln['color'], width=2)
    # 数据点（格式 (x, y, color)）
    for p in cfg.get('points', []):
        xx, yy = px(p[0]), py(p[1])
        cv.create_oval(xx - 3, yy - 3, xx + 3, yy + 3, fill=p[2], outline='')
    # 参考线
    for ref in cfg.get('reflines', []):
        yy = py(ref[0])
        cv.create_line(ML, yy, CW - MR, yy, fill=ref[1] if len(ref) > 1 else '#fbbf24', dash=(4, 4))
        if len(ref) > 2:
            cv.create_text(CW - MR - 4, yy - 8, text=ref[2], fill='#fbbf24', anchor='e', font=('Segoe UI', 8))

    # 轴标签
    cv.create_text(ML + PLOT_W / 2, CH - 4, text=cfg['xlabel'], fill='#c7d4e5', font=('Segoe UI', 9))
    cv.create_text(14, MT + PLOT_H / 2, text=cfg['ylabel'], fill='#c7d4e5', font=('Segoe UI', 9))


# ============================ 应用 ============================
class App:
    def __init__(self, root):
        self.root = root
        root.title('乏燃料运输容器智能运维系统 · 威布尔可靠性评估')
        root.geometry('1400x840')
        root.configure(bg=BG)

        self.param = tk.StringVar(value='加速度（峰值，单位 g）')
        self.cond = tk.StringVar(value='公路运输')
        self.method = tk.StringVar(value='mle')
        self.th_warn = tk.StringVar(value='')
        self.th_alarm = tk.StringVar(value='')

        self.build_ui()
        self.load_sample()

    # ---------- UI ----------
    def build_ui(self):
        # 左侧控制面板
        left = tk.Frame(self.root, bg=PANEL, width=330)
        left.pack(side='left', fill='y', padx=(12, 6), pady=12)
        left.pack_propagate(False)

        tk.Label(left, text='数据与参数设置', bg=PANEL, fg=ACCENT, font=('Microsoft YaHei', 12, 'bold')).pack(anchor='w', pady=(10, 6))

        tk.Label(left, text='监测参数', bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 9)).pack(anchor='w')
        ttk.Combobox(left, textvariable=self.param, state='readonly', width=26,
                     values=['加速度（峰值，单位 g）', '应变（累积形变，单位 με）', '温度（极值，单位 ℃）']).pack(fill='x', pady=2)
        self.param.trace_add('write', lambda *a: self._sync_param())

        tk.Label(left, text='典型工况', bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 9)).pack(anchor='w', pady=(8, 0))
        ttk.Combobox(left, textvariable=self.cond, state='readonly', width=26, values=CONDITIONS).pack(fill='x', pady=2)

        tk.Label(left, text='输入数据（寿命 / 极值样本，逗号、空格、换行分隔）', bg=PANEL, fg=MUTED,
                 font=('Microsoft YaHei', 9), wraplength=300, justify='left').pack(anchor='w', pady=(8, 0))
        self.data_text = tk.Text(left, height=7, bg=PANEL2, fg=TEXT, insertbackground=TEXT, relief='flat',
                                 font=('Consolas', 10), wrap='word')
        self.data_text.pack(fill='x', pady=3)

        btnrow = tk.Frame(left, bg=PANEL)
        btnrow.pack(fill='x', pady=4)
        tk.Button(btnrow, text='示例数据', command=self.load_sample, bg=PANEL2, fg=TEXT, relief='flat',
                  font=('Microsoft YaHei', 9)).pack(side='left', fill='x', expand=True, padx=1)
        tk.Button(btnrow, text='读 CSV', command=self.load_csv, bg=PANEL2, fg=TEXT, relief='flat',
                  font=('Microsoft YaHei', 9)).pack(side='left', fill='x', expand=True, padx=1)
        tk.Button(btnrow, text='清空', command=lambda: self.data_text.delete('1.0', 'end'), bg=PANEL2, fg=TEXT,
                  relief='flat', font=('Microsoft YaHei', 9)).pack(side='left', fill='x', expand=True, padx=1)

        tk.Label(left, text='拟合方法', bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 9)).pack(anchor='w', pady=(8, 0))
        mr = tk.Frame(left, bg=PANEL)
        mr.pack(fill='x')
        for val, txt in [('mle', '极大似然估计 MLE'), ('rank', '概率纸回归(最小二乘)'), ('both', '两者对比')]:
            tk.Radiobutton(mr, text=txt, variable=self.method, value=val, bg=PANEL, fg=TEXT, selectcolor=PANEL2,
                           activebackground=PANEL, activeforeground=ACCENT, anchor='w', font=('Microsoft YaHei', 9)).pack(anchor='w')

        tk.Label(left, text='三级阈值体系（分位数，可手动修改）', bg=PANEL, fg=MUTED,
                 font=('Microsoft YaHei', 9)).pack(anchor='w', pady=(8, 0))
        tr = tk.Frame(left, bg=PANEL)
        tr.pack(fill='x')
        tk.Label(tr, text='预警 P90', bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 9)).pack(side='left')
        tk.Entry(tr, textvariable=self.th_warn, bg=PANEL2, fg=TEXT, relief='flat', font=('Consolas', 10),
                 width=14).pack(side='left', padx=(4, 8))
        tr2 = tk.Frame(left, bg=PANEL)
        tr2.pack(fill='x', pady=3)
        tk.Label(tr2, text='报警 P99', bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 9)).pack(side='left')
        tk.Entry(tr2, textvariable=self.th_alarm, bg=PANEL2, fg=TEXT, relief='flat', font=('Consolas', 10),
                 width=14).pack(side='left', padx=(4, 8))

        tk.Button(left, text='▶  运行分析', command=self.run, bg=BLUE, fg='#ffffff', relief='flat',
                  font=('Microsoft YaHei', 11, 'bold'), activebackground='#2f6fd8', activeforeground='#fff').pack(fill='x', pady=(12, 4))

        tk.Label(left, text='说明：两参数威布尔分布 F(t)=1−exp(−(t/η)^β)。\nβ 形状参数、η 特征寿命；R(t) 表示“在载荷 t 下仍安全”的概率；\nβ>1 失效率递增（磨损期）、β<1 递减、β=1 退化为指数分布。',
                 bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 8), wraplength=300, justify='left').pack(anchor='w', pady=8)

        # 右侧结果区（可滚动）
        right = tk.Frame(self.root, bg=BG)
        right.pack(side='left', fill='both', expand=True, padx=(6, 12), pady=12)

        self.canvas_scroll = tk.Canvas(right, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(right, orient='vertical', command=self.canvas_scroll.yview)
        self.canvas_scroll.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.canvas_scroll.pack(side='left', fill='both', expand=True)

        self.result_frame = tk.Frame(self.canvas_scroll, bg=BG)
        self.result_window = self.canvas_scroll.create_window((0, 0), window=self.result_frame, anchor='nw')
        self.result_frame.bind('<Configure>', lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox('all')))
        self.canvas_scroll.bind('<Configure>', lambda e: self.canvas_scroll.itemconfigure(self.result_window, width=e.width))

        # 预建结果控件
        self._build_results()

    def _build_results(self):
        rf = self.result_frame
        # 参数卡片
        self.card_frame = tk.Frame(rf, bg=BG)
        self.card_frame.pack(fill='x')
        self.cards = {}
        card_keys = [('beta', '形状参数 β', ''), ('eta', '尺度(特征寿命) η', ''), ('mttf', '平均寿命 MTTF', ''),
                     ('median', '中位寿命 B50', ''), ('b10', 'B10 寿命', ''), ('sd', '标准差 σ', '')]
        for key, ktxt, _ in card_keys:
            f = tk.Frame(self.card_frame, bg=PANEL, padx=10, pady=8)
            f.pack(side='left', fill='x', expand=True, padx=4, pady=4)
            tk.Label(f, text=ktxt, bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 8)).pack(anchor='w')
            vlab = tk.Label(f, text='—', bg=PANEL, fg=TEXT, font=('Consolas', 14, 'bold'))
            vlab.pack(anchor='w')
            self.cards[key] = vlab

        # 统计行
        self.stat_label = tk.Label(rf, text='', bg=PANEL, fg=MUTED, font=('Microsoft YaHei', 9), justify='left',
                                   anchor='w', padx=10, pady=8, wraplength=1000)
        self.stat_label.pack(fill='x', pady=4)
        # 阈值行
        self.th_label = tk.Label(rf, text='', bg=PANEL, fg=TEXT, font=('Microsoft YaHei', 9), justify='left',
                                 anchor='w', padx=10, pady=6, wraplength=1000)
        self.th_label.pack(fill='x', pady=2)

        # 6 张图
        self.chart_defs = [
            ('可靠度曲线 R(t)   R(t)=exp(−(t/η)^β)', C_R),
            ('失效概率密度曲线 f(t)   f(t)=(β/η)(t/η)^(β−1)·exp(−(t/η)^β)', C_F),
            ('故障率（失效率）曲线 λ(t)   λ(t)=(β/η)(t/η)^(β−1)', C_L),
            ('累积失效概率 F(t)   F(t)=1−exp(−(t/η)^β)', C_FF),
            ('威布尔概率纸拟合直线   ln[−ln(1−F)]=β·ln t − β·ln η', C_R),
            ('经验可靠度（台阶函数）   R̂(tᵢ)=1−(i−0.3)/(n+0.4)', C_R),
        ]
        self.chart_canvases = []
        grid = tk.Frame(rf, bg=BG)
        grid.pack(fill='x')
        for idx, (title, _) in enumerate(self.chart_defs):
            box = tk.Frame(grid, bg=PANEL, padx=6, pady=6)
            box.grid(row=idx // 2, column=idx % 2, padx=4, pady=4, sticky='nsew')
            tk.Label(box, text=title, bg=PANEL, fg=TEXT, font=('Microsoft YaHei', 9, 'bold')).pack(anchor='w')
            cv = tk.Canvas(box, width=CW, height=CH, bg=PANEL, highlightthickness=0)
            cv.pack()
            self.chart_canvases.append(cv)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def _sync_param(self):
        pass

    def _param_key(self):
        p = self.param.get()
        if '加速' in p:
            return 'acc'
        if '应变' in p:
            return 'strain'
        return 'temp'

    # ---------- 逻辑 ----------
    def parse_data(self, txt):
        nums = []
        for tok in txt.replace(',', ' ').replace(';', ' ').replace('，', ' ').replace('、', ' ').split():
            try:
                v = float(tok)
            except ValueError:
                continue
            if v > 0:
                nums.append(v)
        return nums

    def load_sample(self):
        key = self._param_key()
        beta, eta, n = PRESETS[key]
        vals = sample_weibull(n, beta, eta)
        self.data_text.delete('1.0', 'end')
        self.data_text.insert('1.0', ', '.join('%.2f' % v for v in vals))

    def load_csv(self):
        path = filedialog.askopenfilename(title='选择数据文件', filetypes=[('CSV/文本', '*.csv *.txt'), ('所有文件', '*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                self.data_text.delete('1.0', 'end')
                self.data_text.insert('1.0', f.read())
        except Exception as e:
            messagebox.showerror('读取失败', str(e))

    def run(self):
        pkey = self._param_key()
        unit = PARAM_UNIT[pkey]
        pname = PARAM_NAME[pkey]
        method = self.method.get()
        data = self.parse_data(self.data_text.get('1.0', 'end'))

        if len(data) < 3:
            messagebox.showwarning('数据不足', '样本量需 ≥ 3 个正数，请检查输入数据。')
            return
        s = sorted(data)
        n = len(data)
        if s[0] == s[-1]:
            messagebox.showwarning('无法拟合', '输入数据全部相同，无法进行分布拟合。')
            return

        mle = weibull_mle(data)
        rk = weibull_rank(data)
        beta, eta = mle if method != 'rank' else rk
        if method == 'both':
            beta, eta = mle
        mttf, median, b10, sd = weibull_stats(beta, eta)

        mean = sum(data) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in data) / (n - 1))
        cv = std / mean * 100
        p50 = quantile(s, 0.5)
        p90 = quantile(s, 0.9)
        p99 = quantile(s, 0.99)

        th_w = float(self.th_warn.get()) if self.th_warn.get().strip() else p90
        th_a = float(self.th_alarm.get()) if self.th_alarm.get().strip() else p99
        self.th_warn.set(fmt(th_w)); self.th_alarm.set(fmt(th_a))
        over_w = sum(1 for v in data if v > th_w)
        over_a = sum(1 for v in data if v > th_a)

        # 更新卡片
        self.cards['beta'].config(text=fmt(beta))
        self.cards['eta'].config(text=fmt(eta) + ' ' + unit)
        self.cards['mttf'].config(text=fmt(mttf) + ' ' + unit)
        self.cards['median'].config(text=fmt(median) + ' ' + unit)
        self.cards['b10'].config(text=fmt(b10) + ' ' + unit)
        self.cards['sd'].config(text=fmt(sd) + ' ' + unit)

        cmp_txt = ''
        if method == 'both':
            cmp_txt = '　对比：MLE β=%s η=%s ｜ 概率纸回归 β=%s η=%s' % (fmt(mle[0]), fmt(mle[1]), fmt(rk[0]), fmt(rk[1]))
        self.stat_label.config(
            text='样本量 n=%d　拟合优度 ρ=%.4f (R²=%.4f)　均值 %s %s　峰值 %s %s　极差 %s %s　变异系数 %s%%%s' % (
                n, rk[2], rk[2] ** 2, fmt(mean), unit, fmt(s[-1]), unit, fmt(s[-1] - s[0]), unit, fmt(cv), cmp_txt))
        self.th_label.config(
            text='三级阈值体系：正常 ≤ %s ｜ 预警 %s（超限 %d 次）｜ 报警 %s（超限 %d 次）' % (
                fmt(p50), fmt(th_w), over_w, fmt(th_a), over_a))

        # 绘制曲线
        tmin, tmax = min(data) * 0.6, max(data) * 1.15
        N = 240
        T = [tmin + (tmax - tmin) * i / N for i in range(N + 1)]
        R = [math.exp(-(t / eta) ** beta) for t in T]
        F = [1 - r for r in R]
        fpdf = [(beta / eta) * (t / eta) ** (beta - 1) * math.exp(-(t / eta) ** beta) for t in T]
        hzd = [(beta / eta) * (t / eta) ** (beta - 1) for t in T]

        empR, probPts = [], []
        for i in range(n):
            Fi = (i + 1 - 0.3) / (n + 0.4)
            empR.append((s[i], 1 - Fi))
            probPts.append((s[i], Fi))

        Fmin = max(0.002, min(p[1] for p in probPts) * 0.6)
        Fmax = min(0.995, max(p[1] for p in probPts) * 1.2)
        tplo, tphi = min(data) * 0.5, max(data) * 1.3

        bins, bw = histogram(data, math.sqrt(n) * 1.6)
        bins = [(x0, x1, c / (n * bw)) for x0, x1, c in bins]
        ymax_pdf = max(max(fpdf), max(c for _, _, c in bins)) * 1.15

        # 概率纸直线
        lnT = [tplo * (tphi / tplo) ** (i / N) for i in range(N + 1)]
        prob_line = [(t, 1 - math.exp(-(t / eta) ** beta)) for t in lnT]

        # 台阶
        step = [(s[i], 1 - (i + 1 - 0.3) / (n + 0.4)) for i in range(n)]
        step_line = [(tmin, 1.0)] + step + [(tmax, step[-1][1])]

        charts = [
            dict(x_range=[tmin, tmax], y_range=[0, 1], xlabel='时间/载荷 t (%s)' % unit, ylabel='可靠度 R(t)',
                 lines=[dict(data=list(zip(T, R)), color=C_R)],
                 points=[(t, r, C_PT) for t, r in empR],
                 reflines=[(0.5, '#fbbf24', 'R=50%'), (0.9, '#fbbf24', 'R=90%')]),
            dict(x_range=[tmin, tmax], y_range=[0, ymax_pdf], xlabel='时间/载荷 t (%s)' % unit, ylabel='概率密度 f(t)',
                 hist=bins, lines=[dict(data=list(zip(T, fpdf)), color=C_F)]),
            dict(x_range=[tmin, tmax], y_range=[0, max(hzd) * 1.1], xlabel='时间/载荷 t (%s)' % unit, ylabel='故障率 λ(t)',
                 lines=[dict(data=list(zip(T, hzd)), color=C_L)]),
            dict(x_range=[tmin, tmax], y_range=[0, 1], xlabel='时间/载荷 t (%s)' % unit, ylabel='累积失效概率 F(t)',
                 lines=[dict(data=list(zip(T, F)), color=C_FF)],
                 points=[(t, ff, C_PT) for t, ff in probPts],
                 reflines=[(0.632, '#fbbf24', 'F=63.2%')]),
            dict(x_range=[tplo, tphi], y_range=[lnln(Fmin), lnln(Fmax)], x_scale='log', y_scale='weibull',
                 xlabel='时间/载荷 t (%s) 对数坐标' % unit, ylabel='累积失效概率 F(t)',
                 lines=[dict(data=prob_line, color=C_R)],
                 points=[(t, ff, C_PT) for t, ff in probPts]),
            dict(x_range=[tmin, tmax], y_range=[0, 1], xlabel='时间/载荷 t (%s)' % unit, ylabel='经验可靠度 R̂(t)',
                 lines=[dict(data=step_line, color=C_R)],
                 points=[(t, r, C_R) for t, r in step]),
        ]
        for cv, cfg in zip(self.chart_canvases, charts):
            draw_chart(cv, cfg)


def main():
    root = tk.Tk()
    # 深色主题基础样式
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    style.configure('TCombobox', fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=TEXT)
    style.map('TCombobox', fieldbackground=[('readonly', PANEL2)])
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
