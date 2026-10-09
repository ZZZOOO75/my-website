// Mirror of the app's math to verify correctness
function gamma(z){
  if(z<0.5) return Math.PI/(Math.sin(Math.PI*z)*gamma(1-z));
  z-=1;
  const C=[0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,
           -176.61502916214059,12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
  const g=7; let x=C[0];
  for(let i=1;i<g+2;i++) x+=C[i]/(z+i);
  const t=z+g+0.5;
  return Math.sqrt(2*Math.PI)*Math.pow(t,z+0.5)*Math.exp(-t)*x;
}
function linreg(xs,ys){
  const n=xs.length; if(n<2) return {slope:0,intercept:0,r:0};
  let sx=0,sy=0,sxx=0,syy=0,sxy=0;
  for(let i=0;i<n;i++){sx+=xs[i];sy+=ys[i];sxx+=xs[i]*xs[i];syy+=ys[i]*ys[i];sxy+=xs[i]*ys[i];}
  const den=(n*sxx-sx*sx);
  const slope=den===0?0:(n*sxy-sx*sy)/den;
  const intercept=(sy-slope*sx)/n;
  const r=(n*sxy-sx*sy)/Math.sqrt((n*sxx-sx*sx)*(n*syy-sy*sy)||1);
  return {slope,intercept,r};
}
function weibullMLE(data){
  const n=data.length;
  const tmax=Math.max(...data);
  const w=data.map(t=>t/tmax);        // 0 < w <= 1, 数值稳定
  const lnT=data.map(t=>Math.log(t));
  const meanLn=lnT.reduce((a,b)=>a+b,0)/n;
  // g(beta) 单调递增；稳定形式：sum(w^b ln t)/sum(w^b) - 1/b - mean(ln t)
  const g=b=>{
    let s1=0,s2=0;
    for(let i=0;i<n;i++){const wb=Math.pow(w[i],b);s1+=wb*lnT[i];s2+=wb;}
    return s1/s2 - 1/b - meanLn;
  };
  let lo=0.02, hi=1;
  while(g(hi)<=0 && hi<1e9) hi*=2;      // 保证 g(hi)>0
  while(g(lo)>=0 && lo>1e-9) lo/=2;     // 保证 g(lo)<0
  for(let i=0;i<90;i++){const mid=(lo+hi)/2; if(g(mid)<0) lo=mid; else hi=mid;}
  const beta=(lo+hi)/2;
  let s2=0; for(const t of data) s2+=Math.pow(t/tmax,beta);
  const eta=tmax*Math.pow(s2/n,1/beta);
  return {beta,eta};
}
function weibullRank(data){
  const n=data.length;
  const s=[...data].sort((a,b)=>a-b);
  const xs=[],ys=[];
  for(let i=0;i<n;i++){
    const F=(i+1-0.3)/(n+0.4);
    xs.push(Math.log(s[i])); ys.push(Math.log(-Math.log(1-F)));
  }
  const {slope,intercept,r}=linreg(xs,ys);
  return {beta:slope, eta:Math.exp(-intercept/slope), r};
}
// deterministic LCG for reproducible sampling
let seed=123456789;
function rnd(){seed=(seed*1664525+1013904223)>>>0; return seed/4294967296;}
function sampleWeibull(n,beta,eta){const o=[];for(let i=0;i<n;i++)o.push(eta*Math.pow(-Math.log(1-rnd()),1/beta));return o;}

// tests
console.log("gamma(1.5) =", gamma(1.5), "(expect ~0.88623)");
console.log("gamma(2)   =", gamma(2), "(expect 1)");
console.log("gamma(0.5) =", gamma(0.5), "(expect ~1.77245)");

const TRUE_B=2.5, TRUE_E=100;
for(const n of [30, 100, 2000]){
  const d=sampleWeibull(n,TRUE_B,TRUE_E);
  const mle=weibullMLE(d), rk=weibullRank(d);
  console.log(`\nn=${n}  (true beta=2.5, eta=100)`);
  console.log(`  MLE  beta=${mle.beta.toFixed(4)}  eta=${mle.eta.toFixed(4)}`);
  console.log(`  Rank beta=${rk.beta.toFixed(4)}  eta=${rk.eta.toFixed(4)}  r=${rk.r.toFixed(6)}`);
}
// edge: exponential (beta=1)
let seed2=7;
function rnd2(){seed2=(seed2*1664525+1013904223)>>>0; return seed2/4294967296;}
const expData=[];for(let i=0;i<500;i++)expData.push(50*(-Math.log(1-rnd2())));
console.log("\nExponential (beta=1, eta=50):", JSON.stringify(weibullMLE(expData)));
