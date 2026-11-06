
SELECT bom.parent_item, item.Description, item.cost, bom.ITEM_TYPE, SUM(bom.quantity) as Cantidad
FROM bom
INNER JOIN Item ON bom.PARENT_ITEM = item.Item_Code
WHERE bom.ITEM_TYPE = 'P'
GROUP BY bom.parent_item, item.Description, item.cost, bom.ITEM_TYPE;
