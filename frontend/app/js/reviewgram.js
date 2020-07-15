// Промежуток для выбора в редакторе
function ReviewgramEditorSelectRange() {
    this.start = null;
    this.end = null;
    this.lastClick = null;
    this.limit = 10;
};

// Редактируемый файл
function EditedFile() {
    this.name = "";
    this.url = "";
    this.sha = "";
    this.content = "";
    this.lineSeparator = "";
};

// API webogram
function WebogramAdapter() {
    this.appMessagesManager = null;
    this.appPeersManager = null;
    this.mtpApiManager = null;
    this.$scope = null
};

// Лексер
function Tokenizer() {
}

// @var String line строка
// @return Object[] набор лексем
Tokenizer.prototype.tokenize = function(line) {
    throw "Метод не реализован";
};

// @var String line строка
// @var Object cursorPosition позиция курсора
// @return Object[] набор лексем
Tokenizer.prototype.getPreviousTokens = function(line, cursorPosition) {
    var result = [];
    var pos = cursorPosition;
    var tokens = this.tokenize(line);
    for (var  i = 0; i < tokens.length; i++) {
        if (tokens[i][0] <= pos.column) {
            result.push(line.substring(tokens[i][0], tokens[i][1]));
        }
    }
    return result;
};

// Лексер питона
function PythonTokenizer() {

}

