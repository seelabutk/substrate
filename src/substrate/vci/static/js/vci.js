hostName = '//' + window.location.host; //accona.eecs.utk.edu:8840';

class VCI{
	hosts = [];
	maxRequests = 6;

	constructor(hosts){
		if(hosts === undefined)	return
		this.setHosts(hosts);
	}	

	setHosts(hostList){
		for(let host of hostList){
			this.hosts[host] = {numOutgoingRequests: 0, controller: null, load: 0, failRate: []};
		}
	}


	/***************** 
	* parameters:
	*	loc			: location to post request to, appended to host
	*	data		: data to be sent in request
	*	callback	: callback function to be called to process returned data
	*	maxAttempts	: maximum number attempts to try reaching the server before giving up
	* 	timeout		: maximum amount of time to wait for a response per request before cancelling request
	*	maxTimeout	: maximum amount of time to wait for a response (with resends) before giving up 
	*****************/ 

	async postData(parameters, callbackParams, force=false){
		let fulfilled = false;
		let currtime;

		let {url, loc, data, callback, multiHost, maxAttempts, timeout, maxTimeout} = parameters;
		multiHost = multiHost || false;
		maxAttempts = maxAttempts || 0;
		timeout = timeout || 4.0;
		maxTimeout = maxTimeout || 5.0;
		url = url || hostName;

		let requestStartTime = Date.now();
		let sortedHosts = this.hosts.sort((a,b)=>{ return a.load > b.load; });

		for(let hostName in sortedHosts){
			let host = sortedHosts[hostName];
			if(host.numOutgoingRequests < this.maxRequests || force){
				++host.numOutgoingRequests;
				host.controller = new AbortController();
				setTimeout(() => host.controller.abort(), timeout*1000); 
				const signal = host.controller.signal;
				const response = await fetch(`${url}/${loc}`, {
					method: 'POST',
					body: JSON.stringify(data),
					signal
				}).then(async function success(response){
					if(fulfilled){//request has already been fulfilled
						const millis = Date.now() - currtime;
						console.log(`late msg recieved ${Math.floor(millis/1000)} seconds after first`);
						return;
					}
					let avgLoad = 0;
					let header = JSON.parse(response.headers.get('X-VCI-Load'));
					if(header != null){				
						let hostsLoad = header.hosts;
						for(let hostLoad in hostsLoad){
							hostsLoad[hostLoad] = JSON.parse(hostsLoad[hostLoad]);
							avgLoad += hostsLoad[hostLoad].cpu;
						}
						avgLoad /= hostsLoad.length;
						host.load = avgLoad;
					}
					--host.numOutgoingRequests;
					try{
						if(!fulfilled){
							if(host.failRate.length > 16)	host.failRate.shift();
							host.failRate.push(1);
							for await (const data of ndjson(ndlines(response))){
								callback(data, callbackParams);
							}
						}
						fulfilled = true;
						currtime = Date.now();
					}catch(err){}
					
					if(fulfilled){
						for(let otherhost in this.hosts){
							if(otherhost !== hostName){
								this.hosts[otherhost].controller.abort();
							}
						}
					}
				}).catch((err)=>{
					--host.numOutgoingRequests
					if(host.failRate.length > 16)	host.failRate.shift();
					host.failRate.push(0);
					let currTime = requestStartTime - Date.now();
					if((maxAttempts > 0) && (currTime < maxTimeout)){
						postData({loc, data, callback, multiHost, maxAttempts: maxAttempts - 1, timeout, maxTimeout: currTime});
					}
				});
			}
			if(!multiHost)	return;
		}
	}


	/***************** 
	* parameters:
	*	loc			: location to post request to, appended to host
	*	data		: data to be sent in request
	*	callback	: callback function to be called to process returned data
	*	maxAttempts	: maximum number attempts to try reaching the server before giving up
	* 	timeout		: maximum amount of time to wait for a response per request before cancelling request
	*	maxTimeout	: maximum amount of time to wait for a response (with resends) before giving up 
	*****************/ 

	async postDataWS(parameters, callbackParams){
		let fulfilled = false;
		let currtime;
		
		function onmessage(event) {
			const { id, result } = JSON.parse(event.data);
			const { callback, callbackParams } = this.ws._callbacks[id];
			if(callback)	callback(result, callbackParams);
		}

		if (!this.ws) {
			const ws = new WebSocket('ws://' + window.location.hostname + ':' + (+window.location.port + 1));
			ws.onmessage = onmessage.bind(this);
			ws.onerror = () => console.log('ws.onerror');
			ws.onclose = () => console.log('ws.onclose');
			ws._callbacks = {};
			ws._id = 0;
			this.ws = ws;
		}
		const ws = this.ws;
		if (ws.readyState !== WebSocket.OPEN) return; // lmao


		let {url, loc, data, callback, multiHost, maxAttempts, timeout, maxTimeout} = parameters;
		multiHost = multiHost || false;
		maxAttempts = maxAttempts || 0;
		timeout = timeout || 4.0;
		maxTimeout = maxTimeout || 5.0;
		url = url || hostName;

		let requestStartTime = Date.now();
		let sortedHosts = this.hosts.sort((a,b)=>{ return a.load > b.load; });

		for(let hostName in sortedHosts){
			// lmao //setTimeout(() => host.controller.abort(), timeout*1000); 
			//const signal = host.controller.signal;
			const id = ws._id++;
			ws._callbacks[id] = { callback, callbackParams };
			ws.send(JSON.stringify({ 'id': id, 'job': data }));
		}
	}

	
}



async function *ndjson(lines) {
	for await (const line of lines) {
		yield JSON.parse(line);
	}
}
async function *ndlines(response) {
	const reader = response.body.getReader();
	const decoder = new TextDecoder('utf-8');
	let data = '';
	
	while (true) {
		const { done, value } = await reader.read();
		if (done) return;
		
		data += decoder.decode(value);
		while (true) {
			const index = data.indexOf('\n');
			if (index === -1) break;
			const line = data.substring(0, index);
			yield line;
			data = data.substring(index + 1);
		}
	}
}
