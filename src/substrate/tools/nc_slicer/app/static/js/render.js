function render(initial){
    const button = document.querySelector('.render-btn');
    const options = {};

    let perms = {
        ncpath:document.getElementById("basin").value, 
        variable:document.getElementById("varname").value,
        date:document.getElementById("date").value,
        hour:document.getElementById("hour").value
    }
    if (!initial) {
        options.body = JSON.stringify(perms);
        options.headers = {'Content-Type': 'application/json'};
        options.method = 'POST';
    }
    
    fetch('/render/', options).then((response) => response.blob()).then((blob) => {
		const image_url = URL.createObjectURL(blob);

		const image = document.querySelector('.render');
		image.src = image_url;
	});
  
}
