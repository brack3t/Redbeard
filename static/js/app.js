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

Redbeard.FilterSelectField = Ember.Select.extend({
    content: Ember.A([
        {type: "all", label: "All"},
        {type: "hash", label: "Hashes"},
        {type: "list", label: "Lists"},
        {type: "set", label: "Sets"},
        {type: "string", label: "Strings"},
        {type: "zset", label: "ZSets"}
    ]),
    optionLabelPath: "content.label",
    optionValuePath: "content.type"
});

Redbeard.keysController = Ember.ArrayController.create({
    content: [],
    key_name: '',
    query: '',
    type_filter: '',
    total_content: [],

    filter_type: function() {
        var self = this,
            type_filter = self.get("type_filter");

        if (type_filter !== null && type_filter.type !== "all") {
            self.set("content", self.total_content);
            var real_type_filter = type_filter.type,
                content = self.get("content");

            new_content = _.filter(content, function(key) {
                return key.type === real_type_filter;
            });
            self.set("content", new_content);
        } else {
            self.loadKeys();
        }

    }.observes("type_filter"),

    filter: function() {
        var self = this,
            query = self.get("query");

        self.set("key_name", query);

        self.loadKeys(query);
    }.observes("query"),

    loadKeys: function() {
        var self = this,
            key_name = self.get("key_name"),
            url;

        if (key_name.length > 0) {
            url = "/keys/%@".fmt(self.get("key_name"));
        } else {
            url = "/keys";
        }
        $.getJSON(url, function(data) {
            self.set("content", []);

            data.forEach(function(key) {
                self.pushObject(Redbeard.Key.create(key));
            });
            self.set("total_content", self.content);
        });
    }
});

Redbeard.keyDetailController = Ember.ArrayController.create({
    content: [],
    key_name: '',
    detail_url: "/keys/%@",

    addKey: function(key) {
        var self = this,
            key_name = key.context.get("id");
        self.set("content", []);

        url = self.detail_url.fmt(key_name);
        $.getJSON(url, function(data) {
            data.forEach(function(key) {
                self.pushObject(Redbeard.Key.create(key));
            });
        });
    },
    editKey: function(key) {
        var self = this,
            key_name = key.context.get("id");
        self.set("content", []);

        url = self.detail_url.fmt(key_name);
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
    templateName: "key-detail"
});
Redbeard.keyEditView = Ember.View.extend({});

Redbeard.keyView = Ember.View.extend({});

Redbeard.keysController.loadKeys();