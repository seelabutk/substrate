((seedName)=>{
    function xmur3(str) {
        for(var i = 0, h = 1779033703 ^ str.length; i < str.length; i++)
            h = Math.imul(h ^ str.charCodeAt(i), 3432918353),
            h = h << 13 | h >>> 19;
        return function() {
            h = Math.imul(h ^ h >>> 16, 2246822507);
            h = Math.imul(h ^ h >>> 13, 3266489909);
            return (h ^= h >>> 16) >>> 0;
        }
    }
    function sfc32(a, b, c, d) {
        return function() {
            a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0; 
            var t = (a + b) | 0;
            a = b ^ b >>> 9;
            b = c + (c << 3) | 0;
            c = (c << 21 | c >>> 11);
            d = d + 1 | 0;
            t = t + d | 0;
            c = c + t | 0;
            return (t >>> 0) / 4294967296;
        }
    }
    const seed = xmur3(seedName);
    const rand = sfc32(seed(), seed(), seed(), seed());
    const random = () => rand() / (1 << 32);
    Math.random = random;
})("apples");

export function wrap(x, lo, hi) {
	if (x >= hi) x = lo + (x - hi) % (hi - lo);
	else if (x <= lo) x = lo + (x - lo) % (hi - lo);
	return x;
}

export function wrapLat(lat) {
	return wrap(lat, -90, 90);
}

export function wrapLng(lng) {
	return wrap(lng, 0, 360);
}

//not currently used
export function seedsAroundPoint(x, y, prs, sec=0, r=1, count=3) {
	const requests = [];
	
	for (let i=0; i<count; ++i){
		const seeds = [];
		const angle = i*(2 * Math.PI)/count;
		const radius = (i/count) * r;
		seeds.push(x + radius * Math.cos(angle));
		seeds.push(y + radius * Math.sin(angle));
		seeds.push(prs);
		seeds.push(sec);
		requests.push(seeds);
	}
	
	return requests;
}

export function seedsOnSphere(u, v, h, count){
	const r = 0.005;

	const requests = [];

	for (let i=0; i<count; ++i){
		const seeds = [];
		const off_u = (Math.random()-0.5)*(r*2);
		const off_v = (Math.random()-0.5)*(r*2);
		const off_h = (Math.random()-0.5)*(.001*2);

		const lng = (u + off_u) * 360;
		const lat = (1.0 - (v + off_v)) * 180 - 90;
		const prs = h + off_h;
		const sec = 0.0;

		seeds.push(wrapLat(lat));
		seeds.push(wrapLng(lng));
		seeds.push(prs);
		seeds.push(sec);
		requests.push(seeds);
	}
	return requests;
}

//not currently used
export function seedsFromCanvas(ctx, nseeds) {
	const { canvas } = ctx;
	const width = +canvas.width;
	const height = +canvas.height;
	const { data }  = ctx.getImageData(0, 0, width, height);
	let seeds = [];
	
	for (let i=0; i<nseeds; ++i) {
		let u, v, alpha;	//this is terrible
		do {
			u = Math.random();
			v = Math.random();
			const x = (u * width)|0;
			const y = (v * height)|0;
			const index = 4 * x + 4 * width * y;
			alpha = data[index+3];
		} while (alpha < 128);
		const lon = u * 360;
		const lat = (1.0 - v) * 180 - 90;
		const prs = 500.0;
		const sec = 0.0;
		seeds.push(wrapLat(lat));
		seeds.push(wrapLng(lon));
		seeds.push(prs);
		seeds.push(sec);
	}
	return seeds;
}

export function toxyz(lat, lon, prs, sec) {
	const radius = 6.0;
 	if (lat < -90 || lat > 90){ console.warn('lat', lat, lon, prs); lat = bound(-90, 90, lat); }
	if (lon < 0 || lon > 360) { console.warn('lon', lat, lon, prs); lon = bound(0,  360, lon); }
	if (prs < 1 || prs > 1000){ console.warn('prs', lat, lon, prs); prs = bound(2, 1000, prs); }
	const cosLat = Math.cos(lat * Math.PI / 180.0);
	const sinLat = Math.sin(lat * Math.PI / 180.0);
	const cosLon = Math.cos(lon * Math.PI / 180.0);
	const sinLon = Math.sin(lon * Math.PI / 180.0);
	const C = 1.0; //1.0 / Math.sqrt(cosLat * cosLat + (1.0 - f) * (1.0 - f) * sinLat * sinLat);
	const S = 1.0; //(1.0 - f) * (1.0 - f) * C;
	const h = 0.0; //(-10.9271 * prs + 11038.0) / 10000.0;

	prs = interpolate(1, 1000, radius, radius+1, prs);
	
	const x = (prs * C + h) * cosLat * cosLon;
	const y = (prs * C + h) * cosLat * sinLon;
	const z = (prs * S + h) * sinLat;
	return [x, y, z];
}

export function bound(low, high, num){
	num = num < low ? low : num > high ? high : num;
}

export function interpolate(x0, x1, y0, y1, x){
	return (y0*(x1-x) + y1*(x-x0))/(x1-x0);
}

//not currently used
export function createElement(elementName, options){
    let element = document.createElement(elementName);
    for(const option in options)  element[option] = options[option];
    return element;
}




//transformation functions
export function transformToNcar(oseeds){
	return oseeds;
}

export function transformToStreamline(oseeds){	
	let seeds = [];
	for(let i = 0; i < oseeds.length; i+=4){
		seeds.push(interpolate(-90, 90, 0, 490, oseeds[i+0]));
		seeds.push(interpolate( 0, 360, 0, 490, oseeds[i+1]));
		seeds.push(interpolate(1, 1000, 0, 280, oseeds[i+2]));
	}
	return seeds;
}

export function transformFromNcar(streamline, j){
	return [streamline[j+0], streamline[j+1], streamline[j+2], streamline[j+3]];
}

export function transformFromStreamline(streamline, j){
	return [interpolate(0, 490, -90, 90, streamline[j+0]),
			interpolate(0, 490,  0, 360, streamline[j+1]),
			interpolate(0, 280, 1, 1000, streamline[j+2]),
			0];
}

export function getWindowSize(){
	return [
			window.innerWidth,
			window.innerHeight
		];
}