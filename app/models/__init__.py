"""Importa todos os modelos para que o Alembic (flask db migrate) os detecte."""
from app.models.user import User, UserPermissionOverride  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.catalog import Product, UnitConversion  # noqa: F401
from app.models.inventory import StockLocation, Lot, StockBalance, StockMovement  # noqa: F401
from app.models.sales import (  # noqa: F401
    CashSession,
    Sale,
    SaleItem,
    Payment,
    Quote,
    QuoteItem,
    Order,
    OrderItem,
)
from app.models.purchasing import (  # noqa: F401
    Supplier,
    PurchaseQuoteRequest,
    SupplierOffer,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
)
from app.models.finance import Payable, PayableSettlement  # noqa: F401
from app.models.logistics import (  # noqa: F401
    Carrier,
    Vehicle,
    Driver,
    Delivery,
    DeliveryOccurrence,
)
