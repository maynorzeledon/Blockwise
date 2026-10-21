/* First document launch only; navigation, category changes and resume never replay it. */
(()=>{
 const intro=document.getElementById('blockwise-intro');if(!intro)return;
 let seen=false;try{seen=sessionStorage.getItem('blockwise-intro-seen')==='1';sessionStorage.setItem('blockwise-intro-seen','1')}catch{}
 const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(seen||reduced){intro.remove();return}
 window.BlockwiseIntroActive=true;window.BlockwiseNative?.setChromeDark(true);
 let finished=false;function finish(){if(finished)return;finished=true;window.BlockwiseIntroActive=false;intro.remove();let theme='system';try{theme=JSON.parse(localStorage.getItem('blockwise')||'{}').theme||'system'}catch{}window.BlockwiseTheme?.apply(theme)}
 // No input blocking or audio autoplay. CSS also hides the overlay without JS.
 intro.addEventListener('animationend',e=>{if(e.target===intro&&e.animationName==='intro-away')finish()});
 setTimeout(finish,2300);
})();