PythonTokenizer.prototype =  Object.create(Tokenizer.prototype);
PythonTokenizer.prototype.tokenize = function(line) {
    var str = line;
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

// Возвращает лексер для языка
function TokenizerFactory() {
    this.langsToTokenizer = {
        "1": new PythonTokenizer()
    };
};

TokenizerFactory.prototype.create = function (langId) {
    if (this.langsToTokenizer.hasOwnProperty(langId)) {
        return this.langsToTokenizer[langId];
    } else {
        throw "Не задан лексический анализатор для указанного языка";
    }
};

// Основной класс для работы
function Reviewgram() {
    // @var {Recorder} рекордер для записи
    this._recorder = null;
    // @var {ReviewgramEditorSelectRange} текуший промежуток выбранный для редактирования в диалоге выбора редактора
    this._editorRange = new ReviewgramEditorSelectRange();
    // @var {EditedFile} редактируемый файл
    this._editedFile = new EditedFile();
    // @var {WebogramAdapter} адаптер для работы с Telegram
    this._webogramAdapter = new WebogramAdapter();
    // @var {String} результирующий файл
    this._resultFileContent = "";
    // @var {Object} редактор для выбора промежутка
    this._rangeSelectEditor = null;
    // @var {Object} редактор для редактирования текста
    this._mainEditor = null;
    // @var {Object} позицияи курсора в главном редакторе
    this._mainEditorCursorPosition = null;
    // @var {String} текущий диалог
    this._currentDialog = "";
    // @var {String} имя ветки
    this._branchName = "";
    // @var {Number} время жизни токена авторизациии Reviewgram в минутах
    this._tokenLiveCountMinutes = 150;
    // @var {Number} число секунд в минуте
    this._secondsInMinute = 60;

    this.__selectAceGutterRange = function(parent, start, end) {
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
    // Получение/сохранение идентификатора авторизации  пользователя
    // @var {Function} функция которой передаётся время и UUID
    this.__fetchOrCreateUUID = function(fun) {
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
            if (currentTimestamp - timestamp >= this._tokenLiveCountMinutes * this._secondsInMinute) {
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
    // Инициализация виджета микрофона
    // TODO: Нормальная работа
    this._initMicrophoneWidgets = function() {
        var e = $(".reviewgram-microphone-widget");
        var content = "<div class=\"button-wrapper common write\"><div class=\"button common\"></div></div>";
        content += "<div class=\"button-wrapper common append\"><div class=\"button common plus\"></div></div>";
        content += "<div class=\"label\">&lt;-Нажмите, чтобы<br/>&lt;-ввести голосом<br/>&lt;-или дополнить</div>";
        content += "<a href=\"/dictationhelp.html\" target=\"_blank\"><div class=\"button-wrapper\"><div class=\"button help\"></div></div></a>";
        e.html(content);
        for (var i = 0; i < e.length; i++) {
            $(e[i]).attr("specific-id", i);
        }
        if (this._recorder == null) {
            try {
                this._recorder = new Recorder();
                this._recorder.ondataavailable = function( typedArray ) {
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
            } catch(exc) {
                  // Если голосовой ввод не поддерживается браузером - выключаем его.
                  e.remove();
            }
        }
        var me = this;
        e.find(".button-wrapper.common").click(function() {
            currentRecorderId = parseInt($(this).attr('specific-id'));
            var parent = $(this).closest(".reviewgram-microphone-widget");
            parent.removeClass("append").removeClass("write");
            if ($(this).hasClass("write"))
            {
                parent.find(".button-wrapper.common.append").css("display", "none");
                parent.addClass("write");
            }
            else
            {
                parent.find(".button-wrapper.common.write").css("display", "none");
                parent.addClass("append");
            }
            if (parent.hasClass("in-process")) {
                parent.removeClass("in-process");
                parent.addClass("recognizing");
                parent.find(".label").html("Производится<br/> распознавание");
                me._recorder.stop();
                // TODO: callback here
            } else {
              if (parent.hasClass("recognizing")) {
                  parent.removeClass("recognizing");
                  parent.find(".label").html("&lt;-Нажмите, чтобы<br/>&lt;-ввести голосом<br/>&lt;-или дополнить");
                  $(".btn-next-tab").removeAttr("disabled");
                  parent.find(".button-wrapper.common").css("display", "inline-block");
                  // TODO: callback here
              } else {
                  parent.addClass("in-process");
                  parent.find(".label").html("Идёт запись");
                  me._recorder.start().catch(function(exc){
                      window.alert( exc.message );
                      parent.remove();
                  });
                  $(".btn-next-tab").attr("disabled", "disabled");
                  // TODO: callback here
              }
            }
        });
    };
    this._initSearchHintWidgets = function() {
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
          };
        };

        $("body").on("cut paste keyup", "#branchNameSearch", makeSearchSubstringHandler("#branchName ul li"));
        $("body").on("cut paste keyup", "#commitFileSearch", makeSearchSubstringHandler("#commitFile ul li"));
    };
    this._initSelectBoxes = function() {
        $("body").on("click", ".reviewgram-select-box li", function() {
            $(this).closest(".reviewgram-select-box").find("li").removeClass("selected");
            $(this).addClass("selected");
        });
    };
    this._initRangeSelect = function() {
        var me = this;

        $("body").on("click", "#editor_range_select .ace_gutter-cell", function() {
            var currentLineNo = parseInt($(this).text());
            if (me._editorRange.start == null) {
                me._editorRange.start = currentLineNo;
                $(this).addClass("selected");
            } else {
                if (Math.abs(currentLineNo - me._editorRange.lastClick) < me._editorRange.limit) {
                    if (currentLineNo < me._editorRange.lastClick) {
                        me._editorRange.start = currentLineNo;
                        me._editorRange.end = me._editorRange.lastClick;
                    } else {
                        me._editorRange.start = me._editorRange.lastClick;
                        me._editorRange.end = currentLineNo;
                    }
                } else {
                    if (currentLineNo < me._editorRange.lastClick) {
                        me._editorRange.start = currentLineNo;
                        me._editorRange.end = currentLineNo + me._editorRange.limit - 1;
                    } else {
                        me._editorRange.start = currentLineNo - me._editorRange.limit + 1;
                        me._editorRange.end = currentLineNo;
                    }
                }
                me.__selectAceGutterRange("#editor_range_select", me._editorRange.start, me._editorRange.end);
            }
             me._editorRange.lastClick = currentLineNo;
        });

        setInterval(function() {
            if ($("#editor_range_select").length != 0) {
                if ( me._editorRange.start != null) {
                    if ( me._editorRange.end != null) {
                        me.__selectAceGutterRange("#editor_range_select", me._editorRange.start, me._editorRange.end);
                    } else {
                        me.__selectAceGutterRange("#editor_range_select", me._editorRange.start, me._editorRange.start);
                    }
                }
            }
        }, 300);
    };
    this._initTabWidgets = function() {
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
    };
    this._initAutocompleteButtonHandlers = function() {
        var parent = this;
        $("body").on("click", ".autocompletion .body .btn.btn-md", function() {
            var me = $(this);
            var row = parseInt(me.attr("data-row"));
            var column = parseInt(me.attr("data-column"));
            var completeType = me.attr("data-complete-type");
            var complete = me.attr("data-complete");
            if (completeType != "no_space") {
                complete = " " + completeType;
            }
            parent._mainEditor.session.insert({"row": row, "column": column}, complete);
            parent._mainEditor.focus();
            $(".autocompletion .body").html("");
        });
    };
    // Получает предыдущие лексемы
    this._getPreviousTokens = function(langId, cursorPosition) {
        var result = [];
        var pos = cursorPosition;
        var lines = this._mainEditor.session.doc.getAllLines();
        var line = lines[pos.row];
        var factory = new TokenizerFactory();
        return factory.create(langId).getPreviousTokens(line, cursorPosition);
    };
    // Возвращает содержимое результрующего файла
    this._getResultFileContent = function() {
        var strings = this._editedFile.content.split(this._editedFile.lineSeparator);
        var begin = strings.slice(0, this._editorRange.start - 1);
        var rangeEnd = this._editorRange.start.end;
        if (rangeEnd == null) {
            rangeEnd = this._editorRange.start;
        }
        var end = strings.slice(rangeEnd);
        var middle = this._mainEditor.session.doc.getAllLines();
        var content = begin.concat(middle).concat(end);
        this._resultFileContent = content.join(this._editedFile.lineSeparator);
        return this._resultFileContent;
    };
    // Инициализация работы с UI системы
    this.initReviewgramEvents = function() {
        this._initSelectBoxes();
        this._initSearchHintWidgets();
        this._initMicrophoneWidgets();
        this._initRangeSelect();
        this._initTabWidgets();
        this._initAutocompleteButtonHandlers();
    };
    // Инициализация для работы с Webogram
    this.initWebogramAdapter = function(appMessagesManager, appPeersManager, mtpApiManager) {
        this._webogramAdapter.appMessagesManager = appMessagesManager;
        this._webogramAdapter.appPeersManager = appPeersManager;
        this._webogramAdapter.mtpApiManager = mtpApiManager;
    };
    // Устанавливает текущий диалог в системе
    this.setCurrentDialog = function(dialogString) {
        this._currentDialog = dialogString;
    };
    // Возвращает текущий диалог
    this.getCurrentDialog = function() {
        return this._currentDialog;
    };
    // Отправить сообщение боту
    // @var {String} text текст сообщения
    // @var {Function} onSuccess функция для ответа на результат
    this.sendMessageToBot = function(text, onSuccess)  {
        if ((typeof onSuccess === "undefined")  || (onSuccess === null)) {
            onSuccess = function() { console.log("Message to Reviewgram bot sent successfully!"); }
        }
        var me = this;
        $.ajax({
            "url": "/reviewgram/bot_username/",
            "dataType": "text",
            "method": "GET",
            "success": function(result) {
                me._webogramAdapter.appPeersManager.resolveUsername(result).then(function (peerID) {
                    var sentRequestOptions = {}
                    var apiPromise = me._webogramAdapter.mtpApiManager.invokeApi('messages.sendMessage', {
                      flags: 128,
                      peer: me._webogramAdapter.appPeersManager.getInputPeerByID(peerID),
                      message: text,
                      random_id: [nextRandomInt(0xFFFFFFFF), nextRandomInt(0xFFFFFFFF)],
                      reply_to_msg_id: 0,
                      entities: []
                    }, sentRequestOptions);
                    apiPromise.then(function() {
                       me._webogramAdapter.appMessagesManager.flushHistory(peerID).then(function() {
                           fun();
                       });
                    });
                });
            },
            "error" : function() {
                setTimeout(function() {
                    me.sendMessageToBot(text, onSuccess);
                }, 5000);
            }
        });
    };
    // Запрос PeerID через API Webogram
    this.requestPeerID = function(peerString) {
        return this._webogramAdapter.appPeersManager.getPeerID(peerString);
    };
    // Возвращает PeerID текущего диалога
    this.getCurrentDialogPeerID = function() {
        return this.requestPeerID(this.getCurrentDialog());
    };

    //  Посылает запрос на автодополнение
    // @var {Number} langId ID языка
    this.sendAutocompleteRequest = function(langId) {
        var chatId = this.getCurrentDialogPeerID();
        var branchId = this._branchName;
        var row =  this._mainEditorCursorPosition.row;
        var column = this._mainEditorCursorPosition.column;
        var line = this._mainEditorCursorPosition.row + this._editorRange.start;
        var position = this._mainEditorCursorPosition.column;
        var content = b64EncodeUnicode(this.getResultFileContent());
        var tokens = null;
        try {
            tokens = this._getPreviousTokens(langId, this._mainEditorCursorPosition);
        } catch (e) {
            return;
        }
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
                "branchId": branchId,
                "langId": langId
            }),
            "success": function(o) {
                if ((row == this._mainEditorCursorPosition.row) && (column == this._mainEditorCursorPosition.column)) {
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
}
