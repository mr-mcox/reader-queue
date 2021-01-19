class AssetPresenter:
    def __init__(self, asset):
        self.asset = asset

    @property
    def url(self):
        return self.asset.url

    @property
    def title(self):
        biblio_title = self.asset.biblio.get("title")
        if biblio_title:
            return biblio_title
        return self.asset.title

    @property
    def id(self):
        return self.asset.id

    @property
    def has_image(self):
        return self.image is not None and len(self.image) > 0

    @property
    def image(self):
        return self.asset.biblio.get("top_image")

    @property
    def description(self):
        if self.asset.description is not None and len(self.asset.description) > 0:
            return self.asset.description
        else:
            return self.asset.biblio.get("summary")

    @property
    def reading_time(self):
        n_words = self.asset.biblio.get("n_words")
        if n_words:
            return f"Reading time: {n_words / 200:0.1f} min"
        else:
            return None
