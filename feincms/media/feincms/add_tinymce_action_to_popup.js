function stripHtml(s) {
	var matchTag = /<(?:.|\s)*?>/g;
        // Replace the tag
        s=s.replace(matchTag, "");
	s=s.replace(/&nbsp;/g, "");
	return s;
};
var FileBrowserDialogue = {
    init : function () {
        // Here goes your code for setting your custom things onLoad.
    },
    mySubmit : function (url, title) {
    	var URL = url;
        var win = tinyMCEPopup.getWindowArg("window");
        // insert information now
        win.document.getElementById(tinyMCEPopup.getWindowArg("input")).value = URL;
	if (!tinyMCEPopup.getWindowArg("is_image")) {
		win.document.getElementById('linktitle').value = title;
	};
        // close popup window
        tinyMCEPopup.close();
    }
};
tinyMCEPopup.onInit.add(FileBrowserDialogue.init, FileBrowserDialogue);

(function($) {
// Replace popup onlick action with tinymce onlick action.
if(tinyMCEPopup.getWindowArg('title', '') == "link_browser"){
// Make this onlick replacement only for tinymce popup
	$(document).ready(function($) {
		$('tr[class]').each(function() {  
			//get/grep the link from the "View on Website Link"
			url=$(this).find('a[title]').attr('href');
			if (!url){
			url=$(this).find('img').attr('src');
			};
			$(this).find('a[onclick]').each(function(){
				var $a_with_onclick = $(this);   
				title=stripHtml($a_with_onclick.html());
				$a_with_onclick.attr({'onClick': "FileBrowserDialogue.mySubmit('"+url+"', '"+title+"');",});
			});
		}); 
	});
};
})(django.jQuery);
