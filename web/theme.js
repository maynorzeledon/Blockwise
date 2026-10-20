(function(){
 const media=typeof matchMedia==='function'?matchMedia('(prefers-color-scheme: dark)'):null;
 let preference='system';try{const value=JSON.parse(localStorage.getItem('blockwise')||'{}').theme;if(['system','light','dark'].includes(value))preference=value}catch{}
 function apply(value){preference=['system','light','dark'].includes(value)?value:'system';const dark=preference==='dark'||(preference==='system'&&(window.BlockwiseNative?.isSystemDark?BlockwiseNative.isSystemDark():!!media?.matches));const root=document.documentElement;root.dataset.theme=dark?'dark':'light';root.style.colorScheme=dark?'dark':'light';root.style.backgroundColor=dark?'#111e19':'#f5f5ed';document.body?.classList.toggle('dark',dark);document.querySelector('meta[name="theme-color"]')?.setAttribute('content',dark?'#111e19':'#f5f5ed');return dark}
 apply(preference);media?.addEventListener?.('change',()=>apply(preference));window.BlockwiseTheme={apply};
})();
