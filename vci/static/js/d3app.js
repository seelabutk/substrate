import * as helper from './helper.js';
import * as vcid3 from './d3.vci.js';


var GUIcontrols = new function () {
	this.mode = "NCEP";
	this.partitions = 8;
	this.pressure = 5;
	this.timeslice = 0;
	this.numSteps = 50;
	this.seedsShownAtOnce = 125;
	this.monkeyTest = false;
};





class D3_APP extends HTMLElement {

	
	/*
			SETUP FUNCTIONS
	*/
	constructor() {
		super();

		this.service = new vcid3.D3_VCI(["http://" + location.host]);

		this.width = null;
		this.height = null;
		this.bbox = null;
		this.world = null;
		this.transform = null;

		this.mousedown = false;
		this.timeout = true;

		this.root = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
		this.root.setAttribute('id', 'd3');

		this.svg = d3.select(this.root)
			.style('float', 'left')
			.style('box-sizing', 'border-box')

		this.svg.node().addEventListener('contextmenu', function(ev) {
			ev.preventDefault();
			return false;
		}, false);

		window.addEventListener('resize', this.onWindowResize.bind(this), false);
		this.onWindowResize();
		
		this.setupHandling();
		this.setupd3();
		
		this.attachShadow({ mode: 'open' });
		this.shadowRoot.append(this.root);

		this.polygons = [];
	}

	testScale() {
		const points = [
			{ x: -90, y: 0 },
			{ x: -90, y: 360 },
			{ x: 90, y: 0 },
			{ x: 90, y: 360 },
		];
		this.render(points);
	}

	testcurve(){
		const curvepoint = [
			{x: -43.34765625, y: 255.4840087890625} //server response in tn
		];
		console.log(this.streamlineToStates(curvepoint));
	}

	onWindowResize() {

		const [width, height] = helper.getWindowSize();

		this.width = Math.floor(width / 2);
		this.height = Math.floor(height);//Math.floor(height/2) - 10;
		this.svg.style('width', `${this.width}px`)
			.style('height', `${this.height}px`);

		this.svg.attr('width', `${this.width}px`)
			.attr('height', `${this.height}px`)
	}

	loadcsv() {
		return fetch("/static/resources/power.csv")
			.then(r => r.text())
			.then(r => r.split('\n').map(t => t.split(',').slice(2, 4).map(n => parseFloat(n))));
	}

	setupd3() {

		this.vertices = [];
		const { svg, width, height } = this;

		const min = Math.max(width, height);

		this.projection = d3.geoMercator()
			.scale(min/Math.PI)
			.translate([width / 2, height / 2]);

		this.path = d3.geoPath()
			.projection(this.projection);

		const zoom = d3.zoom()
			.filter(function () {
				switch (d3.event.type) {
					case "mousedown": return d3.event.button === 2 || d3.event.button === 1;
					case "wheel": return d3.event.button === 0;
					default: return false;
				}
			})
			.scaleExtent([0.5, 8])
			.on('zoom', zoomed)
		svg.call(zoom);
		
		const self = this;
		svg
			.on('mousedown', function(){self.mousedown = true;})
			.on('mouseup', function(){self.mousedown = false;})
			.on('mouseleave', function(){self.mousedown = false;})
			.on('mousemove', self.drag.bind(self));

		const g = svg.append('g');
		const m = g
			.append('g')
			.attr('class', 'map');

		
		Promise.all([
			/*d3.json('//unpkg.com/world-atlas@1/world/110m.json'),
			d3.json('//unpkg.com/us-atlas@1/us/10m.json')*/
			d3.json('https://gist.githubusercontent.com/MaciejKus/61e9ff1591355b00c1c1caf31e76a668/raw/4a5d012dc2df1aae1c36e2fdd414c21824329452/combined2.json'),
		]).then(([world]) => {
			this.bbox = [-180, -85.06, 180, 85.06];
			this.world = world;

			//world border
			m.append('path')
				.datum({ 'type': 'Sphere' })
				.attr('class', 'Sphere')
				.attr('d', this.path)
				.style('stroke', '#f00')
				.style('stroke-width', 1);

			//countries
			m.append('g')
				.attr('class', 'boundary')
				.selectAll('boundary')
				.data(topojson.feature(world, world.objects.countries).features)
				.enter()
				.append('path')
				.attr('d', this.path)
				.style('stroke', '#fff')
				.style('stroke-width', 1);

			//states
			m.append('g')
				.attr('class', 'states')
				.selectAll('states')
				.data(topojson.feature(world, world.objects.states).features)
				.enter()
				.append('path')
				.attr('d', this.path)
				.style('stroke', '#fff')
				.style('stroke-width', 0.5)
				.style('fill', '#fff')
				.style('fill-opacity', 0.0)



			/* //countries
			m.append('path')
				.datum(topojson.merge(world, world.objects.countries.geometries))
				.attr('class', 'land')
				.attr('d', this.path)
				.style('stroke', '#fff')
				.style('stroke-width', 1);

			//borders
			m.append('path')
				.datum(topojson.mesh(world, world.objects.countries, (a, b) => a !== b))
				.attr('class', 'boundary')
				.attr('d', this.path)
				.style('stroke', '#fff')
				.style('stroke-width', 1); */


			//us-states
			//todo: how the heck do I merge two maps? it don't work, nothing online, fudge.
			//todo: d3.pointer selection.on customevent UIEvent? new UIEvent(...)
			/* m.append('path')
				.datum(topojson.merge(us, us.objects.states.geometries))
				.attr('class', 'state')
				.attr('d', this.path)
				.style('stroke', '#fff')
				.style('stroke-wdith', 1); */
				
				

			//this.testScale();
			//this.testcurve();
			this.getStreamlines([]); //initialize ws
			setTimeout(() => this.loadcsv().then(d => this.renderPP(d)), 1000);
		});

		this.hulls = g
			.append('g')
			.attr('class', 'hull');

		this.powerplants = g
			.append('g')
			.attr('class', 'powerplants')

		function zoomed() {
			g.attr('transform', d3.event.transform);
		}
	}

