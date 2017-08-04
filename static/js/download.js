/**
 * Created by mruizo on 01/08/17.
 */
$(function () {
    var experimentId =  $("#experimentId").val();
    $("downloadButton").click(function () {
        $.fileDownload($(this).attr('/downloads/experimentId/'), {
            preparingMessageHtml: "The file download will begin shortly, please wait...",
            failMessageHtml: "There was a problem generating your data, please try again."
        });
        return false;
    });
});

// $(function() {
//     var progressTimer,
//         experimentId = $("#experimentId").val(),
//         progressbar = $("#progressbar"),
//         progressLabel = $( ".progress-label" ),
//         dialogButtons = [{
//             text: "Cancel Download",
//             click: closeDownload
//         }],
//         dialog = $( "#dialog" ).dialog({
//             autoOpen: false,
//             closeOnEscape: false,
//             resizable: false,
//             buttons: dialogButtons,
//             open: function() {
//                 progressTimer = setTimeout( progress, 2000 );
//             },
//             beforeClose: function() {
//                 downloadButton.button( "option", {
//                     disabled: false,
//                     label: "Start Download"
//                 });
//             }
//         }),
//         downloadButton = $( "#downloadButton" ).button().on( "click", function() {
//             // $( this ).button( "option", {
//             //     disabled: true,
//             //     label: "Downloading..."
//             // });
//             $.ajax({
//                 type: "POST",
//                 url: "/downloads/experimentId/",
//                 success: function(data) {
//                     dialog.dialog( "open" );
//                 }
//             });
//
//         });
//
//     progressbar.progressbar({
//         value: false,
//         change: function () {
//             progressLabel.text("Current Progress: " + progressbar.progressbar("value") + "%");
//         },
//         complete: function () {
//             progressLabel.text("Complete!");
//             dialog.dialog("option", "buttons", [{
//                 text: "Close",
//                 click: closeDownload
//             }]);
//             $(".ui-dialog button").last().trigger("focus");
//         }
//     });
//
//     function progress() {
//         var val = progressbar.progressbar("value") || 0;
//         progressbar.progressbar("value", val + Math.floor( Math.random() * 3 ));
//         if(val <= 99){
//             progressTimer = setTimeout( progress, 50 );
//         }
//     }
//
//     function closeDownload() {
//         clearTimeout( progressTimer );
//         dialog
//             .dialog( "option", "buttons", dialogButtons )
//             .dialog( "close" );
//         progressbar.progressbar( "value", false );
//         progressLabel
//             .text( "Starting download..." );
//         downloadButton.trigger( "focus" );
//     }
//
// });