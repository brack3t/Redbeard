Redbeard = Ember.Application.create();

Redbeard.Key = Ember.Object.extend({
    type: null,
    id: null,
    value: null
});

Redbeard.SearchTextField = Ember.TextField.extend({
    insertNewLine: function() {
        Redbeard.keysController.loadKeys();
    }
});

Redbeard.keysController = Ember.ArrayController.create({
    content: [],
    key_name: '',

    loadKeys: function() {
        var self = this,
            key_name = self.get("key_name"),
            url;

        if (key_name) {
            url = "/keys/%@".fmt(self.get("key_name"));
        } else {
            url = "/keys";
        }
        $.getJSON(url, function(data) {
            self.set("content", []);

            $(data).each(function(index, value) {
                self.pushObject(Redbeard.Key.create(value));
            });
        });
    }
});

Redbeard.keysView = Ember.CollectionView.extend({
    content: [],

    init: function() {
        var self = this;
        $.getJSON("/keys", function(data) {
            keys = [];
            data.forEach(function(key) {
                keys.push(Redbeard.Key.create(key));
            });
            self.set("content", keys);
        });
    },

    itemViewClass: Ember.View.extend({
        template: Ember.Handlebars.compile("<li>{{content.id}}</li>")
    })
});