from extensions.permissions import *
from extensions.exceptions import *
from extensions.viewsets import *
from apps.stock_transfer.serializers import *
from apps.stock_transfer.permissions import *
from apps.stock_transfer.filters import *
from apps.stock_transfer.schemas import *
from apps.stock_transfer.models import *
from apps.goods.models import *
from apps.flow.models import *
from apps.stock_in.models import *
from apps.stock_out.models import *


class StockTransferOrderViewSet(BaseViewSet, ListModelMixin, RetrieveModelMixin, CreateModelMixin):
    """调拨单据"""

    serializer_class = StockTransferOrderSerializer
    permission_classes = [IsAuthenticated, StockTransferPermission]
    filterset_class = StockTransferOrderFilter
    search_fields = ['number', 'remark']
    ordering_fields = ['id', 'number', 'total_quantity', 'create_time']
    select_related_fields = ['out_warehouse', 'in_warehouse', 'handler', 'stock_out_order',
                             'stock_in_order', 'creator']
    prefetch_related_fields = ['stock_transfer_goods_set', 'stock_transfer_goods_set__goods',
                               'stock_transfer_goods_set__goods__unit']
    queryset = StockTransferOrder.objects.all()

    @transaction.atomic
    def perform_create(self, serializer):
        stock_transfer_order = serializer.save()

        # 创建出库单据
        if not stock_transfer_order.enable_auto_stock_out:
            stock_out_order_number = StockOutOrder.get_number(team=self.team)
            stock_out_order = StockOutOrder.objects.create(
                number=stock_out_order_number, warehouse=stock_transfer_order.out_warehouse,
                type=StockOutOrder.Type.STOCK_TRANSFER, stock_transfer_order=stock_transfer_order,
                total_quantity=stock_transfer_order.total_quantity,
                remain_quantity=stock_transfer_order.total_quantity,
                creator=self.user, team=self.team
            )

        # 创建入库单据
        if not stock_transfer_order.enable_auto_stock_in:
            stock_in_order_number = StockInOrder.get_number(team=self.team)
            stock_in_order = StockInOrder.objects.create(
                number=stock_in_order_number, warehouse=stock_transfer_order.in_warehouse,
                type=StockInOrder.Type.STOCK_TRANSFER, stock_transfer_order=stock_transfer_order,
                total_quantity=stock_transfer_order.total_quantity,
                remain_quantity=stock_transfer_order.total_quantity,
                creator=self.user, team=self.team
            )

        inventory_flows = []
        stock_out_goods_set = []
        stock_in_goods_set = []
        for stock_transfer_goods in stock_transfer_order.stock_transfer_goods_set.all():
            if stock_transfer_order.enable_auto_stock_out:
                # 同步库存, 流水
                inventory = Inventory.objects.get(warehouse=stock_transfer_order.out_warehouse,
                                                  goods=stock_transfer_order.goods, team=self.team)
                quantity_before = inventory.total_quantity
                quantity_change = stock_transfer_goods.stock_transfer_quantity
                quantity_after = NP.minus(quantity_before, quantity_change)

                inventory_flows.append(InventoryFlow(
                    warehouse=stock_transfer_order.out_warehouse, goods=stock_transfer_order.goods,
                    type=InventoryFlow.Type.STOCK_TRANSFER_OUT, quantity_before=quantity_before,
                    quantity_change=quantity_change, quantity_after=quantity_after,
                    stock_transfer_order=stock_transfer_order, creator=self.user, team=self.team
                ))

                inventory.total_quantity = quantity_after
                inventory.save(update_fields=['total_quantity'])
            else:
                # 创建出库商品
                stock_out_goods_set.append(StockOutGoods(
                    stock_out_order=stock_out_order, goods=stock_transfer_order.goods,
                    stock_out_quantity=stock_transfer_goods.stock_transfer_quantity,
                    remain_quantity=stock_transfer_goods.stock_transfer_quantity, team=self.team
                ))

            if stock_transfer_order.enable_auto_stock_in:
                # 同步库存, 流水
                inventory = Inventory.objects.get(warehouse=stock_transfer_order.in_warehouse,
                                                  goods=stock_transfer_order.goods, team=self.team)
                quantity_before = inventory.total_quantity
                quantity_change = stock_transfer_goods.stock_transfer_quantity
                quantity_after = NP.plus(quantity_before, quantity_change)

                inventory_flows.append(InventoryFlow(
                    warehouse=stock_transfer_order.in_warehouse, goods=stock_transfer_order.goods,
                    type=InventoryFlow.Type.STOCK_TRANSFER_IN, quantity_before=quantity_before,
                    quantity_change=quantity_change, quantity_after=quantity_after,
                    stock_transfer_order=stock_transfer_order, creator=self.user, team=self.team
                ))

                inventory.total_quantity = quantity_after
                inventory.save(update_fields=['total_quantity'])
            else:
                # 创建入库商品
                stock_in_goods_set.append(StockInGoods(
                    stock_in_order=stock_in_order, goods=stock_transfer_order.goods,
                    stock_in_quantity=stock_transfer_goods.stock_transfer_quantity,
                    remain_quantity=stock_transfer_goods.stock_transfer_quantity, team=self.team
                ))
        else:
            InventoryFlow.objects.bulk_create(inventory_flows)
            StockOutGoods.objects.bulk_create(stock_out_goods_set)
            StockInGoods.objects.bulk_create(stock_in_goods_set)

    @extend_schema(responses={200: NumberResponse})
    @action(detail=False, methods=['get'])
    def number(self, request, *args, **kwargs):
        """获取编号"""

        number = StockTransferOrder.get_number(self.team)
        return Response(data={'number': number}, status=status.HTTP_200_OK)

    @transaction.atomic
    @extend_schema(request=None, responses={200: StockTransferOrderSerializer})
    @action(detail=True, methods=['post'])
    def void(self, request, *args, **kwargs):
        """作废"""


__all__ = [
    'StockTransferOrderViewSet',
]
