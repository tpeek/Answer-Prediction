$(function(){
    var answer = null;
    $("body").on("click", "#show_prediction", function(event){
        $("#prediction").toggle();
    });

    /*---- SITE WIDE AJAX ----*/
    $(".navlink").on("click", function(event){
        event.preventDefault();
        var ref = $(this).attr("href")

        $.ajax({
            method : "GET",
            url : ref,
        }).done(function(response){
            $("main").replaceWith($($.parseHTML(response)).filter("main"))
            /*alert($("main").html())*/
        }).fail(function(){
            alert("Something went wrong")
        });
    });

    /*---- QUESTION PAGE AJAX ----*/
    $("input:radio[name=answer]").click(function() {
        answer = $(this).val();
    });

    $("body").on("submit", '.question_form', function(event){
        event.preventDefault();
        $("#submit").attr('disabled', true);
        var question_id = $("#qu").val();

        $.ajax({
            method : "POST",
            url : "/question",
            data : {"answer": answer,
                    "question_id": question_id
                }
        }).done(function(response){
            answer = null;
            $("#q_text").html(response.text)
            $("#qu").val(response.qid)
            $("#prediction").html(response.prediction)
            $("input:radio[name='answer']").each(function(){
                $(this).prop('checked', false)
            });
            $("#submit").attr('disabled', false);
        }).fail(function(){
            answer = null;
            alert("Something went wrong")
        });
    });

    /*---- LOGIN PAGE AJAX ----*/
    $("body").on("submit", "#login_form", function(event){
        event.preventDefault();
        var username = $("#username").val();
        var password = $("#password").val();

        $.ajax({
            method : "POST",
            url : "/login",
            data : {
                "username" : username,
                "password" : password
            }
        }).done(function(response){
            $("header").replaceWith($($.parseHTML(response)).filter("header"));
            $("main").replaceWith($($.parseHTML(response)).filter("main"));
            $("#username").val(username);
        }).fail(function(response){
            alert("Something went wrong")
        })

    });




});