	setupHandling() {

		let gui = new dat.GUI();
		var appMode = gui.add(GUIcontrols, 'mode', ["Test1", "NCEP"]).name("Data");
		//gui.add(GUIcontrols, 'partitions', 1, 20).step(1);
		gui.add(GUIcontrols, 'pressure', 0, 10).step(1).name("Seed Pressure");
		gui.add(GUIcontrols, 'timeslice', 0, 500).step(1).name("Seed Time");
		gui.add(GUIcontrols, 'numSteps', 2, 1000).step(1).name("nSteps/Trace");
		gui.add(GUIcontrols, 'seedsShownAtOnce', 0, 2000).name("MaxTraceShown");

		switch(GUIcontrols.mode){
			default:
			case "Test1":
				this.jobLoc = "service/job/streamline";
				this.transform = helper.transformFromStreamline;
				break;
			case "NCEP":
				this.jobLoc = "service/job/ncar";
				this.transform = helper.transformFromNcar;
				break;
		}
	}

	//https://stackoverflow.com/questions/30755696/get-svg-object-s-at-given-coordinates
	/* elementsAt = function(x, y){

		//todo: transform to transformed svg space to svg space to window space in this function or not?
		//todo: perform this elementAt on an invisble fully-sized (everything visible) map so things rendered off screen on the real map still works correctly?

		var elements = [], current = this.shadowRoot.elementFromPoint(x, y);
		while(current && current.nearestViewportElement){
			elements.push(current);
			// hide the element and look again
			current.style.display = "none";
			current = document.elementFromPoint(x, y);
		}
		// restore the display
		elements.forEach(function(elm){
		   elm.style.display = ''; 
		});
		return elements;
	} */

	drag(e) {
		if(this.mousedown && this.timeout){
			this.timeout = false;
			let self = this;
			setTimeout(function(){self.timeout = true;}, 50);

			let [x, y] = this.projection.invert(d3.zoomTransform(this.svg.node()).invert(d3.mouse(this.svg.node()))); //from screen space to projection space

			const p = GUIcontrols.pressure;
			const t = GUIcontrols.timeslice;
			this.getStreamlines([x, y, p, t], (d)=>this.render(this.initStreamline));
		}
	}


	/*
		REQUEST FUNCTIONS
	*/

	async getStreamlines(seeds, callback, force = false) {
		const request = { partitions: GUIcontrols.partitions, hostid: 0, seeds, steps: GUIcontrols.numSteps };
		await this.service.postDataWS({
			url: "http://accona.eecs.utk.edu:8840",
			loc: this.jobLoc,
			data: request,
			callback: callback ? callback.bind(this) : undefined,
			multiHost: true
		}, undefined, { bbox: this.bbox }).catch(err => console.log(err));
	}

