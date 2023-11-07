var textareas = document.getElementsByTagName('textarea');
var count = textareas.length;
for(var i=0;i<count;i++){
    textareas[i].onkeydown = function(e){
        if(e.keyCode==9 || e.which==9){
            e.preventDefault();
            var s = this.selectionStart;
            this.value = this.value.substring(0,this.selectionStart) + "    " + this.value.substring(this.selectionEnd);
            this.selectionEnd = s+4; 
        }
    }
}

function doPOST(url, data, outfunc) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            try {
                var res = JSON.parse(this.responseText);
                if (outfunc === "return") {
                    return res;
                }
                else {
                    outfunc(res);
                }
            }
            catch(err) {
                if (outfunc === "return") {
                    return this.responseText;
                }
                else {
                    outfunc(this.responseText);
                }
            }
        }
    }
    xmlhttp.open("POST", url, false);
    xmlhttp.setRequestHeader("Content-Type", "application/json");
    xmlhttp.send(JSON.stringify(data));
}

shortcut.add('ctrl+s', saveNotes);

function makeLink() {
    noteid = document.getElementById('currentTitle').value;
    render = confirm('Render text (or display raw). Yes: render, Cancel: raw');
    link = prompt('Enter link name (this will be part of the URL - eg: https://notes.marcusj.tech/link/demo)');
    doPOST('/makelink', {'id':noteid, 'render':render, 'link':link}, function(res) {
        if ('error' in res) {
            alert('error: ' + res['error']);
        } else {
            window.location.href = res['url'];
        }
    })
}

function toggleNotes() {
    li = document.getElementById('notestoggle');
    leftpane = document.getElementById('leftpane');
    midpane = document.getElementById('midpane');

    if (li.className == 'nav active') {
        leftpane.style = 'display: none';
        li.className = 'nav';
        midpane.style = 'width: 40%';
    } else {
        leftpane.style = '';
        li.className = 'nav active';
        midpane.style = 'width: 30%';
    }
}

function logout() {
    if (confirm('Are you sure you want to log out? Any unsaved progress will be lost.')) {
        window.location.href = '/logout';
    }
}

function saveNotes() {
    var area = document.getElementById('editor');
    var ctitle = document.getElementById('currentTitle');
    if (ctitle.value == '') {
        if (checksave()) {
            return;
        }
        
        ntitle = prompt('Title is not set. Enter a title or click cancel.')
        if (ntitle) {
            ctitle.value = ntitle
        } else {
            return
        }
    }
    var data = {};
    data[ctitle.value] = area.value;
    for (note in notes) {
        ls = window.sessionStorage.getItem(note);
        if (ls) {
            data[note] = ls;
        }
    }

    doPOST('/notes', data, function(res) {
        $.notify("Saved Notes", "success"); // first time trying jQuery
    })
}

function unescape(text) {
    text = text.split('|bt|').join('`');
    text = text.split('|lt|').join('<');
    text = text.split('|gt|').join('>');
    return text;
}

function openNote(id) {
    var note = notes[id];
    document.getElementById('currentTitle').value = id;
    document.getElementById('currentDate').value = note['date'];
    ls = window.sessionStorage.getItem(id);
    if (ls) {
        document.getElementById('editor').value = ls;
    } else {
        document.getElementById('editor').value = unescape(note['body']);
    }
    if (note['link']) {
        nav = document.getElementById('linkNav');
        nav.href = '/link/' + note['link'];
        nav.innerText = 'View Link';
    }
    //document.getElementById(note).className 'node active'; // would need to un-active previous note
    updateContent();
}

function newNote() {
    var ntitle = prompt("Title:");
    if (ntitle) {
        notes[ntitle] = ''
        document.getElementById('editor').value = '';
        document.getElementById('currentTitle').value = ntitle;
        saveNotes();
        $.notify("Created", "success")
    }
}

function toggleAutosave() {
    li = document.getElementById('savetoggle');

    if (li.className == 'nav active') {
        li.className = 'nav';
    } else {
        li.className = 'nav active';
    }
}

function deleteNote() {
    var ntitle = document.getElementById('currentTitle').value;

    if (confirm('Are you sure you want to delete note: ' + ntitle + '? This action cannot be undone.')) {
        doPOST('/delete/note', {'id': ntitle}, function() {
            delete notes[ntitle];
            document.getElementById(ntitle).style.display = 'none';
            document.getElementById('currentTitle').value = '';
            document.getElementById('editor').value = '';
            document.getElementById('currentDate').value = '';
            updateContent();
            $.notify("Deleted", "info")
        })
    }
}

function checksave() {
    return document.getElementById('savetoggle').className == 'nav active';
}

function updateContent() {
    var area = document.getElementById('editor');
    var content = document.getElementById('content');

    window.sessionStorage.setItem(document.getElementById('currentTitle').value, area.value);

    content.innerHTML = marked.parse(area.value)
}

var area = document.getElementById('editor');
if (area.addEventListener) {
area.addEventListener('input', function() {
    updateContent();
}, false);
} else if (area.attachEvent) {
    area.attachEvent('onpropertychange', function() {
        // IE-specific event handling code
        updateContent();
    });
}

setInterval(function() {
    if (checksave()) {
        saveNotes();
    }
}, 60 * 1000) // every minute
