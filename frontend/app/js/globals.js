var globalCurrentDialog = "";
var sendMessageRequest = null;
var requestPeerID = null;
var tokenLiveCountMinutes = 150;
var secondsInMinute = 60;
var isEditRequestRunning = false;

function makeBasicAuth(user, password) {
  var tok = user + ':' + password;
  var hash = btoa(tok);
  return "Basic " + hash;
}

var originalAjax = $.ajax
$.ajax = function(options) {
    if (('username' in options) && ('password' in options)) {
        options['beforeSend'] = function (xhr) {
            xhr.setRequestHeader('Authorization', makeBasicAuth(options['username'], options['password']));
        }
    }
    originalAjax(options);
};

// Функция для генерации уникального UUID
var largeUuidv4 = function() {
  var result =  ('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = nextRandomInt(0xFFFFFFFF) * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return  v.toString(16);
  }));
  return (new Date().getTime()) + "-" + result;
};

// Получение/сохранение идентификатора
var fetchOrCreateUUID = function(fun) {
    var uuid = localStorage.getItem("reviewgram_uuid");
    var timestamp = parseInt(localStorage.getItem("reviewgram_uuid_timestamp"));
    if ((uuid === null) || (timestamp === null)) {
        uuid = largeUuidv4();
        timestamp = parseInt((new Date()).getTime() / 1000.0);
        localStorage.setItem("reviewgram_uuid", uuid);
        localStorage.setItem("reviewgram_uuid_timestamp", timestamp);
        fun(true, uuid, timestamp);
    } else {
        currentTimestamp = parseInt((new Date()).getTime() / 1000.0);
        if (currentTimestamp - timestamp >= tokenLiveCountMinutes * secondsInMinute) {
            uuid = largeUuidv4();
            timestamp = currentTimestamp;
            localStorage.setItem("reviewgram_uuid", uuid);
            localStorage.setItem("reviewgram_uuid_timestamp", timestamp);
            fun(true, uuid, timestamp);
        } else {
            fun(false, uuid, timestamp);
        }
    }
};

var makeRepeatedRequest = function(options, success)  {
    var ownOptions = options;
    ownOptions["success"] = success;
    ownOptions["error"] = function(xhr) {
         if (xhr.status == 404) {
             if (typeof options["on404"] == "function") {
                 options["on404"]();
             } else {
                 setTimeout(makeRepeatedRequest.bind(null, options, success), 5000);
             }
         } else {
             setTimeout(makeRepeatedRequest.bind(null, options, success), 5000);
        }
    };
    $.ajax(ownOptions);
};


// Начало для получения данных из чата для работы системы
var startRequestForRepoInformation = function(chatId, fun)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            makeRepeatedRequest({
                "url": "/reviewgram/register_chat_id_for_token/",
                "dataType": "text",
                "data": {
                    "chatId" : requestPeerID(chatId),
                    "uuid": uuid,
                },
                "method": "POST",
            }, fun);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            sendMessageRequest(text, wrapper);
        } else {
            wrapper();
        }
    });
};

// Получение настроек репозитория
var getRepoSettings = function(chatId, fun, on404)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            var wrapInner = function(o) {
                o.password = atob(o.password);
                fun(o);
            };
            makeRepeatedRequest({
                "url": "/reviewgram/get_repo_settings/",
                "dataType": "json",
                "data": {
                    "chatId" : requestPeerID(chatId),
                    "uuid": uuid,
                },
                "method": "GET",
                "on404" : on404
            }, wrapInner);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            sendMessageRequest(text, wrapper);
        } else {
            wrapper();
        }
    });
};

// Установка настроек репозитория
var setRepoSettings = function(chatId, fun, repoUserName, repoSameName, user, password, on404)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            makeRepeatedRequest({
                "url": "/reviewgram/set_repo_settings/",
                "dataType": "json",
                "data": {
                    "chatId" : requestPeerID(chatId),
                    "uuid": uuid,
                    "repoUserName": repoUserName,
                    "repoSameName": repoSameName,
                    "user": user,
                    "password": btoa(password)
                },
                "method": "POST",
                "on404": on404
            }, fun);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            sendMessageRequest(text, wrapper);
        } else {
            wrapper();
        }
    });
};

