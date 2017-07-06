/**
 * Created by caco on 22/06/17.
 */

/**
 * Returns how many experiments are to be analysed at the moment
 */
function load_to_be_analysed_count() {
    $.ajax({
        url: '/experiments/to_be_analysed/count',
        dataType: 'text',
        type: 'get',
        success: function(data) {
            // data is the number of experiments to be analysed, returned from server
            if (data > 0) {
                $('#new_experiments').addClass('badger');
                $('head').append('<style>.badger::after{content:"' + data + '"}</style>');
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log('jQuery.ajax() error when updating trustee notification.');
            console.log(errorThrown);
        }
    });
    if ($('#new_experiment').hasClass('badger')) {
        $('.badger')
    }
}

$(function () {
    load_to_be_analysed_count()
});