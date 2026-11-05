// 사용자가 버튼으로 보낸 원문만 추가 화면에 채운다. 자동 분석·저장은 하지 않는다.
(()=>{'use strict';window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==window.parent||event.data?.type!=='contract-addon:fill')return;
 if(typeof event.data.text!=='string'||event.data.text.length>100000||busy)return;
 upload={...upload,text:event.data.text,name:String(event.data.name||'가져온 계약').slice(0,120),sample:false,mode:'demo'};
 status='원본에서 가져왔습니다. 계약 유형과 원문을 다시 확인하세요.';go('upload');
});})();