var widgetsToCallbacks = {};
var repoSettings = {};
var branchName = "";
var lastCommit = "";
var editedFileName = "";
var editedFileUrl = "";
var editedFileSha = "";
var editedFileContent = "";
var rangeStart = 0;
var rangeEnd = 0;
var aceEditorForRangeSelect = null;
var aceEditorMain = null;
var allowedFileExtensions = [".txt", ".py"];
var editorRangeSelectStart = null;
var editorRangeSelectEnd = null;
var editorRangeSelectLastClick = null;
var editorCursorPosition = null;
var editorAutocompleteSendTimeoutHandle = null;
var lineSelectLimit = 10;
var editorEditedPart = "";
var namesToModes = {".py": "ace/mode/python"};
var lineSeparator = "";
var resultFileContent = "";
var editedSoundFileBlob = null;
var globalRecorder = null;
var currentRecorderId = 0;

var fileNameToAceMode = function(fileName) {
    var name = fileName.toLowerCase();
    for (var  key in namesToModes) {
        if (namesToModes.hasOwnProperty(key)) {
            if (name.endsWith(key)) {
                return namesToModes[key];
            }
        }
    }
    return "ace/mode/plain_text";
};

function uint8ArrayToBase64( bytes ) {
    var len = bytes.byteLength;
    for (var i = 0; i < len; i++) {
        binary += String.fromCharCode( bytes[ i ] );
    }
    return window.btoa( binary );
}

// Инициализация виджета микрофона
// TODO: Нормальная работа
var initMicrophoneWidgets = function() {
    var e = $(".reviewgram-microphone-widget");
    e.html("<div class=\"button-wrapper\"><div class=\"button\"></div><div class=\"label\">Нажмите, чтобы ввести голосом</div></div>");
    for (var i = 0; i < e.length; i++) {
        $(e[i]).attr("specific-id", i);
    }
    if (globalRecorder == null) {
        globalRecorder = new Recorder();
        globalRecorder.ondataavailable = function( typedArray ) {
          var dataBlob = new Blob( [typedArray], { type: 'audio/wav' } );
          var fileName = new Date().toISOString() + ".wav";

          dataBlob.arrayBuffer().then(function(o) { editedSoundFileBlob = new Uint8Array(o); });
          /*
          var url = URL.createObjectURL( dataBlob );

          var audio = document.createElement('audio');
          audio.controls = true;
          audio.src = url;

          var link = document.createElement('a');
          link.href = url;
          link.download = fileName;
          link.innerHTML = link.download;

          var li = document.createElement('li');
          li.appendChild(link);
          li.appendChild(audio);

          recordingslist.appendChild(li);
          */
        };
    }
    e.click(function() {
        currentRecorderId = parseInt($(this).attr('specific-id'));
        if ($(this).hasClass("in-process")) {
            $(this).removeClass("in-process");
            $(this).addClass("recognizing");
            $(this).find(".label").html("Производится распознавание");
            globalRecorder.stop();
            // TODO: callback here
        } else {
            if ($(this).hasClass("recognizing")) {
                $(this).removeClass("recognizing");
                $(this).find(".label").html("Нажмите, чтобы ввести голосом");
                $(".btn-next-tab").removeAttr("disabled");
                // TODO: callback here
            } else {
                $(this).addClass("in-process");
                $(this).find(".label").html("Введите команду");
                globalRecorder.start().catch(function(e){
                    window.alert( e.message );
                });
                $(".btn-next-tab").attr("disabled", "disabled");
                // TODO: callback here
            }
        }
    });
}


