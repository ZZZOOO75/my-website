const fs=require('fs');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const m=html.match(/<script>([\s\S]*?)<\/script>/);
let code=m[1].replace(/^"use strict";/,'') + '\n;return {run, loadSample, parseData, weibullMLE, weibullRank, weibullStats, chart, hist, gamma};';

function makeEl(){return {value:'',innerHTML:'',files:[],classList:{remove(){},add(){}},addEventListener(ev,fn){this['_'+ev]=fn;},click(){},setAttribute(){},style:{}};}
const els={};
const document={
  getElementById(id){return els[id]||(els[id]=makeEl());},
  querySelector(sel){return {value:'mle'};},
  querySelectorAll(sel){return [];},
  createElement(){return makeEl();},
};
['param','cond','thWarn','thAlarm','data','results'].forEach(id=>{els[id]=makeEl();});
els['param'].value='acc'; els['cond'].value='公路运输';
const factory=new Function('document','window','navigator','alert', code);
const ctx=factory(document, {}, {clipboard:{writeText:()=>Promise.resolve()}}, ()=>{});
ctx.run();
const out=els['results'].innerHTML;

// 定位每个 svg 是否含 NaN
const svgs=out.split('<svg');
svgs.forEach((s,i)=>{
  if(i===0) return;
  const nan=(s.match(/NaN/g)||[]).length;
  console.log(`SVG ${i}: NaN 数量 = ${nan}`);
  if(nan>0){
    let idx=s.indexOf('NaN');
    console.log('   上下文:', JSON.stringify(s.slice(Math.max(0,idx-80), idx+80)));
  }
});
