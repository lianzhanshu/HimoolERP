from extensions.permissions import ModelPermission


class PurchaseReportPermission(ModelPermission):
    code = 'purchase_report'


class SalesReportPermission(ModelPermission):
    code = 'sales_report'


class SalesHotGoodsPermission(ModelPermission):
    code = 'sales_hot_goods'


class SalesTrendPermission(ModelPermission):
    code = 'sales_trend'


class ProfitTrendPermission(ModelPermission):
    code = 'profit_trend'


__all__ = [
    'PurchaseReportPermission', 'SalesReportPermission',
    'SalesHotGoodsPermission', 'SalesTrendPermission',
    'ProfitTrendPermission',
]
