$(document).ready(function(){
	$(".hyperimage").tapestry({
		n_tiles: 4,
		width: 512,
		height: 512,
		lo_res: 128,
	});

	// Listen to slider events and change the 
	// isosurface threshold accordingly
	$(".threshold-slider").on("input", function(){
		$(".hyperimage").eq(0).data("tapestry").settings.isovalues=[parseInt($(this).val())];
		$(".hyperimage").eq(0).data("tapestry").render(0);
	});
});
