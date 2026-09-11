from app.routes.api import auth, catalog, inventory, pdv


def register_api(app):
    app.register_blueprint(auth.bp)
    app.register_blueprint(catalog.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(pdv.bp)
