$(document).ready(function(){
    // function var_callback(obj){
    //     hyperimg = obj;
    //     console.log(obj.settings);
    //     console.log('var_callback here')
    //     i = 0;
    //     if (i==0){
    //         var suffix = "input"
    //     }
    //     else{
    //         var suffix = "output"
    //     }
    //     ele = document.getElementById("basin-"+suffix);
    //     console.log(ele)
    //     var basin = ele.value+"_"+suffix;
    //     console.log(basin)
    //     console.log(hyperimg.settings.variable_list)
    //     // switch the config to the selected basin ( also sets up the variable list )
    //     hyperimg.do_action("switch_config(" + basin + ")")

    //     // reset input_var variables
    //     fillOptions(document.getElementById("varname-"+suffix), hyperimg.settings.variable_list)
    // }

    /**
     * Setup tapestry
     */
    $(".hyperimage").tapestry({
        host: "http://127.0.0.1:8000",
        // host: "http://accona.eecs.utk.edu:8000",
        n_tiles: 4,
        width: 1024,
        height: 1024,
        animation_interval: 500,
        // callbacks: [var_callback]
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
        console.log($(".hyperimage").eq(0).data("tapestry"));//.eq(i).data("tapestry");)
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
        fillOptions(document.getElementById("varname-"+suffix), hyperimg.settings.variable_list)
    }

    $(".basin-input").on("input", function(){
        set_basin(0);
    });
    // $(".basin-output").on("input", function(){
    //     set_basin(1);
    // });

    /**
     * Setup call back for variable selection
     */
    
    function set_variable(val, i){
        var hyperimg = get_hyperimg(i);
        // console.log($(this))
        // console.log(val)
        hyperimg.settings.variable=val;
        hyperimg.render(0);
    }
    $(".varname-input").on("input",  function(){ set_variable($(this).val(), 0) });
    // $(".varname-output").on("input", function(){ set_variable($(this).val(), 1) });

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
        var hour = document.getElementById("hour-input").value;
        var date = document.getElementById("date-input").value;
        var hyperimg = get_hyperimg(i);
        var timestep = get_timestep(date, hour);
        if (!isNaN(timestep)){
            hyperimg.current_timestep = timestep;
            hyperimg.render(0);
        }
    }
    $(".date-input").on("input",  function(){ set_timestep(0); });
    // $(".date-output").on("input", function(){ set_timestep(1); });
    $(".hour-input").on("input",  function(){ set_timestep(0); });
    // $(".hour-output").on("input", function(){ set_timestep(1); });

    set_basin(0);
    // set_basin(1);
});
