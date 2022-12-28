$(document).ready(function(){
    /**
     * Setup callbacks for playing and pausing
     */
     function get_date_hour(timestep) {
        // extract hour and offset from timestep
        var hour = (timestep+1)%24;
        var offset = (timestep-hour+1)/24;

        // extract year and day offset from offset
        var day_2016_offset = 366-214
        offset = offset-day_2016_offset;
        var day_of_year = (offset % 365);
        var year_offset = (offset-day_of_year)/365;
        if (day_of_year < 0) {
            day_of_year = 365 + day_of_year ;
            year_offset = year_offset - 1;
        }
        day_of_year -= 1;

        // build date from year and day offset
        var year = year_offset + 2017;
        var date = new Date(year,0);
        date.setDate(date.getDate() + day_of_year);
        return {
            'date':date.toISOString().substring(0,10), 'hour':hour
        }
    }

    function date_change_callback(tapestry){
        // get the date and hour from the current timestep
        date_hour = get_date_hour(tapestry.current_timestep);

        // set date and hour selects
        if (tapestry.element.id =='input_var'){
            document.getElementById("hour-input").value = date_hour.hour;
            document.getElementById("date-input").value = date_hour.date;
        }
        else if(tapestry.element.id =='output_var'){
            document.getElementById("hour-output").value = date_hour.hour;
            document.getElementById("date-output").value = date_hour.date;
        }

    }

    /**
     * Setup tapestry
     */
    $(".hyperimage").tapestry({
        // host: "http://127.0.0.1:8000",
        host: "http://kavir.eecs.utk.edu:8000",
        n_tiles: 4,
        width: 1024,
        height: 1024,
        animation_interval: 1000,
        callbacks: [date_change_callback]
    });

    function get_hyperimg(i){
        return $(".hyperimage").eq(i).data("tapestry");
    }

    /**
     * Setup call back for basin selection
     */
    function fillOptions(el, optionsList) {
        while (el.options.length) el.remove(0);
        optionsList.forEach(optionText => {
            const option = document.createElement('option');
            option.text = optionText;
            // option.text = optionText.replaceAll('_', ' ');
            option.value = optionText;
            el.appendChild(option);
        });
    }
    function set_basin(i){
        var hyperimg = get_hyperimg(i);
        console.log(hyperimg)
        if (i==0){
            var suffix = "input"
        }
        else{
            var suffix = "output"
        }
        ele = document.getElementById("basin-"+suffix);
        console.log(ele)
        var basin = ele.value+"_"+suffix;
        console.log(basin)
        console.log(hyperimg.settings.variable_list)
        
        // switch the config to the selected basin ( also sets up the variable list )
        hyperimg.do_action("switch_config(" + basin + ")")

        // reset input_var variables
        fillOptions(document.getElementById("varname-"+suffix), hyperimg.settings.variable_list);
        console.log('rendering after variable set')
        hyperimg.render(0);
    }

    $(".basin-input").on("input", function(){
        set_basin(0);
    });
    $(".basin-output").on("input", function(){
        set_basin(1);
    });

    /**
     * Setup call back for variable selection
     */
    
    function set_variable(val, i){
        var hyperimg = get_hyperimg(i);
        hyperimg.settings.variable=val;
        console.log('rendering after variable set')
        hyperimg.render(0);
    }
    $(".varname-input").on("input",  function(){ set_variable($(this).val(), 0) });
    $(".varname-output").on("input", function(){ set_variable($(this).val(), 1) });

    /**
     * Setup call back for date selection
     */
    function get_timestep(date, hour){
        // parse date and hour string
        date = date.split("-");
        var year = parseInt(date[0]);
        var month = parseInt(date[1]);
        var day = parseInt(date[2]);
        hour = parseInt(hour);

        // get day of year
        date = new Date(year, month-1, day);
        var start = new Date(year, 0, 0);
        var day_of_year = (date-start) +  ((start.getTimezoneOffset() - date.getTimezoneOffset()) * 60 * 1000);
        var oneDay =  1000 * 60 * 60 * 24;
        day_of_year = Math.floor(day_of_year / oneDay);
    
        // calculate offset from start of dataset
        var year_offset = year - 2017
        var day_2016_offset = 366-214
        offset = 365 * year_offset + day_2016_offset + day_of_year 
        
        // calc time index
        var time_index = offset * 24 + (hour-1)
        return time_index;
    }


    function set_timestep(i){
        if (i==0){
            var hour = document.getElementById("hour-input").value;
            var date = document.getElementById("date-input").value;
        }else if(i==1){
            var hour = document.getElementById("hour-output").value;
            var date = document.getElementById("date-output").value;
        }
        var hyperimg = get_hyperimg(i);
        var timestep = get_timestep(date, hour);
        if (!isNaN(timestep)){
            hyperimg.current_timestep = timestep;
            hyperimg.render(0);
        }
    }
    $(".date-input").on("input",  function(){ set_timestep(0); });
    $(".date-output").on("input", function(){ set_timestep(1); });
    $(".hour-input").on("input",  function(){ set_timestep(0); });
    $(".hour-output").on("input", function(){ set_timestep(1); });

    set_basin(0);
    set_basin(1);
});
