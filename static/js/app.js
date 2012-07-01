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

            data.forEach(function(key) {
                self.pushObject(Redbeard.Key.create(key));
            });
        });
    }
});

Redbeard.keyView = Ember.View.extend({
    template: Ember.Handlebars.compile("<li>balls</li>"),

    click: function() {
        alert("here");
    }
});
