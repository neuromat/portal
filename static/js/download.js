/**
 * Created by mruizo on 01/08/17.
 */
$(function () {
   $(document).on("click", "a.fileDownloadSimpleRichExperience", function () {
       $.fileDownload($(this).prop('href'), {
           preparingMessageHtml: "We are preparing your download, please wait...", 
           failMessageHtml: "There was a problem generating your download, please try again." 
       });
       return false;
   });
});

// $(function () {
//     var experimentId =  $("#experimentId").val(),
//         url = "/downloads/experimentId/";
//     $(document).on("click", "a.fileDownloadCustomRichExperience",function () {
//         var $preparingFileModal = $("preparing-file-modal");
//         $preparingFileModal.dialog({modal: true});
//         $.fileDownload($(this).prop('href'), {
//             sucessCallback: function (url) {
//                 $preparingFileModal.dialog('close');
//             },
//             failCallback: function (responseHtml, url) {
//                 $preparingFileModal.dialog('close');
//                 $("#error-modal").dialog({modal: true});
//             }
//             // preparingMessageHtml: "The file download will begin shortly, please wait...",
//             // failMessageHtml: "There was a problem generating your data, please try again."
//         });
//         return false;
//     });
// });

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
//                 // progressTimer = setTimeout( progress, 2000 );
//                 downloadFile();
//             },
//             beforeClose: function() {
//                 downloadButton.button( "option", {
//                     disabled: false,
//                     label: "Start Download"
//                 });
//             }
//         }),
//         downloadButton = $( "#downloadButton" ).button().on( "click", function() {
//             $( this ).button( "option", {
//                 disabled: true,
//                 label: "Downloading..."
//             });
//             dialog.dialog( "open" );
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
//     function downloadFile() {
//         experimentId = $("#experimentId").val()
//         $.ajax({
//                 type: "POST",
//                 url: "/downloads/7/",
//                 success: function(data) {
//                     dialog.dialog( "close" );
//                 }
//             });
//         // dialog.dialog("close");
//     }
//
// });