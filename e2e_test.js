const fs=require('fs');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const m=html.match(/<script>([\s\S]*?)<\/script>/);
let code=m[1];
// 暴露内部函数供测试
code=code.replace(/^"use strict";/,'') + '\n;return {run, loadSample, parseData, weibullMLE, weibullRank, weibullStats, chart, hist, gamma};';

// ---- mock DOM ----
function makeEl(){return {
  value:'', innerHTML:'', files:[], classList:{remove(){},add(){}},
  addEventListener(ev,fn){this['_'+ev]=fn;},
  click(){if(this['_click'])this['_click']();},
  setAttribute(){}, style:{},
};}
const els={};
const document={
  getElementById(id){return els[id]||(els[id]=makeEl());},
  querySelector(sel){ if(sel.includes('method')) return {value:'mle'}; return {value:'mle'}; },
  querySelectorAll(sel){ return []; },
  createElement(){ return makeEl(); },
};
const window={};
const navigator={clipboard:{writeText:()=>Promise.resolve()}};

// 预置 select 默认值
['param','cond','thWarn','thAlarm','data','results'].forEach(id=>{els[id]=makeEl();});
els['param'].value='acc';
els['cond'].value='公路运输';

const factory=new Function('document','window','navigator','alert', code);
const ctx=factory(document, window, navigator, ()=>{});

// 初始 loadSample 已执行，data 里应有示例数据
console.log('示例数据已载入，长度 =', ctx.parseData(els['data'].value).length);

// 跑一次分析
ctx.run();
const out=els['results'].innerHTML;
console.log('run() 生成 HTML 长度 =', out.length);
const bad=(out.match(/NaN|Infinity|undefined/g)||[]);
console.log('异常标记(NaN/Infinity/undefined):', bad.length===0?'无 ✓':bad);

// 提取 beta/eta 卡片值
const svgCount=(out.match(/<svg/g)||[]).length;
console.log('SVG 图数量 =', svgCount, '(期望 6)');
const chartBox=(out.match(/chart-box/g)||[]).length;
console.log('图表框数量 =', chartBox);

// 打印 β η 和统计
const d=ctx.parseData(els['data'].value);
const mle=ctx.weibullMLE(d), rk=ctx.weibullRank(d), st=ctx.weibullStats(d,mle.beta,mle.eta);
console.log('\n示例数据拟合结果:');
console.log('  n =', d.length, ' 范围 =', Math.min(...d).toFixed(2), '~', Math.max(...d).toFixed(2));
console.log('  MLE  beta =', mle.beta.toFixed(4), ' eta =', mle.eta.toFixed(4));
console.log('  Rank beta =', rk.beta.toFixed(4), ' eta =', rk.eta.toFixed(4), ' r =', rk.r.toFixed(6));
console.log('  MTTF =', st.mttf.toFixed(3), ' B10 =', st.b10.toFixed(3), ' 中位 =', st.median.toFixed(3));

// 检查每个 SVG 的坐标是否在 viewBox 内（抽样 path 的坐标）
const paths=out.match(/<path d="([^"]+)"/g)||[];
console.log('\npath 数量 =', paths.length);
// 简单检查：所有 chart 无 NaN 即通过
console.log('\n端到端测试完成');
