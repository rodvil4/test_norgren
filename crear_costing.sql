BEGIN TRANSACTION;

CREATE TABLE Costing (
    Item_Code TEXT PRIMARY KEY NOT NULL,
    RawMaterial_Cost NUMERIC NOT NULL,
    Labor_Cost NUMERIC NOT NULL,
    Landed_Cost NUMERIC NOT NULL
);

INSERT INTO Costing (Item_Code, RawMaterial_Cost, Labor_Cost, Landed_Cost)
SELECT
    Item_Code,
    COALESCE(SUM(CASE WHEN Cost_Type = 'M' THEN Cost ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN Cost_Type = 'L' THEN Cost ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN Cost_Type = 'I' THEN Cost ELSE 0 END), 0)
FROM Costeo
GROUP BY Item_Code;

COMMIT;