$("body").on("click", ".reviewgram-select-box li", function() {
    $(this).closest(".reviewgram-select-box").find("li").removeClass("selected");
    $(this).addClass("selected");
});

var makeSearchSubstringHandler = function(dependentSelector) {
    return function() {
        var a = $(this).val().trim();
        var elements = $(dependentSelector);
        for (var i = 0; i < elements.length; i++) {
            var element = $(elements[i]);
            var name = element.attr("data-name");
            var match = true;
            if (a.length > 0) {
                match = (name.indexOf(a) != -1);
            }
            if (match) {
                element.removeClass("hidden").css("display", "block");
            } else {
                element.addClass("hidden").css("display", "none");
            }
        }
    }
};

$("body").on("cut paste keyup", "#branchNameSearch", makeSearchSubstringHandler("#branchName ul li"));
$("body").on("cut paste keyup", "#commitFileSearch", makeSearchSubstringHandler("#commitFile ul li"));


function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

 function b64DecodeUnicode(str) {
    // Going backwards: from bytestream, to percent-encoding, to original string.
    return decodeURIComponent(atob(str).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
}

function b64EncodeUnicode(str) {
    // first we use encodeURIComponent to get percent-encoded UTF-8,
    // then we convert the percent encodings into raw bytes which
    // can be fed into btoa.
    return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,
        function toSolidBytes(match, p1) {
            return String.fromCharCode('0x' + p1);
    }));
}

function isMatchesAllowedExtensions(fileName) {
    var name = fileName.toLowerCase();
    for (var  i = 0 ; i < allowedFileExtensions.length; i++) {
        if (name.endsWith(allowedFileExtensions[i])) {
            return true;
        }
    }
    return false;
}


function selectAceGutterRange(parent, start, end) {
    var list = $(parent + " .ace_gutter-cell");
    for (var i = 0; i < list.length; i++) {
        var e  = $(list[i]);
        var no = parseInt(e.text());
        if (no >= start && no <= end) {
            e.addClass("selected");
        } else {
            e.removeClass("selected");
        }
    }
}

$("body").on("click", "#editor_range_select .ace_gutter-cell", function() {
    var currentLineNo = parseInt($(this).text());
    if (editorRangeSelectStart == null) {
        editorRangeSelectStart = currentLineNo;
        $(this).addClass("selected");
    } else {
        if (Math.abs(currentLineNo - editorRangeSelectLastClick) < lineSelectLimit) {
            if (currentLineNo < editorRangeSelectLastClick) {
                editorRangeSelectStart = currentLineNo;
                editorRangeSelectEnd = editorRangeSelectLastClick;
            } else {
                editorRangeSelectStart = editorRangeSelectLastClick;
                editorRangeSelectEnd = currentLineNo;
            }
        } else {
            if (currentLineNo < editorRangeSelectLastClick) {
                editorRangeSelectStart = currentLineNo;
                editorRangeSelectEnd = currentLineNo + lineSelectLimit - 1;
            } else {
                editorRangeSelectStart = currentLineNo - lineSelectLimit + 1;
                editorRangeSelectEnd = currentLineNo;
            }
        }
        selectAceGutterRange("#editor_range_select", editorRangeSelectStart, editorRangeSelectEnd);
    }
    editorRangeSelectLastClick = currentLineNo;
});

$("body").on("click", ".edit-tab-container .header", function() {
    var parent = $(this).parent();
    if (parent.hasClass("selected")) {
        parent.removeClass("selected");
        parent.find(".section-arrow").removeClass("toggled").removeClass("arrow-down").addClass("arrow-right");
    } else {
        parent.addClass("selected");
        parent.find(".section-arrow").addClass("toggled").addClass("arrow-down").removeClass("arrow-right");
    }
});

