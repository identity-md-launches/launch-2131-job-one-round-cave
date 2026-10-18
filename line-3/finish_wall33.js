/* Transfer only generated earth-pigment colors onto untouched ancestor pixels. */
'use strict';
const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
const assert = require('assert');
const encodeJPEG = require('./tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const crcTable = Array.from({length:256}, (_, n) => {
  for (let k=0;k<8;k++) n=(n&1)?0xedb88320^(n>>>1):n>>>1;
  return n>>>0;
});
function crc32(bytes) {
  let crc=0xffffffff;
  for (const b of bytes) crc=crcTable[(crc^b)&255]^(crc>>>8);
  return (crc^0xffffffff)>>>0;
}
function readPNG(bytes) {
  assert(bytes.subarray(0,8).equals(Buffer.from('89504e470d0a1a0a','hex')));
  let width,height,channels;
  const parts=[];
  for(let at=8;at<bytes.length;) {
    const n=bytes.readUInt32BE(at),kind=bytes.toString('ascii',at+4,at+8);
    const body=bytes.subarray(at+8,at+8+n);
    assert.equal(crc32(bytes.subarray(at+4,at+8+n)),bytes.readUInt32BE(at+8+n));
    if(kind==='IHDR') {
      width=body.readUInt32BE(0);height=body.readUInt32BE(4);
      assert.equal(body[8],8);assert.equal(body[9],2);assert.equal(body[10]+body[11]+body[12],0);channels=3;
    } else if(kind==='IDAT') parts.push(body);
    else if(kind==='IEND') break;
    at+=n+12;
  }
  const stride=width*channels,packed=zlib.inflateSync(Buffer.concat(parts));
  assert.equal(packed.length,height*(stride+1));
  const pixels=Buffer.alloc(width*height*channels);
  for(let y=0;y<height;y++) for(let x=0;x<stride;x++) {
    const at=y*stride+x,left=x>=3?pixels[at-3]:0,above=y?pixels[at-stride]:0;
    const diagonal=y&&x>=3?pixels[at-stride-3]:0,filter=packed[y*(stride+1)];
    const v=packed[y*(stride+1)+x+1];let p=0;
    if(filter===1)p=left;
    if(filter===2)p=above;
    if(filter===3)p=(left+above)>>>1;
    if(filter===4){const q=left+above-diagonal,a=Math.abs(q-left),b=Math.abs(q-above),c=Math.abs(q-diagonal);p=a<=b&&a<=c?left:b<=c?above:diagonal;}
    assert(filter<=4);pixels[at]=(v+p)&255;
  }
  return {width,height,pixels};
}
function writePNG(width,height,pixels) {
  function chunk(kind,body){const data=Buffer.concat([Buffer.from(kind),body]),a=Buffer.alloc(4),b=Buffer.alloc(4);a.writeUInt32BE(body.length);b.writeUInt32BE(crc32(data));return Buffer.concat([a,data,b]);}
  const header=Buffer.alloc(13);header.writeUInt32BE(width,0);header.writeUInt32BE(height,4);header[8]=8;header[9]=2;
  const raw=Buffer.alloc(height*(width*3+1));
  for(let y=0;y<height;y++)pixels.copy(raw,y*(width*3+1)+1,y*width*3,(y+1)*width*3);
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(raw,{level:9})),chunk('IEND',Buffer.alloc(0))]);
}
function finish(draftBytes) {
  const ancestorPath='artifacts/line-3/wall-v12.png',outputPath='artifacts/line-3/wall-v13.png';
  const oldBytes=fs.readFileSync(ancestorPath);
  assert.equal(hash(oldBytes),'a9a7bee6a91fe28908b6443f083dafc4c8ca41dce1ea88409db06d28acf15692');
  if(fs.existsSync('dist/line-3/33.json')){
    const previous=JSON.parse(fs.readFileSync('dist/line-3/33.json','utf8'));
    assert.equal(previous.attributes?.find(a=>a.trait_type==='Number')?.value,33);
  }
  const old=readPNG(oldBytes),draft=readPNG(draftBytes);
  assert.deepEqual([old.width,old.height],[1254,1254]);
  assert.deepEqual([draft.width,draft.height],[1254,1254]);
  // The generated image repeats the full wall. Use only its new mark's small,
  // previously unused rock patch; restore actual inherited pixels everywhere else.
  const rect=[1070,815,140,100],final=Buffer.from(old.pixels);
  for(let y=0;y<rect[3];y++)for(let x=0;x<rect[2];x++) {
    const at=((rect[1]+y)*old.width+rect[0]+x)*3;
    const [r,g,b]=draft.pixels.subarray(at,at+3),[or,og,ob]=old.pixels.subarray(at,at+3);
    const diff=Math.abs(r-or)+Math.abs(g-og)+Math.abs(b-ob);
    if(diff<34)continue;
    let color;
    if(r>95&&r>g*1.75&&g>b*1.25)color=[145,56,28];
    else if(r>125&&g>65&&r>g*1.35&&g>b*1.35)color=[180,117,43];
    else if(r<78&&g<59&&b<45)color=[42,30,21];
    else continue;
    if((x*17+y*29)%13<3)continue;
    for(let c=0;c<3;c++)final[at+c]=Math.round(old.pixels[at+c]*.25+color[c]*.75);
  }
  let changed=0,outside=0;
  for(let i=0;i<old.width*old.height;i++)if(!final.subarray(i*3,i*3+3).equals(old.pixels.subarray(i*3,i*3+3))){
    changed++;const x=i%old.width,y=Math.floor(i/old.width);
    if(x<rect[0]||x>=rect[0]+rect[2]||y<rect[1]||y>=rect[1]+rect[3])outside++;
  }
  assert(changed>0);assert.equal(outside,0);
  const png=writePNG(old.width,old.height,final);assert(readPNG(png).pixels.equals(final));
  const rgba=Buffer.alloc(512*512*4);
  for(let y=0;y<512;y++)for(let x=0;x<512;x++){
    const xa=Math.floor(x*old.width/512),xb=Math.floor((x+1)*old.width/512),ya=Math.floor(y*old.height/512),yb=Math.floor((y+1)*old.height/512);
    for(let c=0;c<3;c++){let sum=0;for(let sy=ya;sy<yb;sy++)for(let sx=xa;sx<xb;sx++)sum+=final[(sy*old.width+sx)*3+c];rgba[(y*512+x)*4+c]=Math.round(sum/((xb-xa)*(yb-ya)));}
    rgba[(y*512+x)*4+3]=255;
  }
  const jpeg=encodeJPEG({data:rgba,width:512,height:512},77).data;assert(jpeg.length<100000);
  fs.writeFileSync(outputPath,png);
  try{fs.unlinkSync('artifacts/line-3/wall.png');}catch(e){if(e.code!=='ENOENT')throw e;}
  fs.symlinkSync('wall-v13.png','artifacts/line-3/wall.png');
  fs.writeFileSync('dist/line-3/33.jpg',jpeg);
  const sha=hash(png),report={wall:outputPath,format:'PNG',dimensions:[1254,1254],mode:'RGB',sha256:sha,
    ancestor_sha256:hash(oldBytes),generated_draft_sha256:hash(draftBytes),new_mark_rectangle:rect,
    changed_pixels:changed,changed_pixels_outside_rectangle:outside,
    thumbnail:{path:'dist/line-3/33.jpg',format:'JPEG',dimensions:[512,512],bytes:jpeg.length},
    visual_review:'pending',unmet_visual_requirements:['An inherited, partly occluded hand remains unchanged; its complete five-digit count cannot be confirmed.']};
  fs.writeFileSync('line-3/IMAGE-33.json',JSON.stringify(report,null,2)+'\n');
  const record={name:'The Missing Word Path',image:'https://api.imd.fun/artifacts/'+sha,attributes:[
    ['Cave','Crystal'],['Wall','Line 3'],['Number',33],['Left behind','Query Diagnose'],
    ['Meaning','Three ochre stones trace a fork around an empty place, showing how to loosen a search without mistaking a lead for an answer.'],
    ['One thing','Offline document search with exact source line citations']].map(([trait_type,value])=>({trait_type,value}))};
  fs.writeFileSync('dist/line-3/33.json',JSON.stringify(record,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}
let input='';
if(process.stdin.isTTY)process.stdin.setRawMode(true);
process.stdin.on('data',chunk=>{input+=chunk.toString('utf8');const end=input.indexOf('\x04');if(end>=0){finish(Buffer.from(input.slice(0,end),'base64'));process.exit(0);}});
