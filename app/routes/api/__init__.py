from app.routes.api import auth, catalog, inventory, pdv, quotes, orders, purchasing, finance, logistics


def register_api(app):
    app.register_blueprint(auth.bp)
    app.register_blueprint(catalog.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(pdv.bp)
    app.register_blueprint(quotes.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(purchasing.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(logistics.bp)
