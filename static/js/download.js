/**
 * Created by mruizo on 01/08/17.
 */
$( function() {
    var progressTimer,
        progressbar = $("#progressbar"),
        progressLabel = $( ".progress-label" ),
        dialogButtons = [{
            text: "Cancel Download",
            click: closeDownload
        }],
        dialog = $( "#dialog" ).dialog({
            autoOpen: false,
            closeOnEscape: false,
            resizable: false,
            buttons: dialogButtons,
            open: function() {
                progressTimer = setTimeout( progress, 2000 );
            },
            beforeClose: function() {
                downloadButton.button( "option", {
                    disabled: false,
                    label: "Start Download"
                });
            }
        }),
        downloadButton = $( "#downloadButton" ).button().on( "click", function() {
            $( this ).button( "option", {
                disabled: true,
                label: "Downloading..."
            });

            dialog.dialog( "open" );
        });

}