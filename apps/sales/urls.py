from extensions.routers import *
from apps.sales.views import *


router = BaseRouter()
router.register('sales_orders', SalesOrderViewSet, 'sales_order')
router.register('sales_return_orders', SalesReturnOrderViewSet, 'sales_return_order')
router.register('sales_tasks', SalesTaskViewSet, 'sales_task')
urlpatterns = router.urls
