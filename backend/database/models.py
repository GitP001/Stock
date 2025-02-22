from .connect import db

class StockNews(db.Model):
    __tablename__ = 'stock_news'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    title = db.Column(db.String(255))
    snippet = db.Column(db.Text)
    source = db.Column(db.String(255))
    published_at = db.Column(db.String(50))

    def __init__(self, symbol, title, snippet, source, published_at):
        self.symbol = symbol
        self.title = title
        self.snippet = snippet
        self.source = source
        self.published_at = published_at