$("body").on("click", ".autocompletion .body .btn.btn-md", function() {
    var me = $(this);
    var row = parseInt(me.attr("data-row"));
    var column = parseInt(me.attr("data-column"));
    var completeType = me.attr("data-complete-type");
    var complete = me.attr("data-complete");
    if (completeType != "no_space") {
        complete = " " + completeType;
    }
    aceEditorMain.session.insert({"row": row, "column": column}, complete);
    aceEditorMain.focus();
    $(".autocompletion .body").html("");
});

setInterval(function() {
    if ($("#editor_range_select").length != 0) {
        if (editorRangeSelectStart != null) {
            if (editorRangeSelectEnd != null) {
                selectAceGutterRange("#editor_range_select", editorRangeSelectStart, editorRangeSelectEnd);
            } else {
                selectAceGutterRange("#editor_range_select", editorRangeSelectStart, editorRangeSelectStart);
            }
        }
    }
}, 300);

// Разбивает строки на токены
var tokenizePython = function(str) {
    var originalLength = str.length;
    var strippedStr = str.replace(/^[ \t]+/, "");
    var newLen = strippedStr.length
    var offset = originalLength - newLen;
    var getToken = filbert.tokenize(strippedStr, {"locations" : true});
    var result = [];
    var error = false;
    var end = false;
    var lastEnd = 0;
    while (!error && !end) {
        try {
            var tmp = getToken();
            if (tmp.type.type == "eof") {
                end = true;
            } else {
                lastEnd = tmp.end;
                result.push([tmp.start + offset, tmp.end + offset]);
            }
        } catch (e) {
            result.push([lastEnd + offset + 1, originalLength]);
            error = true;
        }
    }
    return result;
};

var getResultFileContent = function() {
    var strings = editedFileContent.split(lineSeparator);
    var begin = strings.slice(0, editorRangeSelectStart - 1);
    var rangeEnd = editorRangeSelectEnd;
    if (rangeEnd == null) {
        rangeEnd = editorRangeSelectStart;
    }
    var end = strings.slice(rangeEnd);
    var middle = aceEditorMain.session.doc.getAllLines();
    var content = begin.concat(middle).concat(end);
    resultFileContent = content.join(lineSeparator);
    return resultFileContent;
};

// Получает предыдущие строки
var getPreviousTokens = function(cursorPosition) {
    var result = [];
    var pos = cursorPosition;
    var lines = aceEditorMain.session.doc.getAllLines();
    var line = lines[pos.row];
    var tokens = tokenizePython(line);
    for (var  i = 0; i < tokens.length; i++) {
        if (tokens[i][0] <= pos.column) {
            result.push(line.substring(tokens[i][0], tokens[i][1]));
        }
    }
    return result;
};

//  Посылает запрос на автодополнение
var sendAutocompleteRequest = function() {
    var chatId = requestPeerID(globalCurrentDialog);
    var branchId = branchName;
    var row =  editorCursorPosition.row;
    var column = editorCursorPosition.column;
    var line = editorCursorPosition.row + editorRangeSelectStart;
    var position = editorCursorPosition.column;
    var content = b64EncodeUnicode(getResultFileContent());
    var tokens = getPreviousTokens(editorCursorPosition);
    $.ajax({
        "method": "POST",
        "dataType": "json",
        "url": "/reviewgram/get_autocompletions/",
        'contentType': 'application/json',
        "data": JSON.stringify({
            "tokens": tokens,
            "content": content,
            "line": line,
            "position": position,
            "chatId": chatId,
            "branchId": branchId
        }),
        "success": function(o) {
            if ((row == editorCursorPosition.row) && (column == editorCursorPosition.column)) {
                $(".autocompletion .body").html("");
                for (var i = 0; i < o.length; i++) {
                    $("<button />", {
                        'class': 'btn btn-md',
                        'text': o[i]['name_with_symbols']
                    }).attr("data-row", row)
                    .attr("data-column", column)
                    .attr("data-complete-type", o[i]['append_type'])
                    .attr("data-complete", o[i]['complete'])
                    .appendTo(".autocompletion .body");
                }
            }
        },
        "error": function(xhr) {

        }
    });
};
