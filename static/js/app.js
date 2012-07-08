App = Ember.Application.create();

// Model
App.Key = Ember.Object.extend({
    id: null,
    type: null,
    value: null
});

// Controllers
App.keysController = Ember.ArrayController.create({
    content: [],

    add: function(key) {
        this.insertAt(0, key);
    },

    remove: function(key) {
        this.removeObject(key);
    },

    newKey: function() {
        var id = Math.floor(math.random()*Math.PI),
            type = Math.random();

        this.add(App.Key.create({
            id: id,
            type: type,
            value: ''
        }));
    },

    loadKeys: function() {
        var self = this;

        $.getJSON("/api/keys", function(data) {
            var keys = data;
            keys = keys.map(function(item) {
                return self.createKeyFromJSON(item);
            });

            self.set("content", keys);
        });
    },

    htmlDecode: function(value) {
        return $("<div/>").html(value).text();
    },

    createKeyFromJSON: function(json) {
        json.value = this.htmlDecode(json.value);

        return App.Key.create(json);
    },

    saveKey: function() {
        var self = this,
            found_key = App.selectedKeyController.get("content");

        var submit = $.ajax({
            url: "/api/keys/%@".fmt(found_key.id),
            type: "PUT",
            dataType: "json",
            data: {
                "id": found_key.id,
                "type": found_key.type,
                "value": found_key.value
            }
        });
        submit.done(function(data, jqXHR, textStatus) {
            console.log(data);
        });
        submit.fail(function(data, jqXHR, textStatus) {
            console.log(data);
        });
    }
});

App.keysController.loadKeys();

App.selectedKeyController = Ember.Object.create({
    content: null
});

App.EditField = Ember.View.extend({
    tagName: "span",
    templateName: "key-edit",

    doubleClick: function() {
        this.set("isEditing", true);
        return false;
    },

    touchEnd: function() {
        var touchTime = new Date();
        if (this._lastTouchTime && touchTime - this._lastTouchTime < 250) {
            this.doubleClick();
            this._lastTouchTime = null;
        } else {
            this._lastTouchTime = touchTime;
        }

        return false; // Prevent zooming
    },

    focusOut: function() {
        this.set("isEditing", false);
    },

    keyUp: function(evt) {
        if (evt.keyCode === 13) {
            this.set("isEditing", false);
        }
    }
});

App.TextField = Ember.TextField.extend({
    didInsertElement: function() {
        this.$().focus();
    }
});

App.TextArea = Ember.TextArea.extend({
    didInsertElement: function() {
        this.$().focus();
    }
});

Ember.Handlebars.registerHelper("editable", function(path, options) {
    options.hash.valueBinding = path;
    return Ember.Handlebars.helpers.view.call(this, App.EditField, options);
});

Ember.Handlebars.registerHelper("button", function(options) {
    var hash = options.hash;

    if (!hash.target) {
        hash.target = "App.keysController";
    }
    return Ember.Handlebars.helpers.view.call(this, Ember.Button, options);
});

App.KeyListView = Ember.View.extend({
    classNameBindings: ["isSelected"],

    click: function() {
        var content = this.get("content");

        App.selectedKeyController.set("content", content);
    },

    touchEnd: function() {
        this.click();
    },

    isSelected: function() {
        var selectedItem = App.selectedKeyController.get("content"),
            content = this.get("content");

        if (content === selectedItem) { return true; }
    }.property("App.selectedKeyController.content")
});

App.KeyView = Ember.View.extend({
    contentBinding: "App.selectedKeyController.content",
    classNames: ["key"]
});