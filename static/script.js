$(function(){
    $(".hide").hide();
    $("#show_prediction").on("click", function(event){
        $("#prediction").toggle();
    })
})