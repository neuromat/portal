/**
 * Created by mruizo on 01/08/17.
 */
$(function() {
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
                $.ajax({
                    type: "POST",
                    url: "/downloads/3/"
                });
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

    progressbar.progressbar({
        value: false,
        change: function () {
            progressLabel.text("Current Progress: " + progressbar.progressbar("value") + "%");
        },
        complete: function () {
            progressLabel.text("Complete!");
            dialog.dialog("option", "buttons", [{
                text: "Close",
                click: closeDownload
            }]);
            $(".ui-dialog button").last().trigger("focus");
        }
    });

    function progress() {
        var val = progressbar.progressbar("value") || 0;
        progressbar.progressbar("value", val + Math.floor( Math.random() * 3 ));
        if(val <= 99){
            progressTimer = setTimeout( progress, 50 );
        }
    }

    function closeDownload() {
        clearTimeout( progressTimer );
        dialog
            .dialog( "option", "buttons", dialogButtons )
            .dialog( "close" );
        progressbar.progressbar( "value", false );
        progressLabel
            .text( "Starting download..." );
        downloadButton.trigger( "focus" );
    }

});