	streamlinesToStates(curves){
		let allstates = [];
		curves.forEach(c => {
			let states = this.streamlineToStates(c);
			states.forEach((s) => {
				if(allstates.findIndex((d)=>{ return d.properties.name === s.properties.name}) === -1){
					allstates.push(s);
				}
			});
		});
		return allstates;
	}
	streamlineToStates(curvepoint){
		let [lonmin, latmin, lonmax, latmax] = this.bbox;
		let states = [];

		for(let i = 0; i < curvepoint.length; ++i){
			let cp = [helper.interpolate(-90, 90 , lonmin, lonmax, curvepoint[i].x), helper.interpolate(0,   360, latmin, latmax, curvepoint[i].y)]; //from server geo space to svg geo space
			let features = topojson.feature(this.world, this.world.objects.states).features;
			for(let j = 0; j < features.length; j++){
				if(d3.geoContains(features[j], cp)){
					if(states.findIndex((d)=>{ return d.properties.name === features[j].properties.name}) === -1){
						states.push(features[j]);
					}
					break;
				}
			};
		}
		return states;
	}

	initStreamline(response) {
		const {transform} = this;
		const {points} = response;
		let curves = [];

		for (let i = 0; i < points.length; ++i) {
			let curvepoints = [];
			curvepoints.push(new THREE.Vector3(0, 0, 0));
			const numVerts = points[i].length;

			let totalLength = 0;

			const stepsize = this.jobLoc === "service/job/ncar" ? 4 : 3;
			for (let j = 0; j < numVerts; j += stepsize) {

				let [lat, lon, prs, sec] = transform(points[i], j);
				let newVert = new THREE.Vector3(lat, lon, prs);
				let length = curvepoints[curvepoints.length - 1].distanceTo(newVert);

				if (length > .001) {
					curvepoints.push(newVert);
					totalLength += length;
				}
			}

			curvepoints.shift();
			if ((curvepoints.length <= 1) || (totalLength < 0.1)) continue;

			curves.push(curvepoints);
		}

		return curves;
	}




	/* 
			RENDERING FUNCTIONS
	*/

	renderPP(pplocs) {
		const locs = [];
		for (let i = 0; i < pplocs.length; ++i) {
			let [y, x] = pplocs[i];
			const coord = this.projection([x, y]);
			locs.push(coord);

			let p = GUIcontrols.pressure;
			let t = GUIcontrols.timeslice;
			this.getStreamlines([x, y, p, t], (d)=>{
					let curves = this.initStreamline(d);
					this.render(curves); 
					this.streamlinesToStates(curves);
			});
		}
		this.powerplants
			.selectAll('circle')
			.data(locs)
			.enter()
			.append('circle')
			.merge(this.hulls.selectAll('circle'))
			.attr('cx', loc => loc[0])
			.attr('cy', loc => loc[1])
			.attr('r', 0.75)
			.style('fill', 'red')
			.exit()
			.remove();
	}
	
	render(curves){
		curves.forEach(d => this.renderCurve(d));
	}

	renderCurve(points) {
		let [lonmin, latmin, lonmax, latmax] = this.bbox;

		let streamtubeCoords = [];
		for (let i = 0; i < points.length; i++) {
			const point = points[i];
			const interpolatedcoord = [helper.interpolate(-90, 90, lonmin, lonmax, point.x), helper.interpolate(0, 360, latmin, latmax, point.y)]
			const coord = this.projection(interpolatedcoord);
			streamtubeCoords.push(coord);
		}

		this.polygons.push(streamtubeCoords)
		while(this.polygons.length > GUIcontrols.seedsShownAtOnce){
			this.polygons.shift();	
		}

		let p = this.hulls
			.selectAll('polygon')
			.data(this.polygons);


		p.enter()
			.append('polygon')
			.merge(p)
			.attr('points', polygon => d3.polygonHull(polygon))
			.attr('opacity', 0.3)
			.attr('stroke-width', 0.1)
			.attr('stroke-linejoin', 'round')
			.attr('fill', 'red')
			.attr('stroke', 'blue')
			.exit()
			.remove();
	}
}

customElements.define('d3-viewer', D3_APP);
