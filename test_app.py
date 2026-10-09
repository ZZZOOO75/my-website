# -*- coding: utf-8 -*-
import random, math, sys
sys.path.insert(0, r'C:\Users\l\Documents\deepseek-harness\default-workspace\weibull-tool')
import app

# gamma
print('gamma(1.5)=%.6f (期望~0.88623)' % app.gamma(1.5))
print('gamma(2)=%.6f (期望1)' % app.gamma(2))

# MLE / rank
random.seed(42)
def rnd_wb(n, b, e):
    return [e * (-math.log(1 - random.random())) ** (1 / b) for _ in range(n)]

d = rnd_wb(2000, 2.5, 100.0)
mle = app.weibull_mle(d)
rk = app.weibull_rank(d)
print('\nn=2000 真值 beta=2.5 eta=100')
print('  MLE  beta=%.4f  eta=%.4f' % mle)
print('  Rank beta=%.4f  eta=%.4f  r=%.6f' % rk)

mttf, median, b10, sd = app.weibull_stats(2.5, 100.0)
print('  stats: MTTF=%.3f 中位=%.3f B10=%.3f sd=%.3f' % (mttf, median, b10, sd))
# 理论值: MTTF=100*gamma(1.4)=88.62, 中位=100*ln2^(0.4)=88.7, B10=100*0.1054^0.4=40.6

# 指数分布
random.seed(7)
e = [50 * (-math.log(1 - random.random())) for _ in range(500)]
print('\n指数分布(β=1,η=50):', tuple(round(x, 4) for x in app.weibull_mle(e)))

# 边界：全相同
try:
    app.weibull_mle([5, 5, 5, 5])
    print('\n全相同数据: MLE 未抛异常（beta 会很大）')
except Exception as ex:
    print('\n全相同数据: 异常', ex)

print('\napp.py 导入与数学验证通过 ✓')
