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

Redbeard.keyDetailController = Ember.ArrayController.create({
    content: [],
    key_name: '',

    addKey: function(key) {
        var self = this,
            key_name = key.context.get("id");
        self.set("content", []);

        url = "/keys/%@".fmt(key_name);
        $.getJSON(url, function(data) {
            data.forEach(function(key) {
                self.pushObject(Redbeard.Key.create(key));
            });
        });
    },
    removeKey: function(view) {
        this.removeObject(view.context);
    }
});

Redbeard.keyDetailView = Ember.View.extend({

});

Redbeard.keyView = Ember.View.extend({
    click: function() {
        
    }
});

Redbeard.keysController.loadKeys();