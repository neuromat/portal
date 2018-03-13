/**
 * Receives experiment status and statuses in json encoding,
 * and construct html with input radios in a form inside modal.
 */
function statuses_radio_options(experiment, statuses, logged_user) {
    // Does not display form to choose new experiment status if statuses is
    // empty - is empty because list_trustee.html bring satuses empty when
    // experiment status is approved or not approved.
    // Instead display a warning.
    if ($.isEmptyObject(statuses)) {
        return '<p class="alert">You can\'t change an experiment status' +
            ' that has already been approved or rejected.</p>';
    }
    // If experiment is under analysis and logged user is different from
    // experiment trustee does not display experiment status form. Instead
    // display a warning.
    // TODO: we are comparing with string literal. Best would be refer to
    // TODO: Experiment.UNDER_ANALYSIS.
    if (experiment.status === 'under_analysis' && logged_user !==
        experiment.trustee) {
        return `
                <p class="alert">This experiment is already under analysis by trustee ${experiment.trustee}.</p>
            `;
    }
    // Start html form
    let html = `
            <form id="id_status_choices" action="/experiments/${experiment.id}/change_status"
            method="POST">
                <input name="csrfmiddlewaretoken" value="${csrf_token}" type="hidden" >
        `;
    // Buid input radios with experiment.status === key checked
    html += `
            <div class="form-group">
            `;
    for (let key in statuses) {
        if (statuses.hasOwnProperty(key)) {
            let checked = experiment.status === key ? 'checked' : '';
            html += `
                    <input type="radio" name="status" value=${key} ${checked}>&nbsp;&nbsp;${statuses[key]} <br>
                `;
        }
    }
    html += `
            </div>
            `;
    // Finish html form
    html += `<div id="justification_area"></div>
                <br>
                <div class=modal-footer>
                    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    <input id="submit" type="submit" value="Save changes" class="btn btn-primary">
                </div>
            </form>
         `;
    return html;

}
$('#status_modal').on('show.bs.modal', function (event) {
    let link = $(event.relatedTarget);
    let experiment = {
        id: link.data('experiment_id'),
        title: link.data('experiment_title'),
        status: link.data('experiment_status'),
        trustee: link.data('experiment_trustee'),
    };
    let logged_user = link.data('logged_user');
    let statuses = link.data('experiment_statuses');
    let modal = $(this);
    modal.find('.modal-title').text(gettext('Change status for experiment') +
        ' "' + experiment.title + '"');
    let modal_body = modal.find('.modal-body');
    let html = statuses_radio_options(experiment, statuses, logged_user);
    modal_body.text(gettext('Please select an option:'));
    modal_body.append(html);
    // if trustee will disapprove experiment, force her to write
    // justification message
    let modal_form = $('#id_status_choices');
    modal_form.find('input').on('change', function() {
        if ( $('input[name=status]:checked', '#id_status_choices').val()
            === 'not_approved') { // TODO: should be something like Experiment.NOT_APPROVED. See statuses variable.
            const justification = gettext('Justification is required to ' +
                'reject an experiment (this message will be sent to' +
                ' experiment researcher)');
            const placeholder = gettext('Please write a justification for' +
                ' rejecting this experiment');
            $('#justification_area').append(
                `<br>
                    <label for="justification">
                    ${justification}
                    <span class="alert">*</span></label>
                    <div class="form-group">
                        <textarea rows="10" id="not_approved_box"
                        required class="text-box-justification"
                    name="justification" placeholder="${placeholder}"></textarea>
                    </div>
                    `);
        } else {
            $('#justification_area').empty();
        }
    });
});