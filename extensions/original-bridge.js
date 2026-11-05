// 기존 함수·이벤트·저장소를 교체하지 않는다. 명시적 요청 때 추출 원문만 읽는다.
(()=>{'use strict';let selectedFile=null,analysisBeforeSelection=null;
document.addEventListener('change',event=>{
 if(!['file-input','cam-input'].includes(event.target.id)||!event.target.files?.[0])return;
 selectedFile=event.target.files[0];analysisBeforeSelection=typeof activeAnalysis!=='undefined'?activeAnalysis:null;
},true);
window.addEventListener('message',event=>{
 if(event.origin!==location.origin||event.source!==window.parent||event.data?.type!=='contract-addon:read')return;
 const analysis=typeof activeAnalysis!=='undefined'?activeAnalysis:null;
 const file=typeof pending!=='undefined'?pending:null;
 const ready=!selectedFile||file?.file===selectedFile;
 const fresh=analysis&&analysis!==analysisBeforeSelection;
 const text=ready?(fresh?analysis.text:file?.text||''):'';
 window.parent.postMessage({type:'contract-addon:text',text,name:file?.name||analysis?.name||'원본에서 가져온 계약'},location.origin);
});})();
