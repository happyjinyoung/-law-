'use strict';
const original=document.getElementById('original'),service=document.getElementById('service');
const status=document.getElementById('status');let transferPending=false;
function switchTab(tab){const added=tab==='service';original.hidden=added;service.hidden=!added;document.getElementById('original-tab').setAttribute('aria-pressed',String(!added));document.getElementById('service-tab').setAttribute('aria-pressed',String(added));}
function inject(frame,path){const script=frame.contentDocument.createElement('script');script.src=path;frame.contentDocument.body.appendChild(script);}
original.addEventListener('load',()=>inject(original,'/original-bridge.js'));
service.addEventListener('load',()=>inject(service,'/service-bridge.js'));
document.getElementById('original-tab').addEventListener('click',()=>{switchTab('original');status.textContent='원본 저장소: 브라우저 localStorage·IndexedDB. 기존 파일·기능은 변경하지 않았습니다.';});
document.getElementById('service-tab').addEventListener('click',()=>{switchTab('service');status.textContent='추가 저장소: Python 서버의 SQLite. 원본 데이터와 별도이며 자동 병합·삭제하지 않습니다.';});
document.getElementById('transfer').addEventListener('click',()=>{transferPending=true;original.contentWindow.postMessage({type:'contract-addon:read'},location.origin);status.textContent='원본에서 추출된 원문을 확인 중…';});
window.addEventListener('message',event=>{
 if(event.origin!==location.origin)return;
 if(event.source===original.contentWindow&&event.data?.type==='contract-addon:text'&&transferPending){
  transferPending=false;const {text,name}=event.data;
  if(typeof text!=='string'||!text.trim()){status.textContent='보낼 원문이 없습니다. 기존 화면에서 PDF를 읽거나 사진 OCR을 완료하세요. 추가 화면에서 직접 입력·TXT 업로드도 가능합니다.';return;}
  if(text.length>100000){status.textContent='추가 서버 원문 한도는 100,000자입니다. 추가 화면에서 필요한 부분을 확인·입력하세요.';return;}
  service.contentWindow.postMessage({type:'contract-addon:fill',text,name},location.origin);switchTab('service');status.textContent='원문을 복사했습니다. 추가 화면에서 이름·유형·원문을 확인한 뒤 분석하세요. 원본 데이터는 그대로입니다.';
 }
});
