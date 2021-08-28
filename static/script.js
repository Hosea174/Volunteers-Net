function requested(id) {
    let request = document.getElementById(id)
    request.innerHTML = 'Requested'
    request.style.background = 'rgb(59, 185, 0)'
    request.style.color = '#fff'
    var server_data = [
        { "applicant_id": id },
    ];

    $.ajax({
        type: "POST",
        url: "/request_volunteer",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function (result) {
            if (result.processed === "false") {
                btn_id = '#msg-' + id
                let msg = "You had already sent a request to this volunteer"
                $(btn_id).html(msg);
            }
        }
    });
}
function respond(recruiter, response_id) {
    let recruiter_cls = '.' + recruiter
    let btns = document.querySelectorAll(recruiter_cls)
    for (var i = 0; i < btns.length; ++i) {
        btns[i].style.display = 'none';
    }
    var server_data = [
        { "recruiter": recruiter },
        { "response_id": response_id }
    ];


    $.ajax({
        type: "POST",
        url: "/offers",
        data: JSON.stringify(server_data),
        contentType: "application/json",
        dataType: 'json',
        success: function (result) {
            status_id = '#' + recruiter
            $(status_id).html(result.status);

        }
    });
}

function userMode(id)
{
    let company_name = document.getElementById("company")

    if (id == 'volunteer')
    {
        company_name.style.display = 'none';
    }
    else 
    {
        company_name.style.display = 'flex';
    }
}