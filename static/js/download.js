/**
 * Created by mruizo on 01/08/17.
 */

$(function () {
    var experimentId =  $("#experimentId").val();
    $(document).on("click", "a.fileDownloadCustomRichExperience", function () {
        var $preparingFileModal = $("#preparing-file-modal");
        $preparingFileModal.dialog({modal: true});
        $.fileDownload($(this).prop('href'), {
            sucessCallback: function (url) {
                $preparingFileModal.dialog('close');
            },
            failCallback: function (responseHtml, url) {
                $preparingFileModal.dialog('close');
                $("#error-modal").dialog({modal: true});
            },
            // abortCallback: function (responseHtml, url) {
            //     $preparingFileModal.dialog('close');
            //     $("#error-modal").dialog({modal: true});
            // },
        }).done(function () {
            window.location = '/experiments/' + experimentId;
        });

        return false;
    });
});
