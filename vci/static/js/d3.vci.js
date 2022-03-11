import * as helper from './helper.js';




export class D3_VCI{
    constructor(urls) {
        this.service = new VCI(urls);
    }
    
    async postDataWS(parameters, callbackparams, params){
        let [lonmin, latmin, lonmax, latmax] = params.bbox;

        for(let i = 0; i < parameters.data.seeds.length; i+=4){
            parameters.data.seeds[i+0] = helper.interpolate(lonmin, lonmax, -90,  90, parameters.data.seeds[i+0]);
            parameters.data.seeds[i+1] = helper.interpolate(latmin, latmax,   0, 360, parameters.data.seeds[i+1]);
        }

        //console.log(parameters.data.seeds);

		await this.service.postDataWS(parameters, callbackparams);
    }
};

