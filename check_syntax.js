const fs=require('fs');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const m=html.match(/<script>([\s\S]*?)<\/script>/);
if(!m){console.error('no script block');process.exit(1);}
try{
  new Function(m[1]);
  console.log('JS 语法检查通过 ✓ (script 长度:', m[1].length, '字符)');
}catch(e){
  console.error('语法错误:', e.message);
  process.exit(1);
}
// 顺便确认关键函数都在
for(const fn of ['gamma','weibullMLE','weibullRank','weibullStats','chart','run','loadSample','parseData']){
  console.log('  ', fn, ':', m[1].includes('function '+fn)||m[1].includes('function '+fn) ? 'OK':'MISSING');
}
