/* Minecraft Java seed input uses signed long integers or Java UTF-16 String.hashCode. */
export function parseWorldSeed(input){const s=String(input).trim();if(!s)throw Error('Enter a numeric or text seed.');if(/^[+-]?\d+$/.test(s)){const n=BigInt(s);if(n<-(1n<<63n)||n>(1n<<63n)-1n)throw Error('Numeric seeds must fit a signed 64-bit integer.');return n.toString()}let hash=0;for(let i=0;i<s.length;i++)hash=(Math.imul(hash,31)+s.charCodeAt(i))|0;return String(hash)}
export const MAP_SCALES=[1,4,16,64,256];
export function mapBounds(x,z,scale,size=192){return {x:Math.floor(x/scale)-size/2,z:Math.floor(z/scale)-size/2,width:size,height:size,scale}}
