# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\l\Documents\deepseek-harness\default-workspace\weibull-tool')
import tkinter as tk
import app

root = tk.Tk()
a = app.App(root)          # 构建 UI + 载入示例数据
root.update()              # 让界面实际渲染

# 数据是否载入
txt = a.data_text.get('1.0', 'end').strip()
print('示例数据已载入, 数据点数 =', len(a.parse_data(txt)))

# 运行分析（计算 + 更新卡片 + 画 6 张图）
a.run()
root.update()

print('beta 卡片 =', a.cards['beta'].cget('text'))
print('eta 卡片 =', a.cards['eta'].cget('text'))
print('统计行 =', a.stat_label.cget('text')[:80])
print('阈值行 =', a.th_label.cget('text'))

# 检查每张图是否画了内容（canvas item 数）
for i, cv in enumerate(a.chart_canvases):
    items = cv.find_all()
    print('图表 %d: canvas 元素数 = %d' % (i + 1, len(items)))

root.destroy()
print('GUI 端到端测试通过')
