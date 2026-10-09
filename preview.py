# -*- coding: utf-8 -*-
# 用 Pillow 手绘一份威布尔曲线预览，交叉验证公式与拟合结果
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def gamma(z):
    if z < 0.5:
        return np.pi/(np.sin(np.pi*z)*gamma(1-z))
    z -= 1
    C = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
         -176.61502916214059, 12.507343278686905, -0.13857109526572012,
         9.9843695780195716e-6, 1.5056327351493116e-7]
    g = 7; x = C[0]
    for i in range(1, g+2):
        x += C[i]/(z+i)
    t = z+g+0.5
    return np.sqrt(2*np.pi)*t**(z+0.5)*np.exp(-t)*x

def weibull_mle(data):
    n = len(data); tmax = data.max()
    w = data/tmax; lnT = np.log(data); meanLn = lnT.mean()
    def g(b):
        wb = w**b
        s1 = (wb*lnT).sum(); s2 = wb.sum()
        return s1/s2 - 1.0/b - meanLn
    lo, hi = 0.02, 1.0
    while g(hi) <= 0 and hi < 1e9: hi *= 2
    while g(lo) >= 0 and lo > 1e-9: lo /= 2
    for _ in range(90):
        mid = (lo+hi)/2
        if g(mid) < 0: lo = mid
        else: hi = mid
    beta = (lo+hi)/2
    eta = tmax*(np.power(data/tmax, beta).sum()/n)**(1/beta)
    return beta, eta

rng = np.random.default_rng(42)
TRUE_B, TRUE_E, N = 2.5, 100.0, 200
data = TRUE_E*rng.weibull(TRUE_B, N)
beta, eta = weibull_mle(data)

tmin, tmax = data.min()*0.6, data.max()*1.15
T = np.linspace(tmin, tmax, 300)
R = np.exp(-(T/eta)**beta)
F = 1-R
f = (beta/eta)*(T/eta)**(beta-1)*R
h = (beta/eta)*(T/eta)**(beta-1)

# 中位秩
s = np.sort(data)
n = len(s)
Fi = (np.arange(1, n+1)-0.3)/(n+0.4)
xs = np.log(s); ys = np.log(-np.log(1-Fi))

# ---- 画布 ----
W2, H2 = 1500, 980
img = Image.new("RGB", (W2, H2), (15, 23, 32))
dr = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    font_s = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
except:
    font = ImageFont.load_default(); font_s = font

def fname(txt): return txt

# 子图区域 (x0,y0,x1,y1)
grid = [(60,60,720,470),(790,60,1450,470),(60,520,720,930),(790,520,1450,930)]
titles = ["Reliability R(t) = exp(-(t/eta)^b)",
          "Failure density f(t)  (hist + fitted)",
          "CDF F(t) = 1-exp(-(t/eta)^b)",
          "Hazard rate lambda(t) = (b/eta)(t/eta)^(b-1)"]
colors = [(34,211,238),(52,211,153),(167,139,250),(251,191,36)]

def draw_axes(box, xlabel, ylabel):
    x0,y0,x1,y1 = box
    dr.rectangle([x0,y0,x1,y1], outline=(42,59,80), width=1)
    dr.line([(x0,y1),(x1,y1)], fill=(42,59,80))  # 底轴
    dr.line([(x0,y0),(x0,y1)], fill=(42,59,80))  # 左轴
    dr.text((x0+8, y0+6), ylabel, fill=(199,212,229), font=font_s)
    dr.text((x1-10, y1-22), xlabel, fill=(143,163,187), font=font_s, anchor="ra")

def xy_map(box, xlo, xhi, ylo, yhi):
    x0,y0,x1,y1 = box
    def px(x): return x0 + (x-xlo)/(xhi-xlo)*(x1-x0)
    def py(y): return y1 - (y-ylo)/(yhi-ylo)*(y1-y0)
    return px, py

# 1 R(t)
box = grid[0]
draw_axes(box, "t", "R(t)")
px,py = xy_map(box, tmin, tmax, 0, 1)
pts = [(px(t),py(r)) for t,r in zip(T,R)]
dr.line(pts, fill=colors[0], width=3)
for t,fr in zip(s, 1-Fi):
    dr.ellipse([px(t)-2,py(fr)-2,px(t)+2,py(fr)+2], fill=(59,130,246))
dr.text((box[0]+12, box[1]+12), titles[0], fill=(230,237,245), font=font)

# 2 f(t) + 直方图
box = grid[1]
nbins = int(np.sqrt(n)*1.6)
hist, edges = np.histogram(data, bins=nbins, range=(data.min(), data.max()))
binw = edges[1]-edges[0]
density = hist/(n*binw)
ymax = max(density.max(), f.max())*1.15
draw_axes(box, "t", "f(t)")
px,py = xy_map(box, tmin, tmax, 0, ymax)
for c,e0,e1 in zip(density, edges[:-1], edges[1:]):
    ytop = py(c); ybot = py(0)
    dr.rectangle([px(e0)+1, ytop, px(e1)-1, ybot], fill=(36,64,89))
pts = [(px(t),py(v)) for t,v in zip(T,f)]
dr.line(pts, fill=colors[1], width=3)
dr.text((box[0]+12, box[1]+12), titles[1], fill=(230,237,245), font=font)

# 3 F(t)
box = grid[2]
draw_axes(box, "t", "F(t)")
px,py = xy_map(box, tmin, tmax, 0, 1)
dr.line([(px(t),py(v)) for t,v in zip(T,F)], fill=colors[2], width=3)
for t,fr in zip(s, Fi):
    dr.ellipse([px(t)-2,py(fr)-2,px(t)+2,py(fr)+2], fill=(59,130,246))
dr.line([(box[0],py(0.632)),(box[2],py(0.632))], fill=(251,191,36), width=1)
dr.text((box[0]+12, box[1]+12), titles[2], fill=(230,237,245), font=font)

# 4 lambda(t)
box = grid[3]
draw_axes(box, "t", "lambda(t)")
px,py = xy_map(box, tmin, tmax, 0, h.max()*1.1)
dr.line([(px(t),py(v)) for t,v in zip(T,h)], fill=colors[3], width=3)
dr.text((box[0]+12, box[1]+12), titles[3], fill=(230,237,245), font=font)

img.save(r"C:\Users\l\Documents\deepseek-harness\default-workspace\weibull-tool\preview.png")
print("true beta=%.3f eta=%.3f | MLE beta=%.4f eta=%.4f" % (TRUE_B, TRUE_E, beta, eta))
print("saved preview.png")
