(function(){var p=document.getElementById('prog');addEventListener('scroll',function(){var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';},{passive:true});
var sizes=[16,17,18,20,22],k=2;try{var s=localStorage.getItem('__KEY__-fs');if(s)k=+s;var d=localStorage.getItem('__KEY__-dark');if(d==='1')document.documentElement.classList.add('dark');}catch(e){}
function ap(){document.body.style.fontSize=sizes[k]+'px';}ap();
document.getElementById('fs').onclick=function(){k=(k+1)%sizes.length;ap();try{localStorage.setItem('__KEY__-fs',k)}catch(e){}};
document.getElementById('th').onclick=function(){var on=document.documentElement.classList.toggle('dark');try{localStorage.setItem('__KEY__-dark',on?'1':'0')}catch(e){}};})();
