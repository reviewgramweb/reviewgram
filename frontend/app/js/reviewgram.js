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
    this.langId = "";
    this.lineSeparator = "";
    this.editedPart = "";
};

// API webogram
function WebogramAdapter() {
    this.appMessagesManager = null;
    this.appPeersManager = null;
    this.mtpApiManager = null;
    this.$scope = null
    this.$rootScope = null;
    this.$modal = null;
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
    // @var {String} хеш последнего коммита
    this._lastCommit = "";
    // @var {String[]} поддерживаемые расширения для файлов
    this._allowedFileExtensions = [".txt", ".py", ".dat", ".inc", ".pri", ".mod"];
    // @var {Number} время жизни токена авторизациии Reviewgram в минутах
    this._tokenLiveCountMinutes = 150;
    // @var {Number} число секунд в минуте
    this._secondsInMinute = 60;
    // @var {Object} настройки репозитория
    this._repoSettings = null;
    // @var {Object} названия языков к имени
    this.langIdsToNames = {
        1 : "Python"
    };
    // @var {Object} ID языков к режимам
    this.langIdsToModes = {
        1 : "ace/mode/python"
    };
    // @var {Object} соотношения раширений c ID языков
    this._extsToLangIds = {
        ".txt": null,
        ".py": 1,
        ".dat": null,
        ".inc": null,
        ".pri": null,
        ".mod": null,
    };
    // @var {Boolean} запущен ли запрос на редактирование
    this._isEditRequestRunning = false;
    // @var {Number} хендл на автодополнение
    this._autocompleteSendTimeoutHandle = null;

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
    // @var {Function} fun функция которой передаётся время и UUID
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
    // Возвращает истину если файл подходит под разрешённые расширения
    // @var {String} имя файла
    // @return Boolean полходит или нет
    this.__isMatchesAllowedExtensions = function(fileName) {
        var name = fileName.toLowerCase();
        for (var  i = 0 ; i < this._allowedFileExtensions.length; i++) {
            if (name.endsWith(this._allowedFileExtensions[i])) {
                return true;
            }
        }
        return false;
    }
    // Преобарзует имя файла в режим ACE Editor
    // @var {String} fileName имя файла
    // @return {String} имя файла
    this.__fileNameToAceMode = function(fileName) {
        var name = fileName.toLowerCase();
        if (name.endsWith(".txt")) {
            return  "ace/mode/plain_text";
        }
        return this.langIdsToModes[this.__fileNameToLangId(fileName)];
    };
    // Преобарзует имя файла в режим ACE Editor
    // @var {String} fileName имя файла
    // @return {String} имя файла
    this.__fileNameToLangId = function(fileName) {
        var name = fileName.toLowerCase();
        for (var key in this._extsToLangIds ) {
            if (this._extsToLangIds.hasOwnProperty(key)) {
                if (name.endsWith(key)) {
                    var id =  this._extsToLangIds[key];
                    if (id == null) {
                        return this._repoSettings.langId;
                    }
                }
            }
        }
        return this._repoSettings.langId;
    };
    // Получение настроек репозитория
    // @var {String} ID чата
    // @var {Function}  onSuccess функция, которой передастся JSON-объект настроек после получения
    // @var {Function}  on404 функция которая дёрнется при 404
    this._getRepoSettings = function(chatId, onSuccess, on404)  {
        var me = this;
        this.__fetchOrCreateUUID(function(isNew, uuid, timestamp) {
            var wrapper = (function(fun) {
                var wrapInner = function(o) {
                    o.password = atob(o.password);
                    fun(o);
                };
                makeRepeatedRequest({
                    "url": "/reviewgram/get_repo_settings/",
                    "dataType": "json",
                    "data": {
                        "chatId" : reviewgram.requestPeerID(chatId),
                        "uuid": uuid,
                    },
                    "method": "GET",
                    "on404" : on404
                }, wrapInner);
            }).bind(null, onSuccess);
            if (isNew) {
                var text = btoa(uuid);
                me.sendMessageToBot(text, wrapper);
            } else {
                wrapper();
            }
        });
    };

    // Установка настроек репозитория
    // @var {String} ID чата
    // @var {Function} onSuccess функция которая дёргается при успехе
    // @var {String} repoUserName Имя пользователя репозитория
    // @var {String} repoSameName Иия репозитория
    // @var {String} user пользоватль для доступа
    // @var {int}    langId id языка
    // @var {Function} on404 функция для вызова при 404
    this._setRepoSettings = function(chatId, onSuccess, repoUserName, repoSameName, user, password, langId, on404)  {
        var me = this;
        this.__fetchOrCreateUUID(function(isNew, uuid, timestamp) {
            var wrapper = (function(fun) {
                makeRepeatedRequest({
                    "url": "/reviewgram/set_repo_settings/",
                    "dataType": "json",
                    "data": {
                        "chatId" : reviewgram.requestPeerID(chatId),
                        "uuid": uuid,
                        "repoUserName": repoUserName,
                        "repoSameName": repoSameName,
                        "user": user,
                        "password": btoa(password),
                        "langId": langId
                    },
                    "method": "POST",
                    "on404": on404
                }, fun);
            }).bind(null, onSuccess);
            if (isNew) {
                var text = btoa(uuid);
                me.sendMessageToBot(text, wrapper);
            } else {
                wrapper();
            }
        });
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
                this._recorder = new Recorder({"numberOfChannels" : 1, "encoderSampleRate": 48000});
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
            } catch (exc) {
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
                      $(".btn-next-tab").removeAttr("disabled");
                  });
                  $(".btn-next-tab").attr("disabled", "disabled");
                  // TODO: callback here
              }
            }
        });
    };
    this._initSearchHintWidgets = function() {
        var makeSearchSubstringHandler = function(removeSlash, dependentSelector) {
            return function() {
                var a = $(this).val().trim();
                var elements = $(dependentSelector);
                for (var i = 0; i < elements.length; i++) {
                    var element = $(elements[i]);
                    var name = element.attr("data-name");
                    var match = true;
                    if (a.length > 0) {
                        match = (name.indexOf(a) != -1);
                        if (!match) {
                            match = matchesNonExact(a, name, removeSlash);
                        }
                    }
                    if (match) {
                          element.removeClass("hidden").css("display", "block");
                    } else {
                          element.addClass("hidden").css("display", "none");
                    }
                }
          };
        };

        $("body").on("cut paste keyup", "#branchNameSearch", makeSearchSubstringHandler(true, "#branchName ul li"));
        $("body").on("cut paste keyup", "#commitFileSearch", makeSearchSubstringHandler(false, "#commitFile ul li"));
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
        var rangeEnd = this._editorRange.end;
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
                           onSuccess();
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
        var content = b64EncodeUnicode(this._getResultFileContent());
        var tokens = null;
        var me = this;
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
                if ((row == me._mainEditorCursorPosition.row) && (column == me._mainEditorCursorPosition.column)) {
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
    // Удаляет данные токенов при логауте
    this.onLogout = function() {
        localStorage.removeItem("reviewgram_uuid");
        localStorage.removeItem("reviewgram_uuid_timestamp");
    };
    // Инициализирует пространство имён
    this.initScope = function($scope) {
        $scope.reviewgramShowRepoSettings = function() {
            $scope.$broadcast('reviewgram_show_repo_settings')
        }
        $scope.reviewgramShowCommitWindow = function() {
            $scope.$broadcast('reviewgram_show_commit_window')
        }
    };
    // Имена контроллеров
    this.settingsControllerName  = 'ReviewgramRepoSettingsController';
    this.makeCommitControllerName = 'ReviewgramCommitWindowController';
    // Показывает модалку для настроек
    this.showSettingsModal = function() {
        var $scope = this._webogramAdapter.$rootScope.$new();
        this._webogramAdapter.$scope = $scope;
        this._webogramAdapter.$modal.open({
            controller: 'ReviewgramRepoSettingsController',
            templateUrl: templateUrl('reviewgram_repo_settings_all'),
            scope: $scope,
            windowClass: 'reviewgram_repo_settings_all_modal_window mobile_modal'
        });
        var me = this;
        this._getRepoSettings(this.getCurrentDialog(), function(o) {
            $("#repoUserName").val(o.repo_user_name);
            $("#repoSameName").val(o.repo_same_name);
            $("#user").val(o.user);
            $("#password").val(o.password);
            $("#error").css('display', 'none');
            $("#rsettings_preloader").css('display', 'none');
            $("#rsettings_form").css('display', 'block');
            $("#rsettings_error").css('display', 'none');
            $(".md_modal_title, .navbar-quick-media-back h4").html("Настройки интеграции с GitHub");
            $("#langId ul").html("");
            var result = "";
            for (langId in me.langIdsToNames) {
                if (me.langIdsToNames.hasOwnProperty(langId)) {
                    var text = escapeHtml(me.langIdsToNames[langId]);
                    result = result + "<li data-id=\"" + langId + "\">" + text +  "</li>";
                }
            }
            $("#langId ul").html(result);
            $("#langId ul li[data-id=" + langId + "]").addClass("selected");
        }, function() {
            $("#rsettings_preloader").css('display', 'none');
            $("#rsettings_form").css('display', 'none');
            $("#rsettings_error").css('display', 'block');
            $("#rsettings_error").find(".reviewgram-error").html("Не удалось получить настройки репозитория. Проверьте, что вы добавили пользователя <a href=\"https://t.me/reviewgram_bot\">reviewgram_bot</a> в чат, и что вы являетесь членом чата и попробуйте ещё раз.");
            $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
        });
    };
    // Показывает модалку для коммита
    this.showMakeCommitModal = function() {
        var $scope = this._webogramAdapter.$rootScope.$new();
        this._webogramAdapter.$scope = $scope;
        this._webogramAdapter.$modal.open({
            controller: 'ReviewgramCommitWindowController',
            templateUrl: templateUrl('reviewgram_commit_all'),
            scope: $scope,
            windowClass: 'reviewgram_commit_all_modal_window mobile_modal'
        });
    };
    // Инициализирует действия для модальных окон
    this.initModalActions = function($scope, $rootScope, $modal) {
        this._webogramAdapter.$rootScope = $rootScope;
        this._webogramAdapter.$modal = $modal;

        var me = this;
        $scope.$on('reviewgram_show_repo_settings', function() {
            me.showSettingsModal();
        });
        $scope.$on('reviewgram_show_commit_window', function() {
            me.showMakeCommitModal();
        });
    };
    // Контроллер для окна установки и получения настроек
    this.repoSettingsController = function($rootScope, $scope, $modal, AppUsersManager, MtpApiManager, $modalInstance) {
        var me = this;
        $scope.submitForm = function() {
            var repoUserName = $("#repoUserName").val().trim();
            var repoSameName = $("#repoSameName").val().trim();
            var user = $("#user").val().trim();
            var password = $("#password").val().trim();
            var langId = null;
            var errors = [];
            if (repoUserName.length == 0) {
                errors.push("Не указано имя собственника репозитория");
            }
            if (repoSameName.length == 0) {
                errors.push("Не указано имя репозитория");
            }
            if (user.length == 0) {
                errors.push("Не указано имя пользователя");
            }
            if (password.length == 0) {
                errors.push("Не указан пароль");
            }
            if ($("#langId ul li.selected").length != 0) {
                langId = parseInt($("#langId ul li.selected").attr("data-id"));
                if (langId != langId) {
                    errors.push("Не указан язык");
                }
            } else {
                errors.push("Не указан язык");
            }
            if (errors.length != 0) {
                $("#error").css("display", "block").html(errors.join("<br />"));
            } else {
                $("#error").css("display", "none");
                $("#rsettings_preloader").css('display', 'block');
                $("#rsettings_form").css('display', 'none');
                var fun = function(o) {
                  if (o.error.length != 0) {
                      $("#rsettings_preloader").css('display', 'none');
                      $("#rsettings_form").css('display', 'block');
                      $("#error").css("display", "block").html(o.error);
                  } else {
                      $modalInstance.dismiss();
                  }
                };
                var on404 = function() {
                      $("#rsettings_preloader").css('display', 'none');
                      $("#rsettings_form").css('display', 'none');
                      $("#rsettings_error").css('display', 'block');
                      $("#rsettings_error").find(".reviewgram-error").html("Не удалось сохранить настройки репозитория. Проверьте, что вы добавили пользователя <a href=\"https://t.me/reviewgram_bot\">reviewgram_bot</a> в чат и попробуйте ещё раз.");
                      $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                };
                me._setRepoSettings(me.getCurrentDialog(), fun, repoUserName, repoSameName, user, password, langId, on404);
            }
        }
    };
    // Контроллер для окна проведения изменений
    this.makeCommitController = function($rootScope, $scope, $modal, AppUsersManager, AppPeersManager, MtpApiManager, $modalInstance) {
        var me = this;
        $scope.fetchBranchesList = function() {
            $.ajax({
                "method": "GET",
                "dataType": "json",
                "username": me._repoSettings.user,
                "password": me._repoSettings.password,
                "url": "/github_api/repos/" + me._repoSettings.repo_user_name  + "/" + me._repoSettings.repo_same_name + "/branches",
                "success": function(o) {
                    console.log(o);
                    var result = "";
                    for (var  i = 0; i < o.length; i++) {
                        var text = escapeHtml(o[i].name);
                        var branchEscapedName = o[i].name.replace(/\"/g, "&quot;");
                        var commit = o[i].commit.sha;
                        result = result + "<li data-commit=\"" + commit + "\" data-name=\""  + branchEscapedName + "\">" + text +  "</li>";
                    }
                    $(".md_modal_title, .navbar-quick-media-back h4").html("Выберите ветку");
                    $("#rcommit_branch_select #branchName ul").html(result);
                    if (o.length == 1) {
                        $("#rcommit_branch_select #branchName ul li:first").addClass('selected');
                        $scope.submitBranchName();
                        return;
                    }
                    $("#rcommit_preloader").css('display', 'none');
                    $("#rcommit_branch_select").css('display', 'block');
                    $(window).trigger('resize');
                },
                "error": function() {
                    $("#rcommit_preloader").css('display', 'none');
                    $("#rcommit_error").css('display', 'block');
                    $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить список веток. Пожалуйста, попробуйте ещё раз");
                    $("#rcommit_error").find(".buttons").css("display", "block");
                    $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                    $(".btn-repeat").attr("data-invoke", 'fetchBranchesList').removeAttr('data-arg');
                    $(window).trigger('resize');
                }
            });
        };
        $scope.submitBranchName = function() {
            var branchEl = $("#branchName ul li.selected");
            var selectedElement = null;
            if (branchEl.length != 0) {
                if (branchEl.css("display") != "none") {
                    selectedElement = branchEl;
                }
            }
            if (selectedElement == null) {
                  var elements = $("#branchName ul li");
                  // data-commit, data-name;
                  var val = $("#branchNameSearch").val().trim();
                  for (var i = 0; i < elements.length; i++) {
                      if ($(elements[i]).attr("data-name") == val) {
                          selectedElement = $(elements[i]);
                      }
                  }
            }
            if (selectedElement != null) {
                me._branchName = selectedElement.attr("data-name").replace(/&quot;/, "\"");
                me._lastCommit = selectedElement.attr("data-commit");
                $("#rcommit_preloader").css('display', 'block');
                $("#rcommit_branch_select").css('display', 'none');
                $.ajax({
                   	"method": "GET",
                   	"dataType": "json",
                   	"username":  me._repoSettings.user,
                   	"password":  me._repoSettings.password,
                   	"url": "/github_api/repos/" +  me._repoSettings.repo_user_name  + "/" +  me._repoSettings.repo_same_name + "/commits/" + me._lastCommit,
                   	"success": function(o) {
                   		console.log(o);
                   		var error = true;
                        if ('commit' in o) {
                            if ('tree' in o['commit']) {
                                error = false;
                                $scope.fetchFileList(o['commit']['tree']['url'] + "?recursive=y");
                            }
                        }
                        if (error) {
                            $("#rcommit_preloader").css('display', 'none');
                            $("#rcommit_error").css('display', 'block');
                            $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить список файлов из ветки репозитория GitHub. Пожалуйста, проверьте настройки репозитория и попробуйте ещё раз");
                            $("#rcommit_error").find(".buttons").css("display", "none");
                            $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                            $(window).trigger('resize');
                        }
                   	},
                   	"error": function() {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_error").css('display', 'block');
                        $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить список файлов из-за ошибки сети. Попробуйте ещё раз");
                        $("#rcommit_error").find(".buttons").css("display", "block");
                        $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                        $(".btn-repeat").attr("data-invoke", 'submitBranchName').removeAttr('data-arg');
                        $(window).trigger('resize');
                   	}
                   });
            }
        };
        $scope.fetchFileList = function(url) {
            $.ajax({
                "method": "GET",
                "dataType": "json",
                "username":  me._repoSettings.user,
                "password":  me._repoSettings.password,
                "url": url,
                "success": function(o) {
                     console.log(o);
                     var error = true;
                     if ('tree' in o) {
                         error = false;
                         $(".md_modal_title, .navbar-quick-media-back h4").html("Выберите файл для редактирования");
                         var result = "";
                         var cnt =  0;
                         for (var  i = 0; i < o["tree"].length; i++) {
                             var fileData = o["tree"][i];
                             var path = fileData["path"];
                             var url = fileData["url"];
                             var sha =  fileData["sha"];
                             if (me.__isMatchesAllowedExtensions(path) && (fileData["type"] != "tree")) {
                                 var escapedName = path.replace(/\"/g, "&quot;");
                                 var text = escapeHtml(path);
                                 result = result + "<li data-sha=\"" + sha + "\" data-url=\"" + url + "\" data-name=\""  + escapedName + "\">" + text +  "</li>";
                                 ++cnt;
                             }
                         }
                         $("#rcommit_file_select #commitFile ul").html(result);
                         if (cnt == 1) {
                             $("#rcommit_file_select #commitFile ul li:first").addClass('selected');
                             $scope.submitFileName();
                             return;
                         }
                         $("#rcommit_preloader").css('display', 'none');
                         $("#rcommit_file_select").css('display', 'block');
                         $(window).trigger('resize');
                     }
                     if (error) {
                         $("#rcommit_preloader").css('display', 'none');
                         $("#rcommit_error").css('display', 'block');
                         $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить список файлов. Возможно, ветка изменилась или была удалена. Попробуйте ещё раз.");
                         $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                         $("#rcommit_error").find(".buttons").css("display", "none");
                         $(window).trigger('resize');
                     }
                },
                "error": function() {
                     $("#rcommit_preloader").css('display', 'none');
                     $("#rcommit_error").css('display', 'block');
                     $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить список файлов из-за ошибки сети. Пожалуйста,  попробуйте ещё раз");
                     $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                     $("#rcommit_error").find(".buttons").css("display", "block");
                     $(".btn-repeat").attr("data-invoke", 'fetchFileList').attr('data-arg', url);
                     $(window).trigger('resize');
                }
            });
        };
        $scope.submitFileName = function() {
            var branchEl = $("#commitFile ul li.selected");
            var selectedElement = null;
            if (branchEl.length != 0) {
                if (branchEl.css("display") != "none") {
                    selectedElement = branchEl;
                }
            }
            if (selectedElement == null) {
                  var elements = $("#commitFile ul li");
                  // data-commit, data-name;
                  var val = $("#commitFileSearch").val().trim();
                  for (var i = 0; i < elements.length; i++) {
                      if ($(elements[i]).attr("data-name") == val) {
                          selectedElement = $(elements[i]);
                      }
                  }
            }
            if (selectedElement != null) {
                me._editedFile.name = selectedElement.attr("data-name").replace(/&quot;/, "\"");
                me._editedFile.url = selectedElement.attr("data-url");
                me._editedFile.sha = selectedElement.attr("data-sha");
                me._editedFile.langId = me.__fileNameToLangId(me._editedFile.name);
                $("#rcommit_preloader").css('display', 'block');
                $("#rcommit_branch_select").css('display', 'none');
                $("#rcommit_file_select").css('display', 'none');
                $.ajax({
                    "method": "GET",
                    "dataType": "json",
                    "username": me._repoSettings.user,
                    "password": me._repoSettings.password,
                    "url": me._editedFile.url,
                    "success": function(o) {
                        var error = true;
                        if (('content' in o) && ('encoding' in o)) {
                            error = false;
                            $(".md_modal_title, .navbar-quick-media-back h4").html("Выберите промежуток для редактирования");
                            if (o['encoding'] == 'base64') {
                                me._editedFile.content = b64DecodeUnicode(o['content']);
                            } else {
                                me._editedFile.content = o['content']
                            }
                            $("#rcommit_preloader").css('display', 'none');
                            $("#rcommit_range_select").css('display', 'block');
                            $("#rcommit_range_select .editor-wrapper").html("");
                            $("#rcommit_range_select .editor-wrapper").html("<div id=\"editor_range_select\"></div>");
                            $("#rcommit_range_select .editor-wrapper #editor_range_select").html(escapeHtml(me._editedFile.content));
                            me._rangeSelectEditor = ace.edit("editor_range_select");
                            me._rangeSelectEditor.setTheme("ace/theme/solarized_dark");
                            me._rangeSelectEditor.session.setMode(me.__fileNameToAceMode(me._editedFile.name));
                            me._rangeSelectEditor.setReadOnly(true);
                            me._rangeSelectEditor.setValue(me._editedFile.content);
                            me._editorRange.start = null;
                            me._editorRange.end = null;
                            me._editorRange.lastClick = null;
                            $(window).trigger('resize');
                        }
                        if (error) {
                            $("#rcommit_preloader").css('display', 'none');
                            $("#rcommit_error").css('display', 'block');
                            $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить содержимое файла. Возможно, файл изменился или был удалён. Попробуйте ещё раз.");
                            $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                            $("#rcommit_error").find(".buttons").css("display", "none");
                            $(window).trigger('resize');
                        }
                    },
                    "error": function() {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_error").css('display', 'block');
                        $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить содержимое файла из-за ошибки сети. Пожалуйста,  попробуйте ещё раз");
                        $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                        $("#rcommit_error").find(".buttons").css("display", "block");
                        $(".btn-repeat").attr("data-invoke", 'submitFileName').removeAttr('data-arg');
                        $(window).trigger('resize');
                    }
                });
            }
        };
        $scope.submitRange = function() {
             if (me._editorRange.start != null) {
                 var rangeEnd = me._editorRange.end;
                 if (rangeEnd === null) {
                     rangeEnd =  me._editorRange.start;
                 }
                 var separator = null;
                 if (me._editedFile.content.indexOf("\r\n") != -1) {
                     separator = "\r\n";
                 } else {
                     if (me._editedFile.content.indexOf("\r") != -1) {
                         separator = "\r";
                     } else {
                         separator = "\n";
                     }
                 }
                 me._editedFile.lineSeparator = separator;
                 var strings = me._editedFile.content.split(separator).slice(me._editorRange.start - 1, rangeEnd).join("\n");
                 me._editedFile.editedPart = strings;
                 $("#rcommit_range_select").css('display', 'none');
                 $("#rcommit_edit").css('display', 'block');
                 $("#rcommit_edit #edit-syntax-error").html("");
                 $("#rcommit_edit .editor-wrapper").html("");
                 me._isEditRequestRunning = false;
                 $("#rcommit_edit .editor-wrapper").html("<div id=\"editor_edit\"></div>");
                 $("#rcommit_edit .editor-wrapper #editor_edit").html(escapeHtml(me._editedFile.editedPart));
                 $(".md_modal_title, .navbar-quick-media-back h4").html("");
                 me._mainEditor = ace.edit("editor_edit");
                 me._mainEditor.setOption("firstLineNumber", me._editorRange.start);
                 me._mainEditor.setOption("tabSize", 4)
                 me._mainEditor.setTheme("ace/theme/solarized_dark");
                 me._mainEditor.session.setMode(me.__fileNameToAceMode(me._editedFile.name));
                 me._mainEditor.setValue(me._editedFile.editedPart);
                 me._mainEditor.session.selection.on('changeCursor', function(o) {
                     var cursorPosition = me._mainEditor.getCursorPosition();
                     me._mainEditorCursorPosition = cursorPosition;
                     if (me._autocompleteSendTimeoutHandle !== null) {
                         clearTimeout(me._autocompleteSendTimeoutHandle);
                     }
                     me._autocompleteSendTimeoutHandle = setTimeout(function() {
                         me.sendAutocompleteRequest(me._editedFile.langId);
                     }, 5000);
                 });
                 $(".autocompletion .body").html("");
                 $(window).trigger('resize');
             }
        };
        $scope.applyEditCommand = function() {
            var e = $("#editCommand li.selected");
            if (e.length != 0) {
                if (e.hasClass("add-line-to-begin")) {
                    me._mainEditor.session.insert({"row": 0, "column": 0}, $("#commandLine").val() + me._editedFile.lineSeparator);
                    return;
                }
                if (e.hasClass("add-line-to-end")) {
                    var cnt  = me._mainEditor.session.doc.getAllLines().length;
                    me._mainEditor.session.insert({"row": cnt, "column": 0}, me._editedFile.lineSeparator  + $("#commandLine").val());
                    return;
                }
                if (e.hasClass("insert-line")) {
                    var pos = me._mainEditor.getCursorPosition();
                    me._mainEditor.session.insert({"row": pos.row, "column": 0}, $("#commandLine").val() + me._editedFile.lineSeparator);
                    return;
                }
                if (e.hasClass("delete-line")) {
                    var pos = me._mainEditor.getCursorPosition();
                    me._mainEditor.session.doc.removeLines(pos.row, pos.row);
                    return;
                }
                if (e.hasClass("replace-line")) {
                    var pos = me._mainEditor.getCursorPosition();
                    me._mainEditor.session.doc.removeLines(pos.row, pos.row);
                    me._mainEditor.session.insert({"row": pos.row, "column": 0}, $("#commandLine").val() + me._editedFile.lineSeparator);
                    return;
                }
            }
        };
        $scope.insertTab = function() {
            var pos = me._mainEditor.getCursorPosition();
            me._mainEditor.session.insert(pos, "\t");
            me._mainEditor.focus();
        };
        $scope.insertFourSpaces = function() {
            var pos = me._mainEditor.getCursorPosition();
            me._mainEditor.session.insert(pos, "    ");
            me._mainEditor.focus();
        };
        $scope.removeTab = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.column != line.length) {
                if (line[pos.column] == "\t") {
                    me._mainEditor.session.remove({"start": {"row": pos.row, "column": pos.column}, "end": {"row": pos.row, "column": pos.column + 1}});
                    me._mainEditor.focus();
                    return;
                }
            }
            if (pos.column != 0) {
                if (line[pos.column - 1] == "\t") {
                    me._mainEditor.session.remove({"start": {"row": pos.row, "column": pos.column - 1}, "end": {"row": pos.row, "column": pos.column}});
                    me._mainEditor.focus();
                    return;
                }
            }
            var poses = [
                [pos.column, pos.column + 4],
                [pos.column - 4, pos.column],
                [pos.column - 3, pos.column + 1],
                [pos.column - 2, pos.column + 2],
                [pos.column - 1, pos.column + 3]
            ];
            for (var i = 0; i < poses.length; i++) {
                if (line.substring(poses[i][0], poses[i][1]) ==  "    ") {
                    me._mainEditor.session.remove({"start": {"row": pos.row, "column": poses[i][0] }, "end": {"row": pos.row, "column": poses[i][1]}});
                    me._mainEditor.focus();
                    return;
                }
            }
        };
        $scope.removeFourSpaces = function() {
            $scope.removeTab();
        };
        $scope.removePreviousSymbol = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.column != 0) {
                me._mainEditor.session.remove({"start": {"row": pos.row, "column": pos.column - 1}, "end": {"row": pos.row, "column": pos.column}});
                me._mainEditor.focus();
                return;
            }
        };
        $scope.removeNextSymbol = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.column != line.length) {
                me._mainEditor.session.remove({"start": {"row": pos.row, "column": pos.column}, "end": {"row": pos.row, "column": pos.column + 1}});
                me._mainEditor.focus();
                return;
            }
        };
        $scope.removePreviousLexeme = function() {
            try {
                var pos = me._mainEditor.getCursorPosition();
                var lines = me._mainEditor.session.doc.getAllLines();
                var line = lines[pos.row];
                var factory = new TokenizerFactory();
                var tokens = factory.create(me._editedFile.langId).tokenize(line);
                var token = false;
                for (var  i = 0; (i < tokens.length) && (token === false); i++) {
                    if (tokens[i][0] <= pos.column && pos.column <  tokens[i][1]) {
                        token = i;
                    }
                }
                if (token === false) {
                    for (var  i = 0; (i < tokens.length) && (token === false); i++) {
                        if (tokens[i][0] <= pos.column && tokens[i][1] <= pos.column) {
                            token = i;
                        }
                    }
                }
                if (token !== false) {
                    me._mainEditor.session.remove({"start": {"row": pos.row, "column": tokens[token][0]}, "end": {"row": pos.row, "column": tokens[token][1]}});
                    me._mainEditor.focus();
                }
            } catch (exc) {
                console.log(exc);
            }
        };
        $scope.findNextLexeme  = function(pos, tokens) {
            var token = false;
            for (var  i = 0; (i < tokens.length) && (token === false); i++) {
                if (tokens[i][0] <= pos.column && pos.column <  tokens[i][1]) {
                    token = i;
                }
            }
            if (token === false) {
                for (var  i = 0; (i < tokens.length) && (token === false); i++) {
                    if (tokens[i][0] >= pos.column) {
                        token = i;
                    }
                }
            }
            return token;
        };
        $scope.removeNextLexeme = function() {
            try {
                var pos = me._mainEditor.getCursorPosition();
                var lines = me._mainEditor.session.doc.getAllLines();
                var line = lines[pos.row];
                var factory = new TokenizerFactory();
                var tokens = factory.create(me._editedFile.langId).tokenize(line);
                var token = $scope.findNextLexeme(pos, tokens);
                if (token !== false) {
                    me._mainEditor.session.remove({"start": {"row": pos.row, "column": tokens[token][0]}, "end": {"row": pos.row, "column": tokens[token][1]}});
                    me._mainEditor.focus();
                }
            } catch(exc) {
                console.log(exc);
            }
        };
        $scope.moveToNextSymbol = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.column != line.length) {
                me._mainEditor.gotoLine(pos.row + 1, pos.column + 1);
            } else {
                if (pos.row < line.length - 1) {
                    me._mainEditor.gotoLine(pos.row + 2, 0);
                }
            }
            me._mainEditor.focus();
        };
        $scope.moveToPreviousSymbol = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.column != 0) {
                me._mainEditor.gotoLine(pos.row + 1, pos.column - 1);
            } else {
                if (pos.row > 0) {
                    line = lines[pos.row - 1];
                    me._mainEditor.gotoLine(pos.row, line.length);
                }
            }
            me._mainEditor.focus();
        };
        $scope.moveToPrevRow = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.row > 0) {
                me._mainEditor.gotoLine(pos.row, pos.column);
            }
            me._mainEditor.focus();
        };
        $scope.moveToNextRow = function() {
            var pos = me._mainEditor.getCursorPosition();
            var lines = me._mainEditor.session.doc.getAllLines();
            var line = lines[pos.row];
            if (pos.row < lines.length) {
                me._mainEditor.gotoLine(pos.row + 2, pos.column);
            }
            me._mainEditor.focus();
        };
        $scope.moveToBeginOfNextLexeme = function() {
            try {
                var pos = me._mainEditor.getCursorPosition();
                var lines = me._mainEditor.session.doc.getAllLines();
                var line = lines[pos.row];
                var factory = new TokenizerFactory();
                var tokens = factory.create(me._editedFile.langId).tokenize(line);
                var token = $scope.findNextLexeme(pos, tokens);
                if (token !== false) {
                    me._mainEditor.gotoLine(pos.row + 1, tokens[token][0]);
                    me._mainEditor.focus();
                }
            } catch (exc) {
                console.log(exc);
            }
        };
        $scope.moveToEndOfNextLexeme = function() {
            try {
                var pos = me._mainEditor.getCursorPosition();
                var lines = me._mainEditor.session.doc.getAllLines();
                var line = lines[pos.row];
                var factory = new TokenizerFactory();
                var tokens = factory.create(me._editedFile.langId).tokenize(line);
                var token = $scope.findNextLexeme(pos, tokens);
                if (token !== false) {
                    me._mainEditor.gotoLine(pos.row + 1, tokens[token][1]);
                    me._mainEditor.focus();
                }
            } catch (exc) {
                console.log(exc);
            }
        };
        $scope.moveToMiddleOfNextLexeme = function() {
            try {
                var pos = me._mainEditor.getCursorPosition();
                var lines = me._mainEditor.session.doc.getAllLines();
                var line = lines[pos.row];
                var factory = new TokenizerFactory();
                var tokens = factory.create(me._editedFile.langId).tokenize(line);
                var token = $scope.findNextLexeme(pos, tokens);
                if (token !== false) {
                    me._mainEditor.gotoLine(pos.row + 1, parseInt((tokens[token][1] + tokens[token][0]) / 2));
                    me._mainEditor.focus();
                }
            } catch (exc) {
                console.log(exc);
            }
        };
        $scope.submitEdit = function() {
            if (me._isEditRequestRunning) {
                return;
            }
            me._isEditRequestRunning = true;
            me._getResultFileContent();
            $("#rcommit_edit #edit-syntax-error").html("");
            $("#rcommit_edit").css("display", "none");
            $("#rcommit_preloader").css('display', 'block');
            $scope.performSyntaxCheck();
        };
       $scope.performSyntaxCheck = function() {
           var rangeEnd = me._editorRange.end;
           if (rangeEnd == null) {
               rangeEnd = me._editorRange.start;
           }
           $.ajax({
               "method": "POST",
               "dataType": "json",
               "url": "/reviewgram/check_syntax/",
               'contentType': 'application/json',
               "data": JSON.stringify({
                   "filename": me._editedFile.name,
                   "content": b64EncodeUnicode(me._resultFileContent),
                   "start":  me._editorRange.start,
                   "end": rangeEnd,
                   "langId": me._editedFile.langId
               }),
               "success": function(o) {
                   me._isEditRequestRunning = false;
                   var error = true;
                   if ('errors' in o) {
                       error = false;
                       var text = escapeHtml(b64DecodeUnicode(o["errors"]));
                       if (text.trim().length == 0) {
                           $("#rcommit_edit #edit-syntax-error").html("");
                           $("#rcommit_preloader").css('display', 'none');
                           $("#rcommit_edit").css('display', 'none');
                           $("#rcommit_confirm").css('display', 'block');
                           $("#rcommit_confirm_apply").css('display', 'block');
                           $("#rcommit_confirm_error").css('display', 'none');
                           $(".md_modal_title, .navbar-quick-media-back h4").html("Подтверждение");
                           $(window).trigger('resize');
                       } else {
                           text = text.replace(/[\n]/g, "<br>")
                           $("#rcommit_preloader").css('display', 'none');
                           $("#rcommit_edit").css('display', 'block');
                           var errorWrap = "<div class=\"edit-tab-container selected\">";
                           errorWrap += "<div class=\"header\">";
                           errorWrap += "<div class=\"section-arrow toggled arrow-down\"></div>";
                           errorWrap += "Ошибка";
                           errorWrap += "</div>";
                           errorWrap += "<div class=\"reviewgram-error body\">";
                           errorWrap += "Синтаксическая ошибка! При проверке, обнаружены следующие ошибки ниже:<br>" + text;
                           errorWrap += "</div>";
                           errorWrap += "</div>";
                           $("#rcommit_edit #edit-syntax-error").html(errorWrap);
                           $(window).trigger('resize');
                       }
                   }
                   if (error) {
                       $("#rcommit_preloader").css('display', 'none');
                       $("#rcommit_error").css('display', 'block');
                       $("#rcommit_error").find(".reviewgram-error").html("Не удалось проверить синтаксис файла. Попробуйте ещё раз провести правку.");
                       $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                       $("#rcommit_error").find(".buttons").css("display", "none");
                       $(window).trigger('resize');
                   }
               },
               "error": function(xhr) {
                   if (xhr.status == "404" || xhr.status == "403" || xhr.status == "401") {
                       $("#rcommit_preloader").css('display', 'none');
                       $("#rcommit_error").css('display', 'block');
                       $("#rcommit_error").find(".reviewgram-error").html("Не удалось проверить синтаксис файла. Попробуйте ещё раз провести правку.");
                       $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                       $("#rcommit_error").find(".buttons").css("display", "none");
                       $(window).trigger('resize');
                   } else {
                       setTimeout(function() {
                         $scope.performSyntaxCheck();
                       }, 5000);
                   }
               }
           });
       };
        $scope.showConfirmationModal = function() {
            $("#rcommit_edit").css('display', 'none');
            $("#rcommit_confirm").css('display', 'block');
            $("#rcommit_confirm_apply").css('display', 'block');
            $("#rcommit_confirm_error").css('display', 'none');
            $(".md_modal_title, .navbar-quick-media-back h4").html("Подтверждение");
            $(window).trigger('resize');
            me._isEditRequestRunning = false;
        };
        $scope.submitConfirmation = function() {
            $("#rcommit_confirm").css('display', 'none');
            $("#rcommit_preloader").css('display', 'block');
            $scope.checkIfCommitInRepoIsLatest(1);
        };
        $scope.checkIfCommitInRepoIsLatest = function(step) {
            $.ajax({
                "method": "GET",
                "dataType": "json",
                "username": me._repoSettings.user,
                "password": me._repoSettings.password,
                "url": "/github_api/repos/" + me._repoSettings.repo_user_name  + "/" + me._repoSettings.repo_same_name + "/branches/" + encodeURIComponent(me._branchName),
                "success": function(o) {
                    var error = true;
                    if ('commit' in o) {
                        if ('sha' in o['commit']) {
                            error = false;
                            var newLastCommit = o['commit']['sha'];
                            if (me._lastCommit == newLastCommit) {
                                if (step == 1) {
                                    //$scope.$dismiss();
                                     $scope.tryLock();
                                }
                                if (step == 2) {
                                     $scope.performEdit();
                                }
                            } else {
                                $("#rcommit_preloader").css('display', 'none');
                                $("#rcommit_confirm").css('display', 'block');
                                $("#rcommit_confirm_apply").css('display', 'none');
                                $("#rcommit_confirm_error").css('display', 'block');
                                $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! В репозиторий уже были внесены изменения. Проверье, что ваши изменения корректны и попробуйте ещё раз.");
                            }
                        }
                    }
                    if (error) {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_confirm").css('display', 'block');
                        $("#rcommit_confirm_apply").css('display', 'none');
                        $("#rcommit_confirm_error").css('display', 'block');
                        $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! Не удалось получить получить актуальные данные из репозитория. Проверьте данные репозитория и попробуйте позже.");
                    }
                },
                "error": function(xhr) {
                    if (xhr.status == "404" || xhr.status == "403" || xhr.status == "401") {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_confirm").css('display', 'block');
                        $("#rcommit_confirm_apply").css('display', 'none');
                        $("#rcommit_confirm_error").css('display', 'block');
                        $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! Не удалось получить актуальные данные из репозитория. Проверьте данные репозитория и попробуйте позже.");
                    } else {
                        setTimeout(function() {
                          $scope.checkIfCommitInRepoIsLatest(step);
                        }, 5000);
                    }
                }
            });
        };
        $scope.tryLock = function() {
            me.__fetchOrCreateUUID(function(isNew, uuid, timestamp) {
                 $scope.tryPerformLock(uuid);
            });
        };
        $scope.tryPerformLock = function(uuid) {
            $.ajax({
                "method": "GET",
                "dataType": "json",
                "username": me._repoSettings.user,
                "password": me._repoSettings.password,
                "data": {
                    "chatId" : me.getCurrentDialogPeerID(),
                    "uuid": uuid,
                },
                "url": "/reviewgram/try_lock/",
                "success": function(o) {
                    var error = true;
                    if ('locked' in o) {
                        error = false;
                        if (o['locked']) {
                            setTimeout(function() {
                              $scope.tryLock();
                            }, 5000);
                        } else {
                            $scope.checkIfCommitInRepoIsLatest(2);
                        }
                    }
                    if (error) {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_confirm").css('display', 'block');
                        $("#rcommit_confirm_apply").css('display', 'none');
                        $("#rcommit_confirm_error").css('display', 'block');
                        $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! Не удалось заблокировать репозиторий. Проверьте данные репозитория и попробуйте позже.");
                    }
                },
                "error": function(xhr) {
                    if (xhr.status == "404" || xhr.status == "403" || xhr.status == "401") {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_confirm").css('display', 'block');
                        $("#rcommit_confirm_apply").css('display', 'none');
                        $("#rcommit_confirm_error").css('display', 'block');
                        $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! Не удалось заблокировать репозиторий. Проверьте данные репозитория и попробуйте позже.");
                    } else {
                        setTimeout(function() {
                          $scope.tryLock();
                        }, 5000);
                    }
                }
            });
        };
        $scope.performEdit = function() {
            $.ajax({
                "method": "PUT",
                "dataType": "json",
                "username": me._repoSettings.user,
                "password": me._repoSettings.password,
                "url": "/github_api/repos/" + me._repoSettings.repo_user_name  + "/" + me._repoSettings.repo_same_name + "/contents/" + encodeURIComponent(me._editedFile.name),
                'contentType': 'application/json',
                "data": JSON.stringify({
                    "message": "Быстрое исправление через Reviewgram",
                    "content": b64EncodeUnicode(me._resultFileContent),
                    "sha": me._editedFile.sha
                }),
                "success": function(o) {
                    var error = true;
                    if ('commit' in o) {
                        if ('url' in o['commit']) {
                            error = false;
                            var resultUrl = o['commit']['url'];
                            resultUrl = resultUrl.replace("api.", "").replace("/repos/", "/").replace("git/commits", "commit");
                            var sentRequestOptions = {};
                            var repoUrl = "https://github.com/" + me._repoSettings.repo_user_name  + "/" + me._repoSettings.repo_same_name + "/";
                            var text = " отправил правку " + resultUrl + " в репозиторий " + repoUrl;
                            var apiPromise = MtpApiManager.invokeApi('messages.sendMessage', {
                              flags: 128,
                              peer: AppPeersManager.getInputPeerByID(AppPeersManager.getPeerID(me.getCurrentDialog())),
                              message: text,
                              random_id: [nextRandomInt(0xFFFFFFFF), nextRandomInt(0xFFFFFFFF)],
                              reply_to_msg_id: 0,
                              entities: []
                            }, sentRequestOptions);
                            $scope.$dismiss();
                        }
                    }
                    if (error) {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_confirm").css('display', 'block');
                        $("#rcommit_confirm_apply").css('display', 'none');
                        $("#rcommit_confirm_error").css('display', 'block');
                        $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! Не удалось изменить файл. Проверьте данные репозитория и попробуйте позже.");
                    }
                },
                "error": function(xhr) {
                    if (xhr.status == "404" || xhr.status == "403" || xhr.status == "401") {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_confirm").css('display', 'block');
                        $("#rcommit_confirm_apply").css('display', 'none');
                        $("#rcommit_confirm_error").css('display', 'block');
                        $("#rcommit_confirm_error .reviewgram-error").html("Ошибка! Не удалось изменить файл. Проверьте данные репозитория и попробуйте позже.");
                    } else {
                        setTimeout(function() {
                          $scope.performEdit();
                        }, 5000);
                    }
                }
            });
        };
        $scope.back = function() {
            if ($("#rcommit_file_select").css('display') != 'none') {
                $("#rcommit_preloader").css('display', 'block');
                $("#rcommit_file_select").css('display', 'none');
                $.ajax({
                    "method": "GET",
                    "dataType": "json",
                    "username": me._repoSettings.user,
                    "password": me._repoSettings.password,
                    "url": "/github_api/repos/" + me._repoSettings.repo_user_name  + "/" + me._repoSettings.repo_same_name + "/branches",
                    "success": function(o) {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_branch_select").css('display', 'block');
                        $(".md_modal_title, .navbar-quick-media-back h4").html("Выберите ветку");
                        var result = "";
                        for (var  i = 0; i < o.length; i++) {
                            var text = escapeHtml(o[i].name);
                            var branchEscapedName = o[i].name.replace(/\"/g, "&quot;");
                            var commit = o[i].commit.sha;
                            result = result + "<li data-commit=\"" + commit + "\" data-name=\""  + branchEscapedName + "\">" + text +  "</li>";
                        }
                        $("#rcommit_branch_select #branchName ul").html(result);
                    },
                    "error": function() {
                        $("#rcommit_preloader").css('display', 'none');
                        $("#rcommit_error").css('display', 'block');
                        $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить список веток из-за ошибки сети. Пожалуйста, проверьте настройки репозитория.");
                        $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                        $("#rcommit_error").find(".buttons").css("display", "block");
                    }
                });

                return;
            }
            if ($("#rcommit_range_select").css('display') != 'none') {
                $(".md_modal_title, .navbar-quick-media-back h4").html("Выберите файл для редактирования");
                $("#rcommit_file_select").css('display', 'block');
                $("#rcommit_range_select").css('display', 'none');
                $(window).trigger('resize');
                return;
            }
            if ($("#rcommit_edit").css('display') != 'none') {
                $("#rcommit_range_select").css('display', 'block');
                $("#rcommit_edit").css('display', 'none');
                $(".md_modal_title, .navbar-quick-media-back h4").html("Выберите промежуток для редактирования");
                $(window).trigger('resize');
            }
            if ($("#rcommit_confirm").css('display') != 'none') {
                $("#rcommit_edit").css('display', 'block');
                $("#rcommit_edit #edit-syntax-error").html("");
                $("#rcommit_confirm").css('display', 'none');
                $(".md_modal_title, .navbar-quick-media-back h4").html("");
                me._isEditRequestRunning = false;
                $(window).trigger('resize');
            }
        }
        $scope.repeat = function() {
              $("#rcommit_error").css("display", "none");
              $("#rcommit_preloader").css("display", "block");
              $("#rcommit_error").find(".buttons").css("display", "none");
              var fn   = $(".btn-repeat").attr("data-invoke");
              var farg = $(".btn-repeat").attr("data-arg");
              if ((typeof farg != "undefined") && (farg != null)) {
                  $scope[fn](farg);
              } else {
                  $scope[fn]();
              }
        };
        $scope.backToBranchSelect = function() {
            $("#rcommit_preloader").css('display', 'block');
            $("#rcommit_confirm").css('display', 'none');
            $scope.fetchBranchesList();
        };
        setTimeout(function() {
            me._getRepoSettings(me.getCurrentDialog(), function(o) {
                me._initMicrophoneWidgets();
                me._repoSettings = o;
                if (o.repo_user_name.length == 0 || o.repo_same_name.length == 0 || o.user == 0 || o.password == 0) {
                    $("#rcommit_preloader").css('display', 'none');
                    $("#rcommit_error").css('display', 'block');
                    $("#rcommit_error").find(".reviewgram-error").html("Не указаны параметры репозитория. Пожалуйста, настройте их");
                    $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
                } else {
                    $scope.fetchBranchesList();
                }
            }, function() {
                $("#rcommit_preloader").css('display', 'none');
                $("#rcommit_form").css('display', 'none');
                $("#rcommit_error").css('display', 'block');
                $("#rcommit_error").find(".reviewgram-error").html("Не удалось получить настройки репозитория. Проверьте, что вы добавили пользователя <a href=\"https://t.me/reviewgram_bot\">reviewgram_bot</a> в чат, и что вы являетесь членом чата и попробуйте ещё раз.");
                $("#rcommit_error").find(".buttons").css('display', 'none');
                $(".md_modal_title, .navbar-quick-media-back h4").html("Ошибка");
            });
        }, 500);
    };
}
